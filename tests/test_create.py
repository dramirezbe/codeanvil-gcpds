"""Tests for cmd_create — input resolution, scaffolding, and registration."""

import re
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from codeanvil.CLI.commands.create import (
    CreateInputError,
    cmd_create,
    resolve_create_inputs,
)
from codeanvil.CLI.commands.list import cmd_list
from codeanvil.CLI.commands.status import cmd_status
from codeanvil.CLI.parser import argparser
from codeanvil.config.paths import CONFIG, PROJECT_MANIFEST, TEMPLATES_DIR
from codeanvil.db.schema import create_schema
from codeanvil.db.utils import connect_db


@pytest.fixture
def db_path(tmp_path, monkeypatch):
    """Isolated DB plus patched create/list/status module globals."""
    path = tmp_path / "db" / "codeanvil.db"
    path.parent.mkdir()
    conn = connect_db(path)
    create_schema(conn)
    conn.close()
    monkeypatch.setattr("codeanvil.CLI.commands.create.DB_PATH", path)
    monkeypatch.setattr("codeanvil.CLI.commands.create.preflight", lambda: True)
    monkeypatch.setattr("codeanvil.CLI.commands.list.DB_PATH", path)
    monkeypatch.setattr("codeanvil.CLI.commands.status.DB_PATH", path)
    return path


def _manifest(project_dir):
    return yaml.safe_load((project_dir / PROJECT_MANIFEST).read_text(encoding="utf-8"))


# --- input resolution -------------------------------------------------------

def test_resolve_name_flag_derives_folder():
    assert resolve_create_inputs(None, "My SDR Lab", None) == ("My SDR Lab", "my_sdr_lab")


def test_resolve_name_flag_with_explicit_folder():
    assert resolve_create_inputs(None, "My SDR Lab", "my_custom") == ("My SDR Lab", "my_custom")


def test_resolve_positional_name_is_also_folder():
    """Legacy path (S2): name is both the project label and the folder."""
    assert resolve_create_inputs("My Proj", None, None) == ("My Proj", "My Proj")


def test_resolve_interactive_when_no_inputs():
    calls = []

    def fake_interactive(target):
        calls.append(target)
        return ("From TUI", "from_tui")

    assert resolve_create_inputs(None, None, None, interactive=fake_interactive) == ("From TUI", "from_tui")
    assert len(calls) == 1


def test_resolve_interactive_cancel_returns_none():
    assert resolve_create_inputs(None, None, None, interactive=lambda target: None) is None


def test_resolve_folder_requires_name():
    with pytest.raises(CreateInputError, match="requires '--name'"):
        resolve_create_inputs(None, None, "custom")


def test_resolve_folder_after_positional_name_is_error():
    with pytest.raises(CreateInputError, match="requires '--name'"):
        resolve_create_inputs("proj", None, "custom")


def test_resolve_name_flag_with_positional_is_error():
    with pytest.raises(CreateInputError, match="cannot combine"):
        resolve_create_inputs("proj", "Other Proj", None)


def test_resolve_blank_name_flag_is_error():
    with pytest.raises(CreateInputError, match="must not be empty"):
        resolve_create_inputs(None, "   ", None)


# --- parser wiring ----------------------------------------------------------

def test_parser_create_flags_and_optional_positional():
    args = argparser(["create", "--name", "Test Proj", "--folder", "custom"])
    assert args.name is None
    assert args.project_name == "Test Proj"
    assert args.folder == "custom"


def test_parser_create_positional_still_supported():
    args = argparser(["create", "proj"])
    assert args.name == "proj"
    assert args.project_name is None
    assert args.folder is None


# --- scaffolding ------------------------------------------------------------

def test_cmd_create_twice_same_uuid_one_row(tmp_path, monkeypatch):
    """Re-running create on the same dir keeps the manifest UUID and
    leaves exactly one DB row (no stale duplicate)."""
    db_path = tmp_path / "db" / "codeanvil.db"
    db_path.parent.mkdir()
    conn = connect_db(db_path)
    create_schema(conn)
    conn.close()
    monkeypatch.setattr("codeanvil.CLI.commands.create.DB_PATH", db_path)
    monkeypatch.setattr("codeanvil.CLI.commands.create.preflight", lambda: True)

    cmd_create("proj", tmp_path)
    first = yaml.safe_load(
        (tmp_path / "proj" / PROJECT_MANIFEST).read_text(encoding="utf-8")
    )

    cmd_create("proj", tmp_path)
    second = yaml.safe_load(
        (tmp_path / "proj" / PROJECT_MANIFEST).read_text(encoding="utf-8")
    )

    assert second["id"] == first["id"]

    conn = connect_db(db_path)
    rows = conn.execute("SELECT * FROM projects").fetchall()
    conn.close()
    assert len(rows) == 1
    assert rows[0]["id"] == first["id"]


def test_cmd_create_name_flag_scaffolds_derived_folder(tmp_path, db_path):
    cmd_create(None, tmp_path, project_name="Test Proj")

    project = tmp_path / "test_proj"
    assert (project / PROJECT_MANIFEST).is_file()
    assert _manifest(project)["name"] == "Test Proj"

    conn = connect_db(db_path)
    row = conn.execute("SELECT name, path FROM projects").fetchone()
    conn.close()
    assert row["name"] == "Test Proj"
    assert row["path"] == str(project.resolve())


def test_cmd_create_name_flag_with_explicit_folder(tmp_path, db_path):
    cmd_create(None, tmp_path, project_name="My SDR Lab", folder="my_custom_folder")

    project = tmp_path / "my_custom_folder"
    assert (project / PROJECT_MANIFEST).is_file()
    assert _manifest(project)["name"] == "My SDR Lab"
    assert not (tmp_path / "my_sdr_lab").exists()


def test_cmd_create_legacy_positional_keeps_name_as_folder(tmp_path, db_path):
    cmd_create("My Proj", tmp_path)

    project = tmp_path / "My Proj"
    assert (project / PROJECT_MANIFEST).is_file()
    assert _manifest(project)["name"] == "My Proj"


def test_cmd_create_interactive_uses_prompted_values(tmp_path, db_path, monkeypatch):
    monkeypatch.setattr(
        "codeanvil.CLI.commands.create._prompt_interactive",
        lambda target: ("Interactive Proj", "interactive_proj"),
    )

    cmd_create(None, tmp_path)

    project = tmp_path / "interactive_proj"
    assert _manifest(project)["name"] == "Interactive Proj"


def test_cmd_create_interactive_cancel_has_no_side_effects(tmp_path, db_path, monkeypatch):
    monkeypatch.setattr("codeanvil.CLI.commands.create._prompt_interactive", lambda target: None)

    cmd_create(None, tmp_path)  # must not raise

    assert not (tmp_path / "test_proj").exists()
    conn = connect_db(db_path)
    assert conn.execute("SELECT COUNT(*) AS n FROM projects").fetchone()["n"] == 0
    conn.close()


def test_cmd_create_folder_without_name_exits(tmp_path, db_path):
    with pytest.raises(SystemExit) as exc:
        cmd_create(None, tmp_path, folder="custom")
    assert exc.value.code == 1
    assert not (tmp_path / "custom").exists()


def test_cmd_create_name_with_positional_exits(tmp_path, db_path):
    with pytest.raises(SystemExit) as exc:
        cmd_create("proj", tmp_path, project_name="Other Proj")
    assert exc.value.code == 1
    assert not (tmp_path / "proj").exists()
    assert not (tmp_path / "other_proj").exists()


# --- list / status use the human label (S7, S8) -----------------------------

def test_list_shows_human_name_not_folder(tmp_path, db_path, capsys):
    cmd_create(None, tmp_path, project_name="My SDR Lab")

    cmd_list()

    out = capsys.readouterr().out
    assert "My SDR Lab" in out
    assert "my_sdr_lab" in out  # the path still ends with the folder


def test_status_lookup_by_human_name(tmp_path, db_path, capsys):
    cmd_create(None, tmp_path, project_name="My SDR Lab")

    cmd_status("My SDR Lab")

    out = capsys.readouterr().out
    assert "Project: My SDR Lab" in out
    assert str((tmp_path / "my_sdr_lab").resolve()) in out


def test_status_unknown_human_name_exits(tmp_path, db_path):
    with pytest.raises(SystemExit) as exc:
        cmd_status("nope")
    assert exc.value.code == 1


# --- non-TTY guard (S11) ----------------------------------------------------

def test_create_without_flags_errors_when_stdin_is_not_a_tty():
    result = subprocess.run(
        [sys.executable, "-I", "-m", "codeanvil", "create"],
        capture_output=True, text=True, timeout=30,
        stdin=subprocess.DEVNULL,
    )
    assert result.returncode != 0
    assert "--name" in (result.stdout + result.stderr)


# --- ordering, path plumbing, and dependency declaration (S2, S9, S10, S12) --

def test_legacy_positional_never_prompts(tmp_path, db_path, monkeypatch):
    def boom(*args, **kwargs):
        raise AssertionError("prompt used in legacy positional mode")

    monkeypatch.setattr("codeanvil.CLI.commands.create._prompt_interactive", boom)

    cmd_create("Legacy Proj", tmp_path)

    assert (tmp_path / "Legacy Proj" / PROJECT_MANIFEST).is_file()
    conn = connect_db(db_path)
    row = conn.execute("SELECT name, path FROM projects").fetchone()
    conn.close()
    assert row["name"] == "Legacy Proj"
    assert Path(row["path"]).name == "Legacy Proj"


def test_tui_receives_path_flag_target(tmp_path, db_path, monkeypatch):
    seen = {}

    def fake(target):
        seen["target"] = target
        return None

    monkeypatch.setattr("codeanvil.CLI.commands.create._prompt_interactive", fake)

    cmd_create(None, tmp_path)  # cancel before any scaffolding

    assert seen["target"] == tmp_path


def test_mcp_validated_after_inputs_before_scaffold(tmp_path, db_path):
    with pytest.raises(SystemExit) as exc:
        cmd_create(None, tmp_path, mcp_servers=["bogus"], project_name="Proj")

    assert exc.value.code == 1
    assert not (tmp_path / "proj").exists()


def test_tui_cancel_skips_mcp_validation(tmp_path, db_path, monkeypatch):
    monkeypatch.setattr("codeanvil.CLI.commands.create._prompt_interactive", lambda target: None)

    cmd_create(None, tmp_path, mcp_servers=["bogus"])  # must not raise or exit

    assert [p.name for p in tmp_path.iterdir()] == ["db"]  # only the fixture's DB dir


def test_status_rejects_folder_name_lookup(tmp_path, db_path):
    cmd_create(None, tmp_path, project_name="My SDR Lab")

    with pytest.raises(SystemExit) as exc:
        cmd_status("my_sdr_lab")

    assert exc.value.code == 1


def test_db_row_stores_label_and_explicit_folder(tmp_path, db_path):
    cmd_create(None, tmp_path, project_name="My SDR Lab", folder="sdr_lab_dir")

    conn = connect_db(db_path)
    row = conn.execute("SELECT name, path FROM projects").fetchone()
    conn.close()
    assert row["name"] == "My SDR Lab"
    assert Path(row["path"]).name == "sdr_lab_dir"


def test_beaupy_is_a_runtime_dependency():
    pyproject = Path(__file__).resolve().parents[1] / "pyproject.toml"
    text = pyproject.read_text(encoding="utf-8")
    deps_block = re.search(r"^dependencies = \[(.*?)\]", text, re.S | re.M)
    assert deps_block, "dependencies array not found in pyproject.toml"
    assert "beaupy" in deps_block.group(1)


# --- sync reconciles the label with the manifest (S13) ----------------------

# --- report-driven gate chain (S1, S2, S3, S8, S9) --------------------------

def test_config_declares_skill_prerequisite_chain():
    skills = CONFIG["skills"]
    assert skills["G0_valid_req_and_GT"]["prerequisite"] is None
    assert skills["custody-chain"]["prerequisite"] == "G0"
    assert skills["G1_start_design"]["prerequisite"] == "CC"


def test_create_makes_report_dir_without_cycle_subdir(tmp_path, db_path):
    cmd_create(None, tmp_path, project_name="Proj")

    report = tmp_path / "proj" / ".codeanvil" / "report"
    assert report.is_dir()
    assert list(report.iterdir()) == []


def _agents_md(tmp_path, db_path) -> str:
    cmd_create(None, tmp_path, project_name="Proj")
    return (tmp_path / "proj" / "AGENTS.md").read_text(encoding="utf-8")


def test_agents_md_is_a_passive_reference(tmp_path, db_path):
    text = _agents_md(tmp_path, db_path)

    assert "## Cycle" in text
    assert "## Report Format" in text
    assert "## Folder Reference" in text
    assert "## Startup" not in text
    assert "## Report creation" not in text
    assert "Identify the lowest-numbered incomplete gate" not in text


def test_agents_md_mandates_a_cycle_on_every_project_open(tmp_path, db_path):
    text = _agents_md(tmp_path, db_path)

    assert "On every project open" in text
    assert "native question" in text
    assert "01_test_sdr_usrp_iot_signals" in text
    assert "02_websocket_refactor" in text
    assert "cycle: <name>" in text


def test_agents_md_defines_the_iterative_report_format(tmp_path, db_path):
    text = _agents_md(tmp_path, db_path)

    assert ".codeanvil/report/<cycle-name>/<gate>.md" in text
    for field in ("Gate", "Cycle", "Document", "Created", "Date", "Timestamp",
                  "Iteration", "HITL"):
        assert f"| {field}" in text
    assert "### Description" in text
    assert "HITL: PASS" in text
    assert "HITL: FEEDBACK" in text
    assert "no DENIED" in text


def test_agents_md_skill_table_shows_the_prerequisite_chain(tmp_path, db_path):
    text = _agents_md(tmp_path, db_path)

    assert "| Gate | Skill | Prerequisite |" in text
    lines = text.splitlines()
    g0 = next(line for line in lines if ".agents/skills/G0_valid_req_and_GT/" in line)
    cc = next(line for line in lines if ".agents/skills/custody-chain/" in line)
    g1 = next(line for line in lines if ".agents/skills/G1_start_design/" in line)

    assert "None (entry point)" in g0
    assert "`G0.md` latest iteration `HITL: PASS`" in cc
    assert "`CC.md` latest iteration `HITL: PASS`" in g1
    assert lines.index(g0) < lines.index(cc) < lines.index(g1)


def _skill_text(*parts: str) -> str:
    return (TEMPLATES_DIR / "skills" / Path(*parts) / "SKILL.md").read_text(encoding="utf-8")


def test_g0_skill_writes_an_iterative_report():
    text = _skill_text("G0_valid_req_and_GT")

    assert ".codeanvil/report/<cycle-name>/G0.md" in text
    assert "HITL: FEEDBACK" in text
    assert "no prerequisite" in text.lower()


def test_custody_skill_requires_a_passing_g0_report():
    text = _skill_text("custody-chain")

    assert ".codeanvil/report/<cycle-name>/G0.md" in text
    assert "G0 must pass first. Run the G0 skill." in text
    assert ".codeanvil/report/<cycle-name>/CC.md" in text


def test_g1_skill_requires_a_passing_custody_report():
    text = _skill_text("G1_start_design")

    assert ".codeanvil/report/<cycle-name>/CC.md" in text
    assert "Custody chain must pass first. Run the custody-chain skill." in text
    assert ".codeanvil/report/<cycle-name>/G1.md" in text


# --- status reads cycle-scoped reports (T7) ---------------------------------

def _write_report(project, cycle: str, gate: str, iterations: list[tuple[int, str]]) -> None:
    report_dir = project / ".codeanvil" / "report" / cycle
    report_dir.mkdir(parents=True, exist_ok=True)
    sections = []
    for number, hitl in iterations:
        sections.append(
            f"## Iteration {number}\n\n"
            "| Field       | Value |\n"
            "|-------------|-------|\n"
            "| Date        | 2026-10-23 10:30 |\n"
            "| Timestamp   | 2026-10-23_10-30-00-000 |\n"
            f"| Iteration   | {number} |\n"
            f"| Cycle       | {cycle} |\n"
            f"| HITL        | {hitl} |\n\n"
            "### Description\n\nN/A\n"
        )
    (report_dir / f"{gate}.md").write_text(
        f"# {gate}\n\n" + "\n---\n\n".join(sections), encoding="utf-8"
    )


def _set_cycle(project, cycle: str) -> None:
    manifest = project / PROJECT_MANIFEST
    data = yaml.safe_load(manifest.read_text(encoding="utf-8"))
    data["cycle"] = cycle
    manifest.write_text(yaml.dump(data, sort_keys=False), encoding="utf-8")


def test_status_reads_cycle_scoped_reports(tmp_path, db_path, capsys):
    cmd_create(None, tmp_path, project_name="Proj")
    project = tmp_path / "proj"
    _set_cycle(project, "01_first_run")
    _write_report(project, "01_first_run", "G0", [(1, "FEEDBACK"), (2, "PASS")])
    _write_report(project, "01_first_run", "CC", [(1, "FEEDBACK")])

    cmd_status("Proj")

    out = capsys.readouterr().out
    assert "01_first_run (active)" in out
    assert "G0: PASS (iteration 2)" in out
    assert "CC: FEEDBACK (iteration 1)" in out


def test_status_lists_every_cycle(tmp_path, db_path, capsys):
    cmd_create(None, tmp_path, project_name="Proj")
    project = tmp_path / "proj"
    _set_cycle(project, "02_second_run")
    _write_report(project, "01_first_run", "G0", [(1, "PASS")])
    _write_report(project, "02_second_run", "G0", [(1, "PASS")])

    cmd_status("Proj")

    out = capsys.readouterr().out
    assert "01_first_run" in out
    assert "02_second_run (active)" in out


def test_sync_reconciles_label_for_list_and_status(tmp_path, db_path, monkeypatch, capsys):
    from codeanvil.init.sync import run_sync

    cmd_create(None, tmp_path, project_name="Old Label", folder="proj_dir")
    project = tmp_path / "proj_dir"

    # Simulate an upstream label rename pulled from git.
    manifest = project / PROJECT_MANIFEST
    data = yaml.safe_load(manifest.read_text(encoding="utf-8"))
    data["name"] = "New Label"
    manifest.write_text(yaml.dump(data), encoding="utf-8")

    monkeypatch.setattr("codeanvil.init.sync.DB_PATH", db_path)
    assert run_sync(project)[0] == "renamed"

    cmd_list()
    out = capsys.readouterr().out
    assert "New Label" in out
    assert "Old Label" not in out

    cmd_status("New Label")
    assert "Project: New Label" in capsys.readouterr().out

    with pytest.raises(SystemExit):
        cmd_status("Old Label")

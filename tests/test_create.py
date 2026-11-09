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
    assert list(skills) == [
        "S0_normalise_build_package", "G0_valid_req_and_GT",
        "S1_design_services", "G1_design_review",
        "S2_implement_services", "G2_adaptive_verification",
    ]
    assert skills["S0_normalise_build_package"]["prerequisite"] is None
    assert skills["G0_valid_req_and_GT"]["prerequisite"] == "S0"
    assert skills["S1_design_services"]["prerequisite"] == "G0"
    assert skills["G1_design_review"]["prerequisite"] == "S1"
    assert skills["S2_implement_services"]["prerequisite"] == "G1"
    assert skills["G2_adaptive_verification"]["prerequisite"] == "S2"


def test_create_makes_report_dir_without_cycle_subdir(tmp_path, db_path):
    cmd_create(None, tmp_path, project_name="Proj")

    report = tmp_path / "proj" / ".codeanvil" / "report"
    assert report.is_dir()
    assert list(report.iterdir()) == []


def test_create_scaffolds_the_methodology_tree_under_codeanvil(tmp_path, db_path):
    cmd_create(None, tmp_path, project_name="Proj")

    project = tmp_path / "proj"
    for rel in (".codeanvil/GT", ".codeanvil/design", ".codeanvil/backups",
                ".codeanvil/report", ".codeanvil/custody"):
        assert (project / rel).is_dir(), rel
    assert (project / ".codeanvil/GT/README.md").is_file()
    assert not (project / "GT").exists()


def test_create_manifest_points_to_the_new_gt_pair(tmp_path, db_path):
    cmd_create(None, tmp_path, project_name="Proj")

    assert _manifest(tmp_path / "proj")["gt"] == {
        "strs": ".codeanvil/GT/StRS.md",
        "syrs": ".codeanvil/GT/SyRS.md",
    }


def _agents_md(tmp_path, db_path) -> str:
    cmd_create(None, tmp_path, project_name="Proj")
    return (tmp_path / "proj" / "AGENTS.md").read_text(encoding="utf-8")


def test_agents_md_is_a_passive_reference(tmp_path, db_path):
    text = _agents_md(tmp_path, db_path)

    assert "## On Project Open" in text
    assert "codeanvil status" in text
    assert "## Cycle" in text
    assert "## Report Format" in text
    assert "## Folder Reference" in text
    assert "## Startup" not in text
    assert "## Report creation" not in text
    assert "Identify the lowest-numbered incomplete gate" not in text


def test_agents_md_mandates_a_cycle_on_every_project_open(tmp_path, db_path):
    text = _agents_md(tmp_path, db_path)

    assert "codeanvil status" in text
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
    rows = {
        name: next(line for line in lines if f".agents/skills/{name}/" in line)
        for name in ("S0_normalise_build_package", "G0_valid_req_and_GT",
                     "S1_design_services", "G1_design_review", "S2_implement_services",
                     "G2_adaptive_verification", "RFD_request_for_deviation")
    }

    assert "None (entry point)" in rows["S0_normalise_build_package"]
    assert "`S0.md` latest iteration `HITL: PASS`" in rows["G0_valid_req_and_GT"]
    assert "`G0.md` latest iteration `HITL: PASS`" in rows["S1_design_services"]
    assert "`S1.md` latest iteration `HITL: PASS`" in rows["G1_design_review"]
    assert "`G1.md` latest iteration `HITL: PASS`" in rows["S2_implement_services"]
    assert "`S2.md` latest iteration `HITL: PASS`" in rows["G2_adaptive_verification"]
    assert rows["RFD_request_for_deviation"].rstrip().endswith("| - |")
    order = [lines.index(rows[name]) for name in rows]
    assert order == sorted(order)


def _skill_text(*parts: str) -> str:
    return (TEMPLATES_DIR / "skills" / Path(*parts) / "SKILL.md").read_text(encoding="utf-8")


def test_g0_skill_writes_an_iterative_report():
    text = _skill_text("G0_valid_req_and_GT")

    assert ".codeanvil/report/<cycle-name>/G0.md" in text
    assert "HITL: FEEDBACK" in text
    assert "no prerequisite" not in text.lower()
    assert "S0 must pass first. Run the S0 skill." in text
    assert "S0 must rework first. Run the S0 skill." in text
    assert "Based on: S0 iteration" in text
    assert "Requirements complete, bounded, and verifiable?" in text
    assert "Decided by:" in text
    assert "| HITL | PASS |" in text


def _scaffold_skill(tmp_path, skill: str, *parts: str) -> Path:
    return tmp_path / "proj" / ".agents" / "skills" / skill / Path(*parts)


def test_scaffold_ships_the_v3_chain_and_not_the_retired_skills(tmp_path, db_path):
    cmd_create(None, tmp_path, project_name="Proj")
    skills = tmp_path / "proj" / ".agents" / "skills"

    for name in ("S0_normalise_build_package", "G0_valid_req_and_GT", "S1_design_services",
                 "G1_design_review", "S2_implement_services", "G2_adaptive_verification",
                 "RFD_request_for_deviation"):
        assert (skills / name / "SKILL.md").is_file()
    assert not (skills / "custody-chain").exists()
    assert not (skills / "G1_start_design").exists()
    text = (tmp_path / "proj" / "AGENTS.md").read_text(encoding="utf-8")
    for retired in ("custody-chain", "CC.md", "G1_SRS", "G1_artifacts"):
        assert retired not in text


def test_s0_blueprints_match_the_g0_copies(tmp_path, db_path):
    cmd_create(None, tmp_path, project_name="Proj")

    for name in ("StRS.md", "SyRS.md"):
        s0 = _scaffold_skill(tmp_path, "S0_normalise_build_package", "templates", name)
        g0 = _scaffold_skill(tmp_path, "G0_valid_req_and_GT", "templates", name)
        assert s0.read_bytes() == g0.read_bytes()


def test_scaffolded_s1_ships_its_graph_template_and_library(tmp_path, db_path):
    cmd_create(None, tmp_path, project_name="Proj")

    template = _scaffold_skill(tmp_path, "S1_design_services", "references", "dependency_graph_template.html")
    library = _scaffold_skill(tmp_path, "S1_design_services", "assets", "vis-network.min.js")
    assert template.is_file() and library.is_file()
    html = template.read_text(encoding="utf-8")
    assert "// === DATA" in html
    assert "https://" not in html.split("<style>")[0]
    assert _scaffold_skill(tmp_path, "S1_design_services", "references", "SDD.md").is_file()
    assert _scaffold_skill(tmp_path, "G1_design_review", "references", "G1_CHECKLIST.md").is_file()


def test_scaffolded_skills_are_self_contained(tmp_path, db_path):
    """C10 — a skill never points into another skill's folder or into methodology/."""
    cmd_create(None, tmp_path, project_name="Proj")
    skills = tmp_path / "proj" / ".agents" / "skills"
    names = [path.name for path in skills.iterdir() if path.is_dir()]

    for skill in names:
        others = [name for name in names if name != skill]
        for file in (skills / skill).rglob("*"):
            if file.suffix not in (".md", ".html") or not file.is_file():
                continue
            text = file.read_text(encoding="utf-8")
            assert "methodology/" not in text, file
            for other in others:
                assert f".agents/skills/{other}/" not in text, (file, other)


# --- V-SIL v3 skills: S0, S1, G1, RFD (text contracts) -----------------------

def _skill_file(skill: str, *parts: str) -> Path:
    return TEMPLATES_DIR / "skills" / skill / Path(*parts)


def test_s0_skill_is_the_entry_point_and_normalises_the_build_package():
    text = _skill_text("S0_normalise_build_package")

    assert ".codeanvil/report/<cycle-name>/S0.md" in text
    assert ".codeanvil/GT/build_package.md" in text
    assert "no prerequisite" in text.lower()
    assert "| HITL | PASS |" in text
    assert "S0 complete. Run the G0 skill." in text
    assert "in **any** cycle" in text  # RFD re-entry is not a hand-written pair


def test_s1_skill_writes_the_design_and_graph_to_the_design_dir():
    text = _skill_text("S1_design_services")

    assert ".codeanvil/report/<cycle-name>/S1.md" in text
    assert ".codeanvil/design/SDD.md" in text
    assert "G0 must pass first. Run the G0 skill." in text
    assert "Based on: G0 iteration" in text
    assert "| HITL | PASS |" in text
    assert "g1_check" not in text
    assert "G1_CHECKLIST" not in text  # self-contained: never reads G1's folder


def test_s1_skill_builds_the_spider_graph_from_its_own_template():
    text = _skill_text("S1_design_services")

    assert ".codeanvil/design/dependency_graph.html" in text
    assert "dependency_graph_template.html" in text
    assert "spider" in text
    assert ".codeanvil/project.yaml" in text
    assert "DATA" in text


def test_s1_graph_template_is_offline_and_ships_the_vendored_library():
    template = _skill_file("S1_design_services", "references", "dependency_graph_template.html")
    library = _skill_file("S1_design_services", "assets", "vis-network.min.js")

    html = template.read_text(encoding="utf-8")
    assert "// === DATA" in html and "// ===" in html
    assert "https://" not in html.split("<style>")[0]  # no remote script source
    assert "assets/vis-network.min.js" in html
    assert "@version 9.1.9" in library.read_text(encoding="utf-8")[:400]


def test_s1_design_template_keeps_the_numbered_sections():
    text = _skill_file("S1_design_services", "references", "SDD.md").read_text(encoding="utf-8")

    for heading in ("## 0. COTS envelope", "## 1. Building block view", "### 2.2 Topological",
                    "### 3.4 Service → service contracts", "## 4. Traceability",
                    "## 5. Design decisions", "## 6. Risks"):
        assert heading in text


def test_g1_skill_is_a_human_review_with_no_script():
    text = _skill_text("G1_design_review")

    assert ".codeanvil/report/<cycle-name>/G1.md" in text
    assert "S1 must pass first. Run the S1 skill." in text
    assert "S1 must rework first. Run the S1 skill." in text
    assert "Cycle suspended by RFD. Run the RFD skill." in text
    assert "Based on: S1 iteration" in text
    assert "PASS" in text and "FEEDBACK" in text and "RFD" in text
    assert "dependency_graph.html" in text
    assert "Decided by:" in text
    assert "g1_check" not in text
    assert not (TEMPLATES_DIR / "skills" / "G1_design_review" / "scripts").exists()
    assert _skill_file("G1_design_review", "references", "G1_CHECKLIST.md").is_file()


def test_rfd_skill_separates_defects_from_infeasible_requirements():
    text = _skill_text("RFD_request_for_deviation")

    assert ".codeanvil/report/<cycle-name>/RFD.md" in text
    assert "RFD_artifacts/RFD-NNN.md" in text
    assert "infeasible on the declared COTS platform" in text
    assert "ANALYSIS (no VL)" in text
    assert "Superseded by cycle:" in text
    assert "Outcome: Withdrawn" in text


def test_chain_skills_refuse_a_cycle_closed_by_an_rfd():
    for skill in ("S0_normalise_build_package", "G0_valid_req_and_GT",
                  "S1_design_services", "G1_design_review"):
        text = _skill_text(skill)
        assert "Cycle closed by RFD. Continue in cycle <name>." in text, skill
        assert "Superseded by cycle:" in text, skill


def test_rfd_skill_requires_a_new_unique_cycle_name_and_records_the_build_package_digest():
    text = _skill_text("RFD_request_for_deviation")

    assert "Build Package digest:" in text
    assert "must not match an existing folder" in text
    assert "redo the whole flow" in text


def test_s0_skill_requires_an_updated_build_package_after_an_rfd():
    text = _skill_text("S0_normalise_build_package")

    assert "Build Package unchanged since the RFD. Update .codeanvil/GT/build_package.md first." in text
    assert "Build Package digest:" in text


# --- status reads cycle-scoped reports (T7) ---------------------------------

def _write_report(
    project, cycle: str, gate: str, iterations: list[tuple],
) -> None:
    """Each iteration is (number, hitl) or (number, hitl, description)."""
    report_dir = project / ".codeanvil" / "report" / cycle
    report_dir.mkdir(parents=True, exist_ok=True)
    sections = []
    for number, hitl, *rest in iterations:
        description = rest[0] if rest else "N/A"
        sections.append(
            f"## Iteration {number}\n\n"
            "| Field       | Value |\n"
            "|-------------|-------|\n"
            "| Date        | 2026-10-23 10:30 |\n"
            "| Timestamp   | 2026-10-23_10-30-00-000 |\n"
            f"| Iteration   | {number} |\n"
            f"| Cycle       | {cycle} |\n"
            f"| HITL        | {hitl} |\n\n"
            f"### Description\n\n{description}\n"
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


def test_status_ignores_the_ambiguous_schema_row(tmp_path, db_path, capsys):
    """S1 — the literal schema row (two values) is not a verdict."""
    cmd_create(None, tmp_path, project_name="Proj")
    project = tmp_path / "proj"
    _set_cycle(project, "01_c")
    report_dir = project / ".codeanvil" / "report" / "01_c"
    report_dir.mkdir(parents=True)
    (report_dir / "G0.md").write_text(
        "| Field | Value |\n|---|---|\n| HITL | PASS | FEEDBACK |\n", encoding="utf-8"
    )

    cmd_status("Proj")

    out = capsys.readouterr().out
    assert "G0: UNKNOWN" in out
    assert "G0: PASS" not in out


def test_status_reads_legacy_reports_when_no_cycles_exist(tmp_path, db_path, capsys):
    """T7 — legacy <gate>_<timestamp>.md stay readable, newest per gate."""
    cmd_create(None, tmp_path, project_name="Proj")
    report = tmp_path / "proj" / ".codeanvil" / "report"
    (report / "G0_2026-10-21_16-23-45-123.md").write_text("# old\n", encoding="utf-8")
    (report / "G0_2026-10-22_09-00-00-000.md").write_text("# new\n", encoding="utf-8")
    (report / "CC_2026-10-21_17-00-00-000.md").write_text("# cc\n", encoding="utf-8")

    cmd_status("Proj")

    out = capsys.readouterr().out
    assert "Legacy reports (pre-cycle layout):" in out
    assert "G0: G0_2026-10-22_09-00-00-000.md" in out
    assert "CC: CC_2026-10-21_17-00-00-000.md" in out
    assert "Reports: none yet" not in out


def test_status_reports_latest_hitl_not_first(tmp_path, db_path, capsys):
    """S1/T7 — the last appended iteration verdict wins (PASS then FEEDBACK)."""
    cmd_create(None, tmp_path, project_name="Proj")
    project = tmp_path / "proj"
    _set_cycle(project, "01_c")
    _write_report(project, "01_c", "G0", [(1, "PASS"), (2, "FEEDBACK")])

    cmd_status("Proj")

    out = capsys.readouterr().out
    assert "G0: FEEDBACK (iteration 2)" in out
    assert "G0: PASS" not in out


# --- status: chain order, delivered stages, stale reports, closed cycles (T10) --

def _status_out(tmp_path, capsys, reports, cycle="01_c"):
    """reports: (gate, iterations) pairs written into one active cycle."""
    cmd_create(None, tmp_path, project_name="Proj")
    project = tmp_path / "proj"
    _set_cycle(project, cycle)
    for gate, iterations in reports:
        _write_report(project, cycle, gate, iterations)
    cmd_status("Proj")
    return capsys.readouterr().out


def test_status_orders_gates_by_the_chain_then_unknown_ids(tmp_path, db_path, capsys):
    out = _status_out(tmp_path, capsys, [
        ("RFD", [(1, "FEEDBACK")]), ("CC", [(1, "PASS")]), ("S1", [(1, "PASS")]),
        ("G0", [(1, "PASS")]), ("S0", [(1, "PASS")]),
    ])
    positions = [out.index(f"    {gate}:") for gate in ("S0", "G0", "S1", "CC", "RFD")]
    assert positions == sorted(positions)


def test_status_prints_a_passing_stage_as_delivered(tmp_path, db_path, capsys):
    out = _status_out(tmp_path, capsys, [
        ("S1", [(1, "PASS")]), ("G1", [(1, "PASS")]), ("S0", [(1, "FEEDBACK")]),
    ])
    assert "S1: delivered (iteration 1)" in out
    assert "G1: PASS (iteration 1)" in out
    assert "S0: FEEDBACK (iteration 1)" in out


def test_status_marks_a_report_stale_when_its_predecessor_moved_on(tmp_path, db_path, capsys):
    out = _status_out(tmp_path, capsys, [
        ("S1", [(1, "PASS"), (2, "PASS")]),
        ("G1", [(1, "PASS", "Based on: S1 iteration 1")]),
    ])
    assert "G1: PASS (iteration 1) [stale: based on S1 iteration 1, S1 is at 2]" in out


def test_status_propagates_staleness_down_the_chain(tmp_path, db_path, capsys):
    out = _status_out(tmp_path, capsys, [
        ("S1", [(1, "PASS"), (2, "PASS")]),
        ("G1", [(1, "PASS", "Based on: S1 iteration 1")]),
        ("S2", [(1, "PASS", "Based on: G1 iteration 1")]),
    ])
    assert "S2: delivered (iteration 1) [stale: G1 is stale]" in out


def test_status_shows_no_suffix_for_an_up_to_date_report(tmp_path, db_path, capsys):
    out = _status_out(tmp_path, capsys, [
        ("S1", [(1, "PASS"), (2, "PASS")]),
        ("G1", [(1, "PASS", "Based on: S1 iteration 2")]),
    ])
    assert "G1: PASS (iteration 1)\n" in out
    assert "stale" not in out


def test_status_ignores_based_on_in_earlier_iterations(tmp_path, db_path, capsys):
    out = _status_out(tmp_path, capsys, [
        ("S1", [(1, "PASS"), (2, "PASS")]),
        ("G1", [(1, "FEEDBACK", "Based on: S1 iteration 1"), (2, "PASS", "no marker")]),
    ])
    assert "stale" not in out


def test_status_ignores_a_based_on_naming_a_missing_report(tmp_path, db_path, capsys):
    out = _status_out(tmp_path, capsys, [("G1", [(1, "PASS", "Based on: S1 iteration 1")])])
    assert "stale" not in out


def test_status_stops_on_a_based_on_loop(tmp_path, db_path, capsys):
    out = _status_out(tmp_path, capsys, [
        ("S1", [(1, "PASS", "Based on: G1 iteration 1")]),
        ("G1", [(1, "PASS", "Based on: S1 iteration 1")]),
    ])
    assert "S1: delivered (iteration 1)" in out
    assert "G1: PASS (iteration 1)" in out


def test_status_marks_a_cycle_closed_by_the_latest_rfd_iteration(tmp_path, db_path, capsys):
    cmd_create(None, tmp_path, project_name="Proj")
    project = tmp_path / "proj"
    _set_cycle(project, "02_x")
    _write_report(project, "01_c", "RFD", [
        (1, "FEEDBACK", "Superseded by cycle: 00_old"),
        (2, "PASS", "Superseded by cycle: 02_x"),
    ])
    _write_report(project, "03_c", "RFD", [
        (1, "PASS", "Superseded by cycle: 02_x"), (2, "PASS", "decided again"),
    ])

    cmd_status("Proj")

    out = capsys.readouterr().out
    assert "01_c (closed: superseded by 02_x)" in out
    assert "03_c\n" in out


def test_status_always_prints_the_active_cycle_even_without_reports(tmp_path, db_path, capsys):
    cmd_create(None, tmp_path, project_name="Proj")
    project = tmp_path / "proj"
    _set_cycle(project, "02_new")
    _write_report(project, "01_old", "G0", [(1, "PASS")])

    cmd_status("Proj")

    out = capsys.readouterr().out
    assert "02_new (active)" in out


def test_status_shows_the_latest_backup_per_stage(tmp_path, db_path, capsys):
    cmd_create(None, tmp_path, project_name="Proj")
    project = tmp_path / "proj"
    _set_cycle(project, "01_c")
    _write_report(project, "01_c", "S1", [(1, "PASS")])
    backups = project / ".codeanvil" / "backups" / "01_c"
    (backups / "S1_iter1").mkdir(parents=True)
    (backups / "S1_iter2").mkdir()

    cmd_status("Proj")

    out = capsys.readouterr().out
    assert "  Backups: S1 iteration 2 → .codeanvil/backups/01_c/S1_iter2/" in out
    assert "S1_iter1" not in out


def test_status_lists_backups_without_a_producing_cycle(tmp_path, db_path, capsys):
    cmd_create(None, tmp_path, project_name="Proj")
    project = tmp_path / "proj"
    folder = project / ".codeanvil" / "backups" / "unknown" / "S2_2026-11-06_14-10-00-123"
    folder.mkdir(parents=True)

    cmd_status("Proj")

    out = capsys.readouterr().out
    assert "Backups without a producing cycle:" in out
    assert "S2: .codeanvil/backups/unknown/S2_2026-11-06_14-10-00-123/" in out


def test_g0_validator_is_side_effect_free_and_maps_exit_codes(tmp_path):
    """S4 — validator prints only; 0 pass, 1 errors, 2 usage/IO."""
    import hashlib
    import shutil

    repo = Path(__file__).resolve().parents[1]
    validator = repo / "templates/skills/G0_valid_req_and_GT/scripts/g0_validate.py"
    fixtures = repo / "templates/tests/fixtures"
    strs, syrs = tmp_path / "StRS.md", tmp_path / "SyRS.md"
    shutil.copy2(fixtures / "StRS.md", strs)
    shutil.copy2(fixtures / "SyRS.md", syrs)

    def digests():
        return [hashlib.sha256(p.read_bytes()).hexdigest() for p in (strs, syrs)]

    before = digests()
    ok = subprocess.run(
        [sys.executable, str(validator), str(strs), str(syrs)],
        capture_output=True, text=True,
    )
    assert ok.returncode == 0, ok.stdout + ok.stderr
    assert digests() == before

    bad = tmp_path / "Bad.md"
    bad.write_text(
        "## Stakeholder Requirements Specification (StRS)\n\njunk\n", encoding="utf-8"
    )
    errs = subprocess.run(
        [sys.executable, str(validator), str(bad), str(syrs)], capture_output=True
    )
    assert errs.returncode == 1

    usage = subprocess.run(
        [sys.executable, str(validator), str(strs), str(tmp_path / "nope.md")],
        capture_output=True,
    )
    assert usage.returncode == 2


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

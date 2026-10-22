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
from codeanvil.config.paths import PROJECT_MANIFEST
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

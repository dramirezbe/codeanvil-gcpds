"""Command-level sync tests: printed action strings and idempotent no-write (S13)."""

import hashlib

import pytest
import yaml

from codeanvil.CLI.commands.list import cmd_list
from codeanvil.CLI.commands.status import cmd_status
from codeanvil.CLI.commands.sync import cmd_sync
from codeanvil.config.paths import PROJECT_MANIFEST
from codeanvil.db.projects import get_project_by_id, get_project_by_name, sync_project
from codeanvil.db.schema import create_schema
from codeanvil.db.utils import connect_db
from codeanvil.init.create import write_project_manifest
from codeanvil.init.sync import run_sync


def _db(tmp_path):
    path = tmp_path / "db" / "codeanvil.db"
    path.parent.mkdir()
    conn = connect_db(path)
    create_schema(conn)
    conn.close()
    return path


def _patch_db(monkeypatch, db_path):
    monkeypatch.setattr("codeanvil.init.sync.DB_PATH", db_path)
    monkeypatch.setattr("codeanvil.CLI.commands.sync.DB_PATH", db_path)
    monkeypatch.setattr("codeanvil.CLI.commands.list.DB_PATH", db_path)
    monkeypatch.setattr("codeanvil.CLI.commands.status.DB_PATH", db_path)


def _rename(project, name):
    manifest = project / PROJECT_MANIFEST
    data = yaml.safe_load(manifest.read_text(encoding="utf-8"))
    data["name"] = name
    manifest.write_text(yaml.dump(data), encoding="utf-8")


def test_cmd_sync_reports_each_action(tmp_path, monkeypatch, capsys):
    db_path = _db(tmp_path)
    _patch_db(monkeypatch, db_path)
    project = tmp_path / "proj"
    project.mkdir()
    write_project_manifest(project, "id-1", "Old Label")

    monkeypatch.chdir(project)
    cmd_sync()
    assert "[registered]" in capsys.readouterr().out

    cmd_sync()
    assert "[already registered]" in capsys.readouterr().out

    _rename(project, "New Label")
    cmd_sync()
    assert "[renamed]" in capsys.readouterr().out

    moved = tmp_path / "moved"
    project.rename(moved)
    _rename(moved, "Third Label")
    monkeypatch.chdir(moved)
    cmd_sync()
    out = capsys.readouterr().out
    assert "[updated]" in out
    assert "Third Label" in out


def test_renamed_label_resolves_and_old_label_is_gone(tmp_path, monkeypatch, capsys):
    db_path = _db(tmp_path)
    _patch_db(monkeypatch, db_path)
    project = tmp_path / "proj"
    project.mkdir()
    write_project_manifest(project, "id-1", "Old Label")
    assert run_sync(project)[0] == "registered"

    _rename(project, "New Label")
    assert run_sync(project)[0] == "renamed"

    cmd_list()
    out = capsys.readouterr().out
    assert "New Label" in out
    assert "Old Label" not in out

    cmd_status("New Label")
    assert "Project: New Label" in capsys.readouterr().out

    with pytest.raises(SystemExit) as exc:
        cmd_status("Old Label")
    assert exc.value.code == 1

    conn = connect_db(db_path)
    assert get_project_by_name(conn, "New Label")["path"] == str(project.resolve())
    assert get_project_by_name(conn, "Old Label") is None
    conn.close()


def test_idempotent_sync_does_not_write_the_db(tmp_path):
    db_path = _db(tmp_path)

    def digest():
        return hashlib.sha256(db_path.read_bytes()).hexdigest()

    conn = connect_db(db_path)
    assert sync_project(conn, "id-1", "Label", tmp_path / "p") == "registered"
    before = digest()
    assert sync_project(conn, "id-1", "Label", tmp_path / "p") == "already registered"
    assert sync_project(conn, "id-1", "Label", tmp_path / "p") == "already registered"
    after = digest()
    conn.close()

    assert before == after
    conn = connect_db(db_path)
    row = get_project_by_id(conn, "id-1")
    conn.close()
    assert (row["name"], row["path"]) == ("Label", str(tmp_path / "p"))

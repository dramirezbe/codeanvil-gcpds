"""Tests for project registration, sync flow, manifest, and schema migration."""

import sqlite3

import pytest
import yaml

from codeanvil.config.paths import PROJECT_MANIFEST
from codeanvil.db.projects import (
    get_project_by_id,
    get_project_by_name,
    register_project,
    sync_project,
)
from codeanvil.db.schema import create_schema, has_legacy_schema, recreate_if_legacy
from codeanvil.db.utils import connect_db
from codeanvil.init.create import write_project_manifest
from codeanvil.init.sync import _migrate_provenance, run_sync

_OLD_SCHEMA = """
CREATE TABLE projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    path TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL
);
CREATE TABLE gate_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL
);
"""


@pytest.fixture
def conn():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    create_schema(conn)
    yield conn
    conn.close()


# --- register_project -------------------------------------------------------

def test_register_project_inserts_uuid(conn):
    pid = "019296a0-7b1c-7d4e-8a3f-1c2d3e4f5a6b"
    register_project(conn, pid, "proj", "/tmp/proj")
    row = get_project_by_id(conn, pid)
    assert row["name"] == "proj"
    assert row["path"] == "/tmp/proj"


def test_register_project_idempotent(conn):
    pid = "019296a0-7b1c-7d4e-8a3f-1c2d3e4f5a6b"
    register_project(conn, pid, "proj", "/tmp/proj")
    register_project(conn, pid, "proj", "/tmp/proj")  # must not raise
    rows = conn.execute("SELECT * FROM projects").fetchall()
    assert len(rows) == 1


def test_get_project_by_name_returns_id_name_path(conn):
    pid = "019296a0-7b1c-7d4e-8a3f-1c2d3e4f5a6b"
    register_project(conn, pid, "proj", "/tmp/proj")
    row = get_project_by_name(conn, "proj")
    assert dict(row) == {"id": pid, "name": "proj", "path": "/tmp/proj"}


def test_get_project_by_name_unknown(conn):
    assert get_project_by_name(conn, "nope") is None


# --- sync_project -----------------------------------------------------------

def test_sync_project_registered(conn):
    action = sync_project(conn, "id-1", "clone", "/tmp/clone")
    assert action == "registered"
    assert get_project_by_id(conn, "id-1")["path"] == "/tmp/clone"


def test_sync_project_already_registered(conn):
    sync_project(conn, "id-1", "clone", "/tmp/clone")
    action = sync_project(conn, "id-1", "clone", "/tmp/clone")
    assert action == "already registered"


def test_sync_project_moved(conn):
    sync_project(conn, "id-1", "clone", "/tmp/clone")
    action = sync_project(conn, "id-1", "clone", "/tmp/new-location")
    assert action == "moved"
    assert get_project_by_id(conn, "id-1")["path"] == "/tmp/new-location"


def test_sync_project_renamed(conn):
    """Manifest label changed, path unchanged -> renamed."""
    sync_project(conn, "id-1", "old-label", "/tmp/clone")
    action = sync_project(conn, "id-1", "new-label", "/tmp/clone")
    assert action == "renamed"
    row = get_project_by_id(conn, "id-1")
    assert row["name"] == "new-label"
    assert row["path"] == "/tmp/clone"


def test_sync_project_updated(conn):
    """Both label and path changed -> updated."""
    sync_project(conn, "id-1", "old-label", "/tmp/clone")
    action = sync_project(conn, "id-1", "new-label", "/tmp/new-location")
    assert action == "updated"
    row = get_project_by_id(conn, "id-1")
    assert row["name"] == "new-label"
    assert row["path"] == "/tmp/new-location"


def test_sync_project_unchanged_name_and_path(conn):
    sync_project(conn, "id-1", "clone", "/tmp/clone")
    assert sync_project(conn, "id-1", "clone", "/tmp/clone") == "already registered"


# --- write_project_manifest -------------------------------------------------

def test_write_project_manifest_content(tmp_path):
    pid = "019296a0-7b1c-7d4e-8a3f-1c2d3e4f5a6b"
    write_project_manifest(tmp_path, pid, "proj")

    manifest_path = tmp_path / PROJECT_MANIFEST
    assert manifest_path.is_file()
    data = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    assert data["id"] == pid
    assert data["name"] == "proj"
    assert data["gt"] == {"strs": "GT/G0_StRS.md", "syrs": "GT/G0_SyRS.md"}
    assert "path" not in data  # manifest is collaboration-safe: no absolute paths


def test_write_project_manifest_header(tmp_path):
    write_project_manifest(tmp_path, "id", "proj")
    text = (tmp_path / PROJECT_MANIFEST).read_text(encoding="utf-8")
    assert text.startswith("# Auto-generated — do not edit.")


def test_write_project_manifest_skips_when_same_id_exists(tmp_path):
    pid = "019296a0-7b1c-7d4e-8a3f-1c2d3e4f5a6b"
    write_project_manifest(tmp_path, pid, "proj")
    before = (tmp_path / PROJECT_MANIFEST).read_bytes()

    write_project_manifest(tmp_path, pid, "proj")  # re-scaffold: same id
    assert (tmp_path / PROJECT_MANIFEST).read_bytes() == before


def test_write_project_manifest_rewrites_on_different_id(tmp_path):
    write_project_manifest(tmp_path, "id-old", "proj")
    write_project_manifest(tmp_path, "id-new", "proj")
    data = yaml.safe_load((tmp_path / PROJECT_MANIFEST).read_text(encoding="utf-8"))
    assert data["id"] == "id-new"


# --- _migrate_provenance ----------------------------------------------------

def test_migrate_provenance_moves_dir(tmp_path):
    old = tmp_path / ".provenance"
    old.mkdir()
    (old / "snapshot.json").write_text("{}", encoding="utf-8")

    _migrate_provenance(tmp_path)

    new = tmp_path / ".codeanvil" / "custody"
    assert (new / "snapshot.json").is_file()
    assert not old.exists()


def test_migrate_provenance_noop_without_old_dir(tmp_path):
    _migrate_provenance(tmp_path)
    assert not (tmp_path / ".codeanvil").exists()


def test_migrate_provenance_fills_empty_custody_dir(tmp_path):
    """Re-scaffold leaves an empty custody/ — migration must still run,
    otherwise .provenance/ is orphaned forever."""
    old = tmp_path / ".provenance"
    old.mkdir()
    (old / "snapshot.json").write_text("{}", encoding="utf-8")
    new = tmp_path / ".codeanvil" / "custody"
    new.mkdir(parents=True)  # empty, created by scaffold

    _migrate_provenance(tmp_path)

    assert (new / "snapshot.json").is_file()
    assert not old.exists()


def test_migrate_provenance_skips_non_empty_custody(tmp_path):
    old = tmp_path / ".provenance"
    old.mkdir()
    (old / "old.jsonl").write_text("old", encoding="utf-8")
    new = tmp_path / ".codeanvil" / "custody"
    new.mkdir(parents=True)
    (new / "keep.jsonl").write_text("keep", encoding="utf-8")

    _migrate_provenance(tmp_path)

    assert old.exists()
    assert (new / "keep.jsonl").read_text(encoding="utf-8") == "keep"


# --- run_sync ---------------------------------------------------------------

def _write_manifest(root, pid="id-1", name="proj"):
    write_project_manifest(root, pid, name)


def test_run_sync_registers(tmp_path, monkeypatch):
    db_path = tmp_path / "db" / "codeanvil.db"
    db_path.parent.mkdir()
    conn = connect_db(db_path)
    create_schema(conn)
    conn.close()
    monkeypatch.setattr("codeanvil.init.sync.DB_PATH", db_path)

    _write_manifest(tmp_path, pid="id-1", name="proj")
    action, data = run_sync(tmp_path)
    assert action == "registered"
    assert data["id"] == "id-1"

    conn = connect_db(db_path)
    assert get_project_by_id(conn, "id-1")["path"] == str(tmp_path.resolve())
    conn.close()


def test_run_sync_noop_then_moved(tmp_path, monkeypatch):
    db_path = tmp_path / "db" / "codeanvil.db"
    db_path.parent.mkdir()
    conn = connect_db(db_path)
    create_schema(conn)
    conn.close()
    monkeypatch.setattr("codeanvil.init.sync.DB_PATH", db_path)

    # Project dir must live outside the renamed subtree: keep it a sibling
    # so moving it doesn't move the DB with it.
    project = tmp_path / "proj"
    project.mkdir()
    _write_manifest(project, pid="id-1", name="proj")
    action, _ = run_sync(project)
    assert action == "registered"
    action, _ = run_sync(project)
    assert action == "already registered"

    moved = tmp_path / "moved-here"
    project.rename(moved)
    action, _ = run_sync(moved)
    assert action == "moved"
    conn = connect_db(db_path)
    assert get_project_by_id(conn, "id-1")["path"] == str(moved.resolve())
    conn.close()


def test_run_sync_migrates_provenance(tmp_path, monkeypatch):
    db_path = tmp_path / "db" / "codeanvil.db"
    db_path.parent.mkdir()
    conn = connect_db(db_path)
    create_schema(conn)
    conn.close()
    monkeypatch.setattr("codeanvil.init.sync.DB_PATH", db_path)

    _write_manifest(tmp_path, pid="id-1", name="proj")
    old = tmp_path / ".provenance"
    old.mkdir()
    (old / "custody.jsonl").write_text("", encoding="utf-8")

    run_sync(tmp_path)

    assert (tmp_path / ".codeanvil" / "custody" / "custody.jsonl").is_file()
    assert not old.exists()


def test_run_sync_missing_manifest(tmp_path):
    with pytest.raises(FileNotFoundError):
        run_sync(tmp_path)


def test_run_sync_reconciles_renamed_label(tmp_path, monkeypatch):
    """A label rename pulled from git reaches the DB on sync (S13)."""
    db_path = tmp_path / "db" / "codeanvil.db"
    db_path.parent.mkdir()
    conn = connect_db(db_path)
    create_schema(conn)
    conn.close()
    monkeypatch.setattr("codeanvil.init.sync.DB_PATH", db_path)

    project = tmp_path / "proj"
    project.mkdir()
    _write_manifest(project, pid="id-1", name="Old Label")
    assert run_sync(project)[0] == "registered"

    # Simulate an upstream rename: rewrite the committed manifest in place.
    manifest = project / PROJECT_MANIFEST
    data = yaml.safe_load(manifest.read_text(encoding="utf-8"))
    data["name"] = "New Label"
    manifest.write_text(yaml.dump(data), encoding="utf-8")

    action, payload = run_sync(project)
    assert action == "renamed"
    assert payload["name"] == "New Label"

    conn = connect_db(db_path)
    assert get_project_by_name(conn, "New Label")["path"] == str(project.resolve())
    assert get_project_by_name(conn, "Old Label") is None
    conn.close()


# --- legacy schema migration ------------------------------------------------

def test_has_legacy_schema_false_for_missing_db(tmp_path):
    assert has_legacy_schema(tmp_path / "nope.db") is False


def test_has_legacy_schema_false_for_current_schema(tmp_path):
    db_path = tmp_path / "codeanvil.db"
    conn = connect_db(db_path)
    create_schema(conn)
    conn.close()
    assert has_legacy_schema(db_path) is False


def test_has_legacy_schema_true_for_old_db(tmp_path):
    db_path = tmp_path / "codeanvil.db"
    conn = sqlite3.connect(str(db_path))
    conn.executescript(_OLD_SCHEMA)
    conn.commit()
    conn.close()
    assert has_legacy_schema(db_path) is True


def test_recreate_if_legacy_removes_db(tmp_path):
    db_path = tmp_path / "codeanvil.db"
    conn = sqlite3.connect(str(db_path))
    conn.executescript(_OLD_SCHEMA)
    conn.commit()
    conn.close()

    assert recreate_if_legacy(db_path) is True
    assert not db_path.exists()

    # After recreation the new schema is in place and stays.
    conn = connect_db(db_path)
    create_schema(conn)
    conn.close()
    assert has_legacy_schema(db_path) is False
    assert recreate_if_legacy(db_path) is False

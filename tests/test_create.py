"""Tests for cmd_create — re-scaffold must reuse the committed project UUID."""

import yaml

from codeanvil.CLI.cli import cmd_create
from codeanvil.config.paths import PROJECT_MANIFEST
from codeanvil.db.schema import create_schema
from codeanvil.db.utils import connect_db


def test_cmd_create_twice_same_uuid_one_row(tmp_path, monkeypatch):
    """Re-running create on the same dir keeps the manifest UUID and
    leaves exactly one DB row (no stale duplicate)."""
    db_path = tmp_path / "db" / "codeanvil.db"
    db_path.parent.mkdir()
    conn = connect_db(db_path)
    create_schema(conn)
    conn.close()
    monkeypatch.setattr("codeanvil.CLI.cli.DB_PATH", db_path)
    monkeypatch.setattr("codeanvil.CLI.cli.preflight", lambda: True)

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

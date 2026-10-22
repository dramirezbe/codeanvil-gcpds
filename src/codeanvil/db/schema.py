import sqlite3
from pathlib import Path

from codeanvil.config.logger import get_logger

log = get_logger(__name__)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS projects (
    id          TEXT PRIMARY KEY,       -- UUIDv7
    name        TEXT NOT NULL,          -- human label, NOT UNIQUE
    path        TEXT NOT NULL,          -- absolute path on THIS machine (local, not shared)
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


def db_exists(db_path: Path) -> bool:
    return db_path.is_file()


def create_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(_SCHEMA)
    conn.commit()
    log.info("schema initialized")


def has_legacy_schema(db_path: Path) -> bool:
    """Pre-release check: old INTEGER-id `projects` table or the removed
    `sessions`/`gate_results` tables. Fresh or current DBs return False."""
    if not db_path.is_file():
        return False
    conn = sqlite3.connect(str(db_path))
    try:
        tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if "sessions" in tables or "gate_results" in tables:
            return True
        if "projects" in tables:
            for col in conn.execute("PRAGMA table_info(projects)"):
                if col[1] == "id" and not str(col[2]).upper().startswith("TEXT"):
                    return True
        return False
    finally:
        conn.close()


def recreate_if_legacy(db_path: Path) -> bool:
    """If the DB has a pre-release schema, delete it (and WAL sidecars).
    Returns True when a legacy DB was removed."""
    if not has_legacy_schema(db_path):
        return False
    for suffix in ("", "-wal", "-shm"):
        sidecar = db_path.parent / (db_path.name + suffix)
        if sidecar.exists():
            sidecar.unlink()
    log.warning("pre-release schema detected — database recreated at %s", db_path)
    return True

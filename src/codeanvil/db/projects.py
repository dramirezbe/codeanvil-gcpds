from pathlib import Path

from codeanvil.config.logger import get_logger

log = get_logger(__name__)


def register_project(conn, name: str, path: Path) -> int:
    existing = get_project_by_name(conn, name)
    if existing:
        log.info("project '%s' already registered (id=%d) — skipping insert", name, existing["id"])
        return existing["id"]

    cur = conn.execute(
        "INSERT INTO projects (name, path) VALUES (?, ?)",
        (name, str(path)),
    )
    conn.commit()
    log.info("registered project '%s' (id=%d)", name, cur.lastrowid)
    return cur.lastrowid


def list_projects(conn) -> list:
    return conn.execute("SELECT id, name, path, created_at FROM projects ORDER BY created_at DESC").fetchall()


def get_project_by_name(conn, name: str):
    return conn.execute("SELECT id FROM projects WHERE name = ?", (name,)).fetchone()

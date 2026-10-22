from pathlib import Path

from codeanvil.config.logger import get_logger

log = get_logger(__name__)


def register_project(conn, project_id: str, name: str, path: Path) -> str:
    """Register a project by UUIDv7. Idempotent: an existing UUID is a no-op."""
    existing = conn.execute("SELECT id FROM projects WHERE id = ?", (project_id,)).fetchone()
    if existing:
        log.info("project '%s' already registered (id=%s) — skipping insert", name, project_id)
        return project_id

    conn.execute(
        "INSERT INTO projects (id, name, path) VALUES (?, ?, ?)",
        (project_id, name, str(path)),
    )
    conn.commit()
    log.info("registered project '%s' (id=%s)", name, project_id)
    return project_id


def sync_project(conn, project_id: str, name: str, path: Path) -> str:
    """Register or update a project from its manifest. Returns action taken."""
    existing = conn.execute(
        "SELECT path FROM projects WHERE id = ?", (project_id,)
    ).fetchone()

    if existing is None:
        conn.execute(
            "INSERT INTO projects (id, name, path) VALUES (?, ?, ?)",
            (project_id, name, str(path)),
        )
        conn.commit()
        return "registered"

    if existing["path"] == str(path):
        return "already registered"

    conn.execute(
        "UPDATE projects SET path = ? WHERE id = ?",
        (str(path), project_id),
    )
    conn.commit()
    return "moved"


def list_projects(conn) -> list:
    return conn.execute("SELECT id, name, path, created_at FROM projects ORDER BY created_at DESC").fetchall()


def get_project_by_id(conn, project_id: str):
    return conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()


def get_project_by_name(conn, name: str):
    return conn.execute("SELECT id, name, path FROM projects WHERE name = ?", (name,)).fetchone()

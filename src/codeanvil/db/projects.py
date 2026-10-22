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
    """Register or update a project from its manifest. Returns action taken:
    registered | already registered | renamed | moved | updated.

    The manifest is the source of truth: an id that already exists gets its
    name and/or path reconciled, so a label rename published through git is
    reflected locally after a sync."""
    existing = conn.execute(
        "SELECT name, path FROM projects WHERE id = ?", (project_id,)
    ).fetchone()

    if existing is None:
        conn.execute(
            "INSERT INTO projects (id, name, path) VALUES (?, ?, ?)",
            (project_id, name, str(path)),
        )
        conn.commit()
        return "registered"

    new_path = str(path)
    name_changed = existing["name"] != name
    path_changed = existing["path"] != new_path

    if not name_changed and not path_changed:
        return "already registered"

    if name_changed:
        conn.execute(
            "UPDATE projects SET name = ?, path = ? WHERE id = ?",
            (name, new_path, project_id),
        )
    else:
        conn.execute(
            "UPDATE projects SET path = ? WHERE id = ?",
            (new_path, project_id),
        )
    conn.commit()

    if name_changed and path_changed:
        return "updated"
    return "renamed" if name_changed else "moved"


def list_projects(conn) -> list:
    return conn.execute("SELECT id, name, path, created_at FROM projects ORDER BY created_at DESC").fetchall()


def get_project_by_id(conn, project_id: str):
    return conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()


def get_project_by_name(conn, name: str):
    return conn.execute("SELECT id, name, path FROM projects WHERE name = ?", (name,)).fetchone()

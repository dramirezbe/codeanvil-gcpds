"""Project sync — register a cloned/moved project from its manifest."""

from pathlib import Path

import yaml

from codeanvil.config.logger import get_logger
from codeanvil.config.paths import DB_PATH, find_manifest
from codeanvil.db.projects import sync_project
from codeanvil.db.utils import connect_db

log = get_logger(__name__)


def run_sync(project_dir: Path) -> tuple[str, dict]:
    """Full sync: read manifest, migrate .provenance if needed, upsert DB.
    Returns (action, manifest_data)."""
    manifest = find_manifest(project_dir)
    if manifest is None:
        raise FileNotFoundError(f"no .codeanvil/project.yaml found under {project_dir}")
    data = yaml.safe_load(manifest.read_text(encoding="utf-8"))
    # find_manifest may have walked up — sync the tree that owns the manifest
    project_root = manifest.parent.parent
    _migrate_provenance(project_root)
    conn = connect_db(DB_PATH)
    try:
        action = sync_project(conn, data["id"], data["name"], project_root.resolve())
    finally:
        conn.close()
    return action, data


def _migrate_provenance(project_dir: Path) -> None:
    """Pre-release migration: .provenance/ -> .codeanvil/custody/.

    Migrates when custody/ is missing OR empty — a re-scaffold creates an
    empty custody/ that would otherwise orphan .provenance/ forever.
    Never overwrites a non-empty custody/."""
    old = project_dir / ".provenance"
    new = project_dir / ".codeanvil" / "custody"
    if not old.is_dir():
        return
    if new.is_dir() and any(new.iterdir()):
        log.warning("%s is not empty — leaving %s in place", new, old)
        return
    new.parent.mkdir(parents=True, exist_ok=True)
    if new.is_dir():
        new.rmdir()  # empty — rename cannot replace it portably
    old.rename(new)
    log.info("migrated .provenance/ -> .codeanvil/custody/")

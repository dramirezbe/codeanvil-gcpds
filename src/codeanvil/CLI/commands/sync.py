"""`codeanvil sync` — register or move a cloned project in the local DB."""

import sys
from pathlib import Path

from codeanvil.config.logger import get_logger
from codeanvil.config.paths import DB_PATH, find_manifest
from codeanvil.db.schema import db_exists

log = get_logger(__name__)


def cmd_sync() -> None:
    from codeanvil.init.sync import run_sync

    if not db_exists(DB_PATH):
        log.error("not initialized — run 'codeanvil init' first")
        sys.exit(1)

    manifest = find_manifest(Path.cwd())
    if manifest is None:
        log.error("no .codeanvil/project.yaml found (searched up from cwd)")
        sys.exit(1)
    project_dir = manifest.parent.parent
    action, data = run_sync(project_dir)
    short_id = data["id"][:8]
    print(f"Synced: {data['name']} ({short_id}) → {project_dir.resolve()}  [{action}]")

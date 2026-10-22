"""`codeanvil list` — show every registered project."""

import sys

from codeanvil.config.logger import get_logger
from codeanvil.config.paths import DB_PATH
from codeanvil.db.projects import list_projects
from codeanvil.db.schema import db_exists
from codeanvil.db.utils import connect_db

log = get_logger(__name__)


def cmd_list() -> None:
    if not db_exists(DB_PATH):
        log.error("not initialized — run 'codeanvil init' first")
        sys.exit(1)

    conn = connect_db(DB_PATH)
    rows = list_projects(conn)
    conn.close()

    if not rows:
        print("No projects found.")
        return
    for row in rows:
        # Pre-refactor DBs used INTEGER ids — coerce before slicing.
        # `name` is the human label; `path` ends with the project folder.
        print(f"  [{str(row['id'])[:8]}] {row['name']}  —  {row['path']}  ({row['created_at']})")

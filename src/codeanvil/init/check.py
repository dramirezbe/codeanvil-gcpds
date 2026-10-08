from pathlib import Path

from codeanvil.config.logger import get_logger
from codeanvil.config.paths import WORKDIR, DB_PATH
from codeanvil.db.schema import db_exists
from codeanvil.db.utils import health_db

log = get_logger(__name__)


def preflight() -> bool:
    ok = True

    if not WORKDIR.exists():
        log.warning("workdir %s does not exist (will be created on init)", WORKDIR)
        ok = False

    if not db_exists(DB_PATH):
        log.warning("database not found at %s (will be created on init)", DB_PATH)
        ok = False
    elif not health_db(DB_PATH):
        log.error("database at %s is not healthy", DB_PATH)
        ok = False

    return ok


def check_project_path(path: Path) -> bool:
    if path.exists() and any(path.iterdir()):
        log.error("target path %s already exists and is not empty", path)
        return False
    return True

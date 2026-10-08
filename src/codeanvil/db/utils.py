import sqlite3
from pathlib import Path

from codeanvil.config.logger import get_logger

log = get_logger(__name__)


def connect_db(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    log.debug("connected to %s", db_path)
    return conn


def health_db(db_path: Path) -> bool:
    try:
        conn = connect_db(db_path)
        conn.execute("SELECT 1")
        conn.close()
        return True
    except sqlite3.Error as exc:
        log.error("db health check failed: %s", exc)
        return False

"""`codeanvil init` — create the workdir, the database and the methodology runtime;
optionally install MCP servers."""

import sys

from codeanvil.config.logger import get_logger
from codeanvil.config.paths import DB_PATH, ensure_dirs
from codeanvil.db.schema import create_schema, db_exists, recreate_if_legacy
from codeanvil.db.utils import connect_db
from codeanvil.init.ui import UISetupError, prepare_ui

log = get_logger(__name__)


def cmd_init(mcp_servers: list[str] | None = None) -> None:
    try:
        prepare_ui()
    except UISetupError as exc:
        log.error("%s", exc)
        raise SystemExit(1) from exc
    ensure_dirs()
    recreate_if_legacy(DB_PATH)
    if not db_exists(DB_PATH):
        conn = connect_db(DB_PATH)
        create_schema(conn)
        conn.close()
        log.info("CodeAnvil initialized")
    else:
        log.info("already initialized")

    from codeanvil.init.runtime import RuntimeSetupError, sync
    try:
        sync()
    except RuntimeSetupError as exc:
        log.error("%s", exc)
        sys.exit(1)

    log.info("UI ready — run 'codeanvil ui'")

    if mcp_servers:
        from codeanvil.CLI.commands.mcp import cmd_mcp
        cmd_mcp("add", mcp_servers)

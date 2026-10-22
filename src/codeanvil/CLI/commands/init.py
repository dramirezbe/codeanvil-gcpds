"""`codeanvil init` — create the workdir and database, optionally install MCP servers."""

import sys

from codeanvil.config.logger import get_logger
from codeanvil.config.paths import DB_PATH, ensure_dirs
from codeanvil.db.schema import create_schema, db_exists, recreate_if_legacy
from codeanvil.db.utils import connect_db

log = get_logger(__name__)


def cmd_init(mcp_servers: list[str] | None = None) -> None:
    ensure_dirs()
    recreate_if_legacy(DB_PATH)
    if not db_exists(DB_PATH):
        conn = connect_db(DB_PATH)
        create_schema(conn)
        conn.close()
        log.info("CodeAnvil initialized")
    else:
        log.info("already initialized")

    if mcp_servers:
        from codeanvil.config.paths import CONFIG
        from codeanvil.init.mcp import install_mcp_server
        available = CONFIG.get("mcp_servers", {})
        for name in mcp_servers:
            if name not in available:
                log.error("unknown MCP server '%s' — available: %s",
                          name, ", ".join(available))
                sys.exit(1)
            install_mcp_server(name)

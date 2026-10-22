"""`codeanvil create` — scaffold and register a project."""

import sys
from pathlib import Path

from codeanvil.config.logger import get_logger
from codeanvil.config.paths import DB_PATH
from codeanvil.db.projects import register_project
from codeanvil.db.utils import connect_db
from codeanvil.init.check import preflight
from codeanvil.init.create import read_manifest_id, scaffold_project, write_project_manifest

log = get_logger(__name__)


def cmd_create(name: str, path: Path, mcp_servers: list[str] | None = None) -> None:
    if not preflight():
        log.error("preflight failed — run 'codeanvil init' first")
        sys.exit(1)

    if mcp_servers:
        from codeanvil.config.paths import CONFIG
        from codeanvil.init.mcp import is_mcp_installed
        available = CONFIG.get("mcp_servers", {})
        for srv in mcp_servers:
            if srv not in available:
                log.error("unknown MCP server '%s' — available: %s",
                          srv, ", ".join(available))
                sys.exit(1)
            if not is_mcp_installed(srv):
                log.error("MCP server '%s' not installed — run 'codeanvil init --mcp %s' first",
                          srv, srv)
                sys.exit(1)

    from codeanvil.config.identity import generate_uuidv7

    conn = connect_db(DB_PATH)
    project_dir = scaffold_project(name, path, mcp_servers=mcp_servers or None)
    # Re-scaffold keeps the committed identity: reuse the manifest UUID when
    # present so the DB never gets a stale duplicate row and the manifest is
    # never rewritten with a fresh UUID.
    project_id = read_manifest_id(project_dir) or generate_uuidv7()
    register_project(conn, project_id, name, project_dir)
    write_project_manifest(project_dir, project_id, name)
    conn.close()

import argparse
import sys
from pathlib import Path

from codeanvil.config.logger import get_logger
from codeanvil.config.paths import DB_PATH, ensure_dirs
from codeanvil.db.schema import db_exists, create_schema
from codeanvil.db.utils import connect_db
from codeanvil.init.check import preflight, check_project_path
from codeanvil.db.projects import get_project_by_name, list_projects, register_project
from codeanvil.init.create import scaffold_project

log = get_logger(__name__)


def argparser() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="codeanvil",
        description=(
            "CodeAnvil — V-SIL methodology harness.\n"
            "\n"
            "Scaffolds verified-prototype projects on COTS hardware using the\n"
            "V-SIL pipeline: Ground Truth (GT) documents define the contract,\n"
            "deterministic and agent-driven gates validate each stage.\n"
            "\n"
            "Typical workflow:\n"
            "  1. codeanvil init                  Set up ~/.codeanvil/ and database\n"
            "  2. codeanvil create myproj          Scaffold project in current directory\n"
            "     codeanvil create myproj -p /tmp  ...or in a specific path\n"
            "  3. Fill in the GT files              G0_SRS.md, G0_HCS.md\n"
            "  4. codeanvil status myproj           Check session and gate progress"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "GT files (Ground Truth):\n"
            "  G0_SRS.md            System Requirements Specification (IEEE 29148)\n"
            "  G0_HCS.md            Hardware Constraints Specification (design constraints)\n"
            "\n"
            "Gates:\n"
            "  G0  Deterministic structural validation of GT files (no AI)\n"
            "  G1+ Agent-driven design, implementation, and verification gates\n"
            "\n"
            "Config and DB stored at ~/.codeanvil/ — projects live anywhere."
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True, title="commands")

    init_parser = sub.add_parser(
        "init",
        help="Initialize CodeAnvil workdir and database",
        description="Creates ~/.codeanvil/ directory structure and the SQLite database. Safe to re-run.",
    )
    init_parser.add_argument(
        "--mcp",
        action="append",
        default=[],
        dest="mcp_servers",
        metavar="SERVER",
        help="Install an MCP server (e.g. marconi). Repeatable.",
    )

    create = sub.add_parser(
        "create",
        help="Scaffold a new project from GT templates",
        description=(
            "Creates a new project directory at the given path (default: current\n"
            "directory) with GT document templates and skill definitions copied\n"
            "from the methodology templates. Registers the project in the database.\n"
            "\n"
            "Projects live wherever you want — only the DB stays in ~/.codeanvil/."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    create.add_argument("name", help="Project name (used as directory name and DB identifier)")
    create.add_argument(
        "-p", "--path",
        type=Path,
        default=Path.cwd(),
        help="Parent directory to scaffold the project in (default: current directory)",
    )
    create.add_argument(
        "--mcp",
        action="append",
        default=[],
        dest="mcp_servers",
        metavar="SERVER",
        help="Include an MCP server (e.g. marconi). Repeatable.",
    )

    sub.add_parser(
        "list",
        help="List all registered projects",
        description="Shows all projects with their ID, name, path, and creation date.",
    )

    status = sub.add_parser(
        "status",
        help="Show sessions and gate progress for a project",
        description="Displays all sessions for the given project, including current gate and status.",
    )
    status.add_argument("name", help="Name of the project to inspect")

    return parser.parse_args()


def cmd_init(mcp_servers: list[str] | None = None) -> None:
    ensure_dirs()
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

    conn = connect_db(DB_PATH)
    project_dir = scaffold_project(name, path, mcp_servers=mcp_servers or None)
    register_project(conn, name, project_dir)
    conn.close()


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
        print(f"  [{row['id']}] {row['name']}  —  {row['path']}  ({row['created_at']})")


def cmd_status(name: str) -> None:
    if not db_exists(DB_PATH):
        log.error("not initialized — run 'codeanvil init' first")
        sys.exit(1)

    conn = connect_db(DB_PATH)
    project = get_project_by_name(conn, name)
    if not project:
        log.error("project '%s' not found", name)
        sys.exit(1)

    from codeanvil.db.sessions import list_sessions
    sessions = list_sessions(conn, project["id"])
    conn.close()

    if not sessions:
        print(f"No sessions for project '{name}'.")
        return
    for s in sessions:
        print(f"  session {s['id']}  gate={s['current_gate']}  status={s['status']}  ({s['updated_at']})")


def choose_option(args: argparse.Namespace) -> None:
    match args.command:
        case "init":
            cmd_init(mcp_servers=args.mcp_servers or None)
        case "create":
            cmd_create(args.name, args.path, mcp_servers=args.mcp_servers or None)
        case "list":
            cmd_list()
        case "status":
            cmd_status(args.name)


def main() -> None:
    """Console-script entry point (`codeanvil ...`)."""
    choose_option(argparser())


if __name__ == "__main__":
    main()

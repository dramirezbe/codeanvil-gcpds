import argparse
import re
import sys
from pathlib import Path

import yaml

from codeanvil.config.logger import get_logger
from codeanvil.config.paths import DB_PATH, PROJECT_REPORT, ensure_dirs, find_manifest
from codeanvil.db.schema import create_schema, db_exists, recreate_if_legacy
from codeanvil.db.utils import connect_db
from codeanvil.init.check import preflight
from codeanvil.db.projects import (
    get_project_by_id,
    get_project_by_name,
    list_projects,
    register_project,
    sync_project,
)
from codeanvil.init.create import read_manifest_id, scaffold_project, write_project_manifest

log = get_logger(__name__)

# Gate report filenames: <gate>_<machine-timestamp>.md (e.g. G0_2026-10-21_16-23-45-123.md)
_REPORT_RE = re.compile(r"^(?P<gate>.+)_(?P<ts>\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}-\d{3})\.md$")


def argparser() -> argparse.Namespace:
    from codeanvil import __version__

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
            "  1. codeanvil init                  Set up ~/.codeanvil-config/ and database\n"
            "  2. codeanvil create myproj          Scaffold project in current directory\n"
            "     codeanvil create myproj -p /tmp  ...or in a specific path\n"
            "  3. Fill in the GT files              G0_SRS.md, G0_HCS.md\n"
            "  4. codeanvil status myproj           Check gate progress (or 'status' inside a project)"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("-v", "--version", action="version", version=f"%(prog)s {__version__}")
    parser.epilog = (
            "GT files (Ground Truth):\n"
            "  G0_SRS.md            System Requirements Specification (IEEE 29148)\n"
            "  G0_HCS.md            Hardware Constraints Specification (design constraints)\n"
            "\n"
            "Gates:\n"
            "  G0  Deterministic structural validation of GT files (no AI)\n"
            "  G1+ Agent-driven design, implementation, and verification gates\n"
            "\n"
            "Config and DB stored at ~/.codeanvil-config/ — projects live anywhere."
        )
    sub = parser.add_subparsers(dest="command", required=True, title="commands")

    init_parser = sub.add_parser(
        "init",
        help="Initialize CodeAnvil workdir and database",
        description="Creates ~/.codeanvil-config/ directory structure and the SQLite database. Safe to re-run.",
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
            "Projects live wherever you want — only the DB stays in ~/.codeanvil-config/."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    create.add_argument("name", help="Project name (used as directory name and DB label)")
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
        description="Shows all projects with their short ID, name, path, and creation date.",
    )

    sub.add_parser(
        "sync",
        help="Register or update a cloned project in the local DB",
        description=(
            "Reads .codeanvil/project.yaml from the current directory (or a parent),\n"
            "then registers the project locally or updates its path if it moved.\n"
            "Use after cloning a repo that contains a scaffolded project."
        ),
    )

    status = sub.add_parser(
        "status",
        help="Show gate progress for a project",
        description=(
            "Displays project identity and the latest gate report per gate.\n"
            "With no argument, reads from the project found in the current\n"
            "directory (auto-registers it if needed); with a name, looks up\n"
            "the project path in the database."
        ),
    )
    status.add_argument("name", nargs="?", default=None, help="Name of the project to inspect (default: current directory)")

    now_parser = sub.add_parser(
        "now",
        help="Print the current system timestamp",
        description="Prints a human-readable timestamp with millisecond precision in the configured timezone.",
    )
    now_parser.add_argument(
        "--tz",
        default=None,
        metavar="TIMEZONE",
        help="Override timezone (e.g. UTC, US/Eastern). Default: config or UTC.",
    )
    now_parser.add_argument(
        "--machine",
        action="store_true",
        help="Filename-safe format (no colons or spaces)",
    )

    return parser.parse_args()


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
        print(f"  [{str(row['id'])[:8]}] {row['name']}  —  {row['path']}  ({row['created_at']})")


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


def _latest_reports(report_dir: Path) -> dict[str, str]:
    """Latest report filename per gate, ordered by the machine timestamp."""
    latest: dict[str, str] = {}
    latest_ts: dict[str, str] = {}
    if not report_dir.is_dir():
        return latest
    for path in report_dir.glob("*.md"):
        match = _REPORT_RE.match(path.name)
        if not match:
            continue
        gate = match.group("gate")
        ts = match.group("ts")
        if gate not in latest_ts or ts > latest_ts[gate]:
            latest_ts[gate] = ts
            latest[gate] = path.name
    return latest


def cmd_status(name: str | None = None) -> None:
    if not db_exists(DB_PATH):
        log.error("not initialized — run 'codeanvil init' first")
        sys.exit(1)

    conn = connect_db(DB_PATH)
    try:
        project_dir: Path | None = None
        identity: dict | None = None

        if name is not None:
            project = get_project_by_name(conn, name)
            if not project:
                log.error("project '%s' not found", name)
                sys.exit(1)
            project_dir = Path(project["path"])
            identity = {"id": project["id"], "name": project["name"]}
            manifest = find_manifest(project_dir)
            # find_manifest walks up — a parent dir's manifest must not
            # hijack identity when the recorded project path is stale.
            if manifest is not None and manifest.parent.parent.resolve() == project_dir.resolve():
                try:
                    identity = yaml.safe_load(manifest.read_text(encoding="utf-8"))
                except yaml.YAMLError:
                    log.warning("cannot parse %s — using DB identity", manifest)
        else:
            manifest = find_manifest(Path.cwd())
            if manifest is None:
                log.error("no .codeanvil/project.yaml found (searched up from cwd) and no project name given")
                sys.exit(1)
            project_dir = manifest.parent.parent
            try:
                identity = yaml.safe_load(manifest.read_text(encoding="utf-8"))
            except yaml.YAMLError:
                log.error("cannot parse %s", manifest)
                sys.exit(1)
            if not isinstance(identity, dict) or "id" not in identity or "name" not in identity:
                log.error("%s is not a valid project manifest (missing id/name)", manifest)
                sys.exit(1)
            # Agents run status constantly — auto-register a manifest that
            # isn't in the DB yet instead of demanding a separate sync.
            existing = get_project_by_id(conn, identity["id"])
            if existing is None:
                sync_project(conn, identity["id"], identity["name"], project_dir.resolve())

        if not project_dir or not identity:
            log.error("could not resolve project")
            sys.exit(1)

        print(f"Project: {identity['name']} ({identity['id']})")
        print(f"Path:    {project_dir.resolve()}")

        latest = _latest_reports(project_dir / PROJECT_REPORT)
        if not latest:
            print("Reports: none yet (.codeanvil/report/ is empty)")
            return
        print("Reports (latest per gate):")
        for gate in sorted(latest):
            print(f"  {gate}: {latest[gate]}")
    finally:
        conn.close()


def cmd_now(tz: str | None = None, machine: bool = False) -> None:
    from codeanvil.config.time import format_timestamp, format_timestamp_machine
    if machine:
        print(format_timestamp_machine(tz_name=tz))
    else:
        print(format_timestamp(tz_name=tz))


def choose_option(args: argparse.Namespace) -> None:
    match args.command:
        case "init":
            cmd_init(mcp_servers=args.mcp_servers or None)
        case "create":
            cmd_create(args.name, args.path, mcp_servers=args.mcp_servers or None)
        case "list":
            cmd_list()
        case "sync":
            cmd_sync()
        case "status":
            cmd_status(args.name)
        case "now":
            cmd_now(tz=args.tz, machine=args.machine)


def main() -> None:
    """Console-script entry point (`codeanvil ...`)."""
    choose_option(argparser())


if __name__ == "__main__":
    main()

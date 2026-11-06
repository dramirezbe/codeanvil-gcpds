"""Argument definitions for the `codeanvil` console script.

Pure argument definition — no command logic lives here. `argparser()` also
returns the parsed namespace so `main()` stays a thin dispatch.
"""

import argparse
from collections.abc import Sequence
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    """Build the full `codeanvil` parser (subcommands included)."""
    from codeanvil import __version__
    from codeanvil.config.paths import CONFIG

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
            "  2. codeanvil create                 Interactive prompts: project and folder name\n"
            "     codeanvil create myproj          ...or non-interactive, legacy positional name\n"
            "     codeanvil create --name 'My Lab' ...or flags for agents and scripts (no TUI)\n"
            "  3. Write the Build Package           GT/build_package.md (S0 normalises it into the GT pair)\n"
            "  4. codeanvil status myproj           Check gate progress (or 'status' inside a project)"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("-v", "--version", action="version", version=f"%(prog)s {__version__}")
    parser.epilog = (
            "GT files (Ground Truth):\n"
            "  build_package.md     Your Build Package (the only input you write)\n"
            "  G0_StRS.md           Stakeholder Requirements Specification (IEEE 29148 §9.4)\n"
            "  G0_SyRS.md           System Requirements Specification (IEEE 29148 §9.5)\n"
            "\n"
            "Flow (RFD can be raised from any stage):\n"
            "  S0 -> G0 -> S1 -> G1 -> S2 -> G2\n"
            "  S0  Normalise the Build Package into the GT pair\n"
            "  G0  Deterministic structural validation of the GT pair + human Gate H\n"
            "  S1  Design of layered services    G1  Human design review\n"
            "  S2, G2  Implementation and verification (not available yet)\n"
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
            "With no name given, an interactive prompt asks for the project name\n"
            "(human label) and the folder name (default: derived snake_case).\n"
            "Use --name (and optionally --folder) to skip the prompts — required\n"
            "when stdin is not a terminal (agents, scripts, CI).\n"
            "\n"
            "Projects live wherever you want — only the DB stays in ~/.codeanvil-config/."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    create.add_argument(
        "name",
        nargs="?",
        default=None,
        help="Project name, also used as folder name (deprecated: use --name)",
    )
    create.add_argument(
        "--name",
        dest="project_name",
        default=None,
        metavar="LABEL",
        help="Human-readable project name (e.g. 'My SDR Lab'). Skips the interactive prompts.",
    )
    create.add_argument(
        "--folder",
        dest="folder",
        default=None,
        metavar="DIR",
        help="Folder to create (default: derived from --name). Requires --name.",
    )
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
        help="Show stage and gate progress for a project",
        description=(
            "Displays project identity and the latest report per stage and gate, in flow\n"
            "order, marking delivered stages, stale reports and closed cycles.\n"
            "With no argument, reads from the project found in the current\n"
            "directory (auto-registers it if needed); with a name, looks up\n"
            "the project path in the database."
        ),
    )
    status.add_argument("name", nargs="?", default=None, help="Name of the project to inspect (default: current directory)")

    backup = sub.add_parser(
        "backup",
        help="Save a stage's working artifacts before a skill overwrites them",
        description=(
            "Copies the files a stage overwrites into .codeanvil/backups/, with a\n"
            "MANIFEST.yaml holding each source path and SHA-256. Skills run it before\n"
            "rewriting an artifact. It only copies and hashes: it never decides or\n"
            "advances a gate. A stage with nothing on disk prints 'nothing to back up'."
        ),
    )
    backup.add_argument(
        "stage",
        choices=["S0", "S1", "S2", "G2"],
        help="Stage whose artifacts to back up",
    )

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

    sandbox = sub.add_parser(
        "sandbox",
        help="Launch an agent isolated to project-local settings",
        description=(
            "Starts an AI coding agent inside the current project with only\n"
            "project-local settings visible: AGENTS.md, .agents/skills/, and\n"
            "the GT files. Global skills, MCP servers, extensions, and memory\n"
            "are disabled — no state to revert (ephemeral). Run from inside\n"
            "a scaffolded project."
        ),
    )
    sandbox.add_argument(
        "agent",
        choices=sorted(CONFIG.get("sandbox_agents", {})),
        help="Agent to launch in the sandbox",
    )

    sub.add_parser(
        "upgrade",
        help="Upgrade codeanvil to the latest version from GitHub",
        description="Reinstalls codeanvil from the main branch using uv. Works on Linux, macOS and Windows.",
    )

    return parser


def argparser(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments (defaults to `sys.argv[1:]`)."""
    return build_parser().parse_args(argv)

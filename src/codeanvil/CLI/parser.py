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
            "  3. Write the Build Package           .codeanvil/GT/build_package.md (S0 normalises it into the GT pair)\n"
            "  4. codeanvil status myproj           Check gate progress (or 'status' inside a project)"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("-v", "--version", action="version", version=f"%(prog)s {__version__}")
    parser.epilog = (
            "GT files (Ground Truth, under .codeanvil/GT/):\n"
            "  build_package.md     Your Build Package (the only input you write)\n"
            "  StRS.md              Stakeholder Requirements Specification (IEEE 29148 §9.4)\n"
            "  SyRS.md              System Requirements Specification (IEEE 29148 §9.5)\n"
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
        help="Install an MCP server (alias of codeanvil mcp add). Repeatable.",
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
        choices=list(CONFIG.get("backup_targets", {})),
        help="Stage whose artifacts to back up",
    )

    runtime = sub.add_parser(
        "runtime",
        help="Manage the global methodology runtime (one venv for every project)",
        description=(
            "The methodology runtime is one uv venv under ~/.codeanvil-config/runtime/,\n"
            "shared by every project. Skill scripts run on it with 'codeanvil python'.\n"
            "Packages you add live in runtime/user.yaml and survive 'codeanvil upgrade'."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    runtime_sub = runtime.add_subparsers(dest="action", required=True, title="actions")
    runtime_sub.add_parser("sync", help="Create or update the runtime venv from the shipped spec + your packages")
    for action, verb in (("add", "Add"), ("remove", "Remove")):
        action_parser = runtime_sub.add_parser(action, help=f"{verb} packages, then sync")
        action_parser.add_argument("packages", nargs="+", metavar="PACKAGE", help="Requirement, e.g. torch or 'numpy>=2'")
    runtime_sub.add_parser("list", help="Base and user packages with their installed versions")
    runtime_sub.add_parser("path", help="Print the runtime's Python interpreter")

    python_parser = sub.add_parser(
        "python",
        help="Run a script on the methodology runtime",
        description=(
            "Runs <script> with the runtime's Python (-I) from the project root.\n"
            "A script under .agents/skills/<skill>/ is checked against the skill's\n"
            "metadata.runtime packages first. Every argument after the script is\n"
            "passed to it unchanged."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    python_parser.add_argument("script", help="Path to the Python script")
    python_parser.add_argument("args", nargs=argparse.REMAINDER, help="Arguments for the script")

    servers = sorted(CONFIG.get("mcp_servers", {}))
    mcp_parser = sub.add_parser(
        "mcp",
        help="Install, check and launch MCP servers (one pinned venv per server)",
        description=(
            "MCP servers live under ~/.codeanvil-config/mcp/<name>/, pinned to the\n"
            "ref in config.yaml. Projects call them through 'codeanvil mcp run <name>',\n"
            "so their configs hold no absolute path. enable/disable run inside a project."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    mcp_sub = mcp_parser.add_subparsers(dest="action", required=True, title="actions")
    add_p = mcp_sub.add_parser("add", help="Clone, pin, build the venv and probe system packages")
    add_p.add_argument("names", nargs="+", choices=servers, metavar="SERVER")
    update_p = mcp_sub.add_parser("update", help="Re-pin to the configured ref and rebuild a stale venv (default: all installed)")
    update_p.add_argument("names", nargs="*", choices=servers, metavar="SERVER")
    remove_p = mcp_sub.add_parser("remove", help="Delete an installed server (refuses while projects use it)")
    remove_p.add_argument("names", nargs=1, choices=servers, metavar="SERVER")
    remove_p.add_argument("--yes", action="store_true", help="Remove even if projects still use it")
    mcp_sub.add_parser("list", help="Configured servers, installed or not, and their pinned ref")
    doctor_p = mcp_sub.add_parser("doctor", help="Check PATH tools, pin, venv and system packages (default: all)")
    doctor_p.add_argument("names", nargs="*", choices=servers, metavar="SERVER")
    run_p = mcp_sub.add_parser("run", help="Start a server over stdio (what agent configs call)")
    run_p.add_argument("names", nargs=1, choices=servers, metavar="SERVER")
    for action, verb in (("enable", "Wire"), ("disable", "Unwire")):
        toggle = mcp_sub.add_parser(action, help=f"{verb} a server in the current project (skills, configs, AGENTS.md)")
        toggle.add_argument("names", nargs=1, choices=servers, metavar="SERVER")

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

    telemetry = sub.add_parser(
        "telemetry",
        help="Sample host and process telemetry into a JSON-lines file",
        description="Samples CPU, memory and temperature of the verification process tree "
        "once per interval into a JSON-lines file. Runs until SIGINT/SIGTERM or --duration.",
    )
    telemetry.add_argument("--pid", type=int, default=None,
                           help="root of the process tree to measure (default: the parent process)")
    telemetry.add_argument("--output", type=Path, default=None,
                           help="output JSON-lines file (default: verification/telemetry/ under the cwd)")
    telemetry.add_argument("--interval", type=float, default=1.0,
                           help="seconds between samples (default: 1.0)")
    telemetry.add_argument("--duration", type=float, default=0.0,
                           help="seconds to sample; 0 runs until SIGINT or SIGTERM (default: 0)")
    telemetry.add_argument("--counters", type=Path, default=None,
                           help="JSON object written by the HAL or the service instrumentation")

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

    cred = sub.add_parser(
        "credential-setup",
        help="Bootstrap an HIL target's agent credentials and register it in the project",
        description=(
            "Generates the vsil_hil_mcp confined keys, bootstraps the remote target over SSH\n"
            "(locked-login agent user, NOPASSWD sudo, workspace, rrsync, the two pubkeys) and\n"
            "registers it under `targets:` in .codeanvil/project.yaml. Run from inside a\n"
            "project. The password is passed to the engine via env, never argv."
        ),
    )
    cred.add_argument("-u", "--user", required=True, help="existing admin (sudoer) user on the target (bootstrap only)")
    cred.add_argument("-p", "--password", default=None, help="admin SSH password; prompted securely if omitted (never logged)")
    cred.add_argument("-s", "--sudo-password", dest="sudo_password", default=None,
                      help="sudo password, only if it differs from the SSH password (default: reuse it)")
    cred.add_argument("-i", "--ip", "-ip", dest="ip", required=True, help="target IP or hostname")
    cred.add_argument("-w", "--workspace", default="", help="agent workspace (default: /home/codeanvil-agent/workspace)")
    cred.add_argument("--port", type=int, default=22, help="SSH port (default: 22)")
    cred.add_argument("-t", "--target", default="", help="target name (default: derived from the IP)")
    cred.add_argument("--os", choices=["linux", "windows"], default="linux", help="target OS (default: linux)")

    sub.add_parser(
        "upgrade",
        help="Upgrade codeanvil to the latest version from GitHub",
        description="Reinstalls codeanvil from the main branch using uv. Works on Linux, macOS and Windows.",
    )

    return parser


def argparser(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments (defaults to `sys.argv[1:]`)."""
    return build_parser().parse_args(argv)

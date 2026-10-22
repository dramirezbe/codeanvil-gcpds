"""`codeanvil create` — resolve inputs, scaffold, and register a project."""

import sys
from collections.abc import Callable
from pathlib import Path

from codeanvil.config.logger import get_logger
from codeanvil.config.paths import DB_PATH
from codeanvil.db.projects import register_project
from codeanvil.db.utils import connect_db
from codeanvil.init.check import preflight
from codeanvil.init.create import read_manifest_id, scaffold_project, write_project_manifest

log = get_logger(__name__)


class CreateInputError(ValueError):
    """Invalid combination or value for `codeanvil create` inputs."""


def cmd_create(
    name: str | None,
    path: Path,
    mcp_servers: list[str] | None = None,
    *,
    project_name: str | None = None,
    folder: str | None = None,
) -> None:
    """Scaffold and register a project.

    `name` is the deprecated positional form (project name and folder).
    `project_name`/`folder` are the `--name`/`--folder` flags. With neither,
    an interactive prompt collects both.
    """
    try:
        inputs = resolve_create_inputs(name, project_name, folder, target=path)
    except CreateInputError as exc:
        log.error("%s", exc)
        sys.exit(1)

    if inputs is None:
        log.debug("cancelled — no project created")
        return

    label, folder_name = inputs

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
    try:
        project_dir = scaffold_project(label, folder_name, path, mcp_servers=mcp_servers or None)
        # Re-scaffold keeps the committed identity: reuse the manifest UUID when
        # present so the DB never gets a stale duplicate row and the manifest is
        # never rewritten with a fresh UUID.
        project_id = read_manifest_id(project_dir) or generate_uuidv7()
        register_project(conn, project_id, label, project_dir)
        write_project_manifest(project_dir, project_id, label)
    finally:
        conn.close()


def resolve_create_inputs(
    name: str | None,
    project_name: str | None,
    folder: str | None,
    *,
    target: Path | None = None,
    interactive: Callable[[Path], tuple[str, str] | None] | None = None,
) -> tuple[str, str] | None:
    """Resolve `(project_name, folder_name)` from the CLI inputs.

    Precedence:
      1. `--name` → flags (folder defaults to the derived snake_case name).
      2. positional `name` → legacy path, name is also the folder name.
      3. neither → interactive prompts.

    Returns None when the user cancels the interactive flow.
    Raises CreateInputError for invalid or ambiguous combinations.
    """
    if project_name is not None:
        if name is not None:
            raise CreateInputError(
                "cannot combine '--name' with a positional project name — use one or the other"
            )
        label = project_name.strip()
        if not label:
            raise CreateInputError("project name must not be empty")
        if folder is not None:
            return label, _validate_folder_name(folder)
        return label, _derive_folder_name(label)

    if folder is not None:
        raise CreateInputError("'--folder' requires '--name'")

    if name is not None:
        if not name.strip():
            raise CreateInputError("project name must not be empty")
        # Legacy positional path: no prompts, the name is the folder name.
        return name, name

    prompt = interactive or _prompt_interactive
    return prompt(Path.cwd() if target is None else Path(target))


def _derive_folder_name(project_name: str) -> str:
    from codeanvil.CLI.prompts import to_folder_name

    try:
        return to_folder_name(project_name)
    except ValueError as exc:
        raise CreateInputError(
            f"cannot derive a folder name from '{project_name}' — pass --folder"
        ) from exc


def _validate_folder_name(folder: str) -> str:
    folder_name = folder.strip()
    if not folder_name:
        raise CreateInputError("--folder must not be empty")
    return folder_name


def _prompt_interactive(target: Path) -> tuple[str, str] | None:
    """Run the TUI, surfacing a missing terminal as a create input error."""
    from codeanvil.CLI.prompts import NotATTYError, interactive_create

    try:
        return interactive_create(target)
    except NotATTYError as exc:
        raise CreateInputError(str(exc)) from exc

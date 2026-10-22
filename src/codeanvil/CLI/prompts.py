"""Interactive prompts for `codeanvil create`.

Vite-style flow built on beaupy (Rich-powered prompt widgets): project name,
folder name (defaulted to the derived snake_case form), then a confirmation.
Every prompt can be cancelled with Ctrl+C.
"""

import re
import sys
from pathlib import Path

import beaupy
from rich.console import Console

console = Console()

_HEADER = "CodeAnvil — create project"
_CANCELLED = "Cancelled — no project created."
_NOT_A_TTY = (
    "interactive prompts need a terminal — pass --name (and optionally --folder) "
    "to scaffold without prompts"
)

_FOLDER_SEPARATORS = re.compile(r"[\s\-]+")
_NOT_FOLDER_CHARS = re.compile(r"[^a-z0-9_]")
_REPEATED_UNDERSCORES = re.compile(r"_+")


class NotATTYError(RuntimeError):
    """Interactive prompts were requested but stdin is not a terminal."""


def to_folder_name(name: str) -> str:
    """Derive a snake_case folder name from a human-readable project name.

    Lowercases, turns spaces and hyphens into underscores, drops characters
    that are not alphanumeric or underscore, collapses repeated underscores,
    and trims leading/trailing underscores.

    Raises ValueError when nothing usable is left (empty or punctuation only).
    """
    folded = _NOT_FOLDER_CHARS.sub("", _FOLDER_SEPARATORS.sub("_", name.strip().lower()))
    folder = _REPEATED_UNDERSCORES.sub("_", folded).strip("_")
    if not folder:
        raise ValueError(f"cannot derive a folder name from {name!r}")
    return folder


def interactive_create(default_path: Path | None = None) -> tuple[str, str] | None:
    """Ask for project and folder names, then confirm.

    Returns `(project_name, folder_name)`, or None when the user cancels
    (Ctrl+C, Esc, or answering No). Raises NotATTYError when stdin is not a
    terminal, since the prompts cannot read keys from a pipe.
    """
    if not _stdin_is_tty():
        raise NotATTYError(_NOT_A_TTY)

    target = Path.cwd() if default_path is None else Path(default_path)

    console.print()
    console.print(f"  [bold]{_HEADER}[/bold]")
    console.print()

    try:
        project_name = _ask_project_name()
        if project_name is None:
            return _cancel()

        folder_name = _ask_folder_name(to_folder_name(project_name))
        if folder_name is None:
            return _cancel()

        console.print()
        console.print(f"  Project: {project_name}")
        console.print(f"  Folder:  {folder_name}  →  {target / folder_name}")
        console.print()
        if not beaupy.confirm(f"Create project '{project_name}'?"):
            return _cancel()
    except (KeyboardInterrupt, beaupy.Abort):
        return _cancel()

    return project_name, folder_name


def _ask_project_name() -> str | None:
    """Prompt for the human-readable project name (required, any case)."""
    while True:
        raw = beaupy.prompt(
            "Project name",
            validator=_non_empty,
            raise_validation_fail=False,
        )
        if raw is None:
            return None
        project_name = raw.strip()
        if not project_name:
            continue
        try:
            to_folder_name(project_name)
        except ValueError as exc:
            console.print(f"  [red]{exc}[/red]")
            continue
        return project_name


def _ask_folder_name(default: str) -> str | None:
    """Prompt for the folder name, pre-filled with the derived default."""
    raw = beaupy.prompt(
        "Folder name",
        initial_value=default,
        validator=_non_empty,
        raise_validation_fail=False,
    )
    if raw is None:
        return None
    return raw.strip() or default


def _non_empty(value: str) -> bool:
    return bool(value.strip())


def _stdin_is_tty() -> bool:
    isatty = getattr(sys.stdin, "isatty", None)
    return bool(isatty and isatty())


def _cancel() -> None:
    console.print(f"  {_CANCELLED}")
    return None

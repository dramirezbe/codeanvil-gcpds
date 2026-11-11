"""Remove a project registration, optionally deleting its local files."""

import sys

from codeanvil.config.paths import DB_PATH
from codeanvil.project_delete import ProjectDeleteError, delete_project, resolve_delete_target


def cmd_delete(project: str | None = None, remove_files: bool = False, yes: bool = False) -> None:
    """Preview the selected project and require confirmation before mutation."""
    try:
        target = resolve_delete_target(project, db_path=DB_PATH)
        print(f"Project: {target['name']}\nID: {target['id']}\nFolder: {target['path']}")
        if remove_files:
            print("Action: Permanently delete the project folder and all its contents, and remove its registration.")
        else:
            print("Action: Remove the project from the registry. Keep the project folder and all files.")

        if not yes:
            if not sys.stdin.isatty():
                raise ProjectDeleteError("Confirmation requires a terminal; pass --yes to proceed. No project was deleted.")
            try:
                answer = input("Delete project and files? [y/N]: " if remove_files else "Remove project registration? [y/N]: ")
            except (EOFError, KeyboardInterrupt):
                answer = ""
            if answer.strip().lower() not in {"y", "yes"}:
                print("Cancelled — no project was deleted.")
                return

        result = delete_project(target["id"], expected_path=target["path"], remove_files=remove_files, db_path=DB_PATH)
        if result["removed_files"]:
            print(f"Deleted project and folder: {result['project']['name']} → {result['project']['path']}")
        else:
            print(f"Removed project registration: {result['project']['name']} — project files kept at {result['project']['path']}")
    except ProjectDeleteError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

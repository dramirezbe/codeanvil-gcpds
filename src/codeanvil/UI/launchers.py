"""Local agent/editor discovery and launch helpers for the UI.

Registry commands are argv arrays so user-editable YAML never becomes shell
source. Install recipes are deliberately restricted to direct commands.
"""

from __future__ import annotations

import os
import platform
import shlex
import shutil
import subprocess
import sys
from importlib import resources
from pathlib import Path
from typing import Any

import yaml

from codeanvil.config.paths import WORKDIR


class LauncherError(ValueError):
    pass


def registry_path() -> Path:
    return WORKDIR / "launchers.yaml"


def _bundled_registry() -> dict[str, Any]:
    path = Path(str(resources.files("codeanvil.UI") / "launchers.yaml"))
    with path.open(encoding="utf-8") as stream:
        return yaml.safe_load(stream) or {}


def load_registry(path: Path | None = None) -> dict[str, dict[str, Any]]:
    """Read editable global registry, creating it from shipped defaults once."""
    target = path or registry_path()
    if not target.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(yaml.safe_dump(_bundled_registry(), sort_keys=False), encoding="utf-8")
    try:
        data = yaml.safe_load(target.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError) as exc:
        raise LauncherError(f"cannot read launcher registry {target}: {exc}") from exc
    launchers = data.get("launchers") if isinstance(data, dict) else None
    if not isinstance(launchers, dict):
        raise LauncherError("launcher registry must contain a 'launchers' mapping")
    for key, item in launchers.items():
        if not isinstance(item, dict) or item.get("kind") not in {"gui", "terminal"}:
            raise LauncherError(f"invalid launcher entry: {key}")
    return launchers


def _os_key() -> str:
    return {"Darwin": "darwin", "Windows": "windows"}.get(platform.system(), "linux")


def _argv(value: Any, project: Path) -> list[str]:
    if isinstance(value, str):
        # Strings are supported for hand-edited registries, but parsed without a shell.
        parts = shlex.split(value)
    elif isinstance(value, list) and all(isinstance(part, (str, int, float)) for part in value):
        parts = [str(part) for part in value]
    else:
        raise LauncherError("command must be a string or argv list")
    return [part.replace("{project}", str(project)) for part in parts]


def scan(path: Path | None = None) -> list[dict[str, Any]]:
    entries = load_registry(path)
    os_key = _os_key()
    result = []
    for key, item in entries.items():
        detect = item.get("detect", [])
        if isinstance(detect, dict):
            detect = detect.get("cmd", [])
        if isinstance(detect, str):
            detect = [detect]
        binary = str(detect[0]) if detect else ""
        result.append({"id": key, "label": item.get("label", key), "kind": item["kind"],
                       "icon": item.get("icon"), "installed": bool(binary and shutil.which(binary)),
                       "available": os_key in item.get("launch", {}) or "any" in item.get("launch", {})})
    return result


def launch(identifier: str, project: Path, path: Path | None = None) -> dict[str, Any]:
    entries = load_registry(path)
    item = entries.get(identifier)
    if item is None:
        raise LauncherError(f"unknown launcher: {identifier}")
    command = item.get("launch", {})
    command = command.get(_os_key(), command.get("any")) if isinstance(command, dict) else command
    argv = _argv(command, project.resolve())
    if not argv or not shutil.which(argv[0]):
        raise LauncherError(f"launcher is not installed: {identifier}")
    if item["kind"] == "terminal":
        return {"kind": "terminal", "cwd": str(project.resolve()), "argv": argv}
    process = subprocess.Popen(argv, cwd=project.resolve(), shell=False,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return {"kind": "gui", "pid": process.pid}


def install(identifier: str, path: Path | None = None) -> dict[str, Any]:
    entries = load_registry(path)
    item = entries.get(identifier)
    if item is None:
        raise LauncherError(f"unknown launcher: {identifier}")
    recipes = item.get("install", {})
    recipe = recipes.get(_os_key()) if isinstance(recipes, dict) else None
    if not recipe:
        return {"installed": False, "manual": True, "message": "Install manually; no recipe is configured for this OS."}
    argv = _argv(recipe, Path.cwd())
    if not argv or argv[0] in {"sudo", "doas", "su", "pkexec"} or any(
        token in {"|", "||", "&&", ";", ">", "<", "$(", "`"} for token in argv
    ):
        return {"installed": False, "manual": True, "message": "Recipe requires manual installation."}
    if _os_key() == "windows" and argv[0] != "winget":
        return {"installed": False, "manual": True, "message": "Windows installs use winget; install this app manually."}
    if not shutil.which(argv[0]):
        return {"installed": False, "manual": True, "message": f"Installer not found: {argv[0]}"}
    result = subprocess.run(argv, cwd=Path.home(), capture_output=True, text=True, shell=False)
    if result.returncode:
        return {"installed": False, "manual": True, "message": (result.stderr or result.stdout).strip()}
    return {"installed": True, "manual": False, "message": result.stdout.strip()}

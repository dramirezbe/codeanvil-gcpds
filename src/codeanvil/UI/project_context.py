"""Validated project identity for the UI's read and workflow adapters."""

import re
from pathlib import Path
from typing import Any

import yaml

from codeanvil.config.paths import find_manifest


class ProjectManifestError(ValueError):
    """The selected folder cannot supply a valid project identity."""


def project_context(start: Path) -> tuple[Path, dict[str, Any]] | None:
    """Find a project above an existing folder and validate its public identity.

    Reads only: selection does not register a project or change its cycle.
    """
    try:
        selected = start.expanduser().resolve()
    except (OSError, RuntimeError, ValueError) as exc:
        raise ProjectManifestError("Cannot resolve the selected project folder.") from exc
    if not selected.is_dir():
        raise ProjectManifestError("Choose an existing project folder.")
    try:
        manifest = find_manifest(selected)
    except (OSError, RuntimeError, ValueError) as exc:
        raise ProjectManifestError("Cannot resolve the project manifest.") from exc
    if manifest is None:
        return None
    root = manifest.parent.parent.resolve()
    try:
        inside = manifest.resolve().is_relative_to(root)
    except (OSError, RuntimeError, ValueError) as exc:
        raise ProjectManifestError("Cannot resolve the project manifest.") from exc
    if not inside:
        raise ProjectManifestError("The project manifest must stay inside its project folder.")
    try:
        identity = yaml.safe_load(manifest.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise ProjectManifestError("Cannot read .codeanvil/project.yaml as UTF-8 YAML.") from exc
    if not isinstance(identity, dict):
        raise ProjectManifestError("The project manifest must contain an id/name mapping.")
    for key in ("id", "name"):
        if not isinstance(identity.get(key), str) or not identity[key].strip():
            raise ProjectManifestError(f"The project manifest's {key} must be non-empty text.")
    cycle = identity.get("cycle")
    if "cycle" in identity and (
        not isinstance(cycle, str) or re.fullmatch(r"[A-Za-z0-9_-]+", cycle) is None
    ):
        raise ProjectManifestError("The project manifest's cycle must be a directory-safe name.")
    return root, identity


def project_summary(path: Path, identity: dict[str, Any]) -> dict[str, Any]:
    """Serialize the identity and its local root without leaking other config."""
    return {
        "id": identity["id"],
        "name": identity["name"],
        "path": str(path),
        "cycle": identity.get("cycle"),
    }

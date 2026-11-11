"""Prepare the UI shipped inside the global CodeAnvil installation."""

import importlib
from pathlib import Path

from codeanvil.UI.assets import UIAssetsError, validate_frontend
from codeanvil.UI.launchers import LauncherError, load_registry


class UISetupError(RuntimeError):
    """The installation cannot provide a complete UI."""


def prepare_ui(workdir: Path | None = None) -> Path:
    """Validate bundled UI/dependencies and seed editable launcher settings once."""
    from codeanvil.config.paths import WORKDIR

    try:
        for dependency in ("fastapi", "uvicorn", "httpx", "watchdog"):
            importlib.import_module(dependency)
        dist = Path(__file__).resolve().parents[1] / "UI" / "frontend" / "dist"
        validate_frontend(dist)
        load_registry((workdir if workdir is not None else WORKDIR) / "launchers.yaml")
    except (ImportError, OSError, UIAssetsError, LauncherError) as exc:
        raise UISetupError(f"UI setup failed: {exc}. Reinstall CodeAnvil to repair its global environment.") from exc
    return dist

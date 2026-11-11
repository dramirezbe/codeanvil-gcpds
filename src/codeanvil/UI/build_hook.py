"""Build and include the UI frontend in CodeAnvil distributions."""

from __future__ import annotations

import importlib.util
from pathlib import Path

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class CustomBuildHook(BuildHookInterface):
    """Require a complete prebuilt UI; never install Node tooling on consumers."""

    def initialize(self, version: str, build_data: dict[str, object]) -> None:
        frontend = Path(self.root) / "src" / "codeanvil" / "UI" / "frontend"
        # Load the stdlib-only validator directly: build isolation does not
        # install CodeAnvil or its runtime dependencies before building it.
        specification = importlib.util.spec_from_file_location("codeanvil_ui_assets", frontend.parent / "assets.py")
        module = importlib.util.module_from_spec(specification)
        specification.loader.exec_module(module)
        module.validate_frontend(frontend / "dist")

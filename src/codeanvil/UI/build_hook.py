"""Build and include the UI frontend in CodeAnvil distributions."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class CustomBuildHook(BuildHookInterface):
    """Compile the Vite app before Hatch collects wheel files."""

    def initialize(self, version: str, build_data: dict[str, object]) -> None:
        frontend = Path(self.root) / "src" / "codeanvil" / "UI" / "frontend"
        # The source distribution already carries the output produced by the
        # sdist hook. Rebuilding it in Hatch's temporary extraction would need
        # a second Node dependency install and can discard pnpm's virtual store.
        if (frontend / "dist" / "index.html").is_file():
            return
        pnpm = shutil.which("pnpm")
        if pnpm is None:
            raise RuntimeError("Building CodeAnvil requires pnpm; install it and rerun the package build.")
        subprocess.run([pnpm, "install", "--frozen-lockfile"], cwd=frontend, check=True)
        subprocess.run([pnpm, "build"], cwd=frontend, check=True)

"""`codeanvil sandbox` — launch an agent with project-local configuration."""

import shutil
import subprocess
import sys
from pathlib import Path

from codeanvil.config.logger import get_logger
from codeanvil.config.paths import find_manifest
from codeanvil.sandbox import SANDBOX_AGENTS, SandboxError, prepare_sandbox
from codeanvil.sandbox import _build_command as _sandbox_command

log = get_logger(__name__)


def _build_command(spec: dict, project_dir: Path | None = None) -> list[str]:
    """Retain the CLI helper's exit behavior around the shared recipe builder."""
    try:
        return _sandbox_command(spec, project_dir)
    except SandboxError as exc:
        log.error("%s", exc)
        sys.exit(1)


def cmd_sandbox(agent: str) -> None:
    """Run `codeanvil sandbox <agent>` — isolated agent session in this project."""
    manifest = find_manifest(Path.cwd())
    if manifest is None:
        log.error("not inside a scaffolded project — .codeanvil/project.yaml not found (searched up from cwd)")
        sys.exit(1)
    try:
        with prepare_sandbox(agent, manifest.parent.parent) as launch:
            if SANDBOX_AGENTS[agent].get("strategy", "native") == "native":
                sys.exit(subprocess.run(launch["argv"]).returncode)
            sys.exit(subprocess.run(launch["argv"], env=launch["env"]).returncode)
    except SandboxError as exc:
        log.error("%s", exc)
        sys.exit(1)

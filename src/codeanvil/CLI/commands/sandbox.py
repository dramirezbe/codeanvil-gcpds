"""`codeanvil sandbox` — launch an AI agent isolated to project-local settings.

Starts the named agent inside a scaffolded project with only AGENTS.md,
.agents/skills/, and the GT visible — no global skills, MCPs, extensions,
or memory. Recipes live in templates/config.yaml under `sandbox_agents`;
three strategies: native (flags only), xdg_redirect (empty XDG_CONFIG_HOME),
env_redirect (config-dir env override + auth files only).
"""

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from codeanvil.config.logger import get_logger
from codeanvil.config.paths import CONFIG, find_manifest

log = get_logger(__name__)

SANDBOX_AGENTS: dict[str, dict] = CONFIG.get("sandbox_agents", {})


def _pi_extension_dir() -> Path:
    """Pi installs extensions under ~/.pi/agent/npm/node_modules/<name>/src/."""
    return Path.home() / ".pi" / "agent" / "npm" / "node_modules"


def _resolve_required_extensions(names: list[str]) -> list[str]:
    """Locate required extension entrypoints (e.g. pi-claude-bridge).

    Exits with an error when a required extension is missing — launching
    without it would produce a half-isolated agent (Pi without model access).
    """
    paths: list[str] = []
    extension_root = _pi_extension_dir()
    for name in names:
        entry = extension_root / name / "src" / "index.ts"
        if not entry.is_file():
            log.error(
                "required extension '%s' not found at %s — install it first",
                name, entry,
            )
            sys.exit(1)
        paths.append(str(entry))
    return paths


def _build_command(spec: dict) -> list[str]:
    """Construct the agent launch argv from a sandbox_agents recipe."""
    args = list(spec.get("args", []))
    for ext_path in _resolve_required_extensions(spec.get("required_extensions", [])):
        args += ["-e", ext_path]
    return [spec["binary"]] + args


def _copy_auth_files(spec: dict, sandbox_dir: Path) -> None:
    """Seed the sandbox dir with identity files only (no config, skills, memory)."""
    source_dir = Path(str(spec.get("config_dir", ""))).expanduser()
    for name in spec.get("auth_files", []):
        src = source_dir / name
        if src.is_file():
            shutil.copy2(src, sandbox_dir / name)


def cmd_sandbox(agent: str) -> None:
    """Run `codeanvil sandbox <agent>` — isolated agent session in this project."""
    if find_manifest(Path.cwd()) is None:
        log.error("not inside a scaffolded project — .codeanvil/project.yaml not found (searched up from cwd)")
        sys.exit(1)

    spec = SANDBOX_AGENTS.get(agent)
    if spec is None:
        known = ", ".join(sorted(SANDBOX_AGENTS))
        log.error("unknown agent '%s' — known agents: %s", agent, known)
        sys.exit(1)

    binary = spec["binary"]
    if shutil.which(binary) is None:
        log.error("'%s' binary not found on PATH — install it first", binary)
        sys.exit(1)

    cmd = _build_command(spec)
    strategy = spec.get("strategy", "native")

    if strategy == "native":
        sys.exit(subprocess.run(cmd).returncode)

    env_var = spec["env_var"]
    sandbox_dir = Path(tempfile.mkdtemp(prefix="codeanvil-sandbox-"))
    try:
        if spec.get("auth_files"):
            _copy_auth_files(spec, sandbox_dir)
        env = {**os.environ, env_var: str(sandbox_dir)}
        sys.exit(subprocess.run(cmd, env=env).returncode)
    finally:
        shutil.rmtree(sandbox_dir, ignore_errors=True)

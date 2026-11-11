"""Project-local agent configuration for CLI and interactive terminal sessions.

This isolates agent configuration using the methodology's existing recipes; it
does not create an operating-system filesystem or process sandbox. Keep the
context open for the child's entire lifetime so redirected config survives until
the process exits. The parent environment and working directory never change.
"""

import os
import shutil
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, TypedDict

from codeanvil.config.paths import CONFIG

SANDBOX_AGENTS: dict[str, dict] = CONFIG.get("sandbox_agents", {})


class SandboxError(RuntimeError):
    """An agent's project-local launch could not be prepared."""


class SandboxLaunch(TypedDict):
    argv: list[str]
    env: dict[str, str]


def _build_command(spec: dict, project_dir: Path | None = None) -> list[str]:
    """Apply recipe flags, required Pi extensions and project MCP configuration."""
    args = list(spec.get("args", []))
    extension_root = Path.home() / ".pi/agent/npm/node_modules"
    for name in spec.get("required_extensions", []):
        entry = extension_root / name / "src/index.ts"
        if not entry.is_file():
            raise SandboxError(
                f"required extension '{name}' not found at {entry} — install it first"
            )
        args += ["-e", str(entry)]
    mcp_config = spec.get("project_mcp_config")
    if mcp_config and project_dir is not None:
        config_path = project_dir / mcp_config
        if config_path.is_file():
            args += ["--mcp-config", str(config_path)]
    return [spec["binary"]] + args


def _copy_auth_files(spec: dict, sandbox_dir: Path) -> None:
    """Copy only recipe-approved identity files; never copy global settings."""
    source_dir = Path(str(spec.get("config_dir", ""))).expanduser()
    for name in spec.get("auth_files", []):
        source = source_dir / name
        if source.is_file():
            shutil.copy2(source, sandbox_dir / name)


@contextmanager
def prepare_sandbox(agent: str, project: Path) -> Iterator[SandboxLaunch]:
    """Yield ``argv`` and a complete child ``env`` for a scaffolded project.

    Redirected configuration and identity copies are removed after context exit,
    including when preparation or process launch fails. Consumers must stop and
    reap the child before exiting this context.
    """
    project = Path(project).resolve()
    if not (project / ".codeanvil/project.yaml").is_file():
        raise SandboxError("not a scaffolded project — .codeanvil/project.yaml not found")
    spec = SANDBOX_AGENTS.get(agent)
    if spec is None:
        known = ", ".join(sorted(SANDBOX_AGENTS))
        raise SandboxError(f"unknown agent '{agent}' — known agents: {known}")
    if shutil.which(spec["binary"]) is None:
        raise SandboxError(f"'{spec['binary']}' binary not found on PATH — install it first")
    argv = _build_command(spec, project)
    env = dict(os.environ)
    strategy = spec.get("strategy", "native")
    if strategy == "native":
        yield {"argv": argv, "env": env}
        return
    if strategy not in {"xdg_redirect", "env_redirect"}:
        raise SandboxError(f"unknown sandbox strategy '{strategy}'")
    directory = None
    try:
        try:
            directory = Path(tempfile.mkdtemp(prefix="codeanvil-sandbox-"))
            _copy_auth_files(spec, directory)
            env[spec["env_var"]] = str(directory)
        except OSError as exc:
            raise SandboxError(str(exc)) from exc
        yield {"argv": argv, "env": env}
    finally:
        if directory is not None:
            shutil.rmtree(directory, ignore_errors=True)

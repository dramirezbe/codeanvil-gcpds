"""`codeanvil mcp <add|update|remove|list|doctor|run|enable|disable>`."""

import sys
from pathlib import Path

from codeanvil.config.logger import get_logger
from codeanvil.config.paths import CONFIG, find_manifest
from codeanvil.init import mcp

log = get_logger(__name__)


def _project_dir() -> Path:
    manifest = find_manifest(Path.cwd())
    if manifest is None:
        raise mcp.McpError("not inside a CodeAnvil project (no .codeanvil/project.yaml above cwd)")
    return manifest.parent.parent


def _print_doctor(name: str) -> bool:
    healthy = True
    print(name)
    for check, ok, detail in mcp.doctor(name):
        healthy &= ok
        print(f"  [{'ok' if ok else 'FAIL'}] {check}: {detail}")
    return healthy


def cmd_mcp(action: str, names: list[str] | None = None, yes: bool = False) -> None:
    names = list(names or [])
    try:
        if action == "add":
            for name in names:
                mcp.install_mcp_server(name)
        elif action == "update":
            targets = names or [row["name"] for row in mcp.server_rows() if row["installed"]]
            for name in targets:
                mcp.update_mcp_server(name)
        elif action == "remove":
            using = mcp.remove_mcp_server(names[0], force=yes)
            for label, path in using:
                log.warning("project %s (%s) still references %s", label, path, names[0])
        elif action == "list":
            for row in mcp.server_rows():
                state = "installed" if row["installed"] else "not installed"
                pin = ("pinned" if row["pinned"] else f"at {row['head'][:12]}") if row["installed"] else ""
                print(f"{row['name']:<12} {state:<14} ref {row['ref'][:12]} {pin}".rstrip())
        elif action == "doctor":
            targets = names or list(CONFIG.get("mcp_servers", {}))
            healthy = all([_print_doctor(name) for name in targets])
            if not healthy:
                sys.exit(1)
        elif action == "run":
            sys.exit(mcp.run_server(names[0]))
        elif action == "enable":
            project = _project_dir()
            servers = mcp.enable_server(names[0], project)
            log.info("enabled %s in %s (servers: %s)", names[0], project, ", ".join(servers))
        elif action == "disable":
            project = _project_dir()
            servers = mcp.disable_server(names[0], project)
            log.info("disabled %s in %s (servers: %s)", names[0], project, ", ".join(servers) or "none")
    except mcp.McpError as exc:
        # One diagnostic on stderr; stdout stays clean for `run`.
        log.error("%s", exc)
        sys.exit(1)

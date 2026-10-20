import json
import shutil
import subprocess
from pathlib import Path

import yaml

from codeanvil.config.logger import get_logger
from codeanvil.config.paths import CONFIG, MCP_DIR, SKILLS_DIRNAME

log = get_logger(__name__)


def _server_cfg(name: str) -> dict:
    servers = CONFIG.get("mcp_servers", {})
    if name not in servers:
        raise ValueError(f"unknown MCP server '{name}' — not defined in config.yaml")
    return servers[name]


def is_mcp_installed(name: str) -> bool:
    return (MCP_DIR / _server_cfg(name)["install_dir"].split("/")[-1]).is_dir()


def get_mcp_install_path(name: str) -> Path:
    cfg = _server_cfg(name)
    return (MCP_DIR / cfg["install_dir"].split("/")[-1]).resolve()


def install_mcp_server(name: str) -> Path:
    cfg = _server_cfg(name)
    dest = MCP_DIR / cfg["install_dir"].split("/")[-1]

    if dest.is_dir():
        log.info("MCP server '%s' already cloned at %s — pulling latest", name, dest)
        subprocess.run(["git", "-C", str(dest), "pull", "--ff-only"],
                       check=False, capture_output=True)
    else:
        log.info("cloning MCP server '%s' from %s", name, cfg["repo"])
        subprocess.run(["git", "clone", cfg["repo"], str(dest)],
                       check=True, capture_output=True)

    log.info("prewarming MCP server '%s' dependencies", name)
    subprocess.run(
        ["uv", "--directory", str(dest), "sync", "--extra", "mcp"],
        check=False, capture_output=True,
    )

    log.info("MCP server '%s' installed at %s", name, dest)
    return dest


def copy_mcp_skills(name: str, project_dir: Path) -> list[str]:
    cfg = _server_cfg(name)
    install_path = get_mcp_install_path(name)
    skills_src = install_path / cfg.get("skills_subdir", "skills")

    if not skills_src.is_dir():
        log.warning("no skills directory at %s for MCP server '%s'", skills_src, name)
        return []

    prefix = cfg.get("skill_prefix", name)
    copied = []

    for skill_dir in sorted(skills_src.iterdir()):
        if not skill_dir.is_dir():
            continue
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            continue

        dest_name = f"{prefix}-{skill_dir.name}"
        dest = project_dir / SKILLS_DIRNAME / dest_name
        shutil.copytree(skill_dir, dest, dirs_exist_ok=True)

        _ensure_gate_frontmatter(dest / "SKILL.md")
        copied.append(dest_name)
        log.debug("copied MCP skill %s -> %s", skill_dir.name, dest)

    log.info("copied %d skills from MCP server '%s'", len(copied), name)
    return copied


def _ensure_gate_frontmatter(skill_md: Path) -> None:
    """Marconi skills lack the gate field CodeAnvil expects.
    Add gate: '*' to the metadata block if missing."""
    text = skill_md.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return

    end = text.find("\n---", 3)
    if end == -1:
        return

    frontmatter_str = text[3:end].strip()
    try:
        fm = yaml.safe_load(frontmatter_str)
    except yaml.YAMLError:
        return
    if not isinstance(fm, dict):
        return

    metadata = fm.get("metadata")
    if isinstance(metadata, dict) and "gate" in metadata:
        return

    if metadata is None:
        fm["metadata"] = {"gate": "*"}
    elif isinstance(metadata, dict):
        metadata["gate"] = "*"
    else:
        return

    new_fm = yaml.dump(fm, default_flow_style=False, sort_keys=False).rstrip()
    new_text = f"---\n{new_fm}\n---{text[end + 4:]}"
    skill_md.write_text(new_text, encoding="utf-8")


def write_mcp_manifest(servers: list[str], project_dir: Path) -> None:
    manifest = {}
    for name in servers:
        cfg = _server_cfg(name)
        install_path = str(get_mcp_install_path(name))
        manifest[name] = {
            "command": cfg["command"],
            "args": [a.replace("{install_path}", install_path) for a in cfg["args"]],
            "env": {
                k: v.replace("{project_dir}", str(project_dir.resolve()))
                for k, v in cfg.get("env", {}).items()
            },
            "description": cfg.get("description", ""),
        }

    dest = project_dir / SKILLS_DIRNAME.parent / "mcp.yaml"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(
        yaml.dump({"mcp_servers": manifest}, default_flow_style=False, sort_keys=False),
        encoding="utf-8",
    )
    log.debug("wrote MCP manifest %s", dest)


def generate_agent_mcp_configs(servers: list[str], project_dir: Path) -> None:
    entries = {}
    for name in servers:
        cfg = _server_cfg(name)
        install_path = str(get_mcp_install_path(name))
        args = [a.replace("{install_path}", install_path) for a in cfg["args"]]
        env = {
            k: v.replace("{project_dir}", str(project_dir.resolve()))
            for k, v in cfg.get("env", {}).items()
        }
        entries[name] = {"command": cfg["command"], "args": args, "env": env}

    _write_claude_mcp(entries, project_dir)
    _write_vscode_mcp(entries, project_dir)
    _write_opencode_mcp(entries, project_dir)
    _write_codex_mcp(entries, project_dir)


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    log.debug("wrote %s", path)


def _write_claude_mcp(entries: dict, project_dir: Path) -> None:
    mcp_servers = {}
    for name, e in entries.items():
        mcp_servers[name] = {
            "command": e["command"],
            "args": e["args"],
            "env": e["env"],
        }
    # .mcp.json at project root — the standard Claude Code project MCP manifest.
    # Also read by VS Code and other MCP-aware tools.
    mcp_json_path = project_dir / ".mcp.json"
    existing_mcp = {}
    if mcp_json_path.exists():
        try:
            existing_mcp = json.loads(mcp_json_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    existing_mcp.setdefault("mcpServers", {}).update(mcp_servers)
    _write_json(mcp_json_path, existing_mcp)

    # .claude/settings.json — enable the .mcp.json servers so Claude Code
    # connects them even under --setting-sources "project" (which excludes
    # the "local" source where interactive enablement is normally stored).
    settings_path = project_dir / ".claude" / "settings.json"
    existing_settings = {}
    if settings_path.exists():
        try:
            existing_settings = json.loads(settings_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    enabled = existing_settings.get("enabledMcpjsonServers", [])
    for name in mcp_servers:
        if name not in enabled:
            enabled.append(name)
    existing_settings["enabledMcpjsonServers"] = enabled
    _write_json(settings_path, existing_settings)

    # Also write to settings.local.json for normal (non-sandboxed) sessions.
    local_path = project_dir / ".claude" / "settings.local.json"
    existing_local = {}
    if local_path.exists():
        try:
            existing_local = json.loads(local_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    local_enabled = existing_local.get("enabledMcpjsonServers", [])
    for name in mcp_servers:
        if name not in local_enabled:
            local_enabled.append(name)
    existing_local["enabledMcpjsonServers"] = local_enabled
    _write_json(local_path, existing_local)


def _write_vscode_mcp(entries: dict, project_dir: Path) -> None:
    servers = {}
    for name, e in entries.items():
        servers[name] = {
            "command": e["command"],
            "args": e["args"],
            "env": e["env"],
        }
    _write_json(project_dir / ".vscode" / "mcp.json", {"servers": servers})


def _write_opencode_mcp(entries: dict, project_dir: Path) -> None:
    servers = {}
    for name, e in entries.items():
        servers[name] = {
            "type": "local",
            "command": [e["command"]] + e["args"],
            "environment": e["env"],
        }
    _write_json(project_dir / ".opencode" / "mcp.json", {"mcp": {"servers": servers}})


def _write_codex_mcp(entries: dict, project_dir: Path) -> None:
    servers = {}
    for name, e in entries.items():
        servers[name] = {
            "command": e["command"],
            "args": e["args"],
            "env": e["env"],
        }
    _write_json(project_dir / ".codex" / "mcp.json", {"mcp_servers": servers})

"""MCP servers: a pinned venv per server under ~/.codeanvil-config/mcp/<name>/,
one launcher (`codeanvil mcp run <name>`) and portable per-project configs.

Lifecycle: `add` (clone, check out the pinned `ref`, build the venv, probe the
system packages), `update`, `remove`, `list`, `doctor`. Every project config
calls `codeanvil mcp run <name>`; the launcher resolves the install path, the
project root and the env at start-up, so a moved or cloned project keeps
working. stdout is the MCP protocol channel: nothing here prints to it.
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

from codeanvil.config.logger import get_logger
from codeanvil.config.paths import CONFIG, MCP_DIR, SKILLS_DIRNAME, TEMPLATES_DIR, find_manifest
from codeanvil.init import system_packages as syspkg

log = get_logger(__name__)

_IS_WIN = sys.platform == "win32"
PROBE_CACHE = ".probe.json"


class McpError(Exception):
    """An MCP operation failed; the message says what to do."""


def _server_cfg(name: str) -> dict:
    servers = CONFIG.get("mcp_servers", {})
    if name not in servers:
        raise McpError(
            f"unknown MCP server '{name}' — available: {', '.join(servers) or 'none'}"
        )
    return servers[name]


def get_mcp_install_path(name: str) -> Path:
    cfg = _server_cfg(name)
    return (MCP_DIR / cfg["install_dir"].split("/")[-1]).resolve()


def is_mcp_installed(name: str) -> bool:
    return get_mcp_install_path(name).is_dir()


def venv_bin(install_path: Path) -> Path:
    return install_path / ".venv" / ("Scripts" if _IS_WIN else "bin")


def venv_python(install_path: Path) -> Path:
    return venv_bin(install_path) / ("python.exe" if _IS_WIN else "python")


def _run(args: list[str], what: str) -> str:
    """Run a command; on failure raise with its stderr instead of swallowing it."""
    try:
        result = subprocess.run(args, capture_output=True, text=True)
    except FileNotFoundError as exc:
        raise McpError(f"{what}: {args[0]} is not installed") from exc
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        raise McpError(f"{what} failed (`{' '.join(args)}`, exit {result.returncode}):\n{detail}")
    return result.stdout.strip()


def _head(install_path: Path) -> str | None:
    try:
        return _run(["git", "-C", str(install_path), "rev-parse", "HEAD"], "git rev-parse")
    except McpError:
        return None


def _checkout_ref(name: str, cfg: dict, dest: Path) -> None:
    ref = cfg.get("ref")
    if not ref:
        raise McpError(f"mcp_servers.{name}.ref is not set — pin a tag or commit in config.yaml")
    if not dest.is_dir():
        log.info("cloning MCP server '%s' from %s", name, cfg["repo"])
        dest.parent.mkdir(parents=True, exist_ok=True)
        _run(["git", "clone", "--quiet", cfg["repo"], str(dest)], "git clone")
    else:
        _run(["git", "-C", str(dest), "fetch", "--quiet", "--tags", "origin"], "git fetch")
    _run(["git", "-C", str(dest), "checkout", "--quiet", "--detach", ref], f"git checkout {ref}")


def _is_bundled(cfg: dict) -> bool:
    return cfg.get("source") == "bundled"


def _copy_bundled(name: str, cfg: dict, dest: Path) -> None:
    """Install a first-party server by copying its source from the wheel
    (templates/mcp/<dir>) instead of cloning. Keeps an existing .venv so a
    re-run is an in-place refresh."""
    src = TEMPLATES_DIR / "mcp" / cfg["install_dir"].split("/")[-1]
    if not src.is_dir():
        raise McpError(f"bundled MCP server '{name}' is missing from this CodeAnvil install ({src})")
    log.info("installing bundled MCP server '%s' from %s", name, src)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src, dest, dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns(".venv", "__pycache__", "*.pyc"))


def _target_interpreter(name: str, cfg: dict) -> Path | None:
    """The system interpreter the server's system packages were built for, or
    None when the server declares none (uv then picks the interpreter)."""
    chosen: Path | None = None
    for package in cfg.get("system_packages", []):
        site = syspkg.detect_system_site_packages(package)
        if site is None:
            raise McpError(
                f"{package} is not installed. Install it: {syspkg.install_hint(package)}"
            )
        interpreter = syspkg.system_interpreter_for(site)
        if interpreter is None:
            raise McpError(
                f"{package} is installed at {site} but its Python "
                f"{syspkg.built_for_python(site) or '?'} interpreter was not found"
            )
        if chosen is not None and interpreter != chosen:
            raise McpError(f"{name}'s system packages need different interpreters: {chosen}, {interpreter}")
        chosen = interpreter
    return chosen


def _venv_matches(install_path: Path, interpreter: Path) -> bool:
    """True when the venv runs `interpreter`'s version and sees its site-packages."""
    python = venv_python(install_path)
    if not python.exists():
        return False
    cfg_file = install_path / ".venv" / "pyvenv.cfg"
    try:
        text = cfg_file.read_text(encoding="utf-8")
    except OSError:
        return False
    if "include-system-site-packages = true" not in text:
        return False
    return syspkg.interpreter_version(python) == syspkg.interpreter_version(interpreter)


def _build_venv(name: str, cfg: dict, dest: Path) -> None:
    uv = shutil.which("uv")
    if uv is None:
        raise McpError("uv is not installed — install it first (https://docs.astral.sh/uv/)")
    interpreter = _target_interpreter(name, cfg)
    sync = [uv, "sync", "--directory", str(dest), *cfg.get("sync_args", [])]
    if interpreter is not None:
        if not _venv_matches(dest, interpreter):
            shutil.rmtree(dest / ".venv", ignore_errors=True)
            log.info("creating %s venv on %s with system site-packages", name, interpreter)
            _run([uv, "venv", "--quiet", "--python", str(interpreter), "--system-site-packages",
                  str(dest / ".venv")], "uv venv")
        sync += ["--python", str(interpreter)]
    log.info("syncing MCP server '%s' dependencies", name)
    _run(sync, "uv sync")
    (dest / PROBE_CACHE).unlink(missing_ok=True)


def probe_server(name: str, use_cache: bool = True) -> list[syspkg.ProbeResult]:
    cfg = _server_cfg(name)
    install_path = get_mcp_install_path(name)
    python = venv_python(install_path)
    owner = f"the {name} venv"
    results = []
    for package in cfg.get("system_packages", []):
        if use_cache:
            result = syspkg.cached_probe(package, python, owner, install_path / PROBE_CACHE)
        else:
            result = syspkg.probe(package, python, owner)
        if result.status == "mismatch":
            result = syspkg.ProbeResult(
                result.package, result.status, f"{result.message} Run codeanvil mcp update {name}."
            )
        results.append(result)
    return results


def _require_probes(name: str) -> None:
    failures = [result for result in probe_server(name, use_cache=False) if not result.ok]
    if failures:
        raise McpError("\n".join(result.message for result in failures))


def install_mcp_server(name: str) -> Path:
    """`codeanvil mcp add`: clone, pin, build the venv, probe. Idempotent."""
    cfg = _server_cfg(name)
    dest = get_mcp_install_path(name)
    bundled = _is_bundled(cfg)
    if bundled:
        _copy_bundled(name, cfg, dest)
    else:
        _checkout_ref(name, cfg, dest)
    _build_venv(name, cfg, dest)
    _require_probes(name)
    log.info("MCP server '%s' installed at %s (%s)", name, dest, "bundled" if bundled else cfg["ref"])
    return dest


def update_mcp_server(name: str) -> Path:
    """`codeanvil mcp update`: re-pin to the configured ref and rebuild the
    venv when its interpreter no longer matches the system packages."""
    if not is_mcp_installed(name):
        raise McpError(f"MCP server '{name}' is not installed. Run codeanvil mcp add {name}.")
    return install_mcp_server(name)


def projects_using(name: str) -> list[tuple[str, str]]:
    """(project name, path) of registered projects whose .agents/mcp.yaml names `name`."""
    from codeanvil.config.paths import DB_PATH
    from codeanvil.db.projects import list_projects
    from codeanvil.db.schema import db_exists
    from codeanvil.db.utils import connect_db

    if not db_exists(DB_PATH):
        return []
    conn = connect_db(DB_PATH)
    try:
        rows = list_projects(conn)
    finally:
        conn.close()
    using = []
    for row in rows:
        if name in project_servers(Path(row["path"])):
            using.append((row["name"], row["path"]))
    return using


def remove_mcp_server(name: str, force: bool = False) -> list[tuple[str, str]]:
    """Delete the install. Refuses without `force` while projects use it;
    returns those projects either way."""
    _server_cfg(name)
    dest = get_mcp_install_path(name)
    using = projects_using(name)
    if using and not force:
        listed = "\n".join(f"  {label}: {path}" for label, path in using)
        raise McpError(
            f"{len(using)} project(s) use '{name}':\n{listed}\n"
            f"Run codeanvil mcp disable {name} in each, or pass --yes to remove anyway."
        )
    if dest.is_dir():
        shutil.rmtree(dest)
        log.info("removed MCP server '%s' (%s)", name, dest)
    return using


def server_rows() -> list[dict]:
    """One row per configured server for `codeanvil mcp list`."""
    rows = []
    for name, cfg in CONFIG.get("mcp_servers", {}).items():
        install_path = get_mcp_install_path(name)
        installed = install_path.is_dir()
        bundled = _is_bundled(cfg)
        # A bundled server has no git HEAD: it is pinned by the wheel it ships in.
        head = None if bundled or not installed else _head(install_path)
        rows.append({
            "name": name,
            "installed": installed,
            "source": "bundled" if bundled else "git",
            "ref": "bundled" if bundled else cfg.get("ref", ""),
            "head": head or "",
            "pinned": installed if bundled else bool(
                head and cfg.get("ref") and head.startswith(str(cfg["ref"]))),
        })
    return rows


def doctor(name: str) -> list[tuple[str, bool, str]]:
    """(check, ok, detail) for one server."""
    cfg = _server_cfg(name)
    install_path = get_mcp_install_path(name)
    checks: list[tuple[str, bool, str]] = []
    for tool in cfg.get("requires", []):
        found = shutil.which(tool)
        checks.append((f"{tool} on PATH", found is not None, found or f"install {tool}"))
    if not install_path.is_dir():
        checks.append(("installed", False, f"Run codeanvil mcp add {name}."))
        return checks
    checks.append(("installed", True, str(install_path)))
    if _is_bundled(cfg):
        checks.append(("bundled source", True, "shipped in the CodeAnvil wheel"))
    else:
        head = _head(install_path) or ""
        ref = str(cfg.get("ref", ""))
        pinned = bool(ref) and head.startswith(ref)
        checks.append(("pinned ref", pinned,
                       head if pinned else f"checked out {head[:12] or '?'}, config pins {ref[:12]} — run codeanvil mcp update {name}"))
    python = venv_python(install_path)
    checks.append(("venv", python.exists(),
                   str(python) if python.exists() else f"no venv — run codeanvil mcp update {name}"))
    if python.exists():
        for result in probe_server(name, use_cache=False):
            checks.append((f"system package {result.package}", result.ok, result.message))
    return checks


def _expand(value: str, install_path: Path, project_dir: Path) -> str:
    return (value.replace("{install_path}", str(install_path))
                 .replace("{venv_bin}", str(venv_bin(install_path)))
                 .replace("{project_dir}", str(project_dir)))


def launch_spec(name: str, cwd: Path) -> tuple[list[str], dict[str, str]]:
    """argv and env the launcher starts, after every start-up check."""
    cfg = _server_cfg(name)
    install_path = get_mcp_install_path(name)
    if not install_path.is_dir():
        raise McpError(f"MCP server '{name}' is not installed. Run codeanvil mcp add {name}.")
    if not venv_python(install_path).exists():
        raise McpError(f"MCP server '{name}' has no venv. Run codeanvil mcp update {name}.")
    failures = [result for result in probe_server(name) if not result.ok]
    if failures:
        raise McpError(" ".join(result.message for result in failures))

    manifest = find_manifest(cwd)
    project_dir = manifest.parent.parent if manifest else cwd.resolve()
    command = _expand(cfg["command"], install_path, project_dir)
    if _IS_WIN and not Path(command).suffix and Path(command + ".exe").exists():
        command += ".exe"
    argv = [command, *(_expand(arg, install_path, project_dir) for arg in cfg.get("args", []))]
    env = {key: value for key, value in os.environ.items() if key != "PYTHONPATH"}
    env.update({key: _expand(str(value), install_path, project_dir)
                for key, value in cfg.get("env", {}).items()})
    return argv, env


def run_server(name: str) -> int:
    """Start the server with inherited stdio. POSIX replaces this process; on
    Windows `os.execv` would spawn and exit (a dead server to the client), so
    the launcher stays as the parent and forwards the exit code."""
    argv, env = launch_spec(name, Path.cwd())
    if not _IS_WIN:
        sys.stderr.flush()
        os.execvpe(argv[0], argv, env)
    child = subprocess.Popen(argv, env=env)
    try:
        return child.wait()
    except KeyboardInterrupt:
        child.terminate()
        return child.wait()


# --- per-project wiring --------------------------------------------------------


def project_servers(project_dir: Path) -> list[str]:
    """Server names listed in the project's .agents/mcp.yaml."""
    path = project_dir / SKILLS_DIRNAME.parent / "mcp.yaml"
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError):
        return []
    servers = data.get("mcp_servers", {}) if isinstance(data, dict) else {}
    return list(servers) if isinstance(servers, dict) else []


def _launcher_entry(name: str) -> dict:
    return {"command": "codeanvil", "args": ["mcp", "run", name], "env": {}}


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

    if copied:
        _copy_license_notices(install_path, project_dir, prefix, cfg)

    log.info("copied %d skills from MCP server '%s'", len(copied), name)
    return copied


def _copy_license_notices(install_path: Path, project_dir: Path, prefix: str, cfg: dict) -> None:
    """Carry the upstream license and attribution into the scaffolded project.

    Copied skills are licensed by their upstream project (e.g. Marconi is
    GPL-3.0-or-later). The scaffolded project is not distributed by CodeAnvil —
    its owner may publish or sell it — so at that point the owner redistributes
    these files and the license text and copyright notices must travel with
    them. The scaffold modifies the copies (adds gate frontmatter), which is a
    permitted modification only as long as the notices survive."""
    dest_dir = project_dir / SKILLS_DIRNAME

    licenses = sorted(install_path.glob("LICENSE*"))
    if not licenses:
        log.warning("no LICENSE file at %s — copied skills carry no license text", install_path)
    for lic in licenses:
        shutil.copy2(lic, dest_dir / f"{prefix}-{lic.name}")

    repo = cfg.get("repo", "")
    license_names = ", ".join(lic.name for lic in licenses) or "unknown"
    notice = (
        f"# Notice — {prefix} skills\n\n"
        f"The `{prefix}-*` skill directories in this project are derived from\n"
        f"upstream project: {repo}\n\n"
        f"They are licensed under the terms of the upstream LICENSE file(s)\n"
        f"copied here as: {license_names}.\n\n"
        "CodeAnvil's scaffold modified these copies by adding gate frontmatter\n"
        "to their SKILL.md metadata. This is a permitted modification; the\n"
        "upstream license terms and copyright notices continue to apply.\n\n"
        "If you redistribute this project (public repository, sale, delivery\n"
        "to a client), keep this notice and the upstream license file(s)\n"
        "alongside the copied skills.\n"
    )
    (dest_dir / f"{prefix}-NOTICE.md").write_text(notice, encoding="utf-8")
    log.debug("wrote %s license notice (%d file(s))", prefix, len(licenses))


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
    """Agent-agnostic `.agents/mcp.yaml`: every server through the launcher."""
    manifest = {}
    for name in servers:
        cfg = _server_cfg(name)
        entry = _launcher_entry(name)
        manifest[name] = {"command": entry["command"], "args": entry["args"],
                          "description": cfg.get("description", "")}

    dest = project_dir / SKILLS_DIRNAME.parent / "mcp.yaml"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(
        yaml.dump({"mcp_servers": manifest}, default_flow_style=False, sort_keys=False,
                  allow_unicode=True),
        encoding="utf-8",
    )
    log.debug("wrote MCP manifest %s", dest)


def generate_agent_mcp_configs(servers: list[str], project_dir: Path) -> None:
    """The four per-agent configs. Identical on every OS: no absolute path,
    no env — the launcher resolves both at start-up."""
    entries = {name: _launcher_entry(name) for name in servers if _server_cfg(name)}
    _write_claude_mcp(entries, project_dir)
    _write_vscode_mcp(entries, project_dir)
    _write_opencode_mcp(entries, project_dir)
    _write_codex_mcp(entries, project_dir)


def _load_json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def _drop_from_configs(name: str, project_dir: Path) -> None:
    for path, keys in (
        (project_dir / ".mcp.json", ("mcpServers",)),
        (project_dir / ".vscode" / "mcp.json", ("servers",)),
        (project_dir / "opencode.json", ("mcp",)),
        (project_dir / ".codex" / "mcp.json", ("mcp_servers",)),
    ):
        if not path.exists():
            continue
        data = _load_json(path)
        section = data.get(keys[0])
        if isinstance(section, dict) and name in section:
            del section[name]
            _write_json(path, data)
    for settings in (".claude/settings.json", ".claude/settings.local.json"):
        path = project_dir / settings
        if not path.exists():
            continue
        data = _load_json(path)
        enabled = data.get("enabledMcpjsonServers")
        if isinstance(enabled, list) and name in enabled:
            data["enabledMcpjsonServers"] = [server for server in enabled if server != name]
            _write_json(path, data)


def _refresh_agents_md_table(project_dir: Path, servers: list[str]) -> None:
    """Replace only the generated MCP table inside AGENTS.md."""
    from codeanvil.init.create import _mcp_table

    path = project_dir / "AGENTS.md"
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return
    start_marker = "## MCP Servers\n\n"
    end_marker = "\n\nMCP servers provide tool-calling"
    start = text.find(start_marker)
    end = text.find(end_marker, start)
    if start == -1 or end == -1:
        log.warning("AGENTS.md has no generated MCP table — update it by hand")
        return
    start += len(start_marker)
    path.write_text(text[:start] + _mcp_table(servers or None) + text[end:], encoding="utf-8")


def enable_server(name: str, project_dir: Path) -> list[str]:
    """Wire `name` into a project (also rewrites a pre-launcher config)."""
    _server_cfg(name)
    if not is_mcp_installed(name):
        raise McpError(f"MCP server '{name}' is not installed. Run codeanvil mcp add {name}.")
    servers = project_servers(project_dir)
    if name not in servers:
        servers.append(name)
    copy_mcp_skills(name, project_dir)
    write_mcp_manifest(servers, project_dir)
    generate_agent_mcp_configs(servers, project_dir)
    _refresh_agents_md_table(project_dir, servers)
    return servers


def disable_server(name: str, project_dir: Path) -> list[str]:
    cfg = _server_cfg(name)
    servers = [server for server in project_servers(project_dir) if server != name]
    prefix = cfg.get("skill_prefix", name)
    skills = project_dir / SKILLS_DIRNAME
    for path in sorted(skills.glob(f"{prefix}-*")):
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()
    _drop_from_configs(name, project_dir)
    write_mcp_manifest(servers, project_dir)
    _refresh_agents_md_table(project_dir, servers)
    return servers


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
    # OpenCode reads opencode.json at project root. Servers live directly
    # under "mcp" (flat), not "mcp.servers" (despite what `opencode mcp add` writes).
    path = project_dir / "opencode.json"
    existing = {}
    if path.exists():
        try:
            existing = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    mcp = existing.setdefault("mcp", {})
    for name, e in entries.items():
        mcp[name] = {
            "type": "local",
            "command": [e["command"]] + e["args"],
            "environment": e["env"],
        }
    existing.setdefault("$schema", "https://opencode.ai/config.json")
    _write_json(path, existing)


def _write_codex_mcp(entries: dict, project_dir: Path) -> None:
    servers = {}
    for name, e in entries.items():
        servers[name] = {
            "command": e["command"],
            "args": e["args"],
            "env": e["env"],
        }
    _write_json(project_dir / ".codex" / "mcp.json", {"mcp_servers": servers})

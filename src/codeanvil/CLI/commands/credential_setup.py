"""`codeanvil credential-setup` — bootstrap an HIL target for vsil_hil_mcp.

Thin wrapper around the bundled bash engine
(templates/mcp/vsil_hil_mcp/scripts/setup_credentials_ssh_hil.sh): it generates
the confined keys, bootstraps the remote target over SSH, then registers the
target in the project's .codeanvil/project.yaml. The admin password is passed
to the script through the environment only (never argv) and is never logged.
"""

import getpass
import os
import re
import subprocess
import sys
from pathlib import Path

import yaml

from codeanvil.config.logger import get_logger
from codeanvil.config.paths import TEMPLATES_DIR, find_manifest

log = get_logger(__name__)

# Mirrors vsil_hil_mcp.config._NAME_RE.
_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")
_USER_RE = re.compile(r"^[a-z_][a-z0-9_-]{0,31}$")
_HOST_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9.:-]{0,252}$")
_WORKSPACE_RE = re.compile(r"^/[A-Za-z0-9._/+@-]+$")
_SCRIPTS = Path("mcp") / "vsil_hil_mcp" / "scripts"
PASSWORD_ENV = "CODEANVIL_HIL_PASSWORD"
SUDO_PASSWORD_ENV = "CODEANVIL_HIL_SUDO_PASSWORD"
# The agent user is fixed on every target, for traceability — never configurable.
AGENT_USER = "codeanvil-agent"


def _derive_target(ip: str) -> str:
    return re.sub(r"[.:]", "_", ip)


def _hil_dir(target: str) -> Path:
    return Path.home() / ".codeanvil-config" / "hil" / target


def _ensure_keys(target: str) -> Path:
    """Create the two confined ed25519 keys (idempotent) — used on the windows path."""
    hil = _hil_dir(target)
    hil.mkdir(parents=True, exist_ok=True)
    for d in (hil.parent, hil):
        os.chmod(d, 0o700)
    known = hil / "known_hosts"
    known.touch(mode=0o600)
    for role in ("deploy", "exec"):
        key = hil / f"{role}_ed25519"
        if key.exists():
            continue
        res = subprocess.run(
            ["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-C", f"vsil-hil-{role}-{target}", "-f", str(key)],
            check=False,
        )
        if res.returncode != 0:
            log.error("ssh-keygen failed for the %s key (exit %s)", role, res.returncode)
            sys.exit(1)
        if key.exists():
            os.chmod(key, 0o600)
    return hil


def _register_target(project_yaml: Path, entry: dict) -> bool:
    """Append `entry` to `targets:` unless that name exists. True when written."""
    data = yaml.safe_load(project_yaml.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        data = {}
    block = data.get("targets") or []
    if isinstance(block, dict):
        if entry["name"] in block:
            return False
        block[entry["name"]] = {k: v for k, v in entry.items() if k != "name"}
    elif isinstance(block, list):
        if any(isinstance(t, dict) and t.get("name") == entry["name"] for t in block):
            return False
        block.append(entry)
    else:
        log.error("`targets:` in %s must be a list or a map", project_yaml)
        sys.exit(1)
    data["targets"] = block
    project_yaml.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return True


def _check_existing_target(project_yaml: Path, entry: dict) -> None:
    """Refuse a name collision before changing credentials on any target."""
    data = yaml.safe_load(project_yaml.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("project.yaml must be a mapping")
    block = data.get("targets") or []
    if isinstance(block, dict):
        rows = [dict(value, name=name) for name, value in block.items() if isinstance(value, dict)]
        if len(rows) != len(block):
            raise ValueError("each target must be a mapping")
    elif isinstance(block, list):
        rows = block
    else:
        raise ValueError("`targets:` must be a list or a map")
    names = set()
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("name"), str):
            raise ValueError("each target must have a name")
        if row["name"] in names:
            raise ValueError(f"duplicate target name {row['name']!r}")
        names.add(row["name"])
        if row["name"] == entry["name"]:
            for key, value in entry.items():
                actual = row.get(key, 22 if key == "port" else "trusted" if key == "hil_policy" else None)
                if actual != value:
                    raise ValueError(f"target {entry['name']!r} already exists with different {key}")


def cmd_credential_setup(
    user: str,
    ip: str,
    password: str | None = None,
    sudo_password: str | None = None,
    workspace: str = "",
    port: int = 22,
    target: str = "",
    os_: str = "linux",
) -> None:
    """Run `codeanvil credential-setup` — keys + remote bootstrap + project.yaml.

    The agent user is always ``codeanvil-agent`` (fixed, for traceability).
    """
    manifest = find_manifest(Path.cwd())
    if manifest is None:
        log.error("not inside a scaffolded project — .codeanvil/project.yaml not found (searched up from cwd)")
        sys.exit(1)

    target = target or _derive_target(ip)
    if not _NAME_RE.match(target):
        log.error("invalid target name '%s' (allowed: letters, digits, '_' and '-', max 64) — pass -t", target)
        sys.exit(1)
    workspace = workspace or f"/home/{AGENT_USER}/workspace"
    entry = {
        "name": target, "host": ip, "user": AGENT_USER, "workspace": workspace,
        "os": os_, "hil_policy": "trusted", "port": port,
    }
    try:
        if os_ != "linux":
            raise ValueError("credential bootstrap is implemented for Linux targets only")
        if type(port) is not int or not 1 <= port <= 65535:
            raise ValueError("SSH port must be an integer from 1 to 65535")
        if not _USER_RE.fullmatch(user) or not _HOST_RE.fullmatch(ip):
            raise ValueError("invalid admin user or target host")
        if not _WORKSPACE_RE.fullmatch(workspace) or ".." in workspace.split("/"):
            raise ValueError("invalid absolute target workspace")
        _check_existing_target(manifest, entry)
    except (ValueError, yaml.YAMLError) as exc:
        log.error("%s", exc)
        sys.exit(1)

    # Prompt securely when -p is omitted; sudo reuses the SSH password unless a
    # different one is given (or entered at the second prompt).
    if password is None:
        password = getpass.getpass(f"SSH password for {user}@{ip}: ")
        if sudo_password is None:
            entered = getpass.getpass("sudo password (press Enter to reuse the SSH password): ")
            sudo_password = entered or password
    if not password:
        log.error("no SSH password provided")
        sys.exit(1)
    sudo_password = sudo_password or password

    if os_ == "linux":
        script = TEMPLATES_DIR / _SCRIPTS / "setup_credentials_ssh_hil.sh"
        if not script.is_file():
            log.error("bundled script not found: %s", script)
            sys.exit(1)
        cmd = [
            "bash", str(script), "-u", user, "-i", ip, "--port", str(port),
            "-a", AGENT_USER, "-t", target, "-w", workspace,
        ]
        log.info("bootstrapping %s@%s as admin '%s' (target '%s')", AGENT_USER, ip, user, target)
        res = subprocess.run(
            cmd,
            env={**os.environ, PASSWORD_ENV: password, SUDO_PASSWORD_ENV: sudo_password},
            check=False,
            capture_output=True,
            text=True,
        )
        if res.stdout:
            print(res.stdout, end="")
        if res.stderr:
            print(res.stderr, end="", file=sys.stderr)
        if res.returncode != 0:
            log.error("remote bootstrap failed (exit %s) — project.yaml not modified", res.returncode)
            sys.exit(1)
    else:
        hil = _ensure_keys(target)
        ps1 = TEMPLATES_DIR / _SCRIPTS / "setup_credentials_ssh_hil.ps1"
        log.info("Windows target: automatic bootstrap is not supported from this host.")
        log.info("Run this script ON the target as Administrator:")
        log.info("  %s", ps1)
        log.info("Public keys to install for user '%s':", AGENT_USER)
        log.info("  deploy: %s", hil / "deploy_ed25519.pub")
        log.info("  exec:   %s", hil / "exec_ed25519.pub")

    if _register_target(manifest, entry):
        log.info("registered target '%s' in %s", target, manifest)
    else:
        log.info("target '%s' already registered in %s — left unchanged", target, manifest)

    log.info("done. The vsil_hil_mcp tools (ssh_exec_cmd, code_sync, fetch_evidence, ...) can now use target '%s'.", target)
    log.info("Next: running the verification kit on the target also needs CodeAnvil installed there "
             "(install.sh as '%s'); this command sets up access only.", AGENT_USER)

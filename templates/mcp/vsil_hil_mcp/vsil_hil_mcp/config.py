"""Project root, remote-target declarations and the per-target key store.

Self-contained: stdlib + pyyaml only. Never imports `codeanvil`.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from pathlib import PurePosixPath

import yaml

from . import identity

POLICIES = ("trusted", "guarded", "locked")
DEFAULT_POLICY = "trusted"
AGENT_USER = "codeanvil-agent"
_RELEASE_VERSION_RE = re.compile(r"[0-9]+\.[0-9]+\.[0-9]+")

# Strict allowlists: these values end up in ssh/rsync argv and in a shell script
# the human runs as root on the target, so anything outside the pattern is refused.
_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")
_USER_RE = re.compile(r"^[a-z_][a-z0-9_-]{0,31}$")
_HOST_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9.:-]{0,252}$")  # no leading '-', no whitespace
_WORKSPACE_RE = re.compile(r"^/[A-Za-z0-9._/+@-]+$")  # absolute, no shell metacharacters


class ConfigError(ValueError):
    """Bad or missing project / target configuration."""


def release_version(value: str) -> str:
    """Validate a released version before interpolating its git tag in a script."""
    if not _RELEASE_VERSION_RE.fullmatch(value):
        raise ConfigError("expected a released CodeAnvil version X.Y.Z; development installs need an explicit release")
    return value


def host_version() -> str:
    """The launcher supplies its own installed package version; never guess a pin."""
    value = os.environ.get("VSIL_HIL_CODEANVIL_VERSION", "")
    if not value:
        raise ConfigError("missing host CodeAnvil version: launch through codeanvil mcp run vsil_hil_mcp")
    return release_version(value)


@dataclass(frozen=True)
class Target:
    name: str
    host: str
    user: str
    workspace: str
    os: str = "linux"
    arch: str = ""
    device: str = ""
    hil_policy: str = DEFAULT_POLICY
    port: int = 22
    device_id: str = ""
    deploy_root: str = ""
    mac_addresses: tuple[str, ...] = ()
    bootstrap_user: str = ""
    persistent_paths: tuple[str, ...] = ()

    @property
    def key_identity(self) -> str:
        return identity.local_key_identity(self.device_id) if self.device_id else self.name


def project_root() -> Path:
    """`VSIL_HIL_WORKSPACE`, else the nearest ancestor of cwd holding `.codeanvil/`."""
    env = os.environ.get("VSIL_HIL_WORKSPACE", "").strip()
    if env:
        return Path(env).resolve()
    here = Path.cwd().resolve()
    for candidate in (here, *here.parents):
        if (candidate / ".codeanvil").is_dir():
            return candidate
    raise ConfigError("no project root: set VSIL_HIL_WORKSPACE or run inside a project with .codeanvil/")


def project_yaml(root: Path) -> Path:
    return root / ".codeanvil" / "project.yaml"


def _read_project(root: Path) -> dict:
    path = project_yaml(root)
    if not path.is_file():
        raise ConfigError(f"{path} not found: not a CodeAnvil project")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ConfigError(f"{path} is not a mapping")
    return data


def validate_target_fields(name: str, host: str, user: str, workspace: str, policy: str,
                           port: int = 22, os_name: str = "linux") -> None:
    if not _NAME_RE.match(name):
        raise ConfigError(f"invalid target name {name!r}")
    if not _HOST_RE.match(host):
        raise ConfigError(f"invalid host {host!r}")
    if not _USER_RE.match(user):
        raise ConfigError(f"invalid user {user!r}")
    if not _WORKSPACE_RE.match(workspace) or ".." in workspace.split("/"):
        raise ConfigError(f"invalid workspace {workspace!r}: must be an absolute path of [A-Za-z0-9._/+@-]")
    if policy not in POLICIES:
        raise ConfigError(f"invalid hil_policy {policy!r}: expected one of {POLICIES}")
    if type(port) is not int or not 1 <= port <= 65535:
        raise ConfigError("invalid SSH port: expected an integer from 1 to 65535")
    if os_name not in ("linux", "windows"):
        raise ConfigError(f"unsupported target OS {os_name!r}: expected linux or windows")


def _to_target(name: str, raw: dict) -> Target:
    if not isinstance(raw, dict):
        raise ConfigError(f"target {name!r} is not a mapping")
    for field in ("mac_addresses", "persistent_paths"):
        if field in raw and not isinstance(raw[field], list):
            raise ConfigError(f"{field} must be a list")
    t = Target(
        name=name,
        host=str(raw.get("host", "")),
        user=str(raw.get("user", "")),
        workspace=str(raw.get("workspace", "")),
        os=str(raw.get("os", "linux")),
        arch=str(raw.get("arch", "")),
        device=str(raw.get("device", "")),
        hil_policy=str(raw.get("hil_policy", DEFAULT_POLICY)),
        port=raw.get("port", 22),
        device_id=str(raw.get("device_id", "")),
        deploy_root=str(raw.get("deploy_root", "")),
        mac_addresses=tuple(raw.get("mac_addresses", [])),
        bootstrap_user=str(raw.get("bootstrap_user", "")),
        persistent_paths=tuple(raw.get("persistent_paths", [])),
    )
    validate_target_fields(t.name, t.host, t.user, t.workspace, t.hil_policy, t.port, t.os)
    if t.device_id:
        try:
            if identity.mac_device_id(t.device_id.removeprefix("mac_")) != t.device_id:
                raise ValueError("invalid equipment identity")
            if any(identity.normalize_mac(mac) != mac for mac in t.mac_addresses):
                raise ValueError("MAC aliases must be normalized")
        except ValueError as exc:
            raise ConfigError(str(exc)) from exc
    if t.deploy_root:
        if not _WORKSPACE_RE.fullmatch(t.deploy_root) or ".." in t.deploy_root.split("/"):
            raise ConfigError("invalid deploy_root")
        if not PurePosixPath(t.workspace).is_relative_to(PurePosixPath(t.deploy_root)) or t.workspace == t.deploy_root:
            raise ConfigError("workspace must be a project subdirectory of deploy_root")
    for relative in t.persistent_paths:
        if not isinstance(relative, str) or not re.fullmatch(r"[A-Za-z0-9._/@+-]+", relative):
            raise ConfigError("persistent_paths must contain plain relative paths")
        path = PurePosixPath(relative)
        if path.is_absolute() or relative in ("", ".") or ".." in path.parts:
            raise ConfigError("persistent_paths must stay inside the workspace")
    return t


def load_targets(root: Path) -> dict[str, Target]:
    """Read `targets:` from project.yaml — a list of dicts (with `name`) or a name->dict map."""
    block = _read_project(root).get("targets") or []
    out: dict[str, Target] = {}
    if isinstance(block, dict):
        items = [(str(k), v) for k, v in block.items()]
    elif isinstance(block, list):
        items = [(str(v.get("name", "")) if isinstance(v, dict) else "", v) for v in block]
    else:
        raise ConfigError("`targets:` must be a list or a map")
    for name, raw in items:
        if name in out:
            raise ConfigError(f"duplicate target name {name!r}")
        out[name] = _to_target(name, raw)
    return out


def resolve_target(name: str = "", root: Path | None = None) -> Target:
    """The named target, or the only declared one when `name` is empty."""
    targets = load_targets(root or project_root())
    if not targets:
        raise ConfigError("no remote target declared in .codeanvil/project.yaml `targets:` (run init_codeanvil)")
    if not name:
        if len(targets) == 1:
            return next(iter(targets.values()))
        raise ConfigError(f"several targets declared ({', '.join(targets)}): pass `target`")
    if name not in targets:
        raise ConfigError(f"unknown target {name!r} (declared: {', '.join(targets)})")
    return targets[name]


def register_target(root: Path, target: Target) -> bool:
    """Add `target` to `targets:` if absent. Returns True when written.

    Rewrites project.yaml through yaml.safe_dump (comments are not preserved).
    """
    data = _read_project(root)
    existing = load_targets(root).get(target.name)
    if existing is not None:
        if existing != target:
            raise ConfigError(f"target {target.name!r} already exists with different connection settings")
        return False
    block = data.get("targets") or []
    fields = {
        "name": target.name, "host": target.host, "user": target.user,
        "workspace": target.workspace, "os": target.os, "arch": target.arch,
        "device": target.device, "hil_policy": target.hil_policy,
        "port": target.port,
    }
    if target.device_id:
        fields.update(device_id=target.device_id, deploy_root=target.deploy_root,
                      mac_addresses=list(target.mac_addresses), bootstrap_user=target.bootstrap_user)
    if target.persistent_paths:
        fields["persistent_paths"] = list(target.persistent_paths)
    if isinstance(block, dict):
        if target.name in block:
            return False
        block[target.name] = {k: v for k, v in fields.items() if k != "name"}
    elif isinstance(block, list):
        if any(isinstance(v, dict) and v.get("name") == target.name for v in block):
            return False
        block.append(fields)
    else:
        raise ConfigError("`targets:` must be a list or a map")
    data["targets"] = block
    project_yaml(root).write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return True


# --- key store -------------------------------------------------------------

def hil_dir(name: str) -> Path:
    if not _NAME_RE.match(name):
        raise ConfigError(f"invalid target name {name!r}")
    return Path.home() / ".codeanvil-config" / "hil" / name


def key_paths(name: str) -> dict[str, Path]:
    d = hil_dir(name)
    return {
        "dir": d,
        "deploy": d / "deploy_ed25519",
        "exec": d / "exec_ed25519",
        "known_hosts": d / "known_hosts",
    }


def ensure_key_dir(name: str) -> dict[str, Path]:
    """Create the key dir (0700, parents too) and an empty 0600 known_hosts."""
    paths = key_paths(name)
    d = paths["dir"]
    d.mkdir(parents=True, exist_ok=True)
    for p in (d.parent, d):
        os.chmod(p, 0o700)
    kh = paths["known_hosts"]
    if not kh.exists():
        kh.touch(mode=0o600)
    os.chmod(kh, 0o600)
    return paths


def lock_key_perms(paths: dict[str, Path]) -> None:
    """Private keys 0600, public keys 0644 (idempotent)."""
    for kind in ("deploy", "exec"):
        priv = paths[kind]
        if priv.exists():
            os.chmod(priv, 0o600)
        pub = priv.with_name(priv.name + ".pub")
        if pub.exists():
            os.chmod(pub, 0o644)

"""Authenticated equipment discovery and controller-local SSH key reuse."""

from __future__ import annotations

from dataclasses import dataclass, field
import importlib.util
import os
from pathlib import Path
import shlex
import subprocess

from codeanvil.config.paths import TEMPLATES_DIR


def _load_identity():
    path = TEMPLATES_DIR / "mcp/vsil_hil_mcp/vsil_hil_mcp/identity.py"
    spec = importlib.util.spec_from_file_location("_codeanvil_hil_identity", path)
    if spec is None or spec.loader is None:
        raise ValueError("bundled HIL identity helper is unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


identity = _load_identity()
AGENT_USER = "codeanvil-agent"
DEPLOY_ROOT = "/home/codeanvil-agent/projects"
DISCOVER_MACS = ('for iface in /sys/class/net/*; do '
                 '[ -e "$iface/device" ] || continue; cat "$iface/address"; done')


@dataclass
class Access:
    macs: list[str]
    key_identity: str | None
    login_user: str
    known_hosts: Path
    password: str | None = field(default=None, repr=False)


def _ssh_options(host: str, port: int, known_hosts: Path) -> list[str]:
    return ["-F", os.devnull, "-o", "IdentitiesOnly=yes", "-o", "IdentityAgent=none",
            "-o", f"GlobalKnownHostsFile={os.devnull}", "-o", f"UserKnownHostsFile={known_hosts}",
            "-o", "StrictHostKeyChecking=accept-new", "-o", "ConnectTimeout=5", "-p", str(port)]


def _macs(stdout: str) -> list[str]:
    values = []
    for line in stdout.splitlines():
        try:
            value = identity.normalize_mac(line)
        except ValueError:
            continue
        if value not in values:
            values.append(value)
    if not values:
        raise ValueError("SSH returned no physical interface MAC; no keys were generated")
    return sorted(values)


def _candidates(host: str, port: int, targets: list[dict]) -> list[tuple[str, str, list[str]]]:
    devices = identity.read_devices()
    preferred, others = [], []
    for device_id, row in devices.items():
        candidate = (row.get("key_identity", device_id), AGENT_USER, row["mac_addresses"])
        (preferred if {"host": host, "port": port} in row.get("endpoints", []) else others).append(candidate)
    for target in targets:
        name = target.get("device_id") or target.get("name", "")
        if not name:
            continue
        key = identity.local_key_identity(name) if target.get("device_id") else name
        expected = target.get("mac_addresses", [])
        if target.get("device_id") and not expected:
            expected = [identity.normalize_mac(target["device_id"].removeprefix("mac_"))]
        candidate = (key, target.get("user", AGENT_USER), expected)
        (preferred if target.get("host") == host and target.get("port", 22) == port else others).append(candidate)
    directory = identity.store_dir()
    if directory.exists():
        # Old aliases have no MAC registry. Successful dedicated-key authentication
        # followed by sysfs discovery identifies which legacy keys belong here.
        others.extend((path.parent.name, AGENT_USER, []) for path in sorted(directory.glob("*/exec_ed25519")))
    result = []
    for item in preferred + others:
        if item not in result:
            result.append(item)
    return result


def discover_with_keys(host: str, port: int, targets: list[dict]) -> Access | None:
    for key_id, user, expected_macs in _candidates(host, port, targets):
        keys = identity.key_paths(key_id)
        if not keys["exec"].is_file():
            continue
        argv = ["ssh", *_ssh_options(host, port, keys["known_hosts"]), "-i", str(keys["exec"]),
                "-o", "BatchMode=yes", f"{user}@{host}", DISCOVER_MACS]
        try:
            result = subprocess.run(argv, capture_output=True, text=True, timeout=15)
        except subprocess.TimeoutExpired:
            continue
        if result.returncode != 0:
            if "HOST IDENTIFICATION HAS CHANGED" in result.stderr or "Host key verification failed" in result.stderr:
                raise ValueError("SSH host authentication changed; inspect known_hosts before enrollment")
            continue
        macs = _macs(result.stdout)
        if expected_macs and not set(macs).intersection(expected_macs):
            raise ValueError("dedicated key reached different equipment; refusing to reassign its identity")
        return Access(macs, key_id, user, keys["known_hosts"])
    return None


def discover_with_admin(host: str, port: int, user: str, password: str, known_hosts: Path) -> Access:
    argv = ["sshpass", "-e", "ssh", *_ssh_options(host, port, known_hosts),
            "-o", "PubkeyAuthentication=no", "-o", "PreferredAuthentications=password", f"{user}@{host}", DISCOVER_MACS]
    result = subprocess.run(argv, env={**os.environ, "SSHPASS": password}, capture_output=True, text=True, timeout=20)
    if result.returncode:
        raise ValueError(f"admin SSH discovery failed (exit {result.returncode}); no keys generated")
    return Access(_macs(result.stdout), None, user, known_hosts, password)


def verify_access(host: str, port: int, key_id: str, expected_macs: list[str]) -> None:
    """Check the selected agent key and existing host pin before publishing mappings."""
    keys = identity.key_paths(key_id)
    argv = ["ssh", *_ssh_options(host, port, keys["known_hosts"]), "-i", str(keys["exec"]),
            "-o", "BatchMode=yes", f"{AGENT_USER}@{host}", DISCOVER_MACS]
    result = subprocess.run(argv, capture_output=True, text=True, timeout=15)
    if result.returncode or not set(_macs(result.stdout)).intersection(expected_macs):
        raise ValueError("dedicated SSH verification failed after bootstrap; registry and project unchanged")


def ensure_keys(key_id: str) -> dict[str, Path]:
    paths = identity.key_paths(key_id)
    paths["dir"].mkdir(parents=True, exist_ok=True)
    paths["dir"].chmod(0o700)
    paths["known_hosts"].touch(mode=0o600, exist_ok=True)
    paths["known_hosts"].chmod(0o600)
    for role in ("deploy", "exec"):
        private = paths[role]
        public = private.with_name(private.name + ".pub")
        if not private.exists():
            if public.exists():
                raise ValueError("public key exists without its private key; refusing regeneration")
            result = subprocess.run(["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-C", f"vsil-{role}-{key_id}", "-f", str(private)],
                                    capture_output=True, text=True)
            if result.returncode:
                raise ValueError("ssh-keygen failed")
        result = subprocess.run(["ssh-keygen", "-y", "-f", str(private)], stdin=subprocess.DEVNULL,
                                capture_output=True, text=True, timeout=10)
        if result.returncode or len(result.stdout.split()) < 2:
            raise ValueError("existing private key could not be read; refusing regeneration")
        derived = result.stdout.split()[:2]
        if public.exists():
            if public.read_text().split()[:2] != derived:
                raise ValueError("public/private key mismatch; restore the matching public key explicitly")
        else:
            public.write_text(" ".join(derived) + "\n")
        private.chmod(0o600)
    return paths


def bootstrap(access: Access, host: str, port: int, keys: dict[str, Path], workspace: str,
              deploy_root: str, install_deploy: bool, sudo_password: str = "") -> None:
    import base64
    script = (TEMPLATES_DIR / "mcp/vsil_hil_mcp/scripts/enroll_equipment.sh").read_text()
    header = {"HIL_WORKSPACE": workspace, "HIL_DEPLOY_ROOT": deploy_root,
              "HIL_INSTALL_DEPLOY": "yes" if install_deploy else "no"}
    for role in ("deploy", "exec"):
        text = keys[role].with_name(keys[role].name + ".pub").read_text().strip()
        parts = text.split()
        if len(parts) < 2 or parts[0] != "ssh-ed25519" or "\n" in text:
            raise ValueError("invalid dedicated public key")
        header[f"HIL_{role.upper()}_PUB"] = text
    payload = "\n".join(f"{name}={shlex.quote(value)}" for name, value in header.items()) + "\n" + script
    encoded = base64.b64encode(payload.encode()).decode()
    remote = f"sudo {'-S -p ' + shlex.quote('') if access.password is not None else '-n'} bash -c {shlex.quote(f'printf %s {encoded} | base64 -d | bash')}"
    argv = ["ssh", *_ssh_options(host, port, keys["known_hosts"])]
    kwargs = {}
    if access.password is None:
        argv += ["-i", str(identity.key_paths(access.key_identity)["exec"]), "-o", "BatchMode=yes"]
    else:
        argv = ["sshpass", "-e", *argv, "-o", "PubkeyAuthentication=no", "-o", "PreferredAuthentications=password"]
        kwargs = {"env": {**os.environ, "SSHPASS": access.password}, "input": sudo_password + "\n"}
    argv += [f"{access.login_user}@{host}", remote]
    result = subprocess.run(argv, capture_output=True, text=True, timeout=180, **kwargs)
    if result.returncode:
        raise ValueError(f"equipment bootstrap failed (exit {result.returncode}); project registration unchanged")

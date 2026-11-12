"""Enroll authenticated hardware by MAC and reuse this controller's keys."""

import getpass
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import uuid

import yaml

from codeanvil.config.logger import get_logger
from codeanvil.config.paths import find_manifest
from . import hil_enrollment as enrollment

log = get_logger(__name__)
AGENT_USER = enrollment.AGENT_USER
PASSWORD_ENV = "CODEANVIL_HIL_PASSWORD"
SUDO_PASSWORD_ENV = "CODEANVIL_HIL_SUDO_PASSWORD"
_USER = re.compile(r"[a-z_][a-z0-9_-]{0,31}")
_HOST = re.compile(r"[A-Za-z0-9][A-Za-z0-9.:-]{0,252}")


def _target_rows(data: dict) -> list[dict]:
    block = data.get("targets") or []
    if isinstance(block, dict):
        rows = [dict(row, name=name) for name, row in block.items() if isinstance(row, dict)]
        if len(rows) != len(block):
            raise ValueError("each target must be a mapping")
    elif isinstance(block, list):
        rows = block
    else:
        raise ValueError("`targets:` must be a list or a map")
    if any(not isinstance(row, dict) or not isinstance(row.get("name"), str) for row in rows):
        raise ValueError("each target needs a name")
    if len({row["name"] for row in rows}) != len(rows):
        raise ValueError("duplicate target names; resolve project metadata before enrollment")
    return rows


def _passwords(user: str, host: str, password: str | None, sudo_password: str | None):
    password = password or os.environ.get(PASSWORD_ENV)
    prompted = password is None
    if password is None:
        password = getpass.getpass(f"SSH password for {user}@{host}: ")
    if not password:
        raise ValueError("no SSH password provided")
    sudo_password = sudo_password or os.environ.get(SUDO_PASSWORD_ENV)
    if sudo_password is None:
        sudo_password = (getpass.getpass("sudo password (Enter reuses SSH password): ") or password) if prompted else password
    return password, sudo_password


def _copy_known_hosts(source: Path, destination: Path):
    if source == destination or not source.exists():
        return
    lines = destination.read_text().splitlines() if destination.exists() else []
    for line in source.read_text().splitlines():
        if line not in lines:
            lines.append(line)
    destination.write_text("\n".join(lines) + "\n")
    destination.chmod(0o600)


def _known_endpoint_pin(host: str, port: int, rows: list[dict]) -> Path | None:
    records = [(name, row) for name, row in enrollment.identity.read_devices().items()
               if {"host": host, "port": port} in row.get("endpoints", [])]
    if len(records) > 1:
        raise ValueError("endpoint has multiple local equipment identities; resolve it before enrollment")
    if records:
        name, record = records[0]
        keys = enrollment.identity.key_paths(record.get("key_identity", name))
    else:
        legacy = [enrollment.identity.key_paths(row["name"]) for row in rows
                  if not row.get("device_id") and row.get("host") == host and row.get("port", 22) == port]
        legacy = [keys for keys in legacy if keys["dir"].exists()]
        if not legacy:
            return None  # A cloned declaration without this PC's keys is first contact.
        if len(legacy) > 1:
            raise ValueError("endpoint has multiple local legacy key stores; resolve them before enrollment")
        keys = legacy[0]
    if any(not keys[role].is_file() for role in ("exec", "deploy")):
        raise ValueError("registered equipment keys are missing; restore them explicitly, no regeneration")
    if not keys["known_hosts"].is_file() or not keys["known_hosts"].read_text().strip():
        raise ValueError("registered equipment host pin is missing; restore it explicitly before admin access")
    return keys["known_hosts"]


def _matching_project_rows(rows: list[dict], device_id: str, key_id: str, host: str, port: int):
    matches = [old for old in rows if old.get("device_id") == device_id or
               (not old.get("device_id") and old["name"] == key_id)]
    if not matches:
        # A new controller has no old key directory. Its authenticated endpoint
        # can still migrate the sole public legacy declaration without duplicating it.
        matches = [old for old in rows if not old.get("device_id") and
                   old.get("host") == host and old.get("port", 22) == port]
    return matches


def _identity_for(access, rows: list[dict], host: str, port: int):
    known = enrollment.identity.find_device(access.macs)
    public = [row for row in rows if row.get("device_id") and set(access.macs).intersection(row.get("mac_addresses", []))]
    if len({row["device_id"] for row in public}) > 1:
        raise ValueError("authenticated interfaces match multiple project identities")
    device_id = known[0] if known else public[0]["device_id"] if public else enrollment.identity.mac_device_id(access.macs[0])
    previous = known[1] if known else {}
    if not known and not public:
        for record in enrollment.identity.read_devices().values():
            if {"host": host, "port": port} in record.get("endpoints", []):
                raise ValueError("endpoint belongs to unrecognized equipment; no keys will be regenerated")
    key_id = previous.get("key_identity") or access.key_identity
    if not key_id:
        # An authenticated admin may restore legacy keys associated with this
        # declared endpoint; never choose an unrelated legacy directory by guess.
        aliases = [row["name"] for row in rows if not row.get("device_id") and row.get("host") == host and row.get("port", 22) == port]
        aliases.append(re.sub(r"[.:]", "_", host))
        key_id = next((name for name in aliases if enrollment.identity.key_paths(name)["exec"].exists()), device_id)
    for owner, record in enrollment.identity.read_devices().items():
        if record.get("key_identity", owner) == key_id and owner != device_id:
            raise ValueError("local keys already belong to different equipment; refusing reassignment")
    matches = _matching_project_rows(rows, device_id, key_id, host, port)
    if len(matches) > 1:
        raise ValueError("multiple project aliases reference this equipment; resolve them before enrollment")
    if known:
        for role in ("exec", "deploy"):
            keys = enrollment.identity.key_paths(key_id)
            if not keys[role].exists():
                raise ValueError("registered equipment keys are missing; restore them explicitly, no regeneration")
    macs = sorted(set(access.macs).union(previous.get("mac_addresses", []),
                  *(row.get("mac_addresses", []) for row in public)))
    return device_id, key_id, macs


def _link_project(manifest: Path, data: dict, rows: list[dict], device_id: str, key_id: str,
                  row: dict, host: str, port: int, admin: str, workspace: str):
    matches = _matching_project_rows(rows, device_id, key_id, host, port)
    if len(matches) > 1:
        raise ValueError("multiple project aliases reference this equipment; resolve them before enrollment")
    old = matches[0] if matches else {}
    entry = {**old, "name": old.get("name", device_id), "device_id": device_id,
             "mac_addresses": row["mac_addresses"], "bootstrap_user": admin,
             "host": host, "port": port, "user": AGENT_USER,
             "workspace": workspace, "deploy_root": enrollment.DEPLOY_ROOT, "os": "linux", "hil_policy": "trusted"}
    # Key locations are local controller details, never shared metadata.
    for private_field in ("key_identity", "key_path", "exec_key", "deploy_key", "known_hosts"):
        entry.pop(private_field, None)
    rows = [entry if item is old else item for item in rows]
    if not old:
        rows.append(entry)
    if isinstance(data.get("targets"), dict):
        data["targets"] = {item["name"]: {k: v for k, v in item.items() if k != "name"} for item in rows}
    else:
        data["targets"] = rows
    manifest.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def cmd_credential_setup(user: str, ip: str, password: str | None = None,
                         sudo_password: str | None = None, port: int = 22, os_: str = "linux") -> None:
    """Discover MAC through authenticated SSH; enroll/link a UUID workspace."""
    try:
        manifest = find_manifest(Path.cwd())
        if manifest is None:
            raise ValueError("not inside a scaffolded project — .codeanvil/project.yaml not found")
        if os_ != "linux":
            raise ValueError("credential bootstrap is implemented for Linux targets only")
        if type(port) is not int or not 1 <= port <= 65535:
            raise ValueError("SSH port must be an integer from 1 to 65535")
        if not _USER.fullmatch(user) or not _HOST.fullmatch(ip):
            raise ValueError("invalid admin user or host")
        data = yaml.safe_load(manifest.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("project.yaml must be a mapping")
        project_id = str(uuid.UUID(str(data.get("id", ""))))
        rows = _target_rows(data)
        workspace = f"{enrollment.DEPLOY_ROOT}/{project_id}"
        with tempfile.TemporaryDirectory(prefix="codeanvil-enroll-") as temporary:
            endpoint_pin = _known_endpoint_pin(ip, port, rows)
            access = enrollment.discover_with_keys(ip, port, rows)
            if access is None:
                password, sudo_password = _passwords(user, ip, password, sudo_password)
                access = enrollment.discover_with_admin(ip, port, user, password,
                                                       endpoint_pin or Path(temporary) / "known_hosts")
            device_id, key_id, macs = _identity_for(access, rows, ip, port)
            keys = enrollment.ensure_keys(key_id)
            _copy_known_hosts(access.known_hosts, keys["known_hosts"])
            try:
                enrollment.bootstrap(access, ip, port, keys, workspace, enrollment.DEPLOY_ROOT,
                                     install_deploy=key_id == device_id, sudo_password=sudo_password or password or "")
            except ValueError:
                if access.password is not None:
                    raise
                # Key login may work while sudo setup needs the administrator once.
                password, sudo_password = _passwords(user, ip, password, sudo_password)
                admin_access = enrollment.discover_with_admin(ip, port, user, password, keys["known_hosts"])
                if not set(admin_access.macs).intersection(access.macs):
                    raise ValueError("equipment changed during bootstrap; registration unchanged")
                _copy_known_hosts(admin_access.known_hosts, keys["known_hosts"])
                enrollment.bootstrap(admin_access, ip, port, keys, workspace, enrollment.DEPLOY_ROOT,
                                     install_deploy=key_id == device_id, sudo_password=sudo_password)
            enrollment.verify_access(ip, port, key_id, access.macs)
            device_id, device = enrollment.identity.remember_device(macs, ip, port, user, key_id, device_id)
            _link_project(manifest, data, rows, device_id, key_id, device, ip, port, user, workspace)
        log.info("Equipment %s linked to %s at %s:%s; local keys reused when present.", device_id, workspace, ip, port)
        log.info("Access is ready; target tool/project updates remain after the pre-HW review checkpoint.")
    except (ValueError, OSError, subprocess.SubprocessError, yaml.YAMLError) as exc:
        log.error("%s", exc)
        sys.exit(1)

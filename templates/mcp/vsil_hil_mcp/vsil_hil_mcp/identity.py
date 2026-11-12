"""Local equipment registry shared by enrollment and the standalone MCP server.

Public project metadata identifies equipment by MAC. Private keys stay on each
client; a local key_identity may point at an adopted legacy key directory.
"""

from __future__ import annotations

import os
from pathlib import Path
import re
import tempfile

import yaml

_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}")


def normalize_mac(value: str) -> str:
    if not isinstance(value, str):
        raise ValueError("hardware MAC must be a string")
    compact = value.strip().lower().replace(":", "").replace("-", "")
    if not re.fullmatch(r"[0-9a-f]{12}", compact) or compact == "000000000000" or int(compact[:2], 16) & 1:
        raise ValueError(f"invalid unicast hardware MAC {value!r}")
    return ":".join(compact[i:i + 2] for i in range(0, 12, 2))


def mac_device_id(value: str) -> str:
    return "mac_" + normalize_mac(value).replace(":", "")


def store_dir() -> Path:
    return Path.home() / ".codeanvil-config" / "hil"


def key_paths(key_identity: str) -> dict[str, Path]:
    if not isinstance(key_identity, str) or not _NAME.fullmatch(key_identity):
        raise ValueError("invalid local key identity")
    directory = store_dir() / key_identity
    return {"dir": directory, "deploy": directory / "deploy_ed25519",
            "exec": directory / "exec_ed25519", "known_hosts": directory / "known_hosts"}


def read_devices() -> dict[str, dict]:
    path = store_dir() / "devices.yaml"
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("version") != 1 or not isinstance(data.get("devices"), dict):
        raise ValueError("invalid local HIL equipment registry")
    devices = data["devices"]
    for device_id, row in devices.items():
        if not isinstance(row, dict) or not isinstance(device_id, str) or not device_id.startswith("mac_"):
            raise ValueError("invalid equipment registry entry")
        if mac_device_id(device_id[4:]) != device_id:
            raise ValueError("invalid equipment identity")
        key_paths(row.get("key_identity", device_id))
        if not isinstance(row.get("mac_addresses"), list) or not row["mac_addresses"]:
            raise ValueError("equipment entry needs observed MAC addresses")
        if any(normalize_mac(mac) != mac for mac in row["mac_addresses"]):
            raise ValueError("equipment MAC aliases must be normalized")
    return devices


def local_key_identity(device_id: str) -> str:
    """A second client uses its own canonical keys, never another client's path."""
    if mac_device_id(device_id.removeprefix("mac_")) != device_id:
        raise ValueError("invalid equipment identity")
    return read_devices().get(device_id, {}).get("key_identity", device_id)


def find_device(macs: list[str], devices: dict[str, dict] | None = None) -> tuple[str, dict] | None:
    observed = {normalize_mac(mac) for mac in macs}
    matches = [(name, row) for name, row in (read_devices() if devices is None else devices).items()
               if observed.intersection(row["mac_addresses"])]
    if len(matches) > 1:
        raise ValueError("observed interfaces match several equipment records; resolve the registry explicitly")
    return matches[0] if matches else None


def remember_device(macs: list[str], host: str, port: int, bootstrap_user: str,
                    key_identity: str | None = None, device_id: str | None = None) -> tuple[str, dict]:
    """Merge authenticated interface observations without changing established keys."""
    observed = sorted({normalize_mac(mac) for mac in macs})
    if not observed:
        raise ValueError("no physical interface MAC was observed; no keys created")
    devices = read_devices()
    known = find_device(observed, devices)
    if device_id and (mac_device_id(device_id.removeprefix("mac_")) != device_id
                      or normalize_mac(device_id.removeprefix("mac_")) not in observed):
        raise ValueError("declared stable equipment identity must be among its authenticated aliases")
    if known and device_id and known[0] != device_id:
        raise ValueError("declared identity conflicts with the local equipment registry")
    device_id, previous = known if known else (device_id or mac_device_id(observed[0]), {})
    existing_key = previous.get("key_identity")
    if existing_key and key_identity and existing_key != key_identity:
        raise ValueError("equipment already has a different local key identity; refusing to replace it")
    selected_key = existing_key or key_identity or device_id
    key_paths(selected_key)
    endpoints = list(previous.get("endpoints", []))
    endpoint = {"host": host, "port": port}
    if endpoint not in endpoints:
        endpoints.append(endpoint)
    row = {"mac_addresses": sorted(set(observed).union(previous.get("mac_addresses", []))),
           "endpoints": endpoints, "bootstrap_user": bootstrap_user, "key_identity": selected_key}
    devices[device_id] = row
    directory = store_dir()
    directory.mkdir(parents=True, exist_ok=True)
    directory.chmod(0o700)
    # Atomic replacement keeps a failed write from destroying the existing mapping.
    fd, temporary = tempfile.mkstemp(prefix=".devices-", dir=directory)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            yaml.safe_dump({"version": 1, "devices": devices}, stream, sort_keys=False)
        os.chmod(temporary, 0o600)
        os.replace(temporary, directory / "devices.yaml")
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return device_id, row

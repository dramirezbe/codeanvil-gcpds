"""SUB-006/config — Load, validate and publish config_status.v1.

Atomically accepts or rejects site-config.json and the station reference.
Keeps the last valid configuration on reject.
"""
from __future__ import annotations

import hashlib
import json
import os
import socket
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from fm_supervisor.config.logger import get_logger
from fm_supervisor.config.paths import CONFIG_FILE, CONFIG_SOCK, STATION_REF_FILE
from fm_supervisor.lib.framing import send_msg

log = get_logger(__name__)

_REQUIRED_FIELDS = {"station_id", "station_name", "latitude_deg", "longitude_deg", "ntp_sources"}
_FREQ_MIN_MHZ = 87.5
_FREQ_MAX_MHZ = 108.0


@dataclass
class SiteConfig:
    station_id: str
    station_name: str
    latitude_deg: float
    longitude_deg: float
    ntp_sources: list[str]
    scan_start_mhz: float = 87.5
    scan_end_mhz: float = 108.0
    step_mhz: float = 8.0
    lna_gain_db: int = 0
    rf_gain_db: int = 0
    bb_gain_db: int = 0
    raw: dict = field(default_factory=dict)
    sha256: str = ""

    def validate(self) -> None:
        if not (isinstance(self.latitude_deg, float) and -90 <= self.latitude_deg <= 90):
            raise ValueError(f"latitude_deg {self.latitude_deg} out of [-90, 90]")
        if not (isinstance(self.longitude_deg, float) and -180 <= self.longitude_deg <= 180):
            raise ValueError(f"longitude_deg {self.longitude_deg} out of [-180, 180]")
        if not self.ntp_sources:
            raise ValueError("ntp_sources must not be empty")
        if not (self.scan_start_mhz >= _FREQ_MIN_MHZ and self.scan_end_mhz <= _FREQ_MAX_MHZ):
            raise ValueError(f"scan range [{self.scan_start_mhz}, {self.scan_end_mhz}] out of FM band")


def _load_config(path: Path) -> tuple[SiteConfig, str]:
    text = path.read_text()
    sha = hashlib.sha256(text.encode()).hexdigest()
    raw = json.loads(text)
    missing = _REQUIRED_FIELDS - raw.keys()
    if missing:
        raise ValueError(f"missing required fields: {missing}")
    cfg = SiteConfig(
        station_id=str(raw["station_id"]),
        station_name=str(raw["station_name"]),
        latitude_deg=float(raw["latitude_deg"]),
        longitude_deg=float(raw["longitude_deg"]),
        ntp_sources=list(raw["ntp_sources"]),
        scan_start_mhz=float(raw.get("scan_start_mhz", 87.5)),
        scan_end_mhz=float(raw.get("scan_end_mhz", 108.0)),
        step_mhz=float(raw.get("step_mhz", 8.0)),
        lna_gain_db=int(raw.get("lna_gain_db", 0)),
        rf_gain_db=int(raw.get("rf_gain_db", 0)),
        bb_gain_db=int(raw.get("bb_gain_db", 0)),
        raw=raw,
        sha256=sha,
    )
    cfg.validate()
    return cfg, sha


class ConfigPublisher:
    """Loads config, publishes config_status.v1 on the config socket."""

    def __init__(self, config_path: Path = CONFIG_FILE, sock_path: Path = CONFIG_SOCK) -> None:
        self._config_path = config_path
        self._sock_path = sock_path
        self._current: Optional[SiteConfig] = None
        self._clients: list[socket.socket] = []
        self._server: Optional[socket.socket] = None

    def load(self) -> bool:
        """Load or reload config. Returns True if accepted, False if rejected (old kept)."""
        try:
            cfg, sha = _load_config(self._config_path)
            self._current = cfg
            log.info(f"config accepted station_id={cfg.station_id} sha={sha[:8]}")
            return True
        except (FileNotFoundError, json.JSONDecodeError, ValueError) as exc:
            log.warning(f"config rejected: {exc}; keeping previous config")
            return False

    def start_server(self) -> None:
        self._sock_path.parent.mkdir(parents=True, exist_ok=True)
        if self._sock_path.exists():
            self._sock_path.unlink()
        srv = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        srv.bind(str(self._sock_path))
        srv.listen(32)
        srv.setblocking(False)
        self._server = srv
        log.info(f"config publisher on {self._sock_path}")

    def publish(self) -> None:
        """Publish current config_status.v1 to all connected clients."""
        if self._server is None:
            return
        try:
            while True:
                c, _ = self._server.accept()
                c.setblocking(False)
                self._clients.append(c)
                # Send the current config immediately on connect
                if self._current is not None:
                    try:
                        send_msg(c, self._make_msg())
                    except Exception:
                        pass
        except BlockingIOError:
            pass

    def broadcast(self) -> None:
        """Broadcast current config to all existing clients."""
        if self._current is None:
            return
        msg = self._make_msg()
        dead = []
        for c in self._clients:
            try:
                send_msg(c, msg)
            except Exception:
                dead.append(c)
        for c in dead:
            self._clients.remove(c)
            c.close()

    def _make_msg(self) -> dict:
        cfg = self._current
        assert cfg is not None
        return {
            "schema_version": "1.0",
            "station_id": cfg.station_id,
            "station_name": cfg.station_name,
            "latitude_deg": cfg.latitude_deg,
            "longitude_deg": cfg.longitude_deg,
            "ntp_sources": cfg.ntp_sources,
            "scan_start_mhz": cfg.scan_start_mhz,
            "scan_end_mhz": cfg.scan_end_mhz,
            "step_mhz": cfg.step_mhz,
            "lna_gain_db": cfg.lna_gain_db,
            "rf_gain_db": cfg.rf_gain_db,
            "bb_gain_db": cfg.bb_gain_db,
            "config_sha256": cfg.sha256,
            "ts_utc_us": int(time.time() * 1_000_000),
        }

    @property
    def current(self) -> Optional[SiteConfig]:
        return self._current

    def close(self) -> None:
        for c in self._clients:
            c.close()
        self._clients.clear()
        if self._server:
            self._server.close()
            self._server = None

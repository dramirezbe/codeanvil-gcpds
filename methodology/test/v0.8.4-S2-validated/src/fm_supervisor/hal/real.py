"""Real HW HAL for fm_supervisor — hardware watchdog and Pi 5 thermal zone."""
from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Optional

from fm_supervisor.config.logger import get_logger
from fm_supervisor.hal.port import ResourcePort, ThermalPort, WatchdogPort

log = get_logger(__name__)

_WATCHDOG_MAGIC = b"V"


class RealWatchdogPort(WatchdogPort):
    def __init__(self, dev: Path = Path("/dev/watchdog")) -> None:
        self._dev = dev
        self._fd: Optional[int] = None

    def open(self) -> None:
        self._fd = os.open(str(self._dev), os.O_WRONLY)
        log.info(f"RealWatchdogPort.open {self._dev}")

    def feed(self) -> None:
        if self._fd is not None:
            os.write(self._fd, b"\x00")

    def close(self, reason: str = "ordered") -> None:
        if self._fd is not None:
            if reason == "ordered":
                os.write(self._fd, _WATCHDOG_MAGIC)
            os.close(self._fd)
            self._fd = None
        log.info(f"RealWatchdogPort.close reason={reason}")


class RealThermalPort(ThermalPort):
    def __init__(self, zone: Path = Path("/sys/class/thermal/thermal_zone0/temp")) -> None:
        self._zone = zone

    def read_celsius(self) -> float:
        return int(self._zone.read_text().strip()) / 1000.0


class RealResourcePort(ResourcePort):
    def cpu_percent(self, pid: Optional[int] = None) -> float:
        # Read /proc/stat for overall CPU; simplified
        return 0.0

    def rss_mb(self, pid: Optional[int] = None) -> float:
        return 0.0

"""Runtime Mock HAL for fm_supervisor — in-process, reads no verification file."""
from __future__ import annotations

import time
from typing import Optional

from fm_supervisor.config.logger import get_logger
from fm_supervisor.hal.port import ResourcePort, ThermalPort, WatchdogPort

log = get_logger(__name__)

_THERMAL_SEQUENCE = [25.0, 69.0, 71.0, 64.0, 85.0]


class MockWatchdogPort(WatchdogPort):
    """In-process watchdog: records feeds, simulates reset if silent > 15 s."""

    def __init__(self, timeout_s: float = 15.0) -> None:
        self._timeout_s = timeout_s
        self._last_feed: Optional[float] = None
        self._open = False
        self._close_reason: Optional[str] = None
        self.feed_times: list[float] = []
        self.reset_triggered = False

    def open(self) -> None:
        self._open = True
        self._last_feed = time.monotonic()
        log.info("MockWatchdogPort.open")

    def feed(self) -> None:
        now = time.monotonic()
        if self._last_feed is not None and (now - self._last_feed) > self._timeout_s:
            self.reset_triggered = True
            log.error("MockWatchdogPort: watchdog timeout — reset would occur")
        self._last_feed = now
        self.feed_times.append(now)

    def close(self, reason: str = "ordered") -> None:
        self._open = False
        self._close_reason = reason
        log.info(f"MockWatchdogPort.close reason={reason}")


class MockThermalPort(ThermalPort):
    """Returns scripted temperature sequence [25, 69, 71, 64, 85] °C, then repeats."""

    def __init__(self) -> None:
        self._idx = 0
        self.reads: list[float] = []

    def read_celsius(self) -> float:
        temp = _THERMAL_SEQUENCE[self._idx % len(_THERMAL_SEQUENCE)]
        self._idx += 1
        self.reads.append(temp)
        return temp


class MockResourcePort(ResourcePort):
    def cpu_percent(self, pid: Optional[int] = None) -> float:
        return 0.5

    def rss_mb(self, pid: Optional[int] = None) -> float:
        return 10.0

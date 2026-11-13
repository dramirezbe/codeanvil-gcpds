"""SUB-006/watchdog — Hardware watchdog and thermal management.

Feeds the watchdog every 5 s ONLY when the supervision loop ran.
Reads SoC temperature every 10 s, raises/clears the thermal condition at 70/65 °C.
VL-2 only for the real HAL; Mock HAL proves the feed/hold logic at VL-0/1.
"""
from __future__ import annotations

import time
from typing import Optional

from fm_supervisor.config.logger import get_logger
from fm_supervisor.hal.port import ThermalPort, WatchdogPort

log = get_logger(__name__)

_FEED_INTERVAL_S = 5.0
_TEMP_INTERVAL_S = 10.0
_TEMP_RAISE_C = 70.0
_TEMP_CLEAR_C = 65.0


class WatchdogManager:
    """Feeds the hardware watchdog and manages the thermal condition."""

    def __init__(self, wdog: WatchdogPort, thermal: ThermalPort) -> None:
        self._wdog = wdog
        self._thermal = thermal
        self._last_feed = 0.0
        self._last_temp = 0.0
        self._thermal_condition = False
        self._loop_ran = False

    def open(self) -> None:
        self._wdog.open()
        self._last_feed = time.monotonic()

    def mark_loop_ran(self) -> None:
        """Call once per supervision tick to allow the watchdog to be fed."""
        self._loop_ran = True

    def tick(self) -> None:
        """Call on the supervision tick (≈1 s). Feeds watchdog and reads temperature."""
        now = time.monotonic()
        if self._loop_ran and (now - self._last_feed) >= _FEED_INTERVAL_S:
            self._wdog.feed()
            self._last_feed = now
            self._loop_ran = False

        if (now - self._last_temp) >= _TEMP_INTERVAL_S:
            self._check_temperature()
            self._last_temp = now

    def _check_temperature(self) -> None:
        try:
            temp = self._thermal.read_celsius()
        except Exception as exc:
            log.warning(f"thermal read failed: {exc}")
            return
        if not self._thermal_condition and temp >= _TEMP_RAISE_C:
            self._thermal_condition = True
            log.warning(f"thermal condition raised at {temp:.1f} °C")
        elif self._thermal_condition and temp <= _TEMP_CLEAR_C:
            self._thermal_condition = False
            log.info(f"thermal condition cleared at {temp:.1f} °C")
        else:
            log.debug(f"soc_temp={temp:.1f} °C thermal_condition={self._thermal_condition}")

    @property
    def thermal_condition(self) -> bool:
        return self._thermal_condition

    def close(self, reason: str = "ordered") -> None:
        self._wdog.close(reason)

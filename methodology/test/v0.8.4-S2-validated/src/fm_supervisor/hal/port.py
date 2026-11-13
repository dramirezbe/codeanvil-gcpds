"""HAL port interfaces for fm_supervisor."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional


class WatchdogPort(ABC):
    @abstractmethod
    def open(self) -> None: ...

    @abstractmethod
    def feed(self) -> None:
        """Feed the watchdog; must be called at least every 15 s."""

    @abstractmethod
    def close(self, reason: str = "ordered") -> None: ...


class ThermalPort(ABC):
    @abstractmethod
    def read_celsius(self) -> float:
        """Read SoC temperature in °C."""


class ResourcePort(ABC):
    @abstractmethod
    def cpu_percent(self, pid: Optional[int] = None) -> float: ...

    @abstractmethod
    def rss_mb(self, pid: Optional[int] = None) -> float: ...

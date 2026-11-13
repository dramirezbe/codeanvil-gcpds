"""HAL port for fm_store_alert — socket data sources."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class StoreDataPort(ABC):
    """Abstract source of scan records and calibration validity messages."""

    @abstractmethod
    def next_scan_record(self, timeout_s: float = 10.0) -> dict:
        """Block until one scan_records.v1 message arrives."""

    @abstractmethod
    def next_calv(self, timeout_s: float = 10.0) -> dict:
        """Block until one calibration_validity message arrives."""

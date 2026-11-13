"""HAL port for fm_time — NTP query abstraction."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class NtpSample:
    offset_ms: Optional[float]  # None when unreachable
    delay_ms: Optional[float]
    source_id: str
    leap: int = 0  # 0=no leap, 1=+1 s, 2=−1 s, 3=alarm


class NtpPort(ABC):
    @abstractmethod
    def query(self, server: str) -> NtpSample:
        """Query one NTP server; never raises — returns None offset on failure."""

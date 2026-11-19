"""HAL port interfaces for fm_measure."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Sequence


class SdrUnavailable(Exception):
    """Raised when the SDR device cannot be opened or sustains an error."""


@dataclass
class SdrConfig:
    center_hz: float
    sample_rate_hz: float = 10_000_000.0
    lna_gain_db: int = 0
    rf_gain_db: int = 0
    bb_gain_db: int = 0
    agc: bool = False
    antenna_power: bool = False
    baseband_filter_hz: float = 10_000_000.0

    def validate(self) -> None:
        """Raise ValueError for settings outside the allowed range."""
        if not (1_000_000 <= self.center_hz <= 6_000_000_000):
            raise ValueError(f"center_hz {self.center_hz} out of range [1 MHz, 6 GHz]")
        if not (2_000_000 <= self.sample_rate_hz <= 20_000_000):
            raise ValueError(f"sample_rate_hz {self.sample_rate_hz} out of range [2, 20] Msps")
        if not (0 <= self.lna_gain_db <= 40):
            raise ValueError(f"lna_gain_db {self.lna_gain_db} out of range [0, 40]")
        if not (0 <= self.rf_gain_db <= 14):
            raise ValueError(f"rf_gain_db {self.rf_gain_db} out of range [0, 14]")
        if not (0 <= self.bb_gain_db <= 62):
            raise ValueError(f"bb_gain_db {self.bb_gain_db} out of range [0, 62]")
        if self.agc:
            raise ValueError("AGC must be disabled")


@dataclass
class CaptureFrame:
    """One frame of int8 interleaved I/Q samples."""
    samples: bytes  # 131072 int8 values (65536 complex samples)
    clipped: bool = False
    overflow: bool = False


@dataclass
class CaptureMeta:
    center_hz: float
    sample_rate_hz: float
    rf_amp_db: int
    lna_db: int
    baseband_db: int
    agc_enabled: bool
    clipped: bool
    clip_count: int
    dropped_frames: int
    overflow_events: int
    retune_failed: bool


class SdrPort(ABC):
    """Abstract SDR hardware port."""

    @abstractmethod
    def open(self) -> None:
        """Open and claim the device; raises SdrUnavailable on failure."""

    @abstractmethod
    def info(self) -> dict:
        """Return device identity information."""

    @abstractmethod
    def configure(self, config: SdrConfig) -> None:
        """Apply configuration; validates before calling the device."""

    @abstractmethod
    def read_frames(self, n: int, timeout_s: float = 2.0) -> list[CaptureFrame]:
        """Read n frames; raises SdrUnavailable on sustained error."""

    @abstractmethod
    def close(self) -> None:
        """Release the device."""

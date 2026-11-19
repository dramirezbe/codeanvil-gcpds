"""HAL port interfaces for fm_report (SDD §1.3.2)."""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class ReportStorePort(ABC):
    """Abstract filesystem store for the screening report."""

    @abstractmethod
    def open_run(self, run_id: str) -> Path:
        """Create the run directory and return its path."""

    @abstractmethod
    def append_scan(self, run_id: str, lines: list[str]) -> None:
        """Append CSV lines to the current segment file."""

    @abstractmethod
    def fsync(self, run_id: str) -> None:
        """Flush and fsync the current segment file."""

    @abstractmethod
    def open_segment(self, run_id: str, segment_id: str) -> None:
        """Open a new segment file within the run."""

    @abstractmethod
    def close_segment(self, run_id: str, segment_id: str) -> None:
        """Close and finalise the current segment."""

    @abstractmethod
    def free_space(self) -> int:
        """Return available bytes on the report filesystem."""

    @abstractmethod
    def rename_atomic(self, src: Path, dst: Path) -> None:
        """Atomic rename (os.replace semantics)."""

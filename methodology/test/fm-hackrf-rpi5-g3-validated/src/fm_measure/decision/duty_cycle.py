"""SUB-001/duty_cycle — Accumulate occupancy counts per UTC-aligned interval.

Publishes duty_cycle.v1 when each 3600 s interval closes.
Counts: Occupied, Free, Uncertain per channel per interval.
Duty cycle = Occupied / (Occupied + Free + Uncertain).
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional

from fm_measure.decision.detector import OccupancyResult

_INTERVAL_S = 3600  # 1 hour UTC-aligned


@dataclass
class DutyCycleRecord:
    channel: int
    interval_start_utc_s: int
    interval_end_utc_s: int
    occupied_count: int
    free_count: int
    uncertain_count: int
    duty_cycle_pct: Optional[float]  # None when denominator = 0
    uncertain_fraction_pct: Optional[float]


@dataclass
class _Bucket:
    occupied: int = 0
    free: int = 0
    uncertain: int = 0

    @property
    def total(self) -> int:
        return self.occupied + self.free + self.uncertain


class DutyCycleAccumulator:
    def __init__(self, interval_s: int = _INTERVAL_S) -> None:
        self._interval_s = interval_s
        self._current_start: Optional[int] = None   # UTC seconds
        self._buckets: dict[int, _Bucket] = {}      # channel → bucket

    def add(self, occupancy: list[OccupancyResult], scan_utc_s: float) -> Optional[list[DutyCycleRecord]]:
        """Add one scan. Returns closed interval records if the interval just closed."""
        interval_start = int(scan_utc_s // self._interval_s) * self._interval_s

        # Interval boundary: publish previous and reset
        if self._current_start is not None and interval_start != self._current_start:
            records = self._close()
            self._current_start = interval_start
            self._buckets = {}
            self._accumulate(occupancy)
            return records

        if self._current_start is None:
            self._current_start = interval_start

        self._accumulate(occupancy)
        return None

    def _accumulate(self, occupancy: list[OccupancyResult]) -> None:
        for r in occupancy:
            b = self._buckets.setdefault(r.channel, _Bucket())
            if r.state == "Occupied":
                b.occupied += 1
            elif r.state == "Free":
                b.free += 1
            else:
                b.uncertain += 1

    def _close(self) -> list[DutyCycleRecord]:
        start = self._current_start
        end = start + self._interval_s  # type: ignore[operator]
        records = []
        for ch, b in sorted(self._buckets.items()):
            denom = b.total
            dc = round(100.0 * b.occupied / denom, 2) if denom > 0 else None
            uf = round(100.0 * b.uncertain / denom, 2) if denom > 0 else None
            records.append(DutyCycleRecord(
                channel=ch,
                interval_start_utc_s=start,
                interval_end_utc_s=end,
                occupied_count=b.occupied,
                free_count=b.free,
                uncertain_count=b.uncertain,
                duty_cycle_pct=dc,
                uncertain_fraction_pct=uf,
            ))
        return records

    def flush(self) -> Optional[list[DutyCycleRecord]]:
        """Force-close current interval (called at shutdown)."""
        if self._current_start is None or not self._buckets:
            return None
        return self._close()

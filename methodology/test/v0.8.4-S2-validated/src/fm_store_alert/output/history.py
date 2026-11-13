"""SUB-002/history — 744 h ring buffer of 60 s bins per channel.

Keeps the latest scan and answers bounded history queries (SSC-HIST-001).
Memory ceiling: 512 MB (enforced by the 744 h × 199 ch × 60 s bin design).
"""
from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass
from typing import Optional

_RING_HOURS = 744          # 31 days
_BIN_S = 60                # 1 minute bins
_MAX_BINS_PER_CH = 2000    # query cap per channel
_MAX_BINS_TOTAL = 40000    # query cap total
_CHANNELS = 199


@dataclass
class HistoryBin:
    bin_start_utc_s: int
    n_scans: int
    n_occupied: int
    n_free: int
    n_uncertain: int
    mean_power_dbm: Optional[float]
    withheld_reason: Optional[str]


@dataclass
class HistoryResponse:
    channels: list[int]
    from_utc_us: int
    to_utc_us: int
    resolution_s: int
    history_state: str         # "ok" | "insufficient_history" | "empty_start"
    history_start_utc_us: Optional[int]
    bins: dict[int, list[HistoryBin]]  # channel → bins
    latest_scan: Optional[dict]
    dropped_messages: int


class HistoryStore:
    """In-memory 744 h ring buffer; answers SSC-HIST-001 queries."""

    def __init__(self, ring_hours: int = _RING_HOURS, bin_s: int = _BIN_S) -> None:
        self._ring_hours = ring_hours
        self._bin_s = bin_s
        self._max_bins = (ring_hours * 3600) // bin_s
        # channel → deque of HistoryBin (oldest first)
        self._ring: dict[int, deque[HistoryBin]] = {
            ch: deque(maxlen=self._max_bins) for ch in range(1, _CHANNELS + 1)
        }
        self._latest_scan: Optional[dict] = None
        self._start_utc_us: Optional[int] = None
        self._dropped = 0
        self._seen_scan_ids: set[int] = set()

    def ingest(self, scan_records: dict) -> None:
        """Add one scan_records.v1 message."""
        scan_id = scan_records.get("scan_id", 0)
        if scan_id in self._seen_scan_ids:
            return  # idempotent
        self._seen_scan_ids.add(scan_id)
        # Evict old IDs to bound memory
        if len(self._seen_scan_ids) > 10000:
            self._seen_scan_ids = set(list(self._seen_scan_ids)[-5000:])

        utc_us = scan_records.get("scan_start_utc_us", 0)
        utc_s = utc_us // 1_000_000
        bin_start = (utc_s // self._bin_s) * self._bin_s

        if self._start_utc_us is None:
            self._start_utc_us = utc_us

        self._latest_scan = scan_records
        health = scan_records.get("health", {})
        flag_scan = health.get("records_flag_scan", False)

        for ch_rec in scan_records.get("channels", []):
            ch = ch_rec.get("channel")
            if ch is None or ch not in self._ring:
                continue
            ring = self._ring[ch]

            # Find or create bin for this scan's minute
            if ring and ring[-1].bin_start_utc_s == bin_start:
                b = ring[-1]
            else:
                b = HistoryBin(
                    bin_start_utc_s=bin_start,
                    n_scans=0, n_occupied=0, n_free=0, n_uncertain=0,
                    mean_power_dbm=None, withheld_reason=None,
                )
                ring.append(b)

            b.n_scans += 1
            occ = ch_rec.get("occupancy", "Uncertain")
            if not flag_scan:
                if occ == "Occupied":
                    b.n_occupied += 1
                elif occ == "Free":
                    b.n_free += 1
                else:
                    b.n_uncertain += 1

            power = ch_rec.get("power_dbm")
            if power is not None:
                prev = b.mean_power_dbm
                n = b.n_scans
                b.mean_power_dbm = power if prev is None else (prev * (n - 1) + power) / n
            elif b.withheld_reason is None:
                b.withheld_reason = ch_rec.get("withheld_reason")

    def query(
        self,
        channels: list[int],
        from_utc_us: int,
        to_utc_us: int,
        resolution_s: int = _BIN_S,
    ) -> HistoryResponse:
        from_s = from_utc_us // 1_000_000
        to_s = to_utc_us // 1_000_000
        state = "ok"
        if self._start_utc_us is not None and from_utc_us < self._start_utc_us:
            state = "insufficient_history"

        result_bins: dict[int, list[HistoryBin]] = {}
        total_bins = 0

        for ch in channels:
            if ch not in self._ring:
                result_bins[ch] = []
                continue
            bins = [
                b for b in self._ring[ch]
                if from_s <= b.bin_start_utc_s < to_s
            ]
            # Apply per-channel cap
            if len(bins) > _MAX_BINS_PER_CH:
                bins = bins[-_MAX_BINS_PER_CH:]
            # Apply total cap
            remaining = _MAX_BINS_TOTAL - total_bins
            if len(bins) > remaining:
                bins = bins[-remaining:]
            result_bins[ch] = bins
            total_bins += len(bins)
            if total_bins >= _MAX_BINS_TOTAL:
                break

        return HistoryResponse(
            channels=channels,
            from_utc_us=from_utc_us,
            to_utc_us=to_utc_us,
            resolution_s=resolution_s,
            history_state=state,
            history_start_utc_us=self._start_utc_us,
            bins=result_bins,
            latest_scan=self._latest_scan,
            dropped_messages=self._dropped,
        )

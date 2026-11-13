"""Mock HAL for fm_store_alert — scripted scan records, no sockets."""
from __future__ import annotations

import time
from typing import Optional

from fm_store_alert.config.logger import get_logger
from fm_store_alert.hal.port import StoreDataPort

log = get_logger(__name__)


def _make_scan(scan_id: int, channel_powers: Optional[dict] = None) -> dict:
    utc_us = int(time.time() * 1_000_000) + scan_id * 6_000_000
    channels = []
    for ch in range(1, 200):
        power = None if channel_powers is None else channel_powers.get(ch)
        channels.append({
            "channel": ch,
            "step": ((ch - 1) // 67) + 1,
            "frequency_hz": 87_600_000 + (ch - 1) * 100_000,
            "power_dbm": power,
            "uncertainty_db": 0.5,
            "occupancy": "Occupied" if power is not None and power > -100 else "Free",
            "verdict": "Authorised" if power is not None and power > -100 else "Clear",
            "withheld_reason": None,
            "dc_adjacent": False,
            "no_data": False,
            "clipped": False,
            "scan_flagged": False,
        })
    return {
        "schema_version": "1.0",
        "scan_id": scan_id,
        "scan_start_utc_us": utc_us,
        "scan_start_sync_state": "synced",
        "station_id": "COL-001",
        "config_sha256": "abc123",
        "calibration_state": "valid",
        "evidence_label": "FM screening — not a compliance determination",
        "health": {
            "scan_id": scan_id, "scan_late": False, "overflow_count": 0,
            "dropped_frame_count": 0, "clipped_captures": 0, "retune_failures": 0,
            "scan_duration_s": 5.9, "records_flag_scan": False,
        },
        "channels": channels,
    }


class MockStoreDataPort(StoreDataPort):
    """Scripted scan record source — plays through a list or a push queue."""

    def __init__(self, scans: Optional[list[dict]] = None, default_scans: int = 0) -> None:
        self._queue: list[dict] = []
        # If scans provided, use them as the sequence; if default_scans > 0, pre-populate
        if scans is not None:
            self._scans: list[dict] = list(scans)
        elif default_scans > 0:
            self._scans = [_make_scan(i) for i in range(1, default_scans + 1)]
        else:
            self._scans = []
        self._idx = 0
        self._calv_sequence = [
            {"state": "valid", "verified_until_utc_s": time.time() + 365 * 86400},
            {"state": "expiring", "verified_until_utc_s": time.time() + 3 * 86400},
            {"state": "expired", "verified_until_utc_s": time.time() - 86400},
        ]
        self._calv_idx = 0

    def push_scan(self, record: dict) -> None:
        """Push a record into the queue (used by VL-0 tests)."""
        self._queue.append(record)

    def next_scan_record(self, timeout_s: float = 10.0) -> dict:
        # Prefer the push queue
        if self._queue:
            return self._queue.pop(0)
        # Then the scripted sequence
        if self._idx < len(self._scans):
            scan = self._scans[self._idx]
            self._idx += 1
            return scan
        # Empty: either TimeoutError (consistent with real HAL) or StopIteration
        import time as _time
        # Short timeout means the caller wants a timeout error
        if timeout_s <= 1.0:
            _time.sleep(min(timeout_s, 0.05))
            raise TimeoutError("no scan record available")
        raise StopIteration("mock scan sequence exhausted")

    def next_calv(self, timeout_s: float = 10.0) -> dict:
        calv = self._calv_sequence[self._calv_idx % len(self._calv_sequence)]
        self._calv_idx += 1
        return dict(calv)

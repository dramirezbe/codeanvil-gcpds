"""VL-1 tests for SUB-002/history ring buffer."""
import time
import pytest
from fm_store_alert.output.history import HistoryStore


def _scan(scan_id: int, utc_s: int, channels_occ: dict) -> dict:
    channels = []
    for ch in range(1, 200):
        occ = "Occupied" if ch in channels_occ else "Free"
        power = channels_occ.get(ch)
        channels.append({
            "channel": ch,
            "occupancy": occ,
            "power_dbm": power,
            "withheld_reason": None,
        })
    return {
        "scan_id": scan_id,
        "scan_start_utc_us": utc_s * 1_000_000,
        "health": {"records_flag_scan": False},
        "channels": channels,
    }


@pytest.mark.vl1
def test_ingest_and_query_basic():
    store = HistoryStore()
    store.ingest(_scan(1, 0, {100: -60.0}))
    resp = store.query([100], from_utc_us=0, to_utc_us=120 * 1_000_000)
    assert resp.history_state == "ok"
    bins = resp.bins[100]
    assert len(bins) >= 1
    assert bins[0].n_occupied == 1


@pytest.mark.vl1
def test_idempotent_scan_id():
    store = HistoryStore()
    store.ingest(_scan(1, 0, {100: -60.0}))
    store.ingest(_scan(1, 0, {100: -60.0}))  # duplicate
    resp = store.query([100], from_utc_us=0, to_utc_us=120 * 1_000_000)
    assert resp.bins[100][0].n_scans == 1  # counted once


@pytest.mark.vl1
def test_flagged_scan_not_counted():
    scan = _scan(2, 0, {100: -60.0})
    scan["health"]["records_flag_scan"] = True
    store = HistoryStore()
    store.ingest(scan)
    resp = store.query([100], from_utc_us=0, to_utc_us=120 * 1_000_000)
    b = resp.bins[100][0]
    assert b.n_occupied == 0   # not counted when flagged


@pytest.mark.vl1
def test_insufficient_history():
    store = HistoryStore()
    store.ingest(_scan(1, 3600, {100: -60.0}))  # starts at 3600 s
    # Query from before the start
    resp = store.query([100], from_utc_us=0, to_utc_us=7200 * 1_000_000)
    assert resp.history_state == "insufficient_history"


@pytest.mark.vl1
def test_per_channel_bin_cap():
    store = HistoryStore()
    # Ingest 2001 bins (one scan per minute in different minutes)
    for i in range(2001):
        store.ingest(_scan(i, i * 60, {100: -60.0}))
    resp = store.query([100], from_utc_us=0, to_utc_us=2001 * 60 * 1_000_000)
    assert len(resp.bins[100]) <= 2000


@pytest.mark.vl1
def test_withheld_bin_null_power():
    scan = _scan(5, 0, {})
    scan["channels"][99]["power_dbm"] = None
    scan["channels"][99]["withheld_reason"] = "clipped"
    store = HistoryStore()
    store.ingest(scan)
    resp = store.query([100], from_utc_us=0, to_utc_us=120 * 1_000_000)
    b = resp.bins[100][0]
    assert b.mean_power_dbm is None
    assert b.withheld_reason == "clipped"

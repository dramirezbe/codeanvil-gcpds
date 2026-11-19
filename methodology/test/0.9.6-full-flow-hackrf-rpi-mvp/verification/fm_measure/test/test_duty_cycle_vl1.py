"""VL-1 tests for SUB-001/duty_cycle."""
import pytest
from fm_measure.decision.duty_cycle import DutyCycleAccumulator
from fm_measure.decision.detector import OccupancyResult


def _occ(ch: int, state: str) -> OccupancyResult:
    return OccupancyResult(channel=ch, state=state, uncertain_reason=None)


@pytest.mark.vl1
def test_no_records_before_interval_closes():
    acc = DutyCycleAccumulator(interval_s=3600)
    result = acc.add([_occ(100, "Occupied")], scan_utc_s=0.0)
    assert result is None


@pytest.mark.vl1
def test_records_emitted_on_interval_boundary():
    acc = DutyCycleAccumulator(interval_s=3600)
    # Add scans in first interval (0 s)
    for _ in range(10):
        acc.add([_occ(100, "Occupied")], scan_utc_s=1800.0)
    # Scan in second interval → triggers close of first
    records = acc.add([_occ(100, "Free")], scan_utc_s=3601.0)
    assert records is not None
    rec_100 = next(r for r in records if r.channel == 100)
    assert rec_100.occupied_count == 10
    assert rec_100.free_count == 0
    assert rec_100.duty_cycle_pct == 100.0


@pytest.mark.vl1
def test_duty_cycle_pct_mixed():
    acc = DutyCycleAccumulator(interval_s=3600)
    for _ in range(6):
        acc.add([_occ(100, "Occupied")], scan_utc_s=100.0)
    for _ in range(4):
        acc.add([_occ(100, "Free")], scan_utc_s=100.0)
    records = acc.add([_occ(100, "Free")], scan_utc_s=3700.0)
    assert records is not None
    rec = next(r for r in records if r.channel == 100)
    assert abs(rec.duty_cycle_pct - 60.0) < 0.1


@pytest.mark.vl1
def test_null_denominator():
    """If no scans were added for a channel, denominator is 0 → None."""
    acc = DutyCycleAccumulator(interval_s=3600)
    # Channel 101 never added, only channel 100
    acc.add([_occ(100, "Occupied")], scan_utc_s=1800.0)
    records = acc.add([_occ(100, "Free")], scan_utc_s=3700.0)
    # Only channel 100 in records; no channel 101
    assert records is not None
    channels = {r.channel for r in records}
    assert 101 not in channels


@pytest.mark.vl1
def test_flush_returns_current_interval():
    acc = DutyCycleAccumulator(interval_s=3600)
    acc.add([_occ(100, "Occupied")], scan_utc_s=100.0)
    records = acc.flush()
    assert records is not None
    assert len(records) == 1

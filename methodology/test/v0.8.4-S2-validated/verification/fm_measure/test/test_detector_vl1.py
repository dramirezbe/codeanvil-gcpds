"""VL-1 tests for SUB-001/detector and comparator."""
import pytest
from fm_measure.decision.detector import ChannelDetector, OccupancyResult
from fm_measure.decision.comparator import compare, StationEntry, AssignmentResult
from fm_measure.dsp.calibration import CalibratedChannel


def _make_cal(ch: int, power: float | None, withheld: str | None = None) -> CalibratedChannel:
    return CalibratedChannel(
        channel=ch, step=1, power_dbm=power, uncertainty_db=0.5,
        withheld_reason=withheld, dc_adjacent=False, no_data=withheld == "no_data",
        clipped=withheld == "clipped", scan_flagged=withheld == "scan_flagged",
        mapping_error_bound_khz=0.0, mapping_limit_exceeded=False,
        frequency_correction_ppm=0.0,
    )


@pytest.mark.vl1
def test_occupied_above_threshold():
    det = ChannelDetector(threshold_dbm=-100.0)
    # Channel 100 occupied, 101 and 99 much lower (adj ratio ok)
    channels = [
        _make_cal(99, -120.0),
        _make_cal(100, -60.0),
        _make_cal(101, -120.0),
    ]
    results = det.classify(channels)
    occ = {r.channel: r.state for r in results}
    assert occ[100] == "Occupied"


@pytest.mark.vl1
def test_free_below_threshold():
    det = ChannelDetector(threshold_dbm=-100.0)
    channels = [_make_cal(100, -120.0)]
    results = det.classify(channels)
    assert results[0].state == "Free"


@pytest.mark.vl1
def test_withheld_becomes_uncertain():
    det = ChannelDetector()
    channels = [_make_cal(50, None, withheld="clipped")]
    results = det.classify(channels)
    assert results[0].state == "Uncertain"
    assert results[0].uncertain_reason == "clipped"


@pytest.mark.vl1
def test_hysteresis_one_scan_delay():
    det = ChannelDetector(threshold_dbm=-100.0)
    # Scan 1: occupied
    channels = [_make_cal(99, -120.0), _make_cal(100, -60.0), _make_cal(101, -120.0)]
    det.classify(channels)
    # Scan 2: power drops below threshold → should be Uncertain (hysteresis), not Free
    channels2 = [_make_cal(99, -120.0), _make_cal(100, -120.0), _make_cal(101, -120.0)]
    results2 = det.classify(channels2)
    state_map = {r.channel: r.state for r in results2}
    assert state_map[100] == "Uncertain"
    # Scan 3: still below threshold → now Free
    results3 = det.classify(channels2)
    state_map3 = {r.channel: r.state for r in results3}
    assert state_map3[100] == "Free"


@pytest.mark.vl1
def test_adj_ratio_uncertain_when_missing():
    """Channel above threshold but adjacent also high → Uncertain (adj_ratio)."""
    det = ChannelDetector(threshold_dbm=-100.0)
    # Both channel and adjacent are above threshold and within 10 dB of each other
    channels = [
        _make_cal(100, -60.0),
        _make_cal(101, -63.0),  # only 3 dB below — adj ratio not met
    ]
    results = det.classify(channels)
    state_map = {r.channel: r.state for r in results}
    assert state_map[100] == "Uncertain"


# --- Comparator tests ---

@pytest.mark.vl1
def test_authorised():
    occ = [OccupancyResult(channel=100, state="Occupied", uncertain_reason=None)]
    ref = [StationEntry(channel=100, callsign="TEST-FM")]
    asg = compare(occ, ref)
    assert asg[0].verdict == "Authorised"


@pytest.mark.vl1
def test_unexpected():
    occ = [OccupancyResult(channel=100, state="Occupied", uncertain_reason=None)]
    asg = compare(occ, [])  # empty reference
    assert asg[0].verdict == "Unexpected"


@pytest.mark.vl1
def test_silent():
    occ = [OccupancyResult(channel=100, state="Free", uncertain_reason=None)]
    ref = [StationEntry(channel=100, callsign="TEST-FM")]
    asg = compare(occ, ref)
    assert asg[0].verdict == "Silent"


@pytest.mark.vl1
def test_clear():
    occ = [OccupancyResult(channel=100, state="Free", uncertain_reason=None)]
    asg = compare(occ, [])
    assert asg[0].verdict == "Clear"


@pytest.mark.vl1
def test_uncertain_always_indeterminate():
    occ = [OccupancyResult(channel=100, state="Uncertain", uncertain_reason="clipped")]
    ref = [StationEntry(channel=100, callsign="TEST-FM")]
    asg = compare(occ, ref)
    assert asg[0].verdict == "Indeterminate"


@pytest.mark.vl1
def test_absent_reference_all_indeterminate():
    occ = [
        OccupancyResult(channel=100, state="Occupied", uncertain_reason=None),
        OccupancyResult(channel=101, state="Free", uncertain_reason=None),
    ]
    asg = compare(occ, None)
    assert all(a.verdict == "Indeterminate" for a in asg)

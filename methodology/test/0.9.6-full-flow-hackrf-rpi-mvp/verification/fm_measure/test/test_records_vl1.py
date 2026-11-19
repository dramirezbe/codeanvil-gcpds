"""VL-1 tests for SUB-001/records assembler."""
import pytest
from fm_measure.output.records import assemble, _EVIDENCE_LABEL, _PROHIBITED_WORDS
from fm_measure.dsp.calibration import CalibratedChannel, CalibratedPowerScan
from fm_measure.decision.detector import OccupancyResult
from fm_measure.decision.comparator import AssignmentResult, StationEntry


def _make_cal_scan(n_channels: int = 3) -> CalibratedPowerScan:
    channels = [
        CalibratedChannel(
            channel=i, step=1, power_dbm=-80.0, uncertainty_db=0.5,
            withheld_reason=None, dc_adjacent=False, no_data=False,
            clipped=False, scan_flagged=False,
            mapping_error_bound_khz=0.0, mapping_limit_exceeded=False,
            frequency_correction_ppm=0.0,
        )
        for i in range(1, n_channels + 1)
    ]
    return CalibratedPowerScan(
        scan_id=1, scan_start_utc_us=1_000_000_000, scan_start_sync_state="synced",
        gains={}, calibrated=True, calibration_valid=True, config_sha256_match=True,
        frequency_correction_ppm=0.0, channels=channels,
    )


def _make_occ(n: int = 3) -> list[OccupancyResult]:
    return [OccupancyResult(channel=i, state="Occupied", uncertain_reason=None)
            for i in range(1, n + 1)]


def _make_asg(n: int = 3) -> list[AssignmentResult]:
    return [AssignmentResult(channel=i, occupancy="Occupied", verdict="Authorised",
                              station=StationEntry(channel=i, callsign=f"TEST-{i:03d}"))
            for i in range(1, n + 1)]


def _health() -> dict:
    return dict(scan_late=False, overflow_count=0, dropped_frame_count=0,
                clipped_captures=0, retune_failures=0, scan_duration_s=5.9,
                records_flag_scan=False)


@pytest.mark.vl1
def test_assemble_produces_correct_channel_count():
    rec = assemble(_make_cal_scan(199), _make_occ(199), _make_asg(199),
                   _health(), "COL-001", "abc", "valid")
    assert len(rec.channels) == 199


@pytest.mark.vl1
def test_evidence_label_present():
    rec = assemble(_make_cal_scan(3), _make_occ(3), _make_asg(3),
                   _health(), "COL-001", "abc", "valid")
    assert rec.evidence_label == _EVIDENCE_LABEL


@pytest.mark.vl1
def test_prohibited_word_in_label_raises():
    from fm_measure.output.records import _check_prohibited
    for word in ["compliant", "certified", "illegal"]:
        with pytest.raises(ValueError, match="prohibited"):
            _check_prohibited(word)


@pytest.mark.vl1
def test_health_record_propagated():
    h = dict(scan_late=True, overflow_count=3, dropped_frame_count=1,
             clipped_captures=1, retune_failures=0, scan_duration_s=7.4,
             records_flag_scan=True)
    rec = assemble(_make_cal_scan(3), _make_occ(3), _make_asg(3),
                   h, "COL-001", "abc", "valid")
    assert rec.health.scan_late is True
    assert rec.health.overflow_count == 3


@pytest.mark.vl1
def test_withheld_channel_in_record():
    cal = _make_cal_scan(3)
    cal.channels[1].power_dbm = None
    cal.channels[1].withheld_reason = "clipped"
    rec = assemble(cal, _make_occ(3), _make_asg(3), _health(), "COL-001", "abc", "valid")
    ch2 = next(c for c in rec.channels if c.channel == 2)
    assert ch2.power_dbm is None
    assert ch2.withheld_reason == "clipped"

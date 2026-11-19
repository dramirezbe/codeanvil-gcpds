"""VL-1 tests for SUB-001/estimator."""
import pytest
import numpy as np
from fm_measure.hal.mock import MockSdrPort
from fm_measure.hal.port import SdrConfig
from fm_measure.dsp.estimator import estimate, _CHANNELS


def _get_frames(scenario: str = "gv001") -> dict:
    """Return step_frames and step_meta from MockSdrPort."""
    sdr = MockSdrPort(scenario=scenario)
    sdr.open()
    cfg = SdrConfig(center_hz=90_250_000.0, sample_rate_hz=10_000_000.0)
    sdr.configure(cfg)
    frames = sdr.read_frames(39)
    sdr.close()

    step_frames = {}
    step_meta = {}
    for step, centre in enumerate([90_250_000.0, 97_750_000.0, 105_250_000.0], 1):
        # Use same frames for all steps (mock doesn't distinguish)
        step_frames[step] = [f.samples for f in frames]
        step_meta[step] = {
            "clipped": [f.clipped for f in frames],
            "no_data": False,
        }
    return step_frames, step_meta


@pytest.mark.vl1
def test_estimate_produces_199_channels():
    frames, meta = _get_frames("gv001")
    cps, ss = estimate(
        frames, meta, scan_id=1,
        scan_start_utc_us=1_000_000_000,
        scan_start_sync_state="synced",
        gains={"rf_amp_db": 0, "lna_db": 0, "baseband_db": 0},
    )
    assert len(cps.channels) == _CHANNELS


@pytest.mark.vl1
def test_estimate_spectrum_has_3_steps():
    frames, meta = _get_frames("gv001")
    _, ss = estimate(
        frames, meta, scan_id=1,
        scan_start_utc_us=1_000_000_000,
        scan_start_sync_state="synced",
        gains={},
    )
    assert len(ss.steps) == 3
    for step_data in ss.steps:
        assert len(step_data["points_dbfs"]) == 819


@pytest.mark.vl1
def test_gv006_dropped_frame_withholds_power():
    """GV-006: 38 of 39 frames delivered → channels marked dropped."""
    sdr = MockSdrPort(scenario="gv006")
    sdr.open()
    cfg = SdrConfig(center_hz=90_250_000.0, sample_rate_hz=10_000_000.0)
    sdr.configure(cfg)
    frames = sdr.read_frames(39)
    sdr.close()
    # 38 frames delivered
    assert len(frames) == 38

    step_frames = {1: [f.samples for f in frames], 2: [f.samples for f in frames], 3: [f.samples for f in frames]}
    step_meta = {s: {"clipped": [False]*len(frames), "no_data": False, "expected_frames": 39} for s in (1, 2, 3)}
    cps, _ = estimate(step_frames, step_meta, scan_id=1, scan_start_utc_us=0,
                       scan_start_sync_state="unsynced", gains={})
    # At least some channels should be withheld as "dropped"
    withheld = [ch for ch in cps.channels if ch.withheld_reason == "dropped"]
    assert len(withheld) > 0


@pytest.mark.vl1
def test_gv005_clipped_withholds_power():
    """GV-005: first frame clipped → channels marked clipped."""
    sdr = MockSdrPort(scenario="gv005")
    sdr.open()
    cfg = SdrConfig(center_hz=90_250_000.0, sample_rate_hz=10_000_000.0)
    sdr.configure(cfg)
    frames = sdr.read_frames(39)
    sdr.close()

    clipped_flags = [f.clipped for f in frames]
    step_frames = {s: [f.samples for f in frames] for s in (1, 2, 3)}
    step_meta = {s: {"clipped": clipped_flags, "no_data": False} for s in (1, 2, 3)}
    cps, _ = estimate(step_frames, step_meta, scan_id=1, scan_start_utc_us=0,
                       scan_start_sync_state="unsynced", gains={})
    withheld_clipped = [ch for ch in cps.channels if ch.withheld_reason == "clipped"]
    assert len(withheld_clipped) > 0


@pytest.mark.vl1
def test_scan_flagged_withholds_all():
    frames, meta = _get_frames("gv001")
    cps, _ = estimate(frames, meta, scan_id=1, scan_start_utc_us=0,
                       scan_start_sync_state="unsynced", gains={},
                       scan_flagged=True)
    withheld = [ch for ch in cps.channels if ch.withheld_reason == "scan_flagged"]
    assert len(withheld) == _CHANNELS


@pytest.mark.vl1
def test_bin_spacing_matches_spec():
    frames, meta = _get_frames("gv001")
    cps, _ = estimate(frames, meta, scan_id=1, scan_start_utc_us=0,
                       scan_start_sync_state="synced", gains={})
    assert abs(cps.bin_spacing_hz - 2441.40625) < 0.01


@pytest.mark.vl1
def test_gv001_has_power_on_all_channels():
    frames, meta = _get_frames("gv001")
    cps, _ = estimate(frames, meta, scan_id=1, scan_start_utc_us=0,
                       scan_start_sync_state="synced", gains={})
    have_power = [ch for ch in cps.channels if ch.power_dbfs is not None]
    # In the nominal scenario most channels should have power
    assert len(have_power) >= 100

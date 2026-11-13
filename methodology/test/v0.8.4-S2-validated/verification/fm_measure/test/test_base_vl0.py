"""VL-0 base top-down tests for fm_measure."""
import pytest
from fm_measure.hal.mock import MockSdrPort
from fm_measure.hal.port import SdrConfig, SdrUnavailable


@pytest.mark.vl0
def test_mock_sdr_open_close():
    sdr = MockSdrPort()
    sdr.open()
    info = sdr.info()
    assert info["configured"] is False
    sdr.close()


@pytest.mark.vl0
def test_mock_sdr_configure_accepts_valid():
    sdr = MockSdrPort()
    sdr.open()
    cfg = SdrConfig(
        center_hz=90_250_000.0,
        sample_rate_hz=10_000_000.0,
        lna_gain_db=0,
        rf_gain_db=0,
        bb_gain_db=0,
        agc=False,
    )
    sdr.configure(cfg)
    assert sdr.info()["configured"] is True
    sdr.close()


@pytest.mark.vl0
def test_mock_sdr_rejects_agc():
    sdr = MockSdrPort()
    sdr.open()
    cfg = SdrConfig(center_hz=90_250_000.0, agc=True)
    with pytest.raises(ValueError, match="AGC"):
        sdr.configure(cfg)
    sdr.close()


@pytest.mark.vl0
def test_mock_sdr_rejects_out_of_range_sample_rate():
    sdr = MockSdrPort()
    sdr.open()
    cfg = SdrConfig(center_hz=90_250_000.0, sample_rate_hz=25_000_000.0)
    with pytest.raises(ValueError, match="sample_rate_hz"):
        sdr.configure(cfg)
    sdr.close()


@pytest.mark.vl0
def test_mock_sdr_read_frames_gv001():
    sdr = MockSdrPort(scenario="gv001")
    sdr.open()
    cfg = SdrConfig(center_hz=90_250_000.0, sample_rate_hz=10_000_000.0)
    sdr.configure(cfg)
    frames = sdr.read_frames(39)
    assert len(frames) == 39
    for f in frames:
        assert len(f.samples) == 131_072  # 65536 complex int8 pairs
    sdr.close()


@pytest.mark.vl0
def test_mock_sdr_gv005_first_frame_clipped():
    sdr = MockSdrPort(scenario="gv005")
    sdr.open()
    cfg = SdrConfig(center_hz=90_250_000.0, sample_rate_hz=10_000_000.0)
    sdr.configure(cfg)
    frames = sdr.read_frames(39)
    assert frames[0].clipped is True
    assert all(not f.clipped for f in frames[1:])
    sdr.close()


@pytest.mark.vl0
def test_mock_sdr_gv006_dropped_frame():
    sdr = MockSdrPort(scenario="gv006")
    sdr.open()
    cfg = SdrConfig(center_hz=90_250_000.0, sample_rate_hz=10_000_000.0)
    sdr.configure(cfg)
    frames = sdr.read_frames(39)
    assert len(frames) == 38  # one dropped
    sdr.close()


@pytest.mark.vl0
def test_mock_sdr_read_without_open_raises():
    sdr = MockSdrPort()
    cfg = SdrConfig(center_hz=90_250_000.0)
    sdr.configure = lambda c: None  # bypass validation
    with pytest.raises(SdrUnavailable):
        sdr.read_frames(1)


@pytest.mark.vl0
def test_mock_sdr_records_configure_calls():
    sdr = MockSdrPort()
    sdr.open()
    cfg = SdrConfig(center_hz=90_250_000.0)
    sdr.configure(cfg)
    assert len(sdr._calls) == 1
    assert sdr._calls[0].center_hz == 90_250_000.0
    sdr.close()

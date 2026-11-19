"""VL-0 floor tests for SUB-001 fm_measure."""
import pytest


@pytest.mark.vl0
def test_mock_sdr_port_opens_and_configures():
    """Mock SdrPort opens, configures with valid settings, and closes."""
    from fm_measure.hal.mock import MockSdrPort
    from fm_measure.hal.port import SdrConfig

    hal = MockSdrPort(scenario="gv001")
    hal.open()
    hal.configure(SdrConfig(
        center_hz=98_000_000.0,
        sample_rate_hz=10_000_000.0,
        lna_gain_db=16,
        rf_gain_db=0,
        bb_gain_db=20,
    ))
    info = hal.info()
    assert info["configured"] is True
    hal.close()


@pytest.mark.vl0
def test_mock_sdr_port_reads_39_frames_gv001():
    """GV-001: read_frames returns exactly 39 frames of 131072 int8 bytes each."""
    from fm_measure.hal.mock import MockSdrPort
    from fm_measure.hal.port import SdrConfig

    hal = MockSdrPort(scenario="gv001")
    hal.open()
    hal.configure(SdrConfig(center_hz=98_000_000.0, sample_rate_hz=10_000_000.0,
                            lna_gain_db=16, rf_gain_db=0, bb_gain_db=20))
    frames = hal.read_frames(39, timeout_s=5.0)
    assert len(frames) == 39
    for f in frames:
        assert len(f.samples) == 131_072
        assert not f.clipped
        assert not f.overflow
    hal.close()


@pytest.mark.vl0
def test_mock_sdr_port_gv005_clips_first_frame():
    """GV-005: first frame is clipped."""
    from fm_measure.hal.mock import MockSdrPort
    from fm_measure.hal.port import SdrConfig

    hal = MockSdrPort(scenario="gv005")
    hal.open()
    hal.configure(SdrConfig(center_hz=98_000_000.0, sample_rate_hz=10_000_000.0,
                            lna_gain_db=16, rf_gain_db=0, bb_gain_db=20))
    frames = hal.read_frames(39, timeout_s=5.0)
    assert frames[0].clipped is True
    hal.close()


@pytest.mark.vl0
def test_mock_sdr_port_gv006_drops_one_frame():
    """GV-006: 38 of 39 frames delivered."""
    from fm_measure.hal.mock import MockSdrPort
    from fm_measure.hal.port import SdrConfig

    hal = MockSdrPort(scenario="gv006")
    hal.open()
    hal.configure(SdrConfig(center_hz=98_000_000.0, sample_rate_hz=10_000_000.0,
                            lna_gain_db=16, rf_gain_db=0, bb_gain_db=20))
    frames = hal.read_frames(39, timeout_s=5.0)
    assert len(frames) == 38
    hal.close()


@pytest.mark.vl0
def test_mock_sdr_port_rejects_invalid_config():
    """Mock HAL validates config — out-of-range raises ValueError."""
    from fm_measure.hal.mock import MockSdrPort
    from fm_measure.hal.port import SdrConfig

    hal = MockSdrPort()
    hal.open()
    with pytest.raises(ValueError):
        hal.configure(SdrConfig(center_hz=100.0))  # below 1 MHz


@pytest.mark.vl0
def test_framing_roundtrip():
    """Shared framing: encode and decode a JSON message over a socketpair."""
    import socket
    from fm_measure.lib.framing import send_msg, recv_msg

    a, b = socket.socketpair()
    try:
        payload = {"key": "value", "num": 42}
        send_msg(a, payload)
        result = recv_msg(b)
        assert result == payload
    finally:
        a.close()
        b.close()

"""VL-0 floor tests for SUB-005 fm_time."""
import pytest


@pytest.mark.vl0
def test_mock_ntp_port_returns_sequence():
    """MockNtpPort returns scripted offset sequence."""
    from fm_time.hal.mock import MockNtpPort

    port = MockNtpPort()
    s1 = port.query("mock")
    assert s1.offset_ms == 12.0
    assert s1.source_id == "mock-ntp"

    s2 = port.query("mock")
    assert s2.offset_ms == 49.0

    s3 = port.query("mock")
    assert s3.offset_ms == 60.0  # > 50 ms threshold → unsynced


@pytest.mark.vl0
def test_mock_ntp_port_returns_unreachable():
    """MockNtpPort returns None offset for unreachable entry."""
    from fm_time.hal.mock import MockNtpPort

    port = MockNtpPort()
    # Advance to index 4 (unreachable)
    for _ in range(4):
        port.query("mock")
    s = port.query("mock")
    assert s.offset_ms is None


@pytest.mark.vl0
def test_framing_roundtrip():
    """Framing roundtrip for fm_time."""
    import socket
    from fm_time.lib.framing import send_msg, recv_msg

    a, b = socket.socketpair()
    try:
        send_msg(a, {"time": "2026-01-01T00:00:00Z"})
        assert recv_msg(b)["time"] == "2026-01-01T00:00:00Z"
    finally:
        a.close()
        b.close()

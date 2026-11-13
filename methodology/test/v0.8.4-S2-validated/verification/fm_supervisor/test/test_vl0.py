"""VL-0 floor tests for SUB-006 fm_supervisor."""
import pytest


@pytest.mark.vl0
def test_mock_watchdog_port_opens_and_feeds():
    """MockWatchdogPort opens, records feed timestamps, closes cleanly."""
    from fm_supervisor.hal.mock import MockWatchdogPort

    wd = MockWatchdogPort()
    wd.open()
    wd.feed()
    wd.feed()
    assert len(wd.feed_times) == 2
    assert not wd.reset_triggered
    wd.close()


@pytest.mark.vl0
def test_mock_thermal_port_sequence():
    """ThermalPort returns [25, 69, 71, 64, 85] °C then repeats."""
    from fm_supervisor.hal.mock import MockThermalPort

    tp = MockThermalPort()
    readings = [tp.read_celsius() for _ in range(10)]
    expected = [25.0, 69.0, 71.0, 64.0, 85.0, 25.0, 69.0, 71.0, 64.0, 85.0]
    assert readings == expected


@pytest.mark.vl0
def test_mock_resource_port_returns_values():
    """MockResourcePort returns non-negative cpu and rss values."""
    from fm_supervisor.hal.mock import MockResourcePort

    rp = MockResourcePort()
    assert rp.cpu_percent() >= 0.0
    assert rp.rss_mb() >= 0.0


@pytest.mark.vl0
def test_framing_roundtrip():
    """Framing roundtrip for fm_supervisor."""
    import socket
    from fm_supervisor.lib.framing import send_msg, recv_msg

    a, b = socket.socketpair()
    try:
        send_msg(a, {"status": "ok"})
        assert recv_msg(b) == {"status": "ok"}
    finally:
        a.close()
        b.close()

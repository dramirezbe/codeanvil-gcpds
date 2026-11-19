"""VL-0 floor tests for SUB-003 fm_report."""
import pytest


@pytest.mark.vl0
def test_mock_store_port_opens_run_and_appends():
    """MockReportStorePort creates run directory and appends CSV lines."""
    from fm_report.hal.mock import MockReportStorePort

    port = MockReportStorePort()
    try:
        run_dir = port.open_run("run_001")
        assert run_dir.exists()
        port.append_scan("run_001", ["col1,col2,col3", "1,2,3", "4,5,6"])
        seg = run_dir / "current_segment.csv"
        assert seg.exists()
        content = seg.read_text()
        assert "col1,col2,col3" in content
        assert "1,2,3" in content
    finally:
        port.cleanup()


@pytest.mark.vl0
def test_mock_store_free_space_positive():
    """free_space returns a positive integer."""
    from fm_report.hal.mock import MockReportStorePort

    port = MockReportStorePort()
    try:
        assert port.free_space() > 0
    finally:
        port.cleanup()


@pytest.mark.vl0
def test_framing_roundtrip():
    """Framing roundtrip works for fm_report."""
    import socket
    from fm_report.lib.framing import send_msg, recv_msg

    a, b = socket.socketpair()
    try:
        send_msg(a, {"scan": 1})
        assert recv_msg(b) == {"scan": 1}
    finally:
        a.close()
        b.close()

"""VL-0 floor tests for SUB-002 fm_store_alert."""
import pytest


@pytest.mark.vl0
def test_mock_data_port_queues_scan_record():
    """MockStoreDataPort delivers pushed records via next_scan_record."""
    from fm_store_alert.hal.mock import MockStoreDataPort

    port = MockStoreDataPort()
    record = {"schema": "scan_records.v1", "scan_index": 0}
    port.push_scan(record)
    result = port.next_scan_record(timeout_s=1.0)
    assert result == record


@pytest.mark.vl0
def test_mock_data_port_timeout_raises():
    """next_scan_record raises TimeoutError when queue is empty."""
    from fm_store_alert.hal.mock import MockStoreDataPort

    port = MockStoreDataPort()
    with pytest.raises(TimeoutError):
        port.next_scan_record(timeout_s=0.05)


@pytest.mark.vl0
def test_framing_roundtrip():
    """Framing module encodes and decodes consistently."""
    import socket
    from fm_store_alert.lib.framing import send_msg, recv_msg

    a, b = socket.socketpair()
    try:
        send_msg(a, {"test": True})
        assert recv_msg(b) == {"test": True}
    finally:
        a.close()
        b.close()

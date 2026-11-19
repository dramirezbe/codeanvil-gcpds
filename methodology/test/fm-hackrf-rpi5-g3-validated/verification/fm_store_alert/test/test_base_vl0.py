"""VL-0 base top-down tests for fm_store_alert."""
import pytest
from fm_store_alert.lib.framing import send_msg, recv_msg


@pytest.mark.vl0
def test_framing_roundtrip():
    import socket
    a, b = socket.socketpair()
    obj = {"scan_id": 42, "value": 3.14}
    send_msg(a, obj)
    result = recv_msg(b)
    assert result == obj
    a.close(); b.close()


@pytest.mark.vl0
def test_framing_large_message():
    import socket
    a, b = socket.socketpair()
    obj = {"data": "x" * 100_000}
    send_msg(a, obj)
    result = recv_msg(b)
    assert result["data"] == "x" * 100_000
    a.close(); b.close()

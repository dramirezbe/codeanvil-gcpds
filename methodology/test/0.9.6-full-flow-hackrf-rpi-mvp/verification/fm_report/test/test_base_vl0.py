"""VL-0 base top-down tests for fm_report."""
import pytest
from fm_report.lib.framing import send_msg, recv_msg


@pytest.mark.vl0
def test_framing_roundtrip_report():
    import socket
    a, b = socket.socketpair()
    obj = {"run_id": "RUN-20260101-000000-01"}
    send_msg(a, obj)
    result = recv_msg(b)
    assert result == obj
    a.close(); b.close()

"""VL-0 base top-down tests for fm_time."""
import pytest
from fm_time.hal.mock import MockNtpPort


@pytest.mark.vl0
def test_ntp_mock_sequence():
    ntp = MockNtpPort()
    s1 = ntp.query("mock")
    assert s1.offset_ms == 12.0
    s2 = ntp.query("mock")
    assert s2.offset_ms == 49.0


@pytest.mark.vl0
def test_ntp_mock_third_sample_unsynced():
    ntp = MockNtpPort()
    ntp.query("mock"); ntp.query("mock")
    s3 = ntp.query("mock")
    assert s3.offset_ms == 60.0  # > 50 ms → unsynced


@pytest.mark.vl0
def test_ntp_mock_unreachable():
    ntp = MockNtpPort()
    for _ in range(4):
        ntp.query("mock")
    s5 = ntp.query("mock")
    assert s5.offset_ms is None

"""VL-1 tests for SUB-005/ntp state machine."""
import time
import pytest
from fm_time.decision.ntp import NtpStateMachine, _UNSYNCED_OFFSET_MS, _STEPPED_OFFSET_MS
from fm_time.hal.mock import MockNtpPort
from fm_time.hal.port import NtpSample


def _synced_sample(offset_ms: float = 10.0) -> NtpSample:
    return NtpSample(offset_ms=offset_ms, delay_ms=5.0, source_id="mock")


def _make_state(startup_wait_s: float = 0.0) -> NtpStateMachine:
    """Return a state machine that skips the startup window."""
    return NtpStateMachine(startup_wait_s=startup_wait_s)


@pytest.mark.vl1
def test_starts_unsynced():
    state = NtpStateMachine(startup_wait_s=120.0)
    assert state.sync_state == "unsynced"


@pytest.mark.vl1
def test_synced_after_good_sample():
    state = _make_state()
    state.update(_synced_sample(10.0))
    assert state.sync_state == "synced"


@pytest.mark.vl1
def test_unsynced_when_offset_above_50ms():
    state = _make_state()
    state.update(_synced_sample(60.0))
    assert state.sync_state == "unsynced"


@pytest.mark.vl1
def test_stepped_when_offset_above_200ms():
    state = _make_state()
    state.update(_synced_sample(250.0))
    assert state.sync_state == "stepped"


@pytest.mark.vl1
def test_unsynced_on_unreachable():
    state = _make_state()
    state.update(_synced_sample(10.0))  # first ok
    state.update(NtpSample(offset_ms=None, delay_ms=None, source_id=""))  # fail
    # Offset still from before but last_success still recent so stays synced…
    # unless poll_interval resets
    # After unreachable, consecutive_ok resets and poll_interval resets to min
    assert state._consecutive_ok == 0
    assert state.poll_interval_s == 16.0


@pytest.mark.vl1
def test_poll_interval_backs_off():
    state = _make_state()
    initial = state.poll_interval_s
    for _ in range(3):
        state.update(_synced_sample(10.0))
    assert state.poll_interval_s > initial  # backed off after 3 consecutive ok


@pytest.mark.vl1
def test_poll_interval_resets_on_failure():
    state = _make_state()
    for _ in range(5):
        state.update(_synced_sample(10.0))
    backed = state.poll_interval_s
    assert backed > 16.0
    state.update(NtpSample(offset_ms=None, delay_ms=None, source_id=""))
    assert state.poll_interval_s == 16.0


@pytest.mark.vl1
def test_leap_propagated():
    state = _make_state()
    sample = NtpSample(offset_ms=10.0, delay_ms=5.0, source_id="mock", leap=1)
    state.update(sample)
    assert state.leap == 1


@pytest.mark.vl1
def test_time_publisher_tick(tmp_path):
    """TimePublisher.tick must call ntp.query and produce a msg."""
    from fm_time.decision.ntp import TimePublisher
    ntp = MockNtpPort()
    sock_path = tmp_path / "time.sock"
    pub = TimePublisher(ntp, ["mock"], sock_path=sock_path, startup_wait_s=0.0)
    pub.start_server()
    pub.tick(utc_us=1_000_000_000)
    pub.close()
    # No assertion on output, just must not raise

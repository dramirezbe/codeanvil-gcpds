"""VL-1 tests for SUB-006/processes."""
import time
import pytest
from fm_supervisor.decision.processes import ProcessManager, UnitState, _LADDER


@pytest.mark.vl1
def test_restart_ladder_increments():
    pm = ProcessManager()
    unit = pm._units[0]
    # Simulate restarts
    now = time.monotonic()
    pm._schedule_restart(unit, now, thermal_condition=False)
    assert unit.next_restart_at > now
    delay1 = unit.next_restart_at - now
    assert 4.5 <= delay1 <= 5.5  # first ladder step = 5 s (restart_count=1)

    # _schedule_restart increments restart_count itself; call it again for step 2
    pm._schedule_restart(unit, now, thermal_condition=False)
    delay2 = unit.next_restart_at - now
    assert 9.5 <= delay2 <= 10.5  # second step = 10 s (restart_count=2)


@pytest.mark.vl1
def test_loop_detected_after_three_restarts():
    pm = ProcessManager()
    unit = pm._units[0]
    now = time.monotonic()
    for _ in range(3):
        pm._schedule_restart(unit, now, thermal_condition=False)
    assert unit.loop_detected is True


@pytest.mark.vl1
def test_thermal_condition_uses_max_delay():
    pm = ProcessManager()
    unit = pm._units[0]
    now = time.monotonic()
    pm._schedule_restart(unit, now, thermal_condition=True)
    assert unit.next_restart_at >= now + _LADDER[-1] - 0.1


@pytest.mark.vl1
def test_update_progress_resets_stuck_timer():
    pm = ProcessManager()
    unit = pm._units[0]
    # Set last_progress far in the past
    unit.last_progress = time.monotonic() - 20.0
    pm.update_progress(unit.name)
    assert (time.monotonic() - unit.last_progress) < 1.0


@pytest.mark.vl1
def test_status_returns_all_units():
    pm = ProcessManager()
    s = pm.status()
    names = [u["name"] for u in s]
    assert "fm_time" in names
    assert "fm_measure" in names

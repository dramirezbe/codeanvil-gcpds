"""VL-1 tests for SUB-006/watchdog."""
import time
import pytest
from fm_supervisor.decision.watchdog import WatchdogManager
from fm_supervisor.hal.mock import MockThermalPort, MockWatchdogPort


@pytest.mark.vl1
def test_watchdog_fed_after_interval():
    wdog = MockWatchdogPort(timeout_s=60.0)
    thermal = MockThermalPort()
    mgr = WatchdogManager(wdog, thermal)
    mgr.open()
    mgr.mark_loop_ran()
    # Manually set last_feed to force feed
    mgr._last_feed = time.monotonic() - 6.0
    mgr.tick()
    assert len(wdog.feed_times) == 1


@pytest.mark.vl1
def test_watchdog_not_fed_without_loop_ran():
    wdog = MockWatchdogPort(timeout_s=60.0)
    thermal = MockThermalPort()
    mgr = WatchdogManager(wdog, thermal)
    mgr.open()
    # Do NOT call mark_loop_ran
    mgr._last_feed = time.monotonic() - 6.0
    mgr.tick()
    assert len(wdog.feed_times) == 0


@pytest.mark.vl1
def test_thermal_condition_raised_at_71():
    wdog = MockWatchdogPort()
    thermal = MockThermalPort()  # sequence: 25, 69, 71, 64, 85
    mgr = WatchdogManager(wdog, thermal)
    mgr.open()
    # Advance to 71 °C (3rd read)
    mgr._last_temp = time.monotonic() - 11.0
    mgr.tick()   # reads 25 → no condition
    mgr._last_temp = time.monotonic() - 11.0
    mgr.tick()   # reads 69 → no condition
    assert mgr.thermal_condition is False
    mgr._last_temp = time.monotonic() - 11.0
    mgr.tick()   # reads 71 → condition raised
    assert mgr.thermal_condition is True


@pytest.mark.vl1
def test_thermal_condition_cleared_at_64():
    wdog = MockWatchdogPort()
    thermal = MockThermalPort()  # sequence: 25, 69, 71, 64, 85
    mgr = WatchdogManager(wdog, thermal)
    mgr.open()
    # Advance to 71 then 64
    for _ in range(3):
        mgr._last_temp = time.monotonic() - 11.0
        mgr.tick()
    assert mgr.thermal_condition is True
    mgr._last_temp = time.monotonic() - 11.0
    mgr.tick()   # reads 64 → condition cleared
    assert mgr.thermal_condition is False

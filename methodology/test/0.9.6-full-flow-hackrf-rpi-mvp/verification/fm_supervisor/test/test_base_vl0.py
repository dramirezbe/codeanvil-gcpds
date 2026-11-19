"""VL-0 base top-down tests for fm_supervisor."""
import time

import pytest
from fm_supervisor.hal.mock import MockThermalPort, MockWatchdogPort


@pytest.mark.vl0
def test_thermal_sequence():
    t = MockThermalPort()
    readings = [t.read_celsius() for _ in range(5)]
    assert readings == [25.0, 69.0, 71.0, 64.0, 85.0]


@pytest.mark.vl0
def test_thermal_repeats_after_sequence():
    t = MockThermalPort()
    for _ in range(5):
        t.read_celsius()
    assert t.read_celsius() == 25.0  # wraps


@pytest.mark.vl0
def test_thermal_condition_at_71():
    t = MockThermalPort()
    readings = [t.read_celsius() for _ in range(5)]
    assert readings[2] == 71.0  # triggers thermal condition
    assert readings[3] == 64.0  # below 65 °C → clear


@pytest.mark.vl0
def test_watchdog_feeds_recorded():
    w = MockWatchdogPort()
    w.open()
    w.feed()
    w.feed()
    assert len(w.feed_times) == 2
    w.close("ordered")


@pytest.mark.vl0
def test_watchdog_no_reset_when_fed():
    w = MockWatchdogPort(timeout_s=60.0)
    w.open()
    w.feed()
    assert w.reset_triggered is False
    w.close()

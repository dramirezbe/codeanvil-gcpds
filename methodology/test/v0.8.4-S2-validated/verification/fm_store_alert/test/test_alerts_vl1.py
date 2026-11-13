"""VL-1 tests for SUB-002/alerts engine."""
import pytest
from fm_store_alert.output.alerts import AlertEngine


def _ch(ch: int, occ: str) -> dict:
    return {"channel": ch, "occupancy": occ, "power_dbm": -60.0 if occ == "Occupied" else -120.0}


def _chs(occ_map: dict) -> list[dict]:
    chs = []
    for ch in range(1, 200):
        occ = occ_map.get(ch, "Free")
        chs.append(_ch(ch, occ))
    return chs


@pytest.mark.vl1
def test_not_configured_without_station_map():
    eng = AlertEngine()
    assert eng._global["calibration_not_demonstrated"].status == "not_configured"


@pytest.mark.vl1
def test_configure_moves_to_evaluating():
    eng = AlertEngine()
    eng.configure({100: "TEST-FM"})
    # Per-channel rules are created on first evaluate
    events = eng.evaluate(_chs({}), "valid", "synced", 0)
    # No events yet (no silence run-up)
    assert all(e.rule != "channel_silent" for e in events)


@pytest.mark.vl1
def test_channel_silent_raises_after_10_scans():
    eng = AlertEngine({100: "TEST-FM"})
    for i in range(10):
        events = eng.evaluate(_chs({100: "Free"}), "valid", "synced", i * 6_000_000)
    raised = [e for e in events if e.rule == "channel_silent" and e.state == "raised"]
    assert len(raised) == 1
    assert raised[0].channel == 100


@pytest.mark.vl1
def test_channel_silent_clears_on_occupied():
    eng = AlertEngine({100: "TEST-FM"})
    for i in range(10):
        eng.evaluate(_chs({100: "Free"}), "valid", "synced", i * 6_000_000)
    # Occupied → cleared
    events = eng.evaluate(_chs({100: "Occupied"}), "valid", "synced", 10 * 6_000_000)
    cleared = [e for e in events if e.rule == "channel_silent" and e.state == "cleared"]
    assert len(cleared) == 1


@pytest.mark.vl1
def test_unexpected_occupancy_raises_after_3_scans():
    eng = AlertEngine({})  # no stations configured
    eng.configure({})
    for i in range(3):
        events = eng.evaluate(_chs({100: "Occupied"}), "valid", "synced", i * 6_000_000)
    raised = [e for e in events if e.rule == "unexpected_occupancy" and e.state == "raised"]
    assert len(raised) == 1
    assert raised[0].channel == 100


@pytest.mark.vl1
def test_cal_not_demonstrated_on_expired():
    eng = AlertEngine({100: "TEST-FM"})
    events = eng.evaluate(_chs({}), "expired", "synced", 0)
    raised = [e for e in events if e.rule == "calibration_not_demonstrated" and e.state == "raised"]
    assert len(raised) == 1


@pytest.mark.vl1
def test_cal_not_demonstrated_clears_on_valid():
    eng = AlertEngine({100: "TEST-FM"})
    eng.evaluate(_chs({}), "expired", "synced", 0)
    events = eng.evaluate(_chs({}), "valid", "synced", 1_000_000)
    cleared = [e for e in events if e.rule == "calibration_not_demonstrated" and e.state == "cleared"]
    assert len(cleared) == 1


@pytest.mark.vl1
def test_cal_expiring_raises_once():
    eng = AlertEngine({100: "TEST-FM"})
    events1 = eng.evaluate(_chs({}), "expiring", "synced", 0)
    events2 = eng.evaluate(_chs({}), "expiring", "synced", 1_000_000)
    raised_first = [e for e in events1 if e.rule == "calibration_expiring" and e.state == "raised"]
    raised_second = [e for e in events2 if e.rule == "calibration_expiring" and e.state == "raised"]
    assert len(raised_first) == 1
    assert len(raised_second) == 0  # not raised again


@pytest.mark.vl1
def test_active_alerts_tracked():
    eng = AlertEngine({100: "TEST-FM"})
    for i in range(10):
        eng.evaluate(_chs({100: "Free"}), "valid", "synced", i * 6_000_000)
    assert len(eng.active_alerts) >= 1

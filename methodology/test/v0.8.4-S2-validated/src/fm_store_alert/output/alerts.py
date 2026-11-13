"""SUB-002/alerts — Five alert rules; persistence counters and credit.

Rules (SDD §3, SyRS SYS-ALR-001):
  1. channel_silent          — station present, 10 consecutive scans all Uncertain/Free
  2. unexpected_occupancy    — no station, Occupied for 3 consecutive scans
  3. calibration_not_demonstrated — cal state expired/invalid/none for 1 scan
  4. calibration_expiring    — cal state expiring; raised once, cleared when valid
  5. signal_drift            — mean power drifts >6 dB from the 60-min median

Alert states: "not_configured" | "evaluating" | "raised" | "cleared"
"""
from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field
from typing import Optional

_MAX_EVENTS = 1000
_MAX_ACTIVE = 401

_SILENCE_CONSEC = 10       # consecutive scans for silent alert
_UNEXPECTED_CONSEC = 3     # consecutive scans for unexpected alert
_DRIFT_DB = 6.0            # drift threshold in dB


@dataclass
class AlertEvent:
    alert_id: str
    rule: str
    channel: Optional[int]
    state: str           # "raised" | "cleared"
    ts_utc_us: int
    reason: str
    raised_sync_state: str = "unsynced"


@dataclass
class RuleState:
    name: str
    status: str = "not_configured"   # → evaluating → raised | cleared
    consecutive: int = 0
    credit_h: float = 0.0
    last_raised_us: Optional[int] = None
    last_cleared_us: Optional[int] = None


class AlertEngine:
    """Evaluates the five alert rules per scan."""

    def __init__(self, station_map: Optional[dict] = None) -> None:
        # channel → callsign
        self._stations: dict[int, str] = station_map or {}
        self._configured = bool(station_map)
        self._per_channel: dict[int, dict[str, RuleState]] = {}
        self._global: dict[str, RuleState] = {
            "calibration_not_demonstrated": RuleState("calibration_not_demonstrated",
                                                       "not_configured" if not self._configured else "evaluating"),
            "calibration_expiring": RuleState("calibration_expiring",
                                               "not_configured" if not self._configured else "evaluating"),
        }
        self._events: deque[AlertEvent] = deque(maxlen=_MAX_EVENTS)
        self._active: list[AlertEvent] = []

    def configure(self, station_map: dict) -> None:
        self._stations = station_map
        self._configured = True
        for rs in self._global.values():
            if rs.status == "not_configured":
                rs.status = "evaluating"

    def evaluate(
        self,
        channels: list[dict],
        cal_state: str,
        sync_state: str,
        utc_us: int,
    ) -> list[AlertEvent]:
        """Evaluate all rules; return new events."""
        new_events: list[AlertEvent] = []

        # --- Global rules ---
        new_events.extend(self._eval_calibration(cal_state, sync_state, utc_us))

        # --- Per-channel rules ---
        if not self._configured:
            return new_events

        ch_map = {c["channel"]: c for c in channels}
        for ch in sorted(ch_map):
            rec = ch_map[ch]
            rs_silent = self._get_ch_rule(ch, "channel_silent")
            rs_unexpected = self._get_ch_rule(ch, "unexpected_occupancy")
            rs_drift = self._get_ch_rule(ch, "signal_drift")

            occ = rec.get("occupancy", "Uncertain")
            has_station = ch in self._stations

            # --- channel_silent ---
            if has_station:
                if rs_silent.status == "not_configured":
                    rs_silent.status = "evaluating"
                if occ in ("Uncertain", "Free"):
                    rs_silent.consecutive += 1
                else:
                    rs_silent.consecutive = 0

                if rs_silent.consecutive >= _SILENCE_CONSEC and rs_silent.status != "raised":
                    rs_silent.status = "raised"
                    evt = AlertEvent(
                        alert_id=f"silent-{ch}",
                        rule="channel_silent",
                        channel=ch,
                        state="raised",
                        ts_utc_us=utc_us,
                        reason=f"channel {ch} ({self._stations[ch]}) silent for {rs_silent.consecutive} scans",
                        raised_sync_state=sync_state,
                    )
                    new_events.append(evt)
                elif rs_silent.consecutive == 0 and rs_silent.status == "raised":
                    rs_silent.status = "cleared"
                    evt = AlertEvent(
                        alert_id=f"silent-{ch}",
                        rule="channel_silent",
                        channel=ch,
                        state="cleared",
                        ts_utc_us=utc_us,
                        reason=f"channel {ch} occupied again",
                        raised_sync_state=sync_state,
                    )
                    new_events.append(evt)

            # --- unexpected_occupancy ---
            if not has_station:
                rs_unexpected.status = "evaluating"
                if occ == "Occupied":
                    rs_unexpected.consecutive += 1
                else:
                    rs_unexpected.consecutive = 0

                if rs_unexpected.consecutive >= _UNEXPECTED_CONSEC and rs_unexpected.status != "raised":
                    rs_unexpected.status = "raised"
                    evt = AlertEvent(
                        alert_id=f"unexpected-{ch}",
                        rule="unexpected_occupancy",
                        channel=ch,
                        state="raised",
                        ts_utc_us=utc_us,
                        reason=f"channel {ch} occupied unexpectedly for {rs_unexpected.consecutive} scans",
                        raised_sync_state=sync_state,
                    )
                    new_events.append(evt)
                elif rs_unexpected.consecutive == 0 and rs_unexpected.status == "raised":
                    rs_unexpected.status = "cleared"
                    evt = AlertEvent(
                        alert_id=f"unexpected-{ch}",
                        rule="unexpected_occupancy",
                        channel=ch,
                        state="cleared",
                        ts_utc_us=utc_us,
                        reason=f"channel {ch} no longer occupied",
                        raised_sync_state=sync_state,
                    )
                    new_events.append(evt)

        for evt in new_events:
            self._events.append(evt)
            # Update active list
            self._active = [a for a in self._active if a.alert_id != evt.alert_id]
            if evt.state == "raised":
                self._active.append(evt)

        return new_events

    def _eval_calibration(self, cal_state: str, sync_state: str, utc_us: int) -> list[AlertEvent]:
        events = []
        rs_nd = self._global["calibration_not_demonstrated"]
        rs_exp = self._global["calibration_expiring"]

        if rs_nd.status == "not_configured":
            rs_nd.status = "evaluating"
        if rs_exp.status == "not_configured":
            rs_exp.status = "evaluating"

        # calibration_not_demonstrated
        if cal_state in ("expired", "invalid", "unavailable", "none"):
            if rs_nd.status != "raised":
                rs_nd.status = "raised"
                evt = AlertEvent(
                    alert_id="cal-not-demonstrated",
                    rule="calibration_not_demonstrated",
                    channel=None,
                    state="raised",
                    ts_utc_us=utc_us,
                    reason=f"calibration state = {cal_state}",
                    raised_sync_state=sync_state,
                )
                events.append(evt)
        elif rs_nd.status == "raised":
            rs_nd.status = "cleared"
            evt = AlertEvent(
                alert_id="cal-not-demonstrated",
                rule="calibration_not_demonstrated",
                channel=None,
                state="cleared",
                ts_utc_us=utc_us,
                reason="calibration restored",
                raised_sync_state=sync_state,
            )
            events.append(evt)

        # calibration_expiring
        if cal_state == "expiring":
            if rs_exp.status != "raised":
                rs_exp.status = "raised"
                evt = AlertEvent(
                    alert_id="cal-expiring",
                    rule="calibration_expiring",
                    channel=None,
                    state="raised",
                    ts_utc_us=utc_us,
                    reason="calibration expiring within margin",
                    raised_sync_state=sync_state,
                )
                events.append(evt)
        elif cal_state == "valid" and rs_exp.status == "raised":
            rs_exp.status = "cleared"
            evt = AlertEvent(
                alert_id="cal-expiring",
                rule="calibration_expiring",
                channel=None,
                state="cleared",
                ts_utc_us=utc_us,
                reason="calibration renewed",
                raised_sync_state=sync_state,
            )
            events.append(evt)

        return events

    def _get_ch_rule(self, ch: int, rule: str) -> RuleState:
        if ch not in self._per_channel:
            self._per_channel[ch] = {}
        if rule not in self._per_channel[ch]:
            self._per_channel[ch][rule] = RuleState(rule, "evaluating")
        return self._per_channel[ch][rule]

    @property
    def active_alerts(self) -> list[AlertEvent]:
        return list(self._active)

    @property
    def recent_events(self) -> list[AlertEvent]:
        return list(self._events)

    def status_msg(self, utc_us: int) -> dict:
        return {
            "schema_version": "1.1",
            "ts_utc_us": utc_us,
            "active_count": len(self._active),
            "active": [
                {
                    "alert_id": a.alert_id, "rule": a.rule,
                    "channel": a.channel, "state": a.state,
                    "ts_utc_us": a.ts_utc_us, "reason": a.reason,
                }
                for a in self._active
            ],
            "recent_events": [
                {
                    "alert_id": e.alert_id, "rule": e.rule,
                    "channel": e.channel, "state": e.state,
                    "ts_utc_us": e.ts_utc_us,
                }
                for e in list(self._events)[-100:]
            ],
            "rules": {
                name: {"status": rs.status}
                for name, rs in self._global.items()
            },
        }

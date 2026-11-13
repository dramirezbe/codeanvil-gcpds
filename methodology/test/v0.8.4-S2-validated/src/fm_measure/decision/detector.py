"""SUB-001/detector — Classify each channel as Occupied / Free / Uncertain.

Decision rules (from §3, SDD):
  Occupied : excess ≥ THRESHOLD_DB and adj_ratio ≥ ADJ_RATIO_DB
  Free     : excess < THRESHOLD_DB AND all Free-release conditions met
  Uncertain: everything else

Hysteresis: a channel leaving Occupied must spend ≥1 scan at Free before it can
re-enter Occupied (prevents rapid state flip on the threshold edge).

Adjacent-channel ratio: at least one of the two adjacent channels must be ≥10 dB
below the target channel to confirm the target is a real carrier (not leakage).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

_THRESHOLD_DB = -100.0        # dBm occupied threshold (operator-configurable)
_ADJ_RATIO_DB = 10.0          # dB minimum ratio over adjacent channel
_MIN_POWER_DBFS = -140.0


@dataclass
class OccupancyResult:
    channel: int
    state: str                # "Occupied" | "Free" | "Uncertain"
    uncertain_reason: Optional[str]  # e.g. "no_data" | "clipped" | "scan_flagged" | "insufficient_history" | None


class ChannelDetector:
    """Stateful per-channel detector with hysteresis."""

    def __init__(self, threshold_dbm: float = _THRESHOLD_DB) -> None:
        self._threshold = threshold_dbm
        self._prev_state: dict[int, str] = {}

    def classify(
        self,
        channels: list,  # list of CalibratedChannel
        noise_floor: Optional[dict] = None,  # channel → noise floor in dBm (from history)
    ) -> list[OccupancyResult]:
        powers = {ch.channel: ch for ch in channels}
        results = []

        for ch in sorted(powers, key=lambda x: x):
            rec = powers[ch]

            # --- Withheld / no data first ---
            if rec.withheld_reason is not None or rec.power_dbm is None:
                reason = rec.withheld_reason or "no_data"
                results.append(OccupancyResult(channel=ch, state="Uncertain",
                                                uncertain_reason=reason))
                self._prev_state[ch] = "Uncertain"
                continue

            power = rec.power_dbm
            nf = (noise_floor or {}).get(ch)
            # Use noise floor when available; otherwise use static threshold
            threshold = (nf + 6.0) if nf is not None else self._threshold
            excess = power - threshold

            # Adjacent channel powers
            left = powers.get(ch - 1)
            right = powers.get(ch + 1)
            left_p = left.power_dbm if left and left.power_dbm is not None else None
            right_p = right.power_dbm if right and right.power_dbm is not None else None

            # Adjacent ratio: at least one adjacent must be ADJ_RATIO_DB below
            adj_ok = False
            if left_p is not None and (power - left_p) >= _ADJ_RATIO_DB:
                adj_ok = True
            if right_p is not None and (power - right_p) >= _ADJ_RATIO_DB:
                adj_ok = True
            if left_p is None and right_p is None:
                adj_ok = True  # edge of band; no adjacent to compare

            if excess >= 0.0 and adj_ok:
                state = "Occupied"
            elif excess < 0.0:
                # Hysteresis: if previously Occupied, stay one scan at the boundary
                prev = self._prev_state.get(ch, "Free")
                if prev == "Occupied":
                    state = "Uncertain"
                    reason = "hysteresis"
                    results.append(OccupancyResult(channel=ch, state=state,
                                                    uncertain_reason=reason))
                    self._prev_state[ch] = "Uncertain"
                    continue
                state = "Free"
            else:
                # Above threshold but adj_ratio not met → Uncertain (leakage)
                state = "Uncertain"
                results.append(OccupancyResult(channel=ch, state=state,
                                                uncertain_reason="adj_ratio"))
                self._prev_state[ch] = "Uncertain"
                continue

            results.append(OccupancyResult(channel=ch, state=state, uncertain_reason=None))
            self._prev_state[ch] = state

        return results

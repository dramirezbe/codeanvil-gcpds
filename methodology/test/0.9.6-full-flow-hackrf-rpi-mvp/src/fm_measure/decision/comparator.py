"""SUB-001/comparator — Compare occupancy with the station reference.

Decision table (SDD §3):
  Occupied  + station present  → Authorised
  Occupied  + station absent   → Unexpected
  Free      + station present  → Silent
  Free      + station absent   → Clear
  Uncertain + any              → Indeterminate (never a verdict)
  Any       + reference absent → Indeterminate

Reference absent/invalid → all channels Indeterminate.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from fm_measure.decision.detector import OccupancyResult

_VERDICTS = {
    ("Occupied", True): "Authorised",
    ("Occupied", False): "Unexpected",
    ("Free", True): "Silent",
    ("Free", False): "Clear",
}


@dataclass
class StationEntry:
    channel: int
    callsign: str
    expected_power_dbm: Optional[float] = None


@dataclass
class AssignmentResult:
    channel: int
    occupancy: str
    verdict: str           # "Authorised" | "Unexpected" | "Silent" | "Clear" | "Indeterminate"
    station: Optional[StationEntry]


def compare(
    occupancy: list[OccupancyResult],
    reference: Optional[list[StationEntry]],  # None = reference absent
) -> list[AssignmentResult]:
    if reference is None:
        return [
            AssignmentResult(channel=r.channel, occupancy=r.state,
                              verdict="Indeterminate", station=None)
            for r in occupancy
        ]

    # Build lookup: channel → station entry
    station_map = {s.channel: s for s in reference}

    results = []
    for r in occupancy:
        if r.state == "Uncertain":
            verdict = "Indeterminate"
            station = station_map.get(r.channel)
        else:
            station = station_map.get(r.channel)
            has_station = station is not None
            verdict = _VERDICTS.get((r.state, has_station), "Indeterminate")

        results.append(AssignmentResult(
            channel=r.channel,
            occupancy=r.state,
            verdict=verdict,
            station=station,
        ))

    return results

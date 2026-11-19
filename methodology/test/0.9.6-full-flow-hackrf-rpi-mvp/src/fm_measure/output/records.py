"""SUB-001/records — Assemble scan_records.v1 from all pipeline outputs.

Schema: scan_records.v1 — one message per 6 s scan, ~0.23 MB.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Optional

from fm_measure.dsp.calibration import CalibratedChannel, CalibratedPowerScan
from fm_measure.decision.comparator import AssignmentResult
from fm_measure.decision.detector import OccupancyResult

_EVIDENCE_LABEL = "FM screening — not a compliance determination"
_PROHIBITED_WORDS = ["compliant", "certified", "legal", "illegal"]


@dataclass
class ChannelRecord:
    channel: int
    step: int
    frequency_hz: float
    power_dbm: Optional[float]
    uncertainty_db: float
    occupancy: str
    verdict: str
    withheld_reason: Optional[str]
    dc_adjacent: bool
    no_data: bool
    clipped: bool
    scan_flagged: bool
    mapping_error_bound_khz: float
    mapping_limit_exceeded: bool
    station_callsign: Optional[str]
    expected_power_dbm: Optional[float]


@dataclass
class HealthRecord:
    scan_id: int
    scan_late: bool
    overflow_count: int
    dropped_frame_count: int
    clipped_captures: int
    retune_failures: int
    scan_duration_s: float
    records_flag_scan: bool


@dataclass
class ScanRecords:
    schema_version: str
    scan_id: int
    scan_start_utc_us: int
    scan_start_sync_state: str
    station_id: str
    config_sha256: str
    calibration_state: str
    evidence_label: str
    health: HealthRecord
    channels: list[ChannelRecord]


def _check_prohibited(text: str) -> None:
    for word in _PROHIBITED_WORDS:
        if word in text.lower():
            raise ValueError(f"prohibited word in evidence label: {word!r}")


def assemble(
    cal_scan: CalibratedPowerScan,
    occupancy: list[OccupancyResult],
    assignments: list[AssignmentResult],
    health: dict,
    station_id: str,
    config_sha256: str,
    cal_state: str,
    freq_start_hz: float = 87_600_000.0,
    channel_spacing_hz: float = 100_000.0,
) -> ScanRecords:
    _check_prohibited(_EVIDENCE_LABEL)

    occ_map = {r.channel: r for r in occupancy}
    asg_map = {r.channel: r for r in assignments}
    cal_map = {c.channel: c for c in cal_scan.channels}

    channels: list[ChannelRecord] = []
    for ch_num in sorted(cal_map):
        cal_ch = cal_map[ch_num]
        occ = occ_map.get(ch_num)
        asg = asg_map.get(ch_num)
        freq = freq_start_hz + (ch_num - 1) * channel_spacing_hz
        channels.append(ChannelRecord(
            channel=ch_num,
            step=cal_ch.step,
            frequency_hz=freq,
            power_dbm=cal_ch.power_dbm,
            uncertainty_db=cal_ch.uncertainty_db,
            occupancy=occ.state if occ else "Uncertain",
            verdict=asg.verdict if asg else "Indeterminate",
            withheld_reason=cal_ch.withheld_reason,
            dc_adjacent=cal_ch.dc_adjacent,
            no_data=cal_ch.no_data,
            clipped=cal_ch.clipped,
            scan_flagged=cal_ch.scan_flagged,
            mapping_error_bound_khz=cal_ch.mapping_error_bound_khz,
            mapping_limit_exceeded=cal_ch.mapping_limit_exceeded,
            station_callsign=asg.station.callsign if asg and asg.station else None,
            expected_power_dbm=asg.station.expected_power_dbm if asg and asg.station else None,
        ))

    hrec = HealthRecord(
        scan_id=cal_scan.scan_id,
        scan_late=health.get("scan_late", False),
        overflow_count=health.get("overflow_count", 0),
        dropped_frame_count=health.get("dropped_frame_count", 0),
        clipped_captures=health.get("clipped_captures", 0),
        retune_failures=health.get("retune_failures", 0),
        scan_duration_s=health.get("scan_duration_s", 0.0),
        records_flag_scan=health.get("records_flag_scan", False),
    )

    return ScanRecords(
        schema_version="1.0",
        scan_id=cal_scan.scan_id,
        scan_start_utc_us=cal_scan.scan_start_utc_us,
        scan_start_sync_state=cal_scan.scan_start_sync_state,
        station_id=station_id,
        config_sha256=config_sha256,
        calibration_state=cal_state,
        evidence_label=_EVIDENCE_LABEL,
        health=hrec,
        channels=channels,
    )

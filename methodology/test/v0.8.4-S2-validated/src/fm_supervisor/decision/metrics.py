"""SUB-006/metrics — Availability and field-validation analysis.

Reads supervisor log lines and report_header files. Never writes runtime output.
Provides availability over 30-day window (R-48/R-49) and 72 h field-validation analysis.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class AvailabilityRecord:
    window_start_utc_us: int
    window_end_utc_us: int
    total_scans_expected: int
    total_scans_delivered: int
    availability_pct: float
    missing_gaps: list[dict]


@dataclass
class FieldValidationRecord:
    run_id: str
    station_id: str
    start_utc_us: int
    end_utc_us: int
    scans_analysed: int
    acceptance: bool
    notes: str


def compute_availability(
    log_lines: list[dict],
    window_start_us: int,
    window_end_us: int,
    scan_interval_us: int = 6_000_000,
) -> AvailabilityRecord:
    """Compute availability percentage from log lines over a time window.

    Each log line must have `ts_utc_us` and `event` fields.
    A 'scan_complete' event counts as one delivered scan.
    """
    delivered_times = [
        line["ts_utc_us"]
        for line in log_lines
        if line.get("event") == "scan_complete"
        and window_start_us <= line["ts_utc_us"] <= window_end_us
    ]
    delivered_times.sort()
    window_us = window_end_us - window_start_us
    expected = max(1, window_us // scan_interval_us)
    delivered = len(delivered_times)
    pct = 100.0 * delivered / expected

    # Detect gaps
    gaps: list[dict] = []
    prev = window_start_us
    for t in delivered_times:
        gap = t - prev
        if gap > 2 * scan_interval_us:
            gaps.append({"start_us": prev, "end_us": t, "duration_s": gap / 1_000_000})
        prev = t
    if window_end_us - prev > 2 * scan_interval_us:
        gaps.append({"start_us": prev, "end_us": window_end_us,
                     "duration_s": (window_end_us - prev) / 1_000_000})

    return AvailabilityRecord(
        window_start_utc_us=window_start_us,
        window_end_utc_us=window_end_us,
        total_scans_expected=expected,
        total_scans_delivered=delivered,
        availability_pct=pct,
        missing_gaps=gaps,
    )


def run_field_validation(
    report_dir: Path,
    start_utc_us: int,
    end_utc_us: int,
    station_id: str,
    acceptance_threshold_pct: float = 95.0,
) -> FieldValidationRecord:
    """Run the 72 h field-validation procedure from report header files."""
    scans = 0
    run_id = "unknown"
    for header_path in sorted(report_dir.glob("*/report_header.csv")):
        try:
            lines = header_path.read_text().splitlines()
            for line in lines:
                parts = line.split(",")
                if len(parts) >= 2 and parts[0].strip() == "run_id":
                    run_id = parts[1].strip()
                if len(parts) >= 2 and parts[0].strip() == "scan_count":
                    scans += int(parts[1].strip())
        except Exception:
            continue

    window_us = end_utc_us - start_utc_us
    expected = max(1, window_us // 6_000_000)
    pct = 100.0 * scans / expected
    acceptance = pct >= acceptance_threshold_pct

    return FieldValidationRecord(
        run_id=run_id,
        station_id=station_id,
        start_utc_us=start_utc_us,
        end_utc_us=end_utc_us,
        scans_analysed=scans,
        acceptance=acceptance,
        notes=(
            f"availability {pct:.1f}% >= {acceptance_threshold_pct}%"
            if acceptance
            else f"availability {pct:.1f}% < {acceptance_threshold_pct}%; REJECTED"
        ),
    )

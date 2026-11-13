"""VL-1 tests for SUB-006/metrics."""
import csv
import pytest
from pathlib import Path
from fm_supervisor.decision.metrics import compute_availability, run_field_validation


@pytest.mark.vl1
def test_availability_100pct():
    start = 0
    end = 60_000_000  # 60 s = 10 expected scans
    lines = [
        {"event": "scan_complete", "ts_utc_us": i * 6_000_000}
        for i in range(10)
    ]
    rec = compute_availability(lines, start, end)
    assert rec.total_scans_delivered == 10
    assert rec.availability_pct == 100.0


@pytest.mark.vl1
def test_availability_with_gap():
    start = 0
    end = 60_000_000
    # deliver only 5 of 10 scans, with a gap
    lines = [
        {"event": "scan_complete", "ts_utc_us": i * 6_000_000}
        for i in range(5)
    ]
    rec = compute_availability(lines, start, end)
    assert rec.total_scans_delivered == 5
    assert rec.availability_pct < 60.0
    assert len(rec.missing_gaps) >= 1


@pytest.mark.vl1
def test_availability_excludes_out_of_window():
    start = 10_000_000
    end = 60_000_000
    lines = [
        {"event": "scan_complete", "ts_utc_us": 0},  # before window
        {"event": "scan_complete", "ts_utc_us": 15_000_000},
        {"event": "scan_complete", "ts_utc_us": 21_000_000},
    ]
    rec = compute_availability(lines, start, end)
    assert rec.total_scans_delivered == 2


@pytest.mark.vl1
def test_field_validation_acceptance(tmp_path):
    run_dir = tmp_path / "RUN-001"
    run_dir.mkdir()
    header = run_dir / "report_header.csv"
    # 72 h window = 72 * 3600 / 6 = 43200 expected scans; deliver 42000 → 97.2 %
    header.write_text("run_id,RUN-001\nscan_count,42000\n")
    start_us = 0
    end_us = 72 * 3600 * 1_000_000
    rec = run_field_validation(tmp_path, start_us, end_us, "COL-001")
    assert rec.acceptance is True


@pytest.mark.vl1
def test_field_validation_rejection(tmp_path):
    run_dir = tmp_path / "RUN-002"
    run_dir.mkdir()
    header = run_dir / "report_header.csv"
    # Only 30000 scans → 69 % → rejected
    header.write_text("run_id,RUN-002\nscan_count,30000\n")
    start_us = 0
    end_us = 72 * 3600 * 1_000_000
    rec = run_field_validation(tmp_path, start_us, end_us, "COL-001")
    assert rec.acceptance is False

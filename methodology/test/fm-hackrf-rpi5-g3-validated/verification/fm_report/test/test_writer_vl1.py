"""VL-1 tests for SUB-003/writer."""
import csv
import os
import time
import pytest
from pathlib import Path
from fm_report.output.writer import ReportWriter


def _scan(scan_id: int, n_channels: int = 3) -> dict:
    return {
        "scan_id": scan_id,
        "scan_start_utc_us": scan_id * 6_000_000,
        "scan_start_sync_state": "synced",
        "calibration_state": "valid",
        "evidence_label": "FM screening — not a compliance determination",
        "channels": [
            {
                "channel": i, "frequency_hz": 87_600_000 + (i-1)*100_000,
                "power_dbm": -80.0, "uncertainty_db": 0.5,
                "occupancy": "Free", "verdict": "Clear",
                "withheld_reason": None,
            }
            for i in range(1, n_channels + 1)
        ],
    }


@pytest.mark.vl1
def test_open_and_close_run(tmp_path):
    w = ReportWriter(tmp_path)
    w.open_run("RUN-001", "COL-001", "abc123", 0)
    w.write_scan(_scan(1))
    w.close_run()
    assert (tmp_path / "RUN-001" / "report_header.csv").exists()
    assert not (tmp_path / "RUN-001" / "report_header.tmp").exists()


@pytest.mark.vl1
def test_header_contains_scan_count(tmp_path):
    w = ReportWriter(tmp_path)
    w.open_run("RUN-002", "COL-001", "abc123", 0)
    for i in range(5):
        w.write_scan(_scan(i + 1))
    w.close_run()
    rows = {r[0]: r[1] for r in csv.reader((tmp_path / "RUN-002" / "report_header.csv").open())}
    assert rows["scan_count"] == "5"


@pytest.mark.vl1
def test_lines_file_has_correct_rows(tmp_path):
    w = ReportWriter(tmp_path)
    w.open_run("RUN-003", "COL-001", "abc123", 0)
    w.write_scan(_scan(1, n_channels=3))
    w.close_run()
    lines_path = tmp_path / "RUN-003" / "report_lines_0001.csv"
    rows = list(csv.DictReader(lines_path.open()))
    assert len(rows) == 3  # 3 channels
    assert rows[0]["scan_id"] == "1"


@pytest.mark.vl1
def test_atomic_rename_no_tmp_on_close(tmp_path):
    w = ReportWriter(tmp_path)
    w.open_run("RUN-004", "COL-001", "abc123", 0)
    # Abort without close → .tmp exists
    assert (tmp_path / "RUN-004" / "report_header.tmp").exists()
    # Recovery: re-open same run_id
    w.close_run(interrupted=True)
    assert not (tmp_path / "RUN-004" / "report_header.tmp").exists()


@pytest.mark.vl1
def test_segment_rotation(tmp_path, monkeypatch):
    w = ReportWriter(tmp_path)
    w.open_run("RUN-005", "COL-001", "abc123", 0)
    # Force segment rotation by backdating segment_start
    w._segment_start = time.monotonic() - 3601
    w.write_scan(_scan(1))  # triggers rotation
    w.write_scan(_scan(2))
    w.close_run()
    # Should have 2 segment files
    segments = sorted((tmp_path / "RUN-005").glob("report_lines_*.csv"))
    assert len(segments) == 2


@pytest.mark.vl1
def test_interrupted_flag_in_header(tmp_path):
    w = ReportWriter(tmp_path)
    w.open_run("RUN-006", "COL-001", "abc123", 0)
    w.close_run(interrupted=True)
    rows = {r[0]: r[1] for r in csv.reader((tmp_path / "RUN-006" / "report_header.csv").open())}
    assert rows["interrupted"] == "true"

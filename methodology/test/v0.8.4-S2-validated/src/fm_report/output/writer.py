"""SUB-003/writer — Screening report writer.

Writes report_header.csv and report_lines.csv with:
- Atomic header rename (write to .tmp, rename on finalise)
- fsynced scan lines
- 3600 s segment rotation
- 60 s progress publication
- Space checks before each write
- Interrupted-run recovery

Required VL: VL-1 (filesystem logic, temp-dir testable).
"""
from __future__ import annotations

import csv
import io
import os
import time
from pathlib import Path
from typing import Optional

from fm_report.config.logger import get_logger
from fm_report.config.paths import REPORT_DIR

log = get_logger(__name__)

_SEGMENT_S = 3600       # rotate segment every 1 h
_PROGRESS_INTERVAL_S = 60
_MIN_FREE_MB = 100      # refuse to write if less than this free


class ReportWriter:
    """Writes one screening report run to a directory under REPORT_DIR."""

    def __init__(self, report_dir: Path = REPORT_DIR) -> None:
        self._base = report_dir
        self._run_id: Optional[str] = None
        self._run_dir: Optional[Path] = None
        self._header_tmp: Optional[Path] = None
        self._header_final: Optional[Path] = None
        self._lines_fd: Optional[io.TextIOWrapper] = None
        self._scan_count = 0
        self._segment_start: Optional[float] = None
        self._last_progress = 0.0
        self._interrupted = False
        self._segment_index = 1

    def open_run(self, run_id: str, station_id: str, config_sha256: str, start_utc_us: int) -> None:
        """Start a new reporting run."""
        self._run_id = run_id
        self._run_dir = self._base / run_id
        self._run_dir.mkdir(parents=True, exist_ok=True)
        self._scan_count = 0
        self._segment_index = 1
        self._segment_start = time.monotonic()
        self._interrupted = False

        # Recover any interrupted run (header.tmp present)
        tmp_candidate = self._run_dir / "report_header.tmp"
        if tmp_candidate.exists():
            log.warning(f"recovering interrupted run {run_id}")
            tmp_candidate.unlink()
            self._interrupted = True

        # Write header to .tmp (finalised on close_run)
        self._header_tmp = self._run_dir / "report_header.tmp"
        self._header_final = self._run_dir / "report_header.csv"
        with open(self._header_tmp, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["field", "value"])
            w.writerow(["run_id", run_id])
            w.writerow(["station_id", station_id])
            w.writerow(["config_sha256", config_sha256])
            w.writerow(["start_utc_us", start_utc_us])
            w.writerow(["schema_version", "1.0"])
            f.flush()
            os.fsync(f.fileno())

        self._open_segment()
        log.info(f"opened run {run_id}")

    def _open_segment(self) -> None:
        if self._lines_fd is not None:
            self._lines_fd.close()
        seg_path = self._run_dir / f"report_lines_{self._segment_index:04d}.csv"
        self._lines_fd = open(seg_path, "a", newline="")
        if seg_path.stat().st_size == 0:
            w = csv.writer(self._lines_fd)
            w.writerow([
                "scan_id", "scan_start_utc_us", "scan_start_sync_state",
                "channel", "frequency_hz", "power_dbm", "uncertainty_db",
                "occupancy", "verdict", "withheld_reason",
                "calibration_state", "evidence_label",
            ])
            self._lines_fd.flush()
            os.fsync(self._lines_fd.fileno())

    def write_scan(self, scan_records: dict) -> None:
        """Append one scan_records.v1 to the current segment."""
        if self._lines_fd is None or self._run_dir is None:
            raise RuntimeError("run not open")

        # Space check
        st = os.statvfs(str(self._run_dir))
        free_mb = (st.f_bavail * st.f_frsize) / (1024 * 1024)
        if free_mb < _MIN_FREE_MB:
            log.error(f"low disk space: {free_mb:.0f} MB free; skipping scan")
            return

        # Segment rotation
        now = time.monotonic()
        if self._segment_start is not None and (now - self._segment_start) >= _SEGMENT_S:
            self._segment_index += 1
            self._segment_start = now
            self._open_segment()

        w = csv.writer(self._lines_fd)
        scan_id = scan_records.get("scan_id")
        utc_us = scan_records.get("scan_start_utc_us")
        sync = scan_records.get("scan_start_sync_state", "unsynced")
        cal = scan_records.get("calibration_state", "unavailable")
        label = scan_records.get("evidence_label", "")

        for ch in scan_records.get("channels", []):
            w.writerow([
                scan_id, utc_us, sync,
                ch.get("channel"), ch.get("frequency_hz"), ch.get("power_dbm"),
                ch.get("uncertainty_db"), ch.get("occupancy"), ch.get("verdict"),
                ch.get("withheld_reason"), cal, label,
            ])

        self._lines_fd.flush()
        os.fsync(self._lines_fd.fileno())
        self._scan_count += 1

        # Progress
        if (now - self._last_progress) >= _PROGRESS_INTERVAL_S:
            log.info(f"run {self._run_id}: {self._scan_count} scans written")
            self._last_progress = now

    def close_run(self, interrupted: bool = False) -> None:
        """Finalise the run: rename header.tmp → header.csv."""
        if self._lines_fd is not None:
            self._lines_fd.close()
            self._lines_fd = None

        if self._header_tmp and self._header_final:
            # Append final scan count and close time to the header
            with open(self._header_tmp, "a", newline="") as f:
                w = csv.writer(f)
                w.writerow(["scan_count", self._scan_count])
                w.writerow(["end_utc_us", int(time.time() * 1_000_000)])
                w.writerow(["interrupted", str(interrupted).lower()])
                f.flush()
                os.fsync(f.fileno())
            self._header_tmp.rename(self._header_final)
            log.info(f"closed run {self._run_id}: {self._scan_count} scans, interrupted={interrupted}")

        self._run_id = None
        self._run_dir = None

    @property
    def scan_count(self) -> int:
        return self._scan_count

    @property
    def run_id(self) -> Optional[str]:
        return self._run_id

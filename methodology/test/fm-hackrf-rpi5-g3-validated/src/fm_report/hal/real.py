"""Real ReportStorePort — writes to the mounted microSD report directory."""
from __future__ import annotations

import os
from pathlib import Path

from fm_report.config.logger import get_logger
from fm_report.config.paths import REPORT_DIR
from fm_report.hal.port import ReportStorePort

log = get_logger(__name__)


class RealReportStorePort(ReportStorePort):
    """Writes to FM_REPORT_DIR (default /var/lib/fm/reports)."""

    def __init__(self, base_dir: Path = REPORT_DIR) -> None:
        self._base = base_dir
        self._base.mkdir(parents=True, exist_ok=True)

    def open_run(self, run_id: str) -> Path:
        run_dir = self._base / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        return run_dir

    def append_scan(self, run_id: str, lines: list[str]) -> None:
        seg_path = self._base / run_id / "current_segment.csv"
        with seg_path.open("a") as f:
            for line in lines:
                f.write(line + "\n")

    def fsync(self, run_id: str) -> None:
        seg_path = self._base / run_id / "current_segment.csv"
        if seg_path.exists():
            with seg_path.open("r+") as f:
                os.fsync(f.fileno())

    def open_segment(self, run_id: str, segment_id: str) -> None:
        seg_path = self._base / run_id / f"{segment_id}.csv"
        seg_path.touch()

    def close_segment(self, run_id: str, segment_id: str) -> None:
        pass

    def free_space(self) -> int:
        import shutil
        return shutil.disk_usage(self._base).free

    def rename_atomic(self, src: Path, dst: Path) -> None:
        os.replace(src, dst)

"""Mock ReportStorePort — writes to a temp directory, no hardware needed."""
from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path

from fm_report.config.logger import get_logger
from fm_report.hal.port import ReportStorePort

log = get_logger(__name__)


class MockReportStorePort(ReportStorePort):
    """In-process mock store backed by a temporary directory."""

    def __init__(self, base_dir: Path | None = None) -> None:
        if base_dir is None:
            self._tmpdir = tempfile.mkdtemp(prefix="fm_report_mock_")
            self._base = Path(self._tmpdir)
        else:
            self._tmpdir = None
            self._base = base_dir
            base_dir.mkdir(parents=True, exist_ok=True)
        self._handles: dict[str, object] = {}
        log.info(f"MockReportStorePort base={self._base}")

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
        return shutil.disk_usage(self._base).free

    def rename_atomic(self, src: Path, dst: Path) -> None:
        os.replace(src, dst)

    def cleanup(self) -> None:
        if self._tmpdir:
            shutil.rmtree(self._tmpdir, ignore_errors=True)

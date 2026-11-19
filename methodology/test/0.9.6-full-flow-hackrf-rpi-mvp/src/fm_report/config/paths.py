"""Filesystem paths for fm_report."""
import os
from pathlib import Path

_SOCKET_DIR = Path(os.environ.get("FM_SOCKET_DIR", "/run/fm"))
_REPORT_DIR = Path(os.environ.get("FM_REPORT_DIR", "/var/lib/fm/reports"))

REPORT_DIR = _REPORT_DIR
SCAN_SOCK = _SOCKET_DIR / "scan.sock"
CATALOG_SOCK = _SOCKET_DIR / "catalog.sock"
REPORT_CMD_SOCK = _SOCKET_DIR / "report_cmd.sock"
TIME_SOCK = _SOCKET_DIR / "time.sock"
CONFIG_SOCK = _SOCKET_DIR / "config.sock"
PROGRESS_SOCK = _SOCKET_DIR / "progress" / "report.sock"

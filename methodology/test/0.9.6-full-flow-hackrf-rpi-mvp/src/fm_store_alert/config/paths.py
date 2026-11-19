"""Filesystem paths for fm_store_alert."""
import os
from pathlib import Path

_SOCKET_DIR = Path(os.environ.get("FM_SOCKET_DIR", "/run/fm"))

SCAN_SOCK = _SOCKET_DIR / "scan.sock"
CALV_SOCK = _SOCKET_DIR / "calv.sock"
HISTORY_SOCK = _SOCKET_DIR / "history.sock"
ALERTS_SOCK = _SOCKET_DIR / "alerts.sock"
TIME_SOCK = _SOCKET_DIR / "time.sock"
CONFIG_SOCK = _SOCKET_DIR / "config.sock"
SUPERVISOR_SOCK = _SOCKET_DIR / "supervisor.sock"
PROGRESS_SOCK = _SOCKET_DIR / "progress" / "store_alert.sock"

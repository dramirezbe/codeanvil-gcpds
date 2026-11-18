"""Filesystem paths for fm_measure."""
import os
from pathlib import Path

_SOCKET_DIR = Path(os.environ.get("FM_SOCKET_DIR", "/run/fm"))
_DATA_DIR = Path(os.environ.get("FM_DATA_DIR", "/var/lib/fm"))

CALIBRATION_DIR = Path(os.environ.get("FM_CALIBRATION_DIR", str(_DATA_DIR / "calibration")))
VALIDATION_DIR = CALIBRATION_DIR / "validation"
CALV_ACTIVE = CALIBRATION_DIR / "active.json"

SCAN_SOCK = _SOCKET_DIR / "scan.sock"
CALV_SOCK = _SOCKET_DIR / "calv.sock"
PROGRESS_SOCK = _SOCKET_DIR / "progress" / "measure.sock"
TIME_SOCK = _SOCKET_DIR / "time.sock"
CONFIG_SOCK = _SOCKET_DIR / "config.sock"

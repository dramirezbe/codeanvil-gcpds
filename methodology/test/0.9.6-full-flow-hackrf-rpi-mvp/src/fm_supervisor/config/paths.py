"""Filesystem paths for fm_supervisor."""
import os
from pathlib import Path

_SOCKET_DIR = Path(os.environ.get("FM_SOCKET_DIR", "/run/fm"))
_DATA_DIR = Path(os.environ.get("FM_DATA_DIR", "/var/lib/fm"))

CONFIG_FILE = _DATA_DIR / "site-config.json"
STATION_REF_FILE = _DATA_DIR / "station-reference.json"
LOG_FILE = _DATA_DIR / "supervisor.log"

SUPERVISOR_SOCK = _SOCKET_DIR / "supervisor.sock"
CONFIG_SOCK = _SOCKET_DIR / "config.sock"
REPORT_CMD_SOCK = _SOCKET_DIR / "report_cmd.sock"
SHUTDOWN_SOCK = _SOCKET_DIR / "shutdown.sock"
PROGRESS_DIR = _SOCKET_DIR / "progress"
WATCHDOG_DEV = Path(os.environ.get("FM_WATCHDOG_DEV", "/dev/watchdog"))
THERMAL_ZONE = Path("/sys/class/thermal/thermal_zone0/temp")

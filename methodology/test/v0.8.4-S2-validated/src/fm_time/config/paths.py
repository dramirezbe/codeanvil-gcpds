"""Filesystem paths for fm_time."""
import os
from pathlib import Path

_SOCKET_DIR = Path(os.environ.get("FM_SOCKET_DIR", "/run/fm"))

TIME_SOCK = _SOCKET_DIR / "time.sock"
CONFIG_SOCK = _SOCKET_DIR / "config.sock"
PROGRESS_SOCK = _SOCKET_DIR / "progress" / "time.sock"

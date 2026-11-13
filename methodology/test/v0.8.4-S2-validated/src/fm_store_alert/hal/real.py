"""Real HAL for fm_store_alert — receives scan records via Unix sockets."""
from __future__ import annotations

import socket
import time
from pathlib import Path
from typing import Optional

from fm_store_alert.config.logger import get_logger
from fm_store_alert.config.paths import SCAN_SOCK, CALV_SOCK
from fm_store_alert.hal.port import StoreDataPort
from fm_store_alert.lib.framing import recv_msg

log = get_logger(__name__)


class RealStoreDataPort(StoreDataPort):
    def __init__(self, scan_sock: Path = SCAN_SOCK, calv_sock: Path = CALV_SOCK) -> None:
        self._scan_sock_path = scan_sock
        self._calv_sock_path = calv_sock
        self._scan_conn: Optional[socket.socket] = None
        self._calv_conn: Optional[socket.socket] = None

    def _connect(self, path: Path) -> socket.socket:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        for _ in range(30):
            try:
                sock.connect(str(path))
                return sock
            except (FileNotFoundError, ConnectionRefusedError):
                time.sleep(1.0)
        raise ConnectionError(f"could not connect to {path}")

    def next_scan_record(self, timeout_s: float = 10.0) -> dict:
        if self._scan_conn is None:
            self._scan_conn = self._connect(self._scan_sock_path)
            self._scan_conn.settimeout(timeout_s)
        return recv_msg(self._scan_conn)

    def next_calv(self, timeout_s: float = 10.0) -> dict:
        if self._calv_conn is None:
            self._calv_conn = self._connect(self._calv_sock_path)
            self._calv_conn.settimeout(timeout_s)
        return recv_msg(self._calv_conn)

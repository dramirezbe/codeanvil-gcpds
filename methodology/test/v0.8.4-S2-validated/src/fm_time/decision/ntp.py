"""SUB-005/ntp — NTP client state machine; publishes time_status.v1 every 1 s.

State machine rules:
  unsynced  if offset > 50 ms, last_success > 3600 s, or still in startup window (120 s)
  synced    if offset <= 50 ms and last_success <= 3600 s
  stepped   if offset > 200 ms (clock step needed)
  leap      if NTP reports a leap second pending
"""
from __future__ import annotations

import socket
import time
from typing import Optional

from fm_time.config.logger import get_logger
from fm_time.config.paths import TIME_SOCK
from fm_time.hal.port import NtpPort, NtpSample
from fm_time.lib.framing import send_msg

log = get_logger(__name__)

_UNSYNCED_OFFSET_MS = 50.0
_STEPPED_OFFSET_MS = 200.0
_UNSYNCED_AGE_S = 3600.0
_STARTUP_WAIT_S = 120.0

# NTP poll interval: short at start, exponentially backed off once stable (RFC 5905)
_POLL_MIN_S = 16.0
_POLL_MAX_S = 1024.0


class NtpStateMachine:
    """Tracks offset, age and sync_state from NTP samples."""

    def __init__(self, startup_wait_s: float = _STARTUP_WAIT_S) -> None:
        self._startup_at = time.monotonic()
        self._startup_wait_s = startup_wait_s
        self._offset_ms: Optional[float] = None
        self._last_success: Optional[float] = None  # monotonic timestamp
        self._leap = 0
        self._poll_interval_s = _POLL_MIN_S
        self._consecutive_ok = 0

    def update(self, sample: NtpSample) -> None:
        if sample.offset_ms is None:
            self._consecutive_ok = 0
            self._poll_interval_s = _POLL_MIN_S
            return
        self._offset_ms = sample.offset_ms
        self._last_success = time.monotonic()
        self._leap = sample.leap
        self._consecutive_ok += 1
        # Back off poll interval once stable (3+ consecutive ok)
        if self._consecutive_ok >= 3:
            self._poll_interval_s = min(self._poll_interval_s * 2, _POLL_MAX_S)

    @property
    def sync_state(self) -> str:
        now = time.monotonic()
        in_startup = (now - self._startup_at) < self._startup_wait_s
        if self._offset_ms is None or self._last_success is None or in_startup:
            return "unsynced"
        age_s = now - self._last_success
        if age_s > _UNSYNCED_AGE_S:
            return "unsynced"
        abs_off = abs(self._offset_ms)
        if abs_off > _STEPPED_OFFSET_MS:
            return "stepped"
        if abs_off > _UNSYNCED_OFFSET_MS:
            return "unsynced"
        return "synced"

    @property
    def offset_ms(self) -> Optional[float]:
        return self._offset_ms

    @property
    def last_sync_age_s(self) -> Optional[float]:
        if self._last_success is None:
            return None
        return time.monotonic() - self._last_success

    @property
    def leap(self) -> int:
        return self._leap

    @property
    def poll_interval_s(self) -> float:
        return self._poll_interval_s


class TimePublisher:
    """Maintains the NTP state machine and publishes time_status.v1 over a Unix socket."""

    def __init__(
        self,
        ntp_port: NtpPort,
        servers: list[str],
        sock_path=TIME_SOCK,
        startup_wait_s: float = _STARTUP_WAIT_S,
    ) -> None:
        self._ntp = ntp_port
        self._servers = servers
        self._sock_path = sock_path
        self._state = NtpStateMachine(startup_wait_s=startup_wait_s)
        self._server_sock: Optional[socket.socket] = None
        self._clients: list[socket.socket] = []
        self._last_poll = 0.0

    def start_server(self) -> None:
        self._sock_path.parent.mkdir(parents=True, exist_ok=True)
        if self._sock_path.exists():
            self._sock_path.unlink()
        srv = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        srv.bind(str(self._sock_path))
        srv.listen(32)
        srv.setblocking(False)
        self._server_sock = srv
        log.info(f"time publisher on {self._sock_path}")

    def tick(self, utc_us: int) -> None:
        """Call once per second. Polls NTP as needed, publishes time_status."""
        now = time.monotonic()
        if (now - self._last_poll) >= self._state.poll_interval_s:
            for server in self._servers:
                sample = self._ntp.query(server)
                self._state.update(sample)
                if sample.offset_ms is not None:
                    break  # first responding server wins
            self._last_poll = now

        self._accept_clients()
        self._broadcast(self._make_msg(utc_us))

    def _make_msg(self, utc_us: int) -> dict:
        return {
            "schema_version": "1.0",
            "utc_us": utc_us,
            "resolution_us": 1000,  # ms-resolution from ntplib
            "sync_state": self._state.sync_state,
            "offset_est_ms": self._state.offset_ms,
            "last_sync_age_s": self._state.last_sync_age_s,
            "source_id": self._servers[0] if self._servers else "",
            "leap": self._state.leap,
        }

    def _accept_clients(self) -> None:
        if self._server_sock is None:
            return
        try:
            while True:
                c, _ = self._server_sock.accept()
                c.setblocking(False)
                self._clients.append(c)
        except BlockingIOError:
            pass

    def _broadcast(self, msg: dict) -> None:
        dead = []
        for c in self._clients:
            try:
                send_msg(c, msg)
            except Exception:
                dead.append(c)
        for c in dead:
            self._clients.remove(c)
            c.close()

    def close(self) -> None:
        for c in self._clients:
            c.close()
        self._clients.clear()
        if self._server_sock:
            self._server_sock.close()

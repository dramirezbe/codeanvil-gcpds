"""SUB-006/processes — Start, watch, restart and stop the five subsystem units.

Restart ladder: 5, 10, 20, 40, 60 s (capped). Progress counter stuck for >10 s triggers restart.
Loop detection: 3 restarts within 60 s = loop; thermal condition halts restart.
"""
from __future__ import annotations

import os
import signal
import socket
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from fm_supervisor.config.logger import get_logger
from fm_supervisor.lib.framing import send_msg

log = get_logger(__name__)

_STUCK_TIMEOUT_S = 10.0
_LADDER = [5, 10, 20, 40, 60]
_LOOP_WINDOW_S = 60.0
_LOOP_THRESHOLD = 3


@dataclass
class UnitState:
    name: str
    command: list[str]
    proc: Optional[subprocess.Popen] = None
    last_progress: float = field(default_factory=time.monotonic)
    restart_count: int = 0
    restart_times: list[float] = field(default_factory=list)
    loop_detected: bool = False
    next_restart_at: float = 0.0
    env: dict = field(default_factory=dict)


class ProcessManager:
    """Starts and supervises all five subsystem units."""

    _UNITS: list[tuple[str, list[str]]] = [
        ("fm_time", ["uv", "run", "fm_time"]),
        ("fm_measure", ["uv", "run", "fm_measure"]),
        ("fm_store_alert", ["uv", "run", "fm_store_alert"]),
        ("fm_report", ["uv", "run", "fm_report"]),
        ("fm_web", ["uv", "run", "fm_web"]),  # ts via tsx in a later iteration
    ]

    def __init__(self, supervisor_env: Optional[dict] = None) -> None:
        env = dict(os.environ)
        if supervisor_env:
            env.update(supervisor_env)
        self._units: list[UnitState] = [
            UnitState(name=name, command=cmd, env=env)
            for name, cmd in self._UNITS
        ]
        self._running = True

    def start_all(self) -> None:
        for unit in self._units:
            self._start_unit(unit)

    def _start_unit(self, unit: UnitState) -> None:
        if unit.loop_detected:
            log.error(f"loop detected on {unit.name}; will not restart")
            return
        try:
            unit.proc = subprocess.Popen(
                unit.command,
                env=unit.env,
                start_new_session=True,
            )
            unit.last_progress = time.monotonic()
            log.info(f"started {unit.name} pid={unit.proc.pid}")
        except FileNotFoundError as exc:
            log.warning(f"could not start {unit.name}: {exc}")

    def tick(self, thermal_condition: bool = False) -> None:
        """Check unit health; restart stuck or dead units."""
        now = time.monotonic()
        for unit in self._units:
            if unit.loop_detected:
                continue
            proc = unit.proc
            if proc is None:
                if now >= unit.next_restart_at:
                    self._start_unit(unit)
                continue
            rc = proc.poll()
            if rc is not None:
                log.warning(f"{unit.name} exited with rc={rc}")
                unit.proc = None
                self._schedule_restart(unit, now, thermal_condition)
                continue
            # Check stuck
            if (now - unit.last_progress) > _STUCK_TIMEOUT_S:
                log.warning(f"{unit.name} stuck for {now - unit.last_progress:.1f} s; killing")
                try:
                    proc.send_signal(signal.SIGTERM)
                except ProcessLookupError:
                    pass
                unit.proc = None
                self._schedule_restart(unit, now, thermal_condition)

    def _schedule_restart(self, unit: UnitState, now: float, thermal_condition: bool) -> None:
        # Prune old restart times
        unit.restart_times = [t for t in unit.restart_times if now - t < _LOOP_WINDOW_S]
        unit.restart_times.append(now)
        unit.restart_count += 1

        if len(unit.restart_times) >= _LOOP_THRESHOLD:
            unit.loop_detected = True
            log.error(f"loop detected on {unit.name} ({_LOOP_THRESHOLD} restarts in {_LOOP_WINDOW_S} s)")
            return

        if thermal_condition:
            delay = _LADDER[-1]
            log.warning(f"thermal condition active; delaying {unit.name} restart by {delay} s")
        else:
            idx = min(unit.restart_count - 1, len(_LADDER) - 1)
            delay = _LADDER[idx]

        unit.next_restart_at = now + delay
        log.info(f"scheduling {unit.name} restart in {delay} s (attempt {unit.restart_count})")

    def update_progress(self, unit_name: str) -> None:
        """Call when a progress.v1 message arrives from a unit."""
        for unit in self._units:
            if unit.name == unit_name:
                unit.last_progress = time.monotonic()
                return

    def stop_all(self, timeout_s: float = 5.0) -> None:
        """Send SIGTERM to all units; wait up to timeout_s each."""
        for unit in self._units:
            if unit.proc is not None:
                try:
                    unit.proc.send_signal(signal.SIGTERM)
                except ProcessLookupError:
                    pass
        deadline = time.monotonic() + timeout_s
        for unit in self._units:
            if unit.proc is not None:
                remaining = max(0.0, deadline - time.monotonic())
                try:
                    unit.proc.wait(timeout=remaining)
                except subprocess.TimeoutExpired:
                    unit.proc.kill()
        log.info("all units stopped")

    def status(self) -> list[dict]:
        return [
            {
                "name": u.name,
                "pid": u.proc.pid if u.proc else None,
                "running": u.proc is not None and u.proc.poll() is None,
                "restart_count": u.restart_count,
                "loop_detected": u.loop_detected,
            }
            for u in self._units
        ]

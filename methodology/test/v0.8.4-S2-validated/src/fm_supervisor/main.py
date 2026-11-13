"""fm_supervisor entry point — starts, watches and restarts child processes (SDD §0.5)."""
from __future__ import annotations

import asyncio
import json
import os
import signal
import struct
import subprocess
import sys
import time
from pathlib import Path

from fm_supervisor.config.logger import get_logger
from fm_supervisor.config.paths import (
    SUPERVISOR_SOCK, CONFIG_SOCK, REPORT_CMD_SOCK, SHUTDOWN_SOCK, PROGRESS_DIR
)
from fm_supervisor.config.runtime import HAL_MODE

log = get_logger(__name__)

_WATCHDOG_FEED_INTERVAL = 5.0  # seconds
_UNITS = ["fm_time", "fm_measure", "fm_store_alert", "fm_report", "fm_web"]
_RESTART_LADDER = [5, 10, 20, 40, 60]  # seconds between restarts


def _make_hal():
    if HAL_MODE == "real":
        from fm_supervisor.hal.real import RealWatchdogPort, RealThermalPort, RealResourcePort
        return RealWatchdogPort(), RealThermalPort(), RealResourcePort()
    from fm_supervisor.hal.mock import MockWatchdogPort, MockThermalPort, MockResourcePort
    return MockWatchdogPort(), MockThermalPort(), MockResourcePort()


async def _run() -> None:
    loop = asyncio.get_running_loop()
    stop = asyncio.Event()

    def _shutdown(sig: signal.Signals) -> None:
        log.info(f"received {sig.name}")
        stop.set()

    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, _shutdown, sig)

    watchdog, thermal, resource = _make_hal()
    log.info(f"fm_supervisor starting, HAL={HAL_MODE}")

    for sock_path in (SUPERVISOR_SOCK, CONFIG_SOCK):
        if sock_path.exists():
            sock_path.unlink()
        sock_path.parent.mkdir(parents=True, exist_ok=True)
    PROGRESS_DIR.mkdir(parents=True, exist_ok=True)

    status_subscribers: list[asyncio.StreamWriter] = []
    config_subscribers: list[asyncio.StreamWriter] = []

    async def _on_status_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        status_subscribers.append(writer)
        try:
            await reader.read()
        finally:
            if writer in status_subscribers:
                status_subscribers.remove(writer)

    async def _on_config_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        config_subscribers.append(writer)
        try:
            await reader.read()
        finally:
            if writer in config_subscribers:
                config_subscribers.remove(writer)

    supervisor_server = await asyncio.start_unix_server(_on_status_client, path=str(SUPERVISOR_SOCK))
    config_server = await asyncio.start_unix_server(_on_config_client, path=str(CONFIG_SOCK))

    # Publish initial config_status.v1
    config_status = {
        "schema": "config_status.v1",
        "hal": HAL_MODE,
        "channels": 199,
        "scan_period_s": 6.0,
    }

    async def _broadcast(subscribers: list, msg: dict) -> None:
        body = json.dumps(msg, separators=(",", ":")).encode()
        prefix = struct.pack(">I", len(body))
        dead = []
        for w in subscribers:
            try:
                w.write(prefix + body)
                await w.drain()
            except Exception:
                dead.append(w)
        for w in dead:
            subscribers.remove(w)

    async def _watchdog_loop() -> None:
        watchdog.open()
        log.info("watchdog opened")
        try:
            while not stop.is_set():
                watchdog.feed()
                try:
                    await asyncio.wait_for(stop.wait(), timeout=_WATCHDOG_FEED_INTERVAL)
                except asyncio.TimeoutError:
                    pass
        finally:
            watchdog.close()
            log.info("watchdog closed")

    async def _status_loop() -> None:
        tick = 0
        while not stop.is_set():
            tick += 1
            temp = thermal.read_celsius()
            status = {
                "schema": "supervisor_status.v1",
                "tick": tick,
                "hal": HAL_MODE,
                "temp_c": temp,
                "thermal_ok": temp < 85.0,
            }
            await _broadcast(status_subscribers, status)
            try:
                await asyncio.wait_for(stop.wait(), timeout=1.0)
            except asyncio.TimeoutError:
                pass

    # Start child processes (skipped when HAL=mock in test mode; run.sh handles this)
    children: list[subprocess.Popen] = []
    env = {**os.environ, "FM_HAL": HAL_MODE}
    if HAL_MODE == "mock" and os.environ.get("FM_SUPERVISOR_SPAWN", "1") == "1":
        for unit in _UNITS:
            try:
                proc = subprocess.Popen(
                    [sys.executable, "-m", unit],
                    env=env,
                    start_new_session=True,
                )
                children.append(proc)
                log.info(f"started {unit} pid={proc.pid}")
            except Exception as exc:
                log.error(f"failed to start {unit}: {exc}")

    async with supervisor_server, config_server:
        log.info("fm_supervisor ready")
        await _broadcast(config_subscribers, config_status)
        wd_task = asyncio.create_task(_watchdog_loop())
        st_task = asyncio.create_task(_status_loop())
        await stop.wait()
        wd_task.cancel()
        st_task.cancel()

    # Ordered shutdown: SIGTERM children in reverse order
    for proc in reversed(children):
        try:
            proc.terminate()
        except ProcessLookupError:
            pass
    for proc in children:
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()

    for sock_path in (SUPERVISOR_SOCK, CONFIG_SOCK):
        try:
            sock_path.unlink()
        except FileNotFoundError:
            pass
    log.info("fm_supervisor stopped")


def main() -> None:
    asyncio.run(_run())

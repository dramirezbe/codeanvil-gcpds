"""fm_measure entry point — scan loop with mock or real HAL (SDD §0.5)."""
from __future__ import annotations

import asyncio
import os
import signal
import socket as _socket
import struct
import json
from pathlib import Path

from fm_measure.config.logger import get_logger
from fm_measure.config.paths import SCAN_SOCK, CALV_SOCK, PROGRESS_SOCK, TIME_SOCK, CONFIG_SOCK
from fm_measure.config.runtime import HAL_MODE

log = get_logger(__name__)

_CHANNELS = 199
_STEPS = 3
_FRAMES_PER_STEP = 39


def _make_hal():
    if HAL_MODE == "real":
        from fm_measure.hal.real import RealSdrPort
        return RealSdrPort()
    from fm_measure.hal.mock import MockSdrPort
    return MockSdrPort()


async def _send_progress(sock_path: Path, counter: int) -> None:
    try:
        sock_path.parent.mkdir(parents=True, exist_ok=True)
        reader, writer = await asyncio.open_unix_connection(str(sock_path))
        body = json.dumps({"subsystem": "measure", "counter": counter}, separators=(",", ":")).encode()
        writer.write(struct.pack(">I", len(body)) + body)
        await writer.drain()
        writer.close()
        await writer.wait_closed()
    except Exception:
        pass


async def _scan_loop(hal, stop: asyncio.Event) -> None:
    from fm_measure.hal.port import SdrConfig

    # Three FM sub-band steps: 88.1–96.1, 96.1–104.1, 104.1–107.9 (approximated as 3×8 MHz)
    step_centres = [92_100_000, 100_100_000, 106_000_000]
    scan_count = 0

    # Set up scan.sock server (push scan_records.v1 to subscribers)
    scan_clients: list[asyncio.StreamWriter] = []

    if SCAN_SOCK.exists():
        SCAN_SOCK.unlink()
    SCAN_SOCK.parent.mkdir(parents=True, exist_ok=True)

    async def _on_scan_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        scan_clients.append(writer)
        try:
            await reader.read()
        finally:
            scan_clients.remove(writer)

    scan_server = await asyncio.start_unix_server(_on_scan_client, path=str(SCAN_SOCK))

    hal.open()
    info = hal.info()
    log.info(f"fm_measure started, HAL={HAL_MODE}, device={info}")

    try:
        async with scan_server:
            while not stop.is_set():
                scan_start = asyncio.get_event_loop().time()
                iq_blocks = []
                for centre in step_centres:
                    cfg = SdrConfig(
                        center_hz=float(centre),
                        sample_rate_hz=10_000_000.0,
                        lna_gain_db=16,
                        rf_gain_db=0,
                        bb_gain_db=20,
                    )
                    hal.configure(cfg)
                    frames = hal.read_frames(_FRAMES_PER_STEP, timeout_s=4.0)
                    iq_blocks.append((centre, frames))

                # Placeholder scan record (business logic filled in step 3)
                scan_record = {
                    "schema": "scan_records.v1",
                    "scan_index": scan_count,
                    "steps": [{"centre_hz": c, "frames": len(f)} for c, f in iq_blocks],
                    "late": (asyncio.get_event_loop().time() - scan_start) > 7.0,
                }
                body = json.dumps(scan_record, separators=(",", ":")).encode()
                prefix = struct.pack(">I", len(body))
                dead = []
                for w in scan_clients:
                    try:
                        w.write(prefix + body)
                        await w.drain()
                    except Exception:
                        dead.append(w)
                for w in dead:
                    scan_clients.remove(w)

                scan_count += 1
                await _send_progress(PROGRESS_SOCK, scan_count)

                elapsed = asyncio.get_event_loop().time() - scan_start
                sleep = max(0.0, 6.0 - elapsed)
                try:
                    await asyncio.wait_for(stop.wait(), timeout=sleep)
                except asyncio.TimeoutError:
                    pass
    finally:
        hal.close()
        for w in scan_clients:
            w.close()
        for path in (SCAN_SOCK, CALV_SOCK):
            try:
                path.unlink()
            except FileNotFoundError:
                pass
        log.info("fm_measure stopped")


async def _run() -> None:
    hal = _make_hal()
    loop = asyncio.get_running_loop()
    stop = asyncio.Event()

    def _shutdown(sig: signal.Signals) -> None:
        log.info(f"received {sig.name}")
        stop.set()

    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, _shutdown, sig)

    await _scan_loop(hal, stop)


def main() -> None:
    asyncio.run(_run())

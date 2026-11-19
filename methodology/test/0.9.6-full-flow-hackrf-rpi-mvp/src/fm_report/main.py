"""fm_report entry point — screening report writer (SDD §0.5)."""
from __future__ import annotations

import asyncio
import json
import os
import signal
import struct
from pathlib import Path

from fm_report.config.logger import get_logger
from fm_report.config.paths import SCAN_SOCK, CATALOG_SOCK, REPORT_CMD_SOCK, PROGRESS_SOCK, REPORT_DIR
from fm_report.config.runtime import HAL_MODE

log = get_logger(__name__)


async def _connect_with_retry(path: Path, retries: int = 30, delay: float = 1.0):
    for _ in range(retries):
        try:
            return await asyncio.open_unix_connection(str(path))
        except (FileNotFoundError, ConnectionRefusedError):
            await asyncio.sleep(delay)
    raise ConnectionError(f"cannot connect to {path}")


async def _run() -> None:
    loop = asyncio.get_running_loop()
    stop = asyncio.Event()

    def _shutdown(sig: signal.Signals) -> None:
        log.info(f"received {sig.name}")
        stop.set()

    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, _shutdown, sig)

    log.info(f"fm_report starting, HAL={HAL_MODE}")
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    catalog_clients: list[asyncio.StreamWriter] = []

    for sock_path in (CATALOG_SOCK, REPORT_CMD_SOCK):
        if sock_path.exists():
            sock_path.unlink()
        sock_path.parent.mkdir(parents=True, exist_ok=True)

    async def _on_catalog_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        catalog_clients.append(writer)
        try:
            await reader.read()
        finally:
            if writer in catalog_clients:
                catalog_clients.remove(writer)

    async def _on_report_cmd(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        try:
            hdr = await reader.readexactly(4)
            (length,) = struct.unpack(">I", hdr)
            data = await reader.readexactly(length)
            cmd = json.loads(data)
            log.info(f"report_command: {cmd}")
        except Exception as exc:
            log.error(f"report_cmd error: {exc}")
        finally:
            writer.close()

    catalog_server = await asyncio.start_unix_server(_on_catalog_client, path=str(CATALOG_SOCK))
    cmd_server = await asyncio.start_unix_server(_on_report_cmd, path=str(REPORT_CMD_SOCK))

    async def _consume_scans() -> None:
        scan_count = 0
        while not stop.is_set():
            try:
                reader, _ = await _connect_with_retry(SCAN_SOCK)
                log.info("fm_report connected to scan.sock")
                while not stop.is_set():
                    hdr = await reader.readexactly(4)
                    (length,) = struct.unpack(">I", hdr)
                    data = await reader.readexactly(length)
                    record = json.loads(data)
                    scan_count += 1
                    # Placeholder: write report line (business logic in step 3)
            except (EOFError, ConnectionError, FileNotFoundError):
                if not stop.is_set():
                    await asyncio.sleep(2.0)
            except Exception as exc:
                log.error(f"scan consumer error: {exc}")
                if not stop.is_set():
                    await asyncio.sleep(2.0)

    async with catalog_server, cmd_server:
        log.info("fm_report ready")
        consume_task = asyncio.create_task(_consume_scans())
        await stop.wait()
        consume_task.cancel()

    for sock_path in (CATALOG_SOCK, REPORT_CMD_SOCK):
        try:
            sock_path.unlink()
        except FileNotFoundError:
            pass
    log.info("fm_report stopped")


def main() -> None:
    asyncio.run(_run())

"""The installed service entry point starts without importing the test kit."""

from __future__ import annotations

import asyncio
import json
import socket
import subprocess
import sys

import pytest
from websockets.asyncio.client import connect


@pytest.mark.vl0
@pytest.mark.asyncio
async def test_package_entrypoint_streams_a_websocket_update() -> None:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]

    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "fm_edge",
            "--scene",
            "SC-2",
            "--updates",
            "30",
            "--period",
            "0.1",
            "--port",
            str(port),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        for _ in range(60):
            if process.poll() is not None:
                raise AssertionError(f"fm_edge exited early: {process.stderr.read()}")
            try:
                async with connect(f"ws://127.0.0.1:{port}") as client:
                    message = json.loads(await asyncio.wait_for(client.recv(), 5))
                    assert message["v"] == 1
                    assert message["fc_hz"] == 98_000_000
                    assert len(message["spectrum_dbfs"]) == 853
                    assert len(message["channels"]) == 10
                    return
            except OSError:
                await asyncio.sleep(0.05)
        raise AssertionError("fm_edge did not open its WebSocket port")
    finally:
        process.terminate()
        process.wait(timeout=5)

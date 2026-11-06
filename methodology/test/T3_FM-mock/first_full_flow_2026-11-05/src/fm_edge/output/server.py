import asyncio
import json
from typing import Any

import websockets
from websockets.asyncio.server import Server, ServerConnection

from fm_edge.config.logger import get_logger
from fm_edge.dsp.spectrum import SpectrumResult
from fm_edge.dsp.channels import ChannelResult

log = get_logger(__name__)


def format_message(
    spectrum: SpectrumResult,
    channels: ChannelResult,
    t_capture_end: str,
) -> str:
    payload: dict[str, Any] = {
        "v": 1,
        "t_capture_end": t_capture_end,
        "fc_hz": spectrum.fc_hz,
        "bin_hz": spectrum.bin_hz,
        "spectrum_dbfs": [round(float(x), 1) for x in spectrum.bins_dbfs],
        "floor_dbfs": round(spectrum.floor_dbfs, 1),
        "channels": [
            {
                "f_mhz": ch.f_mhz,
                "power_dbfs": ch.power_dbfs,
                "occupied": ch.occupied,
                "occupancy": ch.occupancy,
            }
            for ch in channels.channels
        ],
    }
    return json.dumps(payload, separators=(",", ":"))


class UpdateServer:

    def __init__(self, port: int = 8765) -> None:
        self._port = port
        self._clients: set[ServerConnection] = set()
        self._server: Server | None = None

    async def _handler(self, ws: ServerConnection) -> None:
        self._clients.add(ws)
        log.info("client connected (%d total)", len(self._clients))
        try:
            async for _ in ws:
                pass
        finally:
            self._clients.discard(ws)
            log.info("client disconnected (%d remaining)", len(self._clients))

    async def start(self) -> None:
        self._server = await websockets.serve(self._handler, "0.0.0.0", self._port)
        log.info("WebSocket server listening on port %d", self._port)

    async def broadcast(self, message: str) -> None:
        if not self._clients:
            return
        await asyncio.gather(
            *(client.send(message) for client in self._clients),
            return_exceptions=True,
        )

    async def stop(self) -> None:
        if self._server is not None:
            self._server.close()
            await self._server.wait_closed()
            log.info("WebSocket server stopped")

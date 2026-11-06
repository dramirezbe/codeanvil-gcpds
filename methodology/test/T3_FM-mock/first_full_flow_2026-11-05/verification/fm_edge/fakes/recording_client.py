"""Fake SVC-002: records the messages SVC-001 broadcasts over WebSocket."""

from __future__ import annotations

import asyncio
import json

import websockets


class RecordingClient:
    """Connect to a WebSocket server and record every message as JSON."""

    def __init__(self, url: str = "ws://127.0.0.1:8765") -> None:
        self.url = url
        self.messages: list[dict] = []
        self._task: asyncio.Task | None = None

    async def _run(self) -> None:
        async with websockets.connect(self.url) as ws:
            async for raw in ws:
                self.messages.append(json.loads(raw))

    async def start(self) -> None:
        self._task = asyncio.create_task(self._run())
        # Give the client a moment to connect.
        await asyncio.sleep(0.1)

    async def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except (asyncio.CancelledError, Exception):
                pass
            self._task = None

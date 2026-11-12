"""Local CLI terminals: allowlisted launchers, explicit modes and same-origin IO."""

import asyncio
from contextlib import ExitStack
import json
from pathlib import Path
import sys
from urllib.parse import urlsplit

from fastapi import APIRouter, HTTPException, Request, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, ConfigDict, Field, StrictBool

from codeanvil.sandbox import SANDBOX_AGENTS, SandboxError, prepare_sandbox
from codeanvil.UI import launchers
from codeanvil.UI.project_context import project_context
from codeanvil.UI.terminal_process import PtyError
from codeanvil.UI.terminal_sessions import MAX_SESSIONS, SessionManager


class StartTerminal(BaseModel):
    model_config = ConfigDict(extra="forbid")
    project_path: str
    launcher_id: str
    sandbox: StrictBool = False
    cols: int = Field(default=100, ge=2, le=500, strict=True)
    rows: int = Field(default=30, ge=2, le=200, strict=True)


def same_origin(headers):
    """WebSocket routes bypass HTTP middleware, so validate both here."""
    try:
        origin = urlsplit(headers.get("origin", ""))
        host = urlsplit("//" + headers.get("host", ""))
        return (
            origin.scheme in {"http", "https"}
            and host.hostname in {"localhost", "127.0.0.1", "::1"}
            and origin.hostname == host.hostname
            and (origin.port or (443 if origin.scheme == "https" else 80)) == (host.port or 80)
            and not origin.username and not origin.password
        )
    except ValueError:
        return False


def create_terminal_router(root: Path, manager: SessionManager):
    router = APIRouter(prefix="/api/terminal")

    def project(path: str):
        selected = Path(path).expanduser()
        try:
            context = project_context(selected if selected.is_absolute() else root / selected)
        except (ValueError, OSError) as exc:
            raise HTTPException(400, str(exc)) from exc
        if context is None:
            raise HTTPException(404, "Not a CodeAnvil project")
        return context[0]

    def get_session(identifier):
        session = manager.sessions.get(identifier)
        if session is None:
            raise HTTPException(404, "Terminal session not found")
        return session

    @router.get("/launchers")
    async def list_launchers():
        items = [dict(item, sandbox_supported=item["id"] in SANDBOX_AGENTS)
                 for item in launchers.scan() if item["kind"] == "terminal"]
        return {"supported": sys.platform.startswith("linux"), "platform": sys.platform, "launchers": items}

    @router.get("/sessions")
    async def list_sessions(project_path: str | None = None):
        selected = str(project(project_path)) if project_path else None
        return {"sessions": [item.summary() for item in manager.sessions.values()
                             if selected is None or item.project_path == selected]}

    @router.post("/sessions")
    async def start_session(body: StartTerminal, request: Request):
        if not same_origin(request.headers):
            raise HTTPException(403, "A same-origin browser request is required")
        if not sys.platform.startswith("linux"):
            raise HTTPException(501, "Interactive terminals currently require Linux or WSL")
        selected = project(body.project_path)
        candidates = {item["id"]: item for item in launchers.scan() if item["kind"] == "terminal"}
        launcher = candidates.get(body.launcher_id)
        if launcher is None:
            raise HTTPException(400, "Choose a configured terminal CLI")
        if not launcher["available"] or not launcher["installed"]:
            raise HTTPException(409, "This CLI is not installed or available on this platform")
        if body.sandbox and body.launcher_id not in SANDBOX_AGENTS:
            raise HTTPException(400, "Sandbox mode is not configured for this CLI")
        async with manager.lock:
            running = [item for item in manager.sessions.values() if item.state == "running"]
            if any(item.project_path == str(selected) for item in running):
                raise HTTPException(409, "This project already has an active terminal")
            if len(running) >= MAX_SESSIONS:
                raise HTTPException(409, "Stop an existing terminal before opening another")
            resources = ExitStack()
            try:
                if body.sandbox:
                    launch = resources.enter_context(prepare_sandbox(body.launcher_id, selected))
                else:
                    launch = launchers.launch(body.launcher_id, selected)
                session = await manager.start(selected, body.launcher_id, body.sandbox,
                                              launch, resources, body.cols, body.rows)
            except (SandboxError, PtyError, ValueError, OSError) as exc:
                resources.close()
                raise HTTPException(400, str(exc)) from exc
            manager.prune()
            return session.summary()

    @router.post("/sessions/{identifier}/stop")
    async def stop_session(identifier: str, request: Request):
        if not same_origin(request.headers):
            raise HTTPException(403, "A same-origin browser request is required")
        session = get_session(identifier)
        await session.stop()
        return session.summary()

    @router.websocket("/sessions/{identifier}/stream")
    async def stream(identifier: str, websocket: WebSocket):
        session = manager.sessions.get(identifier)
        if not same_origin(websocket.headers) or session is None:
            await websocket.close(code=1008)
            return
        await websocket.accept()
        queue = asyncio.Queue(maxsize=64)
        session.clients.add(queue)
        # No await between registration and replay snapshot: output is not lost.
        replay = bytes(session.replay)
        try:
            await websocket.send_json({"type": "ready", "session": session.summary()})
            if replay:
                await websocket.send_bytes(replay)
            if session.state == "exited":
                await websocket.send_json({"type": "exit", "code": session.exit_code})

            async def send():
                while True:
                    message = await queue.get()
                    if isinstance(message, bytes):
                        await websocket.send_bytes(message)
                    elif message["type"] == "overflow":
                        await websocket.close(code=1013, reason="Reconnect to recover terminal output")
                        return
                    else:
                        await websocket.send_json(message)

            async def receive():
                while True:
                    frame = await websocket.receive()
                    if frame["type"] == "websocket.disconnect":
                        return
                    try:
                        raw = frame.get("text")
                        if not isinstance(raw, str):
                            raise ValueError("Expected a text terminal message")
                        if len(raw) > 65536:
                            raise ValueError("Input is too large")
                        message = json.loads(raw)
                        if not isinstance(message, dict):
                            raise ValueError("Expected a terminal message")
                        if message.get("type") == "input" and isinstance(message.get("data"), str):
                            await asyncio.to_thread(session.process.write, message["data"].encode("utf-8"))
                        elif message.get("type") == "resize":
                            cols, rows = message.get("cols"), message.get("rows")
                            if type(cols) is not int or type(rows) is not int or not 2 <= cols <= 500 or not 2 <= rows <= 200:
                                raise ValueError("Invalid terminal size")
                            await asyncio.to_thread(session.process.resize, cols, rows)
                        else:
                            raise ValueError("Unknown terminal message")
                    except (ValueError, PtyError, UnicodeError) as exc:
                        await websocket.close(code=1008, reason=str(exc)[:100])
                        return

            tasks = [asyncio.create_task(send()), asyncio.create_task(receive())]
            try:
                await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
            finally:
                for task in tasks:
                    task.cancel()
                await asyncio.gather(*tasks, return_exceptions=True)
        except (WebSocketDisconnect, RuntimeError, asyncio.CancelledError):
            pass
        finally:
            session.clients.discard(queue)

    return router

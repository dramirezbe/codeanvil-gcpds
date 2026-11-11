"""In-memory local PTY sessions that survive browser navigation, not server exit."""

import asyncio
from contextlib import ExitStack
from dataclasses import dataclass, field
from pathlib import Path
from uuid import uuid4

from codeanvil.UI.terminal_process import PtyProcess


REPLAY_LIMIT = 1024 * 1024
MAX_SESSIONS = 8


@dataclass
class TerminalSession:
    project_path: str
    launcher_id: str
    sandbox: bool
    process: PtyProcess
    resources: ExitStack
    id: str = field(default_factory=lambda: uuid4().hex)
    state: str = "running"
    exit_code: int | None = None
    replay: bytearray = field(default_factory=bytearray)
    clients: set = field(default_factory=set)
    reader: asyncio.Task | None = None

    def summary(self):
        return {
            "id": self.id, "pid": self.process.pid,
            "project_path": self.project_path, "launcher_id": self.launcher_id,
            "sandbox": self.sandbox, "state": self.state,
            "exit_code": self.exit_code, "clients": len(self.clients),
        }

    def publish(self, message):
        # A slow browser cannot retain unlimited terminal output in RAM.
        for queue in tuple(self.clients):
            if queue.full():
                self.clients.remove(queue)
                while not queue.empty():
                    queue.get_nowait()
                queue.put_nowait({"type": "overflow"})
            else:
                queue.put_nowait(message)

    def finish(self, code):
        self.exit_code = code
        try:
            self.resources.close()
        except Exception:
            self.publish({"type": "error", "message": "Terminal sandbox cleanup failed."})
        finally:
            self.state = "exited"
            self.publish({"type": "exit", "code": self.exit_code})

    async def consume(self):
        try:
            while chunk := await asyncio.to_thread(self.process.read):
                self.replay.extend(chunk)
                if len(self.replay) > REPLAY_LIMIT:
                    del self.replay[:-REPLAY_LIMIT]
                self.publish(chunk)
        except Exception:
            self.publish({"type": "error", "message": "The local terminal stream failed."})
        finally:
            # Stop also reaps descendants after the CLI closes its terminal.
            try:
                code = await asyncio.to_thread(self.process.stop)
            except Exception:
                code = self.process.poll()
                self.publish({"type": "error", "message": "The local terminal could not be stopped."})
            # Keep isolation resources available if stopping genuinely failed
            # and the process is still alive. A subsequent stop can retry.
            if code is not None:
                self.finish(code)

    async def stop(self):
        if self.state == "running":
            code = await asyncio.to_thread(self.process.stop)
            if self.reader:
                await self.reader
            if self.state == "running":
                self.finish(code)


class SessionManager:
    """One active CLI per project; all resources belong to this app instance."""

    def __init__(self):
        self.sessions: dict[str, TerminalSession] = {}
        self.lock = asyncio.Lock()

    async def start(self, project: Path, launcher_id: str, sandbox: bool,
                    launch, resources: ExitStack, cols: int, rows: int):
        # The router holds lock across recipe preparation and this operation.
        pending = asyncio.create_task(asyncio.to_thread(
            PtyProcess.start, launch["argv"], project, launch.get("env"), cols, rows,
        ))
        try:
            # Cancellation must not abandon a Popen still starting in a worker.
            process = await asyncio.shield(pending)
        except asyncio.CancelledError:
            try:
                try:
                    process = await pending
                except Exception:
                    process = None
                if process is not None:
                    await asyncio.to_thread(process.stop)
            finally:
                resources.close()
            raise
        session = TerminalSession(str(project), launcher_id, sandbox, process, resources)
        self.sessions[session.id] = session
        session.reader = asyncio.create_task(session.consume())
        return session

    async def close(self):
        sessions = list(self.sessions.items())
        results = await asyncio.gather(*(session.stop() for _, session in sessions), return_exceptions=True)
        for (identifier, _), result in zip(sessions, results):
            if not isinstance(result, BaseException):
                self.sessions.pop(identifier, None)
        # Finish every cleanup before surfacing a failure. Keep failed sessions
        # available for a retry instead of losing their process/resource owner.
        for result in results:
            if isinstance(result, BaseException):
                raise result

    def prune(self):
        # Retain at most one completed replay per project and a bounded history.
        completed = [item for item in self.sessions.values() if item.state == "exited"]
        retained_projects = set()
        retained = 0
        for session in reversed(completed):
            if not session.clients and (session.project_path in retained_projects or retained >= MAX_SESSIONS):
                del self.sessions[session.id]
            else:
                retained_projects.add(session.project_path)
                retained += 1

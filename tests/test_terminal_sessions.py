"""Session ownership, cancellation and bounded replay without starting an agent."""

import asyncio
from contextlib import ExitStack
import threading

import pytest

from codeanvil.UI.terminal_sessions import REPLAY_LIMIT, SessionManager, TerminalSession


class FixtureProcess:
    pid = 123456789

    def __init__(self, chunks=(), stop_error=None):
        self.chunks = iter(chunks)
        self.stops = 0
        self.stop_error = stop_error

    def read(self):
        return next(self.chunks, b"")

    def stop(self):
        self.stops += 1
        if self.stop_error:
            raise self.stop_error
        return 0

    def poll(self):
        return 0


def test_cancelled_start_reaps_late_process_and_closes_sandbox(tmp_path, monkeypatch):
    entered = threading.Event()
    release = threading.Event()
    process = FixtureProcess()
    closed = []
    resources = ExitStack()
    resources.callback(lambda: closed.append(True))

    def spawn(*args):
        entered.set()
        assert release.wait(5)
        return process

    monkeypatch.setattr("codeanvil.UI.terminal_sessions.PtyProcess.start", spawn)

    async def exercise():
        manager = SessionManager()
        task = asyncio.create_task(manager.start(tmp_path, "fixture", True,
                                                {"argv": ["fixture"]}, resources, 100, 30))
        assert await asyncio.to_thread(entered.wait, 5)
        task.cancel()
        release.set()
        with pytest.raises(asyncio.CancelledError):
            await task
        await asyncio.sleep(0.02)
        assert process.stops == 1
        assert closed == [True]
        assert manager.sessions == {}

    asyncio.run(exercise())


def test_stream_cleanup_closes_sandbox_even_when_stop_fails(tmp_path):
    closed = []
    resources = ExitStack()
    resources.callback(lambda: closed.append(True))
    session = TerminalSession(str(tmp_path), "fixture", True,
                              FixtureProcess(stop_error=OSError("fixture stop failed")), resources)

    async def exercise():
        queue = asyncio.Queue()
        session.clients.add(queue)
        await session.consume()
        messages = []
        while not queue.empty():
            messages.append(queue.get_nowait())
        assert any(isinstance(item, dict) and item["type"] == "error" for item in messages)

    asyncio.run(exercise())
    assert closed == [True]
    assert session.state == "exited"


def test_failed_stop_retains_live_sandbox_until_retry(tmp_path):
    process = FixtureProcess(stop_error=OSError("not stopped"))
    process.poll = lambda: None
    closed = []
    resources = ExitStack()
    resources.callback(lambda: closed.append(True))
    session = TerminalSession(str(tmp_path), "fixture", True, process, resources)

    async def exercise():
        await session.consume()
        assert closed == []
        assert session.state == "running"
        process.stop_error = None
        await session.stop()

    asyncio.run(exercise())
    assert closed == [True]
    assert session.state == "exited"


def test_shutdown_waits_for_other_sessions_when_one_stop_fails():
    completed = []

    class BrokenSession:
        async def stop(self):
            raise OSError("cannot stop fixture")

    class SlowSession:
        async def stop(self):
            await asyncio.sleep(0.02)
            completed.append(True)

    async def exercise():
        manager = SessionManager()
        manager.sessions = {"broken": BrokenSession(), "slow": SlowSession()}
        with pytest.raises(OSError):
            await manager.close()
        assert completed == [True]

    asyncio.run(exercise())


def test_replay_and_slow_client_queues_are_bounded(tmp_path):
    resources = ExitStack()
    chunks = [b"a" * 65536] * 70 + [b"tail"]
    session = TerminalSession(str(tmp_path), "fixture", False, FixtureProcess(chunks), resources)

    async def exercise():
        slow = asyncio.Queue(maxsize=3)
        session.clients.add(slow)
        await session.consume()
        assert len(session.replay) == REPLAY_LIMIT
        assert session.replay.endswith(b"tail")
        assert slow not in session.clients
        assert slow.qsize() == 1
        assert slow.get_nowait() == {"type": "overflow"}

    asyncio.run(exercise())


def test_completed_history_keeps_only_last_replay_per_project(tmp_path):
    manager = SessionManager()
    for _ in range(3):
        session = TerminalSession(str(tmp_path), "fixture", False, FixtureProcess(), ExitStack(), state="exited")
        manager.sessions[session.id] = session
    manager.prune()
    assert list(manager.sessions.values()) == [session]

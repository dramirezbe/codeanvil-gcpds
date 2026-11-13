"""Exercise local Linux PTYs with disposable Python processes, never an agent CLI."""

import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import threading
import time

import pytest

from codeanvil.UI.terminal_process import PtyError, PtyProcess


pytestmark = pytest.mark.skipif(not sys.platform.startswith("linux"), reason="Linux/WSL PTY")


class Capture:
    """Drain asynchronously so every assertion has a bounded timeout."""

    def __init__(self, process):
        self.data = bytearray()
        self.condition = threading.Condition()
        self.done = False
        self.error = None
        self.thread = threading.Thread(target=self._drain, args=(process,), daemon=True)
        self.thread.start()

    def _drain(self, process):
        try:
            while chunk := process.read():
                with self.condition:
                    self.data.extend(chunk)
                    self.condition.notify_all()
        except Exception as error:
            self.error = error
        finally:
            with self.condition:
                self.done = True
                self.condition.notify_all()

    def until(self, expected, timeout=5):
        deadline = time.monotonic() + timeout
        with self.condition:
            while expected not in self.data:
                remaining = deadline - time.monotonic()
                assert remaining > 0 and not self.done, bytes(self.data)
                self.condition.wait(remaining)
        return bytes(self.data)

    def finished(self):
        self.thread.join(5)
        assert not self.thread.is_alive(), bytes(self.data)
        assert self.error is None
        return bytes(self.data)


@pytest.fixture
def launch(tmp_path):
    processes = []

    def start(code, **kwargs):
        process = PtyProcess.start([sys.executable, "-u", "-c", code], tmp_path, **kwargs)
        processes.append(process)
        return process, Capture(process)

    yield start
    for process in processes:
        process.close()


def test_actual_session_controlling_tty_cwd_and_environment(launch, tmp_path):
    process, output = launch("""
import json, os
with open('/dev/tty') as tty:
    print(json.dumps({'tty': [os.isatty(n) for n in (0, 1, 2)],
        'foreground': os.tcgetpgrp(tty.fileno()), 'group': os.getpgrp(),
        'session': os.getsid(0), 'pid': os.getpid(), 'cwd': os.getcwd(),
        'env': os.environ['PTY_TEST_VALUE']}, ensure_ascii=False))
""", env={**os.environ, "PTY_TEST_VALUE": "área de trabajo ☃"})
    data = json.loads(output.finished().decode().strip())
    assert data == {"tty": [True, True, True], "foreground": process.pid,
                    "group": process.pid, "session": process.pid, "pid": process.pid,
                    "cwd": str(tmp_path), "env": "área de trabajo ☃"}
    assert process.poll() == 0
    assert process.read() == b""


def test_bidirectional_unicode_and_literal_control_bytes(launch):
    process, output = launch("""
import os, tty
tty.setraw(0)
print('READY', flush=True)
data = os.read(0, 4096)
os.write(1, b'RECEIVED:' + data.hex().encode() + b':END')
""")
    output.until(b"READY")
    payload = "¡Hola!\x01\t☃".encode()
    process.write(payload)
    assert b"RECEIVED:" + payload.hex().encode() + b":END" in output.finished()


def test_initial_size_and_resize_reach_the_child(launch):
    process, output = launch("""
import fcntl, struct, termios
def size():
    rows, cols, _, _ = struct.unpack('HHHH', fcntl.ioctl(0, termios.TIOCGWINSZ, b'\\0' * 8))
    print(f'SIZE:{cols},{rows}', flush=True)
size()
input()
size()
""", cols=91, rows=23)
    output.until(b"SIZE:91,23")
    process.resize(130, 41)
    process.write(b"\n")
    assert b"SIZE:130,41" in output.finished()


def test_ctrl_c_is_delivered_to_the_child_foreground_group(launch):
    process, output = launch("""
import signal, time
def interrupted(*args):
    print('INTERRUPTED', flush=True)
    raise SystemExit(23)
signal.signal(signal.SIGINT, interrupted)
print('READY', flush=True)
while True:
    time.sleep(1)
""")
    output.until(b"READY")
    process.write(b"\x03")
    assert b"INTERRUPTED" in output.finished()
    assert process.stop() == 23


def test_nonzero_exit_and_repeated_cleanup(launch):
    process, output = launch("print('DONE'); raise SystemExit(7)")
    assert b"DONE" in output.finished()
    assert process.stop() == 7
    assert process.stop() == 7
    process.close()
    process.close()
    assert process.read() == b""
    with pytest.raises(PtyError):
        process.write(b"after close")


def test_missing_executable_reports_failure_through_terminal(tmp_path):
    process = PtyProcess.start([str(tmp_path / "missing-command")], tmp_path)
    try:
        output = Capture(process).finished()
        assert b"Cannot execute local terminal command" in output
        assert process.stop() == 127
    finally:
        process.close()


def test_argv_is_passed_literally_without_a_shell(tmp_path):
    value = "literal \"quoted\" $(touch should-not-exist);\n☃"
    process = PtyProcess.start(
        [sys.executable, "-c", "import json,sys; print(json.dumps(sys.argv[1]))", value],
        tmp_path,
    )
    try:
        assert json.loads(Capture(process).finished().decode().strip()) == value
        assert not (tmp_path / "should-not-exist").exists()
    finally:
        process.close()


def _alive(pid):
    path = Path(f"/proc/{pid}/stat")
    try:
        return path.read_text().split(") ", 1)[1].split()[0] != "Z"
    except OSError:  # FileNotFoundError (ENOENT) or ProcessLookupError (ESRCH)
        return False


def test_stop_kills_owned_descendants_without_touching_other_processes(launch):
    unrelated = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"])
    try:
        process, output = launch("""
import signal, subprocess, sys, time
signal.signal(signal.SIGTERM, signal.SIG_IGN)
child = subprocess.Popen([sys.executable, '-c',
    'import signal,time; signal.signal(signal.SIGTERM, signal.SIG_IGN); print("CHILD_READY", flush=True); time.sleep(30)'])
print(f'CHILD:{child.pid}', flush=True)
while True:
    time.sleep(1)
""")
        data = output.until(b"CHILD_READY")
        child_pid = int(next(line for line in data.splitlines() if line.startswith(b"CHILD:")).split(b":")[1])
        started = time.monotonic()
        assert process.stop(timeout=0.1) == -signal.SIGKILL
        assert time.monotonic() - started < 3
        output.finished()
        deadline = time.monotonic() + 3
        while _alive(child_pid) and time.monotonic() < deadline:
            time.sleep(0.01)
        assert not _alive(child_pid)
        assert unrelated.poll() is None
    finally:
        unrelated.terminate()
        unrelated.wait(timeout=5)


def test_stop_cleans_descendants_even_after_session_leader_has_exited(launch):
    process, output = launch("""
import subprocess, sys
child = subprocess.Popen([sys.executable, '-c',
    'import signal,time; signal.signal(signal.SIGHUP, signal.SIG_IGN); print("READY", flush=True); time.sleep(30)'],
    stdout=subprocess.PIPE)
assert child.stdout.readline() == b'READY\\n'
print(f'CHILD:{child.pid}', flush=True)
""")
    data = output.until(b"CHILD:")
    child_pid = int(next(line for line in data.splitlines() if line.startswith(b"CHILD:")).split(b":")[1])
    deadline = time.monotonic() + 5
    while process.poll() is None and time.monotonic() < deadline:
        time.sleep(0.01)
    assert process.poll() == 0
    assert _alive(child_pid)
    assert process.stop(timeout=0.1) == 0
    output.finished()
    deadline = time.monotonic() + 3
    while _alive(child_pid) and time.monotonic() < deadline:
        time.sleep(0.01)
    assert not _alive(child_pid)


@pytest.mark.parametrize("cols,rows", [(0, 24), (80, 0), (-1, 24), (65536, 24), (80, 1.5), (True, 24)])
def test_invalid_dimensions_are_rejected_before_spawn(tmp_path, cols, rows):
    with pytest.raises(PtyError, match="dimensions"):
        PtyProcess.start([sys.executable, "-c", "pass"], tmp_path, cols=cols, rows=rows)


def test_invalid_resize_preserves_terminal(launch):
    process, output = launch("print('READY', flush=True); input()")
    output.until(b"READY")
    with pytest.raises(PtyError, match="dimensions"):
        process.resize(0, 24)
    process.write(b"\n")
    output.finished()


def test_failed_spawn_does_not_leak_file_descriptors(tmp_path):
    baseline = len(os.listdir("/proc/self/fd"))
    for _ in range(3):
        with pytest.raises(PtyError):
            PtyProcess.start([sys.executable], tmp_path / "missing")
    assert len(os.listdir("/proc/self/fd")) == baseline


def test_native_windows_import_stays_available_but_start_is_unsupported(tmp_path, monkeypatch):
    monkeypatch.setattr(sys, "platform", "win32")
    with pytest.raises(PtyError, match="Linux|WSL"):
        PtyProcess.start(["claude"], tmp_path)

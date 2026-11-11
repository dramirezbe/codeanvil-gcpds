"""A local Linux/WSL interactive process attached to its own terminal session.

POSIX modules are loaded only when starting a terminal, so importing the web
application remains safe on platforms where this first implementation is absent.
"""

from collections.abc import Sequence
import errno
import os
from pathlib import Path
import signal
import struct
import subprocess
import sys
import threading


class PtyError(RuntimeError):
    """A terminal cannot be started or operated."""


def _dimensions(cols: int, rows: int) -> bytes:
    if any(type(value) is not int or not 1 <= value <= 65535 for value in (cols, rows)):
        raise PtyError("Terminal dimensions must be integers between 1 and 65535.")
    return struct.pack("HHHH", rows, cols, 0, 0)


class PtyProcess:
    """Own the master PTY and the process group created for one local CLI."""

    def __init__(self, process: subprocess.Popen, master: int):
        self._process = process
        self._master = master
        self._io_lock = threading.Lock()
        self._stop_lock = threading.Lock()
        self._closed = False

    @classmethod
    def start(cls, argv: Sequence[str], cwd: Path, env: dict | None = None,
              cols: int = 100, rows: int = 30) -> "PtyProcess":
        if not sys.platform.startswith("linux"):
            raise PtyError("Interactive terminals currently require Linux or WSL.")
        dimensions = _dimensions(cols, rows)
        if isinstance(argv, (str, bytes)) or not argv or any(
            not isinstance(arg, str) or "\0" in arg for arg in argv
        ) or not argv[0]:
            raise PtyError("A terminal requires a nonempty command argument list.")

        import fcntl
        import pty
        import termios

        master = slave = None
        try:
            master, slave = pty.openpty()
            fcntl.ioctl(master, termios.TIOCSWINSZ, dimensions)
            child_env = {**os.environ, "TERM": "xterm-256color", **(env or {})}
            # A separate helper performs TIOCSCTTY after setsid. Unlike
            # preexec_fn, this is safe when Popen is called from an ASGI thread.
            process = subprocess.Popen(
                [sys.executable, "-m", "codeanvil.UI.pty_child", *argv],
                cwd=cwd, env=child_env, stdin=slave, stdout=slave, stderr=slave,
                start_new_session=True, close_fds=True,
            )
            terminal = cls(process, master)
            master = None
            return terminal
        except (OSError, ValueError, TypeError) as error:
            raise PtyError(f"Cannot start local terminal: {error}") from error
        finally:
            for descriptor in (master, slave):
                if descriptor is not None:
                    os.close(descriptor)

    @property
    def pid(self) -> int:
        return self._process.pid

    def read(self, size: int = 65536) -> bytes:
        if type(size) is not int or size <= 0:
            raise PtyError("Read size must be a positive integer.")
        with self._io_lock:
            if self._closed:
                return b""
            # A private duplicate prevents another thread's close from turning
            # this read into an operation on an unrelated reused descriptor.
            descriptor = os.dup(self._master)
        try:
            return os.read(descriptor, size)
        except OSError as error:
            if error.errno == errno.EIO:  # Linux PTYs signal slave closure this way.
                return b""
            raise PtyError(f"Cannot read terminal: {error}") from error
        finally:
            os.close(descriptor)

    def write(self, data: bytes) -> None:
        if not isinstance(data, bytes):
            raise PtyError("Terminal input must be bytes.")
        with self._io_lock:
            if self._closed:
                raise PtyError("Terminal is closed.")
            try:
                remaining = memoryview(data)
                while remaining:
                    written = os.write(self._master, remaining)
                    remaining = remaining[written:]
            except OSError as error:
                raise PtyError(f"Cannot write terminal: {error}") from error

    def resize(self, cols: int, rows: int) -> None:
        dimensions = _dimensions(cols, rows)
        import fcntl
        import termios

        with self._io_lock:
            if self._closed:
                raise PtyError("Terminal is closed.")
            try:
                fcntl.ioctl(self._master, termios.TIOCSWINSZ, dimensions)
            except OSError as error:
                raise PtyError(f"Cannot resize terminal: {error}") from error

    def poll(self) -> int | None:
        return self._process.poll()

    def _signal_group(self, signum: int) -> None:
        try:
            os.killpg(self.pid, signum)
        except ProcessLookupError:
            pass

    def stop(self, timeout: float = 2) -> int:
        if timeout < 0:
            raise PtyError("Stop timeout cannot be negative.")
        with self._stop_lock:
            if self._closed:
                return self._process.wait()
            try:
                self._signal_group(signal.SIGTERM)
                try:
                    self._process.wait(timeout=timeout)
                except subprocess.TimeoutExpired:
                    pass
                # Kill any remaining group members even if the leader already
                # exited: inherited PTY handles must not keep readers blocked.
                self._signal_group(signal.SIGKILL)
                return self._process.wait()
            finally:
                with self._io_lock:
                    os.close(self._master)
                    self._closed = True

    def close(self) -> None:
        self.stop()

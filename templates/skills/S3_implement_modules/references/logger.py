"""Cross-platform colored logger with caller context.

Self-contained: standard library only. Copy this file unchanged to
``src/<package>/config/logger.py``. The timestamp timezone is read from
``TIMEZONE`` in the sibling ``config/runtime.py``; it defaults to
``America/Bogota`` and falls back to UTC when the zone is unknown.

Usage::

    from <package>.config.logger import get_logger

    log = get_logger(__name__)
    log.info("started")
"""

import logging
import os
import sys
from datetime import datetime, timezone, tzinfo
from functools import lru_cache

_COLORS = {
    "DEBUG": "\033[90m",
    "INFO": "\033[35m",
    "WARNING": "\033[33m",
    "ERROR": "\033[31m",
}
_RESET = "\033[0m"
_DIM = "\033[2m"

_FORMAT = "%Y-%m-%d %H:%M:%S"
_DEFAULT_TIMEZONE = "America/Bogota"


@lru_cache(maxsize=1)
def _timezone() -> tzinfo:
    """Resolve the log timezone from ``config/runtime.py``.

    Returns:
        The configured zone, ``America/Bogota`` when ``TIMEZONE`` is not set,
        or UTC when the configured zone is unknown.
    """
    try:
        from . import runtime  # type: ignore[attr-defined]

        name = getattr(runtime, "TIMEZONE", _DEFAULT_TIMEZONE) or _DEFAULT_TIMEZONE
    except ImportError:
        name = _DEFAULT_TIMEZONE
    try:
        from zoneinfo import ZoneInfo

        return ZoneInfo(name)
    except Exception:
        return timezone.utc


def _format_timestamp(dt: datetime) -> str:
    """Format a datetime with millisecond precision in the log timezone.

    Args:
        dt: An aware datetime.

    Returns:
        ``YYYY-MM-DD HH:MM:SS.mmm`` in the resolved timezone.
    """
    localized = dt.astimezone(_timezone())
    base = localized.strftime(_FORMAT)
    millis = f"{localized.microsecond // 1000:03d}"
    return f"{base}.{millis}"


def _supports_color() -> bool:
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("FORCE_COLOR"):
        return True
    if sys.platform == "win32":
        try:
            import ctypes

            kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
            handle = kernel32.GetStdHandle(-11)
            mode = ctypes.c_ulong()
            kernel32.GetConsoleMode(handle, ctypes.byref(mode))
            kernel32.SetConsoleMode(handle, mode.value | 0x0004)
            return True
        except Exception:
            return False
    return hasattr(sys.stderr, "isatty") and sys.stderr.isatty()


class ColoredFormatter(logging.Formatter):

    def __init__(self, use_color: bool = True):
        super().__init__(
            fmt="[%(asctime)s] %(levelname)s %(name)s.%(funcName)s %(message)s",
        )
        self.use_color = use_color

    def formatTime(self, record: logging.LogRecord, datefmt: str | None = None) -> str:
        dt = datetime.fromtimestamp(record.created, tz=timezone.utc)
        return _format_timestamp(dt)

    def format(self, record: logging.LogRecord) -> str:
        if self.use_color:
            color = _COLORS.get(record.levelname, "")
            record.levelname = f"{color}{record.levelname}{_RESET}"
            record.name = f"{_DIM}{record.name}{_RESET}"
        return super().format(record)


def get_logger(name: str, level: int = logging.DEBUG) -> logging.Logger:
    """Get a named logger with colored output on stderr."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(level)
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(ColoredFormatter(use_color=_supports_color()))
    logger.addHandler(handler)
    logger.propagate = False
    return logger

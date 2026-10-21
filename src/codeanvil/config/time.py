"""Unified system timestamp for human-facing output."""

from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

_FORMAT = "%Y-%m-%d %H:%M:%S"


def get_system_timezone(tz_name: str | None = None) -> ZoneInfo:
    """Resolve timezone: explicit arg > config > UTC fallback."""
    if tz_name:
        try:
            return ZoneInfo(tz_name)
        except (ZoneInfoNotFoundError, KeyError):
            raise ValueError(f"unknown timezone: {tz_name}")

    try:
        from codeanvil.config.paths import CONFIG
        configured = CONFIG.get("defaults", {}).get("country", "")
        if configured:
            return ZoneInfo(configured)
    except Exception:
        pass

    return ZoneInfo("UTC")


def format_timestamp(dt: datetime | None = None, tz_name: str | None = None) -> str:
    """Format a datetime with millisecond precision in the resolved timezone."""
    tz = get_system_timezone(tz_name)
    if dt is None:
        dt = datetime.now(timezone.utc)
    localized = dt.astimezone(tz)
    base = localized.strftime(_FORMAT)
    millis = f"{localized.microsecond // 1000:03d}"
    return f"{base}.{millis}"

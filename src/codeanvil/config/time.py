"""Unified system timestamp for human-facing output."""

from datetime import datetime, timezone, tzinfo

_FORMAT = "%Y-%m-%d %H:%M:%S"


def _try_zoneinfo(name: str) -> tzinfo | None:
    """Return a ZoneInfo for *name*, or None when tzdata is missing (Windows)."""
    try:
        from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
        return ZoneInfo(name)
    except (ImportError, ZoneInfoNotFoundError, KeyError):
        return None


def get_system_timezone(tz_name: str | None = None) -> tzinfo:
    """Resolve timezone: explicit arg > config > UTC fallback."""
    if tz_name:
        tz = _try_zoneinfo(tz_name)
        if tz is not None:
            return tz
        raise ValueError(f"unknown timezone: {tz_name}")

    try:
        from codeanvil.config.paths import CONFIG
        configured = CONFIG.get("defaults", {}).get("country", "")
        if configured:
            tz = _try_zoneinfo(configured)
            if tz is not None:
                return tz
    except Exception:
        pass

    return timezone.utc


def format_timestamp(dt: datetime | None = None, tz_name: str | None = None) -> str:
    """Format a datetime with millisecond precision in the resolved timezone."""
    tz = get_system_timezone(tz_name)
    if dt is None:
        dt = datetime.now(timezone.utc)
    localized = dt.astimezone(tz)
    base = localized.strftime(_FORMAT)
    millis = f"{localized.microsecond // 1000:03d}"
    return f"{base}.{millis}"


def format_timestamp_machine(dt: datetime | None = None, tz_name: str | None = None) -> str:
    """Filename-safe timestamp: spaces, colons, and the millisecond dot replaced."""
    human = format_timestamp(dt, tz_name)
    return human.replace(" ", "_").replace(":", "-").replace(".", "-")

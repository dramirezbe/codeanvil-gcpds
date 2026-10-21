"""Tests for codeanvil.config.time — unified system timestamp."""

import re
from datetime import datetime, timezone

import pytest

from codeanvil.config.time import format_timestamp, get_system_timezone

TIMESTAMP_RE = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3}$")


def test_format_timestamp_matches_regex():
    result = format_timestamp()
    assert TIMESTAMP_RE.match(result), f"'{result}' does not match expected format"


def test_format_timestamp_utc_override():
    dt = datetime(2026, 1, 15, 12, 0, 0, 500_000, tzinfo=timezone.utc)
    result = format_timestamp(dt, tz_name="UTC")
    assert result == "2026-01-15 12:00:00.500"


def test_format_timestamp_bogota_offset():
    dt = datetime(2026, 1, 15, 12, 0, 0, 0, tzinfo=timezone.utc)
    result = format_timestamp(dt, tz_name="America/Bogota")
    assert result == "2026-01-15 07:00:00.000"


def test_get_system_timezone_explicit():
    tz = get_system_timezone("US/Eastern")
    assert str(tz) == "US/Eastern"


def test_get_system_timezone_invalid():
    with pytest.raises(ValueError, match="unknown timezone"):
        get_system_timezone("Not/A/Timezone")


def test_default_timezone_from_config():
    tz = get_system_timezone()
    assert str(tz) == "America/Bogota"

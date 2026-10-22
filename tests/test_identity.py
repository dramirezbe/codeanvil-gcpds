"""Tests for codeanvil.config.identity — stdlib-only UUIDv7 generation."""

import re
import time

from codeanvil.config.identity import generate_uuidv7

UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
)


def test_uuidv7_format():
    value = generate_uuidv7()
    assert UUID_RE.match(value), f"'{value}' is not a UUIDv7 (version/variant bits wrong)"


def test_uuidv7_is_unique():
    ids = {generate_uuidv7() for _ in range(100)}
    assert len(ids) == 100


def test_uuidv7_timestamp_is_recent():
    value = generate_uuidv7()
    ts_ms = int(value.split("-")[0] + value.split("-")[1][:4], 16)
    now_ms = time.time_ns() // 1_000_000
    # 48-bit unix_ts_ms must be within 10 seconds of now
    assert abs(now_ms - ts_ms) < 10_000


def test_uuidv7_monotonicish():
    """Two back-to-back UUIDs must have non-decreasing 48-bit timestamps."""
    first = generate_uuidv7()
    second = generate_uuidv7()
    ts_a = int(first.split("-")[0] + first.split("-")[1][:4], 16)
    ts_b = int(second.split("-")[0] + second.split("-")[1][:4], 16)
    assert ts_b >= ts_a

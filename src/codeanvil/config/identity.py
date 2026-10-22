"""Project identity — UUIDv7 generation (stdlib-only, Python 3.10+)."""

import time
import uuid


def generate_uuidv7() -> str:
    """Generate an RFC 9562 UUIDv7: 48-bit unix timestamp (ms) + version +
    variant + 62 random bits. Time-sortable, unique across machines.

    Implemented manually because uuid.uuid7() only exists on Python 3.14+
    and the package supports 3.10+."""
    ts_ms = (time.time_ns() // 1_000_000) & 0xFFFF_FFFF_FFFF
    rand = uuid.uuid4().int
    # Layout: [48-bit ts_ms][4-bit version=7][62-bit random with variant=0b10]
    value = (ts_ms << 80) | (7 << 76) | (rand & 0x3FFF_FFFF_FFFF_FFFF)
    value = (value & ~(0b11 << 62)) | (0b10 << 62)
    return str(uuid.UUID(int=value))

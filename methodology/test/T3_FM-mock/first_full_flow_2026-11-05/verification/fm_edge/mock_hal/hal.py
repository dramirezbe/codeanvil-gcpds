"""Mock HAL implementation behind the HalPort protocol."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import AsyncIterator

import numpy as np

from fm_edge.config.logger import get_logger
from fm_edge.dsp.capture import convert_samples
from fm_edge.hal.port import HalFrame
from verification.fm_edge.mock_hal.generator import (
    CarrierSpec,
    generate_update,
    SAMPLES_PER_UPDATE,
)

log = get_logger(__name__)


class MockHal:
    """Mock HAL that yields HalFrames from generated or preloaded data."""

    def __init__(
        self,
        fc_hz: int = 98_000_000,
        carriers: list[CarrierSpec] | None = None,
        seed: int = 42,
        num_updates: int = 120,
    ) -> None:
        self.fc_hz = fc_hz
        self.carriers = carriers or []
        self.seed = seed
        self.num_updates = num_updates

    async def stream(self) -> AsyncIterator[HalFrame]:
        rng = np.random.default_rng(self.seed)
        for i in range(self.num_updates):
            raw_bytes = generate_update(self.carriers, self.fc_hz, i, rng)
            samples = convert_samples(raw_bytes)
            t = datetime.now(timezone.utc).isoformat(timespec="milliseconds")
            yield HalFrame(samples=samples, t_capture_end=t, fc_hz=self.fc_hz)
        log.info(f"MockHal: streamed {self.num_updates} updates")


class SingleUpdateMockHal:
    """Mock HAL yielding exactly one update from raw bytes."""

    def __init__(self, raw_bytes: bytes, fc_hz: int = 98_000_000) -> None:
        self.raw_bytes = raw_bytes
        self.fc_hz = fc_hz

    async def stream(self) -> AsyncIterator[HalFrame]:
        samples = convert_samples(self.raw_bytes)
        t = datetime.now(timezone.utc).isoformat(timespec="milliseconds")
        yield HalFrame(samples=samples, t_capture_end=t, fc_hz=self.fc_hz)


class PrecomputedMockHal:
    """Mock HAL yielding frames from precomputed complex64 arrays."""

    def __init__(self, frames: list[np.ndarray], fc_hz: int = 98_000_000) -> None:
        self.frames = frames
        self.fc_hz = fc_hz

    async def stream(self) -> AsyncIterator[HalFrame]:
        for f in self.frames:
            t = datetime.now(timezone.utc).isoformat(timespec="milliseconds")
            yield HalFrame(samples=f, t_capture_end=t, fc_hz=self.fc_hz)

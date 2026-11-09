"""Runtime Mock HAL for the FM occupancy preview.

This is part of the runnable package. The independent golden vectors and test
drivers remain in ``verification/`` and are not needed to start the service.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import AsyncIterator

import numpy as np

from fm_edge.dsp.capture import convert_samples
from fm_edge.hal.port import HalFrame

SAMPLE_RATE = 2_400_000
SAMPLES_PER_UPDATE = 65_536
NOISE_SIGMA = 10 ** (-31.7 / 20)
SCENES = ("SC-1", "SC-2", "SC-3", "SC-4", "SC-5", "SC-6")


@dataclass(frozen=True)
class Carrier:
    channel: int
    level_dbfs: float
    start_update: int = 0
    end_update: int | None = None


def _scene_carriers(scene: str) -> tuple[Carrier, ...]:
    if scene == "SC-1":
        return ()
    if scene == "SC-2":
        return (Carrier(1, -20), Carrier(4, -20), Carrier(8, -20))
    if scene == "SC-3":
        return (Carrier(4, -20), Carrier(5, -20))
    if scene == "SC-4":
        return (Carrier(2, -29), Carrier(7, -39))
    if scene == "SC-5":
        return (Carrier(6, -20, end_update=60),)
    if scene == "SC-6":
        return tuple(Carrier(n, -20) for n in range(8))
    raise ValueError(f"Unknown scene: {scene}")


class MockHal:
    """Generate paced, labelled FM scenes for the package's preview mode."""

    def __init__(
        self,
        scene: str = "SC-2",
        fc_hz: int = 98_000_000,
        seed: int = 1,
        updates: int = 0,
        period_s: float = 0.5,
    ) -> None:
        if period_s <= 0:
            raise ValueError("period_s must be positive")
        if updates < 0:
            raise ValueError("updates must be non-negative")
        self.carriers = _scene_carriers(scene)
        self.fc_hz = fc_hz
        self.seed = seed
        self.updates = updates
        self.period_s = period_s

    async def stream(self) -> AsyncIterator[HalFrame]:
        rng = np.random.default_rng(self.seed)
        t = np.arange(SAMPLES_PER_UPDATE, dtype=np.float64) / SAMPLE_RATE
        update = 0
        while self.updates == 0 or update < self.updates:
            await asyncio.sleep(self.period_s)
            signal = (
                rng.normal(0, NOISE_SIGMA, SAMPLES_PER_UPDATE)
                + 1j * rng.normal(0, NOISE_SIGMA, SAMPLES_PER_UPDATE)
                + 0.02
            )
            for carrier in self.carriers:
                if update < carrier.start_update:
                    continue
                if carrier.end_update is not None and update >= carrier.end_update:
                    continue
                freq_hz = self.fc_hz - 900_000 + 200_000 * carrier.channel
                phase = rng.uniform(0, 2 * np.pi)
                amplitude = 10 ** (carrier.level_dbfs / 20)
                signal += amplitude * np.exp(
                    1j * (
                        2 * np.pi * (freq_hz - self.fc_hz) * t
                        + 75 * np.sin(2 * np.pi * 1000 * t + phase)
                    )
                )

            raw = np.empty(2 * SAMPLES_PER_UPDATE, dtype=np.uint8)
            raw[0::2] = np.clip(
                np.round(127.5 + 127.5 * signal.real), 0, 255
            ).astype(np.uint8)
            raw[1::2] = np.clip(
                np.round(127.5 + 127.5 * signal.imag), 0, 255
            ).astype(np.uint8)
            update += 1
            yield HalFrame(
                samples=convert_samples(raw.tobytes()),
                t_capture_end=datetime.now(timezone.utc).isoformat(
                    timespec="milliseconds"
                ),
                fc_hz=self.fc_hz,
            )

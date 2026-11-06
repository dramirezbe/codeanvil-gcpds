"""Bottom-up drivers: run the SVC-001 pipeline through its base with a HAL."""

from __future__ import annotations

import asyncio

import numpy as np

from fm_edge.dsp.spectrum import compute_spectrum
from fm_edge.dsp.channels import ChannelDetector
from fm_edge.output.server import format_message


def drive_once(samples: np.ndarray, fc_hz: int = 98_000_000) -> str:
    """Run one update through spectrum -> channels -> message formatting."""
    spectrum = compute_spectrum(samples, fc_hz)
    detector = ChannelDetector(fc_hz)
    channels = detector.update(spectrum)
    return format_message(spectrum, channels, "2026-11-05T12:00:00.000Z")


async def drive_stream(hal: object, fc_hz: int = 98_000_000) -> list[str]:
    """Consume a HAL stream and format one message per update."""
    detector = ChannelDetector(fc_hz)
    out: list[str] = []
    async for frame in hal.stream():  # type: ignore[attr-defined]
        spectrum = compute_spectrum(frame.samples, fc_hz)
        channels = detector.update(spectrum)
        out.append(format_message(spectrum, channels, frame.t_capture_end))
    return out


def run(coro: object) -> object:
    return asyncio.run(coro)  # type: ignore[arg-type]

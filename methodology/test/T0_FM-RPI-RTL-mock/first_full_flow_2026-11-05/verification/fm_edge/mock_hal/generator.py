"""Mock HAL signal generator per Build Package B.2.

Generates interleaved uint8 I/Q at 2.4 MS/s. Each scene is deterministic
given its parameters and seed.
"""

from __future__ import annotations

import numpy as np
from dataclasses import dataclass
from fm_edge.config.logger import get_logger

log = get_logger(__name__)

FS = 2_400_000
N = 1024
K = 64
SAMPLES_PER_UPDATE = K * N
DC_SPIKE_REAL = 0.02
NOISE_SIGMA_DBFS = -31.7


@dataclass(frozen=True)
class CarrierSpec:
    freq_hz: float
    level_dbfs: float
    start_update: int = 0
    end_update: int = 999_999


def _noise_sigma() -> float:
    return 10 ** (NOISE_SIGMA_DBFS / 20)


def generate_update(
    carriers: list[CarrierSpec],
    fc_hz: int,
    update_index: int,
    rng: np.random.Generator,
) -> bytes:
    """Generate one update of interleaved uint8 I/Q bytes."""
    sigma = _noise_sigma()
    t = np.arange(SAMPLES_PER_UPDATE, dtype=np.float64) / FS

    noise_i = rng.normal(0, sigma, SAMPLES_PER_UPDATE)
    noise_q = rng.normal(0, sigma, SAMPLES_PER_UPDATE)
    signal = noise_i + 1j * noise_q

    for c in carriers:
        if not (c.start_update <= update_index < c.end_update):
            continue
        amplitude = 10 ** (c.level_dbfs / 20)
        delta_f = c.freq_hz - fc_hz
        phase = rng.uniform(0, 2 * np.pi)
        carrier = amplitude * np.exp(
            1j * (2 * np.pi * delta_f * t + 75 * np.sin(2 * np.pi * 1000 * t + phase))
        )
        signal += carrier

    signal = signal + DC_SPIKE_REAL

    i_raw = np.clip(np.round(127.5 + 127.5 * signal.real), 0, 255).astype(np.uint8)
    q_raw = np.clip(np.round(127.5 + 127.5 * signal.imag), 0, 255).astype(np.uint8)

    interleaved = np.empty(2 * SAMPLES_PER_UPDATE, dtype=np.uint8)
    interleaved[0::2] = i_raw
    interleaved[1::2] = q_raw
    return interleaved.tobytes()


def generate_scene(
    carriers: list[CarrierSpec],
    fc_hz: int,
    seed: int,
    num_updates: int = 120,
) -> list[bytes]:
    """Generate all updates for a labelled scene."""
    rng = np.random.default_rng(seed)
    updates: list[bytes] = []
    for i in range(num_updates):
        updates.append(generate_update(carriers, fc_hz, i, rng))
    log.info(f"Generated scene: {num_updates} updates, {len(carriers)} carriers, seed={seed}")
    return updates


DEFAULT_FC_HZ = 98_000_000


def scene_carriers(scene: str, fc_hz: int = DEFAULT_FC_HZ) -> list[CarrierSpec]:
    """Return the carrier specs for a named labelled scene."""
    def ch_freq(n: int) -> float:
        return fc_hz - 900_000 + 200_000 * n

    if scene == "SC-1":
        return []
    elif scene == "SC-2":
        return [
            CarrierSpec(ch_freq(1), -20.0),
            CarrierSpec(ch_freq(4), -20.0),
            CarrierSpec(ch_freq(8), -20.0),
        ]
    elif scene == "SC-3":
        return [
            CarrierSpec(ch_freq(4), -20.0),
            CarrierSpec(ch_freq(5), -20.0),
        ]
    elif scene == "SC-4":
        return [
            CarrierSpec(ch_freq(2), -29.0),
            CarrierSpec(ch_freq(7), -39.0),
        ]
    elif scene == "SC-5":
        return [
            CarrierSpec(ch_freq(6), -20.0, start_update=0, end_update=60),
        ]
    elif scene == "SC-6":
        return [CarrierSpec(ch_freq(n), -20.0) for n in range(8)]
    else:
        raise ValueError(f"Unknown scene: {scene}")

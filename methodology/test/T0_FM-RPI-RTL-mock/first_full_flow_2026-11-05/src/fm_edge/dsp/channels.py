from collections import deque
from dataclasses import dataclass

import numpy as np

from fm_edge.config.logger import get_logger
from fm_edge.dsp.spectrum import SpectrumResult, BIN_HZ

log = get_logger(__name__)

NUM_CHANNELS = 10
HISTORY_LEN = 120
THRESHOLD_DB = 10.0
HALF_BW_BINS = 38
CHANNEL_BINS = 2 * HALF_BW_BINS + 1  # 77


@dataclass(frozen=True)
class ChannelState:
    f_mhz: float
    power_dbfs: float
    occupied: bool
    occupancy: float


@dataclass(frozen=True)
class ChannelResult:
    channels: list[ChannelState]


class ChannelDetector:

    def __init__(self, fc_hz: int) -> None:
        self._fc_hz = fc_hz
        self._history: list[deque[bool]] = [
            deque(maxlen=HISTORY_LEN) for _ in range(NUM_CHANNELS)
        ]
        self._centres_idx: list[int] = []
        for n in range(NUM_CHANNELS):
            offset_hz = 100_000 + 200_000 * n
            idx = round(offset_hz / BIN_HZ)
            self._centres_idx.append(idx)

    def update(self, spectrum: SpectrumResult) -> ChannelResult:
        bins = spectrum.bins_dbfs
        floor = spectrum.floor_dbfs
        states: list[ChannelState] = []

        for n in range(NUM_CHANNELS):
            centre_idx = self._centres_idx[n]
            lo = max(0, centre_idx - HALF_BW_BINS)
            hi = min(len(bins), centre_idx + HALF_BW_BINS + 1)
            channel_bins = bins[lo:hi]

            linear = 10.0 ** (channel_bins / 10.0)
            power_dbfs = float(10.0 * np.log10(np.mean(linear)))

            occupied = (power_dbfs - floor) >= THRESHOLD_DB
            self._history[n].append(occupied)
            occupancy = sum(self._history[n]) / len(self._history[n])

            f_hz = self._fc_hz - 900_000 + 200_000 * n
            f_mhz = round(f_hz / 1e6, 1)

            states.append(ChannelState(
                f_mhz=f_mhz,
                power_dbfs=round(power_dbfs, 1),
                occupied=occupied,
                occupancy=round(occupancy, 4),
            ))

        log.debug(
            "channels: %d/%d occupied",
            sum(1 for s in states if s.occupied),
            NUM_CHANNELS,
        )

        return ChannelResult(channels=states)

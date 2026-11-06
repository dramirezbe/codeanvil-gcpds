from dataclasses import dataclass

import numpy as np

from fm_edge.config.logger import get_logger

log = get_logger(__name__)

K = 64
N = 1024
TOTAL_SAMPLES = K * N  # 65536
BIN_HZ = 2_400_000 / N  # 2343.75
CENTRAL_BINS = 853
HALF_CENTRAL = 426


@dataclass(frozen=True)
class SpectrumResult:
    bins_dbfs: np.ndarray  # shape (853,)
    floor_dbfs: float
    fc_hz: int
    bin_hz: float = BIN_HZ


def validate_fc(fc_hz: int) -> bool:
    return 89_000_000 <= fc_hz <= 107_000_000 and fc_hz % 200_000 == 0


def compute_spectrum(samples: np.ndarray, fc_hz: int) -> SpectrumResult:
    frames = samples[:TOTAL_SAMPLES].reshape(K, N)
    # Periodic Hann window (standard for Welch periodograms).
    window = np.hanning(N + 1)[:-1].astype(np.float32)
    # Y3 normalises by (sum of the window)**2, so a full-scale bin-centred
    # tone of amplitude 1.0 reads 0 dBFS.
    w_sum = float(np.sum(window))
    norm = w_sum * w_sum

    windowed = frames * window
    fft_result = np.fft.fft(windowed, n=N, axis=1)
    power = (np.abs(fft_result) ** 2) / norm
    avg_power = np.mean(power, axis=0)

    avg_power = np.maximum(avg_power, 1e-20)
    spectrum_db = 10.0 * np.log10(avg_power)
    spectrum_db = np.fft.fftshift(spectrum_db)

    start = N // 2 - HALF_CENTRAL
    end = N // 2 + HALF_CENTRAL + 1
    central = spectrum_db[start:end].astype(np.float64)

    floor_dbfs = float(np.percentile(central, 10))

    log.debug("spectrum computed: floor=%.1f dBFS, fc=%d Hz", floor_dbfs, fc_hz)

    return SpectrumResult(
        bins_dbfs=central,
        floor_dbfs=floor_dbfs,
        fc_hz=fc_hz,
        bin_hz=BIN_HZ,
    )

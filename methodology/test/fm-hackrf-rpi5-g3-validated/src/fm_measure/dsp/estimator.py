"""SUB-001/estimator — IQ → channel powers in dBFS and 819-point spectrum.

4096-point Hann FFT, 50% overlap, 2495 segments, DC-spike replacement.
Produces 199 channel powers (87.6–108.0 MHz at 100 kHz spacing).
Bin spacing: 10 Msps / 4096 = 2441.40625 Hz.
Integration bandwidth per channel: 105 bins × 2441.4 Hz ≈ 256 347 Hz.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import numpy as np

_FFT_N = 4096
_HOP = _FFT_N // 2            # 50% overlap
_SEGMENTS = 2495               # (131072 × 39 // 2 / 2048 ≈ 2495) per step
_BIN_SPACING_HZ = 10_000_000.0 / _FFT_N   # 2441.40625 Hz
_INTEGRATION_BINS = 105        # 105 × 2441.4 ≈ 256 347 Hz per 100 kHz channel
_DC_ADJACENT_BINS = 3          # bins around DC (index 0 and ±1,±2,±3) replaced
_CHANNEL_SPACING_HZ = 100_000.0
_CHANNELS = 199
_FREQ_START_HZ = 87_600_000.0  # channel 1 centre
_FREQ_END_HZ = 107_600_000.0   # channel 199 centre (87.6 + 198×0.1 MHz)

# Step centre frequencies (from §0.5 / SyRS scan plan)
_STEP_CENTRES = [90_250_000.0, 97_750_000.0, 105_250_000.0]
_USABLE_BW = 8_000_000.0        # 8 MHz usable per step

_WINDOW = np.hanning(_FFT_N).astype(np.float32)
_WINDOW_POWER = np.sum(_WINDOW ** 2)


@dataclass
class ChannelResult:
    channel: int           # 1–199
    step: int              # 1–3
    power_dbfs: Optional[float]
    bins_used: int
    dc_adjacent: bool
    no_data: bool
    clipped: bool
    scan_flagged: bool
    mapping_error_bound_khz: float
    mapping_limit_exceeded: bool
    withheld_reason: Optional[str] = None  # "clipped" | "dropped" | "scan_flagged" | None


@dataclass
class ChannelPowerScan:
    scan_id: int
    scan_start_utc_us: int
    scan_start_sync_state: str
    gains: dict
    bin_spacing_hz: float
    integration_bandwidth_hz: float
    window: str
    fft_length: int
    segments: int
    frequency_correction_ppm: float
    channels: list[ChannelResult]


@dataclass
class SpectrumSnapshot:
    scan_id: int
    steps: list[dict]  # [{step, first_frequency_hz, point_spacing_hz, points_dbfs[819]}]


def _iq_to_complex(frame_bytes: bytes) -> np.ndarray:
    """Convert 131072 int8 bytes → 65536 complex64 samples."""
    raw = np.frombuffer(frame_bytes, dtype=np.int8).astype(np.float32)
    return (raw[0::2] + 1j * raw[1::2]) / 128.0


def _welch_psd(frames: list[bytes], clipped: list[bool]) -> tuple[np.ndarray, int, bool, int]:
    """Welch periodogram over all frames.

    Returns (psd_dbfs[4096], segments_used, any_clipped, dropped_frames).
    """
    acc = np.zeros(_FFT_N, dtype=np.float64)
    segs = 0
    any_clipped = False
    dropped = 0

    for i, fbytes in enumerate(frames):
        if clipped[i]:
            any_clipped = True
        samples = _iq_to_complex(fbytes)
        n = len(samples)
        pos = 0
        while pos + _FFT_N <= n:
            block = samples[pos: pos + _FFT_N] * _WINDOW
            spectrum = np.fft.fft(block, n=_FFT_N)
            acc += (np.abs(spectrum) ** 2)
            segs += 1
            pos += _HOP

    if segs == 0:
        return np.full(_FFT_N, -140.0), 0, any_clipped, len(frames)

    psd = acc / (segs * _WINDOW_POWER)
    # Convert to dBFS (0 dBFS = full scale = 1.0)
    with np.errstate(divide="ignore"):
        psd_db = 10 * np.log10(np.maximum(psd, 1e-14)).astype(np.float32)

    # DC-spike replacement: replace ±_DC_ADJACENT_BINS around DC (index 0) with median of neighbours
    dc_region = list(range(0, _DC_ADJACENT_BINS + 1)) + list(range(_FFT_N - _DC_ADJACENT_BINS, _FFT_N))
    neighbours = psd_db[_DC_ADJACENT_BINS + 1: _DC_ADJACENT_BINS + 10]
    replacement = float(np.median(neighbours))
    for idx in dc_region:
        psd_db[idx] = replacement

    return psd_db, segs, any_clipped, 0


def _channel_power(psd_db: np.ndarray, centre_hz: float, offset_hz: float) -> tuple[float, int, bool]:
    """Integrate power in _INTEGRATION_BINS bins centred at offset_hz from centre_hz.

    Returns (power_dbfs, bins_used, dc_adjacent).
    """
    # Bin index of offset_hz
    bin_f = offset_hz / _BIN_SPACING_HZ
    start_bin = int(round(bin_f - _INTEGRATION_BINS / 2))
    end_bin = start_bin + _INTEGRATION_BINS
    # Keep positive-frequency half; wrap negative offsets to negative-frequency side
    # For simplicity: use fftshift so DC is at centre
    psd_shifted = np.fft.fftshift(psd_db)
    half = _FFT_N // 2
    # In shifted array, DC is at index half
    bin_centre = half + int(round(offset_hz / _BIN_SPACING_HZ))
    b0 = max(0, bin_centre - _INTEGRATION_BINS // 2)
    b1 = min(_FFT_N, b0 + _INTEGRATION_BINS)
    used = b1 - b0
    if used == 0:
        return -140.0, 0, False
    linear = 10 ** (psd_shifted[b0:b1] / 10)
    power_db = float(10 * np.log10(np.sum(linear) / _INTEGRATION_BINS))
    # DC adjacent: channel is within _DC_ADJACENT_BINS of DC
    dc_adj = abs(offset_hz) < _DC_ADJACENT_BINS * _BIN_SPACING_HZ
    return power_db, used, dc_adj


def estimate(
    step_frames: dict[int, list[bytes]],      # step (1–3) → list of frame bytes
    step_meta: dict[int, dict],               # step → {clipped: list[bool], no_data: bool, ...}
    scan_id: int,
    scan_start_utc_us: int,
    scan_start_sync_state: str,
    gains: dict,
    scan_flagged: bool = False,
    frequency_correction_ppm: float = 0.0,
) -> tuple[ChannelPowerScan, SpectrumSnapshot]:
    """Main entry point: estimate channel powers and spectrum from raw IQ frames."""

    # --- Per-step Welch PSDs and 819-point spectra ---
    step_psds: dict[int, np.ndarray] = {}
    step_clipped: dict[int, bool] = {}
    step_dropped: dict[int, int] = {}
    spectrum_steps = []

    for step in (1, 2, 3):
        centre = _STEP_CENTRES[step - 1]
        frames = step_frames.get(step, [])
        meta = step_meta.get(step, {})
        clipped_flags = meta.get("clipped", [False] * len(frames))
        no_data = meta.get("no_data", False)

        if no_data or not frames:
            step_psds[step] = np.full(_FFT_N, -140.0, dtype=np.float32)
            step_clipped[step] = False
            step_dropped[step] = 39
            spectrum_steps.append({
                "step": step,
                "first_frequency_hz": centre - _USABLE_BW / 2,
                "point_spacing_hz": 10_000_000.0 / 819,
                "points_dbfs": [-140.0] * 819,
            })
            continue

        expected = meta.get("expected_frames", 39)
        psd, segs, any_clip, _internal_dropped = _welch_psd(frames, clipped_flags)
        actual_dropped = max(0, expected - len(frames))  # from frame count vs expected
        step_psds[step] = psd
        step_clipped[step] = any_clip
        step_dropped[step] = actual_dropped

        # 819-point spectrum via fftshift + decimation
        psd_shifted = np.fft.fftshift(psd)
        half = _FFT_N // 2
        # Take 819 points from the usable ±4 MHz window
        bw_bins = int(_USABLE_BW / _BIN_SPACING_HZ)
        b0 = half - bw_bins // 2
        b1 = b0 + bw_bins
        region = psd_shifted[b0:b1]
        # Downsample to 819 points
        indices = np.linspace(0, len(region) - 1, 819).astype(int)
        pts = region[indices].tolist()
        pt_spacing = _USABLE_BW / 819
        spectrum_steps.append({
            "step": step,
            "first_frequency_hz": centre - _USABLE_BW / 2,
            "point_spacing_hz": pt_spacing,
            "points_dbfs": [round(float(p), 2) for p in pts],
        })

    # --- Channel-level integration ---
    channels: list[ChannelResult] = []
    for ch in range(1, _CHANNELS + 1):
        freq = _FREQ_START_HZ + (ch - 1) * _CHANNEL_SPACING_HZ
        # Apply frequency correction
        freq_corrected = freq * (1 + frequency_correction_ppm * 1e-6)

        # Find which step covers this channel
        step = _step_for_freq(freq_corrected)
        centre = _STEP_CENTRES[step - 1]
        offset = freq_corrected - centre

        no_data = step_meta.get(step, {}).get("no_data", False) or not step_frames.get(step)
        clipped = step_clipped.get(step, False)
        dropped = step_dropped.get(step, 0)

        # Mapping error bound = frequency correction × frequency in kHz
        mapping_bound_khz = abs(frequency_correction_ppm) * freq / 1e9  # ppm × MHz = kHz
        mapping_exceeded = mapping_bound_khz > 20.0

        if no_data:
            power = None
            withheld = "no_data"
        elif scan_flagged:
            power_raw, bins_used, dc_adj = _channel_power(step_psds[step], centre, offset)
            power = None
            withheld = "scan_flagged"
        elif clipped:
            power_raw, bins_used, dc_adj = _channel_power(step_psds[step], centre, offset)
            power = None
            withheld = "clipped"
        elif dropped > 0 and step_dropped.get(step, 0) > 0:
            power_raw, bins_used, dc_adj = _channel_power(step_psds[step], centre, offset)
            power = None
            withheld = "dropped"
        else:
            power_raw, bins_used, dc_adj = _channel_power(step_psds[step], centre, offset)
            power = round(power_raw, 2)
            withheld = None

        # bins_used for display even when withheld
        if no_data:
            bins_used = 0
            dc_adj = False

        channels.append(ChannelResult(
            channel=ch,
            step=step,
            power_dbfs=power,
            bins_used=bins_used if not no_data else 0,
            dc_adjacent=dc_adj if not no_data else False,
            no_data=no_data,
            clipped=clipped,
            scan_flagged=scan_flagged,
            mapping_error_bound_khz=round(mapping_bound_khz, 3),
            mapping_limit_exceeded=mapping_exceeded,
            withheld_reason=withheld,
        ))

    cps = ChannelPowerScan(
        scan_id=scan_id,
        scan_start_utc_us=scan_start_utc_us,
        scan_start_sync_state=scan_start_sync_state,
        gains=gains,
        bin_spacing_hz=_BIN_SPACING_HZ,
        integration_bandwidth_hz=_INTEGRATION_BINS * _BIN_SPACING_HZ,
        window="Hann",
        fft_length=_FFT_N,
        segments=_SEGMENTS,
        frequency_correction_ppm=frequency_correction_ppm,
        channels=channels,
    )
    ss = SpectrumSnapshot(scan_id=scan_id, steps=spectrum_steps)
    return cps, ss


def _step_for_freq(freq_hz: float) -> int:
    """Return the step (1–3) whose centre is closest to freq_hz."""
    dists = [abs(freq_hz - c) for c in _STEP_CENTRES]
    return dists.index(min(dists)) + 1

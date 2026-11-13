"""Runtime Mock HAL for fm_measure — synthesises IQ in code, reads no verification file.

Scenario is selected at construction.  Supported scenarios:
  gv001  Nominal single carrier (default): tone +1 MHz from step centre, −60 dBm equivalent
  gv003  Vacant channel: AWGN only
  gv004  Two tones: strong carrier at channel n, −20 dB carrier at n+2
  gv005  Clipped capture: one frame at full scale
  gv006  Dropped frame: 38 of 39 frames

Fixed seed = 1 for all AWGN.
"""
from __future__ import annotations

import struct
import time
from typing import Optional

import numpy as np

from fm_measure.config.logger import get_logger
from fm_measure.hal.port import CaptureFrame, CaptureMeta, SdrConfig, SdrPort, SdrUnavailable

log = get_logger(__name__)

_FRAMES_PER_STEP = 39
_SAMPLES_PER_FRAME = 131_072   # 65 536 complex int8 pairs
_AMPLITUDE = 0.5               # GV-001 tone amplitude relative to full scale
_RNG = np.random.default_rng(1)
_SNR_DB = 30.0                 # GV-001 SNR


def _awgn(n: int, rng: np.random.Generator) -> np.ndarray:
    sigma = _AMPLITUDE / (10 ** (_SNR_DB / 20))
    return (rng.standard_normal(n) * sigma).astype(np.float32)


def _tone_frame(offset_hz: float, sample_rate_hz: float, rng: np.random.Generator) -> bytes:
    """One frame: _SAMPLES_PER_FRAME bytes = 65536 int8 I/Q pairs interleaved."""
    n = _SAMPLES_PER_FRAME // 2  # 65536 complex samples
    t = np.arange(n, dtype=np.float64) / sample_rate_hz
    angle = 2 * np.pi * offset_hz * t
    i_f = (_AMPLITUDE * np.cos(angle)).astype(np.float32) + _awgn(n, rng)
    q_f = (_AMPLITUDE * np.sin(angle)).astype(np.float32) + _awgn(n, rng)
    iq = np.empty(2 * n, dtype=np.float32)
    iq[0::2] = i_f
    iq[1::2] = q_f
    iq = np.clip(iq, -1.0, 1.0)
    return (iq * 127).astype(np.int8).tobytes()  # 131072 bytes


def _noise_frame(rng: np.random.Generator) -> bytes:
    n = _SAMPLES_PER_FRAME  # 131072 bytes = 65536 complex
    sigma = _AMPLITUDE / (10 ** (_SNR_DB / 20)) * 2
    return (rng.standard_normal(n) * sigma * 127).astype(np.int8).tobytes()


def _clipped_frame() -> bytes:
    import struct
    # 127, -128 interleaved int8 — full scale I/Q, 65536 pairs
    pair = struct.pack("bb", 127, -128)
    return pair * (_SAMPLES_PER_FRAME // 2)


class MockSdrPort(SdrPort):
    """In-process mock SDR that synthesises IQ without touching verification/."""

    def __init__(self, scenario: str = "gv001") -> None:
        self._scenario = scenario
        self._config: Optional[SdrConfig] = None
        self._open = False
        self._calls: list[SdrConfig] = []
        self._rng = np.random.default_rng(1)

    # --- SdrPort interface ---

    def open(self) -> None:
        log.info(f"MockSdrPort.open scenario={self._scenario}")
        self._open = True

    def info(self) -> dict:
        cfg = self._config
        return {
            "model": "HackRF One (mock)",
            "serial": "MOCK000000000000",
            "configured": cfg is not None,
            "center_hz": cfg.center_hz if cfg else None,
            "sample_rate_hz": cfg.sample_rate_hz if cfg else None,
            "lna_gain_db": cfg.lna_gain_db if cfg else None,
            "rf_gain_db": cfg.rf_gain_db if cfg else None,
            "bb_gain_db": cfg.bb_gain_db if cfg else None,
        }

    def configure(self, config: SdrConfig) -> None:
        config.validate()   # guard: raises ValueError for invalid settings
        self._config = config
        self._calls.append(config)
        log.debug(f"MockSdrPort.configure center={config.center_hz:.0f} Hz")

    def read_frames(self, n: int, timeout_s: float = 2.0) -> list[CaptureFrame]:
        if not self._open:
            raise SdrUnavailable("device not open")
        if self._config is None:
            raise SdrUnavailable("device not configured")
        centre = self._config.center_hz
        sr = self._config.sample_rate_hz
        return self._make_frames(n, centre, sr)

    def close(self) -> None:
        self._open = False
        log.info("MockSdrPort.close")

    # --- internal helpers ---

    def _make_frames(self, n: int, centre: float, sr: float) -> list[CaptureFrame]:
        offset = 1_000_000.0  # +1 MHz from centre (GV-001)
        frames: list[CaptureFrame] = []
        if self._scenario == "gv001":
            for i in range(n):
                frames.append(CaptureFrame(samples=_tone_frame(offset, sr, self._rng)))
        elif self._scenario == "gv003":
            for _ in range(n):
                frames.append(CaptureFrame(samples=_noise_frame(self._rng)))
        elif self._scenario == "gv004":
            # strong tone at offset, −20 dB tone at offset + 2*channel_spacing
            ch_spacing = 100_000.0
            nsamp = _SAMPLES_PER_FRAME // 2  # 65536 complex samples
            for _ in range(n):
                t = np.arange(nsamp, dtype=np.float64) / sr
                i_f = (_AMPLITUDE * np.cos(2 * np.pi * offset * t) +
                       0.1 * _AMPLITUDE * np.cos(2 * np.pi * (offset + 2 * ch_spacing) * t)).astype(np.float32)
                q_f = (_AMPLITUDE * np.sin(2 * np.pi * offset * t) +
                       0.1 * _AMPLITUDE * np.sin(2 * np.pi * (offset + 2 * ch_spacing) * t)).astype(np.float32)
                iq = np.empty(2 * nsamp, dtype=np.float32)
                iq[0::2] = i_f; iq[1::2] = q_f
                iq = np.clip(iq, -1.0, 1.0)
                frames.append(CaptureFrame(samples=(iq * 127).astype(np.int8).tobytes()))
        elif self._scenario == "gv005":
            # first frame clipped, rest normal
            frames.append(CaptureFrame(samples=_clipped_frame(), clipped=True))
            for _ in range(n - 1):
                frames.append(CaptureFrame(samples=_tone_frame(offset, sr, self._rng)))
        elif self._scenario == "gv006":
            # deliver only n-1 frames (simulates dropped frame)
            deliver = max(1, n - 1)
            for _ in range(deliver):
                frames.append(CaptureFrame(samples=_tone_frame(offset, sr, self._rng)))
        else:
            raise ValueError(f"unknown scenario: {self._scenario}")
        return frames

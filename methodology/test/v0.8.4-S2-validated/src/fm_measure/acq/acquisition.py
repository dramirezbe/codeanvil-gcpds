"""SUB-001/acq — Three-step scan scheduler and IQ acquisition.

Schedules and executes the three-step scan; configures the SDR; captures 39 frames
per step; counts overflows, dropped frames and clip events.

hw_dependency = true; required_vl = VL-2.
The Mock HAL drives VL-0/VL-1 — it synthesises IQ without real hardware.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional

from fm_measure.config.logger import get_logger
from fm_measure.hal.port import CaptureFrame, SdrConfig, SdrPort, SdrUnavailable

log = get_logger(__name__)

_STEP_CENTRES = [90_250_000.0, 97_750_000.0, 105_250_000.0]
_FRAMES_PER_STEP = 39
_SAMPLE_RATE = 10_000_000.0
_SCAN_NOMINAL_S = 6.0

_DEFAULT_CONFIG = dict(
    sample_rate_hz=_SAMPLE_RATE,
    lna_gain_db=0,
    rf_gain_db=0,
    bb_gain_db=0,
    agc=False,
    antenna_power=False,
    baseband_filter_hz=10_000_000.0,
)


@dataclass
class StepResult:
    step: int
    centre_hz: float
    frames: list[CaptureFrame]
    clip_count: int
    dropped_frames: int
    overflow_events: int
    retune_failed: bool
    no_data: bool = False


@dataclass
class ScanResult:
    scan_id: int
    scan_start_utc_us: int
    scan_start_sync_state: str
    scan_duration_s: float
    scan_late: bool
    steps: list[StepResult]
    gains: dict


class AcquisitionScheduler:
    """Schedules three-step FM scans via the SDR HAL port."""

    def __init__(
        self,
        sdr: SdrPort,
        gains: Optional[dict] = None,
        scan_nominal_s: float = _SCAN_NOMINAL_S,
    ) -> None:
        self._sdr = sdr
        self._gains = gains or {}
        self._scan_nominal_s = scan_nominal_s
        self._scan_id = 0

    def open(self) -> None:
        self._sdr.open()

    def scan(self, utc_us: int, sync_state: str = "unsynced") -> ScanResult:
        """Execute one complete three-step scan."""
        self._scan_id += 1
        t_start = time.monotonic()
        gains = {
            "rf_amp_db": self._gains.get("rf_gain_db", 0),
            "lna_db": self._gains.get("lna_gain_db", 0),
            "baseband_db": self._gains.get("bb_gain_db", 0),
        }

        steps: list[StepResult] = []
        for i, centre in enumerate(_STEP_CENTRES):
            cfg = SdrConfig(
                center_hz=centre,
                **{**_DEFAULT_CONFIG, **self._gains},
            )
            retune_failed = False
            try:
                self._sdr.configure(cfg)
            except (SdrUnavailable, ValueError) as exc:
                log.warning(f"retune failed step {i+1}: {exc}")
                retune_failed = True

            if retune_failed:
                steps.append(StepResult(
                    step=i + 1, centre_hz=centre, frames=[],
                    clip_count=0, dropped_frames=_FRAMES_PER_STEP,
                    overflow_events=0, retune_failed=True, no_data=True,
                ))
                continue

            try:
                frames = self._sdr.read_frames(_FRAMES_PER_STEP)
            except SdrUnavailable as exc:
                log.error(f"read_frames step {i+1} failed: {exc}")
                steps.append(StepResult(
                    step=i + 1, centre_hz=centre, frames=[],
                    clip_count=0, dropped_frames=_FRAMES_PER_STEP,
                    overflow_events=0, retune_failed=False, no_data=True,
                ))
                continue

            delivered = len(frames)
            dropped = max(0, _FRAMES_PER_STEP - delivered)
            clip_count = sum(1 for f in frames if f.clipped)
            overflow_count = sum(1 for f in frames if f.overflow)

            steps.append(StepResult(
                step=i + 1,
                centre_hz=centre,
                frames=frames,
                clip_count=clip_count,
                dropped_frames=dropped,
                overflow_events=overflow_count,
                retune_failed=False,
            ))

        duration = time.monotonic() - t_start
        late = duration > self._scan_nominal_s

        return ScanResult(
            scan_id=self._scan_id,
            scan_start_utc_us=utc_us,
            scan_start_sync_state=sync_state,
            scan_duration_s=round(duration, 3),
            scan_late=late,
            steps=steps,
            gains=gains,
        )

    def close(self) -> None:
        self._sdr.close()

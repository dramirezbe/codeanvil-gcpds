"""SUB-001/calibrate — Operator procedure: establish_amplitude_calibration.

Measures K(f) across the FM band from a traceable reference source.
hw_dependency = true; required_vl = VL-2. Data flow is fully testable at VL-1
with the Mock HAL and synthetic reference levels.
"""
from __future__ import annotations

import hashlib
import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional

from fm_measure.config.logger import get_logger
from fm_measure.dsp.estimator import ChannelResult

log = get_logger(__name__)

_CHANNELS = 199
_FREQ_START_HZ = 87_600_000.0
_CHANNEL_SPACING_HZ = 100_000.0
_UNCERTAINTY_DB = 0.5           # combined standard uncertainty from §4.5


@dataclass
class CalibrationInput:
    channel: int
    frequency_hz: float
    measured_dbfs: float    # from estimator
    reference_dbm: float    # from operator-entered or reference source


@dataclass
class CalibrationOutput:
    station_id: str
    config_sha256: str
    created_utc_s: float
    verified_until_utc_s: float
    k_db: list[float]
    uncertainty_db: float
    frequency_correction_ppm: float
    dynamic_range_db: float


def establish_amplitude_calibration(
    inputs: list[CalibrationInput],
    station_id: str,
    config_sha256: str,
    frequency_correction_ppm: float = 0.0,
    validity_days: int = 365,
    output_path: Optional[Path] = None,
) -> CalibrationOutput:
    """Compute K(f) = reference_dbm - measured_dbfs for each channel.

    Writes an immutable calibration record to output_path if provided.
    """
    if len(inputs) != _CHANNELS:
        raise ValueError(f"expected {_CHANNELS} calibration inputs, got {len(inputs)}")

    k_db = []
    for inp in sorted(inputs, key=lambda x: x.channel):
        k = inp.reference_dbm - inp.measured_dbfs
        k_db.append(round(k, 4))

    # Dynamic range: difference between max and min K values
    dyn_range = round(max(k_db) - min(k_db), 2)

    now = time.time()
    cal = CalibrationOutput(
        station_id=station_id,
        config_sha256=config_sha256,
        created_utc_s=now,
        verified_until_utc_s=now + validity_days * 86400,
        k_db=k_db,
        uncertainty_db=_UNCERTAINTY_DB,
        frequency_correction_ppm=frequency_correction_ppm,
        dynamic_range_db=dyn_range,
    )

    if output_path is not None:
        _write_immutable(cal, output_path)

    return cal


def _write_immutable(cal: CalibrationOutput, path: Path) -> None:
    """Write calibration record atomically; never overwrites."""
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(
        {**asdict(cal), "schema_version": "1.0"},
        indent=2,
    )
    sha = hashlib.sha256(text.encode()).hexdigest()[:8]
    final = path.parent / f"calibration_{sha}.json"
    if final.exists():
        log.warning(f"calibration record already exists: {final}")
        return
    # Write to temp then rename (atomic)
    tmp = final.with_suffix(".tmp")
    tmp.write_text(text)
    tmp.rename(final)
    # Symlink active.json → this record
    active = path.parent / "active.json"
    if active.exists() or active.is_symlink():
        active.unlink()
    active.symlink_to(final.name)
    log.info(f"calibration record written: {final}")

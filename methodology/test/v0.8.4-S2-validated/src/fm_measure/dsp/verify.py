"""SUB-001/verify — Operator procedure: verify_amplitude_correction.

Verifies the active calibration at 12 measurement points.
Tolerance: median |difference| ≤ 1.0 dB. Frequency limit: ±20 ppm.
hw_dependency = true; required_vl = VL-2.
"""
from __future__ import annotations

import hashlib
import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional

from fm_measure.config.logger import get_logger

log = get_logger(__name__)

_TOLERANCE_DB = 1.0
_FREQ_LIMIT_PPM = 20.0
_REQUIRED_POINTS = 12
_UNCERTAINTY_DB = 0.5


@dataclass
class VerificationPoint:
    channel: int
    frequency_hz: float
    corrected_dbm: float     # after applying K(f)
    reference_dbm: float     # from independent reference HW-011
    difference_db: float     # corrected - reference


@dataclass
class ValidationOutput:
    station_id: str
    calibration_sha256: str
    created_utc_s: float
    verified_until_utc_s: float
    median_difference_db: float
    max_difference_db: float
    frequency_correction_ppm: float
    accepted: bool
    rejection_reason: Optional[str]
    points: list[VerificationPoint]


def verify_amplitude_correction(
    points: list[VerificationPoint],
    station_id: str,
    calibration_sha256: str,
    frequency_correction_ppm: float = 0.0,
    validity_days: int = 365,
    output_path: Optional[Path] = None,
) -> ValidationOutput:
    """Check that the active K(f) keeps all 12 measurement points within tolerance."""
    if len(points) < _REQUIRED_POINTS:
        raise ValueError(f"need ≥{_REQUIRED_POINTS} verification points, got {len(points)}")

    diffs = sorted(abs(p.difference_db) for p in points)
    n = len(diffs)
    median_diff = diffs[n // 2] if n % 2 else (diffs[n // 2 - 1] + diffs[n // 2]) / 2
    max_diff = max(diffs)

    rejection = None
    if median_diff > _TOLERANCE_DB:
        rejection = f"median_difference {median_diff:.3f} dB > {_TOLERANCE_DB} dB tolerance"
    if abs(frequency_correction_ppm) > _FREQ_LIMIT_PPM:
        msg = f"frequency_correction {frequency_correction_ppm:.1f} ppm > ±{_FREQ_LIMIT_PPM} ppm"
        rejection = rejection + "; " + msg if rejection else msg

    accepted = rejection is None
    now = time.time()

    result = ValidationOutput(
        station_id=station_id,
        calibration_sha256=calibration_sha256,
        created_utc_s=now,
        verified_until_utc_s=now + validity_days * 86400,
        median_difference_db=round(median_diff, 4),
        max_difference_db=round(max_diff, 4),
        frequency_correction_ppm=frequency_correction_ppm,
        accepted=accepted,
        rejection_reason=rejection,
        points=points,
    )

    if output_path is not None and accepted:
        _write_immutable(result, output_path)

    if not accepted:
        log.warning(f"verification rejected: {rejection}")
    else:
        log.info(f"verification accepted: median={median_diff:.3f} dB")

    return result


def _write_immutable(result: ValidationOutput, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "schema_version": "1.0",
        "station_id": result.station_id,
        "calibration_sha256": result.calibration_sha256,
        "created_utc_s": result.created_utc_s,
        "verified_until_utc_s": result.verified_until_utc_s,
        "median_difference_db": result.median_difference_db,
        "max_difference_db": result.max_difference_db,
        "frequency_correction_ppm": result.frequency_correction_ppm,
        "accepted": result.accepted,
    }
    text = json.dumps(data, indent=2)
    sha = hashlib.sha256(text.encode()).hexdigest()[:8]
    final = path.parent / f"validation_{sha}.json"
    if final.exists():
        return
    tmp = final.with_suffix(".tmp")
    tmp.write_text(text)
    tmp.rename(final)
    log.info(f"validation record written: {final}")

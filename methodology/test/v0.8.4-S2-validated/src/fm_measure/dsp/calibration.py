"""SUB-001/calibration — Apply K(f), validity and calibration_validity.v1 publisher.

Applies the per-channel amplitude correction K(f) from the active calibration record.
Withholds power when: record expired | config SHA mismatch | calibration unavailable.
Publishes calibration_validity.v1 on change.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from fm_measure.config.logger import get_logger
from fm_measure.dsp.estimator import ChannelPowerScan, ChannelResult

log = get_logger(__name__)

_EXPIRY_MARGIN_S = 7 * 24 * 3600   # warn 7 days before expiry
_UNCERTAINTY_UNCAL = 3.0            # dB uncertainty when no calibration
_UNCERTAINTY_CAL = 0.5              # dB uncertainty with valid calibration


@dataclass
class CalibrationRecord:
    station_id: str
    config_sha256: str
    created_utc_s: float
    verified_until_utc_s: float
    k_db: list[float]            # 199 per-channel amplitude corrections in dB
    uncertainty_db: float
    frequency_correction_ppm: float = 0.0

    def is_valid(self, now_s: float) -> bool:
        return now_s <= self.verified_until_utc_s

    def days_to_expiry(self, now_s: float) -> float:
        return (self.verified_until_utc_s - now_s) / 86400


@dataclass
class CalibratedChannel:
    channel: int
    step: int
    power_dbm: Optional[float]       # None if withheld
    uncertainty_db: float
    withheld_reason: Optional[str]
    dc_adjacent: bool
    no_data: bool
    clipped: bool
    scan_flagged: bool
    mapping_error_bound_khz: float
    mapping_limit_exceeded: bool
    frequency_correction_ppm: float


@dataclass
class CalibratedPowerScan:
    scan_id: int
    scan_start_utc_us: int
    scan_start_sync_state: str
    gains: dict
    calibrated: bool
    calibration_valid: bool
    config_sha256_match: bool
    frequency_correction_ppm: float
    channels: list[CalibratedChannel]


def _load_calibration(path: Path) -> Optional[CalibrationRecord]:
    try:
        raw = json.loads(path.read_text())
        return CalibrationRecord(
            station_id=raw["station_id"],
            config_sha256=raw["config_sha256"],
            created_utc_s=float(raw["created_utc_s"]),
            verified_until_utc_s=float(raw["verified_until_utc_s"]),
            k_db=list(raw["k_db"]),
            uncertainty_db=float(raw.get("uncertainty_db", _UNCERTAINTY_CAL)),
            frequency_correction_ppm=float(raw.get("frequency_correction_ppm", 0.0)),
        )
    except Exception as exc:
        log.warning(f"calibration load failed: {exc}")
        return None


class CalibrationApplier:
    """Applies K(f) corrections and manages calibration validity state."""

    def __init__(self, cal_path: Path, config_sha256: str = "") -> None:
        self._cal_path = cal_path
        self._config_sha = config_sha256
        self._record: Optional[CalibrationRecord] = None
        self._state = "unavailable"   # "valid" | "expiring" | "expired" | "unavailable"
        self._last_state = ""

    def reload(self) -> None:
        """Reload calibration record from disk."""
        self._record = _load_calibration(self._cal_path)

    def apply(self, cps: ChannelPowerScan, now_s: Optional[float] = None) -> CalibratedPowerScan:
        now = now_s if now_s is not None else time.time()
        rec = self._record
        cal_valid = False
        config_match = False
        freq_corr = 0.0

        if rec is not None:
            cal_valid = rec.is_valid(now)
            config_match = (self._config_sha == "" or rec.config_sha256 == self._config_sha)
            freq_corr = rec.frequency_correction_ppm

        self._update_state(rec, cal_valid, now)

        channels: list[CalibratedChannel] = []
        for ch_raw in cps.channels:
            power_dbm, withheld, unc = self._apply_channel(ch_raw, rec, cal_valid, config_match, now)
            channels.append(CalibratedChannel(
                channel=ch_raw.channel,
                step=ch_raw.step,
                power_dbm=power_dbm,
                uncertainty_db=unc,
                withheld_reason=withheld,
                dc_adjacent=ch_raw.dc_adjacent,
                no_data=ch_raw.no_data,
                clipped=ch_raw.clipped,
                scan_flagged=ch_raw.scan_flagged,
                mapping_error_bound_khz=ch_raw.mapping_error_bound_khz,
                mapping_limit_exceeded=ch_raw.mapping_limit_exceeded,
                frequency_correction_ppm=freq_corr,
            ))

        return CalibratedPowerScan(
            scan_id=cps.scan_id,
            scan_start_utc_us=cps.scan_start_utc_us,
            scan_start_sync_state=cps.scan_start_sync_state,
            gains=cps.gains,
            calibrated=rec is not None,
            calibration_valid=cal_valid and config_match,
            config_sha256_match=config_match,
            frequency_correction_ppm=freq_corr,
            channels=channels,
        )

    def _apply_channel(
        self,
        ch: ChannelResult,
        rec: Optional[CalibrationRecord],
        cal_valid: bool,
        config_match: bool,
        now_s: float,
    ) -> tuple[Optional[float], Optional[str], float]:
        # Already withheld upstream
        if ch.withheld_reason is not None:
            return None, ch.withheld_reason, _UNCERTAINTY_UNCAL

        if ch.power_dbfs is None:
            return None, "no_data", _UNCERTAINTY_UNCAL

        # Calibration not available
        if rec is None:
            return None, "cal_unavailable", _UNCERTAINTY_UNCAL

        # Calibration expired
        if not cal_valid:
            return None, "cal_expired", _UNCERTAINTY_UNCAL

        # Config mismatch
        if not config_match:
            return None, "config_mismatch", _UNCERTAINTY_UNCAL

        # Apply K(f): power_dbm = power_dbfs + K[ch-1]
        idx = ch.channel - 1
        k = rec.k_db[idx] if idx < len(rec.k_db) else 0.0
        power_dbm = round(ch.power_dbfs + k, 2)
        return power_dbm, None, rec.uncertainty_db

    def _update_state(self, rec: Optional[CalibrationRecord], cal_valid: bool, now_s: float) -> None:
        if rec is None:
            new_state = "unavailable"
        elif not cal_valid:
            new_state = "expired"
        elif rec.days_to_expiry(now_s) <= 7:
            new_state = "expiring"
        else:
            new_state = "valid"

        if new_state != self._last_state:
            log.info(f"calibration state: {self._last_state!r} → {new_state!r}")
            self._last_state = new_state
        self._state = new_state

    @property
    def state(self) -> str:
        return self._state

    def validity_msg(self, scan_id: int, utc_us: int) -> dict:
        rec = self._record
        return {
            "schema_version": "1.0",
            "scan_id": scan_id,
            "ts_utc_us": utc_us,
            "state": self._state,
            "verified_until_utc_s": rec.verified_until_utc_s if rec else None,
            "config_sha256": rec.config_sha256 if rec else None,
            "uncertainty_db": rec.uncertainty_db if rec else _UNCERTAINTY_UNCAL,
        }

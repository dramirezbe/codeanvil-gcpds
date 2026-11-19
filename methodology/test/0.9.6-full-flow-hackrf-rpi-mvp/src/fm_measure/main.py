"""Acquire FM-band I/Q, estimate its spectrum, and publish scan records."""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import json
from math import isfinite
import signal
from statistics import median
import struct
import time
from pathlib import Path

from fm_measure.config.logger import get_logger
from fm_measure.config.paths import CALV_SOCK, PROGRESS_SOCK, SCAN_SOCK, SPECTRUM_FILE
from fm_measure.config.runtime import HAL_MODE, OCCUPANCY_MARGIN_DB, SCAN_PERIOD_S
from fm_measure.dsp.estimator import ChannelResult, estimate
from fm_measure.hal.port import SdrConfig, SdrPort, SdrUnavailable

log = get_logger(__name__)

_FRAMES_PER_STEP = 6
_STEP_CENTRES = (90_250_000.0, 97_750_000.0, 105_250_000.0)
_SAMPLE_RATE_HZ = 10_000_000.0
_EVIDENCE_LABEL = "FM screening — not a compliance determination"


def _make_hal() -> SdrPort:
    if HAL_MODE == "real":
        from fm_measure.hal.real import RealSdrPort
        return RealSdrPort()
    from fm_measure.hal.mock import MockSdrPort
    return MockSdrPort()


async def _send_progress(sock_path: Path, counter: int) -> None:
    try:
        reader, writer = await asyncio.open_unix_connection(str(sock_path))
        body = json.dumps({"subsystem": "measure", "counter": counter}, separators=(",", ":")).encode()
        writer.write(struct.pack(">I", len(body)) + body)
        await writer.drain()
        writer.close()
        await writer.wait_closed()
    except (OSError, asyncio.TimeoutError):
        pass


def _spectrum_payload(scan_id: int, scan_start_utc_us: int, sync_state: str,
                      snapshot, channels: list[ChannelResult], step_meta: dict, health: dict,
                      scan_duration_s: float) -> dict:
    raw_steps = [
        {
            "step": item["step"],
            "first_frequency_hz": item["first_frequency_hz"],
            "point_spacing_hz": item["point_spacing_hz"],
            "points_dbfs": ([None] * len(item["points_dbfs"])
                            if step_meta[item["step"]]["no_data"] else item["points_dbfs"]),
            "withheld_reason": "no_data" if step_meta[item["step"]]["no_data"] else None,
        }
        for item in snapshot.steps
    ]
    levels = {
        channel.channel: channel.power_dbfs for channel in channels
        if channel.power_dbfs is not None and isfinite(channel.power_dbfs)
        and channel.withheld_reason is None and channel.bins_used > 0
    }
    baseline = median(levels.values()) if levels else None
    threshold = baseline + OCCUPANCY_MARGIN_DB if baseline is not None else None
    points = []
    for channel in channels:
        level = levels.get(channel.channel)
        occupancy = "Uncertain"
        if level is not None and threshold is not None:
            occupancy = "Occupied" if level >= threshold else "Free"
        points.append({
            "channel": channel.channel,
            "freq_hz": 87_600_000.0 + (channel.channel - 1) * 100_000.0,
            "power_dbfs": level,
            "power_dbm": None,
            "withheld_reason": (channel.withheld_reason or "no_data") if level is None else None,
            "occupancy": occupancy,
            "dc_adjacent": channel.dc_adjacent,
        })
    received = sum(1 for step in (1, 2, 3) if not step_meta[step]["no_data"])
    data_state = "ok" if received == len(_STEP_CENTRES) else ("partial" if received else "no_data")
    return {
        "schema": "spectrum.v1",
        "data_state": data_state,
        "sync_state": sync_state,
        "scan_id": scan_id,
        "scan_ts_iso": datetime.fromtimestamp(scan_start_utc_us / 1_000_000, timezone.utc).isoformat(),
        "raw_units": "dBFS",
        "hal": HAL_MODE,
        "raw_steps": raw_steps,
        "points": points,
        "occupancy_rule": {
            "method": "sweep_median_plus_margin",
            "baseline_dbfs": baseline,
            "margin_db": OCCUPANCY_MARGIN_DB,
            "threshold_dbfs": threshold,
        },
        "health": health,
        "scan_duration_s": round(scan_duration_s, 3),
        "calibration_state": "unavailable",
        "evidence_label": _EVIDENCE_LABEL,
    }


def _publish_spectrum(payload: dict) -> None:
    SPECTRUM_FILE.parent.mkdir(parents=True, exist_ok=True)
    temporary = SPECTRUM_FILE.with_suffix(".tmp")
    temporary.write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")
    temporary.replace(SPECTRUM_FILE)


async def _scan_loop(hal: SdrPort, stop: asyncio.Event) -> None:
    scan_clients: list[asyncio.StreamWriter] = []
    SCAN_SOCK.parent.mkdir(parents=True, exist_ok=True)
    if SCAN_SOCK.exists():
        SCAN_SOCK.unlink()
    try:
        SPECTRUM_FILE.unlink()
    except FileNotFoundError:
        pass

    async def on_scan_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        scan_clients.append(writer)
        try:
            await reader.read()
        finally:
            if writer in scan_clients:
                scan_clients.remove(writer)

    scan_server = await asyncio.start_unix_server(on_scan_client, path=str(SCAN_SOCK))
    try:
        hal.open()
        log.info("fm_measure started, HAL=%s, device=%s", HAL_MODE, hal.info())
        scan_id = 0
        async with scan_server:
            while not stop.is_set():
                scan_id += 1
                started = time.monotonic()
                scan_start_utc_us = time.time_ns() // 1_000
                # The time subsystem is not wired into this capture path yet.
                # Mark timestamps unsynced instead of implying traceable UTC.
                sync_state = "unsynced"
                step_frames: dict[int, list[bytes]] = {}
                step_meta: dict[int, dict] = {}
                gains = {"lna_gain_db": 16, "rf_gain_db": 0, "bb_gain_db": 20}
                retune_failures = 0
                overflow_count = 0
                hal_dropped_count = 0

                for step, centre in enumerate(_STEP_CENTRES, start=1):
                    frames = []
                    dropped_this_step = 0
                    try:
                        hal.configure(SdrConfig(
                            center_hz=centre,
                            sample_rate_hz=_SAMPLE_RATE_HZ,
                            lna_gain_db=gains["lna_gain_db"],
                            rf_gain_db=gains["rf_gain_db"],
                            bb_gain_db=gains["bb_gain_db"],
                            agc=False,
                            antenna_power=False,
                            baseband_filter_hz=8_000_000.0,
                        ))
                    except (SdrUnavailable, ValueError) as exc:
                        retune_failures += 1
                        log.error("retune failed for step %d at %.3f MHz: %s", step, centre / 1e6, exc)
                    else:
                        try:
                            frames = hal.read_frames(_FRAMES_PER_STEP, timeout_s=4.0)
                        except SdrUnavailable as exc:
                            log.error("capture failed for step %d at %.3f MHz: %s", step, centre / 1e6, exc)
                        dropped_this_step = int(getattr(hal, "dropped_frames", 0))
                        overflow_count += int(getattr(hal, "overflow_events", 0))
                        hal_dropped_count += dropped_this_step
                    step_frames[step] = [frame.samples for frame in frames]
                    step_meta[step] = {
                        "clipped": [frame.clipped for frame in frames],
                        "overflow": [frame.overflow for frame in frames],
                        "no_data": not frames,
                        "expected_frames": _FRAMES_PER_STEP,
                        "dropped_frames": max(0, _FRAMES_PER_STEP - len(frames) - dropped_this_step),
                    }

                elapsed = time.monotonic() - started
                scan_late = elapsed > 7.0
                dropped_count = sum(meta["dropped_frames"] for meta in step_meta.values()) + hal_dropped_count
                clipped_count = sum(sum(meta["clipped"]) for meta in step_meta.values())
                health = {
                    "scan_late": scan_late,
                    "overflow_count": overflow_count,
                    "dropped_frame_count": dropped_count,
                    "clipped_captures": clipped_count,
                    "retune_failures": retune_failures,
                    "scan_duration_s": round(elapsed, 3),
                    "records_flag_scan": bool(scan_late or overflow_count or dropped_count or clipped_count or retune_failures),
                }

                channel_scan, spectrum_snapshot = await asyncio.to_thread(
                    estimate,
                    step_frames,
                    step_meta,
                    scan_id,
                    scan_start_utc_us,
                    sync_state,
                    gains,
                    health["records_flag_scan"],
                )
                spectrum = _spectrum_payload(
                    scan_id, scan_start_utc_us, sync_state, spectrum_snapshot,
                    channel_scan.channels, step_meta, health, elapsed,
                )
                _publish_spectrum(spectrum)

                scan_record = {
                    "schema": "scan_records.v1",
                    "schema_version": "1.0",
                    "scan_id": scan_id,
                    "scan_start_utc_us": scan_start_utc_us,
                    "scan_start_sync_state": sync_state,
                    "station_id": "COL-001",
                    "calibration_state": "unavailable",
                    "evidence_label": _EVIDENCE_LABEL,
                    "health": {"scan_id": scan_id, **health},
                    "channels": [
                        {
                            "channel": channel.channel,
                            "step": channel.step,
                            "frequency_hz": 87_600_000.0 + (channel.channel - 1) * 100_000.0,
                            "power_dbm": None,
                            "power_dbfs": channel.power_dbfs,
                            "uncertainty_db": None,
                            "occupancy": "Uncertain",
                            "verdict": "Indeterminate",
                            "withheld_reason": "uncalibrated" if channel.power_dbfs is not None else "no_data",
                            "dc_adjacent": channel.dc_adjacent,
                            "no_data": channel.no_data,
                            "clipped": channel.clipped,
                            "scan_flagged": health["records_flag_scan"],
                        }
                        for channel in channel_scan.channels
                    ],
                    "spectrum": spectrum,
                }
                body = json.dumps(scan_record, separators=(",", ":")).encode()
                frame = struct.pack(">I", len(body)) + body
                disconnected = []
                for writer in scan_clients:
                    try:
                        writer.write(frame)
                        await writer.drain()
                    except (OSError, ConnectionError):
                        disconnected.append(writer)
                for writer in disconnected:
                    if writer in scan_clients:
                        scan_clients.remove(writer)

                await _send_progress(PROGRESS_SOCK, scan_id)
                log.info(
                    "scan %d: state=%s, HAL=%s, frames=%d/%d, elapsed=%.2fs",
                    scan_id, spectrum["data_state"], HAL_MODE,
                    sum(len(rows) for rows in step_frames.values()),
                    _FRAMES_PER_STEP * len(_STEP_CENTRES), elapsed,
                )
                try:
                    await asyncio.wait_for(stop.wait(), timeout=max(0.0, SCAN_PERIOD_S - (time.monotonic() - started)))
                except asyncio.TimeoutError:
                    pass
    finally:
        hal.close()
        for writer in scan_clients:
            writer.close()
        for path in (SCAN_SOCK, CALV_SOCK):
            try:
                path.unlink()
            except FileNotFoundError:
                pass
        log.info("fm_measure stopped")


async def _run() -> None:
    hal = _make_hal()
    loop = asyncio.get_running_loop()
    stop = asyncio.Event()

    def shutdown(sig: signal.Signals) -> None:
        log.info("received %s", sig.name)
        stop.set()

    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, shutdown, sig)
    await _scan_loop(hal, stop)


def main() -> None:
    asyncio.run(_run())

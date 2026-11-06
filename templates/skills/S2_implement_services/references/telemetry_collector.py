#!/usr/bin/env python3
"""Locked V-SIL telemetry collector.

S2 copies this file unchanged to ``verification/telemetry/telemetry_collector.py``.
It samples the host and the verification process once per interval and appends one
JSON object per line to a file, one file per VL run. A reading that cannot be taken
is written as ``{"unavailable": "<reason>"}``; it is never invented and never
reported as zero.

Application counters (dropped buffers, queue depth, scheduling latency) are not
measured here: the collector copies them from the JSON object the HAL or the
service instrumentation writes to ``--counters``.

psutil supplies CPU, memory and temperature. Without psutil every metric that
needs it is reported as unavailable and the collector keeps running.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import signal
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

COLLECTOR_NAME = "vsil-telemetry"
COLLECTOR_VERSION = "1.0.0"

try:
    import psutil
except ImportError as exc:  # the run continues with every psutil metric unavailable
    psutil = None
    _PSUTIL_ERROR = f"psutil is not installed: {exc}"
else:
    _PSUTIL_ERROR = ""


def _unavailable(reason: str) -> dict:
    return {"unavailable": reason}


def _reading(reader):
    """Return the reader's value, or an unavailable entry with its reason."""
    try:
        return reader()
    except Exception as exc:  # noqa: BLE001 - telemetry never breaks the run
        return _unavailable(f"{type(exc).__name__}: {exc}")


def _device_model():
    path = Path("/proc/device-tree/model")
    try:
        model = path.read_text(encoding="utf-8", errors="replace").strip("\x00").strip()
    except OSError:
        return _unavailable("no /proc/device-tree/model on this host")
    return model or _unavailable("empty /proc/device-tree/model")


def _host_profile() -> dict:
    cpu_count = os.cpu_count()
    return {
        "system": platform.system(),
        "release": platform.release(),
        "machine": platform.machine(),
        "python": platform.python_version(),
        "cpu_count": cpu_count if cpu_count is not None else _unavailable("os.cpu_count() returned None"),
        "device_model": _device_model(),
    }


def _process_block(process) -> dict:
    if psutil is None:
        return _unavailable(_PSUTIL_ERROR)
    if process is None:
        return _unavailable("process handle unavailable")
    return {
        "pid": _reading(lambda: process.pid),
        "cpu_percent": _reading(lambda: process.cpu_percent(interval=None)),
        "rss_bytes": _reading(lambda: process.memory_info().rss),
        "memory_percent": _reading(lambda: process.memory_percent()),
    }


def _system_block() -> dict:
    if psutil is None:
        return _unavailable(_PSUTIL_ERROR)
    cpu = _reading(lambda: psutil.cpu_percent(interval=None))
    memory = _reading(psutil.virtual_memory)
    if isinstance(memory, dict):
        return {
            "cpu_percent": cpu,
            "memory_percent": memory,
            "memory_used_bytes": memory,
            "memory_total_bytes": memory,
        }
    return {
        "cpu_percent": cpu,
        "memory_percent": memory.percent,
        "memory_used_bytes": memory.used,
        "memory_total_bytes": memory.total,
    }


def _temperature() -> dict:
    if psutil is None:
        return _unavailable(_PSUTIL_ERROR)
    sensors = getattr(psutil, "sensors_temperatures", None)
    if sensors is None:
        return _unavailable(f"temperature sensors are not exposed on {platform.system()}")
    try:
        groups = sensors()
    except Exception as exc:  # noqa: BLE001 - telemetry never breaks the run
        return _unavailable(f"{type(exc).__name__}: {exc}")
    readings = [
        (entry.label or name, entry.current)
        for name, entries in groups.items()
        for entry in entries
        if entry.current is not None
    ]
    if not readings:
        return _unavailable("no temperature sensor reported a value")
    label, value = max(readings, key=lambda item: item[1])
    return {"value": round(value, 2), "sensor": label}


def _counters(path):
    if path is None:
        return _unavailable("no counters source configured")
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except OSError as exc:
        return _unavailable(f"counters file unreadable: {exc}")
    except json.JSONDecodeError as exc:
        return _unavailable(f"counters file is not JSON: {exc}")
    if not isinstance(payload, dict) or not payload:
        return _unavailable("counters file holds no JSON object")
    return payload


def _sample(process, counters_path) -> dict:
    return {
        "collector": {"name": COLLECTOR_NAME, "version": COLLECTOR_VERSION},
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
        "monotonic_s": round(time.monotonic(), 3),
        "measurement_source": "psutil" if psutil is not None else "unavailable",
        "host": _host_profile(),
        "process": _process_block(process),
        "system": _system_block(),
        "temperature_c": _temperature(),
        "counters": _counters(counters_path),
        "counters_source": (
            str(counters_path) if counters_path is not None
            else _unavailable("no counters source configured")
        ),
    }


def _default_output() -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return Path(__file__).resolve().parent / f"telemetry-{stamp}.jsonl"


def _parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Sample host and process telemetry into a JSON-lines file.")
    parser.add_argument("--output", type=Path, default=None,
                        help="output JSON-lines file (default: next to this script, one per run)")
    parser.add_argument("--interval", type=float, default=1.0,
                        help="seconds between samples (default: 1.0)")
    parser.add_argument("--duration", type=float, default=0.0,
                        help="seconds to sample; 0 runs until SIGINT or SIGTERM (default: 0)")
    parser.add_argument("--counters", type=Path, default=None,
                        help="JSON object written by the HAL or the service instrumentation")
    args = parser.parse_args(argv)
    if args.interval <= 0:
        parser.error("--interval must be greater than 0")
    if args.duration < 0:
        parser.error("--duration must be 0 or greater")
    return args


def main(argv=None) -> int:
    args = _parse_args(argv)
    output = args.output or _default_output()

    process = None
    if psutil is not None:
        candidate = _reading(psutil.Process)
        if not isinstance(candidate, dict):
            process = candidate
            psutil.cpu_percent(interval=None)
            process.cpu_percent(interval=None)

    stop = threading.Event()

    def _request_stop(signum, frame):
        stop.set()

    for name in ("SIGINT", "SIGTERM"):
        if hasattr(signal, name):
            signal.signal(getattr(signal, name), _request_stop)

    try:
        output.parent.mkdir(parents=True, exist_ok=True)
        stream = output.open("w", encoding="utf-8")
    except OSError as exc:
        print(f"telemetry collector: cannot write {output}: {exc}", file=sys.stderr)
        return 1

    deadline = time.monotonic() + args.duration if args.duration > 0 else None
    try:
        with stream:
            while not stop.is_set():
                stream.write(json.dumps(_sample(process, args.counters), ensure_ascii=False) + "\n")
                stream.flush()
                if deadline is not None and time.monotonic() >= deadline:
                    break
                stop.wait(args.interval)
    except OSError as exc:
        print(f"telemetry collector: write failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

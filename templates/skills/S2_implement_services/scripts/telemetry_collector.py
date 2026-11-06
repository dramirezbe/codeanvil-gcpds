#!/usr/bin/env python3
"""Locked V-SIL telemetry collector.

It runs in place on the CodeAnvil methodology runtime, never copied into a project:
``verification/run.sh`` starts it with ``codeanvil python <this file> --pid $$ ...``.
It samples the host and the verification process tree once per interval and appends
one JSON object per line to a file, one file per VL run. The tree is ``--pid`` (default:
the collector's parent, e.g. ``run.sh``) plus every descendant except the collector
itself, so the services and test processes that ``run.sh`` starts are measured. A
reading that cannot be taken is written as ``{"unavailable": "<reason>"}``; it is
never invented and never reported as zero.

Application counters (dropped buffers, queue depth, scheduling latency) are not
measured here: the collector copies them from the JSON object the HAL or the
service instrumentation writes to ``--counters``.

psutil is the only measurement source (CPU, memory, temperature, CPU count).
The runtime provides it; without it the collector exits 2 before writing anything,
and ``codeanvil python`` refuses to start it in the first place.
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
COLLECTOR_VERSION = "1.1.0"

try:
    import psutil
except ImportError as exc:  # the methodology runtime always ships psutil
    print(f"telemetry collector: psutil is not installed ({exc}); run codeanvil runtime sync",
          file=sys.stderr)
    sys.exit(2)


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
    cpu_count = _reading(lambda: psutil.cpu_count(logical=True))
    return {
        "system": platform.system(),
        "release": platform.release(),
        "machine": platform.machine(),
        "python": platform.python_version(),
        "cpu_count": cpu_count if cpu_count is not None else _unavailable("psutil.cpu_count() returned None"),
        "device_model": _device_model(),
    }


class _ProcessTree:
    """The root process plus its descendants, sampled as one sum.

    psutil's ``cpu_percent(interval=None)`` measures since the previous call on
    the same handle, so handles are kept between samples. A process first seen
    in a sample is primed and counted from the next sample on; the count of such
    processes is reported so a low first reading is never mistaken for idle."""

    def __init__(self, root):
        self.root = root
        self.own_pid = os.getpid()
        self.handles = {}
        self.sample()  # primes every handle; the first real sample comes later

    def _members(self):
        members = [self.root]
        try:
            members.extend(self.root.children(recursive=True))
        except psutil.Error:
            pass
        return [member for member in members if member.pid != self.own_pid]

    def sample(self) -> dict:
        if not self.root.is_running():
            return _unavailable(f"process {self.root.pid} is no longer running")
        cpu = 0.0
        rss = 0
        memory = 0.0
        measured = 0
        new = 0
        alive = {}
        for member in self._members():
            handle = self.handles.get(member.pid, member)
            try:
                with handle.oneshot():
                    value = handle.cpu_percent(interval=None)
                    info = handle.memory_info()
                    percent = handle.memory_percent()
            except psutil.Error:
                continue
            alive[member.pid] = handle
            rss += info.rss
            memory += percent
            if member.pid in self.handles:
                cpu += value
                measured += 1
            else:
                new += 1
        self.handles = alive
        return {
            "pid": self.root.pid,
            "processes": len(alive),
            "cpu_percent": round(cpu, 2),
            "cpu_unmeasured_new_processes": new,
            "rss_bytes": rss,
            "memory_percent": round(memory, 3),
        }


def _process_block(tree) -> dict:
    if isinstance(tree, dict):
        return tree
    return _reading(tree.sample)


def _system_block() -> dict:
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
    except ValueError as exc:  # JSONDecodeError and UnicodeDecodeError
        return _unavailable(f"counters file is not UTF-8 JSON: {exc}")
    if not isinstance(payload, dict) or not payload:
        return _unavailable("counters file holds no JSON object")
    return payload


def _sample(tree, counters_path) -> dict:
    return {
        "collector": {"name": COLLECTOR_NAME, "version": COLLECTOR_VERSION},
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
        "monotonic_s": round(time.monotonic(), 3),
        "measurement_source": "psutil",
        "host": _host_profile(),
        "process": _process_block(tree),
        "system": _system_block(),
        "temperature_c": _temperature(),
        "counters": _counters(counters_path),
        "counters_source": (
            str(counters_path) if counters_path is not None
            else _unavailable("no counters source configured")
        ),
    }


def _default_output() -> Path:
    # Self-contained by design: the copied file imports nothing from the tool
    # that scaffolded it. Milliseconds and the PID keep two runs started in the
    # same second (vl0 and vl1) from sharing one file.
    now = datetime.now(timezone.utc)
    stamp = f"{now:%Y%m%dT%H%M%S}{now.microsecond // 1000:03d}Z"
    # cwd is the project root: `codeanvil python` runs every script from there.
    return Path.cwd() / "verification" / "telemetry" / f"telemetry-{stamp}-{os.getpid()}.jsonl"


def _parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Sample host and process telemetry into a JSON-lines file.")
    parser.add_argument("--output", type=Path, default=None,
                        help="output JSON-lines file (default: verification/telemetry/ under the cwd, one per run)")
    parser.add_argument("--interval", type=float, default=1.0,
                        help="seconds between samples (default: 1.0)")
    parser.add_argument("--duration", type=float, default=0.0,
                        help="seconds to sample; 0 runs until SIGINT or SIGTERM (default: 0)")
    parser.add_argument("--counters", type=Path, default=None,
                        help="JSON object written by the HAL or the service instrumentation")
    parser.add_argument("--pid", type=int, default=None,
                        help="root of the process tree to measure (default: the collector's parent)")
    args = parser.parse_args(argv)
    if args.interval <= 0:
        parser.error("--interval must be greater than 0")
    if args.duration < 0:
        parser.error("--duration must be 0 or greater")
    return args


def main(argv=None) -> int:
    args = _parse_args(argv)
    output = args.output or _default_output()

    pid = args.pid if args.pid is not None else os.getppid()
    root = _reading(lambda: psutil.Process(pid))
    tree = root if isinstance(root, dict) else _reading(lambda: _ProcessTree(root))
    psutil.cpu_percent(interval=None)

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
            # One interval after priming, so the first CPU reading covers a real
            # interval instead of a near-zero delta that psutil reports as 0.0.
            stop.wait(args.interval)
            while not stop.is_set():
                stream.write(json.dumps(_sample(tree, args.counters), ensure_ascii=False) + "\n")
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

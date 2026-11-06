"""Telemetry companion: monitors CPU, memory, temperature during test runs.

A lightweight, non-intrusive process that writes JSON lines to a file.
Lives under verification/telemetry/ — never under src/.
"""

from __future__ import annotations

import json
import os
import signal
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

try:
    import psutil
except ImportError:
    psutil = None


SAMPLE_INTERVAL_S = 1.0


def _read_temp_c() -> float | None:
    for path in (
        "/sys/class/thermal/thermal_zone0/temp",
        "/sys/class/hwmon/hwmon0/temp1_input",
    ):
        try:
            with open(path) as f:
                return int(f.read().strip()) / 1000.0
        except (OSError, ValueError):
            continue
    return None


def main() -> None:
    out_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("telemetry.jsonl")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    stop = {"flag": False}

    def _handle(signum: int, frame: object) -> None:
        stop["flag"] = True

    signal.signal(signal.SIGTERM, _handle)
    signal.signal(signal.SIGINT, _handle)

    proc = psutil.Process(os.getpid()) if psutil else None

    with out_path.open("w", encoding="utf-8") as f:
        while not stop["flag"]:
            record: dict[str, object] = {
                "ts": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
            }
            if psutil:
                record["cpu_pct"] = psutil.cpu_percent(interval=None)
                record["mem_pct"] = psutil.virtual_memory().percent
                if proc is not None:
                    record["rss_mb"] = round(proc.memory_info().rss / 1_048_576, 1)
            else:
                record["cpu_pct"] = None
                record["mem_pct"] = None
            record["temp_c"] = _read_temp_c()
            record["dropped"] = 0
            record["sched_ms"] = 0.0
            f.write(json.dumps(record) + "\n")
            f.flush()
            time.sleep(SAMPLE_INTERVAL_S)


if __name__ == "__main__":
    main()

"""`codeanvil telemetry` — sample host and process telemetry into a JSON-lines file.

Runs the collector in-process. stdout stays empty; the exit code is the collector's.
"""

import sys
from pathlib import Path


def cmd_telemetry(
    pid: int | None = None,
    output: Path | None = None,
    interval: float = 1.0,
    duration: float = 0.0,
    counters: Path | None = None,
) -> None:
    from codeanvil.telemetry.collector import main

    argv = ["--interval", str(interval), "--duration", str(duration)]
    if pid is not None:
        argv += ["--pid", str(pid)]
    if output is not None:
        argv += ["--output", str(output)]
    if counters is not None:
        argv += ["--counters", str(counters)]
    code = main(argv)
    if code:
        sys.exit(code)

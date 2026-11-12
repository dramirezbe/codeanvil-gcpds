"""Read append-only telemetry without turning a damaged tail into valid evidence.

The reader accepts a torn final line after a crash, reports that loss to its
caller, and preserves earlier samples. A missing file, no complete samples, or
corruption before the tail is unavailable evidence, never a successful run.
"""

from dataclasses import dataclass
import json
from pathlib import Path


class EvidenceError(ValueError):
    """Telemetry cannot support an evidence claim."""


@dataclass(frozen=True)
class TelemetryEvidence:
    records: list[dict]
    truncated_tail: bool = False


def read_jsonl(path: Path) -> TelemetryEvidence:
    """Read JSON objects, skipping only an invalid unterminated final line.

    ``truncated_tail`` must be shown alongside the readings by the consumer.
    A valid final object without a newline is still a complete sample.
    """
    path = Path(path)
    try:
        lines = path.read_bytes().splitlines(keepends=True)
    except OSError as exc:
        raise EvidenceError(f"telemetry unavailable: {path}: {exc}") from exc
    records = []
    truncated = False
    for number, line in enumerate(lines, start=1):
        try:
            record = json.loads(line.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            if number == len(lines) and not line.endswith(b"\n"):
                truncated = True
                break
            raise EvidenceError(f"corrupt telemetry at {path}:{number}") from exc
        if not isinstance(record, dict) or not record:
            raise EvidenceError(f"telemetry sample at {path}:{number} is not a nonempty object")
        records.append(record)
    if not records:
        raise EvidenceError(f"telemetry unavailable: {path} contains no complete samples")
    return TelemetryEvidence(records, truncated)

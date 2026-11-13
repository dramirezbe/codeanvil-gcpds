"""Check measurement v2 structure; specific criteria and the G2 verdict need review.

Stdlib only. Does not hash files, attest a deployment, require an oracle or
evaluate a measurement criterion. Historical v1 evidence is left unchanged.
"""

import argparse
from datetime import datetime
import json
import math
from pathlib import Path
import sys


class EvidenceError(ValueError):
    """A measurement record is malformed or incomplete."""


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise EvidenceError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _finite(value):
    if isinstance(value, float) and not math.isfinite(value):
        raise EvidenceError("numeric values must be finite")
    if isinstance(value, dict):
        for child in value.values():
            _finite(child)
    elif isinstance(value, list):
        for child in value:
            _finite(child)


def _text(record, key):
    if not isinstance(record.get(key), str) or not record[key].strip():
        raise EvidenceError(f"{key} must be nonempty text")


def validate(path):
    """Return a structurally valid record without judging its claimed results."""
    record = json.loads(Path(path).read_text(encoding="utf-8"), object_pairs_hook=_object)
    if not isinstance(record, dict) or type(record.get("schema_version")) is not int or record["schema_version"] != 2:
        raise EvidenceError("expected measurement schema_version 2; historical evidence is not rewritten")
    _finite(record)
    for key in ("cycle", "run_id", "target", "command", "started_at", "finished_at"):
        _text(record, key)
    if record.get("stage") not in ("S2", "G2"):
        raise EvidenceError("stage must be S2 or G2")
    if type(record.get("iteration")) is not int or record["iteration"] < 1:
        raise EvidenceError("iteration must be a positive integer")
    if type(record.get("exit_code")) is not int:
        raise EvidenceError("exit_code must be an integer")
    for key in ("started_at", "finished_at"):
        stamp = datetime.fromisoformat(record[key].replace("Z", "+00:00"))
        if stamp.utcoffset() is None:
            raise EvidenceError(f"{key} requires a timezone")
    measurements = record.get("measurements")
    if not isinstance(measurements, list):
        raise EvidenceError("measurements must be a list")
    if "error" in record:
        _text(record, "error")
    if not measurements:
        _text(record, "error")
        if record["exit_code"] == 0:
            raise EvidenceError("a run with no measurements must report a nonzero exit_code")
    for item in measurements:
        if not isinstance(item, dict):
            raise EvidenceError("each measurement must be an object")
        for key in ("requirement_id", "metric", "criterion"):
            _text(item, key)
        if type(item.get("value")) not in (int, float, str, bool):
            raise EvidenceError("value must be a number, text or boolean")
        if item.get("result") not in ("pass", "fail", "inconclusive"):
            raise EvidenceError("result must be pass, fail or inconclusive")
        if "unit" in item and not isinstance(item["unit"], str):
            raise EvidenceError("unit must be text")
    return record


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", type=Path)
    args = parser.parse_args(argv)
    try:
        result = validate(args.record)
    except (OSError, ValueError, TypeError) as exc:
        print(f"measurement record invalid: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"status": "valid record", "run_id": result["run_id"],
                      "results": [item["result"] for item in result["measurements"]],
                      "verdict": "human review required"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())

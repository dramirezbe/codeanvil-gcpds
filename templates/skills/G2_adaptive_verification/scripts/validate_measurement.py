"""Validate captured VL-2 records; validity never establishes a human G2 verdict.

Stdlib only, usable through ``codeanvil python`` in a scaffolded project. The
small schema interpreter implements exactly the keywords used by the bundled
schema; it is not a general JSON Schema implementation.
"""

import argparse
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path
import re
import sys

SCHEMA = Path(__file__).resolve().parents[1] / "references" / "measurement.schema.json"


class EvidenceError(ValueError):
    """A record cannot support a VL-2 evidence claim."""


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise EvidenceError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"), object_pairs_hook=_object)


def _time(value):
    stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if stamp.utcoffset() is None:
        raise EvidenceError("timestamps require a timezone")
    return stamp


def _check(value, schema, at="record"):
    types = {"object": dict, "array": list, "string": str}
    kind = schema.get("type")
    if kind == "number":
        if type(value) not in (int, float) or not math.isfinite(value):
            raise EvidenceError(f"{at}: expected a finite number")
    elif kind and not isinstance(value, types[kind]):
        raise EvidenceError(f"{at}: expected {kind}")
    if "const" in schema and (type(value) is not type(schema["const"]) or value != schema["const"]):
        raise EvidenceError(f"{at}: expected {schema['const']!r}")
    if "enum" in schema and value not in schema["enum"]:
        raise EvidenceError(f"{at}: unsupported value")
    if kind == "object":
        properties = schema.get("properties", {})
        missing = set(schema.get("required", [])) - value.keys()
        extra = value.keys() - properties.keys()
        if missing or (schema.get("additionalProperties") is False and extra):
            raise EvidenceError(f"{at}: missing {sorted(missing)}, unexpected {sorted(extra)}")
        for key, child in value.items():
            _check(child, properties[key], f"{at}.{key}")
    elif kind == "array":
        if len(value) < schema.get("minItems", 0):
            raise EvidenceError(f"{at}: no evidence items")
        for index, child in enumerate(value):
            _check(child, schema["items"], f"{at}[{index}]")
    elif kind == "string":
        if len(value.strip()) < schema.get("minLength", 0):
            raise EvidenceError(f"{at}: empty text")
        if "pattern" in schema and not re.fullmatch(schema["pattern"], value):
            raise EvidenceError(f"{at}: invalid identifier or digest")
        if schema.get("format") == "date-time":
            _time(value)
    elif kind == "number" and value < schema.get("minimum", -math.inf):
        raise EvidenceError(f"{at}: below minimum")


def _inside(root, relative):
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts or "\\" in relative:
        raise EvidenceError(f"evidence path must stay inside the run directory: {relative}")
    resolved = (root / path).resolve(strict=True)
    if root not in resolved.parents or not resolved.is_file():
        raise EvidenceError(f"evidence path escapes the run directory: {relative}")
    return resolved


def validate(path, *, target, run_id, deployment_sha256, codeanvil_version, not_before):
    """Check schema, provenance, captures and recorded scalar tolerance outcomes.

    Expected provenance comes from S2/SDD and this fresh run, never the record
    itself. Calibration, correction math and GT tolerance references still need
    review; this function does not provide an oracle or a metrological verdict.
    """
    path = Path(path).resolve(strict=True)
    record = _load(path)
    _check(record, _load(SCHEMA))
    for actual, expected, label in (
        (record["target"]["name"], target, "target"),
        (record["run_id"], run_id, "run_id"),
        (record["deployment_sha256"], deployment_sha256, "deployment"),
        (record["target"]["codeanvil_version"], codeanvil_version, "CodeAnvil version"),
    ):
        if actual != expected:
            raise EvidenceError(f"{label} does not match the expected fresh run")
    started = _time(record["started_at"])
    if started < _time(not_before):
        raise EvidenceError("capture predates this G2 request")
    if _time(record["finished_at"]) < started:
        raise EvidenceError("finished_at precedes started_at")
    seen = set()
    for capture in record["captures"]:
        captured = _inside(path.parent, capture["path"])
        if captured == path or captured in seen or not captured.stat().st_size:
            raise EvidenceError("capture must be distinct, nonempty, and not the measurement record")
        seen.add(captured)
        digest = hashlib.sha256()
        with captured.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        if digest.hexdigest() != capture["sha256"]:
            raise EvidenceError(f"capture digest mismatch: {capture['path']}")
    telemetry = _inside(path.parent, record["telemetry_path"])
    if telemetry == path or telemetry in seen or not telemetry.stat().st_size:
        raise EvidenceError("telemetry must be a separate, nonempty file")
    for item in record["measurements"]:
        if item["lower"] > item["upper"]:
            raise EvidenceError("reversed tolerance bounds")
        observed = "pass" if item["lower"] <= item["corrected"] <= item["upper"] else "fail"
        if item["result"] != observed:
            raise EvidenceError(f"inconsistent recorded result: {item['requirement_id']}")
    return record


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", type=Path)
    for name in ("target", "run-id", "deployment-sha256", "codeanvil-version", "not-before"):
        parser.add_argument(f"--{name}", required=True)
    args = parser.parse_args(argv)
    try:
        result = validate(args.record, target=args.target, run_id=args.run_id,
                          deployment_sha256=args.deployment_sha256,
                          codeanvil_version=args.codeanvil_version, not_before=args.not_before)
    except (EvidenceError, OSError, ValueError, TypeError) as exc:
        print(f"measurement evidence invalid: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"status": "valid record", "run_id": result["run_id"],
                      "results": [item["result"] for item in result["measurements"]],
                      "verdict": "human review required"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())

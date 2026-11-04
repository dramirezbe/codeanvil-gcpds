#!/usr/bin/env python3
"""ControlRegistry: validate audit controls are declarative, uniquely identified and typed.

Rules enforced
  R1  Free-text executable expressions are PROHIBITED (no expression/script/eval-style
      keys; string values restricted to a safe allowlist; code/shell/template patterns rejected).
  R2  Control IDs are unique and match ^[A-Z][A-Z0-9_]{1,15}-\\d{2,4}$.
  R3  Every parameter is typed: {"type": ..., "value": ...} with a known type and a conforming value.
  R4  Check operators come from a closed set (no free-form conditions).

  control_registry.py --registry controls.json
Exit codes: 0 PASS, 1 FAIL, 2 usage/IO error.
"""
import argparse, json, re, sys
from pathlib import Path
from _common import report

ID_RE = re.compile(r"^[A-Z][A-Z0-9_]{1,15}-\d{2,4}$")
SAFE_STR = re.compile(r"^[\w .:/\-@]{0,200}$")
SHA_RE = re.compile(r"^[0-9a-f]{64}$")
REL_RE = re.compile(r"^(?!/)(?![A-Za-z]:)(?!.*\.\.)[\w.\-/]+$")
FORBIDDEN_KEYS = {"expression", "expr", "script", "code", "eval", "exec", "command", "cmd",
                  "shell", "condition", "predicate", "formula", "lambda", "query", "template"}
FORBIDDEN_PATTERNS = [r"\beval\s*\(", r"\bexec\s*\(", r"\blambda\b", r"__\w+__", r"\bimport\b",
                      r"\bos\.", r"\bsubprocess\b", r"\$\{", r"\$\(", r"\{\{", r"`", r"[;|&<>]",
                      r"\brm\s+-", r"\bcurl\b", r"\bwget\b"]
FORBID_RE = re.compile("|".join(FORBIDDEN_PATTERNS), re.I)
OPERATORS = {"eq", "ne", "lt", "lte", "gt", "gte", "in", "not_in", "matches_enum",
             "sha256_equals", "bytes_equals", "exists", "bound"}
TYPES = {"string", "integer", "number", "boolean", "enum", "path", "sha256", "list"}


def _scan_text(v, where, f, cid):
    """R1 deep scan of any string value."""
    if isinstance(v, str) and FORBID_RE.search(v):
        f.append({"control": cid, "code": "EXECUTABLE_EXPRESSION", "severity": "critical",
                  "where": where, "detail": "string matches a code/shell/template pattern"})


def _walk(obj, where, f, cid):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k.lower() in FORBIDDEN_KEYS:
                f.append({"control": cid, "code": "FORBIDDEN_KEY", "severity": "critical",
                          "where": f"{where}.{k}", "detail": "free-text executable field not allowed"})
            _walk(v, f"{where}.{k}", f, cid)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            _walk(v, f"{where}[{i}]", f, cid)
    else:
        _scan_text(obj, where, f, cid)


def _typed_ok(t, spec):
    v = spec.get("value")
    if t == "string":  return isinstance(v, str) and bool(SAFE_STR.match(v))
    if t == "integer": return isinstance(v, int) and not isinstance(v, bool)
    if t == "number":  return isinstance(v, (int, float)) and not isinstance(v, bool)
    if t == "boolean": return isinstance(v, bool)
    if t == "enum":    return isinstance(spec.get("enum"), list) and v in spec["enum"]
    if t == "path":    return isinstance(v, str) and bool(REL_RE.match(v))
    if t == "sha256":  return isinstance(v, str) and bool(SHA_RE.match(v))
    if t == "list":    return isinstance(v, list) and all(isinstance(x, (str, int, float)) for x in v)
    return False


def validate(reg):
    f, seen = [], {}
    controls = reg.get("controls")
    if not isinstance(controls, list) or not controls:
        return [{"code": "EMPTY_REGISTRY", "severity": "critical"}]
    for i, c in enumerate(controls):
        cid = c.get("id", f"<index {i}>")
        if not isinstance(c.get("id"), str) or not ID_RE.match(c["id"]):
            f.append({"control": cid, "code": "BAD_ID", "severity": "critical",
                      "detail": f"must match {ID_RE.pattern}"})
        if cid in seen:
            f.append({"control": cid, "code": "DUPLICATE_ID", "severity": "critical",
                      "detail": f"also at index {seen[cid]}"})
        seen.setdefault(cid, i)
        if c.get("check", {}).get("operator") not in OPERATORS:
            f.append({"control": cid, "code": "BAD_OPERATOR", "severity": "critical",
                      "detail": f"operator must be one of {sorted(OPERATORS)}"})
        params = c.get("params", {})
        if not isinstance(params, dict):
            f.append({"control": cid, "code": "PARAMS_NOT_OBJECT", "severity": "critical"}); params = {}
        for name, spec in params.items():
            t = spec.get("type") if isinstance(spec, dict) else None
            if t not in TYPES:
                f.append({"control": cid, "code": "UNTYPED_PARAM", "severity": "critical",
                          "where": f"params.{name}", "detail": f"type must be one of {sorted(TYPES)}"})
            elif not _typed_ok(t, spec):
                f.append({"control": cid, "code": "TYPE_MISMATCH", "severity": "critical",
                          "where": f"params.{name}", "detail": f"value does not conform to type '{t}'"})
        # R1: scan everything except the human-readable description/title prose keys
        body = {k: v for k, v in c.items() if k not in ("description", "title")}
        _walk(body, "control", f, cid)
        for k in ("description", "title"):
            if isinstance(c.get(k), str) and len(c[k]) > 500:
                f.append({"control": cid, "code": "PROSE_TOO_LONG", "severity": "warning", "where": k})
    return f


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--registry", required=True)
    a = ap.parse_args()
    try:
        reg = json.loads(Path(a.registry).read_text())
    except (OSError, json.JSONDecodeError) as e:
        print(f"cannot read registry: {e}", file=sys.stderr); sys.exit(2)
    f = validate(reg)
    failed = any(x["severity"] == "critical" for x in f)
    print(json.dumps(report("FAIL" if failed else "PASS", f,
                            controls_checked=len(reg.get("controls", []))), indent=2))
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()

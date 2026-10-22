#!/usr/bin/env python3
"""SourceSnapshot: seal and verify original data (paths, byte lengths, SHA-256).

  snapshot --root . --include 'data/**' --out .codeanvil/custody/snapshot.json
  verify   --root . --snapshot .codeanvil/custody/snapshot.json [--expect-digest HEX] [--strict]

Exit codes: 0 PASS, 1 FAIL (immutability violated), 2 usage/IO error.
"""
import argparse, json, sys
from pathlib import Path
from _common import PathError, canonical, hash_file, now_utc, report, safe_rel, sha256_bytes

DEFAULT_EXCLUDE = (".git/", "__pycache__/", ".codeanvil/")


def _excluded(rel, extra):
    return any(rel.startswith(p) or f"/{p}" in f"/{rel}" for p in DEFAULT_EXCLUDE + tuple(extra))


def _entry_digest(entries):
    return sha256_bytes(canonical(entries))


def take(root: Path, includes, excludes):
    entries, problems = [], []
    seen = set()
    for pattern in includes:
        if pattern.endswith("**"):          # Path.glob('dir/**') yields only directories
            pattern += "/*"
        for p in sorted(root.glob(pattern)):
            if not p.is_file() and not p.is_symlink():
                continue
            rel = p.relative_to(root).as_posix()
            if rel in seen or _excluded(rel, excludes):
                continue
            seen.add(rel)
            try:
                if p.is_symlink():
                    raise PathError(f"symlink not allowed in sealed set: {rel}")
                full = safe_rel(root, rel)
                sha, n = hash_file(full)
                st = full.stat().st_size
                if n != st:
                    problems.append({"path": rel, "code": "UNSTABLE_READ",
                                     "detail": f"stat={st} read={n}; file changed while hashing"})
                entries.append({"path": rel, "bytes": n, "sha256": sha})
            except (PathError, OSError) as e:
                problems.append({"path": rel, "code": "UNREADABLE", "detail": str(e)})
    entries.sort(key=lambda e: e["path"])
    return entries, problems


def cmd_snapshot(a):
    root = Path(a.root).resolve()
    entries, problems = take(root, a.include, a.exclude)
    if not entries and not problems:
        problems.append({"code": "EMPTY_SEAL", "detail": "include patterns matched no files; refusing to seal nothing"})
    if problems:
        print(json.dumps(report("FAIL", problems), indent=2))
        return 1
    doc = {"schema": "source-snapshot/1", "created_utc": now_utc(), "root_label": root.name,
           "algorithm": "sha256", "file_count": len(entries),
           "total_bytes": sum(e["bytes"] for e in entries),
           "includes": a.include, "excludes": a.exclude,
           "entries": entries, "manifest_digest": _entry_digest(entries)}
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists() and not a.force:
        print(f"refusing to overwrite sealed snapshot {out} (use --force)", file=sys.stderr)
        return 2
    out.write_text(json.dumps(doc, indent=2) + "\n")
    print(json.dumps({"status": "SEALED", "files": len(entries), "total_bytes": doc["total_bytes"],
                      "manifest_digest": doc["manifest_digest"], "snapshot": str(out)}, indent=2))
    return 0


def cmd_verify(a):
    root = Path(a.root).resolve()
    try:
        snap = json.loads(Path(a.snapshot).read_text())
    except (OSError, json.JSONDecodeError) as e:
        print(f"cannot read snapshot: {e}", file=sys.stderr)
        return 2
    f = []
    if _entry_digest(snap["entries"]) != snap.get("manifest_digest"):
        f.append({"code": "MANIFEST_TAMPERED", "severity": "critical",
                  "detail": "entries do not match manifest_digest"})
    if a.expect_digest and a.expect_digest != snap.get("manifest_digest"):
        f.append({"code": "MANIFEST_DIGEST_MISMATCH", "severity": "critical",
                  "detail": "manifest_digest differs from externally pinned digest"})
    sealed = set()
    for e in snap["entries"]:
        rel = e["path"]; sealed.add(rel)
        try:
            full = safe_rel(root, rel)
        except PathError as ex:
            f.append({"path": rel, "code": "BAD_PATH", "severity": "critical", "detail": str(ex)}); continue
        if not full.is_file():
            f.append({"path": rel, "code": "MISSING", "severity": "critical"}); continue
        sha, n = hash_file(full)
        if n != e["bytes"]:
            f.append({"path": rel, "code": "LENGTH_CHANGED", "severity": "critical",
                      "expected": e["bytes"], "actual": n})
        if sha != e["sha256"]:
            f.append({"path": rel, "code": "DIGEST_CHANGED", "severity": "critical",
                      "expected": e["sha256"], "actual": sha})
    if not snap["entries"]:
        f.append({"code": "EMPTY_SNAPSHOT", "severity": "critical", "detail": "snapshot seals no files"})
    current, _ = take(root, snap.get("includes", ["**/*"]), snap.get("excludes", []))
    for e in current:
        if e["path"] not in sealed:
            f.append({"path": e["path"], "code": "UNTRACKED_ADDED",
                      "severity": "critical" if a.strict else "warning"})
    failed = any(x["severity"] == "critical" for x in f)
    print(json.dumps(report("FAIL" if failed else "PASS", f, files_checked=len(sealed),
                            manifest_digest=snap.get("manifest_digest")), indent=2))
    return 1 if failed else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("snapshot")
    s.add_argument("--root", default="."); s.add_argument("--include", nargs="+", default=["**/*"])
    s.add_argument("--exclude", nargs="*", default=[]); s.add_argument("--out", required=True)
    s.add_argument("--force", action="store_true"); s.set_defaults(fn=cmd_snapshot)
    v = sub.add_parser("verify")
    v.add_argument("--root", default="."); v.add_argument("--snapshot", required=True)
    v.add_argument("--expect-digest"); v.add_argument("--strict", action="store_true")
    v.set_defaults(fn=cmd_verify)
    a = ap.parse_args()
    sys.exit(a.fn(a))


if __name__ == "__main__":
    main()

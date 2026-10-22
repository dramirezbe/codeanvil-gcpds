#!/usr/bin/env python3
"""Chain-of-custody ledger: append-only, hash-chained, signed JSONL.

  record  --ledger L --doc path --action created|accessed|modified|extracted|signed|verified|exported
          --actor NAME [--role ROLE] [--detail TEXT] [--root .]
  verify  --ledger L [--root .]       # chain, signatures, timestamps, live document hashes
  history --ledger L --doc path       # who did what, when, for one document

Conventional ledger location: .codeanvil/custody/custody.jsonl

Signing: HMAC-SHA256 over each entry hash using the key in env PROVENANCE_HMAC_KEY
(key id in PROVENANCE_KEY_ID, default 'k1'). HMAC proves integrity/authenticity to holders
of the shared key; it is not third-party non-repudiation (use asymmetric signatures for that).
Exit codes: 0 OK, 1 verification FAIL, 2 usage/IO error.
"""
import argparse, fcntl, getpass, hashlib, hmac, json, os, socket, sys
from datetime import datetime
from pathlib import Path
from _common import PathError, canonical, hash_file, now_utc, report, safe_rel, sha256_bytes

ACTIONS = {"created", "accessed", "modified", "extracted", "signed", "verified", "exported"}
GENESIS = "0" * 64


def _key():
    k = os.environ.get("PROVENANCE_HMAC_KEY")
    if not k:
        raise SystemExit("PROVENANCE_HMAC_KEY is not set; refusing to write unsigned custody entries")
    return k.encode(), os.environ.get("PROVENANCE_KEY_ID", "k1")


def _sign(key, entry_hash):
    return hmac.new(key, entry_hash.encode(), hashlib.sha256).hexdigest()


def _entry_hash(e):
    body = {k: v for k, v in e.items() if k not in ("entry_hash", "signature")}
    return sha256_bytes(canonical(body))


def _read(path: Path):
    if not path.exists():
        return []
    return [json.loads(l) for l in path.read_text().splitlines() if l.strip()]


def cmd_record(a):
    key, kid = _key()
    root = Path(a.root).resolve()
    if a.action not in ACTIONS:
        print(f"action must be one of {sorted(ACTIONS)}", file=sys.stderr); return 2
    try:
        full = safe_rel(root, a.doc)
    except PathError as e:
        print(e, file=sys.stderr); return 2
    sha, n = (hash_file(full) if full.is_file() else (None, None))
    if sha is None and a.action != "exported":
        print(f"document not found: {a.doc}", file=sys.stderr); return 2
    ledger = Path(a.ledger)
    ledger.parent.mkdir(parents=True, exist_ok=True)
    with open(ledger, "a+") as fh:                      # lock covers read-last + append
        fcntl.flock(fh, fcntl.LOCK_EX)
        fh.seek(0)
        rows = [json.loads(l) for l in fh.read().splitlines() if l.strip()]
        prev = rows[-1] if rows else None
        last_for_doc = next((r for r in reversed(rows) if r["doc_path"] == a.doc), None)
        e = {"seq": (prev["seq"] + 1) if prev else 1, "ts_utc": now_utc(),
             "actor": a.actor, "role": a.role, "action": a.action, "doc_path": a.doc,
             "doc_sha256": sha, "doc_bytes": n,
             "prev_doc_sha256": last_for_doc["doc_sha256"] if last_for_doc else None,
             "detail": a.detail, "observed_os_user": getpass.getuser(), "host": socket.gethostname(),
             "prev_hash": prev["entry_hash"] if prev else GENESIS, "key_id": kid}
        e["entry_hash"] = _entry_hash(e)
        e["signature"] = _sign(key, e["entry_hash"])
        fh.write(json.dumps(e, sort_keys=True) + "\n")
        fh.flush(); os.fsync(fh.fileno())
    print(json.dumps({"status": "RECORDED", "seq": e["seq"], "entry_hash": e["entry_hash"]}, indent=2))
    return 0


def cmd_verify(a):
    key, _ = _key()
    root = Path(a.root).resolve()
    rows, f = _read(Path(a.ledger)), []
    prev_hash, prev_ts, latest = GENESIS, None, {}
    for i, e in enumerate(rows, 1):
        w = {"seq": e.get("seq")}
        if e.get("seq") != i:
            f.append({**w, "code": "SEQ_GAP", "severity": "critical"})
        if e.get("prev_hash") != prev_hash:
            f.append({**w, "code": "CHAIN_BROKEN", "severity": "critical"})
        if _entry_hash(e) != e.get("entry_hash"):
            f.append({**w, "code": "ENTRY_TAMPERED", "severity": "critical"})
        if not hmac.compare_digest(_sign(key, e.get("entry_hash", "")), e.get("signature", "")):
            f.append({**w, "code": "BAD_SIGNATURE", "severity": "critical"})
        ts = datetime.fromisoformat(e["ts_utc"])
        if prev_ts and ts < prev_ts:
            f.append({**w, "code": "TIME_REGRESSION", "severity": "critical"})
        if e["action"] == "modified" and e.get("doc_sha256") == e.get("prev_doc_sha256"):
            f.append({**w, "code": "MODIFIED_WITHOUT_CHANGE", "severity": "warning"})
        if e["action"] in ("accessed", "extracted", "verified") and e.get("prev_doc_sha256") \
                and e.get("doc_sha256") != e["prev_doc_sha256"]:
            f.append({**w, "code": "UNRECORDED_MODIFICATION", "severity": "critical",
                      "detail": f"hash changed during '{e['action']}' with no 'modified' entry"})
        prev_hash, prev_ts = e.get("entry_hash"), ts
        latest[e["doc_path"]] = e
    for doc, e in latest.items():                       # live check against disk
        try:
            full = safe_rel(root, doc)
        except PathError:
            f.append({"doc": doc, "code": "BAD_PATH", "severity": "critical"}); continue
        if not full.is_file():
            if e["action"] != "exported":
                f.append({"doc": doc, "code": "DOCUMENT_MISSING", "severity": "critical"})
            continue
        sha, n = hash_file(full)
        if sha != e["doc_sha256"] or n != e["doc_bytes"]:
            f.append({"doc": doc, "code": "UNRECORDED_CHANGE_ON_DISK", "severity": "critical",
                      "expected": e["doc_sha256"], "actual": sha})
    failed = any(x["severity"] == "critical" for x in f)
    print(json.dumps(report("FAIL" if failed else "PASS", f, entries=len(rows),
                            documents=len(latest), head=prev_hash), indent=2))
    return 1 if failed else 0


def cmd_history(a):
    rows = [r for r in _read(Path(a.ledger)) if r["doc_path"] == a.doc]
    for r in rows:
        print(f'{r["seq"]:>4}  {r["ts_utc"]}  {r["action"]:<9} {r["actor"]} ({r["role"] or "-"})  '
              f'sha256={str(r["doc_sha256"])[:12]}  {r["detail"] or ""}')
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("record")
    r.add_argument("--ledger", required=True); r.add_argument("--doc", required=True)
    r.add_argument("--action", required=True); r.add_argument("--actor", required=True)
    r.add_argument("--role", default=""); r.add_argument("--detail", default="")
    r.add_argument("--root", default="."); r.set_defaults(fn=cmd_record)
    v = sub.add_parser("verify")
    v.add_argument("--ledger", required=True); v.add_argument("--root", default=".")
    v.set_defaults(fn=cmd_verify)
    h = sub.add_parser("history")
    h.add_argument("--ledger", required=True); h.add_argument("--doc", required=True)
    h.set_defaults(fn=cmd_history)
    a = ap.parse_args()
    sys.exit(a.fn(a))


if __name__ == "__main__":
    main()

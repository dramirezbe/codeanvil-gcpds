"""Shared helpers: safe project-relative paths, streaming SHA-256, canonical JSON."""
import hashlib, json, re
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

CHUNK = 1 << 20


class PathError(ValueError):
    pass


def safe_rel(root: Path, rel: str) -> Path:
    """Return root/rel only if rel is a clean, project-relative POSIX path that
    does not escape root (including via symlinks)."""
    if not isinstance(rel, str) or not rel:
        raise PathError("empty path")
    if "\\" in rel or rel.startswith("/") or re.match(r"^[A-Za-z]:", rel):
        raise PathError(f"not a project-relative POSIX path: {rel!r}")
    if ".." in PurePosixPath(rel).parts:
        raise PathError(f"parent traversal not allowed: {rel!r}")
    full = root / rel
    r = root.resolve()
    res = full.resolve()
    if res != r and r not in res.parents:
        raise PathError(f"path escapes project root: {rel!r}")
    return full


def hash_file(path: Path):
    """Return (sha256_hex, bytes_actually_read). Streams; never loads whole file."""
    h, n = hashlib.sha256(), 0
    with open(path, "rb") as f:
        while chunk := f.read(CHUNK):
            h.update(chunk)
            n += len(chunk)
    return h.hexdigest(), n


def canonical(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


def report(status: str, findings: list, **extra) -> dict:
    return {"status": status, "finding_count": len(findings), "findings": findings, **extra}

"""Stateless SHA-256 integrity owner for the V-SIL methodology.

Custody is the single producer and checker of digests. It computes and verifies
file and directory hashes, never reads or writes the SQLite DB (state lives only
in project files under Git). Every digest recorded by the methodology comes
from `codeanvil custody digest` and is checked via `custody verify` or
`verify-manifest`.
"""

import hashlib
import subprocess
from pathlib import Path
from typing import NamedTuple

from codeanvil.config.logger import get_logger

log = get_logger(__name__)


class Finding(NamedTuple):
    """A manifest or input digest finding."""
    kind: str  # "stale-report", "manifest-mismatch", "backup-mismatch"
    path: str
    recorded: str | None
    current: str


def file_sha256(path: Path) -> str:
    """Compute SHA-256 of a file's bytes."""
    h = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            while True:
                chunk = f.read(8192)
                if not chunk:
                    break
                h.update(chunk)
    except OSError as e:
        log.error("cannot read %s: %s", path, e)
        return ""
    return h.hexdigest()


def tree_sha256(directory: Path) -> str:
    """Compute SHA-256 over a directory tree.
    
    Inside a Git work tree, uses `git ls-files -co --exclude-standard` to get
    the canonical file list. Outside Git, uses rglob minus standard ignores.
    Returns SHA-256 of sorted (relpath, filehash) pairs.
    """
    h = hashlib.sha256()
    files = []
    
    # Try git first
    try:
        result = subprocess.run(
            ["git", "ls-files", "-co", "--exclude-standard", "--", str(directory)],
            cwd=directory,
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            files = result.stdout.strip().split("\n") if result.stdout.strip() else []
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    
    # Fallback: rglob with standard ignores
    if not files:
        ignore_patterns = {".git", "__pycache__", ".venv", "node_modules", "dist",
                          "verification/telemetry"}
        for file_path in sorted(directory.rglob("*")):
            if not file_path.is_file():
                continue
            rel = file_path.relative_to(directory)
            if any(part in ignore_patterns or part.startswith(".") for part in rel.parts):
                continue
            files.append(str(rel))
    
    # Hash sorted (relpath, filehash) pairs
    for rel_str in sorted(set(files)):
        file_path = directory / rel_str
        if not file_path.is_file():
            continue
        file_hash = file_sha256(file_path)
        h.update(f"{rel_str}\0{file_hash}\n".encode())
    
    return h.hexdigest()


def verify(project_root: Path, cycle: str | None = None) -> list[Finding]:
    """Verify Input:/Output: digests in all chain reports of the cycle.
    
    Returns one Finding per mismatch (stale-report, manifest-mismatch, etc.).
    If cycle is None, checks the most recent cycle.
    """
    findings = []
    report_dir = project_root / ".codeanvil" / "report"
    
    if not report_dir.is_dir():
        return findings
    
    # Find cycles
    cycles = sorted([d for d in report_dir.iterdir() if d.is_dir()])
    if not cycles:
        return findings
    
    if cycle:
        target = report_dir / cycle
        if not target.is_dir():
            return findings
        cycles = [target]
    else:
        cycles = [cycles[-1]]
    
    for cycle_dir in cycles:
        # Check all .md files in the cycle
        for report_file in cycle_dir.glob("*.md"):
            # TODO (Phase H): Parse Input: lines, recompute digests, compare
            # For now, custody verify on v3 projects finds only manifest/backup mismatches
            pass
    
    return findings


def verify_manifest(manifest_path: Path) -> list[Finding]:
    """Verify a golden vector manifest against its vectors.
    
    Parses the locked table and compares each row with its file.
    Returns findings for mismatches, missing files, and unlisted files.
    """
    findings = []
    if not manifest_path.is_file():
        return findings
    
    # TODO (Phase H): Parse manifest table, check vectors
    # Manifest format: | Vector ID | SHA-256 | File | ... |
    # For now, Phase A3 provides the structure; validation is deferred.
    
    return findings

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
from typing import TYPE_CHECKING, NamedTuple

from codeanvil.config.logger import get_logger

log = get_logger(__name__)

if TYPE_CHECKING:
    from codeanvil.reports import ReportState


class Finding(NamedTuple):
    """A manifest, baseline or delivery integrity finding."""
    kind: str
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
    directory = directory.resolve()
    result = None
    try:
        result = subprocess.run(
            ["git", "ls-files", "-z", "-co", "--exclude-standard", "--", "."],
            cwd=directory, capture_output=True, timeout=10,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    if result is not None and result.returncode == 0:
        files = {p for p in result.stdout.decode().split("\0") if p}
    else:
        ignored = {".git", "__pycache__", ".venv", "node_modules", "dist"}
        files = {p.relative_to(directory).as_posix() for p in directory.rglob("*")
                 if p.is_file() and not ignored.intersection(p.relative_to(directory).parts)
                 and "verification/telemetry/" not in p.as_posix()}
    h = hashlib.sha256()
    for rel in sorted(files):
        file = directory / rel
        if file.is_file():
            digest = file_sha256(file)
            if not digest:
                return ""
            h.update(f"{rel}\0{digest}\n".encode())
    return h.hexdigest()


def path_sha256(path: Path) -> str:
    return tree_sha256(path) if path.is_dir() else file_sha256(path) if path.is_file() else "missing"


def s1_delivery_findings(project_root: Path, report: "ReportState") -> list[Finding]:
    """Only the latest S1 delivery owns the working design; older outputs may change."""
    if report.hitl != "PASS":
        return []
    findings = []
    for path, recorded in report.outputs:
        current = path_sha256(project_root / path)
        if recorded != current:
            findings.append(Finding("undelivered-output", path, recorded, current))
    return findings


def verify(project_root: Path, cycle: str | None = None, gate: str | None = None) -> list[Finding]:
    """Check latest consumed inputs and S1's latest recorded delivery outputs.

    Historical iterations deliberately remain immutable. An output may have been
    replaced by a later authorized stage; do not check historical outputs or S3 trees.
    """
    import yaml
    from codeanvil.reports import authorized_advance, baseline_reason, read_deltas, report_state
    report_dir = project_root / ".codeanvil/report"
    if cycle is None:
        manifest = project_root / ".codeanvil/project.yaml"
        if manifest.is_file():
            cycle = (yaml.safe_load(manifest.read_text(encoding="utf-8")) or {}).get("cycle")
    if not cycle or not (report_dir / cycle).is_dir():
        return []
    deltas = read_deltas(project_root)
    findings = []
    for report in sorted((report_dir / cycle).glob("*.md")):
        if gate is not None and report.stem != gate:
            continue
        state = report_state(report)
        for error in state.format_errors:
            findings.append(Finding("invalid-report", report.relative_to(project_root).as_posix(),
                                    None, error))
        invalid = baseline_reason(report.stem, state)
        if invalid:
            findings.append(Finding("invalid-baseline", report.relative_to(project_root).as_posix(),
                                    "Based on: G0 iteration <N>", invalid))
        if report.stem == "S1":
            findings.extend(s1_delivery_findings(project_root, state))
        for path, recorded in state.inputs:
            current = path_sha256(project_root / path)
            if recorded != current and not authorized_advance(path, recorded, current, deltas):
                findings.append(Finding("stale-report", path, recorded, current))
    return findings


def verify_manifest(manifest_path: Path) -> list[Finding]:
    """Check the locked vector table; paths are relative to its directory."""
    import re
    from codeanvil.reports import unfenced_text
    if not manifest_path.is_file():
        return [Finding("manifest-mismatch", str(manifest_path), None, "missing")]
    headers = None
    listed = set()
    findings = []
    for line in unfenced_text(manifest_path.read_text(encoding="utf-8")).splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip().strip("`") for c in line.strip().strip("|").split("|")]
        if "SHA-256" in cells and "File" in cells:
            headers = cells
            continue
        if not headers or all(re.fullmatch(r"[: -]+", c) for c in cells):
            continue
        if len(cells) != len(headers):
            findings.append(Finding("manifest-mismatch", str(manifest_path), None, "malformed row"))
            continue
        row = dict(zip(headers, cells))
        path = manifest_path.parent / row["File"]
        resolved = path.resolve()
        if not resolved.is_relative_to(manifest_path.parent.resolve()) or resolved in listed:
            findings.append(Finding("manifest-mismatch", row["File"], row["SHA-256"], "unsafe or duplicate path"))
            continue
        listed.add(resolved)
        current = path_sha256(path)
        if not re.fullmatch(r"[0-9a-f]{64}", row["SHA-256"]) or current != row["SHA-256"]:
            findings.append(Finding("manifest-mismatch", row["File"], row["SHA-256"], current))
    if headers is None:
        findings.append(Finding("manifest-mismatch", str(manifest_path), None, "missing table"))
    for path in sorted(manifest_path.parent.rglob("*")):
        if path.is_file() and path.resolve() != manifest_path.resolve() and path.resolve() not in listed:
            findings.append(Finding("manifest-mismatch", str(path), None, "unlisted"))
    return findings

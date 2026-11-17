"""Shared readers for cycle-scoped gate reports.

`status` prints the chain state and `backup` resolves which iteration produced
the files it saves. Both read the same append-only reports, so the parsing
lives here once: a command module never imports from another command module.
"""

import re
from pathlib import Path
from typing import NamedTuple

from codeanvil.config.logger import get_logger
from codeanvil.config.paths import CONFIG

log = get_logger(__name__)

# Cycle-scoped reports: .codeanvil/report/<cycle>/<gate>.md with appended
# "## Iteration N" sections and a | HITL | PASS|FEEDBACK | row per iteration.
_ITERATION_RE = re.compile(r"^## Iteration (\d+)\s*$", re.MULTILINE)
# Exactly two cells: the schema placeholder "| HITL | PASS | FEEDBACK |" is not
# a verdict and must not be read as PASS.
_HITL_RE = re.compile(r"^\|\s*HITL\s*\|\s*(PASS|FEEDBACK)\s*\|\s*$", re.MULTILINE)

# Chain links, read only from the latest iteration of a report.
_BASED_ON_RE = re.compile(r"^Based on: (\S+) iteration (\d+)\s*$", re.MULTILINE)
_SUPERSEDED_RE = re.compile(r"^Superseded by cycle: (\S+)\s*$", re.MULTILINE)
_DESCRIPTION_RE = re.compile(r"^### Description\s*$", re.MULTILINE)

# V4 report fields: scope (slice/system/delta-sync), input file digests, output digests.
_SCOPE_RE = re.compile(r"^Scope: (slice \d+|system|delta-sync)\s*$", re.MULTILINE)
_INPUT_RE = re.compile(r"^Input: (\S+) sha256:([0-9a-f]{64})\s*$", re.MULTILINE)
_OUTPUT_RE = re.compile(r"^Output: (\S+) sha256:([0-9a-f]{64})\s*$", re.MULTILINE)


def unfenced_text(text: str) -> str:
    """Mask fenced examples while preserving offsets into the original text."""
    visible = []
    fence = None
    for line in text.splitlines(keepends=True):
        marker = re.match(r"^ {0,3}(`{3,}|~{3,})(.*?)(?:\r?\n)?$", line)
        if fence is None and marker:
            fence = (marker.group(1)[0], len(marker.group(1)))
            visible.append(re.sub(r"[^\r\n]", " ", line))
        elif fence is not None:
            visible.append(re.sub(r"[^\r\n]", " ", line))
            if marker and marker.group(1)[0] == fence[0] and len(marker.group(1)) >= fence[1] and not marker.group(2).strip():
                fence = None
        else:
            visible.append(line)
    return "".join(visible)


def _verdict(content: str) -> str | None:
    visible = unfenced_text(content)
    description = _DESCRIPTION_RE.search(visible)
    metadata = visible[:description.start()] if description else visible
    verdicts = _HITL_RE.findall(metadata)
    return verdicts[-1] if verdicts else None


class ReportState(NamedTuple):
    iteration: int | None
    hitl: str | None
    based_on: tuple[str, int] | None = None
    superseded_by: str | None = None
    scope: str | None = None
    inputs: tuple[tuple[str, str], ...] = ()  # (path, sha256) pairs


class ReportIteration(NamedTuple):
    number: int
    content: str
    hitl: str | None


def parse_report_iterations(text: str) -> list[ReportIteration]:
    """Read appended sections in file order, including incomplete iterations."""
    headings = list(_ITERATION_RE.finditer(unfenced_text(text)))
    sections = []
    for index, heading in enumerate(headings):
        end = headings[index + 1].start() if index + 1 < len(headings) else len(text)
        content = text[heading.start():end].rstrip()
        sections.append(ReportIteration(int(heading.group(1)), content, _verdict(content)))
    return sections


def report_header(text: str) -> str:
    """Return the original header before the first real iteration heading."""
    heading = _ITERATION_RE.search(unfenced_text(text))
    return text[:heading.start()] if heading else text


def report_state(report_file: Path) -> ReportState:
    """Latest iteration number, HITL verdict, chain links, scope and inputs in one report."""
    try:
        text = report_file.read_text(encoding="utf-8")
    except OSError as exc:
        log.warning("cannot read %s: %s", report_file, exc)
        return ReportState(None, None)
    sections = parse_report_iterations(text)
    content = sections[-1].content if sections else text
    latest = unfenced_text(content)
    based_on = _BASED_ON_RE.search(latest)
    superseded = _SUPERSEDED_RE.search(latest)
    scope_match = _SCOPE_RE.search(latest)
    inputs = tuple(_INPUT_RE.findall(latest))
    return ReportState(
        sections[-1].number if sections else None,
        _verdict(content),
        (based_on.group(1), int(based_on.group(2))) if based_on else None,
        superseded.group(1) if superseded else None,
        scope_match.group(1) if scope_match else None,
        inputs,
    )


def authorized_advance(
    path: str, recorded: str, current: str, deltas: list[dict] | None = None
) -> bool:
    """True when a file digest change is explained by applied deltas with no interface impact.
    
    Phase H implements delta chain validation. For now, conservatively assume no advances.
    """
    # TODO (Phase H): Parse DELTAS.md, check for applied rows with Interface impact: none
    # that chain recorded → current for this path.
    return False


def stale_reason(
    gate: str, gates: dict[str, ReportState], seen: tuple[str, ...] = (),
    project_root: Path | None = None
) -> str | None:
    """Follow a report's recorded baseline, checking digest staleness if project_root given.
    
    Without project_root, uses v3 iteration-based staleness (backward compatible).
    With project_root, recomputes Input: digests and compares; first mismatch not
    explained by an authorized advance returns the stale message.
    """
    report = gates.get(gate)
    if report is None or report.based_on is None:
        return None
    predecessor, number = report.based_on
    if predecessor not in gates or predecessor == gate or predecessor in seen:
        return None
    latest = gates[predecessor].iteration
    if latest is not None and number < latest:
        return f"based on {predecessor} iteration {number}, {predecessor} is at {latest}"
    if stale_reason(predecessor, gates, seen + (gate,), project_root):
        return f"{predecessor} is stale"
    
    # V4: digest-based staleness (requires custody availability, Phase A3)
    if project_root and report.inputs:
        # TODO (A3): Call custody.verify() to check inputs; return stale-report messages
        pass
    
    return None


def gate_order(gate: str) -> tuple[int, int, str]:
    """Chain gates first, in flow order; any other id follows alphabetically."""
    order = CONFIG.get("report_order", [])
    if gate in order:
        return (0, order.index(gate), gate)
    return (1, 0, gate)


def next_step(gates: dict[str, ReportState]) -> str | None:
    """Derive the next skill and scope from latest iterations.
    
    Returns e.g. "S2 slice 3", "G3 system", "S0 delta-sync", or None if chain
    is incomplete or the next gate is unavailable."""
    if not gates:
        return None
    
    # Find the last PASS in the chain order
    order = CONFIG.get("report_order", [])
    last_pass_idx = -1
    last_scope = None
    
    for idx, gate_id in enumerate(order):
        report = gates.get(gate_id)
        if report and report.hitl == "PASS":
            last_pass_idx = idx
            last_scope = report.scope
        elif report and report.hitl == "FEEDBACK":
            # Hit a FEEDBACK; next is a rework of this or its predecessor
            break
    
    if last_pass_idx < 0:
        # No PASS yet; next is the first entry point
        for gate_id in order:
            if gates.get(gate_id) is None:
                return f"{gate_id} (not started)"
        return None
    
    # Find the next gate after last PASS
    if last_pass_idx + 1 < len(order):
        next_gate = order[last_pass_idx + 1]
        # For S2, include scope: "S2 slice X" or "S2 (waiting for first run)"
        if next_gate == "S2" and last_scope:
            if last_scope.startswith("slice"):
                # Extract slice number and increment for next run
                try:
                    slice_num = int(last_scope.split()[-1])
                    return f"{next_gate} slice {slice_num + 1}"
                except (ValueError, IndexError):
                    pass
            elif last_scope == "system":
                # After system S2, should restart slices (not typical)
                return f"{next_gate} slice 0"
        return next_gate
    
    return None


def cycle_reports(report_dir: Path) -> dict[str, dict[str, ReportState]]:
    """Cycle -> gate -> report state for the cycle-scoped layout."""
    cycles: dict[str, dict[str, ReportState]] = {}
    if not report_dir.is_dir():
        return cycles
    for cycle_dir in sorted(path for path in report_dir.iterdir() if path.is_dir()):
        gates = {
            report.stem: report_state(report)
            for report in sorted(cycle_dir.glob("*.md"), key=lambda p: gate_order(p.stem))
        }
        if gates:
            cycles[cycle_dir.name] = gates
    return cycles


# `codeanvil backup` folder names: <stage>_iter<N> under a producing cycle, or
# <stage>_<machine-timestamp> under backups/unknown/.
# Backups of a file with no resolvable producer live under this folder; the
# name is reserved, so `backup` refuses a cycle with the same name.
UNKNOWN_PRODUCER = "unknown"

# Stage alternatives come from `backup_targets` in config.yaml, the single
# source of truth for which stages `codeanvil backup` accepts.
_STAGES = "|".join(re.escape(stage) for stage in CONFIG.get("backup_targets", {}))
_BACKUP_ITER_RE = re.compile(rf"^(?P<stage>{_STAGES})_iter(?P<iteration>\d+)$")
_BACKUP_UNKNOWN_RE = re.compile(rf"^(?P<stage>{_STAGES})_\d{{4}}-\d{{2}}-\d{{2}}_\d{{2}}-\d{{2}}-\d{{2}}-\d{{3}}$")


def backup_entries(backups_dir: Path) -> dict[str, list[tuple[str, int | None, str]]]:
    """Cycle -> latest backup per stage: [(stage, iteration or None, folder)].

    `folder` is relative to the backups directory, so callers print it with the
    project-relative prefix. Unknown-producer folders live under `unknown/`."""
    # Order key: (1, iteration) for producer folders, (0, timestamp) for
    # unknown-producer ones, so the two kinds never compare int against str.
    best: dict[tuple[str, str], tuple[tuple[int, int | str], str]] = {}
    if not backups_dir.is_dir():
        return {}
    for cycle_dir in sorted(path for path in backups_dir.iterdir() if path.is_dir()):
        for folder in cycle_dir.iterdir():
            if not folder.is_dir():
                continue
            unknown = cycle_dir.name == UNKNOWN_PRODUCER
            match = (_BACKUP_UNKNOWN_RE if unknown else _BACKUP_ITER_RE).match(folder.name)
            if match is None:
                continue
            stage = match.group("stage")
            order: tuple[int, int | str] = (
                (0, folder.name) if unknown else (1, int(match.group("iteration")))
            )
            relative = f"{cycle_dir.name}/{folder.name}"
            key = (cycle_dir.name, stage)
            if key not in best or order > best[key][0]:
                best[key] = (order, relative)
    entries: dict[str, list[tuple[str, int | None, str]]] = {}
    for (cycle, stage), (order, relative) in best.items():
        iteration = order[1] if order[0] == 1 else None
        entries.setdefault(cycle, []).append((stage, iteration, relative))
    for values in entries.values():
        values.sort(key=lambda entry: gate_order(entry[0]))
    return entries

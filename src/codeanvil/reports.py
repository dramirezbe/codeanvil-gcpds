"""Shared readers for cycle-scoped gate reports.

`status` prints the chain state and `backup` resolves which iteration produced
the files it saves. Both read the same append-only reports, so the parsing
lives here once: a command module never imports from another command module.
"""

import re
from pathlib import Path, PurePosixPath
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
    verdict: str | None = None
    accepted_deltas: tuple[str, ...] = ()
    sync_only: bool = False
    rework_from: tuple[str, int] | None = None
    outputs: tuple[tuple[str, str], ...] = ()
    format_errors: tuple[str, ...] = ()


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
    return _state_from_content(sections[-1].content if sections else text,
                               sections[-1].number if sections else None, report_file.stem)


def _digest_errors(latest: str) -> list[str]:
    """Do not silently discard a declared digest, including malformed or duplicate fields."""
    errors = []
    seen = set()
    for number, line in enumerate(latest.splitlines(), 1):
        candidate = re.match(r"\s*(Input|Output)\s*:", line, re.IGNORECASE)
        if not candidate:
            continue
        kind = candidate.group(1).capitalize()
        match = (_INPUT_RE if kind == "Input" else _OUTPUT_RE).fullmatch(line)
        if not match:
            errors.append(f"malformed-{kind.lower()}: line {number}; expected {kind}: "
                          "<path> sha256:<64 lowercase hexadecimal characters>")
        elif (kind, match.group(1)) in seen:
            errors.append(f"duplicate-{kind.lower()}: {match.group(1)}")
        else:
            seen.add((kind, match.group(1)))
    return errors


def _state_from_content(content: str, number: int | None, gate: str = "") -> ReportState:
    latest = unfenced_text(content)
    based_on = _BASED_ON_RE.search(latest)
    superseded = _SUPERSEDED_RE.search(latest)
    scope = _SCOPE_RE.search(latest)
    verdict = re.search(r"^Verdict: ([^\n]+)", latest, re.MULTILINE)
    rework = re.search(r"^Rework from: (\S+) iteration (\d+)\s*$", latest, re.MULTILINE)
    errors = _digest_errors(latest)
    inputs = tuple(_INPUT_RE.findall(latest))
    # Scope identifies v4 deliveries; preserve unscoped legacy report semantics.
    if gate == "S2" and scope and _verdict(content) == "PASS":
        paths = {PurePosixPath(p.replace("\\", "/")).as_posix() for p, _ in inputs}
        for path in (".codeanvil/design/SDD.md", ".codeanvil/GT/SyRS.md"):
            if path not in paths:
                errors.append(f"missing-input: {path}")
    return ReportState(
        number, _verdict(content),
        (based_on.group(1), int(based_on.group(2))) if based_on else None,
        superseded.group(1) if superseded else None,
        scope.group(1) if scope else None, inputs,
        verdict.group(1).strip() if verdict else None,
        tuple(re.findall(r"^Delta accepted: (D-[A-Za-z0-9_-]+)\b", latest, re.MULTILINE)),
        bool(re.search(r"^Sync-only: yes\s*$", latest, re.MULTILINE)),
        (rework.group(1), int(rework.group(2))) if rework else None,
        tuple(_OUTPUT_RE.findall(latest)),
        tuple(errors),
    )


def scoped_report_state(report_file: Path, scope: str) -> ReportState:
    """Latest iteration *of this scope*, never an older PASS after its FEEDBACK."""
    try:
        sections = parse_report_iterations(report_file.read_text(encoding="utf-8"))
    except OSError:
        return ReportState(None, None)
    for section in reversed(sections):
        state = _state_from_content(section.content, section.number, report_file.stem)
        if state.scope == scope:
            return state
    return ReportState(None, None)


def read_deltas(project_root: Path) -> list[dict[str, str]]:
    """Read the locked DELTAS table, ignoring examples in fenced blocks."""
    path = project_root / ".codeanvil/plans/DELTAS.md"
    if not path.is_file():
        return []
    rows = []
    headers = None
    for line in unfenced_text(path.read_text(encoding="utf-8")).splitlines():
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if "Before sha256" in cells and "Document" in cells:
            headers = cells
        elif headers and len(cells) == len(headers) and not all(re.fullmatch(r"[: -]+", c) for c in cells):
            rows.append(dict(zip(headers, cells)))
    return rows


def authorized_advance(
    path: str, recorded: str, current: str, deltas: list[dict] | None = None
) -> bool:
    """Accept only authoritative, applied, interface-neutral digest chains."""
    reachable = {recorded}
    eligible = [row for row in deltas or [] if
                row.get("Document") == path and row.get("Status") == "applied"
                and row.get("Interface impact") == "none"
                and row.get("Authority") and row.get("Applied in")]
    while True:
        expanded = reachable | {row.get("After sha256", "") for row in eligible
                                if row.get("Before sha256") in reachable
                                and re.fullmatch(r"[0-9a-f]{64}", row.get("After sha256", ""))}
        if current in expanded:
            return True
        if expanded == reachable:
            return False
        reachable = expanded


def baseline_reason(gate: str, report: ReportState) -> str | None:
    """A feedback source never replaces S1's upstream GT review baseline."""
    if gate == "S1" and report.based_on and report.based_on[0] != "G0":
        return f"invalid-baseline: S1 must be based on G0, found {report.based_on[0]}"
    return None


def stale_reason(
    gate: str, gates: dict[str, ReportState], seen: tuple[str, ...] = (),
    project_root: Path | None = None
) -> str | None:
    """Check input integrity first, then the recorded predecessor baseline."""
    report = gates.get(gate)
    if report is None:
        return None
    if report.format_errors:
        return f"invalid-report: {gate} iteration {report.iteration}: {report.format_errors[0]}"
    invalid = baseline_reason(gate, report)
    if invalid:
        return invalid
    if project_root is not None:
        from codeanvil.custody import path_sha256, s1_delivery_findings
        deltas = read_deltas(project_root)
        for path, recorded in report.inputs:
            current = path_sha256(project_root / path)
            if recorded != current and not authorized_advance(path, recorded, current, deltas):
                return f"stale-report: {path} changed since {gate} iteration {report.iteration}"
        if gate == "S1":
            pending = s1_delivery_findings(project_root, report)
            if pending:
                return (f"undelivered-output: {pending[0].path} changed since S1 iteration "
                        f"{report.iteration}; complete S1")
    if report.based_on is None:
        return None
    predecessor, number = report.based_on
    if predecessor not in gates or predecessor == gate or predecessor in seen:
        return None
    latest = gates[predecessor].iteration
    if latest is not None and number < latest:
        # Only a reviewed G0/G1 delta-sync may preserve downstream baselines.
        # G0/G1 themselves must review every new S0/S1 delivery.
        if not (project_root is not None and report.inputs and predecessor in {"G0", "G1"}
                and gates[predecessor].scope == "delta-sync" and gates[predecessor].hitl == "PASS"):
            return f"based on {predecessor} iteration {number}, {predecessor} is at {latest}"
    if stale_reason(predecessor, gates, seen + (gate,), project_root):
        return f"{predecessor} is stale"
    return None


def gate_order(gate: str) -> tuple[int, int, str]:
    """Chain gates first, in flow order; any other id follows alphabetically."""
    order = CONFIG.get("report_order", [])
    if gate in order:
        return (0, order.index(gate), gate)
    return (1, 0, gate)


def _sync_reviewed(report: ReportState, rows: list[dict], gates: dict[str, ReportState]) -> bool:
    """A sync-only feedback needs each applied delta's stage AND human gate delivery."""
    if not report.accepted_deltas:
        return False
    for delta_id in report.accepted_deltas:
        matching = [row for row in rows if row.get("ID") == delta_id]
        if len(matching) != 1 or matching[0].get("Status") != "applied":
            return False
        row = matching[0]
        stage, gate = ("S1", "G1") if row.get("Type") == "design-sync" else ("S0", "G0")
        applied = re.fullmatch(rf"{stage} iteration (\d+)", row.get("Applied in", ""))
        delivery, review = gates.get(stage), gates.get(gate)
        if (not applied or not delivery or not review or delivery.hitl != "PASS"
                or (delivery.iteration is None or delivery.iteration < int(applied.group(1))) or review.hitl != "PASS"
                or review.based_on != (stage, delivery.iteration) or review.scope != "delta-sync"):
            return False
    return True


def _pending_sync_review(stage: str, gate: str, gates: dict[str, ReportState]) -> str | None:
    delivery, review = gates.get(stage), gates.get(gate)
    if not delivery or delivery.scope != "delta-sync" or delivery.hitl != "PASS":
        return None
    if not review or review.based_on != (stage, delivery.iteration):
        return gate
    if review.hitl == "FEEDBACK":
        return stage
    return gate if review.hitl != "PASS" else None


def next_step(gates: dict[str, ReportState], project_root: Path | None = None) -> str | None:
    """Derive the next skill and scope from latest iterations.
    
    Returns e.g. "S2 slice 3", "G3 system", "S0 delta-sync", or None if chain
    is incomplete or the next gate is unavailable."""
    if not gates:
        return None
    
    rfd = gates.get("RFD")
    g3 = gates.get("G3")
    if rfd and rfd.superseded_by:
        return f"Cycle closed by RFD. Continue in cycle {rfd.superseded_by}."
    rows = read_deltas(project_root) if project_root is not None else []
    if project_root is not None:
        logged_ids = {row.get("ID") for row in rows if row.get("Status") in {"accepted", "applied"}}
        if g3 and g3.hitl in {"PASS", "FEEDBACK"} and set(g3.accepted_deltas) - logged_ids:
            return "S2 delta-intake"
        if any(row.get("Status") == "accepted" and row.get("Type") != "design-sync" for row in rows):
            return "S0 delta-sync"
        pending = _pending_sync_review("S0", "G0", gates)
        if pending:
            return pending
        if any(row.get("Status") == "accepted" and row.get("Type") == "design-sync" for row in rows):
            return "S1 delta-sync"
        pending = _pending_sync_review("S1", "G1", gates)
        if pending:
            return pending
    order = [g for g in CONFIG.get("report_order", []) if g != "RFD"]
    # Scope changes distinguish a new slice from the preceding slice's reports.
    previous = None
    for gate in order:
        report = gates.get(gate)
        if report is None or report.iteration is None:
            if gate == "S2":
                return "S2 slice 0"
            scope = previous.scope if previous and gate in {"G2", "S3", "G3"} else None
            return f"{gate} {scope}" if scope else gate
        if (gate in {"G2", "S3", "G3"} and previous
                and (report.based_on != (order[order.index(gate)-1], previous.iteration)
                     or report.scope != previous.scope)):
            return f"{gate} {previous.scope}" if previous.scope else gate
        # A newer S1 delivery needs a fresh G1 verdict, even when the old review
        # was FEEDBACK. The old review stays stale; it cannot invalidate its replacement.
        if (gate == "G1" and report.verdict != "RFD" and previous
                and report.based_on is not None and report.based_on[0] == "S1"
                and previous.iteration is not None and report.based_on[1] < previous.iteration):
            return "G1"
        if report.hitl == "FEEDBACK":
            if gate == "G3" and report.sync_only and _sync_reviewed(report, rows, gates):
                return f"S2 {report.scope}" if report.scope else "S2"
            routes = {"plan defect": "S2", "module defect": "S3", "design defect": "S1",
                      "GT defect": "S0", "RFD": "RFD"}
            return routes.get(report.verdict, {"G0": "S0", "G1": "S1", "G2": "S2", "G3": "S3"}.get(gate, gate))
        if report.hitl != "PASS" or stale_reason(gate, gates, project_root=project_root):
            return gate
        previous = report
    final = gates.get("G3")
    if final and final.scope and final.scope.startswith("slice "):
        return f"S2 slice {int(final.scope.split()[1]) + 1} (or system if backlog complete)"
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

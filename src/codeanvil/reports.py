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

# Legacy gate report filenames: <gate>_<machine-timestamp>.md
# (e.g. G0_2026-10-21_16-23-45-123.md), written before cycle-scoped reports.
_REPORT_RE = re.compile(r"^(?P<gate>.+)_(?P<ts>\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}-\d{3})\.md$")

# Cycle-scoped reports: .codeanvil/report/<cycle>/<gate>.md with appended
# "## Iteration N" sections and a | HITL | PASS|FEEDBACK | row per iteration.
_ITERATION_RE = re.compile(r"^## Iteration (\d+)\s*$", re.MULTILINE)
# Exactly two cells: the schema placeholder "| HITL | PASS | FEEDBACK |" is not
# a verdict and must not be read as PASS.
_HITL_RE = re.compile(r"^\|\s*HITL\s*\|\s*(PASS|FEEDBACK)\s*\|\s*$", re.MULTILINE)

# Chain links, read only from the latest iteration of a report.
_BASED_ON_RE = re.compile(r"^Based on: (\S+) iteration (\d+)\s*$", re.MULTILINE)
_SUPERSEDED_RE = re.compile(r"^Superseded by cycle: (\S+)\s*$", re.MULTILINE)


class ReportState(NamedTuple):
    iteration: int | None
    hitl: str | None
    based_on: tuple[str, int] | None = None
    superseded_by: str | None = None


def report_state(report_file: Path) -> ReportState:
    """Latest iteration number, HITL verdict and chain links in one report."""
    try:
        text = report_file.read_text(encoding="utf-8")
    except OSError as exc:
        log.warning("cannot read %s: %s", report_file, exc)
        return ReportState(None, None)
    headings = list(_ITERATION_RE.finditer(text))
    verdicts = _HITL_RE.findall(text)
    latest = text[headings[-1].end():] if headings else ""
    based_on = _BASED_ON_RE.search(latest)
    superseded = _SUPERSEDED_RE.search(latest)
    return ReportState(
        max(int(match.group(1)) for match in headings) if headings else None,
        verdicts[-1] if verdicts else None,
        (based_on.group(1), int(based_on.group(2))) if based_on else None,
        superseded.group(1) if superseded else None,
    )


def gate_order(gate: str) -> tuple[int, int, str]:
    """Chain gates first, in flow order; any other id follows alphabetically."""
    order = CONFIG.get("report_order", [])
    if gate in order:
        return (0, order.index(gate), gate)
    return (1, 0, gate)


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
_BACKUP_ITER_RE = re.compile(r"^(?P<stage>S0|S1|S2|G2)_iter(?P<iteration>\d+)$")
_BACKUP_UNKNOWN_RE = re.compile(r"^(?P<stage>S0|S1|S2|G2)_\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}-\d{3}$")


def backup_entries(backups_dir: Path) -> dict[str, list[tuple[str, int | None, str]]]:
    """Cycle -> latest backup per stage: [(stage, iteration or None, folder)].

    `folder` is relative to the backups directory, so callers print it with the
    project-relative prefix. Unknown-producer folders live under `unknown/`."""
    best: dict[tuple[str, str], tuple[int | str, str]] = {}
    if not backups_dir.is_dir():
        return {}
    for cycle_dir in sorted(path for path in backups_dir.iterdir() if path.is_dir()):
        for folder in cycle_dir.iterdir():
            if not folder.is_dir():
                continue
            match = _BACKUP_ITER_RE.match(folder.name)
            if match:
                stage = match.group("stage")
                iteration: int | None = int(match.group("iteration"))
                order: int | str = iteration
            elif cycle_dir.name == "unknown" and _BACKUP_UNKNOWN_RE.match(folder.name):
                stage, iteration = folder.name.split("_", 1)[0], None
                order = folder.name
            else:
                continue
            relative = f"{cycle_dir.name}/{folder.name}"
            key = (cycle_dir.name, stage)
            # Same key always holds one kind: an iteration int, or the
            # timestamp in an unknown-producer folder name.
            if key not in best or order > best[key][0]:
                best[key] = (order, relative)
    entries: dict[str, list[tuple[str, int | None, str]]] = {}
    for (cycle, stage), (order, relative) in best.items():
        iteration = order if isinstance(order, int) else None
        entries.setdefault(cycle, []).append((stage, iteration, relative))
    for values in entries.values():
        values.sort(key=lambda entry: gate_order(entry[0]))
    return entries

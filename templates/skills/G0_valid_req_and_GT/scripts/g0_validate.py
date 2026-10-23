#!/usr/bin/env python3
"""
G0 - deterministic structural validator for V-SIL Ground Truth documents.

Validates a StRS (IEEE 29148 §9.4) or SyRS (§9.5) markdown file against the
templates, then — when both are given — the G0-X cross-document consistency
rules. Stdlib only. No AI, no network, no filesystem writes: it reads
the input `.md` files, prints a report to stdout, and exits.

Usage:
    python g0_validate.py <file> [<file> ...]

G0 is a pair gate: a StRS and a SyRS must both be provided. Missing
either one is an ERROR (exit 1).

Exit codes:
    0  all files passed (warnings allowed)
    1  at least one file has structural errors, G0-X errors, or the
       StRS/SyRS pair is incomplete
    2  script error (bad arguments, unreadable file, undetectable doc type)
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

# --------------------------------------------------------------------------
# Required sections (Phase 1)
# --------------------------------------------------------------------------

STRS_REQUIRED: List[str] = [
    "## Document Metadata",
    "### 1.1 Purpose",
    "### 1.2 Scope",
    "### 1.3 Definitions, Acronyms, and Abbreviations",
    "### 1.4 References",
    "### 1.5 Document Overview",
    "### 1.6 Hardware Inventory",
    "### 2.1 Product Perspective",
    "### 2.2 Product Functions",
    "### 2.3 User Characteristics",
    "### 2.4 Constraints",
    "### 2.5 Assumptions and Dependencies",
    "### 2.6 Block Diagram",
    "### 2.7 Bus and Interface Topology",
    "## 3. Specific Requirements",
    "## 4. External Interface Requirements",
    "## 5. Non-Functional Requirements",
    "## 6. Traceability",
]

SYRS_REQUIRED: List[str] = [
    "## Document Metadata",
    "### 1.1 Purpose",
    "### 1.2 Scope",
    "### 1.3 Definitions, Acronyms, and Abbreviations",
    "### 1.4 References",
    "### 1.5 Document Overview",
    "## 2. Measurement Framework",
    "### 2.1 Measurand Catalog",
    "### 2.2 Method Selection and Rationale",
    "### 2.3 Normative-to-Method Mapping",
    "## 3. System Requirements",
    "## 4. Correction Chains",
    "## 5. Uncertainty Budgets",
    "## 6. Field Measurement Protocols",
    "## 7. Traceability",
]

# --------------------------------------------------------------------------
# Metadata rules (Phase 2)
# --------------------------------------------------------------------------

METADATA_REQUIRED: List[str] = [
    "Document ID",
    "Project",
    "Organization",
    "Version",
    "Classification",
]

_SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")
_CLASSIFICATIONS = ("PUBLIC", "INTERNAL", "CONFIDENTIAL")
_PLACEHOLDER_MARKERS = ("_ACRONYM_", "_NNN_", "_project_name_", "YYYY-MM-DD")

# --------------------------------------------------------------------------
# Block / field rules (Phase 3)
# --------------------------------------------------------------------------

NRM_ID_RE = re.compile(r"^NRM-[A-Z]{2,8}-\d{3}$")
HWC_ID_RE = re.compile(r"^HWC-[A-Z]{2,4}-\d{3}$")
STK_ID_RE = re.compile(r"^STK-[A-Z]{2,4}-\d{3}$")
SYS_ID_RE = re.compile(r"^SYS-[A-Z]{2,4}-\d{3}$")

STRS_ID_PATTERN_TEXT = r"^(NRM-[A-Z]{2,8}|HWC-[A-Z]{2,4}|STK-[A-Z]{2,4})-\d{3}$"
SYS_ID_PATTERN_TEXT = r"^SYS-[A-Z]{2,4}-\d{3}$"

# Any well-formed StRS block ID appearing inside a cell (traces_to, Dependencies).
_STRS_TOKEN_RE = re.compile(
    r"(?:NRM-[A-Z]{2,8}|HWC-[A-Z]{2,4}|STK-[A-Z]{2,4})-\d{3}"
)

# Dependency IDs: generic 3-5/2-4 form plus long-sub normative IDs (NRM-ICNIRP-001).
_DEP_RE = re.compile(r"NRM-[A-Z]{2,8}-\d{3}|[A-Z]{3,5}-[A-Z]{2,4}-\d{3}")

COMPLIANCE_VALUES: Tuple[str, ...] = (
    "COMPLIANT",
    "PARTIAL",
    "NOT_APPLICABLE",
    "PENDING",
)

# Inline compliance traceability: rows must exist on every StRS block;
# `Standard(s)` / `Clause` may hold an em dash when no source applies.
STRS_COMPLIANCE_PRESENCE: Tuple[str, ...] = ("Standard(s)", "Clause")

STK_ENUMS: Dict[str, Sequence[str]] = {
    "Type": ("FUNCTIONAL", "NON_FUNCTIONAL", "INTERFACE", "CONSTRAINT"),
    "Priority": ("MUST", "SHOULD", "COULD", "WONT"),
    "Status": ("PROPOSED", "APPROVED", "IMPLEMENTED", "VERIFIED", "REJECTED"),
    "Verification": ("INSPECTION", "DEMONSTRATION", "TEST", "ANALYSIS"),
    "Compliance": COMPLIANCE_VALUES,
}
STK_REQUIRED_FIELDS: Tuple[str, ...] = (
    "Type",
    "Priority",
    "Status",
    "Verification",
    "Compliance",
)

NRM_ENUMS: Dict[str, Sequence[str]] = {
    "Priority": ("MUST", "SHOULD", "COULD", "WONT"),
    "Status": ("PROPOSED", "APPROVED", "IMPLEMENTED", "VERIFIED", "REJECTED"),
    "Compliance": COMPLIANCE_VALUES,
}
# A normative obligation always cites its source concretely (never an em dash).
NRM_REQUIRED_FIELDS: Tuple[str, ...] = (
    "Priority",
    "Status",
    "Standard(s)",
    "Clause",
    "Compliance",
)

HWC_ENUMS: Dict[str, Sequence[str]] = {
    "Limit type": ("MAX", "MIN", "RANGE", "FIXED", "ENUM"),
    "Source": ("DATASHEET", "DRIVER_API", "MEASURED", "DERIVED"),
    "Impact": ("HARD", "SOFT", "INFORMATIONAL"),
    "Status": ("CONFIRMED", "PRELIMINARY", "DEPRECATED"),
    "Compliance": COMPLIANCE_VALUES,
}
HWC_REQUIRED_FIELDS: Tuple[str, ...] = (
    "Component",
    "Parameter",
    "Limit type",
    "Source",
    "Source ref",
    "Impact",
    "Status",
    "Compliance",
)

# SyRS MVP (structural only): ID, type, parameter, method, traces_to.
SYS_REQUIRED_FIELDS: Tuple[str, ...] = ("Type", "Parameter", "Method", "Traces to")

MAX_TITLE_LEN = 120

# --------------------------------------------------------------------------
# Markdown primitives
# --------------------------------------------------------------------------

_HEADING_RE = re.compile(r"^(#{1,4})\s+(.*?)\s*$")
_HR_RE = re.compile(r"^-{3,}$")
_TABLE_SEP_RE = re.compile(r"^:?-{3,}:?$")
_NUMBERED_RE = re.compile(r"^\d+\.")

# `**` + `ID` + em/en dash + `TITLE` + `**`. Deliberately loose on the ID so a
# malformed ID is still captured and reported as an ERROR rather than silently
# skipped.
_BLOCK_HEADING_RE = re.compile(r"^\*\*`([^`]+)`\s*[\u2014\u2013-]\s*(.+?)\*\*\s*$")

_EMPTY_VALUES = frozenset({"", "\u2014", "\u2013", "-", "--"})
_NA_VALUES = frozenset({"n/a", "na", "none", "null", "tbd"})


def cell_text(raw: str) -> str:
    """Strip markdown decoration (backticks, bold) from a table cell."""
    value = raw.strip()
    if len(value) >= 2 and value.startswith("`") and value.endswith("`"):
        value = value[1:-1]
    return value.strip("*").strip()


def is_unset(raw: str) -> bool:
    """True when a cell holds no real value (empty, dash, or N/A marker)."""
    value = cell_text(raw)
    return value in _EMPTY_VALUES or value.lower() in _NA_VALUES


def _is_table_row(text: str) -> bool:
    stripped = text.strip()
    return stripped.startswith("|") and stripped.endswith("|") and len(stripped) > 1


def _split_row(text: str) -> List[str]:
    stripped = text.strip()
    if stripped.startswith("|"):
        stripped = stripped[1:]
    if stripped.endswith("|"):
        stripped = stripped[:-1]
    return [cell.strip() for cell in stripped.split("|")]


def _is_separator_row(cells: Sequence[str]) -> bool:
    return bool(cells) and all(_TABLE_SEP_RE.match(cell) for cell in cells)


# --------------------------------------------------------------------------
# Data structures
# --------------------------------------------------------------------------


@dataclass
class Section:
    """A markdown section: heading plus the lines that follow it."""

    level: int
    title: str
    heading_line: int  # 1-indexed line of the heading itself
    content: List[Tuple[int, str]]  # (1-indexed line no, text) up to next heading


@dataclass
class Finding:
    severity: str  # "ERROR" | "WARNING"
    line: int  # 1-indexed line in the source file
    block_id: str  # requirement/constraint ID, or "" for doc-level
    message: str  # human/LLM-readable description
    expected: str = ""  # valid values, shown as "Expected: ..." when set
    doc: str = ""  # "StRS" | "SyRS" — only set on G0-X findings


@dataclass
class Block:
    """A parsed StRS block (NRM/HWC/STK) or SyRS block (SYS)."""

    id: str
    title: str
    line: int  # 1-indexed line of the block heading
    fields: Dict[str, Tuple[str, int]] = field(default_factory=dict)
    has_description: bool = False
    description_text: str = ""
    has_criteria: bool = False
    criteria_count: int = 0
    dependencies: List[str] = field(default_factory=list)


# --------------------------------------------------------------------------
# Phase 0: parse
# --------------------------------------------------------------------------


def parse_markdown(lines: Sequence[str]) -> List[Section]:
    """Build a flat list of sections from `#`-`####` headings."""
    headings: List[Tuple[int, int, str]] = []
    for index, raw in enumerate(lines, start=1):
        match = _HEADING_RE.match(raw)
        if match:
            headings.append((index, len(match.group(1)), match.group(2).strip()))

    sections: List[Section] = []
    for position, (line_no, level, title) in enumerate(headings):
        start = line_no + 1
        end = headings[position + 1][0] - 1 if position + 1 < len(headings) else len(lines)
        content = [(n, lines[n - 1]) for n in range(start, end + 1)]
        sections.append(Section(level=level, title=title, heading_line=line_no, content=content))
    return sections


def detect_doc_type(sections: Sequence[Section]) -> Optional[str]:
    """Detect StRS/SyRS from the first `## ` heading."""
    for section in sections:
        if section.level != 2:
            continue
        title = section.title.lower()
        if "stakeholder requirements specification" in title or "strs" in title:
            return "StRS"
        if "system requirements specification" in title or "syrs" in title:
            return "SyRS"
        return None  # first top-level heading is something else entirely
    return None


def _parse_kv_table(content: Sequence[Tuple[int, str]]) -> Dict[str, Tuple[str, int]]:
    """Parse the first key/value table in `content`.

    Returns {key: (raw_value, line_number)}, skipping the header row and the
    separator row.
    """
    result: Dict[str, Tuple[str, int]] = {}
    saw_row = False
    for line_no, text in content:
        if not _is_table_row(text):
            if saw_row:
                break
            continue
        cells = _split_row(text)
        if _is_separator_row(cells):
            continue
        if not saw_row:
            saw_row = True
            continue  # header row (e.g. `| Field | Value |`)
        if len(cells) < 2:
            continue
        key = cells[0].strip("*").strip()
        if key and key not in result:
            result[key] = (cells[1], line_no)
    return result


def _parse_first_column(content: Sequence[Tuple[int, str]]) -> List[Tuple[str, int]]:
    """Parse the first column of the first table in `content`.

    Returns [(cell_text, line_number)] for every data row.
    """
    out: List[Tuple[str, int]] = []
    saw_row = False
    for line_no, text in content:
        if not _is_table_row(text):
            if saw_row:
                break
            continue
        cells = _split_row(text)
        if _is_separator_row(cells):
            continue
        if not saw_row:
            saw_row = True
            continue
        if cells and cells[0]:
            out.append((cell_text(cells[0]), line_no))
    return out


def _find_section(sections: Sequence[Section], required: str) -> Optional[Section]:
    """Locate a section by substring match on its normalized heading text.

    `required` looks like `### 1.1 Purpose`; matching strips the leading `#`s
    and compares case-insensitively so minor formatting differences pass.
    """
    target = required.lstrip("#").strip().lower()
    for section in sections:
        if target in section.title.lower():
            return section
    return None


# --------------------------------------------------------------------------
# Phase 1: section structure
# --------------------------------------------------------------------------


def validate_sections(sections: Sequence[Section], doc_type: str) -> List[Finding]:
    required = STRS_REQUIRED if doc_type == "StRS" else SYRS_REQUIRED
    findings: List[Finding] = []
    for heading in required:
        if _find_section(sections, heading) is None:
            findings.append(
                Finding(
                    severity="ERROR",
                    line=1,
                    block_id="",
                    message=f"missing required section '{heading}'",
                    expected=heading,
                )
            )
    return findings


# --------------------------------------------------------------------------
# Phase 2: metadata table
# --------------------------------------------------------------------------


def _is_placeholder(value: str) -> bool:
    if value.startswith("_"):
        return True
    return any(marker in value for marker in _PLACEHOLDER_MARKERS)


def validate_metadata(sections: Sequence[Section]) -> List[Finding]:
    findings: List[Finding] = []
    section = _find_section(sections, "## Document Metadata")
    if section is None:
        return findings  # already reported by validate_sections

    fields = _parse_kv_table(section.content)
    anchor = section.heading_line

    for name in METADATA_REQUIRED:
        if name not in fields or is_unset(fields[name][0]):
            findings.append(
                Finding(
                    severity="ERROR",
                    line=anchor,
                    block_id="",
                    message=f"metadata table missing required field '{name}'",
                    expected=name,
                )
            )
            continue

        raw, line = fields[name]
        value = cell_text(raw)

        if _is_placeholder(value):
            findings.append(
                Finding(
                    severity="ERROR",
                    line=line,
                    block_id="",
                    message=f"metadata field '{name}' still holds a template placeholder ('{value}')",
                    expected="a concrete value",
                )
            )
            continue

        if name == "Version" and not _SEMVER_RE.match(value):
            findings.append(
                Finding(
                    severity="ERROR",
                    line=line,
                    block_id="",
                    message=f"metadata Version '{value}' is not SemVer",
                    expected="X.Y.Z (e.g. 1.0.0)",
                )
            )
        elif name == "Classification" and value.upper() not in _CLASSIFICATIONS:
            findings.append(
                Finding(
                    severity="ERROR",
                    line=line,
                    block_id="",
                    message=f"metadata Classification '{value}' is not a recognised value",
                    expected=" | ".join(_CLASSIFICATIONS),
                )
            )
    return findings


# --------------------------------------------------------------------------
# Phase 3: block parsing and field validation
# --------------------------------------------------------------------------


def _build_block(
    block_id: str,
    title: str,
    heading_line: int,
    content: Sequence[Tuple[int, str]],
) -> Block:
    block = Block(id=block_id, title=title, line=heading_line)
    description_parts: List[str] = []
    in_description = False
    in_criteria = False

    for line_no, text in content:
        stripped = text.strip()

        if _is_table_row(text):
            in_description = in_criteria = False
            cells = _split_row(text)
            if _is_separator_row(cells) or len(cells) < 2:
                continue
            key = cells[0].strip("*").strip()
            if key and key.lower() != "field" and key not in block.fields:
                block.fields[key] = (cells[1], line_no)
            continue

        if not stripped:
            continue  # blank lines do not end a capture block

        if stripped.startswith("**Description:**"):
            block.has_description = True
            in_description, in_criteria = True, False
            rest = stripped[len("**Description:**") :].strip()
            if rest:
                description_parts.append(rest)
            continue

        if stripped.startswith("**Acceptance Criteria:**"):
            block.has_criteria = True
            in_criteria, in_description = True, False
            continue

        if stripped.startswith("**"):
            in_description = in_criteria = False  # `**Notes:**` or similar
            continue

        if in_description:
            description_parts.append(stripped)
        elif in_criteria and _NUMBERED_RE.match(stripped):
            block.criteria_count += 1

    block.description_text = "\n".join(description_parts).strip()

    raw_deps = block.fields.get("Dependencies", ("", 0))[0]
    block.dependencies = [] if is_unset(raw_deps) else _DEP_RE.findall(cell_text(raw_deps))
    return block


def parse_blocks(lines: Sequence[str], doc_type: str) -> List[Block]:
    """Extract every requirement/constraint block from the raw lines."""
    del doc_type  # block syntax is identical for StRS and SyRS
    blocks: List[Block] = []
    total = len(lines)
    index = 0

    while index < total:
        match = _BLOCK_HEADING_RE.match(lines[index])
        if not match:
            index += 1
            continue

        block_id = match.group(1).strip()
        title = match.group(2).strip()
        heading_line = index + 1

        cursor = index + 1
        content: List[Tuple[int, str]] = []
        while cursor < total:
            text = lines[cursor]
            stripped = text.strip()
            if (
                _BLOCK_HEADING_RE.match(text)
                or _HR_RE.match(stripped)
                or _HEADING_RE.match(text)
            ):
                break
            content.append((cursor + 1, text))
            cursor += 1

        blocks.append(_build_block(block_id, title, heading_line, content))
        index = cursor

    return blocks


def strs_block_kind(block_id: str) -> Optional[str]:
    """Return "NRM" | "HWC" | "STK" for a well-formed StRS ID, else None."""
    if NRM_ID_RE.match(block_id):
        return "NRM"
    if HWC_ID_RE.match(block_id):
        return "HWC"
    if STK_ID_RE.match(block_id):
        return "STK"
    return None


def _check_fields(
    block: Block,
    required: Sequence[str],
    presence: Sequence[str],
    enums: Dict[str, Sequence[str]],
) -> List[Finding]:
    findings: List[Finding] = []
    for name in required:
        if name not in block.fields or is_unset(block.fields[name][0]):
            findings.append(
                Finding(
                    severity="ERROR",
                    line=block.line,
                    block_id=block.id,
                    message=f"missing required field '{name}'",
                    expected=name,
                )
            )
    for name in presence:
        if name not in block.fields:
            findings.append(
                Finding(
                    severity="ERROR",
                    line=block.line,
                    block_id=block.id,
                    message=f"missing required field '{name}'",
                    expected=f"{name} row (may hold \u2014 when no normative source applies)",
                )
            )
    for name, allowed in enums.items():
        if name not in block.fields or is_unset(block.fields[name][0]):
            continue  # already reported as missing
        value = cell_text(block.fields[name][0])
        if value.upper() not in allowed:
            findings.append(
                Finding(
                    severity="ERROR",
                    line=block.fields[name][1],
                    block_id=block.id,
                    message=f"field '{name}' has invalid value '{value}'",
                    expected=" | ".join(allowed),
                )
            )
    return findings


def validate_blocks(blocks: Sequence[Block], doc_type: str) -> List[Finding]:
    findings: List[Finding] = []
    seen: Dict[str, int] = {}

    for block in blocks:
        # --- ID pattern -----------------------------------------------------
        if doc_type == "StRS":
            kind = strs_block_kind(block.id)
            if kind is None:
                findings.append(
                    Finding(
                        severity="ERROR",
                        line=block.line,
                        block_id=block.id,
                        message="block ID does not match the required pattern",
                        expected=STRS_ID_PATTERN_TEXT,
                    )
                )
        else:
            kind = "SYS"
            if not SYS_ID_RE.match(block.id):
                findings.append(
                    Finding(
                        severity="ERROR",
                        line=block.line,
                        block_id=block.id,
                        message="block ID does not match the required pattern",
                        expected=SYS_ID_PATTERN_TEXT,
                    )
                )

        # --- uniqueness -----------------------------------------------------
        if block.id in seen:
            findings.append(
                Finding(
                    severity="ERROR",
                    line=block.line,
                    block_id=block.id,
                    message=f"duplicate block ID (first declared at line {seen[block.id]})",
                    expected="a unique ID",
                )
            )
        else:
            seen[block.id] = block.line

        # --- title length ---------------------------------------------------
        if len(block.title) > MAX_TITLE_LEN:
            findings.append(
                Finding(
                    severity="ERROR",
                    line=block.line,
                    block_id=block.id,
                    message=f"block title is {len(block.title)} characters",
                    expected=f"at most {MAX_TITLE_LEN} characters",
                )
            )

        # --- fields and type-specific rules ---------------------------------
        if doc_type == "StRS":
            if kind is None:
                continue  # unusable ID — field rules would be noise
            if kind == "STK":
                findings.extend(
                    _check_fields(block, STK_REQUIRED_FIELDS, STRS_COMPLIANCE_PRESENCE, STK_ENUMS)
                )
                findings.extend(_validate_requirement_block(block))
            elif kind == "NRM":
                findings.extend(
                    _check_fields(block, NRM_REQUIRED_FIELDS, (), NRM_ENUMS)
                )
                findings.extend(_validate_requirement_block(block))
            else:  # HWC
                findings.extend(
                    _check_fields(block, HWC_REQUIRED_FIELDS, STRS_COMPLIANCE_PRESENCE, HWC_ENUMS)
                )
                findings.extend(_validate_hwc_block(block))
        else:
            findings.extend(_check_fields(block, SYS_REQUIRED_FIELDS, (), {}))
            findings.extend(_validate_sys_block(block))

    return findings


def _validate_requirement_block(block: Block) -> List[Finding]:
    """Description + acceptance-criteria rules shared by STK and NRM blocks."""
    findings: List[Finding] = []

    if not block.has_description:
        findings.append(
            Finding(
                severity="ERROR",
                line=block.line,
                block_id=block.id,
                message="missing '**Description:**' section",
                expected="a '**Description:**' line followed by the requirement text",
            )
        )
    elif not re.search(r"\bSHALL\b|\bSHOULD\b", block.description_text):
        findings.append(
            Finding(
                severity="WARNING",
                line=block.line,
                block_id=block.id,
                message="description does not use the SHALL/SHOULD keyword",
                expected="SHALL or SHOULD",
            )
        )

    if not block.has_criteria:
        findings.append(
            Finding(
                severity="ERROR",
                line=block.line,
                block_id=block.id,
                message="missing '**Acceptance Criteria:**' section",
                expected="a '**Acceptance Criteria:**' line with numbered items",
            )
        )
    elif block.criteria_count < 1:
        findings.append(
            Finding(
                severity="ERROR",
                line=block.line,
                block_id=block.id,
                message="acceptance criteria section has no numbered items",
                expected="at least 1 numbered item",
            )
        )

    return findings


def _validate_sys_block(block: Block) -> List[Finding]:
    """SyRS MVP: every SYS block carries at least one acceptance criterion."""
    findings: List[Finding] = []

    if not block.has_criteria:
        findings.append(
            Finding(
                severity="ERROR",
                line=block.line,
                block_id=block.id,
                message="missing '**Acceptance Criteria:**' section",
                expected="a '**Acceptance Criteria:**' line with numbered items",
            )
        )
    elif block.criteria_count < 1:
        findings.append(
            Finding(
                severity="ERROR",
                line=block.line,
                block_id=block.id,
                message="acceptance criteria section has no numbered items",
                expected="at least 1 numbered item",
            )
        )

    return findings


def _validate_hwc_block(block: Block) -> List[Finding]:
    findings: List[Finding] = []
    limit_type_raw = block.fields.get("Limit type", ("", 0))[0]
    limit_type = cell_text(limit_type_raw).upper() if not is_unset(limit_type_raw) else ""

    if limit_type == "RANGE":
        for name in ("Value min", "Value max"):
            if name not in block.fields or is_unset(block.fields[name][0]):
                findings.append(
                    Finding(
                        severity="ERROR",
                        line=block.line,
                        block_id=block.id,
                        message=f"Limit type RANGE requires field '{name}'",
                        expected=name,
                    )
                )
    elif limit_type:
        if "Value" not in block.fields or is_unset(block.fields["Value"][0]):
            findings.append(
                Finding(
                    severity="ERROR",
                    line=block.line,
                    block_id=block.id,
                    message=f"Limit type {limit_type} requires a non-empty 'Value' field",
                    expected="Value",
                )
            )

    return findings


# --------------------------------------------------------------------------
# Phase 4: cross-references within one document
# --------------------------------------------------------------------------


def _find_cycles(blocks: Sequence[Block]) -> List[List[str]]:
    # First declaration wins so a duplicate ID cannot silently erase an edge.
    graph: Dict[str, List[str]] = {}
    for block in blocks:
        graph.setdefault(block.id, list(block.dependencies))
    WHITE, GRAY, BLACK = 0, 1, 2
    color: Dict[str, int] = {node: WHITE for node in graph}
    path: List[str] = []
    cycles: List[List[str]] = []

    def visit(node: str) -> None:
        color[node] = GRAY
        path.append(node)
        for target in graph.get(node, []):
            if target not in color:
                continue
            if color[target] == GRAY:
                start = path.index(target)
                cycles.append(path[start:] + [target])
            elif color[target] == WHITE:
                visit(target)
        path.pop()
        color[node] = BLACK

    for node in graph:
        if color[node] == WHITE:
            visit(node)
    return cycles


def validate_cross_refs(
    blocks: Sequence[Block], sections: Sequence[Section], doc_type: str
) -> List[Finding]:
    """Intra-document cross-checks (StRS only; SyRS needs its StRS — G0-X)."""
    findings: List[Finding] = []
    if doc_type != "StRS":
        return findings

    known_ids = {block.id for block in blocks}

    for block in blocks:
        for dep in block.dependencies:
            if dep not in known_ids:
                findings.append(
                    Finding(
                        severity="ERROR",
                        line=block.line,
                        block_id=block.id,
                        message=f"dependency '{dep}' does not exist in this document",
                        expected="an ID declared in this document",
                    )
                )

    for cycle in _find_cycles(blocks):
        findings.append(
            Finding(
                severity="ERROR",
                line=block_line(blocks, cycle[0]),
                block_id=cycle[0],
                message="circular dependency: " + " -> ".join(cycle),
                expected="an acyclic dependency graph",
            )
        )

    trace = _find_section(sections, "## 6. Traceability")
    if trace is not None:
        traced = {value for value, _ in _parse_first_column(trace.content)}
        for block in _blocks_in_section(sections, "## 3. Specific Requirements", blocks):
            if block.id not in traced:
                findings.append(
                    Finding(
                        severity="WARNING",
                        line=block.line,
                        block_id=block.id,
                        message="block is not listed in the §6 Traceability table",
                        expected="a row in §6",
                    )
                )

    inventory = {
        value
        for value, _ in _parse_first_column(
            _section_content(sections, "### 1.6 Hardware Inventory")
        )
    }
    refs = {
        value for value, _ in _parse_first_column(_section_content(sections, "### 1.4 References"))
    }

    for block in blocks:
        if strs_block_kind(block.id) != "HWC":
            continue

        comp_raw = block.fields.get("Component", ("", 0))[0]
        if not is_unset(comp_raw):
            for comp in (c.strip() for c in cell_text(comp_raw).replace("`", "").split(",")):
                if comp and comp not in inventory:
                    findings.append(
                        Finding(
                            severity="ERROR",
                            line=block.fields["Component"][1],
                            block_id=block.id,
                            message=f"component '{comp}' is not listed in the §1.6 Hardware Inventory",
                            expected="a Component ID from §1.6",
                        )
                    )

        ref_raw = block.fields.get("Source ref", ("", 0))[0]
        if refs and not is_unset(ref_raw):
            candidate = cell_text(ref_raw).replace("`", "").strip()
            if not any(candidate.startswith(ref) for ref in refs):
                findings.append(
                    Finding(
                        severity="WARNING",
                        line=block.fields["Source ref"][1],
                        block_id=block.id,
                        message=f"source ref '{candidate}' does not start with a known §1.4 reference",
                        expected=" | ".join(sorted(refs)),
                    )
                )

    return findings


def block_line(blocks: Sequence[Block], block_id: str) -> int:
    for block in blocks:
        if block.id == block_id:
            return block.line
    return 0


def _section_content(sections: Sequence[Section], required: str) -> List[Tuple[int, str]]:
    section = _find_section(sections, required)
    return section.content if section else []


def _blocks_in_section(
    sections: Sequence[Section], required: str, blocks: Sequence[Block]
) -> List[Block]:
    section = _find_section(sections, required)
    if section is None:
        return []
    first = section.heading_line
    last = section.content[-1][0] if section.content else first
    return [block for block in blocks if first <= block.line <= last]


# --------------------------------------------------------------------------
# G0-X: cross-document consistency (StRS + SyRS pair)
# --------------------------------------------------------------------------


def validate_cross_document(
    strs_blocks: Sequence[Block], syrs_blocks: Sequence[Block]
) -> List[Finding]:
    """G0-X rules, evaluated when both GT documents are present.

    - Every STK- StRS block is covered by at least one SYS- `Traces to`.
    - Every `Traces to` value resolves to a real StRS block (NRM-/HWC-/STK-).
    - Block IDs form one namespace: no ID appears in both documents.
    - Every SYS- block cites a normative source (`Standard(s)` never unset).
    """
    findings: List[Finding] = []
    strs_ids = {block.id for block in strs_blocks}
    sys_ids = {block.id for block in syrs_blocks}
    covered: set = set()

    for block in syrs_blocks:
        raw = block.fields.get("Traces to", ("", block.line))[0]
        if not is_unset(raw):
            targets = _STRS_TOKEN_RE.findall(cell_text(raw))
            if not targets:
                findings.append(
                    Finding(
                        severity="ERROR",
                        line=block.fields["Traces to"][1],
                        block_id=block.id,
                        message=(
                            "'Traces to' does not reference any StRS block ID"
                        ),
                        expected=STRS_ID_PATTERN_TEXT,
                        doc="SyRS",
                    )
                )
            for target in targets:
                covered.add(target)
                if target not in strs_ids:
                    findings.append(
                        Finding(
                            severity="ERROR",
                            line=block.fields["Traces to"][1],
                            block_id=block.id,
                            message=f"'Traces to' target '{target}' does not exist in the StRS",
                            expected="an NRM-, HWC-, or STK- block ID declared in the StRS",
                            doc="SyRS",
                        )
                    )

        std_raw = block.fields.get("Standard(s)", ("", block.line))[0]
        if "Standard(s)" not in block.fields or is_unset(std_raw):
            findings.append(
                Finding(
                    severity="ERROR",
                    line=block.line,
                    block_id=block.id,
                    message="no normative source cited — 'Standard(s)' is missing or unset",
                    expected="a concrete normative reference",
                    doc="SyRS",
                )
            )

    for block in strs_blocks:
        if strs_block_kind(block.id) == "STK" and block.id not in covered:
            findings.append(
                Finding(
                    severity="ERROR",
                    line=block.line,
                    block_id=block.id,
                    message=(
                        "stakeholder requirement has no SyRS specification — "
                        "no SYS- block traces to it"
                    ),
                    expected="at least one SYS- block with 'Traces to' naming this ID",
                    doc="StRS",
                )
            )

    for block in syrs_blocks:
        if block.id in strs_ids:
            findings.append(
                Finding(
                    severity="ERROR",
                    line=block.line,
                    block_id=block.id,
                    message="block ID collides with a StRS block ID (shared namespace)",
                    expected="an ID unique across StRS + SyRS",
                    doc="SyRS",
                )
            )

    return findings


# --------------------------------------------------------------------------
# Report
# --------------------------------------------------------------------------


def format_report(path: str, doc_type: str, findings: Sequence[Finding]) -> str:
    ordered = sorted(findings, key=lambda f: f.line)
    errors = [f for f in ordered if f.severity == "ERROR"]
    warnings = [f for f in ordered if f.severity == "WARNING"]

    result = "FAIL" if errors else "PASS"
    lines = [
        "G0 VALIDATION REPORT",
        "====================",
        f"Document: {doc_type}",
        f"File: {path}",
        f"Result: {result} ({len(errors)} errors, {len(warnings)} warnings)",
    ]

    if errors:
        lines.append("")
        lines.append("ERRORS:")
        for position, finding in enumerate(errors, start=1):
            lines.append(_render_finding("E", position, finding))

    if warnings:
        lines.append("")
        lines.append("WARNINGS:")
        for position, finding in enumerate(warnings, start=1):
            lines.append(_render_finding("W", position, finding))

    return "\n".join(lines)


def format_cross_document_report(
    strs_path: str, syrs_path: str, findings: Sequence[Finding]
) -> str:
    """Report for the G0-X pair rules; each finding names its document."""
    ordered = sorted(findings, key=lambda f: f.line)
    errors = [f for f in ordered if f.severity == "ERROR"]
    warnings = [f for f in ordered if f.severity == "WARNING"]

    result = "FAIL" if errors else "PASS"
    lines = [
        "G0-X CROSS-DOCUMENT REPORT",
        "==========================",
        f"StRS: {strs_path}",
        f"SyRS: {syrs_path}",
        f"Result: {result} ({len(errors)} errors, {len(warnings)} warnings)",
    ]

    if errors:
        lines.append("")
        lines.append("ERRORS:")
        for position, finding in enumerate(errors, start=1):
            lines.append(_render_finding("E", position, finding, with_doc=True))

    if warnings:
        lines.append("")
        lines.append("WARNINGS:")
        for position, finding in enumerate(warnings, start=1):
            lines.append(_render_finding("W", position, finding, with_doc=True))

    return "\n".join(lines)


def format_gate_report(findings: Sequence[Finding]) -> str:
    """Report for an incomplete StRS/SyRS pair (gate-level findings)."""
    errors = [f for f in findings if f.severity == "ERROR"]
    warnings = [f for f in findings if f.severity == "WARNING"]
    result = "FAIL" if errors else "PASS"
    lines = [
        "G0 GATE REPORT",
        "==============",
        f"Result: {result} ({len(errors)} errors, {len(warnings)} warnings)",
    ]
    if errors:
        lines.append("")
        lines.append("ERRORS:")
        for position, finding in enumerate(errors, start=1):
            lines.append(_render_finding("E", position, finding))
    if warnings:
        lines.append("")
        lines.append("WARNINGS:")
        for position, finding in enumerate(warnings, start=1):
            lines.append(_render_finding("W", position, finding))
    return "\n".join(lines)


def _render_finding(
    prefix: str, position: int, finding: Finding, with_doc: bool = False
) -> str:
    tag = f"[{prefix}{position:03d}]"
    where = f" [{finding.doc}]" if with_doc and finding.doc else ""
    scope = f"{finding.block_id} \u2014 " if finding.block_id else ""
    line = f"{tag} Line {finding.line}{where}: {scope}{finding.message}"
    if finding.expected:
        line += f". Expected: {finding.expected}"
    return line


# --------------------------------------------------------------------------
# Orchestration
# --------------------------------------------------------------------------


def _read_lines(path: str) -> List[str]:
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return handle.read().splitlines()
    except OSError as exc:
        print(f"error: cannot read '{path}': {exc}", file=sys.stderr)
        raise SystemExit(2)


def validate_file(path: str) -> Tuple[str, List[Finding]]:
    """Validate one file (Phases 1-4, per document). Raises SystemExit(2) on a
    script-level error."""
    lines = _read_lines(path)

    sections = parse_markdown(lines)
    doc_type = detect_doc_type(sections)
    if doc_type is None:
        print(
            f"error: cannot detect document type for '{path}' - "
            "expected a '## Stakeholder Requirements Specification (StRS)' or "
            "'## System Requirements Specification (SyRS)' heading",
            file=sys.stderr,
        )
        raise SystemExit(2)

    findings: List[Finding] = []
    findings.extend(validate_sections(sections, doc_type))
    findings.extend(validate_metadata(sections))

    blocks = parse_blocks(lines, doc_type)
    findings.extend(validate_blocks(blocks, doc_type))
    findings.extend(validate_cross_refs(blocks, sections, doc_type))

    return doc_type, findings


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="g0_validate.py",
        description=(
            "Deterministic structural validation of V-SIL StRS/SyRS Ground Truth documents."
        ),
    )
    parser.add_argument(
        "files",
        nargs="+",
        metavar="file",
        help="path to a GT .md file (StRS or SyRS); pass both for the G0 gate",
    )
    args = parser.parse_args(argv)

    exit_code = 0
    reports: List[str] = []
    detected: Dict[str, str] = {}  # path -> doc_type, in input order
    order: List[str] = []

    for path in args.files:
        doc_type, findings = validate_file(path)
        detected[path] = doc_type
        order.append(path)
        reports.append(format_report(path, doc_type, findings))
        if any(finding.severity == "ERROR" for finding in findings):
            exit_code = 1

    strs_path = next((p for p in order if detected[p] == "StRS"), None)
    syrs_path = next((p for p in order if detected[p] == "SyRS"), None)

    if strs_path is not None and syrs_path is not None:
        strs_blocks = parse_blocks(_read_lines(strs_path), "StRS")
        syrs_blocks = parse_blocks(_read_lines(syrs_path), "SyRS")
        g0x = validate_cross_document(strs_blocks, syrs_blocks)
        reports.append(format_cross_document_report(strs_path, syrs_path, g0x))
        if any(finding.severity == "ERROR" for finding in g0x):
            exit_code = 1
    else:
        # Gate logic: G0 needs the pair.
        gate_findings: List[Finding] = []
        if strs_path is None:
            gate_findings.append(
                Finding(
                    severity="ERROR",
                    line=1,
                    block_id="",
                    message="G0 requires a StRS document — none provided",
                    expected="a file with a '## Stakeholder Requirements Specification (StRS)' heading",
                )
            )
        if syrs_path is None:
            gate_findings.append(
                Finding(
                    severity="ERROR",
                    line=1,
                    block_id="",
                    message="G0 requires a SyRS document — none provided",
                    expected="a file with a '## System Requirements Specification (SyRS)' heading",
                )
            )
        reports.append(format_gate_report(gate_findings))
        exit_code = 1

    print("\n\n".join(reports))
    return exit_code


if __name__ == "__main__":
    sys.exit(main())

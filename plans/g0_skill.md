# Plan: G0 Deterministic Validation Script

## Context

G0 is the first gate in V-SIL. It structurally validates Ground Truth documents (SRS and HCS) against the IEEE 29148 templates (`templates/GT/G0_SRS.md`, `templates/GT/G0_HCS.md`). The `SKILL.md` at `templates/skills/G0_valid_req_and_GT/SKILL.md` was written with the full spec. The script (`scripts/g0_validate.py`) is empty and needs implementation.

The script is **deterministic** (no AI), **stdlib-only** Python, reads `.md` files, prints a structured report to stdout that an LLM can act on (line numbers, block IDs, expected values).

## File to create

```
templates/skills/G0_valid_req_and_GT/scripts/g0_validate.py
```

## Implementation

### 1. Markdown parser (`parse_markdown`)

- Read file line by line, track line numbers (1-indexed).
- Build a flat list of sections from `#`, `##`, `###`, `####` headings.
- Each section: `{level, title, line_start, line_end, raw_lines}`.
- Parse markdown tables within sections into list-of-dicts (key = left column stripped of `**`, value = right column).

### 2. Document type detection (`detect_doc_type`)

- Scan the first `## ` heading for "System Requirements Specification" → `SRS`.
- Or "Hardware Constraints Specification" → `HCS`.
- If neither → ERROR, exit 2.

### 3. Section structure validation (`validate_sections`)

Check required headings exist. Required sections defined as constants:

```python
SRS_REQUIRED = [
    "## Document Metadata",
    "### 1.1 Purpose", "### 1.2 Scope",
    "### 1.3 Definitions, Acronyms, and Abbreviations",
    "### 1.4 References", "### 1.5 Document Overview",
    "### 2.1 Product Perspective", "### 2.2 Product Functions",
    "### 2.3 User Characteristics", "### 2.4 Constraints",
    "### 2.5 Assumptions and Dependencies",
    "## 3. Specific Requirements",
    "## 4. External Interface Requirements",
    "## 5. Non-Functional Requirements",
    "## 6. Traceability",
]

HCS_REQUIRED = [
    "## Document Metadata",
    "### 1.1 Purpose", "### 1.2 Scope",
    "### 1.3 Definitions, Acronyms, and Abbreviations",
    "### 1.4 References", "### 1.5 Hardware Inventory",
    "### 2.1 Block Diagram", "### 2.2 Bus and Interface Topology",
    "## 3. Hardware Constraints",
    "## 4. Derived Constraints",
]
```

Matching by substring on heading text (normalized: stripped, lowercased) to tolerate minor formatting.

### 4. Metadata validation (`validate_metadata`)

Parse table under `## Document Metadata`. Check fields: Document ID, Project, Organization, Version, Classification. Version must match `^\d+\.\d+\.\d+$`. Classification must be one of `PUBLIC | INTERNAL | CONFIDENTIAL`. Flag placeholders (values starting with `_` or containing template markers like `_ACRONYM_`, `_NNN_`, `YYYY-MM-DD`).

### 5. Block parsing (`parse_blocks`)

Scan for bold-code-dash heading pattern:

- SRS: `` **`[A-Z]{3,5}-[A-Z]{2,4}-\d{3}` — `` → requirement block
- HCS: `` **`HWC-[A-Z]{2,4}-\d{3}` — `` → constraint block

For each block, collect until next block heading or `---`:
- Parse field table (rows like `| **Key** | value |`)
- Look for `**Description:**` and capture text
- Look for `**Acceptance Criteria:**` and count numbered items
- Parse Dependencies field into list of IDs

```python
@dataclass
class Block:
    id: str
    title: str
    line: int           # where block heading starts (1-indexed)
    fields: dict        # {"Type": "FUNCTIONAL", "Priority": "MUST", ...}
    has_description: bool
    description_text: str
    has_criteria: bool
    criteria_count: int
    dependencies: list  # parsed from Dependencies field
```

### 6. Block field validation (`validate_blocks`)

Enum values as constants:

```python
SRS_ENUMS = {
    "Type": {"FUNCTIONAL", "NON_FUNCTIONAL", "INTERFACE", "CONSTRAINT"},
    "Priority": {"MUST", "SHOULD", "COULD", "WONT"},
    "Status": {"PROPOSED", "APPROVED", "IMPLEMENTED", "VERIFIED", "REJECTED"},
    "Verification": {"INSPECTION", "DEMONSTRATION", "TEST", "ANALYSIS"},
}
SRS_REQUIRED_FIELDS = {"Type", "Priority", "Status", "Verification"}

HCS_ENUMS = {
    "Limit type": {"MAX", "MIN", "RANGE", "FIXED", "ENUM"},
    "Source": {"DATASHEET", "DRIVER_API", "MEASURED", "DERIVED"},
    "Impact": {"HARD", "SOFT", "INFORMATIONAL"},
    "Status": {"CONFIRMED", "PRELIMINARY", "DEPRECATED"},
}
HCS_REQUIRED_FIELDS = {"Component", "Parameter", "Limit type", "Source", "Source ref", "Impact", "Status"}
```

Per-block:
- ID uniqueness
- Title ≤ 120 chars
- Required fields present
- Enum values valid
- SRS: Description present, SHALL/SHOULD keyword (WARNING), acceptance criteria ≥ 1
- HCS: RANGE → value_min + value_max present; non-RANGE → value present; component exists in inventory

### 7. Cross-reference checks (`validate_cross_refs`)

- **Dependencies (SRS):** directed graph ID → deps. All targets exist. Cycle detection via DFS.
- **Traceability (SRS):** parse §6 table first column, compare against §3 block IDs. Missing = WARNING.
- **Component existence (HCS):** parse §1.5 inventory, extract component IDs. Block's Component must exist.
- **Source ref existence (HCS):** parse §1.4 table, extract ref IDs. Block's Source ref should start with a known ref. Severity: WARNING.

### 8. Report formatting (`format_report`)

```python
@dataclass
class Finding:
    severity: str       # "ERROR" | "WARNING"
    line: int           # 1-indexed
    block_id: str       # or "" for doc-level
    message: str
    expected: str       # or ""
```

Output format:

```
G0 VALIDATION REPORT
====================
Document: SRS | HCS
File: <path>
Result: PASS | FAIL (<N> errors, <M> warnings)

ERRORS:
[E001] Line <n>: <block ID> — <message>. Expected: <values>
[E002] Line <n>: <block ID> — <message>

WARNINGS:
[W001] Line <n>: <block ID> — <message>
```

Sort findings by line number. Errors block the gate (exit 1), warnings don't (exit 0).

### 9. CLI (`main`)

```
python g0_validate.py <file> [<file> ...]
```

Exit codes: 0 = pass, 1 = errors found, 2 = script error.

## Verification

```bash
python templates/skills/G0_valid_req_and_GT/scripts/g0_validate.py \
  methodology/test/T0_ANE-Lap2/just-edge/SRS.md \
  methodology/test/T0_ANE-Lap2/just-edge/HCS.md
```

Both ANE examples should pass or show only minor warnings — they were written to match the v3 templates.

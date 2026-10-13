# G0 Validation Rules — Reference

Full detail behind [SKILL.md](../SKILL.md). The authoritative structure definitions are the
templates: `templates/GT/G0_SRS.md` and `templates/GT/G0_HCS.md` (repository-root relative).

G0 answers one question: **does the document follow the IEEE 29148 structure defined in the
templates?** It does not evaluate requirement quality, correctness of constraint values, or
SRS↔HCS consistency.

## Invocation

```bash
python templates/skills/G0_valid_req_and_GT/scripts/g0_validate.py <file> [<file> ...]
```

Each `<file>` is a GT document; the type (SRS/HCS) is auto-detected from the first `## `
heading.

| Exit | Meaning |
|------|---------|
| 0 | All files passed — no errors |
| 1 | At least one file has structural errors |
| 2 | Script error (bad arguments, unreadable file, undetectable doc type) |

## Phase 1 — Document-level structure

Checks that required headings exist. Matching is by substring on the normalized heading text
(stripped, lowercased) so minor formatting differences pass.

**SRS:** `## Document Metadata`, `### 1.1 Purpose`, `### 1.2 Scope`,
`### 1.3 Definitions, Acronyms, and Abbreviations`, `### 1.4 References`,
`### 1.5 Document Overview`, `### 2.1 Product Perspective`, `### 2.2 Product Functions`,
`### 2.3 User Characteristics`, `### 2.4 Constraints`, `### 2.5 Assumptions and Dependencies`,
`## 3. Specific Requirements`, `## 4. External Interface Requirements`,
`## 5. Non-Functional Requirements`, `## 6. Traceability`.

**HCS:** `## Document Metadata`, `### 1.1 Purpose`, `### 1.2 Scope`,
`### 1.3 Definitions, Acronyms, and Abbreviations`, `### 1.4 References`,
`### 1.5 Hardware Inventory`, `### 2.1 Block Diagram`, `### 2.2 Bus and Interface Topology`,
`## 3. Hardware Constraints`, `## 4. Derived Constraints`.

## Phase 2 — Metadata table

The `## Document Metadata` section must hold a table with a bold key in the left column.

| Required field | Validation |
|----------------|------------|
| Document ID | Non-empty, not a placeholder |
| Project | Non-empty, not a placeholder |
| Organization | Non-empty, not a placeholder |
| Version | Matches SemVer `X.Y.Z` |
| Classification | One of `PUBLIC`, `INTERNAL`, `CONFIDENTIAL` |

A **placeholder** is any value starting with `_`, or containing `_ACRONYM_`, `_NNN_`,
`_project_name_`, or `YYYY-MM-DD`.

## Phase 3 — Block parsing and field validation

Blocks are detected by the heading pattern `` **`<ID>` — <TITLE>** ``. For SRS, `<ID>` must
match `^[A-Z]{3,5}-[A-Z]{2,4}-\d{3}$`; for HCS, `^HWC-[A-Z]{2,4}-\d{3}$`. The detector is
deliberately loose so a malformed ID is still captured and reported as an ERROR.

### SRS requirement blocks

| Rule | Check | Severity |
|------|-------|----------|
| ID format | Matches `^[A-Z]{3,5}-[A-Z]{2,4}-\d{3}$` | ERROR |
| ID uniqueness | No duplicate IDs in the document | ERROR |
| Title length | ≤ 120 characters | ERROR |
| Required fields | Contains Type, Priority, Status, Verification | ERROR |
| Type enum | `FUNCTIONAL` \| `NON_FUNCTIONAL` \| `INTERFACE` \| `CONSTRAINT` | ERROR |
| Priority enum | `MUST` \| `SHOULD` \| `COULD` \| `WONT` | ERROR |
| Status enum | `PROPOSED` \| `APPROVED` \| `IMPLEMENTED` \| `VERIFIED` \| `REJECTED` | ERROR |
| Verification enum | `INSPECTION` \| `DEMONSTRATION` \| `TEST` \| `ANALYSIS` | ERROR |
| Description present | A `**Description:**` line exists after the table | ERROR |
| SHALL/SHOULD keyword | Description contains "SHALL" or "SHOULD" | WARNING |
| Acceptance criteria | A `**Acceptance Criteria:**` line exists | ERROR |
| Criteria count | ≥ 1 numbered item after the heading | ERROR |
| Dependency existence | Every Dependencies ID exists as a block ID in the document | ERROR |

### HCS constraint blocks

| Rule | Check | Severity |
|------|-------|----------|
| ID format | Matches `^HWC-[A-Z]{2,4}-\d{3}$` | ERROR |
| ID uniqueness | No duplicate IDs | ERROR |
| Title length | ≤ 120 characters | ERROR |
| Required fields | Contains Component, Parameter, Limit type, Source, Source ref, Impact, Status | ERROR |
| Limit type enum | `MAX` \| `MIN` \| `RANGE` \| `FIXED` \| `ENUM` | ERROR |
| Source enum | `DATASHEET` \| `DRIVER_API` \| `MEASURED` \| `DERIVED` | ERROR |
| Impact enum | `HARD` \| `SOFT` \| `INFORMATIONAL` | ERROR |
| Status enum | `CONFIRMED` \| `PRELIMINARY` \| `DEPRECATED` | ERROR |
| RANGE fields | Limit type `RANGE` requires both Value min and Value max | ERROR |
| Non-RANGE value | Any other Limit type requires a non-empty Value | ERROR |
| Component existence | Component is listed in the §1.5 Hardware Inventory | ERROR |
| Source ref existence | Source ref starts with a §1.4 References entry | WARNING |

## Phase 4 — Cross-checks within one document

**SRS only**

| Rule | Check | Severity |
|------|-------|----------|
| Traceability coverage | Every §3 requirement ID appears in the §6 table | WARNING |
| Circular dependencies | The dependency graph is acyclic (DFS) | ERROR |

**HCS only**

| Rule | Check | Severity |
|------|-------|----------|
| No orphan components | Every Component ID exists in the §1.5 inventory | ERROR |

## Output format

Printed to stdout, one line per finding, sorted by line number. Optimized for LLM
consumption: line numbers let an agent `Edit` precisely, block IDs name the block to fix, and
`Expected:` gives the valid values without a lookup.

```
G0 VALIDATION REPORT
====================
Document: SRS | HCS
File: <path>
Result: PASS | FAIL (<N> errors, <M> warnings)

ERRORS:
[E001] Line <n>: <block ID> — <what is wrong>. Expected: <valid values>
[E002] Line <n>: <block ID> — <what is wrong>

WARNINGS:
[W001] Line <n>: <block ID> — <what is wrong>
[W002] Line <n>: <block ID> — <what is wrong>
```

Errors block the gate (exit 1); warnings are reported but do not block (exit 0). With multiple
files each gets its own report, and the exit code is the worst result across files.

## Script architecture

`scripts/g0_validate.py` — Python 3.9+, stdlib only (`re`, `sys`, `argparse`, `dataclasses`).
No AI, no network, no filesystem writes: it reads the input `.md` files, prints to stdout, and
exits.

```
g0_validate.py
├── parse_markdown(lines) -> [Section]
│     Flat list of heading sections; each carries its content lines with line numbers.
├── detect_doc_type(sections) -> "SRS" | "HCS" | None
│     Reads the first `## ` heading. None triggers exit 2.
├── validate_sections(sections, doc_type) -> [Finding]        # Phase 1
├── validate_metadata(sections) -> [Finding]                  # Phase 2
├── parse_blocks(lines, doc_type) -> [Block]                  # Phase 3 parse
├── validate_blocks(blocks, doc_type) -> [Finding]            # Phase 3 validate
├── validate_cross_refs(blocks, sections, doc_type) -> [Finding]  # Phase 4
├── format_report(path, doc_type, findings) -> str
└── main()   argparse, per-file loop, worst-case exit code
```

Data structures:

```python
@dataclass
class Finding:
    severity: str       # "ERROR" | "WARNING"
    line: int           # 1-indexed line in the source file
    block_id: str       # requirement/constraint ID, or "" for doc-level
    message: str        # what is wrong
    expected: str       # valid values, or "" when not applicable

@dataclass
class Block:
    id: str
    title: str
    line: int           # line where the block heading starts
    fields: dict        # {name: (raw_value, line_number)}
    has_description: bool
    description_text: str
    has_criteria: bool
    criteria_count: int
    dependencies: list  # IDs parsed from the Dependencies field
```

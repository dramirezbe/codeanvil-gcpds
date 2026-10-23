# G0 Validation Rules — Reference

Full detail behind [SKILL.md](../SKILL.md). The authoritative structure definitions are the
templates: `templates/GT/G0_StRS.md` and `templates/GT/G0_SyRS.md` (repository-root relative).

G0 answers one question: **do the two Ground Truth documents follow the IEEE 29148:2018
structure defined in the templates?** The StRS is the stakeholder view (IEEE 29148 §9.4,
including the COTS hardware envelope as HWC- blocks and inline compliance traceability); the
SyRS is the per-measurand system view (§9.5) derived from it. G0 does not evaluate
requirement quality, measurement-method correctness, or metrological rigor.

## Invocation

```bash
python templates/skills/G0_valid_req_and_GT/scripts/g0_validate.py <StRS.md> <SyRS.md>
```

Each `<file>` is a GT document; the type (StRS/SyRS) is auto-detected from the first `## `
heading. **G0 is a pair gate**: both documents must be provided. Each file gets its own
validation report; when both are present a third G0-X cross-document report is emitted; when
either half is missing a G0 GATE REPORT names it.

| Exit | Meaning |
|------|---------|
| 0 | Both files passed and the pair is consistent — no errors |
| 1 | At least one file has structural errors, G0-X errors, or the pair is incomplete |
| 2 | Script error (bad arguments, unreadable file, undetectable doc type) |

## Phase 1 — Document-level structure

Checks that required headings exist. Matching is by substring on the normalized heading text
(stripped, lowercased) so minor formatting differences pass.

**StRS** (18 headings): `## Document Metadata`, `### 1.1 Purpose`, `### 1.2 Scope`,
`### 1.3 Definitions, Acronyms, and Abbreviations`, `### 1.4 References`,
`### 1.5 Document Overview`, `### 1.6 Hardware Inventory`, `### 2.1 Product Perspective`,
`### 2.2 Product Functions`, `### 2.3 User Characteristics`, `### 2.4 Constraints`,
`### 2.5 Assumptions and Dependencies`, `### 2.6 Block Diagram`,
`### 2.7 Bus and Interface Topology`, `## 3. Specific Requirements`,
`## 4. External Interface Requirements`, `## 5. Non-Functional Requirements`,
`## 6. Traceability`.

**SyRS** (15 headings): `## Document Metadata`, `### 1.1 Purpose`, `### 1.2 Scope`,
`### 1.3 Definitions, Acronyms, and Abbreviations`, `### 1.4 References`,
`### 1.5 Document Overview`, `## 2. Measurement Framework`, `### 2.1 Measurand Catalog`,
`### 2.2 Method Selection and Rationale`, `### 2.3 Normative-to-Method Mapping`,
`## 3. System Requirements`, `## 4. Correction Chains`, `## 5. Uncertainty Budgets`,
`## 6. Field Measurement Protocols`, `## 7. Traceability`.

## Phase 2 — Metadata table

The `## Document Metadata` section must hold a table with a bold key in the left column.
The same rules apply to both document types.

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

Blocks are detected by the heading pattern `` **`<ID>` — <TITLE>** ``. The detector is
deliberately loose so a malformed ID is still captured and reported as an ERROR.

Block ID patterns:

| Kind | Pattern | Where |
|------|---------|-------|
| NRM (normative obligation) | `^NRM-[A-Z]{2,8}-\d{3}$` | StRS |
| HWC (COTS constraint) | `^HWC-[A-Z]{2,4}-\d{3}$` | StRS |
| STK (stakeholder requirement) | `^STK-[A-Z]{2,4}-\d{3}$` | StRS |
| SYS (system specification) | `^SYS-[A-Z]{2,4}-\d{3}$` | SyRS |

Rules common to every block (both documents): ID format ERROR, ID uniqueness ERROR,
title ≤ 120 characters ERROR.

### StRS — STK blocks (stakeholder requirements)

| Rule | Check | Severity |
|------|-------|----------|
| Required fields | Type, Priority, Status, Verification, Compliance | ERROR |
| Compliance rows present | Standard(s) and Clause rows exist (em dash allowed) | ERROR |
| Type enum | `FUNCTIONAL` \| `NON_FUNCTIONAL` \| `INTERFACE` \| `CONSTRAINT` | ERROR |
| Priority enum | `MUST` \| `SHOULD` \| `COULD` \| `WONT` | ERROR |
| Status enum | `PROPOSED` \| `APPROVED` \| `IMPLEMENTED` \| `VERIFIED` \| `REJECTED` | ERROR |
| Verification enum | `INSPECTION` \| `DEMONSTRATION` \| `TEST` \| `ANALYSIS` | ERROR |
| Compliance enum | `COMPLIANT` \| `PARTIAL` \| `NOT_APPLICABLE` \| `PENDING` | ERROR |
| Description present | A `**Description:**` line exists after the table | ERROR |
| SHALL/SHOULD keyword | Description contains "SHALL" or "SHOULD" | WARNING |
| Acceptance criteria | A `**Acceptance Criteria:**` line exists | ERROR |
| Criteria count | ≥ 1 numbered item after the heading | ERROR |

### StRS — NRM blocks (normative obligations)

| Rule | Check | Severity |
|------|-------|----------|
| Required fields | Priority, Status, Standard(s), Clause, Compliance | ERROR |
| Standard(s) concrete | Never an em dash / unset — a normative obligation always cites its source | ERROR |
| Clause concrete | Never an em dash / unset | ERROR |
| Priority enum | `MUST` \| `SHOULD` \| `COULD` \| `WONT` | ERROR |
| Status enum | `PROPOSED` \| `APPROVED` \| `IMPLEMENTED` \| `VERIFIED` \| `REJECTED` | ERROR |
| Compliance enum | `COMPLIANT` \| `PARTIAL` \| `NOT_APPLICABLE` \| `PENDING` | ERROR |
| Description present | A `**Description:**` line exists after the table | ERROR |
| SHALL/SHOULD keyword | Description contains "SHALL" or "SHOULD" | WARNING |
| Acceptance criteria | A `**Acceptance Criteria:**` line exists | ERROR |
| Criteria count | ≥ 1 numbered item after the heading | ERROR |

NRM blocks do **not** require Type or Verification.

### StRS — HWC blocks (COTS platform constraints)

| Rule | Check | Severity |
|------|-------|----------|
| Required fields | Component, Parameter, Limit type, Source, Source ref, Impact, Status, Compliance | ERROR |
| Compliance rows present | Standard(s) and Clause rows exist (em dash allowed) | ERROR |
| Limit type enum | `MAX` \| `MIN` \| `RANGE` \| `FIXED` \| `ENUM` | ERROR |
| Source enum | `DATASHEET` \| `DRIVER_API` \| `MEASURED` \| `DERIVED` | ERROR |
| Impact enum | `HARD` \| `SOFT` \| `INFORMATIONAL` | ERROR |
| Status enum | `CONFIRMED` \| `PRELIMINARY` \| `DEPRECATED` | ERROR |
| Compliance enum | `COMPLIANT` \| `PARTIAL` \| `NOT_APPLICABLE` \| `PENDING` | ERROR |
| RANGE fields | Limit type `RANGE` requires both Value min and Value max | ERROR |
| Non-RANGE value | Any other Limit type requires a non-empty Value | ERROR |

HWC blocks do **not** require a Description or Acceptance Criteria section.

### SyRS — SYS blocks (system specifications)

SyRS validation is deliberately an MVP: structural only (S18), not full metrological rigor.

| Rule | Check | Severity |
|------|-------|----------|
| Required fields | Type, Parameter, Method, Traces to | ERROR |
| Acceptance criteria | A `**Acceptance Criteria:**` line exists | ERROR |
| Criteria count | ≥ 1 numbered item after the heading | ERROR |

There is no enum check, no SHALL/description rule, and no §7 coverage check for SyRS at G0.

## Phase 4 — Cross-checks within one document (StRS only)

SyRS intra-document checks that need the StRS are part of G0-X below.

| Rule | Check | Severity |
|------|-------|----------|
| Dependency existence | Every Dependencies ID exists as a block ID in the document | ERROR |
| Circular dependencies | The dependency graph is acyclic (DFS) | ERROR |
| Traceability coverage | Every §3 block ID appears in the §6 table | WARNING |
| Component existence | Every HWC Component ID is listed in the §1.6 Hardware Inventory | ERROR |
| Source ref existence | HWC Source ref starts with a §1.4 References entry | WARNING |

## G0-X — Cross-document consistency (StRS + SyRS pair)

Run automatically when both files are provided.

| Rule | Check | Severity |
|------|-------|----------|
| STK coverage | Every STK- block is named by at least one SYS- `Traces to` | ERROR |
| Trace resolvability | Every ID token in a SYS- `Traces to` exists as an NRM-/HWC-/STK- block in the StRS | ERROR |
| Trace token present | A non-empty `Traces to` cell contains at least one well-formed StRS block ID | ERROR |
| Shared namespace | No block ID appears in both documents | ERROR |
| Normative citation | Every SYS- block cites a non-unset `Standard(s)` | ERROR |

`Traces to` may list several StRS IDs (comma-separated, backticked); each is extracted and
checked.

## Output format

Printed to stdout. Each file gets a report sorted by line number; G0-X findings carry a
`[StRS]` or `[SyRS]` tag. Optimized for LLM consumption: line numbers let an agent `Edit`
precisely, block IDs name the block to fix, and `Expected:` gives the valid values without a
lookup.

```
G0 VALIDATION REPORT
====================
Document: StRS | SyRS
File: <path>
Result: PASS | FAIL (<N> errors, <M> warnings)

ERRORS:
[E001] Line <n>: <block ID> — <what is wrong>. Expected: <valid values>

WARNINGS:
[W001] Line <n>: <block ID> — <what is wrong>
```

```
G0-X CROSS-DOCUMENT REPORT
==========================
StRS: <path>
SyRS: <path>
Result: PASS | FAIL (<N> errors, <M> warnings)

ERRORS:
[E001] Line <n> [SyRS]: <block ID> — <what is wrong>. Expected: <valid values>
```

When the pair is incomplete:

```
G0 GATE REPORT
==============
Result: FAIL (<N> errors, 0 warnings)

ERRORS:
[E001] Line 1: G0 requires a StRS document — none provided. Expected: ...
```

Errors block the gate (exit 1); warnings are reported but do not block (exit 0).

## Script architecture

`scripts/g0_validate.py` — Python 3.9+, stdlib only (`re`, `sys`, `argparse`, `dataclasses`).
No AI, no network, no filesystem writes: it reads the input `.md` files, prints to stdout, and
exits.

```
g0_validate.py
├── parse_markdown(lines) -> [Section]
│     Flat list of heading sections; each carries its content lines with line numbers.
├── detect_doc_type(sections) -> "StRS" | "SyRS" | None
│     Reads the first `## ` heading. None triggers exit 2.
├── validate_sections(sections, doc_type) -> [Finding]        # Phase 1
├── validate_metadata(sections) -> [Finding]                  # Phase 2
├── parse_blocks(lines, doc_type) -> [Block]                  # Phase 3 parse
├── strs_block_kind(block_id) -> "NRM"|"HWC"|"STK"|None       # StRS kind dispatch
├── validate_blocks(blocks, doc_type) -> [Finding]            # Phase 3 validate
├── validate_cross_refs(blocks, sections, doc_type) -> [Finding]  # Phase 4 (StRS)
├── validate_cross_document(strs_blocks, syrs_blocks) -> [Finding]  # G0-X
├── format_report(path, doc_type, findings) -> str
├── format_cross_document_report(strs_path, syrs_path, findings) -> str
├── format_gate_report(findings) -> str
└── main()   argparse, per-file loop, pair gate, worst-case exit code
```

Data structures:

```python
@dataclass
class Finding:
    severity: str       # "ERROR" | "WARNING"
    line: int           # 1-indexed line in the source file
    block_id: str       # requirement/specification ID, or "" for doc-level
    message: str        # what is wrong
    expected: str       # valid values, or "" when not applicable
    doc: str = ""       # "StRS" | "SyRS" — only set on G0-X findings

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

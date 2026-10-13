# Skill: G0 — Structural Validation of Ground Truth Documents

## Purpose

G0 is the first gate in the V-SIL pipeline. It performs **deterministic, code-only** structural validation of the Ground Truth (GT) documents — SRS and HCS — before any AI-driven gate runs. No LLM is involved in the validation itself; the script produces a stdout report that an LLM (or human) can act on.

G0 answers one question: **does the document follow the IEEE 29148 structure defined in the templates?**

It does NOT evaluate:
- Whether requirements are good, complete, or correct
- Whether constraint values are accurate
- Whether the SRS and HCS are consistent with each other (that is a future gate)

## Reference Templates

The authoritative structure definitions are:

| Document | Template path (relative to CodeAnvil repo root)  |
|----------|--------------------------------------------------|
| SRS      | `templates/GT/G0_SRS.md`                         |
| HCS      | `templates/GT/G0_HCS.md`                         |

When a project is scaffolded, GT files are copied to the project directory. G0 validates those project copies against the rules extracted from the templates above.

## Invocation

```bash
python scripts/g0_validate.py <file> [<file> ...]
```

Each `<file>` is a path to a GT document (SRS or HCS). The script auto-detects the document type from content.

**Exit codes:**

| Code | Meaning                                    |
|------|--------------------------------------------|
| 0    | All files passed — no errors               |
| 1    | At least one file has structural errors    |
| 2    | Script error (bad arguments, file not found, parse failure) |

## What the Script Validates

### Phase 1: Document-level structure

Checks that required top-level sections exist as markdown headings.

**SRS required sections:**

```
## Document Metadata
## 1. Introduction
   ### 1.1 Purpose
   ### 1.2 Scope
   ### 1.3 Definitions, Acronyms, and Abbreviations
   ### 1.4 References
   ### 1.5 Document Overview
## 2. Overall System Description
   ### 2.1 Product Perspective
   ### 2.2 Product Functions
   ### 2.3 User Characteristics
   ### 2.4 Constraints
   ### 2.5 Assumptions and Dependencies
## 3. Specific Requirements
## 4. External Interface Requirements
## 5. Non-Functional Requirements
## 6. Traceability
```

**HCS required sections:**

```
## Document Metadata
## 1. Introduction
   ### 1.1 Purpose
   ### 1.2 Scope
   ### 1.3 Definitions, Acronyms, and Abbreviations
   ### 1.4 References
   ### 1.5 Hardware Inventory
## 2. System Hardware Architecture
   ### 2.1 Block Diagram
   ### 2.2 Bus and Interface Topology
## 3. Hardware Constraints
## 4. Derived Constraints
```

### Phase 2: Metadata table

The `## Document Metadata` section must contain a markdown table with these required rows (left column bold key, right column value):

| Required field   | Validation                                      |
|------------------|-------------------------------------------------|
| Document ID      | Non-empty, not a placeholder pattern            |
| Project          | Non-empty, not a placeholder                    |
| Organization     | Non-empty, not a placeholder                    |
| Version          | Matches SemVer pattern: `X.Y.Z`                |
| Classification   | One of: `PUBLIC`, `INTERNAL`, `CONFIDENTIAL`    |

A "placeholder pattern" is any value that starts with `_` or contains `_ACRONYM_`, `_NNN_`, `_project_name_`, or `YYYY-MM-DD` as the entire value.

### Phase 3: Block parsing and field validation

**SRS requirement blocks** are detected by this heading pattern:

```
**`<ID>` — <TITLE>**
```

Where `<ID>` matches the regex `^[A-Z]{3,5}-[A-Z]{2,4}-\d{3}$`.

For each requirement block, the script validates:

| Rule                  | Check                                                              | Severity |
|-----------------------|--------------------------------------------------------------------|----------|
| ID format             | Matches `^[A-Z]{3,5}-[A-Z]{2,4}-\d{3}$`                          | ERROR    |
| ID uniqueness         | No duplicate IDs in the document                                   | ERROR    |
| Title length          | ≤ 120 characters                                                   | ERROR    |
| Required fields       | Table contains: Type, Priority, Status, Verification               | ERROR    |
| Type enum             | `FUNCTIONAL` \| `NON_FUNCTIONAL` \| `INTERFACE` \| `CONSTRAINT`   | ERROR    |
| Priority enum         | `MUST` \| `SHOULD` \| `COULD` \| `WONT`                          | ERROR    |
| Status enum           | `PROPOSED` \| `APPROVED` \| `IMPLEMENTED` \| `VERIFIED` \| `REJECTED` | ERROR |
| Verification enum     | `INSPECTION` \| `DEMONSTRATION` \| `TEST` \| `ANALYSIS`          | ERROR    |
| Description present   | A line starting with `**Description:**` exists after the table     | ERROR    |
| SHALL/SHOULD keyword  | Description text contains "SHALL" or "SHOULD"                      | WARNING  |
| Acceptance criteria   | A line starting with `**Acceptance Criteria:**` exists             | ERROR    |
| Criteria count        | At least 1 numbered item after the Acceptance Criteria heading     | ERROR    |
| Dependency existence  | Every ID listed in Dependencies exists as a block ID in the doc    | ERROR    |

**HCS constraint blocks** are detected by:

```
**`<ID>` — <TITLE>**
```

Where `<ID>` matches `^HWC-[A-Z]{2,4}-\d{3}$`.

For each constraint block:

| Rule                  | Check                                                              | Severity |
|-----------------------|--------------------------------------------------------------------|----------|
| ID format             | Matches `^HWC-[A-Z]{2,4}-\d{3}$`                                  | ERROR    |
| ID uniqueness         | No duplicate IDs                                                   | ERROR    |
| Title length          | ≤ 120 characters                                                   | ERROR    |
| Required fields       | Table contains: Component, Parameter, Limit type, Source, Source ref, Impact, Status | ERROR |
| Limit type enum       | `MAX` \| `MIN` \| `RANGE` \| `FIXED` \| `ENUM`                   | ERROR    |
| Source enum            | `DATASHEET` \| `DRIVER_API` \| `MEASURED` \| `DERIVED`           | ERROR    |
| Impact enum            | `HARD` \| `SOFT` \| `INFORMATIONAL`                              | ERROR    |
| Status enum            | `CONFIRMED` \| `PRELIMINARY` \| `DEPRECATED`                     | ERROR    |
| RANGE fields          | If Limit type = `RANGE`, both Value min and Value max must exist   | ERROR    |
| Non-RANGE value       | If Limit type ≠ `RANGE`, Value field must exist and be non-empty   | ERROR    |
| Component existence   | Component value exists in the Hardware Inventory table (§1.5)      | ERROR    |
| Source ref existence   | Source ref references an entry from the References table (§1.4)    | WARNING  |

### Phase 4: Cross-checks within one document

**SRS only:**

| Rule                    | Check                                                           | Severity |
|-------------------------|-----------------------------------------------------------------|----------|
| Traceability coverage   | Every requirement ID from §3 appears in the §6 traceability table | WARNING |
| Circular dependencies   | The dependency graph has no cycles                              | ERROR    |

**HCS only:**

| Rule                    | Check                                                           | Severity |
|-------------------------|-----------------------------------------------------------------|----------|
| No orphan components    | Every Component ID used in a constraint exists in §1.5 inventory | ERROR   |

## Output Format

The script prints to **stdout** in a format optimized for LLM consumption — structured, line-numbered, with enough context to fix each issue without re-reading the full document.

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
[W002] Section <s> — <what is wrong>
```

**Design principles for the output:**
- One line per finding — the LLM can parse it without ambiguity.
- Line numbers reference the source `.md` file so the LLM can use `Edit` with precise context.
- Block IDs are included so the LLM knows which requirement/constraint to fix.
- Expected valid values are shown for enum violations — no need to look them up.
- Errors vs. warnings: errors block the gate (exit 1), warnings are reported but don't block (exit 0 if only warnings).

When multiple files are validated in one invocation, each file gets its own report block. The exit code reflects the worst result across all files.

## Script Architecture

```
scripts/g0_validate.py
```

- **Language:** Python 3.9+ (stdlib only — no external dependencies)
- **Modules:** `re`, `sys`, `argparse`, `dataclasses`
- **No AI, no network, no filesystem writes** — reads the input `.md` files, prints to stdout, exits.

### Internal structure

```
g0_validate.py
├── parse_markdown(lines) → SectionTree
│   Builds a tree of heading-level → content from the raw lines.
│   Tracks line numbers for every heading and content block.
│
├── detect_doc_type(tree) → "SRS" | "HCS"
│   Looks for "System Requirements Specification" or
│   "Hardware Constraints Specification" in the first heading.
│
├── validate_sections(tree, doc_type) → [Finding]
│   Checks that all required sections exist (Phase 1).
│
├── validate_metadata(tree) → [Finding]
│   Parses the Document Metadata table and checks required fields (Phase 2).
│
├── parse_blocks(tree, doc_type) → [Block]
│   Extracts requirement or constraint blocks by heading pattern.
│   Each Block has: id, title, line_number, fields (dict), has_description,
│   has_criteria, criteria_count, dependencies.
│
├── validate_blocks(blocks, doc_type) → [Finding]
│   Runs per-block field validation (Phase 3).
│
├── validate_cross_refs(blocks, tree, doc_type) → [Finding]
│   Dependency graph, traceability coverage, component existence (Phase 4).
│
├── format_report(file, doc_type, findings) → str
│   Renders the stdout report.
│
└── main()
    argparse, file loop, exit code.
```

### Data structures

```python
@dataclass
class Finding:
    severity: str       # "ERROR" | "WARNING"
    line: int           # line number in the source file (1-indexed)
    block_id: str       # requirement/constraint ID, or "" for doc-level
    message: str        # human/LLM-readable description
    expected: str       # valid values or "", shown as "Expected: ..."

@dataclass
class Block:
    id: str
    title: str
    line: int           # line where the block heading starts
    fields: dict        # {"Type": "FUNCTIONAL", "Priority": "MUST", ...}
    has_description: bool
    description_text: str
    has_criteria: bool
    criteria_count: int
    dependencies: list  # parsed from Dependencies field
```

## Files in this Skill

```
G0_valid_req_and_GT/
├── SKILL.md                    # This file — skill definition and validation rules
└── scripts/
    └── g0_validate.py          # Deterministic validation script
```

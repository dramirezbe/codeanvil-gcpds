---
name: g0-valid-req-and-gt
description: "G0: Structural validation of SRS/HCS Ground Truth documents"
metadata:
  author: "gcpds"
  version: "1.0"
  gate: "G0"
  pipeline: "V-SIL"
---

# G0 — Structural Validation of Ground Truth

**V-SIL | Gate G0 | No-Tools Variant**

> **Non-determinism disclaimer:** This is LLM-executed structural validation. Results
> are approximate — different models or runs may produce slightly different verdicts on
> the same document. Suitable for quick checks and environments where tool execution is
> unavailable.

## Definitions

| Term | Meaning |
|------|---------|
| **GT** | Ground Truth — the pair of `.md` documents (SRS + HCS) that define the project contract |
| **SRS** | System Requirements Specification — functional and non-functional requirements (IEEE 29148) |
| **HCS** | Hardware Constraints Specification — COTS hardware limits and design constraints (§2.4) |
| **G0** | Gate 0 — structural validation of GT documents. Must pass before any design work |
| **G1** | Gate 1 — agent-driven design synthesis from validated GT |

## Activation Contract

**Load when:**
- The user provides one or two GT documents (SRS and/or HCS) as pasted text or markdown, or attached.
- The user asks for G0 validation, structural check, or GT review.

**Do NOT load when:**
- The user asks about requirement quality, constraint accuracy, or SRS↔HCS consistency — those are later gates.
- The user asks you to write or fix a GT document — G0 only reports, never edits.

## Preconditions

- The user must provide **both an SRS and an HCS**. If only one is provided, ask for the
  other before proceeding. Do not run a partial G0 — the Ground Truth is the pair.
- If the user insists on validating just one, refuse and explain that G0 requires both.

## Decision Gates

| Situation | Action |
|-----------|--------|
| Zero errors (both documents) | Report `G0: PASS`. Warnings are advisory — they do not block. Proceed to G1. |
| One or more errors (either document) | Report `G0: FAIL`. List every error with its ID and what to fix. The user must fix and resubmit. |
| Cannot detect document type | Report `G0: UNDETECTABLE` for that document and stop the entire run — do not continue to the other document. |

---

## Step 1 — Detect document type

Read the document. Identify it as **SRS** or **HCS** from its title heading (any level: `#` or `##`).

- If the title heading contains "System Requirements Specification" or "SRS" → it is an **SRS**.
- If it contains "Hardware Constraints Specification" or "HCS" → it is an **HCS**.
- If you cannot determine the type → report `G0: UNDETECTABLE` and stop the entire run.

If the user pasted two documents, validate each separately. Produce **one report per document**.

---

## Step 2 — Check required sections (Phase 1)

Verify that **every required heading** exists. Match by content, not exact formatting —
minor wording differences are OK as long as the section is clearly present.

### SRS required headings

- `## Document Metadata`
- `### 1.1 Purpose`
- `### 1.2 Scope`
- `### 1.3 Definitions, Acronyms, and Abbreviations`
- `### 1.4 References`
- `### 1.5 Document Overview`
- `### 2.1 Product Perspective`
- `### 2.2 Product Functions`
- `### 2.3 User Characteristics`
- `### 2.4 Constraints`
- `### 2.5 Assumptions and Dependencies`
- `## 3. Specific Requirements`
- `## 4. External Interface Requirements`
- `## 5. Non-Functional Requirements`
- `## 6. Traceability`

### HCS required headings

- `## Document Metadata`
- `### 1.1 Purpose`
- `### 1.2 Scope`
- `### 1.3 Definitions, Acronyms, and Abbreviations`
- `### 1.4 References`
- `### 1.5 Hardware Inventory`
- `### 2.1 Block Diagram`
- `### 2.2 Bus and Interface Topology`
- `## 3. Hardware Constraints`
- `## 4. Derived Constraints`

**Report each missing heading as an ERROR.**

---

## Step 3 — Validate the Metadata table (Phase 2)

The `## Document Metadata` section must contain a table. Check these fields:

| Field | Rule | Severity |
|---|---|---|
| **Document ID** | Row present, non-empty, not a placeholder | ERROR |
| **Project** | Row present, non-empty, not a placeholder | ERROR |
| **Organization** | Row present, non-empty, not a placeholder | ERROR |
| **Version** | Row present, matches SemVer `X.Y.Z` (e.g. `1.0.0`, `0.3.1`) | ERROR |
| **Classification** | Row present, exactly one of: `PUBLIC`, `INTERNAL`, `CONFIDENTIAL` | ERROR |

If a required field row is **missing entirely** from the table, report it as an ERROR (missing field).

**Placeholder detection:** A value is a placeholder if it starts with `_`, or contains
`_ACRONYM_`, `_NNN_`, `_project_name_`, or `YYYY-MM-DD`.

---

## Step 4 — Validate requirement/constraint blocks (Phase 3)

Blocks are detected by their ID pattern and a title separator. Match any of these forms:
- **`ID` — Title** (bold ID, em-dash)
- **`ID` - Title** (bold ID, hyphen)
- **`ID`: Title** (bold ID, colon)
- `### ID — Title` (heading-level block)

If a section (§3 for SRS, §3 for HCS) exists but **zero blocks** are detected in it, report as **ERROR**: "section present but contains no requirement/constraint blocks."

### For SRS requirement blocks

For each block, check:

| Rule | Valid values | Severity |
|---|---|---|
| ID matches `[A-Z]{3,5}-[A-Z]{2,4}-NNN` | e.g. `ANAL-PAR-001` | ERROR |
| No duplicate IDs in the document | — | ERROR |
| Title ≤ 120 characters | — | ERROR |
| **Type** field present and valid | `FUNCTIONAL`, `NON_FUNCTIONAL`, `INTERFACE`, `CONSTRAINT` | ERROR |
| **Priority** field present and valid | `MUST`, `SHOULD`, `COULD`, `WONT` | ERROR |
| **Status** field present and valid | `PROPOSED`, `APPROVED`, `IMPLEMENTED`, `VERIFIED`, `REJECTED` | ERROR |
| **Verification** field present and valid | `INSPECTION`, `DEMONSTRATION`, `TEST`, `ANALYSIS` | ERROR |
| **Description** section exists after the table | — | ERROR |
| Description contains `SHALL` or `SHOULD` | — | WARNING |
| **Acceptance Criteria** section exists | — | ERROR |
| At least 1 numbered criterion listed | — | ERROR |
| Every ID in **Dependencies** that matches the document's own ID pattern exists as a block in the same document | — | ERROR |

**Note on dependencies:** Resolve dependencies within the same document only. An SRS requirement citing an HCS ID (e.g. `HWC-SDR-001`) is a cross-document reference — not an error. Only flag IDs that match the current document's pattern (e.g. `[A-Z]{3,5}-[A-Z]{2,4}-NNN` for SRS) but are missing.

### For HCS constraint blocks

For each block, check:

| Rule | Valid values | Severity |
|---|---|---|
| ID matches `HWC-[A-Z]{2,4}-NNN` | e.g. `HWC-SDR-001` | ERROR |
| No duplicate IDs in the document | — | ERROR |
| Title ≤ 120 characters | — | ERROR |
| **Component** field present | — | ERROR |
| **Parameter** field present | — | ERROR |
| **Limit type** field present and valid | `MAX`, `MIN`, `RANGE`, `FIXED`, `ENUM` | ERROR |
| **Source** field present and valid | `DATASHEET`, `DRIVER_API`, `MEASURED`, `DERIVED` | ERROR |
| **Source ref** field present | — | ERROR |
| **Impact** field present and valid | `HARD`, `SOFT`, `INFORMATIONAL` | ERROR |
| **Status** field present and valid | `CONFIRMED`, `PRELIMINARY`, `DEPRECATED` | ERROR |
| If Limit type = `RANGE`: both **Value min** and **Value max** present | — | ERROR |
| If Limit type ≠ `RANGE`: **Value** is non-empty | — | ERROR |
| **Source ref** starts with a §1.4 References entry | — | WARNING |

**Note:** Component-to-inventory validation is in Step 5 (cross-checks), not here — do not duplicate it.

---

## Step 5 — Cross-checks within the document (Phase 4)

### SRS only

- **Traceability coverage:** Every requirement ID from §3 should appear in the §6
  Traceability table. Report missing ones as **WARNING**.
- **Circular dependencies:** If the dependency graph has cycles, report as **ERROR**.

### HCS only

- **Orphan components:** Every Component value used in a constraint block must exist in
  the §1.5 Hardware Inventory. Report orphans as **ERROR**.

---

## Step 6 — Produce the report

Produce **one report per document**, then a **gate verdict** for the pair.

### Per-document report format

```
G0 VALIDATION REPORT
====================================================
Document: SRS | HCS
Result: PASS | FAIL (N errors, M warnings) | UNDETECTABLE

ERRORS:
[E001] <Block ID or "Metadata"> — <what is wrong>. Expected: <valid values>
[E002] <Block ID or "Section"> — <what is wrong>

WARNINGS:
[W001] <Block ID> — <what is wrong>

SUMMARY:
- Sections: X/Y present
- Metadata fields: X/Y valid (X/Y present)
- Blocks checked: N
- Errors: N (blocking)
- Warnings: M (advisory)
```

### Gate verdict (after both reports)

```
G0 GATE VERDICT: PASS | FAIL
```

## Verdict rules

- **Zero errors in both documents** → `G0: PASS` — warnings are advisory, they do not block.
- **One or more errors in either document** → `G0: FAIL` — list every error with its ID and what to fix.
- **UNDETECTABLE** → `G0: FAIL` — stop the entire run, do not validate the other document.
- Always show the full report for each document, even on PASS.

## After the report

If the verdict is FAIL, end with a **Fix List** — one line per error:
- Block ID → what is wrong → what the valid values are

Do NOT fix the document yourself. Do NOT suggest rewording requirements. Just report
structural problems and move on.


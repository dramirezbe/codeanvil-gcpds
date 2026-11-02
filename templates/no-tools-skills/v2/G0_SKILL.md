---
name: g0-valid-req-and-gt
description: "G0: Structural validation of the StRS/SyRS Ground Truth document pair"
metadata:
  author: "gcpds"
  version: "2.0"
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
| **GT** | Ground Truth — the pair of `.md` documents (StRS + SyRS) that define the project contract |
| **StRS** | Stakeholder Requirements Specification — stakeholder needs, COTS hardware constraints, normative obligations (IEEE 29148 §9.4) |
| **SyRS** | System Requirements Specification — per-measurand system view derived from the StRS: methods, parameters, correction chains, uncertainty budgets (IEEE 29148 §9.5) |
| **G0** | Gate 0 — structural validation of the GT pair. Must pass before any design work |
| **G0-X** | The cross-document consistency check between StRS and SyRS (run as part of G0) |
| **G1** | Gate 1 — agent-driven design synthesis from validated GT, producing the SRS (§9.6) |

## Activation Contract

**Load when:**
- The user provides the GT pair (StRS and SyRS) as pasted text or markdown, or attached.
- The user asks for G0 validation, structural check, or GT review.

**Do NOT load when:**
- The user asks about requirement quality, measurement-method correctness, or metrological
  rigor — those are later gates.
- The user asks you to write or fix a GT document — G0 only reports, never edits.

## Preconditions

- The user must provide **both a StRS and a SyRS**. If only one is provided, ask for the
  other before proceeding. Do not run a partial G0 — the Ground Truth is the pair.
- If the user insists on validating just one, refuse and explain that G0 requires both.

## Decision Gates

| Situation | Action |
|-----------|--------|
| Zero errors (both documents, including G0-X) | Report `G0: PASS`. Warnings are advisory — they do not block. Proceed to G1. |
| One or more errors (either document or G0-X) | Report `G0: FAIL`. List every error with its ID and what to fix. The user must fix and resubmit. |
| Cannot detect document type | Report `G0: UNDETECTABLE` for that document and stop the entire run — do not continue to the other document. |

---

## Step 1 — Detect document type

Read the document. Identify it as **StRS** or **SyRS** from its first `## ` title heading.

- If the heading contains "Stakeholder Requirements Specification" or "StRS" → it is an **StRS**.
- If it contains "System Requirements Specification" or "SyRS" → it is a **SyRS**.
  (Do not confuse it with the full software SRS — that is a G1 product, never a G0 input.)
- If you cannot determine the type → report `G0: UNDETECTABLE` and stop the entire run.

If the user pasted two documents, validate each separately. Produce **one report per document**.

---

## Step 2 — Check required sections (Phase 1)

Verify that **every required heading** exists. Match by content, not exact formatting —
minor wording differences are OK as long as the section is clearly present.

### StRS required headings

- `## Document Metadata`
- `### 1.1 Purpose`
- `### 1.2 Scope`
- `### 1.3 Definitions, Acronyms, and Abbreviations`
- `### 1.4 References`
- `### 1.5 Document Overview`
- `### 1.6 Hardware Inventory`
- `### 2.1 Product Perspective`
- `### 2.2 Product Functions`
- `### 2.3 User Characteristics`
- `### 2.4 Constraints`
- `### 2.5 Assumptions and Dependencies`
- `### 2.6 Block Diagram`
- `### 2.7 Bus and Interface Topology`
- `## 3. Specific Requirements`
- `## 4. External Interface Requirements`
- `## 5. Non-Functional Requirements`
- `## 6. Traceability`

### SyRS required headings

- `## Document Metadata`
- `### 1.1 Purpose`
- `### 1.2 Scope`
- `### 1.3 Definitions, Acronyms, and Abbreviations`
- `### 1.4 References`
- `### 1.5 Document Overview`
- `## 2. Measurement Framework`
- `### 2.1 Measurand Catalog`
- `### 2.2 Method Selection and Rationale`
- `### 2.3 Normative-to-Method Mapping`
- `## 3. System Requirements`
- `## 4. Correction Chains`
- `## 5. Uncertainty Budgets`
- `## 6. Field Measurement Protocols`
- `## 7. Traceability`

**Report each missing heading as an ERROR.**

---

## Step 3 — Validate the Metadata table (Phase 2)

The `## Document Metadata` section must contain a table. The same rules apply to both
document types.

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

## Step 4 — Validate requirement/specification blocks (Phase 3)

Blocks are detected by their ID pattern and a title separator. Match any of these forms:
- **`ID` — Title** (bold ID, em-dash)
- **`ID` - Title** (bold ID, hyphen)
- **`ID`: Title** (bold ID, colon)
- `### ID — Title` (heading-level block)

If §3 exists but **zero blocks** are detected in it, report as **ERROR**: "section present
but contains no blocks."

Block ID patterns:

| Kind | Pattern | Document |
|------|---------|----------|
| NRM (normative obligation) | `NRM-[A-Z]{2,8}-NNN` | StRS |
| HWC (COTS constraint) | `HWC-[A-Z]{2,4}-NNN` | StRS |
| STK (stakeholder requirement) | `STK-[A-Z]{2,4}-NNN` | StRS |
| SYS (system specification) | `SYS-[A-Z]{2,4}-NNN` | SyRS |

### Rules common to every block (both documents)

| Rule | Severity |
|---|---|
| ID matches its kind's pattern | ERROR |
| No duplicate IDs in the document | ERROR |
| Title ≤ 120 characters | ERROR |

### For STK blocks (StRS)

| Rule | Valid values | Severity |
|---|---|---|
| **Type** field present and valid | `FUNCTIONAL`, `NON_FUNCTIONAL`, `INTERFACE`, `CONSTRAINT` | ERROR |
| **Priority** field present and valid | `MUST`, `SHOULD`, `COULD`, `WONT` | ERROR |
| **Status** field present and valid | `PROPOSED`, `APPROVED`, `IMPLEMENTED`, `VERIFIED`, `REJECTED` | ERROR |
| **Verification** field present and valid | `INSPECTION`, `DEMONSTRATION`, `TEST`, `ANALYSIS` | ERROR |
| **Compliance** field present and valid | `COMPLIANT`, `PARTIAL`, `NOT_APPLICABLE`, `PENDING` | ERROR |
| **Standard(s)** and **Clause** rows exist (em dash allowed) | — | ERROR |
| **Description** section exists after the table | — | ERROR |
| Description contains `SHALL` or `SHOULD` | — | WARNING |
| **Acceptance Criteria** section exists | — | ERROR |
| At least 1 numbered criterion listed | — | ERROR |

### For NRM blocks (StRS)

| Rule | Valid values | Severity |
|---|---|---|
| **Priority** field present and valid | `MUST`, `SHOULD`, `COULD`, `WONT` | ERROR |
| **Status** field present and valid | `PROPOSED`, `APPROVED`, `IMPLEMENTED`, `VERIFIED`, `REJECTED` | ERROR |
| **Standard(s)** present and **concrete** (never an em dash — a normative obligation always cites its source) | e.g. `ITU-R SM.1539-2` | ERROR |
| **Clause** present and **concrete** (never an em dash) | e.g. `§5` | ERROR |
| **Compliance** field present and valid | `COMPLIANT`, `PARTIAL`, `NOT_APPLICABLE`, `PENDING` | ERROR |
| **Description** section exists after the table | — | ERROR |
| Description contains `SHALL` or `SHOULD` | — | WARNING |
| **Acceptance Criteria** section exists | — | ERROR |
| At least 1 numbered criterion listed | — | ERROR |

NRM blocks do **not** require Type or Verification.

### For HWC blocks (StRS)

| Rule | Valid values | Severity |
|---|---|---|
| **Component** field present | — | ERROR |
| **Parameter** field present | — | ERROR |
| **Limit type** field present and valid | `MAX`, `MIN`, `RANGE`, `FIXED`, `ENUM` | ERROR |
| **Source** field present and valid | `DATASHEET`, `DRIVER_API`, `MEASURED`, `DERIVED` | ERROR |
| **Source ref** field present | — | ERROR |
| **Impact** field present and valid | `HARD`, `SOFT`, `INFORMATIONAL` | ERROR |
| **Status** field present and valid | `CONFIRMED`, `PRELIMINARY`, `DEPRECATED` | ERROR |
| **Compliance** field present and valid | `COMPLIANT`, `PARTIAL`, `NOT_APPLICABLE`, `PENDING` | ERROR |
| **Standard(s)** and **Clause** rows exist (em dash allowed) | — | ERROR |
| If Limit type = `RANGE`: both **Value min** and **Value max** present | — | ERROR |
| If Limit type ≠ `RANGE`: **Value** is non-empty | — | ERROR |

HWC blocks do **not** require a Description or Acceptance Criteria section.

### For SYS blocks (SyRS)

SyRS validation is deliberately an MVP: structural only, not full metrological rigor.

| Rule | Valid values | Severity |
|---|---|---|
| **Type** field present | — | ERROR |
| **Parameter** field present | — | ERROR |
| **Method** field present | — | ERROR |
| **Traces to** field present | — | ERROR |
| **Standard(s)** present and **concrete** (never an em dash) | e.g. `ITU-R SM.1138-5` | ERROR |
| **Acceptance Criteria** section exists | — | ERROR |
| At least 1 numbered criterion listed | — | ERROR |

There is no enum check, no SHALL/description rule, and no §7 coverage check for SyRS at G0.

---

## Step 5 — Cross-checks

### StRS intra-document (Phase 4)

- **Dependency existence:** Every ID in a **Dependencies** field that matches the StRS
  patterns (`NRM-…`, `HWC-…`, `STK-…`) must exist as a block in the same document.
  Report missing ones as **ERROR**. (Citing a SYS ID from a StRS block is a
  cross-document reference — not an error.)
- **Circular dependencies:** If the dependency graph has cycles, report as **ERROR**.
- **Traceability coverage:** Every §3 block ID (STK/HWC/NRM) should appear in the §6
  Traceability table. Report missing ones as **WARNING**.
- **Orphan components:** Every Component value used in an HWC block must exist in the
  §1.6 Hardware Inventory. Report orphans as **ERROR**.
- **Source ref existence:** Each HWC **Source ref** should start with a §1.4 References
  entry. Report mismatches as **WARNING**.

### G0-X — Cross-document consistency (StRS + SyRS)

Run these checks only after both documents pass their individual checks:

- **STK coverage:** Every STK- block in the StRS must be named by at least one SYS- block's
  **Traces to** field. Report uncovered STKs as **ERROR**.
- **Trace resolvability:** Every ID token in a SYS- **Traces to** field must exist as an
  NRM-/HWC-/STK- block in the StRS. Report unresolvable tokens as **ERROR**.
- **Trace token present:** A non-empty **Traces to** cell must contain at least one
  well-formed StRS block ID (`NRM-…`, `HWC-…`, or `STK-…`). Report empty token lists as
  **ERROR**.
- **Shared namespace:** No block ID may appear in both documents. Report collisions as
  **ERROR**.
- **Normative citation:** Every SYS- block must cite a concrete **Standard(s)** (never an
  em dash). Report missing citations as **ERROR**.

Tag every G0-X finding with the offending document (`[StRS]` or `[SyRS]`) and the block ID.

---

## Step 6 — Produce the report

Produce **one report per document**, then the **G0-X report**, then a **gate verdict** for
the pair.

### Per-document report format

```
G0 VALIDATION REPORT
====================================================
Document: StRS | SyRS
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

### G0-X report format

```
G0-X CROSS-DOCUMENT REPORT
====================================================
Result: PASS | FAIL (N errors, M warnings)

ERRORS:
[E001] [SyRS] <Block ID> — <what is wrong>. Expected: <valid values>

SUMMARY:
- STK blocks: N; covered: M
- Traces to tokens: N; unresolvable: M
```

### Gate verdict (after both reports + G0-X)

```
G0 GATE VERDICT: PASS | FAIL
```

## Verdict rules

- **Zero errors in both documents and G0-X** → `G0: PASS` — warnings are advisory, they do not block.
- **One or more errors in either document or G0-X** → `G0: FAIL` — list every error with its ID and what to fix.
- **UNDETECTABLE** → `G0: FAIL` — stop the entire run, do not validate the other document.
- Always show the full report for each document, even on PASS.

## After the report

If the verdict is FAIL, end with a **Fix List** — one line per error:
- Block ID → what is wrong → what the valid values are

Do NOT fix the document yourself. Do NOT suggest rewording requirements. Just report
structural problems and move on.

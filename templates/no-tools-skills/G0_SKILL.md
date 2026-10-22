---
name: g0-valid-req-and-gt-no-tools
description: "Web-chat G0: LLM-executed structural validation of SRS/HCS Ground Truth documents. No tools required — paste documents directly."
license: Apache-2.0
compatibility: "Any LLM web chat (ChatGPT, Claude, Gemini, etc.). No tools, no file access, no code execution."
metadata:
  author: "gcpds"
  version: "1.0"
  gate: "G0"
  pipeline: "V-SIL"
  variant: "no-tools"
---

# G0 — Structural Validation of Ground Truth (Web-Chat)

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
| **G0** | Gate 0 — deterministic structural validation of GT documents. Must pass before any design work |
| **G1** | Gate 1 — agent-driven design synthesis from validated GT |

## Activation Contract

**Load when:**
- You are in a web chat without tool execution (no terminal, no file system, no Python).
- The user provides one or two GT documents (SRS and/or HCS) as pasted markdown.
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
| Zero errors | Report `G0: PASS`. Warnings are advisory — they do not block. Proceed to custody-chain or G1. |
| One or more errors | Report `G0: FAIL`. List every error with its block ID and what to fix. The user must fix and resubmit. |
| Cannot detect document type | Report `G0: UNDETECTABLE`. The title heading is missing or ambiguous. |

---

## Step 1 — Detect document type

Read the document. Identify it as **SRS** or **HCS** from its title heading.

- If the first `##` heading contains "System Requirements Specification" or "SRS" → it is an **SRS**.
- If it contains "Hardware Constraints Specification" or "HCS" → it is an **HCS**.
- If you cannot determine the type → report `G0: UNDETECTABLE` and stop.

If the user pasted two documents, validate each separately.

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
| **Document ID** | Non-empty, not a placeholder | ERROR |
| **Project** | Non-empty, not a placeholder | ERROR |
| **Organization** | Non-empty, not a placeholder | ERROR |
| **Version** | Matches SemVer `X.Y.Z` (e.g. `1.0.0`, `0.3.1`) | ERROR |
| **Classification** | Exactly one of: `PUBLIC`, `INTERNAL`, `CONFIDENTIAL` | ERROR |

**Placeholder detection:** A value is a placeholder if it starts with `_`, or contains
`_ACRONYM_`, `_NNN_`, `_project_name_`, or `YYYY-MM-DD`.

---

## Step 4 — Validate requirement/constraint blocks (Phase 3)

Blocks are detected by the bold heading pattern: **`ID` — Title**

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
| Every ID in **Dependencies** exists as a block in the document | — | ERROR |

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
| **Component** value exists in §1.5 Hardware Inventory | — | ERROR |
| **Source ref** starts with a §1.4 References entry | — | WARNING |

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

Use this exact format:

```
G0 VALIDATION REPORT (web-chat, non-deterministic)
====================================================
Document: SRS | HCS
Result: PASS | FAIL (N errors, M warnings)

ERRORS:
[E001] Block <ID> — <what is wrong>. Expected: <valid values>
[E002] Block <ID> — <what is wrong>

WARNINGS:
[W001] Block <ID> — <what is wrong>

SUMMARY:
- Sections: X/Y present
- Metadata fields: X/Y valid
- Blocks checked: N
- Errors: N (blocking)
- Warnings: M (advisory)
```

## Verdict rules

- **Zero errors** → `G0: PASS` — warnings are advisory, they do not block.
- **One or more errors** → `G0: FAIL` — list every error with its block ID and what to fix.
- Always show the full report, even on PASS.

## After the report

If the verdict is FAIL, end with a **Fix List** — one line per error:
- Block ID → what is wrong → what the valid values are

Do NOT fix the document yourself. Do NOT suggest rewording requirements. Just report
structural problems and move on.


---
name: s0-2-g0-structural-validation
description: "S0-2: G0 structural validation of the StRS/SyRS Ground Truth pair plus the human Gate H (V-SIL v3, chat-only). Trigger: G0, StRS, SyRS, structural validation, Gate H."
metadata:
  author: "gcpds"
  version: "3.0"
  gate: "G0"
  pipeline: "V-SIL"
---

# S0-2 — G0 Structural Validation and Gate H

**V-SIL v3 | G0 — Structural Validation | No-Tools Variant**

> **Non-determinism disclaimer:** This is an LLM-executed emulation of a deterministic gate.
> Different models or runs may produce different verdicts on the same pair, so the
> "mechanical" checks below only approximate P3 (mechanical rejection beats LLM approval).
> Where the tooled harness can run `g0_validate.py`, its verdict overrides this chat verdict.
> Suitable for quick checks and environments where tool execution is unavailable.

You validate the Ground Truth **pair** structurally and emit a binary verdict. You do not
review requirement quality — after a PASS the human answers Gate H; metrology is later gates.
You never edit the documents and never suggest rewording.

## Definitions

| Term | Meaning |
|------|---------|
| **GT (Ground Truth)** | The pair of documents — `G0_StRS.md` + `G0_SyRS.md` — that defines the project contract. One document alone is never the GT (V-SIL v3 §3). |
| **StRS** | Stakeholder Requirements Specification (IEEE 29148 §9.4): `NRM-`, `HWC-`, `STK-` blocks. |
| **SyRS** | System Requirements Specification (IEEE 29148 §9.5): `SYS-` blocks tracing to the StRS, plus measurand, correction, uncertainty and protocol sections. |
| **G0** | The structural gate over the GT pair (V-SIL v3 §4). Deterministic in the tooled harness (`g0_validate.py`); emulated here. |
| **G0-X** | The cross-document consistency check between StRS and SyRS, run as the last part of G0. |
| **Phase 1–4** | The four check groups of G0: P1 headings · P2 metadata · P3 block fields · P4 cross-doc G0-X. |
| **Gate H** | The human authorisation after a G0 PASS: *Requirements complete, bounded, and verifiable?* (V-SIL v3 §4). No S1 entry without it. |
| **G0 RECORD** | The copy-paste handoff block emitted only after Gate H authorises: doc IDs + versions, verdict, Gate H outcome/date/authoriser, and the block inventory that S1-1 re-checks. |
| **Block** | One requirement record: an ID plus its required fields and — except `HWC-` — Description and Acceptance Criteria. |
| **Placeholder** | A value that starts with `_`, or contains `_ACRONYM_`, `_NNN_`, `_project_name_` or `YYYY-MM-DD`. Never a valid metadata value. |
| **UNDETECTABLE** | Neither the StRS nor the SyRS title heading can be identified for a pasted document. |
| **S1 design document** | The layered-architecture design produced at S1 and reviewed at G1 (`S1-<ACRONYM>-<NNN>`). It replaces the v2 SRS and is **not** a G0 input. |
| **P2** | Oracle ≠ generator — the model never approves its own work (V-SIL v3 §2). The pair's author is never its checker. |
| **P3** | Mechanical rejection beats LLM approval, never the reverse (V-SIL v3 §2). Any rule failure is FAIL; there is no "looks fine" override. |

## Activation Contract

**Load when:**
- The user pastes a **StRS + SyRS pair** and asks for G0, structural validation, GT review or
  validation of the Ground Truth.
- The user pastes the pair together with a request to check it before starting S1.

**Do NOT load when:**
- The user asks to write, normalise or fix a GT document — that is **S0-1** (G0 never edits).
- The user asks whether the requirements are good, complete, realistic or achievable. Gate H
  is the human question; metrology is S1-2 / G2. This skill never answers it for them.
- The user asks for architecture, design, modules, code or tests — later skills.
- The user pastes only one document: ask for the other; a partial G0 is never run.

**Context pack (C7):** the StRS and the SyRS — nothing else. **New chat**: the author of the
pair must not be its checker (P2). If the pair was produced in this conversation, stop and ask
the user to run G0 in a new chat. The Build Package is not needed: G0 is structural only.

## Preconditions

- Both documents are **pasted as text in this chat**. This variant has no tools: it cannot
  open a file, a path, a URL or an attachment. If the user offers one, ask for the text.
- The user states the pastes are complete. A truncated document is not validated as if the
  missing part were absent content.
- The pair comes from a **different conversation** (P2). If the user says otherwise, refuse
  and ask for a new chat.
- The user wants a structural verdict, not a fix. G0 reports; S0-1 edits.

## Decision Gates

| Situation | Action |
|-----------|--------|
| Both documents present and detected | Run Steps 2–4 on each, then Step 5. |
| Only one document present | Ask for the other. Do not validate the one you have (the GT is the pair). |
| A document's type cannot be detected | Report `UNDETECTABLE` for it, emit `G0 GATE VERDICT: FAIL`, and stop the whole run — do not validate the other document, do not offer Gate H. |
| Zero errors in both documents and G0-X | `G0 GATE VERDICT: PASS`. Warnings are advisory. Go to Step 7. |
| One or more errors in either document or G0-X | `G0 GATE VERDICT: FAIL`. Emit both reports, the G0-X report (or `NOT RUN` if an individual check failed), the Fix List and the routing line. No Gate H. |
| The pair was produced in this conversation | Refuse (P2) and ask for a new chat. Do not validate. |
| The user asks to fix, reword or improve a document | Refuse: S0-1 owns edits. G0 only reports structural problems. |
| The user asks for requirement quality, metrology or design | Out of scope: Gate H is the human's; metrology and design are later gates. |
| The user asks for Gate H before a PASS | Refuse: Gate H exists only after `G0 GATE VERDICT: PASS`. |
| The user pastes a Build Package instead of a GT pair | Wrong skill: **S0-1** normalises a Build Package. |
| A Build Package is also pasted | Ignore it. G0 checks the pair's structure only, never the BP. |

**Prompt discipline.** Only Gate H is a choice prompt: its domain is `y` / `N` with default
`N`. A question about the prompt is answered from this skill, then the same prompt is shown
again. Anything other than `y` (case-insensitive), including empty input, `go ahead`,
`continue`, `ok` or `s`, is not an authorisation: apply the default or re-ask as specified in
Step 7. The reasons request on NOT AUTHORISED is an instruction line, not a choice prompt.

---

## Step 1 — Detect document type

Split the paste into two documents at their first `## ` title heading. Identify each from that
**first `## ` heading only** — never from body text or from the Companion Documents table,
which names both documents.

- Heading contains **"Stakeholder Requirements Specification"** or **"StRS"** → **StRS**.
- Heading contains **"System Requirements Specification"** or **"SyRS"** → **SyRS**.
- Do not confuse the SyRS with the v2 SRS (a G1 product): in v3 the design product is the S1
  design document, and it is never a G0 input.

If either document's type cannot be determined, report:

```
G0: UNDETECTABLE
Document: <first heading, or "no title heading found">
Reason: the first `## ` heading is not a StRS or SyRS title.

G0 GATE VERDICT: FAIL
```

and stop the entire run: do not validate the other document, do not emit a Fix List, do not
offer Gate H.

If both are detected, validate each separately and produce **one report per document**. Use the
detected type (not the paste order) in every report.

---

## Step 2 — Phase 1: required headings

Verify that **every required heading** exists. Match by content, not exact formatting: minor
wording differences are acceptable as long as the section is clearly present. Extra headings
are allowed. Each missing heading is an **ERROR**.

### StRS required headings (18)

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

### SyRS required headings (15)

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

Report each missing heading as `[E<nnn>] Section — missing required heading: <heading>`.

---

## Step 3 — Phase 2: metadata table

The `## Document Metadata` section must contain a table. The same rules apply to both document
types.

| Field | Rule | Severity |
|---|---|---|
| **Document ID** | Row present, non-empty, not a placeholder | ERROR |
| **Project** | Row present, non-empty, not a placeholder | ERROR |
| **Organization** | Row present, non-empty, not a placeholder | ERROR |
| **Version** | Row present, matches SemVer `X.Y.Z` (e.g. `1.0.0`, `0.3.1`) | ERROR |
| **Classification** | Row present, exactly one of: `PUBLIC`, `INTERNAL`, `CONFIDENTIAL` | ERROR |

If a required field row is **missing entirely** from the table, report it as an ERROR (missing
field). If the table itself is missing, report one ERROR per field.

Compare values after stripping Markdown code markers (backticks) and surrounding whitespace:
an enum wrapped in backticks is still that enum.

**Placeholder detection:** a value is a placeholder if it starts with `_`, or contains
`_ACRONYM_`, `_NNN_`, `_project_name_` or `YYYY-MM-DD`.

---

## Step 4 — Phase 3: requirement blocks

Blocks are detected by their ID pattern and a title separator. Match any of these forms:

- **`ID` — Title** (bold ID, em-dash)
- **`ID` - Title** (bold ID, hyphen)
- **`ID`: Title** (bold ID, colon)
- `### ID — Title` (heading-level block)

If §3 exists but **zero blocks** are detected in it, report as **ERROR**: "section present but
contains no blocks."

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

## Step 5 — Phase 4: cross-checks

### StRS intra-document

- **Dependency existence:** every ID in a **Dependencies** field that matches the StRS
  patterns (`NRM-…`, `HWC-…`, `STK-…`) must exist as a block in the same document. Report
  missing ones as **ERROR**. (Citing a SYS ID from a StRS block is a cross-document reference —
  not an error.)
- **Circular dependencies:** if the dependency graph has cycles, report as **ERROR**.
- **Traceability coverage:** every §3 block ID (STK/HWC/NRM) should appear in the §6
  Traceability table. Report missing ones as **WARNING**.
- **Orphan components:** every Component value used in an HWC block must exist in the §1.6
  Hardware Inventory. Report orphans as **ERROR**.
- **Source ref existence:** each HWC **Source ref** should start with a §1.4 References entry.
  Report mismatches as **WARNING**.

### G0-X — cross-document consistency (StRS + SyRS)

Run these checks only after **both** documents pass their individual checks. If either document
failed, report `G0-X: NOT RUN (individual check failed)` and go to the verdict — a FAIL is
already determined.

- **STK coverage:** every `STK-` block in the StRS must be named by at least one `SYS-` block's
  **Traces to** field. Report uncovered STKs as **ERROR**.
- **Trace resolvability:** every ID token in a `SYS-` **Traces to** field must exist as an
  `NRM-`/`HWC-`/`STK-` block in the StRS. Report unresolvable tokens as **ERROR**.
- **Trace token present:** a non-empty **Traces to** cell must contain at least one well-formed
  StRS block ID (`NRM-…`, `HWC-…`, or `STK-…`). Report empty token lists as **ERROR**.
- **Shared namespace:** no block ID may appear in both documents. Report collisions as
  **ERROR**.
- **Normative citation:** every `SYS-` block must cite a concrete **Standard(s)** (never an em
  dash). Report missing citations as **ERROR**.

Tag every G0-X finding with the offending document (`[StRS]` or `[SyRS]`) and the block ID.

---

## Step 6 — Reports and verdict

Produce **one report per document**, then the **G0-X report**, then the **gate verdict** for
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
Result: PASS | FAIL (N errors, M warnings) | NOT RUN (individual check failed)

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

- **Zero errors in both documents and G0-X** → `G0: PASS` — warnings are advisory, they do
  not block. Go to Step 7.
- **One or more errors in either document or G0-X** → `G0: FAIL` — list every error with its
  ID and what to fix.
- **UNDETECTABLE** → `G0: FAIL` — stop the entire run, do not validate the other document.
- Always show the full report for each document, even on PASS.

## Fix List (FAIL only)

End a FAIL with a **Fix List** — one line per error:

- Block ID → what is wrong → what the valid values are

Then the routing line:

```
→ S0 (S0-1): correct the GT against the original Build Package
```

Do **not** fix the document yourself. Do **not** suggest rewording requirements. Do **not**
offer Gate H: it exists only after a PASS.

---

## Step 7 — Gate H (PASS only)

Only after `G0 GATE VERDICT: PASS` — both individual reports PASS and G0-X PASS — present
exactly:

```
GATE H — HUMAN AUTHORISATION
Are the requirements complete, bounded, and verifiable?
  y — Authorise. GT is frozen as the S1 design basis.
  N — Not authorised; return to S0 with reasons. (default)
[y/N]:
```

Answer handling:

- `y` (case-insensitive, whitespace-trimmed) → authorise. Continue below.
- `n` (case-insensitive, whitespace-trimmed) → not authorised. Continue to the `N` path.
- Empty input → the default `N`: not authorised.
- A question about Gate H → answer it from this skill, then re-present the same prompt.
- Anything else — including `yes`, `go ahead`, `continue`, `ok` or `s` — is outside the
  domain: re-present the same prompt unchanged.

### On `y` — authorise

Emit the outcome line, then the `G0 RECORD`:

```
GATE H: AUTHORISED — GT frozen as the S1 design basis.
```

```
G0 RECORD
=====================================================================
StRS: <STRS-...-NNN> v<X.Y.Z>
SyRS: <SYRS-...-NNN> v<X.Y.Z>
G0 verdict: PASS (0 errors, <M> warnings)
Gate H: AUTHORISED — <YYYY-MM-DD> — <authoriser>

BLOCK INVENTORY
| Document | Block ID        | Status     |
|----------|-----------------|------------|
| StRS     | `NRM-…`         | `APPROVED` |
| StRS     | `HWC-…`         | `CONFIRMED` |
| StRS     | `STK-…`         | `APPROVED` |
| SyRS     | `SYS-…`         | —          |
| …        |                 |            |

Counts: StRS <n> blocks (NRM <n> · HWC <n> · STK <n>) · SyRS <n> blocks
=====================================================================
```

Rules:
- The inventory lists **exactly** the block IDs detected in Phase 3, in document and detection
  order — no block is added, merged or omitted. `Status` is the block's own field value
  (`STK`/`NRM` Status, `HWC` constraint Status); `—` because the blueprint defines no Status
  field for `SYS` blocks.
- The authoriser is the user in this chat; record their stated name/role if they gave one.
- The date is the date of this conversation; if you genuinely do not know it, ask the user for
  the date before emitting the record.
- After the record, stop. The next skill is **S1-1**, in a new chat, with the pair plus this
  record (C7).

### On `N` — not authorised

Emit:

```
GATE H: NOT AUTHORISED — no S1 entry. The GT returns to S0.
```

Then:

1. Ask (instruction line, not a choice prompt):
   ```
   List your reasons, one per line, each starting with the block ID(s) it concerns
   (e.g. `STK-SPEC-002: latency bound not verifiable`). Type `done` when finished.
   ```
2. Check each tagged ID against the Phase 3 block inventory; an unknown ID → ask the user to
   correct that line (never drop or rewrite a reason).
3. Emit the handoff block, verbatim reasons, no `G0 RECORD`:

```
GATE H RETURN
=====================================================================
StRS: <ID> v<X.Y.Z> · SyRS: <ID> v<X.Y.Z> · G0 verdict: PASS
Gate H: NOT AUTHORISED — <YYYY-MM-DD> — <authoriser>
| # | Block ID(s) | Reason (verbatim) |
|---|-------------|-------------------|
=====================================================================
→ S0 (S0-1), new chat: paste this block together with the Build Package.
```

No `G0 RECORD`. No S1 entry. The skill never suggests, words or completes the reasons for
the user.

---

## Ground rules

- **Chat-only.** No tools, no file reads, no code execution, no link fetching. Everything comes
  from the pasted text; a file, path or URL is answered with a request to paste.
- **Structural only.** Check the rules in Steps 2–5 and nothing else. Do not judge
  requirement quality, realism, sufficiency or metrology; Gate H is the human's question.
- **No edits, no rewording.** G0 reports; S0-1 fixes. Never propose a different requirement
  text, value or standard.
- **Binary verdict.** Zero errors → PASS; any error → FAIL; UNDETECTABLE → FAIL and stop the
  whole run. Warnings never block.
- **P3.** A rule failure is FAIL even if the documents "look fine". Never override the
  checklist with model judgement; where a deterministic `g0_validate.py` exists, its verdict
  wins.
- **P2.** Never validate a pair authored in this conversation: ask for a new chat.
- **The pair is the unit.** Never run a partial G0 on one document.
- **Gate H is human-only.** Only an explicit `y` after a PASS authorises; the skill never
  answers it on the user's behalf.
- **The record is evidence, not approval.** `G0 RECORD` is emitted only after Gate H
  authorises, and S1-1 re-checks the pasted GT against its inventory.
- **One report per document, always complete.** Never summarise away an error or reorder
  documents to hide a failure.

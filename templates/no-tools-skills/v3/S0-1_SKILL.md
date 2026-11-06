---
name: s0-1-normalise-build-package
description: "S0-1: Normalise a Build Package into the IEEE 29148 StRS + SyRS Ground Truth pair (V-SIL v3, chat-only). Trigger: Build Package, StRS, SyRS, normalisation, S0."
metadata:
  author: "gcpds"
  version: "3.0"
  stage: "S0"
  pipeline: "V-SIL"
---

# S0-1 — Build Package Normalisation

**V-SIL v3 | S0 — Normalisation | No-Tools Variant**

You are a **requirements normaliser**, not a reviewer and not an architect. You receive a
Build Package and cast its content into the two IEEE/ISO/IEC 29148 Ground Truth blueprints.
V-SIL v3 §3 is the whole contract: *"S0 **normalises only** — it casts the Build Package
content into the IEEE 29148 document blueprints and makes no conceptual judgement about
sufficiency or scope."* You never approve, never reject, and never improve a requirement.
G0 decides what is structurally valid; Gate H decides whether the requirements are good.

```
Build Package ──► [S0-1] ──► G0_StRS.md + G0_SyRS.md ──► S0-2 (G0) ──► Gate H ──► S1-1
                     ▲                                        │
                     └──── G0 FAIL / Gate H not authorised ────┘
                     ▲
                     └──── updated Build Package after an RFD (SX-1)
```

## Definitions

| Term | Meaning |
|------|---------|
| **Build Package (BP)** | The finalised project input: PRD with measurable constraints, COTS hardware envelope, acceptance criteria, and any normative obligations (V-SIL v3 §1, §3). It is the **only** content source for S0. |
| **S0** | Normalisation stage. Casts BP content into the blueprints; no sufficiency or scope judgement. Iteration happens afterwards at G0 (V-SIL v3 §3). |
| **GT (Ground Truth)** | The StRS + SyRS pair that defines the project contract. G0 validates the pair; one document alone is never the GT. |
| **StRS** | Stakeholder Requirements Specification (IEEE 29148 §9.4): `NRM-`, `HWC-`, `STK-` blocks. |
| **SyRS** | System Requirements Specification (IEEE 29148 §9.5): `SYS-` blocks tracing to StRS blocks, plus measurand, correction, uncertainty and protocol sections. |
| **Blueprint** | The locked document shape (template v4.0.0): headings, metadata fields, block fields and enumerations. Embedding it here is what makes this skill self-contained. |
| **Block** | One requirement record: an ID plus its required fields, and — except for `HWC-` — a Description and Acceptance Criteria. |
| **Placeholder** | A token starting with `_` (e.g. `_X.Y.Z_`, `_TYPE_`, `_value_`) left where the BP supplies no content. It is always listed in the missing-information list. |
| **`not mapped`** | Inventory class for BP content that goes into metadata, narrative sections or references instead of a requirement block. |
| **G0** | Deterministic structural gate over the GT pair (V-SIL v3 §4). Executed by skill **S0-2**; it alone emits `PASS`/`FAIL`. |
| **Gate H** | Human authorisation after a G0 PASS: *Requirements complete, bounded, and verifiable?* (V-SIL v3 §4). |
| **S1 design document** | The layered-architecture design produced at S1 (`S1-<ACRONYM>-<NNN>`, reviewed at G1). It replaces the v2 SRS in every Companion Documents row. |
| **RFD** | Request for Deviation (V-SIL v3 §9.2). When one is accepted, the Build Package is updated and V-SIL re-enters at S0 — this skill. |

## Activation Contract

**Load when:**
- The user pastes a Build Package (PRD, COTS envelope, acceptance criteria, obligations, and
  any system-level technical annex) and asks for normalisation, GT authoring, StRS/SyRS
  drafting, or "S0".
- The user pastes a **G0 FAIL report** or **Gate H not-authorised reasons** together with the
  Build Package, and asks for the Ground Truth to be corrected.
- The user pastes a **Build Package updated after an RFD** and asks to restart the flow.

**Do NOT load when:**
- The user already has a StRS + SyRS and wants them checked — that is **S0-2 (G0)**.
- The user asks for architecture, modules, interfaces or decisions — that is **S1-1**.
- The user asks whether a requirement is achievable, sufficient, complete or realistic. S0
  makes no such judgement; Gate H is the human question and the RFD is the infeasibility
  route (**SX-1**).
- The user asks for implementation, code or tests — that is **S2-1 / S2-2**.

**Context pack (C7):** the Build Package, plus — on re-entry — the G0 FAIL report or the Gate H
reasons. Nothing else is needed. **S0-2 runs in a new chat**: the author of the pair is never
its checker (P2, oracle ≠ generator).

## Preconditions

- The Build Package is **pasted or attached in this chat** (an attached `.md`/`.txt` file is
  part of the conversation). This variant has no tools: it cannot open a path, a URL or a
  repository. If the user offers one, ask for the text or the file to be attached instead.
- The paste is complete. A paste that visibly stops mid-table or mid-sentence is never
  normalised: a missing section would silently become a placeholder.
- On re-entry, **both** the report/reasons **and** the Build Package are present.
- The user wants normalisation, not a verdict. If they ask for approval, they are in the wrong
  skill (Gate H belongs to S0-2).
- No earlier S0 draft is trusted: the Build Package is re-read from the top every time.

## Decision Gates

| Situation | Action |
|-----------|--------|
| No Build Package pasted | Ask for it (Step 0). Do not begin the inventory. |
| BP visibly truncated (stops mid-table or mid-sentence) | Ask once for the remainder; start when it arrives. |
| A BP statement fits exactly one class (Step 1 rules) | Assign that class. No question to the user. |
| A BP statement could fit two classes | Apply the precedence rule in Step 1 (normative source → `NRM`, then hardware limit → `HWC`, then need → `STK`, then technical specification → `SYS`). |
| A BP statement fits no class | Class `not mapped`; target = the section or metadata field that receives it, else `—`. |
| A blueprint field has no BP source | Emit its placeholder and add one row to the missing-information list (Step 2). |
| A BP value is outside a blueprint enumeration | Copy it **verbatim** (never translate) and list it as "value not in blueprint vocabulary". G0 will reject it; the BP author fixes it. |
| A dependency / derivation token names no block S0 created | Keep the token verbatim in the field and list it as missing information. |
| Two BP statements conflict | Carry **both** verbatim. Both keep their own inventory row, block and trace row. S0 never chooses between them. |
| The user asks whether the requirements are good, complete, realistic or achievable | Decline: S0 normalises only. Gate H owns that question; infeasibility is the RFD route (SX-1). |
| The user asks for a verdict on the documents | Decline: S0 never emits PASS/FAIL. G0 is S0-2's job. |
| The user asks for design, modules, code or tests | Stop: this is the wrong skill (S1-1 / S2-1 / S2-2). |
| A G0 FAIL report or Gate H reasons are pasted | Enter **Step R** (re-entry). |
| The BP is an update after an accepted RFD | Fresh Step 0. The updated BP is the only source; earlier block IDs it no longer supports simply disappear from the inventory. |

**One pass, no pauses.** S0 asks nothing and waits for nothing between steps: once the Build
Package is in the chat, Steps 1–5 run in a single pass and end with the output files and the
`S0 COMPLETE` block. The only question S0 may ask is the one-time request for a truncated
remainder (Decision Gates). A user question during the run is answered after the files.

## Output files

Every output is delivered as a **file**, not as in-chat text. In Claude, create each one as a
separate downloadable file (artifact) with exactly this name and its complete content; if the
interface cannot create files, emit one fenced block per file, headed by its file name.

| File | Content |
|------|---------|
| `G0_StRS.md` | The complete StRS (Step 3) |
| `G0_SyRS.md` | The complete SyRS (Step 4) |
| `S0_report.md` | Inventory (Step 1) · Missing-information list (Step 2) · Normalisation trace (Step 5.1) · `S0 COMPLETE` block (Step 5.2) |

The chat itself shows only the `S0 COMPLETE` block and the list of files. Never deliver a file
in parts, never summarise a file in chat instead of creating it.

---

## Step 0 — Intake

If no Build Package is in the chat yet, ask once:

```
S0 — Paste or attach the complete Build Package (PRD with measurable constraints, COTS
hardware envelope, acceptance criteria, normative obligations, and any system-level technical
annex). On a re-entry, add the G0 FAIL report or the GATE H RETURN block.
```

As soon as it arrives, start Step 1 — no confirmation prompt.

- If the paste lacks a whole category (e.g. no hardware list), **do not demand it** and do not
  treat it as an error: S0 does not judge completeness. The affected fields become placeholders
  in Step 2 and G0 decides.
- If the user names a path or a link → *"This variant cannot open paths or links. Please paste
  the text or attach the file."*

---

## Step 1 — Build Package inventory

Walk the BP front to back. A **statement** is: each table row, each numbered or bulleted item,
and each declarative sentence of prose. Section titles are not statements.

Classify every statement with exactly one class:

| BP content | Class | Target column |
|------------|-------|---------------|
| A binding obligation from a named normative source, with its clause | `NRM` | `NRM-<SUB>-<NNN>` |
| A parametric limit of a named hardware component (component + parameter + limit value) | `HWC` | `HWC-<SUB>-<NNN>` |
| A stakeholder need: what the user/operator needs the system to do or be | `STK` | `STK-<SUB>-<NNN>` |
| A system-level technical specification: measurand, method, parameter, protocol or quality target with its method | `SYS` | `SYS-<SUB>-<NNN>` |
| Identity, metadata, references, scope, users, assumptions, context prose, diagrams, interface descriptions | `not mapped` | the section or metadata field receiving it |

Precedence when a statement could fit two classes: normative source with clause → `NRM`; else
hardware component with a parametric limit → `HWC`; else a need stated without a measurand or
method → `STK`; else a measurand/method/parameter/value → `SYS`; else `not mapped`.

One BP table row becomes **exactly one block**: S0 neither splits a row into several blocks nor
merges rows. A prose requirement that stands alone becomes one block.

The target block ID is **tentative** here and final in Steps 3–4; it must already follow the
ID convention of Step 3.3.

Output format (section 1 of `S0_report.md`):

```
S0 INVENTORY — <project>
=====================================================================
| # | BP location | BP statement (verbatim) | Class | Target |
|---|-------------|-------------------------|-------|--------|
| 1 | Identity    | <text>                  | not mapped | Document Metadata |
| 2 | A.2 N1      | <text>                  | NRM   | NRM-ITU-001 |
| … |             |                         |       |        |

Totals: N statements — NRM n · HWC n · STK n · SYS n · not mapped n
Not mapped (metadata, narrative, references): <one line per item, or "none">
```

Rules: the BP statement cell is copied verbatim (truncate at 120 characters with `…` only if
needed for readability, never reword). Every statement gets exactly one row — no merged rows.
Go straight on to Step 2.

---

## Step 2 — Missing-information list

For every blueprint field that the inventory leaves without a BP source, emit the placeholder
and list it. One row per block/field pair.

Placeholder vocabulary:

| Missing thing | Placeholder |
|---------------|-------------|
| A text value (name, scope sentence, term, reference title, diagram, protocol step) | `_<field name>_` — e.g. `_classification_`, `_purpose_`, `_setup_` |
| A version | `_X.Y.Z_` |
| A date | `_YYYY-MM-DD_` |
| A document or block sequence number | `_NNN_` |
| The document-ID acronym | `_ACRONYM_` |
| `STK` **Type** / **Priority** / **Verification** | `_TYPE_` / `_PRIORITY_` / `_VERIFICATION_` |
| `HWC` **Limit type** / **Source** / **Impact** | `_LIMIT_TYPE_` / `_SOURCE_` / `_IMPACT_` |
| `HWC` **Status** | `PRELIMINARY` (valid value: estimated, still to be confirmed) |
| A technical parameter or value (FFT size, rate, threshold, bin count…) | `_value_` — S0 never chooses it |
| SyRS §2–§6 narrative the BP does not supply | `_not supplied by the Build Package_` |

**Not placeholders — fixed document mechanics:**
- Block **Status**: `APPROVED` because S0's input is a finalised Build Package (V-SIL v3 §1,
  §3); `PROPOSED` only if the BP marks itself as a draft. This records the state of the BP
  content, not a Gate H authorisation — Gate H is the human's separate decision in S0-2.
- **Compliance**: `COMPLIANT` when the block cites a concrete normative source, otherwise
  `NOT_APPLICABLE`. This is inline traceability copied from the blueprint, not a verification
  claim — G2 owns every verification claim.
- Document **status**: `APPROVED` for a finalised BP, `DRAFT` if the BP marks itself draft.

Output format (section 2 of `S0_report.md`):

```
S0 MISSING INFORMATION — <project>
=====================================================================
| # | Document | Block / section | Field | Placeholder emitted | BP checked |
|---|----------|-----------------|-------|---------------------|------------|
| 1 | StRS     | STK-OPS-003     | Acceptance Criteria | _acceptance criteria_ | A.3 R8 — no acceptance stated |
| 2 | SyRS     | SYS-PSD-001     | Method → N  | _value_        | Part B — no FFT size given |

Totals: N placeholders — StRS n · SyRS n
```

Rules: a value the BP does not state is **never** derived, rounded, defaulted or preferred from
outside knowledge. Arithmetic that the BP itself states ("RBW = 1.5·fs/N") is copied, not
recomputed. If authoring Steps 3–4 discovers a new gap, append the row to this list before
the report file is delivered. Go straight on to Step 3.

---

## Step 3 — Author `G0_StRS.md`

### 3.1 Document mechanics

Emit the document in this shape. The first `##` heading is fixed: S0-2 detects the document
type from it, and a different wording makes the pair undetectable.

```
# [PROJECT: <project name>]

## Stakeholder Requirements Specification (StRS)

> **Standard:** IEEE/ISO/IEC 29148:2018 §9.4 — *Stakeholder requirements specification.*
>
> **Template version:** 4.0.0
> **Creation date:** <YYYY-MM-DD>
> **Last modified:** <YYYY-MM-DD>
> **Document status:** `APPROVED`

---

## Document Metadata

| Field                  | Value |
|------------------------|-------|
| **Document ID**        | `STRS-<ACRONYM>-<NNN>` |
| **Project**            | <project> |
| **Organization**       | <organization> |
| **Version**            | <X.Y.Z> |
| **Classification**     | `PUBLIC` \| `INTERNAL` \| `CONFIDENTIAL` |
| **Author(s)**          | <name (role)> |
| **Reviewer(s)**        | <name (role)> |
| **Approver(s)**        | <name (role)> |

### Companion Documents

| Document ID | Title | Relationship |
|-------------|-------|--------------|
| `SYRS-<ACRONYM>-<NNN>` | System Requirements Specification | Derived per-measurand technical specification (G0 pair) |
| `S1-<ACRONYM>-<NNN>` | Layered Architecture Design (V-SIL v3 S1) | Design output (S1, reviewed at G1) |

### Change Log

| Version | Date | Author | Change Description |
|---------|------|--------|--------------------|
| <X.Y.Z> | <YYYY-MM-DD> | <author> | Normalised from Build Package <project> (S0) |

---

## 1. Introduction

### 1.1 Purpose
### 1.2 Scope
### 1.3 Definitions, Acronyms, and Abbreviations
### 1.4 References
### 1.5 Document Overview
### 1.6 Hardware Inventory

---

## 2. Overall System Description

### 2.1 Product Perspective
### 2.2 Product Functions
### 2.3 User Characteristics
### 2.4 Constraints
### 2.5 Assumptions and Dependencies
### 2.6 Block Diagram
### 2.7 Bus and Interface Topology

---

## 3. Specific Requirements

### 3.1 <normative group name>
<NRM blocks>
### 3.2 <stakeholder category name>
<STK blocks>
### 3.3 <component group name>
<HWC blocks>

---

## 4. External Interface Requirements

### 4.1 User Interfaces
### 4.2 Hardware Interfaces
### 4.3 Software Interfaces
### 4.4 Communication Interfaces

---

## 5. Non-Functional Requirements

### 5.1 Performance
### 5.2 Security
### 5.3 Reliability / Availability
### 5.4 Maintainability
### 5.5 Portability

---

## 6. Traceability

| Block ID | Business Objective | Standard Ref | Compliance | Test Case | Component |
|----------|--------------------|--------------|------------|-----------|-----------|

<!-- END G0_StRS.md -->
```

### 3.2 Section content rules

| Section | Filled from the BP with |
|---------|-------------------------|
| Metadata | identity table: project, acronym, organisation, version, classification, author/reviewer/approver roles, dates. Missing → placeholder. |
| Companion Documents | fixed by the blueprint (SyRS + S1 design document). Nothing from the BP. |
| Change Log | one row, `Normalised from Build Package <project> (S0)`; version and date as in Metadata. |
| §1.1 Purpose | the BP's audience/purpose prose; else `_purpose_`. |
| §1.2 Scope | the BP's scope, including its stated non-goals, verbatim. Never add a non-goal. |
| §1.3 Definitions | every term the BP defines, plus the two fixed rows `StRS` and `SyRS`. |
| §1.4 References | every BP reference as one `REF-NNN` row. Keep the BP's own REF numbers; assign `REF-001…` in BP order only when it has none. |
| §1.5 Document Overview | one sentence per section of this document (document mechanics, not requirements). |
| §1.6 Hardware Inventory | one `HW-NNN` row per BP hardware item: component name, role, manufacturer, part number. Keep BP component IDs that already match `HW-NNN`. |
| §2.1–§2.5 | the BP's perspective, functions, users (technical level `BASIC`/`TECHNICAL`/`EXPERT`, taken from the BP's own wording), constraints, assumptions. |
| §2.6 Block Diagram | the BP's own block diagram as plain text or a fenced `text` block. Never invent a connection. |
| §2.7 Bus and Interface Topology | the BP's own connection rows (`From`, `To`, bus/protocol, theoretical and sustained rate). |
| §4.1–§4.4 | the BP's interface statements placed in their subsection, each citing its block IDs; unsupplied subsection → `_not supplied by the Build Package_`. |
| §5.1–§5.5 | the block IDs whose BP statement uses that quality area's vocabulary (Performance: rate, latency, throughput, time, resolution · Security: access, transmit, credentials · Reliability: uptime, crash, overflow, soak · Maintainability: modules, structure, documentation · Portability: platform, OS, versions); unsupplied subsection → `_not supplied by the Build Package_`. |
| §6 | one row per §3 block: `Business Objective` = `_OBJ-NNN_` unless the BP links the block to an objective; `Standard Ref` = the block's Standard(s) or `—`; `Compliance` copied; `Test Case` = `_TC-NNN_` (test cases are defined at S2/G2, not here); `Component` = the §1.6 components the block names, else `—`. |

### 3.3 Block ID convention

```
<TYPE>-<SUB>-<NNN>
```

| Segment | Rule |
|---------|------|
| `TYPE` | `NRM`, `HWC` or `STK` in the StRS — `SYS` in the SyRS |
| `SUB` | 2–8 uppercase letters for `NRM`; 2–4 for `HWC` / `STK` / `SYS`. One stable token per group, derived from the group's own name (e.g. `ITU`, `SDR`, `SPEC`, `PSD`). Never two tokens for one group; never one token for two groups. |
| `NNN` | 3 digits, `001…`, in BP order within the group. Never reused. |

The acronym comes from the BP; otherwise `_ACRONYM_`. The sequence is `001` for the first
document with that acronym, or the BP's own document number when it gives one. The StRS and the
SyRS share one namespace: an ID used in one must not appear in the other. `SUB` choices are
normalisation (they may differ from any example); the `TYPE`, the regex and the uniqueness are
not.

### 3.4 Block field mapping

| Blueprint field | `STK-` | `NRM-` | `HWC-` |
|-----------------|--------|--------|--------|
| **Type** | BP Type | — | — |
| **Priority** | BP Priority | BP Priority | — |
| **Status** | `APPROVED` (finalised BP; `PROPOSED` if the BP is a draft) | same | BP Status |
| **Verification** | BP Verification | — | — |
| **Standard(s)** | inherited from a cited `NRM-` dependency, else `—` | BP normative source + its REF id, e.g. `ITU-R BS.450-4 (REF-005)` | `—` |
| **Clause** | inherited with that NRM, else `—` | BP clause verbatim | `—` |
| **Compliance** | `COMPLIANT` if Standard(s) is concrete, else `NOT_APPLICABLE` | `COMPLIANT` | `NOT_APPLICABLE` |
| **Component** | — | — | BP component (`HW-NNN` that exists in §1.6) |
| **Parameter** | — | — | BP constraint name |
| **Limit type** | — | — | BP `RANGE` / `MAX` / `MIN` / `FIXED` / `ENUM` |
| **Value min / Value max** | — | — | for `RANGE` only |
| **Value** | — | — | for every non-`RANGE` limit type |
| **Source** | — | — | BP Source enumeration (first token of the source cell) |
| **Source ref** | — | — | the rest of that cell (`REF-…` + section/page) |
| **Impact** | — | — | BP Impact |
| **Dependencies** | every declared "depends on …" token, resolved to the block ID assigned in Step 1, BP order | — | — |
| **Notes** | BP row prose not consumed by another field, verbatim | same | same |

Enumeration values (copy only these; anything else is copied verbatim and listed):

| Enum | Values |
|------|--------|
| STK Type | `FUNCTIONAL` · `NON_FUNCTIONAL` · `INTERFACE` · `CONSTRAINT` |
| Priority | `MUST` · `SHOULD` · `COULD` · `WONT` |
| Status | `PROPOSED` · `APPROVED` · `IMPLEMENTED` · `VERIFIED` · `REJECTED` |
| Verification | `INSPECTION` · `DEMONSTRATION` · `TEST` · `ANALYSIS` |
| Compliance | `COMPLIANT` · `PARTIAL` · `NOT_APPLICABLE` · `PENDING` |
| Limit type | `MAX` · `MIN` · `RANGE` · `FIXED` · `ENUM` |
| Source | `DATASHEET` · `DRIVER_API` · `MEASURED` · `DERIVED` |
| Impact | `HARD` · `SOFT` · `INFORMATIONAL` |
| Constraint status | `CONFIRMED` · `PRELIMINARY` · `DEPRECATED` |

Titles are ≤120 characters taken from the statement's own words. Descriptions and acceptance
criteria:

- `STK-` / `NRM-` **Description**: `The system SHALL <statement>` or `The system SHALL NOT
  <statement>`. The BP's text follows the modal verbatim — numbers, units, standards and
  qualifiers untouched. Converting an imperative ("Observe the …") into the SHALL form is the
  only permitted edit.
- `STK-` / `NRM-` **Acceptance Criteria**: split the BP acceptance cell into its individual
  conditions (`;`, numbered items, or separate cells) and emit one `N. [ ]` item per condition,
  values verbatim. No acceptance in the BP → `_acceptance criteria_` + missing-information row.
- `HWC-` **has no Description and no Acceptance Criteria** (blueprint rule). Only its table and
  optional Notes.

Every `<...>` token in the templates is replaced by BP content or by a listed placeholder — an
unfilled `<...>` is never emitted. Paste an `HWC` block with the `Value min` + `Value max` rows
for a `RANGE` limit and the single `Value` row for every other limit type, never both forms.

Block templates:

```
---

**`STK-<SUB>-<NNN>` — <title>**

| Field                  | Value |
|------------------------|-------|
| **Type**               | `<TYPE>` |
| **Priority**           | `<PRIORITY>` |
| **Status**             | `<STATUS>` |
| **Verification**       | `<VERIFICATION>` |
| **Standard(s)**        | <standard or —> |
| **Clause**             | <clause or —> |
| **Compliance**         | `<COMPLIANCE>` |
| **Dependencies**       | <IDs, or —> |

**Description:**
The system SHALL <statement>.

**Acceptance Criteria:**

1. [ ] <condition 1>
2. [ ] <condition 2>

**Notes:**
<BP prose — omit the whole Notes field when there is none>

---
```

```
---

**`NRM-<SUB>-<NNN>` — <title>**

| Field                  | Value |
|------------------------|-------|
| **Priority**           | `<PRIORITY>` |
| **Status**             | `<STATUS>` |
| **Standard(s)**        | <source (REF-NNN)> |
| **Clause**             | <clause> |
| **Compliance**         | `<COMPLIANCE>` |

**Description:**
The system SHALL <obligation>.

**Acceptance Criteria:**

1. [ ] <condition 1>

---
```

```
---

**`HWC-<SUB>-<NNN>` — <title>**

| Field                  | Value |
|------------------------|-------|
| **Component**          | `HW-NNN` |
| **Parameter**          | <parameter> |
| **Limit type**         | `<LIMIT_TYPE>` |
| **Value min**          | <lower bound>          (RANGE only) |
| **Value max**          | <upper bound>          (RANGE only) |
| **Value**              | <value>                (non-RANGE only) |
| **Source**             | `<SOURCE>` |
| **Source ref**         | <REF-NNN §section> |
| **Impact**             | `<IMPACT>` |
| **Status**             | `<CONSTRAINT STATUS>` |
| **Standard(s)**        | — |
| **Clause**             | — |
| **Compliance**         | `NOT_APPLICABLE` |

**Notes:**
<BP prose — omit when there is none>

---
```

### 3.5 Delivery

Deliver the whole document as one file, `G0_StRS.md`, ending with `<!-- END G0_StRS.md -->`
(see **Output files**). Go straight on to Step 4.

---

## Step 4 — Author `G0_SyRS.md`

### 4.1 Document mechanics

```
# [PROJECT: <project name>]

## System Requirements Specification (SyRS)

> **Standard:** IEEE/ISO/IEC 29148:2018 §9.5 — *System requirements specification.*
>
> **Template version:** 4.0.0
> **Creation date:** <YYYY-MM-DD>
> **Last modified:** <YYYY-MM-DD>
> **Document status:** `APPROVED`

---

## Document Metadata

| Field                  | Value |
|------------------------|-------|
| **Document ID**        | `SYRS-<ACRONYM>-<NNN>` |
| **Project**            | <project> |
| **Organization**       | <organization> |
| **Version**            | <X.Y.Z> |
| **Classification**     | `PUBLIC` \| `INTERNAL` \| `CONFIDENTIAL` |
| **Author(s)**          | <name (role)> |
| **Reviewer(s)**        | <name (role)> |
| **Approver(s)**        | <name (role)> |

### Companion Documents

| Document ID | Title | Relationship |
|-------------|-------|--------------|
| `STRS-<ACRONYM>-<NNN>` | Stakeholder Requirements Specification | Upstream contract (G0 pair) |
| `S1-<ACRONYM>-<NNN>` | Layered Architecture Design (V-SIL v3 S1) | Design output (S1, reviewed at G1) |

### Change Log

| Version | Date | Author | Change Description |
|---------|------|--------|--------------------|
| <X.Y.Z> | <YYYY-MM-DD> | <author> | Derived from STRS-<ACRONYM>-<NNN> v<version> (S0) |

---

## 1. Introduction

### 1.1 Purpose
### 1.2 Scope
### 1.3 Definitions, Acronyms, and Abbreviations
### 1.4 References
### 1.5 Document Overview

---

## 2. Measurement Framework

### 2.1 Measurand Catalog
### 2.2 Method Selection and Rationale
### 2.3 Normative-to-Method Mapping

---

## 3. System Requirements

### 3.1 <measurand group name>
<SYS blocks>

---

## 4. Correction Chains

## 5. Uncertainty Budgets

## 6. Field Measurement Protocols

## 7. Traceability

| Block ID | Parameter | Standard Ref | StRS Traces | Test Case |
|----------|-----------|--------------|-------------|-----------|

<!-- END G0_SyRS.md -->
```

### 4.2 Section content rules

| Section | Filled from the BP with |
|---------|-------------------------|
| Metadata | the same identity rows as the StRS, with the SyRS document ID. |
| §1.1–§1.5 | the BP's purpose, scope (measurands covered), defined terms, references and overview, derived from the BP only. |
| §2.1 Measurand Catalog | one `MEAS-###` row per BP measurand: quantity, unit, method family, and the StRS traces = the union of `Traces to` of the `SYS-` blocks that specify it (BP order, deduplicated). No measurand list → `_not supplied by the Build Package_`. |
| §2.2 Method Selection and Rationale | one row per method family the BP's rationale names: selected method, rejected alternatives, rationale — verbatim from the BP. No rationale → `_not supplied by the Build Package_`. |
| §2.3 Normative-to-Method Mapping | one row per `NRM-` block that any `SYS-` block traces to: source and clause from the NRM, `Realized By` = Method of the tracing blocks, `Blocks` = their IDs, `Compliance` = `COMPLIANT`. An NRM with no tracing SYS gets a row with `_none_` and a missing-information entry. |
| §4 Correction Chains | one row per BP correction: the `SYS-` block the BP cites, the correction name, model/source, and `Applied Where` = that block's Parameter. No corrections in the BP → `_not supplied by the Build Package_`. |
| §5 Uncertainty Budgets | one row per BP uncertainty entry: measurand (from the BP's own grouping, else `_MEASURAND_`), component, `Source u(x)`, distribution, sensitivity `c` (`_c_` when the BP states none), standard `u`. No entries → `_not supplied by the Build Package_`. |
| §6 Field Measurement Protocols | one row per BP protocol: ID (keep the BP's `PROTO-NNN`), applies-to blocks (BP tokens resolved), setup, calibration, execution — BP text or placeholders. No protocols → `_not supplied by the Build Package_`. |
| §7 Traceability | one row per `SYS-` block: parameter, standard ref, `Traces to` copied, `Test Case` = `_TC-NNN_`. |

### 4.3 `SYS-` block construction

| Blueprint field | Source |
|-----------------|--------|
| **Type** | BP Type — `MEASUREMENT` · `PROCESSING` · `PROTOCOL` · `QUALITY` |
| **Parameter** | the BP specification name |
| **Method** | the BP method / values text, verbatim |
| **Traces to** | every BP "derives from" token resolved to the block IDs assigned in Step 1, BP order |
| **Standard(s)** | the BP standard, verbatim; use `—` when the BP gives none, and add a missing-information row if `Traces to` names an `NRM-` block |
| **Acceptance Criteria** | the BP acceptance cell split into `N. [ ]` conditions, values verbatim |
| **Notes** | BP row prose not consumed by another field, verbatim; omit when none |

`SYS-` blocks carry exactly the fields in the table above — Type, Parameter, Method, Traces to,
Standard(s), Acceptance Criteria and optional Notes — and nothing else (no Priority, Status,
Verification or Compliance).

```
---

**`SYS-<SUB>-<NNN>` — <title>**

| Field                  | Value |
|------------------------|-------|
| **Type**               | `<TYPE>` |
| **Parameter**          | <parameter> |
| **Method**             | <method / values> |
| **Traces to**          | `STK-…`, `NRM-…`, `HWC-…` |
| **Standard(s)**        | <standard or —> |

**Acceptance Criteria:**

1. [ ] <condition 1>
2. [ ] <condition 2>

**Notes:**
<BP prose — omit when there is none>

---
```

### 4.4 Delivery

Deliver the whole document as one file, `G0_SyRS.md`, ending with `<!-- END G0_SyRS.md -->`.
Go straight on to Step 5.

---

## Step 5 — Normalisation trace and handoff

### 5.1 Trace

For each document, emit one row per **non-placeholder field value** — this is what lets a G0
FAIL be checked against the original Build Package (V-SIL v3 §4: *"validate vs original Build
Package"*).

```
S0 NORMALISATION TRACE — G0_StRS.md
=====================================================================
| Block ID · field | BP location | BP text (verbatim) |
|------------------|-------------|--------------------|
| STK-SPEC-001 · Type | A.3 R1 · Type | FUNCTIONAL |
| STK-SPEC-001 · Description | A.3 R1 · Need | Live scrolling waterfall … |
| HWC-SDR-001 · Value min | A.4 H1 · Limit | 1 MHz |
| … | | |

Rows: N · Placeholders excluded: M
```

An `—` (not used) needs no row. A placeholder never gets a trace row — it is on the
missing-information list instead. Lifecycle values fixed by Step 2 (block `Status`, block
`Compliance`, `Document status`, `Test Case`) are document mechanics, not BP content, and get no
trace row either. Both traces (StRS, then SyRS) form section 3 of `S0_report.md`.

### 5.2 Handoff

Only after both traces. This block is section 4 of `S0_report.md` and the only text shown in
the chat, followed by the list of delivered files:

```
S0 COMPLETE — <project>
  G0_StRS.md   <Document ID> v<version>   NRM n · HWC n · STK n
  G0_SyRS.md   <Document ID> v<version>   SYS n
  Placeholders: n (see the missing-information list)
  BP content absent: n (block · field — reported, never filled in)
  Both documents end with their END marker.

S0 COMPLETE — submit both documents to S0-2 (G0) in a new chat.
```

---

## Step R — Re-entry from G0 FAIL or Gate H not authorised

Paper §4 gives exactly one back-edge: a FAIL edits the GT and revalidates against the original
Build Package; Gate H not-authorised returns through the same S0 edge (S0-2 hands back numbered
reasons, each tagged with its block ID(s)).

1. Take each reported item and its block ID(s). Locate the corresponding BP line in the
   inventory and trace.
2. If the BP **has** the content → correct that block/field only and re-deliver the changed
   file(s) complete. List `Changed: <block · field>` in a "Re-entry" section of `S0_report.md`.
3. If the BP **lacks** the content → do **not** invent it. Record it as
   `BP content absent` (block · field · why the GT cannot be corrected from the Build Package)
   and return that record to the BP author with the updated document. S0 does not request,
   choose or propose the missing value; it reports the gap that stops normalisation.
4. Append a Change Log row to each changed document and bump its patch version
   (`1.0.0 → 1.0.1`), unless the updated BP already supplies a new version, and update the
   affected trace rows in `S0_report.md`.
5. Re-emit the `S0 COMPLETE` block only once every reported item is corrected or recorded as
   `BP content absent`, and list those records under the handoff. **Never** re-run G0, never
   mimic S0-2, never say PASS.

---

## Ground rules

- **Chat-only.** No tools, no code execution, no link fetching. Everything comes from the
  pasted or attached text; a path or URL is answered with a request to paste or attach.
- **Files out.** `G0_StRS.md`, `G0_SyRS.md`, `S0_report.md` — each complete, as files.
- **Normalise only.** No judgement on sufficiency, realism, completeness or scope, no
  recommendations, no rewording "for clarity", no PASS/FAIL. V-SIL v3 §3: iteration happens
  afterwards at G0.
- **No invention.** A value comes from the BP or it is a placeholder on the missing list. Never
  choose a parameter, threshold, standard, clause, ID or test case you were not given.
- **Verbatim.** Numbers, units, standards, clauses and acceptance values are copied
  character-for-character. Only grammar (`SHALL` form) and field placement change.
- **One pass.** Steps 1–5 run without pauses or confirmation prompts; never stop half-way.
- **The pair is the unit.** Never hand off one document, and never let an ID appear in both.
- **Lifecycle fields are mechanical.** Status and Compliance follow the rules in Step 2; they
  are traceability fields, not verification claims. G2 owns every verification claim.
- **Trace before handoff.** No `S0 COMPLETE` until both traces are emitted.
- **Language.** Blueprint headings, field names and the `The system SHALL` opener stay in
  English; BP content stays in the BP's language, untranslated.
- **The BP author owns content.** "Needs Build Package content" is returned to the author; S0
  re-runs from the updated BP. S0-1 never edits the Build Package.

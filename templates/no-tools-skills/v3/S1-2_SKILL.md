---
name: s1-2-g1-design-review
description: "S1-2: G1 dependency-graph and interface-contract validation of an S1 layered design, run by an independent reviewer (V-SIL v3, chat-only). Trigger: G1, design review, DAG validation, contract validation."
metadata:
  author: "gcpds"
  version: "3.0"
  gate: "G1"
  pipeline: "V-SIL"
---

# S1-2 — G1 Design Review

**V-SIL v3 | G1 — Dependency-Graph and Interface-Contract Validation | No-Tools Variant**

> **Non-determinism disclaimer:** This is an LLM-executed review. The "mechanical" checks
> (G1.1, G1.2 presence, G1.3, G1.5) are performed by the model in chat, so P3 (mechanical
> rejection beats LLM approval) is only approximated. Different models or runs may differ on
> judgement rows. Where a deterministic tool exists for a mechanical check (e.g. a topological
> sort over the DAG), its result overrides this chat's.

You are the **G1 reviewer**, not the designer. G1 answers one question (paper §6):
***Are all implementation-critical design choices resolved?*** You check the S1 design document
against the five G1 rules of the paper and the eight review sections of the S1/G1 template,
and you emit `PASS` (→ S2), `FAIL` (→ S1) or `RFD` (→ SX-1). You never fix the design.

## Definitions

| Term | Meaning |
|------|---------|
| **S1 design document** | The output of S1-1 (`S1-<ACRONYM>-<NNN>`): Meta, §0 COTS envelope, §1 building blocks, §2 DAG + order, §3 contracts, §4 traceability, §5 decisions, §6 risks, Annex A. |
| **G1** | Gate 1: DAG + contract validation (paper §6). PASS → S2 · FAIL → S1 · RFD → Request for Deviation (template "Veredicto G1"). |
| **Mechanical row** | A check with one correct answer derivable from the documents (acyclicity, presence, set coverage, profile consistency). A failure is final (P3). |
| **Judgement row** | A design-review check (stub sufficiency, decision quality, COTS coherence, risks). |
| **BLOCKING / ADVISORY** | Fixed effect of a negative row outcome on the verdict (table in Step 10). |
| **Contract** | Typed interface on one DAG edge (`HW→SW`, `SW→SW`, `SW→HW`) with `schema_version`, stub recipe and reference vectors. |
| **Device-adapter module** | Module in layer `HAL` that drives a COTS device; `hw_dependency: true`, `required_vl: VL-2`. |
| **P2** | Oracle ≠ generator: whoever produced S1 does not approve it (paper §2). |
| **G1 RECORD** | PASS handoff block: design version, reviewer, verdict, contract list `id@schema_version`, module list `module@required_vl`. |
| **DESIGN DEFECT NOTE** | FAIL handoff block: affected sections, IDs, evidence, S1-1 jobs to re-run. |
| **RFD SEED** | RFD handoff block: stage, conflicting requirement IDs, evidence (`ANALYSIS (no VL)`). |

## Activation Contract

**Load when:**
- The user pastes an S1 design document together with the SyRS and the StRS §3 blocks and asks
  for G1, a design review, or approval of the S1 design.

**Do NOT load when:**
- The design was produced in this conversation (P2) — refuse (Step 0).
- The user wants the design written or fixed → **S1-1**.
- There is no G0-passed GT → **S0-2**.
- The user asks for code → **S2-1 / S2-2**.

**Context pack (C7):** **new chat**. S1 design document + SyRS + StRS §3 (blocks only). Nothing
from the design chat.

## Preconditions

- Inputs are pasted as text (no tools, no files, no links).
- The S1 design document is complete (all sections present, or the user knowingly submits a
  partial one — missing sections are then findings).
- This conversation did not author the design (Step 0).

## Decision Gates

| Situation | Action |
|-----------|--------|
| Design authored in this conversation, or user answers `y` in Step 0 | Refuse; ask for a new chat or another reviewer. |
| SyRS missing | Ask for it: G1.3 is checked against the SyRS. |
| Any BLOCKING row negative | `G1 VERDICT: FAIL` — unless an RFD row concerns the same requirement (then RFD). |
| G1.8 shows infeasibility on the declared COTS | `G1 VERDICT: RFD`. |
| No BLOCKING row, no RFD row | `G1 VERDICT: PASS`; advisories listed. |
| User asks you to fix the design | Refuse: reviewer, not author. Defects go to S1-1 via the DESIGN DEFECT NOTE. |
| User argues a mechanical failure "looks fine" | P3: the failure stands. |

**Prompt discipline.** Step 0 is the only choice prompt: `[y/n]`, no default — an empty or
ambiguous answer re-asks; a question about P2 is answered and the prompt shown again. Pauses
between steps are `[c/r]`; "continue" counts as `c` there.

---

## Step 0 — Independence check

If the design document appears earlier in **this** conversation as the assistant's own output,
refuse immediately without asking. Otherwise present:

```
G1 — INDEPENDENCE CHECK (P2)
G1 must be reviewed by someone other than the S1 author.
Was this S1 design document produced in THIS conversation?

  y — yes (the review will not run here)
  n — no, it was produced elsewhere

[y/n]:
```

- `y` → "G1 cannot run here. Open a new chat (or hand the design to a different reviewer) and
  load S1-2 there." Stop.
- `n` → ask for the reviewer's name/role (free text), record it, go to Step 1.

---

## Step 1 — Inventory

List what you parsed, so the user can confirm nothing was lost in the paste:

```
G1 INVENTORY — S1-<ACRONYM>-<NNN> v<X.Y.Z> (cycle <cycle>)
Modules (n): <id> · <layer> · hw_dependency · required_vl …
Contracts (n): <id> · <class> · <producer → consumer> · schema_version …
DAG edges (n): <from> -<contract>-> <to> …
Decisions (n): DEC-001 …   Risks (n): RSK-001 …
SyRS SYS blocks (n): …     StRS NRM blocks (n): …
```

Pause (`[c/r]`, next: mechanical checks).

---

## Step 2 — G1.1 DAG acyclicity (mechanical)

Run Kahn's algorithm on the §2.1 edges and **write the trace** (in-degree table, queue per
step). Compare the resulting order with §2.2.

| Check | Result |
|-------|--------|
| Is the DAG acyclic? | PASS / FAIL |
| Topological order obtained | (list) |
| Cycles detected | (list, or none) |
| §2.2 order consistent with the DAG? | yes / no: … |

---

## Step 3 — G1.2 Interface completeness (presence mechanical, sufficiency judgement)

For each DAG edge:

| Contract | Exists in §3? | Fields complete | Stub recipe present? | Sufficient for a deterministic stub without asking the designer? |
|----------|---------------|-----------------|----------------------|------------------------------------------------------------------|
| | yes / no | yes / missing: … | yes / no | yes / no: … |

Required fields: HW→SW — physical origin, COTS device, consumer, data type, shape, units, rate,
max latency, schema version, inherited budget · SW→SW — producer, consumers, data type, shape,
units, rate, max latency, schema version · SW→HW — emitter, physical target, data type,
meaning, latency, side effects.

---

## Step 4 — G1.3 Requirement coverage (mechanical, against the SyRS)

Compute the sets explicitly and show them:

| Check | Result |
|-------|--------|
| SYS-* in the SyRS without a module in §4.1 | (list) |
| Modules without SYS-* in §4.2 (orphans) | (list) |
| NRM-* constraining a contract without a row in §4.3 | (list) |

---

## Step 5 — G1.4 Stub feasibility (judgement)

For each stub recipe: can an implementer generate the stub from the contract alone?
Warning signs: "reasonable data"; no edge cases; data that exists only at VL-2; "stream" without
rate or buffer size; reference vectors whose expected output does not cite a SyRS block.

| Contract | Stub recipe sufficient? | Observations |
|----------|-------------------------|--------------|

---

## Step 6 — G1.5 Verification-profile consistency (mechanical)

| Module | hw_dependency | required_vl | Consistent? |
|--------|---------------|-------------|-------------|

Rule: `hw_dependency: true` → `required_vl: VL-2` (paper §6 rule 5).

Pause (`[c/r]`, next: judgement checks).

---

## Step 7 — G1.6 Quality of design decisions (judgement)

| Decision | Context clear? | Real alternatives? | Consequences honest? | Implementation-critical choice left unresolved? | Observations |
|----------|----------------|--------------------|----------------------|-------------------------------------------------|--------------|

---

## Step 8 — G1.7 COTS envelope coherence (judgement)

| Check | Result |
|-------|--------|
| Topology (§0.2) consistent with inventory (§0.1)? | |
| PHY-* cover every connection of the diagram? | |
| HW→SW inherited budgets coherent with PHY-*? | |
| Is the HAL the only point of contact with hardware? | |

---

## Step 9 — G1.8 Risks (judgement)

| RSK-ID | Evidence credible? | Mitigation viable? | Escalate to RFD? |
|--------|--------------------|--------------------|------------------|

"Escalate to RFD" is `yes` only when the evidence shows the requirement is infeasible on the
declared COTS platform (paper §9.2) — not merely hard, and not a design that could be changed.

---

## Step 10 — Verdict

Every row outcome has a fixed effect:

| Row | Negative outcome | Effect | Grounding |
|-----|------------------|--------|-----------|
| G1.1 | cycle found | BLOCKING | paper §6 rule 1 |
| G1.2 | contract missing / fields incomplete / no stub recipe / not sufficient for a deterministic stub | BLOCKING | paper §6 rules 2, 4 |
| G1.3 | SYS without module · NRM without contract | BLOCKING | paper §6 rule 3; template G1.3 |
| G1.3 | module without SYS (orphan) | ADVISORY (question it) | template "código huérfano (cuestionar)" |
| G1.4 | stub recipe insufficient | BLOCKING | paper §6 rule 4 |
| G1.5 | `hw_dependency: true` with VL ≠ VL-2 | BLOCKING | paper §6 rule 5 |
| G1.7 row 4 | a module touches hardware outside the HAL | BLOCKING | paper §5.1 "communicating only through the base layer's declared interfaces" |
| G1.6 / G1.7 rows 1–3 / G1.8 | the reviewer names an implementation-critical design choice left unresolved | BLOCKING | paper §6 G1 question |
| same rows | observation that leaves no implementation-critical choice open | ADVISORY | — |
| G1.8 | escalate to RFD = yes | → RFD | template "RFD → RFD formal"; paper §9.2 |

Verdict:
- Any BLOCKING ⇒ **FAIL** (cannot be argued away — P3), unless an RFD row concerns the same
  requirement ⇒ **RFD**.
- No BLOCKING and no RFD ⇒ **PASS**; list the ADVISORY rows.

```
G1 REVIEW REPORT
====================================================
Design: S1-<ACRONYM>-<NNN> v<X.Y.Z> · Cycle: <cycle>
Reviewer: <name / role> · Date: <YYYY-MM-DD>
Independence: confirmed (design not produced in this conversation)

MECHANICAL FINDINGS
[M-001] G1.<n> <section> — <finding>

JUDGEMENT FINDINGS
[J-001] G1.<n> <section> — <finding> — BLOCKING | ADVISORY

G1 VERDICT: PASS | FAIL | RFD
```

### On FAIL — DESIGN DEFECT NOTE

Map each blocking finding to the S1-1 job that owns its section (§0→Job 1 · DEC-001/Annex A→
Job 2 · §1→Job 3 · §2→Job 4 · §3→Job 5 · §4→Job 6 · §5/§6→Job 7):

```
DESIGN DEFECT NOTE
=====================================================================
Raised by: S1-2 (G1 FAIL) · Design: S1-<ACRONYM>-<NNN> v<X.Y.Z> · Cycle: <cycle>
| # | S1 section | Contract / module IDs | Defect | What would make it pass |
|---|------------|-----------------------|--------|-------------------------|
Evidence: G1 findings [M-…], [J-…] (ANALYSIS, no VL)
S1-1 jobs to re-run: Job <n> and every job after it
→ S1-1 (rework mode)
=====================================================================
```

### On RFD — RFD SEED

```
RFD SEED
=====================================================================
Stage: G1 (S1 design review) · Cycle: <cycle> · Design: S1-<ACRONYM>-<NNN> v<X.Y.Z>
Requirements in conflict: <ID>: <value> (source) · …
Evidence (ANALYSIS (no VL)): <RSK-… evidence, as written in §6>
→ SX-1
=====================================================================
```

### On PASS — G1 RECORD

```
G1 RECORD
=====================================================================
Design: S1-<ACRONYM>-<NNN> v<X.Y.Z> · Cycle: <cycle>
Verdict: PASS · Reviewer: <name / role> · Date: <YYYY-MM-DD>
Contracts: <id>@<schema_version>, …
Modules (topological order): <module>@<required_vl>, …
Advisories: <list, or none>
→ S2-1 (base layer, stubs, top-down integration)
=====================================================================
```

---

## Ground rules

- **Chat-only.** No tools, no file reads, no code execution.
- **Independent.** Never review a design produced in this conversation (P2).
- **Show the mechanics.** Kahn trace and coverage sets are written out, never asserted.
- **P3.** A BLOCKING row cannot be outvoted by a judgement that "it looks fine".
- **Fixed effects.** Each row's effect comes from the Step 10 table, never decided ad hoc.
- **Reviewer, not author.** Never rewrite contracts, modules or decisions; describe what would
  make them pass.
- **Only the paper's outcomes.** PASS → S2-1 · FAIL → S1-1 · RFD → SX-1.

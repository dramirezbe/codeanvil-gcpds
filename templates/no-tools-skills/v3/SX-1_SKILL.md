---
name: sx-1-request-for-deviation
description: "SX-1: Classify a gate failure as defect or infeasibility and, when the Build Package requirements are infeasible on the declared COTS platform, write the formal Request for Deviation (V-SIL v3 §9, chat-only). Trigger: RFD, request for deviation, infeasible requirements, RFD SEED."
metadata:
  author: "gcpds"
  version: "3.0"
  stage: "any"
  pipeline: "V-SIL"
---

# SX-1 — Request for Deviation

**V-SIL v3 | Feedback Routing — Request for Deviation (any stage) | No-Tools Variant**

V-SIL produces two kinds of feedback, and they must not be conflated (paper §9):

- A **defect** — *"V-SIL can fix it internally. The implementation or the design is wrong, but
  the requirements are achievable."* → design defect → S1, module defect → S2.
- An **RFD** — *"the Build Package requirements are infeasible on the declared COTS platform.
  V-SIL cannot fix it internally — the constraints themselves must change. V-SIL suspends until
  the Build Package is updated and re-enters at S0."*

You receive an RFD SEED, decide which of the two it is, and — only for an infeasibility — write
the Request for Deviation in the paper §9.3 form (ECSS-Q-ST-10-09C, MIL-HDBK-61A, NASA NPR
7150.2). You recommend; the **Build Package author decides** (P1). You never approve your own
RFD and never change the Build Package.

```
RFD SEED (S1-1, S1-2, S2-1, S2-2, S2-3) ──► [SX-1] ──► defect ──► S1-1 / S2-2 REWORK
                                               └──► infeasible ──► RFD-NNN ──► Build Package author
                                                                        └──► updated BP ──► S0-1
```

## Definitions

| Term | Meaning |
|------|---------|
| **RFD** | Request for Deviation: a "planned departure" from requirements (ECSS), requested when a product cannot meet its technical requirements, with impact analysis and trade-off options (MIL-HDBK-61A, NASA NPR 7150.2). |
| **RFD SEED** | Handoff block from another skill: stage of discovery, requirement IDs in conflict, evidence with its level. |
| **Defect** | Design or implementation wrong, requirements achievable (paper §9.1). |
| **Infeasibility** | The cited requirements are not met simultaneously on the declared COTS platform by the configurations evaluated (paper §9.2, RFD-001 evidence). |
| **Evidence level** | `VL-0`, `VL-1`, `VL-2` for test evidence (paper §8.1); `ANALYSIS (no VL)` for S1 / G1 design analysis. Always named (P4). |
| **Trade-off option** | A change to the Build Package that resolves the conflict: relaxing a requirement, or a design alternative with its rework impact (RFD-001 option C: "new module, new interface contract, S1 rework"). |
| **Build Package author** | Owner of the Build Package; the only one who decides an RFD (P1). |
| **Suspension** | After an RFD, V-SIL stops until the Build Package is updated; re-entry is at S0 (paper §9.2). |

## Activation Contract

**Load when:**
- The user pastes an **RFD SEED** from S1-1, S1-2, S2-1, S2-2 or S2-3.
- The user asks to write an RFD for requirements that conflict on the declared hardware.

**Do NOT load when:**
- The user wants a defect fixed → **S1-1** (design) or **S2-2** (module).
- The user wants the Build Package rewritten or normalised → the BP author, then **S0-1**.

**Context pack (C7):** the RFD SEED + the cited StRS/SyRS blocks (text and source) + the
evidence pastes the seed refers to.

## Preconditions

- Inputs pasted or attached (e.g. `RFD_SEED.md`, `G0_StRS.md`, `G0_SyRS.md`); no tools.
- The seed names the stage, the requirement IDs and the evidence with its level.
- The cited blocks are pasted, so each requirement can be quoted with its value and source.

## Decision Gates

| Situation | Action |
|-----------|--------|
| Seed missing stage, requirement IDs or evidence | Ask for the missing part; do not draft. |
| Evidence level not named | Ask which level / analysis produced it (P4). |
| Design wrong, requirements achievable | `DEFECT → S1-1` with a DESIGN DEFECT NOTE. Stop. |
| Implementation wrong, requirements achievable | `DEFECT → S2-2 REWORK <module>`. Stop. |
| Requirements not met simultaneously on the declared COTS by the configurations evaluated | `INFEASIBLE → RFD`. Continue to Step 3. |
| User asks you to choose an option for them | Refuse: you recommend; the BP author decides. |
| User asks you to edit the Build Package | Refuse: the BP author updates it; S0-1 normalises it. |

**Prompt discipline.** Pauses `[c/r]` ("continue" = `c`). Questions are answered, then the
pause is shown again.

---

## Output files

The RFD and routing records are delivered as **files**, not as in-chat text. In Claude, create
each one as a separate downloadable file (artifact) with exactly this name and its complete
content; if the interface cannot create files, emit one fenced block per file, headed by its
file name.

| File | Content | When |
|------|---------|------|
| `RFD-<NNN>.md` | Steps 3–5: the complete Request for Deviation, ending with the suspension / re-entry statement | INFEASIBLE |
| `DESIGN_DEFECT_NOTE.md` | The `DESIGN DEFECT NOTE` block | DEFECT → S1-1 |

The chat shows the intake table, the classification line, the pauses and the list of delivered
files. `RFD-<NNN>.md` is built across Steps 3–5 and re-delivered complete after each step.

---

## Step 1 — Intake

Restate the seed:

```
SX-1 INTAKE
Stage of discovery: <S1 | G1 | S2 | G2.0 | G2.1 | G2.2> · Cycle: <cycle> · Design: <ID> v<X.Y.Z>
| Requirement | Text / value | Source (standard or stakeholder) |
|-------------|--------------|----------------------------------|
Evidence (<level>):
| Configuration | Metric(s) | <Req A> met? | <Req B> met? |
```

Every value is copied from the pastes; nothing is estimated. Pause.

---

## Step 2 — Defect or infeasibility (paper §9)

Answer in writing, citing the evidence:

1. **Is the design wrong while the requirements are achievable?** (e.g. undeclared dependency,
   incomplete contract, a partitioning error the evidence exposes) → `DEFECT → S1-1`.
2. **Is the implementation wrong while the requirements are achievable?** (e.g. wrong
   normalisation, logic error) → `DEFECT → S2-2 REWORK <module>`.
3. Otherwise — the evidence shows the cited requirements are **not met simultaneously** on the
   declared COTS by the configurations evaluated → `INFEASIBLE → RFD`.

```
SX-1 CLASSIFICATION: DEFECT → S1-1 | DEFECT → S2-2 REWORK <module> | INFEASIBLE → RFD
Reason: <one paragraph citing the evidence rows>
```

For a design defect, emit:

```
DESIGN DEFECT NOTE
=====================================================================
Raised by: SX-1 (seed from <stage>) · Design: <ID> v<X.Y.Z> · Cycle: <cycle>
| # | S1 section | Contract / module IDs | Defect | Evidence (level) |
S1-1 jobs to re-run: Job <n> and every job after it
→ S1-1 (rework mode)
=====================================================================
```

For a module defect, name the module and the failing evidence for S2-2 REWORK. Then stop.

---

## Step 3 — RFD: conflicting requirements and evidence

```
Request for Deviation — RFD-<NNN>
  Project: <project> · Cycle: <cycle> · Stage of discovery: <stage> · Date: <YYYY-MM-DD>

  Conflicting requirements:
    <ID>: <value>    (source: <standard / stakeholder>)
    <ID>: <value>    (source: <standard / stakeholder>)

  Evidence (from <stage>, <level>):
    <configuration> → <metrics> — <ID> met, <ID> violated
    <configuration> → <metrics> — <ID> met, <ID> violated
```

USER-ATTESTED values keep their label. Pause.

---

## Step 4 — Trade-off options and impact analysis

At least two options, as in RFD-001 — relaxations and/or design alternatives:

```
  Trade-off options:
    A) <change to the Build Package>        → <which requirements are then met>
    B) <change to the Build Package>        → <…>
    C) <design alternative>                 → <…>, <cost: e.g. adds complexity>

  Impact analysis:
    Option A: <normative waiver needed? which clause>
    Option B: <compliance grade / capability lost>
    Option C: <new module, new interface contract, S1 rework>
```

Impact statements cite the affected blocks and standards; nothing is promised that the evidence
does not support. Pause.

---

## Step 5 — Recommendation, suspension, re-entry

```
  Recommendation: <option> — <one-paragraph rationale>

  Decision: Build Package author (not this skill).

V-SIL SUSPENDED — RFD-<NNN> issued at <stage>, cycle <cycle>.
On decision, the Build Package author updates the Build Package; V-SIL re-enters at S0
(S0-1, new chat, with the updated Build Package).
```

Stop.

---

## Ground rules

- **Classify first.** Only the paper's two classes: defect (S1 / S2) or infeasibility (RFD).
- **Evidence names its level.** `VL-n` or `ANALYSIS (no VL)`; nothing estimated or invented.
- **RFD-001 shape.** Conflicting requirements with sources · evidence · ≥ 2 trade-off options ·
  impact analysis per option · recommendation.
- **Recommend, never decide.** The Build Package author decides (P1); you never approve your
  own RFD (P2).
- **Never edit the Build Package or the GT.** Re-entry is always S0 with the updated BP.
- **Chat-only.** No tools, no execution; inputs are pasted or attached.
- **Files out.** `RFD-<NNN>.md` or `DESIGN_DEFECT_NOTE.md`, complete.

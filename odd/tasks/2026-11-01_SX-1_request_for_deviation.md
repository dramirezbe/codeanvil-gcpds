# Plan — Skill SX-1: Request for Deviation (RFD)

Feature: `odd/tasks/2026-11-01_2235_no_tools_skills_v3.md` · Specs S1, S2, S3, S6 · Task T6
Target file: `templates/no-tools-skills/v3/SX-1_SKILL.md`
Prefix `SX`: cross-stage — an RFD can be raised from Gate H, S1-1, S1-2, S2-1, S2-2, S2-3.
Shared contracts used: C1–C3, C7, C12 (feature doc).

## Objetivo

Turn an infeasibility finding into a formal **Request for Deviation** (ECSS-Q-ST-10-09C,
MIL-HDBK-61A, NASA NPR 7150.2 per paper §9.3): conflicting requirements with sources,
evidence with the level it came from, ≥ 2 trade-off options, impact analysis,
recommendation. First apply the **defect-vs-infeasibility test (C12)** so internal defects
(S1/S2) and GT gaps (S0) are routed back instead of being escalated. The RFD suspends V-SIL;
the Build Package author decides; re-entry is at S0 with an updated Build Package.

## Mapeo V-SIL-v3

| Paper | Element |
|-------|---------|
| §9 Feedback routing | classify: defect (internal) vs RFD (external) |
| §9.1 | defect classes → S1 / S2 (not an RFD) |
| §9.2 | RFD = infeasible on the declared COTS; suspend; re-enter at S0; emission points table |
| §9.3 | RFD contents (example RFD-001); option C read per C12 as violating a complexity/schedule constraint |
| §9.4 | distinction summary |
| §2 overview | `S1 -.-> RFD`, `G2 -.-> RFD`, `RFD -.-> BP` |

## Activation Contract (C1)

**Load when:** an `RFD SEED` is pasted (from Gate H, S1-1, S1-2, S2-x), or the user asks
whether a requirement conflict is a deviation, or asks to write an RFD.
**Do NOT load when:** the problem is a missing value in the GT (→ GT GAP NOTE → S0-1); the
user wants a fix implemented (→ S1-1 / S2-2).
**Context pack (C7):** RFD SEED + the cited StRS/SyRS blocks + the Build Package's explicit
constraints (cost, schedule, stack, complexity) + evidence pastes.

## Inputs

| Input | Source | Required |
|-------|--------|----------|
| `RFD SEED` (C3): stage, requirement IDs, evidence | Gate H, S1-1 Job 7, S1-2, S2-1, S2-2, S2-3 | yes |
| Evidence with level: `VL-0 / VL-1 / VL-2` (tests) or `ANALYSIS (no VL)` (Gate H, S1 budgets, datasheet arithmetic) | user / seed | yes (m2) |
| Cited StRS/SyRS blocks (text + source) | user | yes |
| Build Package explicit constraints (cost, schedule, stack, complexity) | user / BP | yes — C12 needs them |
| Previous RFD numbers | user | optional (numbering) |

## Outputs

1. **Classification verdict** (C12) — one of:
   - `DEFECT → S1-1` (another design/algorithm on the same COTS meets all cited
     requirements and violates no explicit BP constraint) — with a DESIGN DEFECT NOTE.
   - `DEFECT → S2-2 REWORK <module>` (a correct implementation of the current design would
     meet them).
   - `GT GAP → S0-1` (the conflict comes from a missing/ambiguous value, not a limit) — GT GAP NOTE.
   - `MORE EVIDENCE` (evidence level cannot support the claim — e.g. VL-0 for a physical
     limit — name the VL-1/VL-2 test or analysis needed).
   - `INFEASIBILITY → RFD`.
2. **RFD-NNN document** (paper §9.3 shape, extended):
   - Header (RFD id, project, cycle, date, stage of discovery, raised by)
   - Conflicting requirements (ID, text, value, source/standard)
   - Evidence (stage, level, environment, data table; USER-ATTESTED labels kept)
   - Why no same-COTS option works: each candidate option + the requirement or explicit BP
     constraint it violates (C12 proof)
   - Trade-off options A/B/C… (each: what changes in the BP — requirement, COTS, or
     constraint — and which requirements are then met)
   - Impact analysis per option (normative waiver? compliance grade? S1 rework? new
     module/contract? cost/schedule)
   - Recommendation + rationale
   - Disposition block for the BP author (C2): `[A..Z] approve option | REJECT | EVIDENCE <what>`
   - Re-entry statement: "V-SIL suspended. On approval, update Build Package → S0-1."
3. **Build Package delta** for the approved option (exact text changes) → S0-1.

## Prompt template (resumido)

```
Step 1  Intake seed (stage, requirement IDs, evidence + level, BP constraints).
Step 2  Classification (C12), three questions in order:
        a) Same-COTS option: is there a design/algorithm on the declared COTS that meets ALL
           cited requirements? For each candidate: does it violate another requirement or an
           explicit BP constraint (cite it)? Any candidate with no violation → DEFECT → S1-1.
        b) Implementation: would a correct implementation of the current design meet them?
           yes → DEFECT → S2-2 REWORK.
        c) Evidence level: can the evidence level support the claim? no → MORE EVIDENCE.
        Also: is the conflict really a missing GT value? → GT GAP → S0-1.
        Only when a), b), c) all point to infeasibility → RFD.
Step 3  Draft RFD-NNN (header, conflict, evidence, C12 proof). pause.
Step 4  Options + impact analysis (≥ 2 options; at least one keeps all requirements and
        changes the COTS — never only "relax", m3). pause.
Step 5  Recommendation + disposition block + BP delta. Final: "V-SIL SUSPENDED".
        Disposition answer (C2) → approve → emit BP delta for S0-1; REJECT → V-SIL stays
        suspended, record; EVIDENCE → list the evidence to produce and the skill that produces it.
```

## Criterios de aceptación

1. Classification always runs first; a same-COTS option without a cited violation is always
   routed as DEFECT, never as RFD (C12).
2. Every conflicting requirement cites its ID and source; every evidence row names its level
   (`VL-n` or `ANALYSIS (no VL)`).
3. ≥ 2 options with impact analysis, at least one changes COTS; recommendation justified.
4. The skill does not approve its own RFD — disposition is the BP author's (P1/P2).
5. Ends with the suspension + S0 re-entry statement.
6. Test (FM case, fixture `F3_pastes.md`, T2b):
   - 6a. Seed "7 overflows in 30 min at 20 MS/s" with no sweep evidence → `DEFECT → S1-1`
     (candidate: two 10 MHz half-band captures at 10 MS/s on the same HackRF, which would
     meet `STK-SPEC-001` and `STK-OPS-001` if line rate holds) — or `MORE EVIDENCE` on the
     sweep's line rate.
   - 6b. Same seed + pasted VL-2 evidence "half-band sweep with retune settling → 8 lines/s"
     (violates `STK-SPEC-002` ≥ 10 lines/s) → `INFEASIBILITY → RFD` with options such as
     A) host with a different USB 2.0 controller / USB 3 host (COTS change, all requirements
     kept), B) relax `STK-SPEC-002` to ≥ 8 lines/s, C) relax `STK-SPEC-001` coverage to
     90–106 MHz at 16 MS/s.

## Dependencias

- Upstream: any stage (RFD SEED). Downstream: Build Package author → S0-1; or S1-1 / S2-2 /
  S0-1 when classification routes back.

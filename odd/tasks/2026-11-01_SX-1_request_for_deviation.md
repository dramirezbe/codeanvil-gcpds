# Plan — Skill SX-1: Request for Deviation (RFD)

Feature: `odd/tasks/2026-11-01_2235_no_tools_skills_v3.md` · Specs S1, S2, S3, S6 · Task T6
Target file: `templates/no-tools-skills/v3/SX-1_SKILL.md`
Prefix `SX`: cross-stage — an RFD can be raised from S1, G1, G2.0, G2.1, G2.2 (and Gate H).

## Objetivo

Turn an infeasibility finding into a formal **Request for Deviation** (ECSS-Q-ST-10-09C,
MIL-HDBK-61A, NASA NPR 7150.2 per paper §9.3): conflicting requirements with sources,
evidence with the verification level it came from, ≥ 2 trade-off options, impact analysis,
recommendation. First apply the **defect-vs-infeasibility test** so internal defects are
routed back (S1/S2) instead of being escalated. The RFD suspends V-SIL; the Build Package
author decides; re-entry is at S0 with an updated Build Package.

## Mapeo V-SIL-v3

| Paper | Element |
|-------|---------|
| §9 Feedback routing | classify: defect (internal) vs RFD (external) |
| §9.1 | defect classes → S1 / S2 (not an RFD) |
| §9.2 | RFD = infeasible on the declared COTS; suspend; re-enter at S0; emission points table |
| §9.3 | RFD contents (example RFD-001) |
| §9.4 | distinction summary |
| §2 overview | `S1 -.-> RFD`, `G2 -.-> RFD`, `RFD -.-> BP` |

## Inputs

| Input | Source | Required |
|-------|--------|----------|
| RFD seed: stage of discovery, requirement IDs in conflict, evidence | S1-1 Job 7, S1-2 verdict RFD, S2-x, S2-3 | yes |
| G0_StRS.md / G0_SyRS.md (to quote requirement text + sources) | user | yes |
| Evidence pastes (metric tables, measurements, latency budgets) with VL | user | yes |
| Previous RFD numbers | user | optional (numbering) |

## Outputs

1. **Classification verdict** — `DEFECT (→ S1 | S2)` or `INFEASIBILITY (→ RFD)`, with the
   test applied: "Is there *any* design/implementation on the declared COTS that meets all
   cited requirements simultaneously, given the evidence?"
2. **RFD-NNN document** (paper §9.3 shape, extended):
   - Header (RFD id, project, cycle, date, stage of discovery, raised by)
   - Conflicting requirements (ID, text, value, source/standard)
   - Evidence (stage, VL, environment, data table) — honesty: evidence VL named
   - Trade-off options A/B/C… (each: what changes in the BP, which requirements met)
   - Impact analysis per option (normative waiver needed? compliance grade? S1 rework? new module/contract? cost/schedule)
   - Recommendation + rationale
   - Disposition block (to be filled by BP author): `APPROVED option X | REJECTED | MORE EVIDENCE`
   - Re-entry statement: "V-SIL suspended. On approval, update Build Package → S0-1."
3. **Build Package delta** for the recommended option (exact text changes) — handed to S0-1
   once the author approves.

## Prompt template (resumido)

```
Step 1  Intake seed (stage, requirement IDs, evidence, VL).
Step 2  Defect-or-infeasibility test (ask the 3 diagnostic questions):
        a) Could another partitioning/algorithm on the same COTS meet all requirements? (yes → S1 defect)
        b) Could a correct implementation of the current design meet them? (yes → S2 defect)
        c) Does the evidence come from a level that can support the claim? (VL-0 evidence of
           a physical limit is weak → ask for VL-1/VL-2 evidence or analysis)
        → classification; if DEFECT: stop with routing.
Step 3  Draft RFD-NNN. pause.
Step 4  Options + impact analysis (≥ 2 options; at least one keeps requirements and changes
        COTS or scope; never only "relax"). pause.
Step 5  Recommendation + disposition block + BP delta. Final: "V-SIL SUSPENDED".
```

## Criterios de aceptación

1. Classification step always runs first; defects never become RFDs.
2. Every conflicting requirement cites its ID and source; every evidence row names its VL.
3. ≥ 2 options with impact analysis; recommendation justified.
4. The skill does not approve its own RFD — disposition is left to the BP author (P1/P2).
5. Ends with the suspension + S0 re-entry statement.
6. Test: FM case — "20 MS/s USB 2.0 sustained throughput → overflows > STK-OPS-001 limit;
   16 MS/s loses 88–90 & 106–108 MHz (STK-SPEC-001)" produces an RFD with options such as
   A) dual-tune sweep two 10 MHz halves, B) relax coverage, C) change host/USB controller.

## Dependencias

- Upstream: any stage. Downstream: Build Package author → S0-1.

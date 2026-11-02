# Plan — Skill SX-1: Request for Deviation (RFD)

Feature: `odd/tasks/2026-11-01_2235_no_tools_skills_v3.md` · Specs S1, S2, S3, S6 · Task T6
Target file: `templates/no-tools-skills/v3/SX-1_SKILL.md`
Prefix `SX`: cross-stage — paper §9.2 "An RFD can be emitted from **any stage**" (table: S1,
G2.0, G2.1, G2.2).
Shared contracts used: C0–C3, C7, C12 (feature doc).

## Objetivo

Write the formal **Request for Deviation** exactly as paper §9.2–§9.3 define it
(ECSS-Q-ST-10-09C, MIL-HDBK-61A, NASA NPR 7150.2): conflicting requirements with sources,
evidence naming its stage and verification level, trade-off options, impact analysis,
recommendation. First check the paper's own distinction (§9, §9.4): a **defect** (design or
implementation wrong, requirements achievable) is routed back to S1/S2; only
"requirements infeasible on the declared COTS platform" becomes an RFD. V-SIL then
**suspends** until the Build Package is updated and re-enters at S0.

## Mapeo V-SIL-v3

| Paper | Element |
|-------|---------|
| §9 Feedback routing | "Defect or infeasibility?" — implementation or design → internal; requirements infeasible → external |
| §9.1 | defect classes → S1 / S2; self-diagnosis |
| §9.2 | RFD definition, suspension, re-entry at S0, emission points |
| §9.3 | RFD contents — the RFD-001 template (conflicting requirements, evidence with VL, trade-off options, impact analysis, recommendation) |
| §9.4 | distinction summary |
| §2 overview / abstract | `S1 -.-> RFD`, `G2 -.-> RFD`, `RFD -.-> updated BP → S0` |
| P1 / P2 | the Build Package author decides; the skill does not approve its own RFD |

## Activation Contract (C1)

**Load when:** an `RFD SEED` is pasted (from S1-1 Job 7, S1-2 verdict RFD, S2-1, S2-2, or
S2-3), or the user asks to write an RFD for conflicting requirements.
**Do NOT load when:** the failure is a design or implementation defect (→ S1-1 / S2-2 per
§9.1); the user wants a fix implemented.
**Context pack (C7):** RFD SEED + the cited StRS/SyRS blocks (text + source) + evidence pastes.

## Inputs

| Input | Source | Required |
|-------|--------|----------|
| `RFD SEED` (C3): stage of discovery, requirement IDs in conflict | S1-1, S1-2, S2-1, S2-2, S2-3 | yes |
| Evidence: data table naming its stage and level (`VL-0/1/2`; at S1 the design analysis of S1_G1_template §6) | seed / user | yes — RFD-001 "Evidence (from G2.1, VL-1)" |
| Cited StRS/SyRS blocks with their sources | user | yes |
| Previous RFD numbers | user | optional (numbering) |

## Outputs

1. **Classification** (paper §9 diamond, C12):
   - `DEFECT → S1-1` (design wrong, requirements achievable: e.g. undeclared dependency,
     incomplete contract) — with a DESIGN DEFECT NOTE.
   - `DEFECT → S2-2 REWORK <module>` (implementation wrong, requirements achievable).
   - `INFEASIBLE → RFD` (evidence shows the cited requirements are not met simultaneously
     on the declared COTS by the configurations evaluated).
2. **RFD-NNN document** in the paper §9.3 shape:
   ```
   Request for Deviation — RFD-NNN
     Conflicting requirements:   <ID>: <value>   (source: <standard / stakeholder>)
     Evidence (from <stage>, <VL>):  <configuration> → <metrics> — <ID> met/violated
     Trade-off options:          A) … → both met   B) …   C) …  (may include design
                                 changes, e.g. "new module, new interface contract, S1 rework")
     Impact analysis:            per option (normative waiver, compliance grade, S1 rework …)
     Recommendation:             <option> + one-paragraph rationale
   ```
   followed by: "V-SIL suspended until the Build Package is updated; re-entry at S0 (S0-1)."
3. Nothing else: the Build Package author updates the Build Package (P1); S0-1 normalises it.

## Prompt template (resumido)

```
Step 1  Intake seed: stage, requirement IDs, evidence (with VL / S1 analysis).
Step 2  Classification (§9): is the design or the implementation wrong while the requirements
        are achievable? → DEFECT (S1-1 or S2-2) and stop. Otherwise → RFD.
        Every evidence row keeps its VL (P4); evidence is never invented (C4).
Step 3  Draft RFD-NNN: conflicting requirements + evidence. pause.
Step 4  Trade-off options + impact analysis (like RFD-001: relaxations and/or design
        alternatives with their rework impact). pause.
Step 5  Recommendation + suspension/re-entry statement. End.
```

## Criterios de aceptación

1. Classification runs first and uses only the paper's two classes (defect / infeasible).
2. The RFD has every RFD-001 section: conflicting requirements with sources, evidence with
   stage + VL, trade-off options, impact analysis per option, recommendation.
3. ≥ 2 trade-off options (RFD-001 lists three).
4. The skill does not approve or apply its own recommendation — the Build Package author
   decides and updates the BP (P1/P2).
5. Ends with the suspension + S0 re-entry statement (§9.2).
6. Test (FM case, fixture `F3_pastes.md`, T2b): seed from G2.2 — 20 MS/s: 7 overflows /
   30 min (`STK-OPS-001` ≤ 3 violated, `STK-SPEC-001` met); 16 MS/s: 0 overflows but span
   90–106 MHz (`STK-OPS-001` met, `STK-SPEC-001` violated) → `INFEASIBLE → RFD` with options
   such as A) relax coverage to 90–106 MHz, B) relax overflow limit, C) two half-band
   captures with retuning (new module + contract, S1 rework — like RFD-001 option C),
   D) host with a different USB controller; impact analysis and a recommendation.
7. Test: a seed whose evidence is a module bug (wrong dBFS normalisation) → `DEFECT → S2-2`.

## Dependencias

- Upstream: any stage (RFD SEED). Downstream: Build Package author → updated BP → S0-1;
  or S1-1 / S2-2 when classified as a defect.

# Plan — Skill S1-2: G1 Design Review (DAG + Contract Validation)

Feature: `odd/tasks/2026-11-01_2235_no_tools_skills_v3.md` · Specs S1, S2, S3, S6 · Task T4
Target file: `templates/no-tools-skills/v3/S1-2_SKILL.md`

## Objetivo

Act as the **independent reviewer** (P2: oracle ≠ generator) of an S1 design document
and answer the single G1 question: *Are all implementation-critical design choices
resolved?* Run the eight review sections of the template (G1.1–G1.8): mechanical checks
first (they override any judgement — P3), then design-judgement checks; emit
`PASS → S2`, `FAIL → S1 (with rework list)` or `RFD → SX-1`.

## Mapeo V-SIL-v3

| Paper / template | Skill step |
|------------------|-----------|
| Paper §6 rule 1 DAG acyclicity / template G1.1 | Step 2 (mechanical) |
| Paper §6 rule 2 interface completeness / G1.2 | Step 3 (presence mechanical, sufficiency judgement) |
| Paper §6 rule 3 coverage / G1.3 | Step 4 (mechanical vs SyRS) |
| Paper §6 rule 4 stub feasibility / G1.4 | Step 5 (judgement) |
| Paper §6 rule 5 VL profile consistency / G1.5 | Step 6 (mechanical) |
| Template G1.6 decision quality | Step 7 (judgement) |
| Template G1.7 COTS envelope coherence | Step 8 (judgement) |
| Template G1.8 risks / escalate to RFD | Step 9 (judgement) |
| Template "Veredicto G1" PASS/FAIL/RFD | Step 10 |
| P2 note at the end of template | Step 0 independence check |

## Inputs

| Input | Source | Required |
|-------|--------|----------|
| `S1_design.md` | S1-1 (pasted) | yes |
| G0_SyRS.md | user | yes (coverage G1.3 is checked against it) |
| G0_StRS.md | user | yes (NRM → contract, HWC/PHY coherence) |
| Reviewer identity (name/role) | user | yes (recorded in verdict) |

## Outputs

`G1 REVIEW REPORT` with:
- Independence statement (Step 0).
- One filled table per G1.1–G1.8 (template column layout), each cell `PASS/FAIL` or
  `sí/no/insuficiente` with an observation.
- Mechanical-findings list (`[M-NNN]`) and judgement-findings list (`[J-NNN]`), each
  pointing to a section of the S1 document.
- `G1 VERDICT: PASS | FAIL | RFD`.
- FAIL → **Rework list**: section → concrete defect → what would make it pass, plus the
  S1-1 jobs to re-run (e.g. "Job 5 contracts c_psd_frame; downstream Jobs 6–7").
- RFD → **RFD seed**: conflicting requirement IDs + evidence + candidate options, to be
  pasted into SX-1.
- PASS → **G1 Record** (design doc version/date, reviewer, verdict) for S2-1.

## Prompt template (resumido)

```
Step 0  INDEPENDENCE CHECK
        "G1 must be reviewed by someone other than the S1 author (P2).
         Was S1_design.md produced in THIS conversation? [y/n]"
         y → refuse: "Open a new chat (or hand to a different reviewer) and load S1-2 there."
         n → record reviewer name/role and continue.
Step 1  Inventory: list modules, contracts, DAG edges, DECs, RSKs parsed from the document.
Step 2–6  Mechanical sections (G1.1, G1.2 presence, G1.3, G1.5) — FAIL here is final (P3).
Step 5,7–9  Judgement sections (G1.2 sufficiency, G1.4, G1.6, G1.7, G1.8).
Step 10 Verdict + rework list / RFD seed / G1 Record.
```

Verdict rules:
- Any mechanical failure ⇒ FAIL (cannot be argued away).
- Any contract judged "insuficiente" for a deterministic stub ⇒ FAIL.
- A risk whose evidence shows infeasibility under every partitioning on the declared
  COTS ⇒ RFD (not FAIL — a redesign cannot fix it).
- Otherwise PASS. Judgement observations that do not block are listed as advisories.

## Criterios de aceptación

1. All eight G1 sections present with the template's columns.
2. Mechanical checks performed explicitly (e.g. Kahn's algorithm trace written out for
   G1.1; set difference for G1.3) — not asserted.
3. P3 respected: verdict cannot be PASS if any mechanical row fails.
4. The skill refuses to review a design produced in the same conversation.
5. FAIL output names S1-1 jobs to re-run; RFD output names conflicting requirement IDs.
6. The skill never fixes the design itself (reviewer, not author).

## Dependencias

- Upstream: S1-1. Downstream: S2-1 (PASS), S1-1 (FAIL), SX-1 (RFD).

## Design notes

- v2 had G1 as design synthesis + self-validation in the same skill; v3 splits author
  (S1-1) and reviewer (S1-2) to enforce P2.

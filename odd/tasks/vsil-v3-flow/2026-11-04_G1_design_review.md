# Plan — G1: human design review (HITL)

Feature: `odd/tasks/2026-11-04_1042_vsil_v3_skill_flow.md` · Task T1 · Specs S1, S2, S3, S7, S9 · Contracts C0–C8
Target: `templates/skills/G1_design_review/` with `SKILL.md` (about 80 lines) and `references/G1_CHECKLIST.md` (about 130 lines). Paper §6, `S1_G1_template.md` G1.1–G1.11.

## Goal

Answer the paper's one question: *Are all implementation-critical design choices resolved?* **The human answers it.** S7: "No deterministic gates. The only determniistic gate is the S0 normalization. The rest are all HITL." G1 has no script and no exit code: the agent prepares the evidence, and the verdict is the human's.

## `references/G1_CHECKLIST.md`

English translation of the G1 half of the template, kept as the report's filled form. The agent pre-fills every row and marks each finding `open` or `advisory`:

| Row | Agent checks and shows | Marked `open` when |
|-----|------------------------|--------------------|
| Graph | `S1_graph.html` shows every service, module, device and service contract of the design, and its panel matches `.codeanvil/project.yaml` | Something is missing or differs, because the human would be reviewing the wrong picture. A missing file is `advisory` |
| G1.1 DAG | Derives the order from the §1.4 cards and compares it with §2.2 | A cycle exists. §3.4 service contracts create no edge: "Runtime message loops do not create implementation dependency cycles" (paper §5.3) |
| G1.2, G1.4 contracts and stubs | Each contract named by a card exists in §3, with fields and a recipe | An implementer would have to ask the designer |
| G1.3 coverage | `SYS-*` in §4.1, `NRM-*` in §4.3, cross-service `SYS-*` in §4.4 | A requirement is uncovered. A module without `SYS-*` is `advisory` |
| G1.5 profile | `hw_dependency: true` means `VL-2`; each `PATH-*` names level and environment | Any mismatch |
| G1.6, G1.7 rows 1–3, G1.8 | Decisions, COTS coherence, risks | An implementation-critical choice is unresolved; otherwise `advisory` |
| G1.8 RFD escalation | Applies paper §9 to each risk: achievable means defect, infeasible on the declared COTS platform means RFD | The test points to RFD. The recommendation names it, with `ANALYSIS (no VL)` evidence |
| G1.7 row 4 | HAL is the only hardware contact | A module touches hardware outside the HAL |
| G1.7 row 5, G1.9 | Links support the contracts; state owner, timeout, acknowledgement, idempotency, safe disconnect | Any is undefined |
| G1.10 | Path budget split across modules and link; VL-0 connected-process test exists | Either is missing |
| G1.11 | Only if §1.5 exists: weights, digest, runtime, COTS budget, fake response | Any is missing. Supplied metrics are not judged as G2 evidence |

## `SKILL.md`

Frontmatter: `name: g1-design-review`, `metadata.gate: "G1"`.

1. **Prerequisite.** C2 on `S1.md`. On G1's own unreworked FEEDBACK it returns `S1 must rework first. Run the S1 skill.`, so an unchanged design is never reviewed twice. The iteration's Description starts with `Based on: S1 iteration <N>` (C11).
2. **Hard rules.**
   - The agent recommends; only the human's answer sets `HITL`. Never write `PASS` without it.
   - `open` findings are shown first and never hidden, softened or fixed here. Rework belongs to S1.
   - The human may pass a design with `open` findings; the answer is recorded verbatim.
   - The graph is a reading aid. The prerequisite and the verdict rest on `S1.md`, the design and the human's answer. G1 never edits the graph; a wrong graph goes back to S1.
3. **Steps.** (0) Give the human the graph's path from `S1.md`: its spiders support the topology and runtime-loop review (G1.9), while the build order is reviewed in the design's §2 (G1.1). (1) Fill the checklist against the design and the GT. (2) Recompute the GT digests and show whether they match the design's Meta row (C5, information only). (3) Present findings and a recommendation, which names RFD when the G1.8 test points to it. (4) Ask **PASS**, **FEEDBACK** or **RFD**. (5) Write the iteration with the filled checklist and the answer verbatim.

| Human answer | Report | Route |
|--------------|--------|-------|
| PASS | `HITL: PASS` | S2 |
| FEEDBACK | `HITL: FEEDBACK` + sections to rework | S1 |
| RFD | `HITL: FEEDBACK` + `Verdict: RFD` | RFD skill |

Reports need no third state: `Verdict: RFD` is a Description line, and FEEDBACK blocks S2 under C2.

## RED tests first

`tests/test_create.py` through `_skill_text("G1_design_review")`:

- names `.codeanvil/report/<cycle-name>/G1.md` and `S1 must pass first. Run the S1 skill.`;
- names `PASS`, `FEEDBACK` and `RFD` as the human's answers;
- does not contain `g1_check` (S7);
- names `S1_graph.html` (S9);
- names `S1 must rework first. Run the S1 skill.`, `Cycle suspended by RFD. Run the RFD skill.` and `Based on: S1 iteration` (C2, C11).

T6 removes the tests of the old `G1_start_design` skill.

## Acceptance

1. No script under `templates/skills/G1_design_review/`.
2. A FEEDBACK iteration names the sections to rework.
3. The agent does not write `HITL` before the human answers (T7).
4. Re-running G1 after FEEDBACK with no S1 rework writes no iteration and routes to S1 (T7).
5. A graph that lacks a module of the design produces an `open` finding, and a deleted graph does not stop G1 (T7).

## Known tradeoff (S7)

A structural defect such as a dependency cycle is now caught only if the agent notices it or the human does. Nothing stops a human PASS on it. The filled checklist records what was shown, so the decision is auditable.

## Reuse

The report contract from `G0_valid_req_and_GT/SKILL.md`; `_copy_skills` ships `references/`; the old `G1_artifacts` convention becomes `S1_artifacts`.

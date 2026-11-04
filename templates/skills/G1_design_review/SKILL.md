---
name: g1-design-review
description: "Trigger: G1, design review, review the S1 design, are design choices resolved. Prepare a design review of the S1 document for a human, with a filled checklist and a recommendation, and record the human's PASS, FEEDBACK or RFD answer."
license: Apache-2.0
compatibility: "No network access, no scripts. Writes only .codeanvil/report/<cycle-name>/G1.md."
metadata:
  author: "gcpds"
  version: "1.0"
  gate: "G1"
  pipeline: "V-SIL"
---

# G1 — Human Design Review

G1 answers one question: **are all implementation-critical design choices resolved?**
**The human answers it.** G1 has no script and no exit code: the agent prepares the evidence and
recommends; only the human's answer sets the verdict.

## Prerequisite and Cycle

Resolve the active cycle from `.codeanvil/project.yaml` (`cycle:`); if missing, ask the user.
Then check, in this order, writing **no iteration** when you stop:

1. `.codeanvil/report/<cycle-name>/S1.md` is missing or its latest iteration is not
   `HITL: PASS`: return exactly `S1 must pass first. Run the S1 skill.`
2. `codeanvil status` marks `S1` or any earlier report of the cycle `stale`: return the same
   line, naming the earliest stale report.
3. G1's own latest iteration is `FEEDBACK`. With `Verdict: RFD`, return exactly
   `Cycle suspended by RFD. Run the RFD skill.`, unless the latest `RFD.md` iteration states
   `Outcome: Withdrawn`. Otherwise, if its `Based on` line names the current latest S1
   iteration, the design was not reworked: return exactly
   `S1 must rework first. Run the S1 skill.` An unchanged design is never reviewed twice.

## Inputs

| Path | Role |
|------|------|
| `.codeanvil/report/<cycle-name>/S1_artifacts/S1_design.md` | The design under review |
| `.codeanvil/report/<cycle-name>/S1_artifacts/S1_graph.html` | Reading aid, named in `S1.md` |
| `GT/G0_StRS.md`, `GT/G0_SyRS.md` | Read-only: requirements the design must cover |
| `templates/skills/G1_design_review/references/G1_CHECKLIST.md` | This skill's checklist and filled form |

## Hard Rules

- The agent recommends; **only the human's answer sets `HITL`**. Never write `PASS` without it.
- `open` findings are shown first and never hidden, softened or fixed here. Rework belongs to S1.
- The human may pass a design that has `open` findings. Record the answer verbatim.
- The graph is a reading aid. The prerequisite and the verdict rest on `S1.md`, the design and the
  human's answer. G1 never edits the graph; a wrong graph goes back to S1.
- Never edit the design or GT here.

## Steps

1. Give the human the graph's path from `S1.md`: its spiders support the topology and
   runtime-loop review (G1.9); the build order is reviewed in the design's §2 (G1.1).
2. Fill the checklist against the design and the GT.
3. Recompute the GT digests with
   `python -c "import hashlib,sys;[print(hashlib.sha256(open(p,'rb').read()).hexdigest(),p) for p in sys.argv[1:]]" GT/G0_StRS.md GT/G0_SyRS.md`
   and show the human whether they match the design's Meta row. Information only: it never blocks.
4. Present the findings, `open` first, and a recommendation. When the G1.8 test points to RFD,
   the recommendation names it.
5. Ask the human: **PASS**, **FEEDBACK** or **RFD**, and who is deciding.
6. Write the iteration with the filled form and the answer verbatim, including `Decided by: <name>`.

| Human answer | Row written | Route |
|--------------|-------------|-------|
| PASS | `HITL: PASS` | S2, which is not available yet: return "G1 passed. S2 is not available in this release." |
| FEEDBACK | `HITL: FEEDBACK` plus sections to rework | S1 |
| RFD | `HITL: FEEDBACK` plus the line `Verdict: RFD` | RFD skill |

## Report Contract

Write exactly one file: `.codeanvil/report/<cycle-name>/G1.md`, append-only.

- First run: header plus `## Iteration 1`; later runs append `## Iteration <N>`.
- Header: a `| Field | Value |` table with `Gate` = `G1`, `Cycle`, `Document` (the design path) and
  `Created` = `codeanvil now`.
- Iteration: a `| Field | Value |` table with `Date` = `codeanvil now`, `Timestamp` =
  `codeanvil now --machine`, `Iteration`, `Cycle`, and exactly one row written as
  `| HITL | PASS |` or `| HITL | FEEDBACK |` (never both in one row, which `codeanvil status`
  reads as `UNKNOWN`). Then `### Description`.
- The Description starts with the exact line `Based on: S1 iteration <N>`, where `N` is the latest
  S1 iteration when the review starts, followed by the filled checklist form.
- G1 is a **gate**: its `PASS` is the human's verdict.

## Output Contract

Return the findings (`open` first), the recommendation, the human's answer, the report path with
the iteration number, and the route.

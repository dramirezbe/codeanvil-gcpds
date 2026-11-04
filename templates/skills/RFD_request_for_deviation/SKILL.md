---
name: rfd-request-for-deviation
description: "Trigger: RFD, request for deviation, infeasible requirement, Build Package conflict. Write a decision document for the Build Package author when requirements are infeasible on the declared COTS platform, and suspend the cycle until the author decides."
license: Apache-2.0
compatibility: "No network access, no scripts. Writes .codeanvil/report/<cycle-name>/RFD.md and RFD_artifacts/RFD-NNN.md."
metadata:
  author: "gcpds"
  version: "1.0"
  gate: "RFD"
  pipeline: "V-SIL"
---

# RFD — Request for Deviation

When Build Package requirements are **infeasible on the declared COTS platform**, V-SIL
suspends. The agent writes a decision document; the Build Package author decides; the flow
re-enters at S0 in a **new cycle** with the updated Build Package.

RFD is outside the chain: it has no prerequisite and can be raised from S1, G1 or any
sub-gate of G2.

## Prerequisite and Cycle

1. Resolve the active cycle from `.codeanvil/project.yaml`. If it is missing, ask the user.
2. A raising stage and its evidence are required (the design's risk section, a G1
   recommendation, or a G2 report). Without them, stop and say so.

## Defect Test First

- A **defect** means V-SIL can fix it internally: the implementation or the design is wrong,
  but the requirements are achievable. **Do not raise an RFD.** Route to S1 (or S2) and write
  no `RFD-NNN.md`.
- An **RFD** means the Build Package requirements are **infeasible on the declared COTS
  platform**.
- A failure in an unchanged module means an undeclared dependency: a design defect, routed to S1.

## Document

Write `.codeanvil/report/<cycle-name>/RFD_artifacts/RFD-NNN.md` (one per deviation,
numbered from 001, overwritten only by the same RFD) with these sections, in this order:

1. Conflicting requirements, each with its source block ID in `GT/`.
2. Evidence, naming the stage and verification level. At S1 the evidence is
   `ANALYSIS (no VL)`: nothing has been measured yet.
3. Trade-off options. They may include design changes that need S1 rework.
4. Impact of each option.
5. Recommendation.

## Hard Rules

- Never invent or round a measurement.
- Never edit GT or `GT/build_package.md`.
- The agent recommends; **the author decides**. Record the decision verbatim and
  `Decided by: <name>`.
- Never write `PASS` without the author's answer.

## Report Contract

Write exactly one file: `.codeanvil/report/<cycle-name>/RFD.md`, append-only
(`## Iteration <N>`). Header: a `| Field | Value |` table with `Gate` = `RFD`, `Cycle`, `Created`
= `codeanvil now`. Iteration: a `| Field | Value |` table with `Date` = `codeanvil now`,
`Timestamp` = `codeanvil now --machine`, `Iteration`, `Cycle`, one verdict row written as
`| HITL | FEEDBACK |` or `| HITL | PASS |`, then `### Description`. RFD has no `Based on` line.

| Event | Row | Description |
|-------|-----|-------------|
| Raised | `HITL: FEEDBACK` | Links `RFD-NNN.md` and lists the open RFDs. The raising stage also wrote `Verdict: RFD`, so the cycle is suspended |
| Decided: deviation accepted | `HITL: PASS` once every RFD of the cycle is decided | Each choice verbatim, `Decided by: <name>` |
| Decided: **Withdrawn** | `HITL: PASS` | The author states the requirement is achievable. Add `Outcome: Withdrawn`. The raising stage's `Verdict: RFD` no longer binds: it returns to ordinary FEEDBACK and its rework route (S1) |

One report holds one verdict, so while any RFD of the cycle is open the iteration stays
FEEDBACK and lists which are open. The author's answer is binding: the agent never
overrides a decision or reopens a decided RFD.

## Re-entry

On the decided iteration (not Withdrawn):

1. Ask the author for the new cycle's name and normalise it as `AGENTS.md`, `## Cycle`,
   describes (lowercase, `_` for spaces, only letters, digits, `_` and `-`, zero-padded
   sequence prefix).
2. Set `cycle:` in `.codeanvil/project.yaml`. Update only that key.
3. Add the exact line `Superseded by cycle: <name>` to the Description. `codeanvil status`
   then shows the old cycle as closed. It stays read-only.
4. Return: "Update `GT/build_package.md`, then run the S0 skill."

## Output Contract

Return the RFD path, the options with the recommendation, the report path and iteration, and
the next step: the author's decision, or the S0 re-entry.

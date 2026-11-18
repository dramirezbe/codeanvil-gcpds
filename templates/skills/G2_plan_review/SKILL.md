---
name: g2-plan-review
description: "Trigger: G2. Review module plans against the six paper §9.1 checks; human verdict."
license: Apache-2.0
runtime: "codeanvil CLI on PATH"
metadata:
  gate: "G2"
  pipeline: "V-SIL"
---

# G2 — Plan micro-gate

## Prerequisite and Cycle

Resolve cycle; closed RFD cycles are read-only (`Cycle closed by RFD. Continue in cycle <name>.`).
Require latest S2 PASS, else `S2 must pass first. Run the S2 skill.`
If own latest FEEDBACK names the current S2 iteration and same scope, return `S2 must rework first.`
Run `codeanvil custody verify --cycle <cycle> --gate S2`; stale inputs stop without an iteration.
Read S2 Output lines and compare to current input digests: an edited plan is an open finding.

## Review

Read BACKLOG, SDD, SyRS, DELTAS and each `.codeanvil/plans/<SUB-xxx>/<module_id>/PLAN.md`
of S2's scope. For slice 0 read INFRA-PLAN.md; for system read INTEGRATION-PLAN.md.
Use references/G2_CHECKLIST.md. Fill one row per check per module, or infra/system scope:

| Check | Required evidence |
|-------|-------------------|
| G2.1 Completeness | Scope, criteria, tasks, test strategy and context set filled for every module; infra/system sections complete for their scope. |
| G2.2 Traceability | Each traced SYS exists in current SyRS, copied text and GT version match; each delta has a valid authority. |
| G2.3 Contract consistency | Consumes provided by earlier slice/base; provided contracts match SDD verbatim, including types and versions. |
| G2.4 Task ordering | Tasks respect module and base dependencies; no producer/consumer pair in the same slice. |
| G2.5 Verification feasibility | Data sources, vectors, oracle, declared HAL and target prerequisites support every VL/tolerance of this scope; module VL-1 tests are planned in their module slice, not deferred to system. |
| G2.6 Fresh-context sufficiency | For a module, every type/value/path resolves to PLAN.md or its Context set without full GT/SDD or other module source. For infra/system, the shared parent Context set explicitly names design/GT inputs and shared artifacts; module isolation does not apply to parent-owned integration. |

Present open findings, evidence, advisories and recommendation. Ask the human PASS / FEEDBACK
with free text, wait and record the answer verbatim plus `Decided by:`. Never infer approval
from continue. FEEDBACK must choose `plan defect` (+ `Modules:`), `design defect`, or `GT defect`;
ask when unspecified. Never offer RFD here.

| Human decision | Route |
|----------------|-------|
| PASS | S3, same scope |
| FEEDBACK — plan defect | S2, named modules only |
| FEEDBACK — design defect | S1 → G1 |
| FEEDBACK — GT defect | S0 triage → G0 |

## Report Contract

Append `.codeanvil/report/<cycle>/G2.md` with header Gate/Cycle/Document/Created,
`## Iteration <N>`, Date/Timestamp via codeanvil now, Iteration/Cycle and exactly one
`| HITL | PASS |` or `| HITL | FEEDBACK |` row. Description begins
`Based on: S2 iteration <N>`, then S2's `Scope:` and Input lines for SDD, BACKLOG and scope plans.
Include checklist, `Verdict:` on FEEDBACK, Modules, human answer and decider.
Every digest comes from `codeanvil custody digest`, pasted verbatim, checked with
`codeanvil custody verify`; never compute or type a hash.
Return findings, answer, report iteration and route. PASS: `G2 passed. Run the S3 skill.`

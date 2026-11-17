---
name: g2-plan-review
description: "Trigger: G2, plan review, slice plan review, module readiness. Review the S2 slice plan for completeness, dependencies, and infrastructure readiness before S3 implementation."
license: Apache-2.0
compatibility: "No scripts. Read-only checks of PLAN.md, BACKLOG.md, DELTAS.md. Writes only .codeanvil/report/<cycle-name>/G2.md."
metadata:
  author: "gcpds"
  version: "1.0"
  gate: "G2"
  pipeline: "V-SIL"
---

# G2 — Plan Review and Slice Readiness Check

G2 answers one question: **is this slice plan ready for S3 implementation?** The human answers it.
G2 runs no script and has no exit code: the agent validates by reading and reasoning; the human's answer sets
the verdict.

## Prerequisite and Cycle

Resolve the active cycle from `.codeanvil/project.yaml` (`cycle:`); if missing, ask the user.
If the latest iteration of `.codeanvil/report/<cycle-name>/RFD.md` holds a line
`Superseded by cycle: <name>`, this cycle is **closed** by an RFD and read-only: return exactly
`Cycle closed by RFD. Continue in cycle <name>.` and write nothing.

**Prerequisite: S2 PASS.**
If the latest iteration of `.codeanvil/report/<cycle-name>/S2.md` is not `HITL: PASS`,
stop and return exactly `S2 must pass first. Run the S2 skill.`

## Inputs

| Path | Role |
|------|------|
| `.codeanvil/plans/PLAN.md` | The current slice plan from S2 |
| `.codeanvil/plans/BACKLOG.md` | Master module inventory |
| `.codeanvil/plans/DELTAS.md` | Prior slice decisions (if applicable) |
| `.codeanvil/design/SDD.md` | The design document with module details |
| `.codeanvil/GT/SyRS.md` | System requirements |

## Output Contract

Return the findings (`open` first), the recommendation, the human's answer, the report path with
the iteration number, and the route.

**Report structure:**

The report includes:
- `Input: .codeanvil/plans/PLAN.md sha256:‹hash›` — hash of the input PLAN (use `codeanvil custody digest`)
- `Input: .codeanvil/plans/BACKLOG.md sha256:‹hash›` — hash of the BACKLOG
- Verdict line: `Verdict: plan approved`, `Verdict: plan defect`, or no verdict (defer to human)

## Checklist: 6 Module-Level Checks

The agent validates every module in the slice plan against these criteria. Mark each finding `open` or
`advisory`.

| Check | Validation | Marked `open` when |
|-------|------------|-------------------|
| **G2.1 Module present** | Each module in PLAN.md is listed in BACKLOG.md with matching 8-field values | A module appears in PLAN but not BACKLOG, or values differ |
| **G2.2 Dependency order** | PLAN.md modules are ordered by topological sort (no module depends on a later module) | A module depends on a contract produced by a later module in the slice, or cycle detected |
| **G2.3 VL-2 readiness** | Modules with `required_vl: VL-2` and `hw_dependency: true` have infrastructure planned (target, MCP, telemetry) | VL-2 module lacks target assignment or infrastructure plan in PLAN.md |
| **G2.4 Test entry** | PLAN.md names the test entry (`verification/run.sh vl0 \| vl1 \| vl2`) and it matches the VL floor of this slice | Test entry missing, or entry level disagrees with VL floor |
| **G2.5 Contract clarity** | Each module's `provides` outputs are consumed by later modules or by the system; `depends_on` inputs are available from prior slices or mocked | A contract is produced but never consumed, or a dependency cannot be satisfied (not in BACKLOG or not yet planned) |
| **G2.6 Slice boundary** | No module in this slice produces a contract required by a module in a later slice, unless that later module's plan is also ready (i.e., no dangling cross-slice dependency) | A later slice depends on this slice's output, but the later slice's PLAN is not yet written or its module is unready |

## Rework Routes

- **Plan defect:** S2 replans this slice (narrowed, expanded, or reordered) and re-enters at S2 `Verdict: plan defect`.
- **GT defect:** A missing contract or inconsistent requirement suggests S1 rework (e.g., SDD lacks a module, or traced_reqs is incomplete). Raise RFD.
- **Infra defect:** Infrastructure (Mock HAL, stubs, telemetry, CI) is unavailable. S2 documents the blocker in PLAN.md and either defers the slice (G2 FEEDBACK) or escalates (RFD).

## Decision Table

| Scenario | Verdict | Action |
|----------|---------|--------|
| All 6 checks pass, no open findings | plan approved | S3 proceeds with the slice |
| 1–2 minor findings, non-blocking | plan approved with advisory | S3 proceeds; advisories become S3 notes |
| VL-2 infrastructure unready, but VL-0/VL-1 is complete | plan approved for vl0/vl1 | S3 proceeds with available levels; G3 defers VL-2 |
| Module order violates DAG or module missing from BACKLOG | plan defect | S2 replans, re-enters at S2 `Verdict: plan defect` |
| Contract cannot be satisfied at all | GT defect | Raise RFD (missing module, mismatched requirement) |
| Infrastructure (Mock HAL, telemetry) is missing entirely | infra defect | S2 documents blocker; G2 defers or RFD escalates |

---

**Instructions:**

1. Read the entire PLAN.md, BACKLOG.md, and SDD §1.4 cards.
2. For each module in the PLAN, validate all 6 checks.
3. Report `open` findings first, then `advisory`.
4. Recommend PASS (plan approved) or FEEDBACK (plan defect / GT defect / infra defect).
5. Wait for the human's verdict. Only the human sets `HITL`.

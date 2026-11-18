---
name: s2-plan-modules
description: "Trigger: S2. Plan the next topological slice, one self-contained PLAN.md per module."
license: Apache-2.0
runtime: "codeanvil CLI on PATH"
metadata:
  gate: "S2"
  pipeline: "V-SIL"
---

# S2 — Module planning

## Prerequisite and Cycle

Resolve `cycle:` in `.codeanvil/project.yaml`; ask when missing. A cycle whose latest RFD
iteration says `Superseded by cycle: <name>` is read-only: return
`Cycle closed by RFD. Continue in cycle <name>.` and write nothing.
Require latest G1 `HITL: PASS`, else `G1 must pass first. Run the G1 skill.`
Run `codeanvil custody verify --cycle <cycle> --gate G1` and `codeanvil status`; a stale prerequisite
returns its `stale-report` reason and writes no iteration.
For slice k >= 1 require G3 PASS with `Scope: slice <k-1>`, else return
`G3 must pass slice <k-1> first. Run the G3 skill.` For system require the last backlog slice's
G3 PASS. Rework after G2/G3 plan defect changes only `Modules:` named by the feedback.

## Cadence and ownership

Run S2(k) → G2(k) → S3(k) → G3(k) for slice 0, module slices 1..n, then system.
S2 is the writer of `.codeanvil/plans/`; S0/S1 may update applied delta fields in delta-sync.
Never edit GT, SDD, `src/` or `verification/`. Risks remain in the plan; S2 never raises RFD.
Structural design changes produce `HITL: FEEDBACK` and `Verdict: design defect` → S1.
Minor changes with no contract version bump or stub impact are proposed `design-sync` deltas.

## Steps

1. Run `codeanvil backup S2`; on failure stop without an iteration.
2. First run: execute `codeanvil python templates/skills/S2_plan_modules/scripts/slice_backlog.py
   .codeanvil/design/SDD.md`. Kahn levels group independent modules; dependencies name modules,
   including cross-subsystem qualified IDs. Never put a producer and its consumer in one slice.
   HAL dependencies naturally come first; DSP and Decision share a slice only when independent.
   Write BACKLOG.md, INFRA-PLAN.md and DELTAS.md with the empty locked table (no invented rows).
   Scope is `slice 0`; INFRA-PLAN covers bases, kit, stubs and top-down placeholder integration.
3. Later runs: ingest each `Delta accepted: D-xxx` from G3 with its exact authority into DELTAS.md.
   Pending accepted GT/design-sync deltas stop planning with
   `Apply accepted deltas first: run S0|S1 in delta-sync.` Do not treat RFD as a delta acceptance.
4. For slice k write one `.codeanvil/plans/<SUB-xxx>/<module_id>/PLAN.md` per module, using
   references/PLAN.md. Copy relevant contracts verbatim with SDD headings; copy traced SYS text
   and GT version. Context set enumerates only required base APIs, kit and dependency stubs.
   Write scopes, allowed source/test/stub paths, tasks, expected outcomes and delta traceability.
5. Once module slices pass G3, write INTEGRATION-PLAN.md for `Scope: system`: cross-subsystem
   contract tests, PATH-* tests, §0.5 root command, URL, smoke and clean shutdown.
6. Update BACKLOG states from recorded S3/G3 evidence (planned, implemented, verified).
   Deliver the report and return `S2 complete. Run the G2 skill.`

## Report Contract

Append `.codeanvil/report/<cycle>/S2.md` with `## Iteration <N>`, header Gate/Cycle/Document/Created,
iteration Date/Timestamp from `codeanvil now` / `codeanvil now --machine`, Iteration/Cycle,
and exactly `| HITL | PASS |` for delivered plans (FEEDBACK for a structural design defect).
Description starts `Based on: G1 iteration <N>` then `Scope: slice <k>` or `Scope: system`.
Record Input lines for SDD and SyRS; cite prior G3 iteration/scope without hashing its
append-only report (later iterations change that file). Record Output lines for every plan written.
Every hash is produced by `codeanvil custody digest`, pasted verbatim; replace Input prefix with
Output for delivered artifacts. Never compute or type a digest. Check with `codeanvil custody verify`.
Return scope, modules, plan paths, risks and report iteration.

---
name: s2-plan-modules
description: "Trigger: S2. Plan the next topological slice, one self-contained PLAN.md per module."
license: Apache-2.0
runtime: "codeanvil CLI on PATH"
metadata:
  author: "gcpds"
  version: "1.1"
  gate: "S2"
  pipeline: "V-SIL"
---

# S2 — Module planning

## Prerequisite and Cycle

Resolve `cycle:` in `.codeanvil/project.yaml`; ask when missing. A cycle whose latest RFD
iteration says `Superseded by cycle: <name>` is read-only: return
`Cycle closed by RFD. Continue in cycle <name>.` and write nothing.
Before planning, process unrecorded G3 acceptances using **delta-intake** below, then resolve
accepted deltas through S0/G0 or S1/G1. This applies to G3 PASS and FEEDBACK alike.
Planning itself requires latest G1 `HITL: PASS`, else
`G1 must pass first. Run the G1 skill.` Run
`codeanvil custody verify --cycle <cycle> --gate G1` and `codeanvil status`;
a stale prerequisite returns its reason and writes no iteration.

For rework, the same parent agent reads the source G2/G3 iteration's `### Description`
for reasons, evidence and correction suggestions, then replans its named scope/modules.
Do not ask the user to repeat recorded feedback; missing authority/input still blocks.

Choose exactly one route:

| Route | Admission and scope |
|-------|---------------------|
| First delivery | No S2 iteration: `slice 0`, even though S1 covers the system. |
| Advance | Only after the latest G3 PASS for the current scope: plan k+1, or system when BACKLOG is complete. |
| G2/G3 plan-defect rework | Latest applicable FEEDBACK identifies `Modules:` and scope; replan only that scope and those modules. No PASS of the failing scope is required. |
| Design/GT rework | After S0/G0 or S1/G1 resolves the named defect, revalidate affected plans in the feedback's original scope before G2/S3/G3. Never restart at slice 0. |
| Sync-only system feedback | After accepted deltas are applied and G0/G1 review them, revalidate S2 for system, followed by G2/S3/G3. |

Only **advance** requires a preceding-slice G3 PASS. For k >= 1 inspect G3.md's full history,
select the latest iteration **with `Scope: slice <k-1>`**, and require its PASS. Do not use
an older PASS if a newer iteration of that same scope is FEEDBACK. For system use the final
module slice's latest scoped PASS. Missing advance prerequisite returns
`G3 must pass slice <k-1> first. Run the G3 skill.` Rework eligibility comes from the feedback,
not the latest global G3 verdict, which may describe the failed scope itself.

## Delta-intake (before planning prerequisites)

`S2 delta-intake` is a bounded ledger update, not a stage delivery. Read each completed G3
iteration's `Delta accepted: D-xxx` lines and its exact human authority and Before/After payload.
Include acceptances on FEEDBACK; ignore partial iterations, mere proposals and RFD decisions.
Run `codeanvil backup S2`, then materialize or update only those IDs in DELTAS.md. Preserve
already applied rows; repeated intake is idempotent. A conflicting payload or absent authority
stops with the exact problem, never guesses a change. A proposed row becomes accepted only
when the matching explicit human acceptance exists. Do not edit plans/BACKLOG or write S2.md.
This operation requires neither G1 freshness nor a G3 PASS; it cannot authorize implementation.
After intake, return `Apply accepted deltas first: run S0|S1 in delta-sync.`
S0/S1 applies them, G0/G1 reviews them, then S2 resumes the feedback's original scope.

## Cadence and ownership

Run S2(k) → G2(k) → S3(k) → G3(k) for slice 0, module slices 1..n, then system.
S2 is the writer of `.codeanvil/plans/`; S0/S1 may update applied delta fields in delta-sync.
Never edit GT, SDD, `src/` or `verification/`. Risks remain in the plan; S2 never raises RFD.
Structural design changes produce `HITL: FEEDBACK` and `Verdict: design defect` → S1.
Minor changes with no contract version bump or stub impact are proposed `design-sync` deltas.

## Execution continuity

Once authorized and admitted to a scope, continue through artifact creation, report publication
and custody checks in the same turn, or identify a concrete blocker. Status, backup, reading
templates and printing Kahn levels are preparation, not delivery. Follow
[S2 delivery and recovery](references/delivery.md). Resume existing drafts without repeating
successful backup or unchanged authorization; never create an internal human checkpoint.
Missing first-run plans are outputs to create, not missing prerequisites. Do not stop merely
because no plans exist yet, a directory listing reports absence, or the work is estimated large.
Respect explicit stop, real permission/tool/input failures, GT/design defects and scope gates.
PASS means delivered plans; only the human decides G2. Do not implement code or advance a slice.

## Steps

1. Run `codeanvil backup S2`; on failure (nonzero exit code) stop without an iteration.
   Exit 0 with `nothing to back up` or `already backed up` is success: continue planning.
2. First run: execute `codeanvil python templates/skills/S2_plan_modules/scripts/slice_backlog.py
   .codeanvil/design/SDD.md`. Kahn levels group independent modules; dependencies name modules,
   including cross-subsystem qualified IDs. Never put a producer and its consumer in one slice.
   HAL dependencies naturally come first; DSP and Decision share a slice only when independent.
   The script prints the module table; it does not write plans. Create the plans directory if
   absent. Write BACKLOG.md with those Kahn rows and INFRA-PLAN.md from its reference template.
   Only DELTAS.md starts with the empty locked table (no invented rows).
   Scope is `slice 0`; INFRA-PLAN covers bases, kit, stubs and top-down placeholder integration.
3. On later runs complete delta-intake first.
   Pending accepted GT/design-sync deltas stop planning with
   `Apply accepted deltas first: run S0|S1 in delta-sync.` Do not treat RFD as a delta acceptance.
4. For module slices k >= 1 write one `.codeanvil/plans/<SUB-xxx>/<module_id>/PLAN.md` per module, using
   references/PLAN.md. Copy relevant contracts verbatim with SDD headings; copy traced SYS text
   and GT version. Context set enumerates only required base APIs, kit and dependency stubs.
   Write scopes, allowed source/test/stub paths, tasks, expected outcomes and delta traceability.
5. For system scope only, once module slices pass G3, write INTEGRATION-PLAN.md for `Scope: system`: cross-subsystem
   contract tests, PATH-* tests, §0.5 root command, URL, smoke and clean shutdown.
6. Update BACKLOG states from recorded S3/G3 evidence (planned, implemented, verified),
   using scoped history: a new feedback reopens its affected rows, not unrelated verified modules.
   Complete the [delivery checks](references/delivery.md), publish the report, then run
   `codeanvil custody verify --cycle <cycle> --gate S2` and `codeanvil status`.
   Resolve delivery errors before claiming completion. Return `S2 complete. Run the G2 skill.`

## Report Contract

Append `.codeanvil/report/<cycle>/S2.md` with `## Iteration <N>`, header Gate/Cycle/Document/Created,
iteration Date/Timestamp from `codeanvil now` / `codeanvil now --machine`, Iteration/Cycle,
and exactly `| HITL | PASS |` for delivered plans (FEEDBACK for a structural design defect).
Description starts `Based on: G1 iteration <N>` then `Scope: slice <k>` or `Scope: system`.
Record Input lines for SDD and SyRS; cite prior G3 iteration/scope without hashing its
append-only report (later iterations change that file). Record Output lines for every plan written.
Every hash is produced by `codeanvil custody digest`, pasted verbatim; replace Input prefix with
Output for delivered artifacts. Never compute or type a digest, concatenate digests or shorten them.
Missing SDD/SyRS Input lines and malformed Input/Output declarations invalidate delivery.
Correct an existing report by appending a checked iteration, never rewriting historical bytes
or treating the correction as G2 approval. Check with `codeanvil custody verify`.
Return scope, modules, plan paths, risks and report iteration.

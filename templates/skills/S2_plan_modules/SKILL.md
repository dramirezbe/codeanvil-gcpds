---
name: s2-plan-modules
description: "Trigger: S2, module slicing, planning, decomposition, delivery cadence. From a G1-passed design, plan the per-module implementation cadence, produce plans for each slice, and prepare deltas for S3."
license: Apache-2.0
compatibility: "No network access, no scripts. Reads .codeanvil/GT/SyRS.md, .codeanvil/design/SDD.md and .codeanvil/project.yaml. Writes .codeanvil/plans/ (BACKLOG.md, PLAN.md, INFRA-PLAN.md, INTEGRATION-PLAN.md, DELTAS.md) and .codeanvil/report/<cycle-name>/S2.md."
metadata:
  author: "gcpds"
  version: "1.0"
  gate: "S2"
  pipeline: "V-SIL"
---

# S2 — Plan Module Slices and Deliverables

From the G1-approved design, produce a module-slicing plan that sequences implementation into
per-module S3 passes, each with bounded scope, clear contracts, and measurable deltas. No code is
written here: S2 is planning only. S3 implements each slice in sequence, then S2 produces the next slice
plan. The loop S2→S3→G3→S2 continues until all modules are delivered.

## Prerequisite and Cycle

Resolve the active cycle from `.codeanvil/project.yaml` (`cycle:`); if missing, ask the user.
If the latest iteration of `.codeanvil/report/<cycle-name>/RFD.md` holds a line
`Superseded by cycle: <name>`, this cycle is **closed** by an RFD and read-only: return exactly
`Cycle closed by RFD. Continue in cycle <name>.` and write nothing.

**Prerequisite: G1 PASS.**
If the latest iteration of `.codeanvil/report/<cycle-name>/G1.md` is not `HITL: PASS`,
stop and return exactly `G1 must pass first. Run the G1 skill.`

**Fresh slice cadence:**
S2 runs twice per cycle: once at cycle entry (C1 — first slice after G1 PASS), and once per slice
completion (C2+, after G3 PASS on the previous slice). On C1, produce the first slice plan. On C2+, check
the latest `G3.md` iteration for `Verdict: module defect` (re-plan this slice in S2 / re-run S3) or
`Verdict: slice complete` (plan the next slice).

## Inputs

| Path | Role |
|------|------|
| `.codeanvil/GT/SyRS.md` | System requirements and measurement framework |
| `.codeanvil/design/SDD.md` | The G1-passed design document with 8-field module cards and dependency graph |
| `.codeanvil/project.yaml` | Project identity and cycle |
| `.codeanvil/plans/BACKLOG.md` | Master list of all modules and their dependencies (written once on C1) |
| `.codeanvil/plans/DELTAS.md` | Accepted deltas from prior slices (C2+) |

## Output Contract

Return the slice identifier (e.g., `slice-01-acq`, `slice-02-calibration`), the module list, the
plan paths, the report path with the iteration number, and the next step (`S2 complete. Run the S3 skill.`).

**Report structure:**

The report includes:
- `Scope: slice <N>` — which modules this slice covers
- `Input: .codeanvil/design/SDD.md sha256:‹hash›` — hash of the input SDD (use `codeanvil custody digest`)
- `Input: .codeanvil/GT/SyRS.md sha256:‹hash›` — hash of the input SyRS
- For C2+: `Input: .codeanvil/report/<cycle>/<G3>.md sha256:‹hash›` — hash of the G3 report from the prior slice

## Planning Rules

1. **Topological sort of modules** (§1.4 cards): S2 computes a valid compile/test order using the
   `depends_on` edges (intra-subsystem) and verifies no cycles.

2. **Slice boundaries are determined by:**
   - **HAL-first:** slice-01 contains only HAL modules (layer = "HAL")
   - **DSP-then-Decision:** slice-02 contains DSP and Decision modules that depend only on slice-01 HAL outputs
   - **Later slices:** Control, Output, other layers in dependency order
   - **Per-subsystem independence:** modules from independent subsystems may run in parallel within a slice

3. **Slice content rules:**
   - Each slice is **minimal independent unit**: a module enters the slice only when all its dependencies
     are satisfied (from prior slices or the existing codebase)
   - **VL constraints honored:** a module with `required_vl: VL-2` and `hw_dependency: true` cannot be
     implemented until S3's target preparation is complete (documented in the PLAN.md)
   - **Contract-driven:** each module's `provides` outputs are available to later slices immediately after
     its S3 pass (mocked during prior slices if needed)

4. **Delta rules** (from G3 FEEDBACK on a prior slice):
   - A `module defect` delta: S2 re-examines that module only; re-enter S3 with a narrowed slice
   - A `slice complete` delta: archive the slice's plan and move to slice N+1
   - Deltas accepted by the Build Package author (via RFD) are recorded in DELTAS.md and shape the next S0 → S1 rework

## Plan Document Templates

### BACKLOG.md

Master module inventory: all modules from SDD §1.4, organized by subsystem and dependency. Written once on
the first S2 run (C1).

```markdown
# Module Backlog

| Subsystem | Module ID | Layer | Depends On | Provides | HW Dep | Required VL | Status |
|-----------|-----------|-------|-----------|----------|--------|-------------|--------|
| SUB-001 | acq | HAL | HW-IQ-001 | INT-IQ-001 | true | VL-2 | slice-01 |
| SUB-001 | estimator | DSP | INT-IQ-001 | INT-PWR-001 | false | VL-1 | slice-02 |
...
```

### PLAN.md

The current slice plan: modules to be implemented, build order, test entry points, expected outputs.
One PLAN.md per slice; prior plans are archived as `PLAN-slice-NN.md`.

```markdown
# Slice 01 Plan

| Field | Value |
|-------|-------|
| Modules | acq (SUB-001), acquisition_counters (SUB-001 internal) |
| VL floor | VL-0 (Mock HAL) + VL-1 (golden vectors) + VL-2 (real HackRF) |
| Build order | acq → (mocked to allow estimator test without acq) |
| Test entry | verification/run.sh vl0 (mock), vl1 (golden), vl2 (real HW) |
| Expected outputs | INT-IQ-001 (IQ samples), INT-ACQ-001 (counters) |
| Telemetry | codeanvil telemetry captures HW access metrics |
...
```

### INFRA-PLAN.md

Shared infrastructure needed across all slices: Mock HAL, stubs, telemetry, CI/CD, environment setup.
Written once; updated if infrastructure changes are discovered.

```markdown
# Infrastructure Plan

| Component | Responsibility | Status |
|-----------|----------------|--------|
| Mock HAL | src/mock_hal/ provides FakeHackRF, FakeSupervisor, etc. | — |
| Telemetry | codeanvil telemetry + verification/logger.py/.ts | — |
| CI gates | verification/run.sh vl0/vl1 (local); vsil_hil_mcp for vl2 | — |
...
```

### INTEGRATION-PLAN.md

Cross-module contracts and integration points: how outputs of one slice become inputs to the next.
Updated per slice as contracts are refined.

```markdown
# Integration Contracts

| Contract | Producer (Module) | Consumer (Module) | Mode | Status |
|----------|-------------------|-------------------|------|--------|
| INT-IQ-001 | acq (slice-01) | estimator (slice-02) | Direct link or mock | — |
| INT-PWR-001 | estimator (slice-02) | detector (slice-02) | Direct link | — |
...
```

### DELTAS.md

Accepted deviations from the planned slicing: re-plans after G3 FEEDBACK or RFD-approved requirement changes.

```markdown
# Slice Deltas

## Slice 01

| Issue | Verdict | Action | Author | Date |
|-------|---------|--------|--------|------|
| acq timeout on first scan | module defect | Re-plan acq into slice-01b | G3 2026-11-20 | — |
| HACKRF clock drift exceeds spec | GT defect → RFD | — | S3 2026-11-19 | 2026-11-20 |

## RFD-Accepted Changes

- SYS-ACQ-001 tolerance adjusted from ±20 ppm to ±50 ppm (accepted 2026-11-20)
- New module SUB-007/compensator planned for slice-05 (accepted 2026-11-20)
...
```

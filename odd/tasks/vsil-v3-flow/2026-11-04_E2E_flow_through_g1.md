# Plan — E2E: run the flow through G1 on a real input

Feature: `odd/tasks/2026-11-04_1042_vsil_v3_skill_flow.md` · Task T7 · Spec S2
Target: replace the G0 → custody → G1 prompts in `methodology/test/README.md` (sections "5. Test prompts" and the checklist at lines 332-346). Extended to S2 and G2 when T8 and T9 exist.

## Goal

Prove the planned part of the flow works with the existing tools, in a clean project, on any runtime that `codeanvil sandbox` supports.

## Procedure

```bash
codeanvil create --name "FM Spectrogram" -p "$(mktemp -d)"
cd <created-folder>
cp <repo>/templates/no-tools-skills/v3/test-inputs/build_package.md GT/
codeanvil sandbox claude    # or pi, opencode, codex
```

| # | Prompt | Expected |
|---|--------|----------|
| 1 | "Check context" | Runs `codeanvil status`, asks for a cycle, table shows S0 → G0 → S1 → G1 and RFD with `-` |
| 2 | "Run G1" before anything else | Refuses: `S1 must pass first. Run the S1 skill.` Writes nothing |
| 3 | "Run S0" | One pass, no prompts; writes the pair and `S0.md` |
| 4 | "Run G0" | Exit 0, asks Gate H; PASS records Gate H |
| 5 | "Run S1" | Writes `S1_artifacts/S1_design.md`, with GT digests in Meta, and `S1_artifacts/S1_graph.html` with spiders and manifest text; `S1.md` PASS names the graph's path |
| 6 | "Run G1" | Filled checklist with findings and a recommendation, digest match shown; agent waits, then human answers PASS |

Expected `codeanvil status`, after T10:

```
Cycles:
  01_fm (active)
    S0: delivered (iteration 1)
    G0: PASS (iteration 1)
    S1: delivered (iteration 1)
    G1: PASS (iteration 1)
```

## FAIL paths

| Case | How | Expected |
|------|-----|----------|
| G0 FAIL → S0 | Remove Part B from `build_package.md` | Placeholders, exit 1, `G0: FEEDBACK`; S0 reports "needs Build Package content" |
| Gate H refused | Answer FEEDBACK with `STK-SPEC-002: …` | Reason stored verbatim; S0 re-entry reads it |
| GT edited after S1 | Change one byte, run G1 | Digest mismatch shown to the human; nothing blocks |
| G1 FEEDBACK → S1 | Remove a stub recipe in the design | Finding marked `open`; human answers FEEDBACK; S1 re-run reads it |
| Reports drive the chain | Delete `S1_graph.html`, run G1 | Prerequisite still passes from `S1.md`; finding marked `advisory` |
| Rework routed from reports | Answer FEEDBACK at G1, run G1 again without S1 | `S1 must rework first. Run the S1 skill.`; no iteration written |
| Stale PASS | After G1 PASS, re-run S1 and check `codeanvil status` | `G1: PASS (iteration 1) [stale: based on S1 iteration 1, S1 is at 2]`; G1 runs again |
| RFD closes the cycle | Answer RFD at G1, decide it, name a new cycle | Old cycle shows `(closed: superseded by <name>)`; re-running G1 before the decision returns `Cycle suspended by RFD. Run the RFD skill.` |
| Skill folder self-contained | Disconnect from the network, open `S1_graph.html` | Graph renders from the skill's `assets/` |
| Graph differs from design | Remove a module from the graph's `DATA`, run G1 | Finding marked `open`; on FEEDBACK, S1 rewrites the graph |
| Runtime loop | Two-service design with telemetry and control | Not reported as a dependency cycle in G1.1; reviewed under G1.9 |
| RFD from S1 | Dry run on the 20 MS/s pressure point in `test-inputs/README.md` | With analysis only: risk in §6 or an RFD with `ANALYSIS (no VL)`; measured evidence comes at G2 |

## Pressure points to check in the S1 design

From `test-inputs/README.md`: the DC spike (`SYS-PSD-002`) appears in §6, and the baseband filter (`SYS-ACQ-001`) appears as a HAL contract.

## Acceptance

Every row observed and recorded in the feature Log, with the runtime used. Anything not run is listed as not run. Scratch folder removed afterwards.

## Not covered

Anything after G1. The flow is **not** "ready to use" end to end until T8 and T9 are done, and this plan must not claim otherwise.

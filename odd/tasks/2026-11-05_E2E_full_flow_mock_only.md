# Plan — T8: end-to-end run, FM edge + dashboard, `mock-only`

Feature: `odd/tasks/2026-11-05_1421_vsil_v3_full_flow.md` · Task T8 · Specs S5, S8, S10
Target: `methodology/test/README.md` (procedure) and a new test case folder `methodology/test/T3_FM-mock/` holding only the Build Package. Supersedes the agent run of `2026-11-04_E2E_flow_through_g1.md`, which was never performed.

## Goal

Prove the flow is usable from S0 to G2 with an agent, on the scenario of S8: SDR → Raspberry Pi, a small user dashboard, validation up to VL-1 with the Mock HAL, no real hardware. The ML model for spectral localisation is left out (S10): its requirement stays in the Build Package as future work, so the design has no §1.5.

## Fixture

`T3_FM-mock/build_package.md`: PRD, COTS envelope (SDR model and Raspberry Pi as `HWC-*`), acceptance criteria with a channel-occupancy metric and a latency budget. No lab section, so S0 writes `Lab inputs: none`.

## Procedure

Run in `codeanvil sandbox <agent>` on a scratch project made with `codeanvil create` in a `mktemp -d` folder.

| Step | Prompt | Expect |
|------|--------|--------|
| 1 | Run S0, then G0 | GT pair passes `g0_validate.py`; human Gate H |
| 2 | Run S1 | `HAL mode: mock-only`; §1.3.4, §1.6, §1.7 filled; no §1.5; no `hw_dependency: true` |
| 3 | Run G1, answer PASS | Checklist with G1.11–G1.13 and the kit row |
| 4 | Run S2 | Kit and base first, then modules and paths; VL-0 suite green with telemetry |
| 5 | Run G2, declare VL-1 for DSP and the edge → UI path | G2.0 and G2.1 run; a VL-2 request is refused; `verified_prototype.md` written on PASS |
| 6 | `codeanvil status` | S0–S2 `delivered`, G0–G2 `PASS` |

Failure probes: add a §1.5 to the design before S2 (expect the exact FW-ML-3 stop and no iteration); remove a contract field before S2 (expect a design-defect iteration and an S1 rework); force a module bug before G2 (expect `Verdict: module defect` routed to S2).

Recommended, not required: run step 5 on the Raspberry Pi so the telemetry companion records the real compute unit.

## Acceptance

Each row's expectation observed and recorded in the feature document's Log, with the agent runtime used. A failing step reopens the task of the skill that failed (S4: rewrite that skill rather than patch around it).

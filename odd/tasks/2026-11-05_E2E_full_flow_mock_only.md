# Plan — T8: end-to-end run, FM edge + dashboard, `mock-only`

Feature: `odd/tasks/2026-11-05_1421_vsil_v3_full_flow.md` · Task T8 · Specs S5, S8, S10, S11, S12, S13
Target: `methodology/test/README.md` (procedure) and a new test case folder `methodology/test/T3_FM-mock/` holding only the Build Package. Supersedes the agent run of `2026-11-04_E2E_flow_through_g1.md`, which was never performed.

## Goal

Prove the flow is usable from S0 to G2 with an agent, on the scenario of S8: SDR → Raspberry Pi, a small user dashboard, validation up to VL-1 with the Mock HAL, no real hardware. The ML model for spectral localisation is left out (S10): its requirement stays in the Build Package as future work, so the design has no §1.5.

## Fixture

`T3_FM-mock/build_package.md`: PRD, COTS envelope (SDR model and Raspberry Pi as `HWC-*`), acceptance criteria with a channel-occupancy metric and a latency budget. No lab section, so S0 writes `Not applicable: no lab inputs in the Build Package.` under SyRS §4, §5 and §6 (D9).

## Procedure

Run in `codeanvil sandbox <agent>` on a scratch project made with `codeanvil create` in a `mktemp -d` folder.

| Step | Prompt | Expect |
|------|--------|--------|
| 1 | Run S0, then G0 | SyRS §4–§6 hold the "not applicable" line; GT pair passes `g0_validate.py`; human Gate H |
| 2 | Run S1 | `HAL mode: mock-only`; `Toolchain` per service (edge and dashboard); §1.3.4 with D2 paths, §1.6, §1.7 filled; no §1.5; no `hw_dependency: true` |
| 3 | Run G1, answer PASS | Checklist with G1.11–G1.13 and the kit row (incl. `Toolchain`); returns `G1 passed. Run the S2 skill.` |
| 4 | Run S2 | D2 tree: `src/fm_edge/` (Python, `__main__.py`) and `src/dashboard/` (TS), `pyproject.toml` + `uv.lock`, `package.json` + `pnpm-workspace.yaml` + `pnpm-lock.yaml`, `verification/` with `run.sh`, `golden/`, `telemetry/`, `fm_edge/`, `dashboard/`; kit and base first, then modules, paths and VL-1 tests; `verification/run.sh vl0` green with telemetry; `test_run.md` has the two `run.sh` commands; `grep -r codeanvil src/` is empty; edge logs show `[YYYY-MM-DD HH:MM:SS.mmm] LEVEL name.funcName message` in colour; `uv sync --frozen --no-dev && uv run fm_edge` starts without kit dependencies |
| 5 | Run G2, declare VL-1 for DSP and the edge → UI path | Runs delegated to `vsil-verifier` (Claude Code, OpenCode); source tree unchanged after them; only the `test_run.md` commands run; a VL-2 request is refused; `verified_prototype.md` written on PASS |
| 6 | `codeanvil status` | S0–S2 `delivered`, G0–G2 `PASS` |

Failure probes: add a §1.5 to the design before S2 (expect the exact FW-ML-3 stop and no iteration); remove a contract field before S2 (expect a design-defect iteration and an S1 rework); force a module bug before G2 (expect `Verdict: module defect` routed to S2); delete one VL-1 test before G2 (expect `Verdict: module defect`, G2 writes no test); re-run G2 after that FEEDBACK without re-running S2 (expect `S2 must rework first. Run the S2 skill.`); interrupt S2 mid-module and re-run it (expect finished modules kept); run G2 in Pi or Copilot (expect the fresh-session request and no runs).

Recommended, not required: run step 5 on the Raspberry Pi so the telemetry companion records the real compute unit.

## Acceptance

Each row's expectation observed and recorded in the feature document's Log, with the agent runtime used. A failing step reopens the task of the skill that failed (S4: rewrite that skill rather than patch around it).

### First-run closure decision (2026-11-05)

The OpenCode run completed the six-step chain, including one real G2 design-defect FEEDBACK loop
back through S1, G1 and S2. The first generated package entry point only logged instructions;
the archived copy now starts a runtime Mock HAL and the two-service `run-demo` launcher has a
working WebSocket smoke test. The exact evidence is in the feature plan L18 and
`methodology/test/T3_FM-mock/S1_G1_review_holdout_2026-11-05.md`. The user asked to close this
first realistic run with that entry-point correction. The failure probes above were not all
performed; keep them as an explicit future regression matrix, never count them as observed PASS.

# Plan — T6: S2 implements the services (one skill)

Feature: `odd/tasks/2026-11-05_1421_vsil_v3_full_flow.md` · Task T6 · Specs S2, S3, S4, S7, S10 · Contracts C0–C11, D1–D6 · Assumption A3
Target: `templates/skills/S2_implement_services/SKILL.md` (about 110 lines), no script, no template. Paper §7.
Replaces the three 2026-11-01 plans (`S2-1`, `S2-2`, and the S2 half of `S2-3`), which targeted chat-only skills.

## Goal

Turn the G1-approved design into running code plus the verification kit, and prove the VL-0 floor. S2 is a **stage** (C4): its `PASS` means "delivered with VL-0 evidence"; the human verdict belongs to G2. The agent runs every test itself: the Mock HAL and the kit exist so it can, without hardware or a human in the loop (C9).

## Prerequisite (C2)

`G1.md` latest iteration `HITL: PASS`, nothing stale. Messages: `G1 must pass first. Run the G1 skill.`, and on an own unreworked design defect `S1 must rework first. Run the S1 skill.` Description starts with `Based on: G1 iteration <N>` (C11).

## Inputs and outputs

| | Path |
|---|------|
| Input | `S1_artifacts/S1_design.md` (read-only), `GT/G0_SyRS.md` for thresholds |
| Output | `app/` delivered software, `verification/` kit (D2) |
| Output | `.codeanvil/report/<cycle-name>/S2_artifacts/test_run.md`: last command, counts, environment, telemetry summary |
| Output | `.codeanvil/report/<cycle-name>/S2.md` |

## Steps

1. **Initial layer (S3).** Build every tool of design §1.3.4 before any module: Mock HAL, golden vectors with `verification/golden/manifest.md` (D4), telemetry companion (D3), one stub or fake peer per contract, drivers, and the Real HW HAL with a fake device API only in `mock+real`. Then the base layer in `app/`. Run base unit tests and the **top-down** test (base + all stubs) with the telemetry companion recording.
2. **ML (loose end, S10).** If design §1.5 exists, stop before any code with exactly `ML integration is future work. Remove design §1.5 for this round.` and write no iteration (FW-ML-3).
3. **Modules in DAG order (§2.2).** Per module: implement against its contract, unit test, **bottom-up** test with a driver through the base, replace its stub.
4. **Services and paths.** Producer and consumer contract tests with fake peers, then each `PATH-*` with the real service processes and Mock HAL input.
5. **Floor run.** One command runs the whole VL-0 suite with the telemetry companion attached. Write `test_run.md`.
6. Write the iteration and return `S2 complete. Run the G2 skill.`

## Hard rules

- Implement only what the design declares. A missing interface, an undeclared dependency or an incomplete contract is a **design defect** (D6): write `| HITL | FEEDBACK |` with `Verdict: design defect` and the sections, then stop.
- A requirement that no implementation can meet on the declared COTS platform: run the RFD skill, as S1 does.
- Expected values come from §3 vectors and the golden manifest, never computed by the agent.
- Nothing under `verification/` is imported by `app/`. The telemetry companion is never in `app/` (S2).
- In `mock+real`, the Real HW HAL's VL-0 tests use the fake device API; S2 never needs the hardware (S7).
- Report only results of runs that actually happened, with their command.
- Rework: a G2 iteration with `Verdict: module defect` names the modules to fix; redo step 3 for them, then step 5.

## RED tests first

Through `_skill_text("S2_implement_services")`: `G1 must pass first. Run the G1 skill.`, `Based on: G1 iteration`, `Verdict: design defect`, `verification/golden/manifest.md`, `ML integration is future work. Remove design §1.5 for this round.`, `Verdict: module defect` (accepted as rework) and `S2 complete. Run the G2 skill.`.

## Acceptance

1. Kit and base exist before the first module commit-sized step (T8).
2. `test_run.md` shows the full VL-0 suite with telemetry readings attached.
3. A forced contract gap produces a design-defect iteration and S1 accepts it (T8).

# Plan — T7: G2 adaptive verification and the Verified Prototype (one skill)

Feature: `odd/tasks/2026-11-05_1421_vsil_v3_full_flow.md` · Task T7 · Specs S1, S2, S4, S7, S10, S11, S13 · Contracts C0–C11, D1–D11 · Depends on T9 (the subagent file)
Target: `templates/skills/G2_adaptive_verification/` with `SKILL.md` (about 110 lines) and `references/verified_prototype.md` (the output template). No script. Paper §8, §9.2, §10.
Replaces the G2 half of `2026-11-01_S2-3_g2_adaptive_verification.md`.

## Goal

A human gate (C6, P1): the agent **runs** the evidence at the declared levels, never writes tests, and drafts the honesty declaration; the human answers. On PASS, the cycle's terminal output is written.

## Prerequisite (C2)

Resolve the cycle from `.codeanvil/project.yaml`. Check, in this order, writing **no iteration** when you stop (same wording as G1):

1. Latest `RFD.md` iteration holds `Superseded by cycle: <name>`: return exactly `Cycle closed by RFD. Continue in cycle <name>.`
2. `S2.md` missing or its latest iteration is not `HITL: PASS`, or `codeanvil status` marks S2 or an earlier report `stale`: return exactly `S2 must pass first. Run the S2 skill.`
3. G2's own latest iteration is `FEEDBACK`. With `Verdict: RFD`, return exactly `Cycle suspended by RFD. Run the RFD skill.`, unless the latest `RFD.md` iteration states `Outcome: Withdrawn`. Otherwise, if its `Based on` line names the current latest S2 iteration, the code was not reworked: return exactly `S2 must rework first. Run the S2 skill.` Unchanged code is never verified twice.

The Description starts with `Based on: S2 iteration <N>` (C11). Never reuse S2's results, always re-run.

## Who runs what (D11)

Steps 2–5 are delegated to the **`vsil-verifier` subagent** (T9): a fresh context that did not write the code, cannot edit files, and returns one results table. G2 passes it the cycle name and the declared levels, and nothing from S2's conversation. G2 itself declares levels, presents, asks the human and writes the report. When the runtime has no `vsil-verifier` subagent, G2 says so and asks the user to run G2 in a fresh session; it does not run steps 2–5 in the session that ran S2.

## Steps

1. **Declare levels.** Show each module and `PATH-*` with its `required_vl`. The human declares the level for this cycle (default VL-0). Refuse VL-2 in `mock-only` (D5).
2. **G2.0 (always, subagent).** Fresh run of the `VL-0` command from `S2_artifacts/test_run.md`, with the telemetry companion.
3. **G2.1 (VL-1 declared, subagent).** Run the `VL-1` command from `test_run.md` (D8): Mock HAL synthetic inputs per §1.6, metrics against `SYS-*` thresholds from `G0_SyRS.md`. Nobody in G2 writes or edits a test: a declared VL-1 module or path with no VL-1 test is a **module defect** routed to S2. No model is measured this round (S10, FW-ML-4).
4. **G2.2 (VL-2 declared, `mock+real` only).** The SyRS §6 `PROTO-*` procedures cited by design §1.6, on the Real HW HAL, with the §4 correction chains and §5 tolerances (D9). The subagent prepares the procedure; if no hardware is reachable from the session, the human runs it and pastes the measurements.
5. **Telemetry check (subagent).** Flag every result produced outside the operating envelope of design §1.7.
6. **Infeasibility.** Show every `Possible infeasibility` entry from `test_run.md` next to the G2 result that confirms or refutes it (paper §9.2). When the defect-or-RFD test points to RFD, the recommendation names it.
7. **Present** a table per module and path (declared level, environment, result, telemetry flag) and the draft honesty declaration. Ask **PASS**, **FEEDBACK** or **RFD**.

| Human answer | Report | Route |
|--------------|--------|-------|
| PASS | `HITL: PASS` + `G2_artifacts/verified_prototype.md` | Done |
| FEEDBACK, module defect | `HITL: FEEDBACK` + `Verdict: module defect` + modules (including missing VL-1 tests) | S2 |
| FEEDBACK, design defect | `HITL: FEEDBACK` + `Verdict: design defect` + sections (D6) | S1 |
| RFD | `HITL: FEEDBACK` + `Verdict: RFD` | RFD skill, with the G2 report as evidence |

S2 accepts `Verdict: module defect` as its rework request (one line in the T6 skill).

## `references/verified_prototype.md`

Sections, from paper §10: cycle, HAL mode, toolchain, module evidence, path evidence, telemetry report, honesty declaration (VERIFIED for VL-0/VL-1, VALIDATED only for VL-2), delivered tree (`src/<service>/`) versus kit `verification/` (D2), verifier (`vsil-verifier` subagent or fresh session), RFDs issued, optional future work register.

## RED tests first

Through `_skill_text("G2_adaptive_verification")`: `Cycle closed by RFD. Continue in cycle`, `Cycle suspended by RFD. Run the RFD skill.`, `S2 must pass first. Run the S2 skill.`, `S2 must rework first. Run the S2 skill.`, `Based on: S2 iteration`, `vsil-verifier`, `fresh session`, `test_run.md`, `PROTO-`, `Possible infeasibility`, `Verdict: module defect`, `Verdict: design defect`, `verified_prototype.md`, `mock-only` and `VALIDATED`.

## Acceptance

1. G2 never writes `HITL` before the human answers.
2. In `mock-only`, a VL-2 declaration is refused and the declaration says no real-hardware claim (T8).
3. A result outside the telemetry envelope is shown flagged, never silently accepted.
4. G2 runs only the commands of `test_run.md`; a VL-1 declaration without a VL-1 test becomes `Verdict: module defect` (T8).
5. Re-running G2 after a FEEDBACK with no new S2 iteration returns `S2 must rework first. Run the S2 skill.`
6. On a runtime with the subagent, steps 2–5 run in `vsil-verifier` and the source tree is unchanged after them; without it, G2 asks for a fresh session and runs nothing (T8).

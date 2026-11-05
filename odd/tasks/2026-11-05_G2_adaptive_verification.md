# Plan — T7: G2 adaptive verification and the Verified Prototype (one skill)

Feature: `odd/tasks/2026-11-05_1421_vsil_v3_full_flow.md` · Task T7 · Specs S1, S2, S4, S7, S10 · Contracts C0–C11, D1–D6 · Assumptions A3, A4
Target: `templates/skills/G2_adaptive_verification/` with `SKILL.md` (about 100 lines) and `references/verified_prototype.md` (the output template). No script. Paper §8, §10.
Replaces the G2 half of `2026-11-01_S2-3_g2_adaptive_verification.md`.

## Goal

A human gate (C6, P1): the agent re-runs the evidence at the declared levels and drafts the honesty declaration; the human answers. On PASS, the cycle's terminal output is written.

## Prerequisite (C2)

`S2.md` latest iteration `HITL: PASS`, nothing stale. Description starts with `Based on: S2 iteration <N>` (C11). A4: recommend a fresh agent session; never reuse S2's results, always re-run.

## Steps

1. **Declare levels.** Show each module and `PATH-*` with its `required_vl`. The human declares the level for this cycle (default VL-0). Refuse VL-2 in `mock-only` (D5).
2. **G2.0 (always).** Fresh run of the full VL-0 suite with the telemetry companion.
3. **G2.1 (VL-1 declared).** Mock HAL synthetic inputs per §1.6; metrics against `SYS-*` thresholds from `G0_SyRS.md`. No model is measured this round (S10, FW-ML-4).
4. **G2.2 (VL-2 declared, `mock+real` only).** The Build Package lab procedures on the Real HW HAL. The agent prepares the procedure; if no hardware is reachable from the session, the human runs it and pastes the measurements.
5. **Telemetry check.** Flag every result produced outside the operating envelope of design §1.7.
6. **Present** a table per module and path (declared level, environment, result, telemetry flag) and the draft honesty declaration. Ask **PASS**, **FEEDBACK** or **RFD**.

| Human answer | Report | Route |
|--------------|--------|-------|
| PASS | `HITL: PASS` + `G2_artifacts/verified_prototype.md` | Done |
| FEEDBACK, module defect | `HITL: FEEDBACK` + `Verdict: module defect` + modules | S2 |
| FEEDBACK, design defect | `HITL: FEEDBACK` + `Verdict: design defect` + sections (D6) | S1 |
| RFD | `HITL: FEEDBACK` + `Verdict: RFD` | RFD skill |

S2 accepts `Verdict: module defect` as its rework request (one line in the T6 skill).

## `references/verified_prototype.md`

Sections, from paper §10: cycle, HAL mode, module evidence, path evidence, telemetry report, honesty declaration (VERIFIED for VL-0/VL-1, VALIDATED only for VL-2), delivered tree `app/` versus kit `verification/` (A3), RFDs issued, optional future work register.

## RED tests first

Through `_skill_text("G2_adaptive_verification")`: `S2 must pass first. Run the S2 skill.`, `Based on: S2 iteration`, `Verdict: module defect`, `Verdict: design defect`, `verified_prototype.md`, `mock-only`, and `VALIDATED`.

## Acceptance

1. G2 never writes `HITL` before the human answers.
2. In `mock-only`, a VL-2 declaration is refused and the declaration says no real-hardware claim (T8).
3. A result outside the telemetry envelope is shown flagged, never silently accepted.

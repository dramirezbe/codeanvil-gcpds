# Plan — T2: S0 casts lab inputs into the SyRS as optional content

Feature: `odd/tasks/2026-11-05_1421_vsil_v3_full_flow.md` · Task T2 · Specs S1, S4, S11 · Contract D9
Targets: `templates/skills/S0_normalise_build_package/SKILL.md` (a few lines) and the locked blueprint `templates/GT/G0_SyRS.md` (the copies inside the S0 and G0 skills come from it on scaffold). `g0_validate.py` and `RULES.md` do not change.

## Goal

The Build Package may carry laboratory procedures, calibration and tolerances. They serve only the Real HW HAL, which is optional (S1). The SyRS already has a section for each, and G0 only requires their headings (`g0_validate.py:68-70`). S0 puts them there (S11); a Build Package without them leaves a fixed "not applicable" line, so G0 still passes.

| Build Package content | SyRS section |
|-----------------------|--------------|
| Laboratory procedures (setup, calibration step, execution) | §6 Field Measurement Protocols, one `PROTO-NNN` row each, `Applies To` naming the `SYS-*` |
| Calibration terms (antenna factor, cable loss, …) | §4 Correction Chains |
| Tolerances | §5 Uncertainty Budgets |

## Changes

**`SKILL.md`, one hard rule** in `## Hard Rules`:

> Laboratory procedures, calibration and tolerances go into `GT/G0_SyRS.md`: procedures to §6 as `PROTO-NNN` rows, calibration to §4, tolerances to §5. Never invent one. When the Build Package has none for a section, write exactly `Not applicable: no lab inputs in the Build Package.` under its heading and keep the heading.

**`templates/GT/G0_SyRS.md`:** the italic guidance under §4, §5 and §6 adds: "Optional. Filled only when the Build Package supplies lab inputs (used by the Real HW HAL in `mock+real`). Otherwise: `Not applicable: no lab inputs in the Build Package.`"

## RED test first

In `tests/test_create.py`: through `_skill_text("S0_normalise_build_package")`, the text contains `Not applicable: no lab inputs in the Build Package.` and `PROTO-NNN`; the scaffolded `G0_SyRS.md` blueprint contains `Not applicable: no lab inputs in the Build Package.` Observe both fail, then edit.

Regression: a SyRS whose §4–§6 hold only the "not applicable" line passes `g0_validate.py` (new test on the existing script, no script change).

## Acceptance

1. A Build Package with a lab section produces a GT pair whose §4–§6 carry it, and the pair passes `g0_validate.py`.
2. A Build Package without one produces §4–§6 with the exact "not applicable" line, and the pair passes `g0_validate.py` (T8).
3. Existing S0 and G0 tests stay green.

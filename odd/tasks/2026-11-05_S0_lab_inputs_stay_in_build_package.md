# Plan — T2: S0 leaves lab inputs in the Build Package

Feature: `odd/tasks/2026-11-05_1421_vsil_v3_full_flow.md` · Task T2 · Specs S1, S4 · Assumption A1
Target: `templates/skills/S0_normalise_build_package/SKILL.md` (a few lines). G0 and the GT templates do not change.

## Goal

The Build Package may now carry laboratory procedures, calibration and tolerances. They serve only the Real HW HAL, which is optional (S1). The simplest place for them is where they already are: `GT/build_package.md`. S0 must not try to cast them into the StRS or SyRS, where no block fits them.

## Change

Add one hard rule to `## Hard Rules`:

> Laboratory procedures, calibration and tolerances stay in `GT/build_package.md`. Do not cast them into `G0_StRS.md` or `G0_SyRS.md`. List the headings that hold them in the S0 iteration Description, or write `Lab inputs: none`.

That Description line lets S1 find them without searching the whole Build Package.

## RED test first

In `tests/test_create.py`, through `_skill_text("S0_normalise_build_package")`: the text contains `Lab inputs: none` and `GT/build_package.md`. Observe it fail, then edit the skill.

## Acceptance

1. A Build Package with a lab section produces a GT pair that still passes `g0_validate.py`, with no lab content in it (T8).
2. The S0 Description names the lab headings, or says `Lab inputs: none`.
3. Existing S0 tests stay green.

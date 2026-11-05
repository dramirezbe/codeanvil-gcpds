# Plan — T3: S1 declares the HAL mode and the verification kit

Feature: `odd/tasks/2026-11-05_1421_vsil_v3_full_flow.md` · Task T3 · Specs S1, S2, S3, S4, S10 · Contracts C0–C11, D1–D6 · Assumption A1
Targets: `templates/skills/S1_design_services/SKILL.md`, `references/S1_design.md`. The graph template does not change.

## Goal

S1 must tell S2 exactly which tools to build first and which HAL to implement, so S2 never has to ask. Keep the skill short: the rules go in `SKILL.md`, the fields go in the template.

## Template (`references/S1_design.md`)

| Section | Change |
|---------|--------|
| Meta | New row `HAL mode` = `mock-only` or `mock+real` (D1). |
| §1.3.2 HAL | Points to §1.6 for the implementations. |
| §1.3.4 (new) Verification kit | Table of the tools S2 builds in its initial layer (S3, D2): Mock HAL, golden vectors + manifest, telemetry companion, stubs, fake peers, drivers, Real HW HAL with a fake device API (only `mock+real`). Columns: tool, path under `verification/` or `app/`, consumed by, source section. |
| §1.5 ML (optional) | Unchanged (S10, FW-ML-1). |
| §1.6 (new) HAL substitution ladder | Mock HAL (always): VL-0 vectors, VL-1 synthetic generator, base-layer port. Real HW HAL (only `mock+real`): device `HWC-*`, the Build Package lab headings named by S0 (A1), calibration grade, tolerances. |
| §1.7 (new) Telemetry companion | Always: signals, sampling interval, resource budget, operating envelope with a threshold and action per signal, output format, how readings attach to evidence (D3). |

English translation of `S1_G1_template.md` §1.6–1.7, as for the rest of the template (assumption A3 of the 2026-11-04 feature).

## `SKILL.md`

- **Inputs:** add the S0 Description line `Lab inputs:` (A1). Add "Rework" sources: a G1, S2 or G2 iteration with `FEEDBACK` naming sections (D6).
- **Hard rules (replace the `hw_dependency` rule):**
  - `HAL mode` is `mock-only` unless the GT or the user requires real hardware this cycle. In `mock-only`, no module has `hw_dependency: true`, so the highest `required_vl` is VL-1 (D5).
  - The Mock HAL and the telemetry companion are always designed. The telemetry companion is never a module and never part of `app/` (S2, D3).
  - The existing §1.5 rule stays as it is. ML integration is future work (S10).
- **Steps:** after step 4, add "fill §1.3.4, §1.6 and §1.7". The self-check of step 9 adds: kit table complete, `HAL mode` set, §1.7 present.

## RED tests first

Through `_skill_text("S1_design_services")`: names `HAL mode`, `mock-only`, `mock+real`, `Telemetry companion`, `verification/` and `Verdict: design defect`. Through the template file: contains `### 1.6 HAL substitution ladder` and `### 1.7 Telemetry companion`. Each assertion fails first.

## Acceptance

1. A `mock-only` design has no Real HW HAL table and no `hw_dependency: true` (T8).
2. Every design has a filled §1.7 and a kit table (T8).
3. An S2 or G2 `Verdict: design defect` iteration makes S1 rework the named sections, and `codeanvil status` then marks G1 stale (existing C11 behaviour).

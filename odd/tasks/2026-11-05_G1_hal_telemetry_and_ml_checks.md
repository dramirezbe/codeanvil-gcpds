# Plan — T4: G1 reviews the HAL mode, the kit, the toolchain and the telemetry companion

Feature: `odd/tasks/2026-11-05_1421_vsil_v3_full_flow.md` · Task T4 · Specs S1, S2, S4, S10, S11 · Contracts C0–C11, D1–D9
Targets: `templates/skills/G1_design_review/references/G1_CHECKLIST.md`; two lines in `SKILL.md`. (The `TEMPLATE_AGENT.md` line moved to T10.)

## Goal

G1 stays a human review with no script (S7 of the 2026-11-04 feature). Only the checklist grows, and its numbers match `S1_G1_template.md` again (G1.11 HAL, G1.12 telemetry, G1.13 ML). G1's PASS now routes to S2, which exists after T5.

## Checklist rows

| Row | Agent checks and shows | Marked `open` when |
|-----|------------------------|--------------------|
| G1.5 profile (edit) | `hw_dependency: true` means `VL-2`, and appears only in `mock+real` | Any mismatch |
| G1.11 HAL ladder (new) | `HAL mode` set. Mock HAL: base-layer port, VL-0 vectors, VL-1 generator, golden manifest fields. Only in `mock+real`: Real HW HAL on the same port, the SyRS `PROTO-*` it executes, its §4 correction chains and §5 tolerances, calibration grade (D9) | Any required item is missing, or `mock+real` with SyRS §6 `Not applicable`. Real HW HAL items in `mock-only` are `advisory` |
| G1.12 Telemetry companion (new) | §1.7 signals, interval, budget, operating envelope, attachment to evidence; not a module, under `verification/telemetry/`, never under `src/` | Any is missing, or it appears as a module |
| G1.13 ML readiness (renumbered from G1.11) | Content unchanged (S10, FW-ML-2) | Unchanged |
| Kit (new, no number) | §1.3.4 lists every tool S2 must build first with D2 paths, and the Meta `Toolchain` row gives every service a package name, language, package manager and test runner from the allowed pairs, runnable on its deployment target (D7) | A tool S2 needs is absent, a path breaks D2, or a service's `Toolchain` entry is missing or incomplete |

## `SKILL.md`

- Step (1): "Fill the checklist, including G1.11–G1.13 and the kit row."
- PASS route, line 70: replace `S2, which is not available yet: return "G1 passed. S2 is not available in this release."` with `S2: return "G1 passed. Run the S2 skill."`.

Nothing else changes.

## RED tests first

Through `_skill_text("G1_design_review")` plus the checklist file: names `G1.11 HAL ladder`, `G1.12 Telemetry companion`, `G1.13 ML readiness`, `Toolchain`, `mock-only` and `G1 passed. Run the S2 skill.`; no longer contains `G1.11 ML readiness` nor `S2 is not available in this release`. (The `AGENTS.md` negatives are in T10.)

## Acceptance

1. A `mock-only` design with no Real HW HAL gets no `open` finding for it.
2. A design without §1.7, or without `Toolchain`, gets an `open` finding.
3. Checklist numbering equals the template numbering.
4. A G1 PASS returns `G1 passed. Run the S2 skill.`

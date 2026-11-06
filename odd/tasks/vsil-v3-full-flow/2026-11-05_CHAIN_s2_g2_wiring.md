# Plan — T5: wire S2 and G2 into the chain

Feature: `odd/tasks/2026-11-05_1421_vsil_v3_full_flow.md` · Task T5 · Specs S5, S9 · Contracts C1, C2, C4, C10
Targets: `templates/config.yaml`, `tests/test_create.py`. No Python change expected.

## Goal

Make `codeanvil create` ship S2 and G2 and list them in the generated `AGENTS.md` table, reusing the existing tools (S9). `codeanvil status` already knows S2 and G2: `report_order` lists them, `stage_reports` lists S2, and a test already covers `S2: delivered`.

## Changes

```yaml
skills:
  # ...existing four entries...
  S2_implement_services:
    project_dir: ".agents/skills/S2_implement_services"
    prerequisite: "G1"
  G2_adaptive_verification:
    project_dir: ".agents/skills/G2_adaptive_verification"
    prerequisite: "S2"
```

Each new directory starts with a `SKILL.md` that has frontmatter (`metadata.gate`) and one line: "Not implemented yet." T6 and T7 replace it. This keeps the suite green between commits.

## RED tests first

- The generated `AGENTS.md` lists `S2_implement_services` with prerequisite `G1` and `G2_adaptive_verification` with prerequisite `S2`, in chain order after G1.
- A scaffolded project contains `.agents/skills/S2_implement_services/SKILL.md` and `.agents/skills/G2_adaptive_verification/SKILL.md`.

## Check

Run `codeanvil create` into a `mktemp -d` scratch folder and read the `AGENTS.md` table. Remove the scratch folder afterwards.

## Acceptance

1. The chain table reads S0 → G0 → S1 → G1 → S2 → G2, with RFD at `-`.
2. The whole suite passes.

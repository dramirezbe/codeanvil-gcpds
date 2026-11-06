# Plan — S0: Build Package normalisation

Feature: `odd/tasks/2026-11-04_1042_vsil_v3_skill_flow.md` · Task T3 · Specs S1, S2, S3 · Contracts C0, C1, C4, C7, C10
Target: `templates/skills/S0_normalise_build_package/SKILL.md` (new, about 110 lines), plus its own `templates/G0_StRS.md` and `templates/G0_SyRS.md`, placed by the scaffold. Paper §3.

## Goal

Cast the Build Package into the two IEEE 29148 blueprints in one pass, with no judgement. Paper: "S0 **normalises only**". Iteration happens at G0.

## Inputs and outputs

| | Path | Notes |
|---|------|-------|
| Input | `GT/build_package.md` | User-authored and the only content source |
| Input | `templates/skills/S0_normalise_build_package/templates/G0_StRS.md`, `.../G0_SyRS.md` | This skill's own locked blueprints (C10). The scaffold writes them, and the path rewrite points the skill text at them |
| Input (re-entry) | `.codeanvil/report/<cycle>/G0.md` | Latest FEEDBACK: script errors or Gate H reasons tagged by block ID |
| Output | `GT/G0_StRS.md`, `GT/G0_SyRS.md` | Filled blueprints |
| Output | `.codeanvil/report/<cycle>/S0.md` | Description holds inventory, missing list and trace |

## Skill sections

Frontmatter: `name: s0-normalise-build-package`, `metadata.gate: "S0"`, trigger words `S0, Build Package, normalise, StRS, SyRS`.

1. **Prerequisite and cycle.** Entry point, no prerequisite. Resolve the cycle as G0 does.
2. **Decision table.**

| Situation | Action |
|-----------|--------|
| `GT/build_package.md` present, no GT pair | Normalise |
| `GT/build_package.md` present, GT pair present, `S0.md` exists | Re-normalise, applying the latest G0 feedback |
| `GT/build_package.md` present, GT pair present, no `S0.md` | Hand-written pair: ask once before overwriting |
| No Build Package, GT pair present | No-op iteration: "pair supplied as normalised input" (A1) |
| Neither | Stop and ask for `GT/build_package.md` |

3. **Hard rules.**
   - Run in **one pass**, with no confirmation prompts (L16 of the chat-only feature: "I dont like S0 needs continue ASkUser all the time").
   - Copy numbers, units, standards and clauses verbatim.
   - Invent nothing. A field the Build Package does not supply keeps its blueprint placeholder and is listed. G0 rejects it and the author supplies it.
   - Copy `Status`, `Compliance` and STK `Standard(s)` from the Build Package; never infer them. Where the blueprint has an enum marker, use `PENDING` or `PROPOSED`. Never fill §5 by vocabulary heuristic. These are the corrections recorded in L10 of the chat-only feature that its S0-1 never received, so do not copy that behaviour.
   - Give no verdict and no comment on sufficiency, realism or scope.
4. **Steps.** (1) Inventory each statement as `STK | HWC | NRM | SYS | not mapped`. (2) Fill the StRS. (3) Fill the SyRS, including `Traces to` from the Build Package's own links. (4) Write the trace and missing list into the report. (5) Write the iteration with `HITL: PASS` (C4) and return `S0 complete. Run the G0 skill.` A re-run after G0's PASS makes `codeanvil status` mark G0 stale, so G0 runs again (C2, C11).
5. **Re-entry.** Match each G0 error to its Build Package line. If the content exists, correct the GT. If not, list it as "needs Build Package content".

## RED tests first

`tests/test_create.py`, through `_skill_text("S0_normalise_build_package")`:

- names `.codeanvil/report/<cycle-name>/S0.md`, `GT/build_package.md` and `HITL: PASS`;
- contains `no prerequisite`;
- `tests/test_create.py` also asserts that a scaffold contains `.agents/skills/S0_normalise_build_package/templates/G0_StRS.md` and `G0_SyRS.md`, byte-identical to the G0 skill's copies.

## Acceptance

1. `test-inputs/build_package.md` normalises to a pair that `g0_validate.py` passes with exit 0 (T7).
2. The same package with Part B removed yields SyRS placeholders and G0 exit 1 (T7), as `test-inputs/README.md` predicts.
3. Every non-placeholder value traces to a Build Package line.

## Reuse

`templates/GT/` stays the single source of the blueprints: `_copy_gt_reference_templates` copies the same two files into both S0 and G0 (T6), so the copies match in every scaffold. `_copy_skills` picks up the new directory.

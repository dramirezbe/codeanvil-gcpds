# Resume G1 after a complete S1 rework — 0.9.3

Branch: `fix/s1-g1-rework`, based on main / v0.9.2. Owner authorized implementation
and release 0.9.3. No edits to the ongoing T0 project's evidence are part of this change.

## Problem and decisions

The live T0 S1 iteration 3 incorrectly used `Based on: G1 iteration 1`. G1 consumed
the previous design, so replacing that design made G1 stale and propagated staleness
back into S1. Independently, `next_step` kept routing an old G1 FEEDBACK to S1 even
after a new, correctly based S1 delivery existed.

S1 always bases its delivery on G0. `Rework from: G1 iteration N` records the feedback
source without adding an upstream dependency. Incorrect S1 predecessors receive an
`invalid-baseline` diagnostic. A newer complete S1 delivery requires a new G1 review;
the old G1 remains historical and stale. RFD, GT drift and incomplete deliveries still block.

## Work units and validation

1. State/routing and regression tests: `src/codeanvil/reports.py`,
   `tests/test_report_state.py`, `tests/test_s1_g1_rework.py`.
   Focused command: `.venv/bin/python -m pytest -q tests/test_s1_g1_rework.py
   tests/test_report_state.py tests/test_v4_flow_boundaries.py tests/test_v4_integrity.py`:
   **39 passed** (0.33 s).
   Runtime probe: read the live project's reports without writing; its invalid predecessor
   receives the new diagnostic. Replacing only the in-memory S1 predecessor with G0 now
   yields `Next: G1` (previously `Next: S1`). Synthetic repeated FEEDBACK/rework tests
   preserve historical bytes and require fresh human gate fixtures.
   Rollback: revert the report parser/routing changes and their accompanying tests.
2. Latest S1 delivery integrity, with custody/status/CLI regression coverage:
   `custody verify --gate S1` and `status` share output comparison for the latest S1
   delivery. A changed/missing design is `undelivered-output`, and an invalid predecessor
   is diagnosed without following a backward edge. Other stages' overwritten outputs
   and historical S1 outputs are not checked. Reports lacking recorded outputs retain
   legacy parsing; the G1 skill still requires the SDD Output baseline before review.
   Focused command above plus `tests/test_create.py`: **116 passed** (1.55 s).
   Runtime boundaries: subprocess custody verification exits 1 for an edited/deleted
   design, and isolated-DB status changes from `Next: S1` to `Next: G1` after delivery.
   Rollback: remove the shared S1 output comparison, CLI help changes and associated tests.
3. S1/G1 completion and re-review instructions, generated reference alignment,
   recovery procedure, manual agent evaluation scenarios and release metadata.
   S1 revision 1.2 and G1 revision 1.1 share `rework_delivery.md`: close the report,
   preserve G0, keep feedback provenance separate, check all module/path/graph profiles
   and recover malformed historical delivery metadata by appending a corrective iteration.
   G1 completes the review through its human decision boundary and never inherits a verdict.
   Focused skill/scaffold/custody/status tests: **123 passed** (1.59 s).
   Full `.venv/bin/python -m pytest -q`: **762 passed, 40 skipped, 1 existing
   FastAPI/httpx deprecation warning** (13.22 s).
   Runtime boundary: generated-project tests include the new reference and both skills;
   a fresh model-driven S1/G1 evaluation is **not run**. The manual evaluation guide records
   the observed 0.9.2 failure and the new scenarios without inventing a passing transcript.
   Rollback: revert the skill/reference/scaffold instructions and their contract tests.

Keep these units independently reviewable; no final PR is created. The CLI remains
stateless and does not execute methodology stages or decide human gates. Automated
fixtures prove state transitions, not model obedience or a real Verified Prototype.

Work-unit commits: `edcf70c` (state/routing), `6ba2466` (delivery integrity),
`e93fe36` (skills/scaffold). Each unit is below 400 authored changed lines;
publication uses the owner's direct merge/release authorization, with no final PR.

## Release preparation and existing projects

Package and lock metadata are 0.9.3; the existing tag-triggered workflow publishes the release.
The CLI update does not rewrite scaffolded instructions or reports. Refresh S1/G1 and their
references plus generated AGENTS instructions separately before resuming an existing project.
A project with the incorrect S1 predecessor still needs a checked corrective delivery; do not
silently reinterpret or remove its historical evidence. This task leaves the live T0 untouched.
Release metadata/docs rollback independently from the three behavior units above.

Package validation: `uv lock --check` succeeded; `uv build --wheel` produced
`dist/codeanvil-0.9.3-py3-none-any.whl`. Archive metadata and S1/G1 skill revisions/reference
were checked. `uvx --from ./dist/codeanvil-0.9.3-py3-none-any.whl codeanvil --version`
reported 0.9.3. An isolated wheel environment outside the source checkout generated a
disposable scaffold with the new skills/reference and routed an older G1 FEEDBACK plus
new S1 delivery to G1. No user reports, GT, design or identity were changed by these probes.

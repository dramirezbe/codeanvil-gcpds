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
2. Latest S1 delivery integrity, with custody/status/CLI regression coverage.
3. S1/G1 completion and re-review instructions, generated reference alignment,
   recovery procedure, manual agent evaluation scenarios and release metadata.

Keep these units independently reviewable; no final PR is created. The CLI remains
stateless and does not execute methodology stages or decide human gates. Automated
fixtures prove state transitions, not model obedience or a real Verified Prototype.

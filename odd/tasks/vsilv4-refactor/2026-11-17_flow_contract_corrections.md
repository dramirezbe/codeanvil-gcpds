# V-SIL v4 — flow contract corrections

The conceptual review found gaps in the implementation candidate despite its green suite.
These corrections close the reported contracts; they do not supply a T0 full-flow verdict.

## Review ledger

| Finding | Correction | Evidence |
|---------|------------|----------|
| Final system smoke required too early | Slice 0 checks bases/stubs and handshakes; module slices regress built modules; only system requires the actual §0.5 root-command smoke and final paths. | S3/G3 skills, verifier and scope-contract test |
| Module VL-1 tests delayed until system | S3 writes/exercises required module VL-1 tests and prepares VL-2 scripts within the module slice; system adds contract/path tests. G3 independently verifies the declared levels. | S3 dispatch, PLAN and run.sh selector contract |
| Implementation notes mutate approved plans | G2-approved PLAN is immutable; parent notes go to S3.md. Plan changes require S2 rework and a new G2 review. | PLAN approval boundary; changed-plan digest regression |
| Previous slice trees block new delivery | S3 and verifier check the current prerequisite with --gate. Full-cycle verify still discloses earlier G3 tree differences as diagnostics. No old baseline is overwritten or silently exempted. | Synthetic slice 0 → slice 1 transition and custody checks |
| Rework wrongly needs a failing scope's PASS | Separate first delivery, advance and rework. Advance selects the latest report of the previous scope; rework uses its feedback scope/modules. A newer scoped FEEDBACK cannot inherit an older PASS. | scoped_report_state and rework tests |
| Accepted deltas cannot reach their applier | S2 delta-intake runs before planning prerequisites, on completed G3 PASS or FEEDBACK. It materializes authoritative acceptance idempotently, writes no S2 iteration, then routes to S0/G0 or S1/G1. | Intake/proposed/accepted/applied transition test |
| Applied deltas reuse the prior human gate verdict | G0/G1 must review each new S0/S1 delivery. Only their completed review can preserve downstream neutral baselines. GT review precedes dependent design sync. | Fresh Gate H/G1, rejection and mixed-sync tests |
| Sync-only feedback loops back to S1 indefinitely | A reviewed sync returns to S2 in the original scope, followed by G2/S3/G3; system PASS requires no unresolved human acceptances or pending accepted deltas. | System feedback → intake → apply → review → replan → final G3 fixture |
| Residual v3 fields and ownership | Remove S1's retired approval Meta row, assign plan rework to S2 and code/kit edits to S3, update G1 metric evidence to G3. | Skill assertions and existing G1/S1 tests |
| Consumed artifacts missing from digest contract | S0 emits GT Output lines, S3 emits test_run.md Output, and G3 records that command artifact plus SDD/SyRS as inputs. | Scope-contract assertions |

The SDD is a parent input for infrastructure/integration. Fresh-context isolation still applies
strictly to module implementors. INFRA/INTEGRATION plans now expose that parent Context set
so G2 can review them without imposing the module agent's narrower read boundary.

## Validation

- Full suite: `.venv/bin/python -m pytest -q` → **742 passed, 40 skipped, 1 warning** (12.26 s).
- Report/custody transitions: `.venv/bin/python -m pytest -q tests/test_v4_flow_boundaries.py tests/test_v4_integrity.py tests/test_report_state.py` → **32 passed** (0.26 s).
- Scope/skill/scaffold checks: the 13-file focused command recorded in FEATURE.md → **109 passed** (1.07 s).
- `git diff --check`: clean.
- The remaining warning is FastAPI/Starlette's httpx TestClient deprecation.

The focused runtime boundary uses the real custody console call from test_v4_integrity and
isolated generated projects from test_v4_scaffold_flow. All report PASS rows in the transition
fixtures are synthetic test data; no agent/human methodology verdict is claimed.
No T0 execution, hardware run, UI source change or DB source change was performed.

## Review and rollback units

1. `eeccc02`: reports.py and its transition/integrity tests. Rollback removes the scoped history,
   delta-intake guidance and mandatory sync-review transition fixes.
2. The following contract commit: methodology skills/templates, updated G1 assertions and the
   scope-contract test, plus this evidence. Rollback removes the scope/immutability/re-entry
   instructions and restores the earlier contracts; keep it paired with unit 1 during review.

No final PR, push, tag or release. The real T0 full-flow acceptance remains pending human gates.

# S1 execution continuity — 0.9.2

Branch: fix/s1-execution-continuity, based on v0.9.1 / main.
User authorization: “Modifica S1 para que no vuelva a pasar esto. haz release 0.9.2 después del cambio”.

## Observed failure

T0 cycle 01_initial had a recorded G0 PASS and current custody inputs. Two explicit `run`
requests produced template/GT reads and backup/digest/timestamp collection, followed by
“I cannot complete S1 in this turn” and “S1 is still pending”. No concrete blocker or runtime
limit was identified, and no S1 artifacts were produced. The S1 skill lacked the explicit
execution-continuity contract already used by S3/G3.

## Change

S1 skill revision 1.1 requires authorized execution in the same turn through design, both
reference graphs and the completed stage report, or a specific real stop condition. Preparation
is not completion. Resume partial design without resetting valid sections, repeating a successful
backup or requesting unchanged authorization. Derive design decisions from GT; ask only for
required choices unavailable in the inputs. Write artifacts incrementally. Continuation aliases
resume the authorized scope but never waive prerequisites or decide G1.

Explicit human stop, required input/permission, operational failure, actual interruption and
RFD remain valid boundaries. Preserve drafts, report precise evidence and never fabricate a
completed iteration. S1 PASS remains delivery only; G1's human verdict is separate.

No orchestrator, new report state or mandatory recovery artifact is introduced. Package/lock
version is 0.9.2. Existing projects need their generated S1 SKILL.md refreshed; upgrading the
CLI alone does not rewrite already scaffolded skills. Only that instruction file is refreshed
for the user's current T0 project after installation, preserving GT, identity, drafts and reports.

## Validation

- `.venv/bin/python -m pytest -q tests/test_vsil_s1.py tests/test_custody_rule.py tests/test_v4_scaffold_flow.py`:
  **15 passed** (0.35 s).
- `.venv/bin/python -m pytest -q`: **748 passed, 40 skipped, 1 existing FastAPI/httpx
  TestClient deprecation warning** (13.07 s).
- Generated-project probe: the scaffolded S1 skill carries the same continuity block and
  project-relative reference paths; the probe creates no design or stage verdict.
- `methodology/test/execution_continuity.md` records the observed failure and adds S1 delivery,
  resume, missing choice, permission, explicit-stop and negative-response evaluation scenarios.
  Updated-skill model evaluation is **not run**; contract tests do not prove model compliance.
- `git diff --check`: clean. No product code, UI or DB behavior changes.

## Delivery and rollback

One work unit: the S1 skill, its contract/scaffold tests, manual evaluation guide and 0.9.2
release documentation/metadata. Revert that unit to restore skill revision 1.0 and old metadata.
The existing T0 instruction refresh preserves its previous instruction file separately and
never runs S1 or modifies S0/G0 evidence. The ongoing run remains the model-behavior evaluation.

The owner authorized merge to main, annotated v0.9.2 and the release. Publication is separate
from V-SIL acceptance. Install the published tag, not a local-only candidate, before resuming.

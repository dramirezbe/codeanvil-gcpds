# Implementation: `.codeanvil/` directory inside scaffolded projects

Spec: `odd/tasks/2026-10-21_1623_project_codeanvil_dir_plan.md` (committed at 50ce49e).
This file tracks progress. Do not edit the plan — implement it.

## Route

Delegated direct (writer trigger: 15+ files). One writer, one verification pass.

## TDD

Mode: ordinary functional checks (no strict_tdd confirmed).
Runner: `PYTHONPATH=src python3 -m pytest tests/ -q` (package not installed editable).
New units MUST have tests: identity, time machine format, paths find_manifest, projects sync, sync flow.

## Checklist

- [x] T1. Config layer: paths.py (WORKDIR rename + PROJECT_* + find_manifest + ensure_dirs migration), identity.py (generate_uuidv7), time.py (format_timestamp_machine) + tests
- [x] T2. DB layer: schema.py (slim: TEXT uuid id, drop sessions/gate_results; old-schema detect+recreate), projects.py (register_project by uuid, get_project_by_id, sync_project), delete sessions.py + tests
- [x] T3. Init layer: create.py (_create_codeanvil_dirs, write_project_manifest, scaffold hook), sync.py (run_sync, _migrate_provenance, find via paths) + tests
- [x] T4. CLI: cmd_sync, cmd_create uuid flow, cmd_status (cwd/name + auto-sync + report dir), cmd_list short uuid, cmd_now --machine, argparser updates
- [x] T5. Templates/docs: TEMPLATE_AGENT.md (paths + timestamps mandate + report creation), custody-chain SKILL/scripts/assets, templates/config.yaml path_replacements, repo AGENTS.md/CLAUDE.md/README.md/methodology test README path renames
- [x] T6. Verification: pytest green, scaffold testproj in /tmp, sync flow, G0 validate, no stale .provenance paths

## Decisions / clarifications (resolved during exploration)

- `install.sh` has NO `~/.codeanvil` references — nothing to change there.
- Python 3.14 has native `uuid.uuid7`, but pyproject requires >=3.10 — implement stdlib-only `generate_uuidv7()` per plan (works everywhere).
- DB keeps `path` column (local machine state); the files-table wording "no path" was a typo — follow the SQL in plan §4.
- Schema migration: pre-release — detect old INTEGER-id `projects` table and recreate DB on init.
- Also update CLAUDE.md, README.md, methodology/test/README.md (same mechanical rename; plan table missed them).
- `codeanvil status` name arg becomes optional (cwd mode).
- Report listing parses `<gate>_<machine-ts>.md` filenames; latest per gate wins.

## Progress log

- 2026-10-21: exploration done, tasks created, branch `feat/project-codeanvil-dir`.
- 2026-10-21: T1–T6 implemented. 40/40 pytest green (`PYTHONPATH=src python3 -m pytest tests/ -q`). Smoke test passed: init → `.codeanvil-config/db/codeanvil.db`; create → `.codeanvil/{project.yaml,custody,report}`, no `.codeanvil/GT`, no `.provenance`, manifest = UUIDv7 (no path); clone sync → registered/moved semantics OK; `list` short uuid; `moved` sync → `[moved]`; `now` / `now --machine` formats OK; `status` cwd+name modes, auto-sync on fresh DB, latest-report-per-gate listing; legacy `~/.codeanvil` home migrated + old-schema DB recreated; G0 validate PASS on T0 GT; generated AGENTS.md has zero `.provenance` refs. Deviations: (a) `methodology/test/smoke_test.sh` also renamed `.provenance` → `.codeanvil/custody` (twin of test README, would break otherwise); (b) `format_timestamp_machine` also replaces the millisecond `.` with `-` (plan §7 example `...16-23-45-123` vs plan snippet which left the dot); (c) `tests/test_time.py` explicit-tz test uses `America/New_York` instead of `US/Eastern` (no tzdata/US link on this OS — pre-existing env failure); (d) `custody_ledger.py` docstring gained one line naming `.codeanvil/custody/custody.jsonl` (its argparse `--ledger` is required, there was no literal stale path to rewrite). Not committed — changes left for orchestrator.
- 2026-10-21: independent verifier PASS with 1 major + 5 minor/nit findings. Fixer round applied: (1) MAJOR — `cmd_create` reuses existing manifest UUID via `read_manifest_id()` + `write_project_manifest` skip-on-same-id (re-scaffold keeps id, no stale DB row); (2) `cmd_list` coerces `str(row['id'])[:8]` for legacy INTEGER ids; (3) `_migrate_provenance` migrates when `custody/` missing OR empty (rmdirs empty first); (4) `cmd_status` name-mode verifies `manifest.parent.parent == project_dir` (no parent-hijack); (5) cwd-mode manifest None/missing-keys guard, exit 1; (6) clean-install README also `rm -rf ~/.codeanvil`. Final: 45/45 pytest green. RDD off (global); risk assess = high (shell smoke_test.sh); verified via independent verifier + parent spot-check re-run.

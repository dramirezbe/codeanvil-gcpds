# Apply S3 pause schedules by scope and preserve plan directory backups — 0.9.5

Branch: `fix/s3-pauses-directory-backups`, based on main / v0.9.4. Owner authorized
implementation, release 0.9.5 and manual synchronization of the active T0 run's instructions.

## Behavior and work units

1. Backup directory handling: detect actual directories rather than a trailing slash removed
   by Path. Keep project-relative paths for directory contents and record `backup_path` in
   MANIFEST.yaml so distinct module PLAN.md files cannot overwrite one another. Individual
   file targets retain their historical flat layout; old snapshots are not rewritten.
   Staging/rename, unknown producer, empty first backup and interrupted-pass reuse remain.
   Rollback: backup.py and its regression tests; existing snapshots remain readable by manifest.
2. S3 pause contract: Per module is valid for slice 0, with a checkpoint after infrastructure
   and checks. Define checkpoints for module and system scopes, retain answered schedules on
   resume, and prevent a before-PATH checkpoint from leaking into earlier scopes. Load actual
   instructions and route broken upstream custody to its owning skill, without deciding HITL.
   Rollback: S3 instructions/reference, contract/scaffold tests and evaluation scenarios.
3. Release and manual run refresh: publish and install the immutable tag, refresh generated
   instruction assets, verify real S2 directory backup, and preserve GT/design/plans/reports,
   identity, current source and all human decisions. Do not implement S3 or invent a G2 verdict.

Each unit keeps tests/docs with behavior and remains below 400 authored changed lines. No final
PR, orchestrator, UI source or DB schema change is part of this release.

## Validation

Backup regressions cover distinct nested PLAN.md files, manifest digests and restore paths,
idempotent interrupted-pass reuse, empty/missing plans, copy failure without a published
snapshot and legacy individual-file layouts. A subprocess checks the actual CLI boundary.
`.venv/bin/python -m pytest -q tests/test_backup.py`: **17 passed** (0.22 s).
Focused S3/question/scaffold/custody/backup checks: **66 passed** (0.87 s).
Fresh model-driven S3 evaluation is separate from static skill/scaffold checks; never claim
that a textual assertion proves the model obeys the pause schedule.

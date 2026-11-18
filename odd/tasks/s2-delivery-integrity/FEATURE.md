# Complete S2 and reject malformed report digests — 0.9.4

Branch: `fix/s2-delivery-integrity`, based on v0.9.3 / main. The owner requested
0.9.4 after a live first S2 delivery stopped on a successful empty backup, then
recorded a 62-character SDD digest which custody silently ignored.

## Work units

1. Report integrity: parse declared Input/Output lines in the latest unfenced iteration.
   Reject malformed/duplicate declarations instead of silently dropping them. A scoped
   S2 PASS also requires the canonical SDD and SyRS Input lines. Historical iterations,
   fenced examples and unscoped legacy reports retain their existing semantics.
   `status` and custody share the parsed errors; custody exits 1 and the chain cannot
   advance from a malformed S2 delivery. Recorded human verdicts remain unmodified.
2. S2 continuity and recovery: define backup success by exit code; create missing
   first-delivery artifacts, finish the scoped report, verify custody and hand off to G2.
   Preserve real stops, scope limits, human decisions and earlier report bytes.
3. Publish 0.9.4, refresh the live S2 instructions and append a checked corrective
   delivery if the run still needs one. Do not decide or overwrite G2.

Each work unit keeps behavior, tests and docs together. No final PR is created; the
owner authorized direct release. Rollback of unit 1 removes parser/custody diagnostics
and accompanying regression tests; unit 2 reverts S2 instructions and evaluation cases.
Release metadata is independent. No orchestrator, DB schema or UI source changes.

## Evidence

- Focused report/flow/scaffold regressions: **64 passed** (0.88 s).
- `.venv/bin/python -m pytest -q`: **782 passed, 40 skipped, 1 existing
  FastAPI/httpx deprecation warning** (13.60 s).
- Source CLI against the live report (read-only): `custody verify --cycle 01_initial
  --gate S2` exits 1 with malformed-input and missing SDD input diagnostics.
- Synthetic subprocess regression covers the same 62-character failure; correction by
  append reopens G2 while preserving bad historical bytes. Fixtures now use real v4
  canonical S2 inputs. This does not prove a model follows the skill or accept a gate.
- S2 revision 1.1 and its delivery reference distinguish exit-0 empty backup from failure,
  resume without redundant authorization, require scoped artifacts and report publication,
  and preserve G2's human boundary. Only DELTAS starts empty; BACKLOG contains Kahn rows.
  The infrastructure reference requests exact handshake data and ordered creation tasks.
- Skill/scaffold/report/backup focused tests after path-compatibility coverage:
  **113 passed**. Required-input presence accepts `./` paths and native Windows separators.
- `methodology/test/execution_continuity.md` adds first-delivery, interruption, real-stop and
  metadata-repair scenarios. A fresh model-driven evaluation is **not run**; static tests
  and instruction copying do not establish model obedience.

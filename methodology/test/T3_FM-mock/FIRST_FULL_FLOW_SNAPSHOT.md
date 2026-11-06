# First full V-SIL v3 result — T3 FM mock

`first_full_flow_2026-11-05/` is a copy of the OpenCode project at
`/home/javastral/GIT/UNAL/sandbox-vsil-opencode.QhpdEN/fm_occupancy_mock`
after G2 iteration 2 passed. It preserves the project files, including hidden
agent configuration, scaffolded skills, GT, reports, source code, lockfiles,
golden vectors and verification kit. The original sandbox was not edited.

The copy excludes only machine-local or regenerable state: `.git/`, `.venv/`,
`node_modules/`, `__pycache__/`, `.pytest_cache/` and the empty `lancedb/`
directory. `rsync -an --itemize-changes` with those same exclusions reported no
differences immediately after copying. Commit `2b760da` is the untouched
99-file result. The later entry-point correction is tracked as a separate
commit; use `git show 2b760da:<path>` to inspect any original file.

The cycle's reports record S0/G0/S1/G1/S2/G2 at iteration 2 and G2 `PASS`.
Those verdicts describe the tests that ran; the first result's package entry
point only printed startup messages. See
`S1_G1_review_holdout_2026-11-05.md` for the review and closure audit.
The corrected copy has `RUN.md` with a tested Mock HAL preview command.

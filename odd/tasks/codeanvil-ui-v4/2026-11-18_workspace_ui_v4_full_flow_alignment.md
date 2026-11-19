# Implement V-SIL v4 workspace compatibility for CodeAnvil 0.10.0

Adapt the existing workspace UI in place. The UI originated with the 0.7.8
project format, and the branch includes preliminary v4 workspace and telemetry
changes from `aa3af22`. Compatibility remains pending until the implementation
meets the requirements and acceptance checks below.
CodeAnvil `0.10.0` delivers UI compatibility with the project format used by
CodeAnvil `0.9.7`, the active V-SIL v4 skills on `main`, and the artifacts in
`0.9.6-full-flow-hackrf-rpi-mvp`.
Use `templates/config.yaml` and the active skills for the report and artifact
contracts. Use the saved snapshot to check how those contracts appear in an
actual run and how the UI handles missing evidence. Match projects by v4 structure.

Reuse the workspace, API, artifact views, and uPlot charts already on `main`.
For each compatibility gap, identify the skill contract or saved artifact
that exposes it and make the smallest fix that satisfies it. Close checks
that already pass using the verification results. Update tests, bundled
assets, and documentation where a fix calls for it. The watchdog, hardware
gallery, and other follow-on ideas remain in the backlog for a separate delivery.

## Delivery sequence

1. Create or update `refactor/ui-vsil-v4` from current `main`. Compare the
   existing workspace, artifact views, and Telemetry & VL-2 view with the
   active skills and the saved run.
2. Fix compatibility gaps on that branch and complete the release acceptance
   checks below. Update `pyproject.toml` and `uv.lock` to `0.10.0` in the same PR.
3. Open a PR into `main`, confirm CI passes, and merge. Confirm CI passes on the
   resulting commit in `main`.
4. Create and push the annotated tag `v0.10.0` from that commit. Confirm the
   GitHub release workflow publishes the release and its generated changelog.

## Findings from the saved full-flow

| Contract | Snapshot value |
|-----------|----------------|
| Project manifest | `.codeanvil/project.yaml`, cycle `01_fm_hackrf_rpi5_mvp` |
| Report chain | `S0.md`, `G0.md`, `S1.md`, `G1.md`, `S2.md`, `G2.md`, `S3.md`, `G3.md` |
| Test evidence | `.codeanvil/report/<cycle>/S3_artifacts/test_run.md` |
| Verified Prototype | `.codeanvil/report/<cycle>/G3_artifacts/verified_prototype.md` |
| Prototype baseline | `S3 iteration 2, G3 iteration 1` |
| Telemetry | No JSONL samples; only text pytest/vitest logs and manually recorded idle readings |
| Machine measurements | No v2 `measurement.json` records |
| VL-2 | G3 says `NO EVIDENCE`; module/path rows include stubbed, blocked, and inconclusive results |

The previous workspace stopped at G2, exposed retired S2/G2 artifact paths, and
compared prototype freshness against S2/G2. Its workspace tests were globally
skipped and targeted 0.7.0 fixtures. The current UI documentation called the
workspace v3-only. The snapshot's manual idle readings are point observations,
not a time series; text test logs are not telemetry.

## Implementation decisions

| Area | Decision |
|------|----------|
| Supported project shape | Current v4 cycle reports and artifacts used by CodeAnvil 0.9.6/0.9.7; no guessed manifest version field and no v3 fallback. |
| Stage chain | Render all eight reports in `templates/config.yaml` order. |
| Verification artifacts | Read only `S3_artifacts/test_run.md` and `G3_artifacts/verified_prototype.md`; reject retired S2/G2 paths. |
| Prototype freshness | Compare the prototype's `Based on` S3/G3 iterations with the selected cycle's latest reports and current G3 status. |
| Telemetry inputs | Read only project-contained `verification/telemetry/**/*.jsonl`, v2 `measurement.json`, and named pytest/vitest text logs; bound file, sample, and response sizes. |
| Plot library | Pin `uplot` 1.6.32 in `package.json` and `pnpm-lock.yaml`. Use its canvas time-series, hover legend/cursor, drag zoom, responsive sizing, and reset control. Preserve nulls as gaps; do not fabricate points. |
| Measurement evidence | Display v2 S3/G3 run metadata and requirement-level value, unit, criterion, and pass/fail/inconclusive result; link to the source record. |
| VL-2 presentation | Show module/path rows and the honesty statement as recorded in the G3 Verified Prototype. Do not infer a VL-2 PASS from a run exit code or missing record. |
| Snapshot gaps | Clearly show no JSONL or measurement records, the explicit G3 VL-2 evidence ceiling, captured logs as text, and manual readings as point values rather than plotted trends. |
| Tests | Replace the global v3-only skip and 0.7.0 fixture assertions with current v4 snapshot coverage. Do not claim automated tests passed unless they are run. |
| Documentation | Update the UI README and top-level statements that advertise the workspace as v3-only; retain old examples as historical. |

## Files

- `src/codeanvil/UI/workspace.py`: v4 artifact allowlist, evidence discovery, bounded JSONL/v2 parsing, VL-2 summary, and prototype freshness.
- `src/codeanvil/UI/frontend/src/Workspace.tsx` and `App.tsx`: eight-stage chain and Telemetry & VL-2 navigation.
- `src/codeanvil/UI/frontend/src/TelemetryView.tsx`: uPlot canvas chart, measurement table, VL-2 evidence, and source-log viewer.
- `src/codeanvil/UI/frontend/src/styles/workspace.css`: responsive theme and uPlot styling.
- `src/codeanvil/UI/frontend/package.json`, `pnpm-lock.yaml`, and bundled `dist/`: pinned chart dependency and production assets.
- `src/codeanvil/UI/frontend/src/api.ts`: telemetry, machine-measurement, and evidence response types.
- `tests/test_ui_workspace.py`: current v4 workspace coverage in place of skipped legacy fixtures.
- `src/codeanvil/UI/README.md`, `AGENTS.md`, and `README.md`: current workspace contract and evidence limitations.

## Compatibility implementation checklist

- [x] Confirm the progress strip renders all eight stages in configured order and preserves missing reports.
- [x] Confirm prototype freshness against the latest selected-cycle S3/G3 reports and G3 verdict.
- [x] Confirm artifact routing accepts current S3/G3 locations and rejects retired S2/G2 locations.
- [x] Check that telemetry JSONL, v2 measurements, and captured text logs use bounded, project-contained reads and follow the selected cycle.
- [x] Verify the pinned uPlot chart with responsive sizing, cursor and legend, drag zoom, reset, timestamps or sample indices, and gaps for unavailable points.
- [x] Verify measurement values, units, criteria, source paths, and authored results beside the plots.
- [x] Verify G3 VL-2 module and path results and the honesty statement with the active template and saved run.
- [x] Verify the snapshot displays missing measurements and JSONL samples, manual readings as points, and the recorded VL-2 ceiling.
- [x] Update documentation to match the verified v4 behavior and distinguish historical fixtures from supported projects.

## Findings and fixes

| Contract and reproducer | Fix |
|-------------------------|-----|
| `templates/config.yaml` defines report order. The API followed it while React maintained a separate ordered list. | Render the API report sequence and use React only for display labels. |
| The archive uses `VL-2: NO EVIDENCE` and the active G3 prototype template uses `VALIDATED (VL-2, …)`. The template-derived prototype exposed the missing declaration in the API. | Read both declarations from the honesty section. Keep the source wording and derive IDs and status from the selected prototype. |
| The archive's mixed-level rows and the fixture's `VL-1 PASS; VL-2 BLOCKED` reproduced a green badge for blocked VL-2 in Chromium. | Apply the badge style to the VL-2 clause while showing the full authored result. |
| The telemetry collector can mark a sample unavailable. Real uPlot passed null to the legend on first render and at the fixture gap, throwing `Cannot read properties of null (reading 'toFixed')`. | Render an empty legend value, keep gaps in the series, and retain the plot across unrelated renders. |
| The S3/G3 machine evidence contract names runs by cycle and iteration. Two similarly named cycles reproduced ambiguous grouping. A regression test with 200 files in the other cycle reproduced missing selected-cycle logs. | Match the cycle from the run directory before applying limits, check measurement provenance against the record, and resolve selected files inside the project. |
| The direct artifact endpoint returned a log larger than the evidence limit even though the listing omitted it. | Bound both reads and return 413 for oversized direct reads. |
| The archive records point observations with an equipment-specific envelope heading. React looked for one named device. | Render the heading from the authored table across projects. Plot only machine samples. |

## Local verification

- `.venv/bin/python -m pytest -q` reported **834 passed, 7 skipped**. API
  checks include missing reports, report order, stale and current prototypes,
  retired artifact locations, cycle isolation, and evidence limits.
- `pnpm test` reported **42 passed**. `pnpm build` compiled TypeScript and
  produced the bundled frontend. Vite reported the existing chunk size warning.
- Playwright Chromium reported **archive: PASS** and **fixture: PASS**.
  The archive showed the eight reports, S3/G3 artifacts, current G3
  baseline, captured logs, manual point values and the recorded VL-2 evidence
  limit. The fixture checked timestamp and index axes, responsive canvas,
  gaps, cursor, legend, drag zoom, reset, measurement source and results,
  missing reports, and replacement of the evidence on cycle change.
- `uv build --python /usr/bin/python3 --offline` built the 0.10.0 source
  archive and wheel. The wheel's bundled assets passed validation and the
  browser suite ran against the wheel's Python package and static assets.

The [browser harness](acceptance/run.sh) starts two local servers and generates
the fixture in a temporary directory. From the repo root, run
`NODE_PATH=<directory containing playwright> bash odd/tasks/codeanvil-ui-v4/acceptance/run.sh`.
Set `PYTHONPATH` to an extracted wheel to check the distributed UI with the
same harness. The acceptance fixes and their regression coverage are contained
in the workspace API, frontend, and bundled assets listed above.

## Release acceptance checks

- [x] Open the saved full-flow project and check the eight stages, S3 test
  evidence, G3 prototype, and prototype freshness against the reports.
- [x] Verify that the saved run shows its authored VL-2 result and captured
  test logs, with empty states for missing JSONL samples and v2 measurements.
- [x] Use a separate fixture based on the active skills to verify that JSONL
  samples plot in uPlot, v2 measurements show their recorded results, and
  changing cycles shows the evidence for the selected cycle.
- [x] Pass the Python and frontend suites, build both distributions, and verify
  the UI served from the wheel.
- [ ] Confirm required GitHub CI checks pass on the PR and then on `main`.
- [ ] Push the annotated tag and confirm the GitHub release and changelog.

## Follow-on backlog outside 0.10.0

These proposals come from the [2026-11-10 UI plan](../ui/2026-11-10_2036_ui.md),
the [2026-11-11 artifact audit](../ui/2026-11-11_current_project_ui_audit.md),
and the [terminal handoff](../ui/2026-11-11_terminal_handoff.md). The order below
applies to future UI work after the compatibility release.

| Priority | Carry-forward idea | Remaining work and boundary |
|----------|--------------------|-----------------------------|
| 1 | **O6/S11 targeted watchdog refresh** | Watch project `.codeanvil/` documents (`report/`, `GT/`, `design/`, `backups/`, `project.yaml`, HIL audit) and `verification/telemetry/` data. Debounce filesystem events, use SHA checks to catch missed saves, handle create/change/delete including extensionless `DRAFT`, and publish a targeted WebSocket invalidation so only dependent views reload. Do not watch project source code or rescan the whole project on every event. The current WebSocket is for terminal sessions; no workspace file watcher is implemented. |
| 2 | **Backup history and inspection** | Expand the existing latest-per-stage listing into full backup history, MANIFEST and SHA-256 inspection, and safe read-only viewing of backed-up artifacts. There is no restore operation in this scope. |
| 3 | **Cross-cycle report comparison** | Compare selected report iterations across cycles, show changed fields and stale/fresh evidence, and keep cycle selection read-only. |
| 4 | **HIL target and audit view** | Show `targets:` and `.codeanvil/hil/audit.log` with configured targets clearly separated from connectivity, deployment, or test evidence. Never expose private keys or treat a target declaration as VL-2 proof. |
| 5 | **Project-wide COTS hardware gallery** | Use the 0.9.6 full-flow artifacts to learn the current v4 production pattern: parse each project's StRS §1.6 hardware inventory, link HWC constraints using each row's `Component` value, and use that project's SDD/G3 only as optional context/evidence. Implement this generically for every current v4 project and future project that follows the contract; never hard-code the HackRF/Pi names, `HW-*` IDs, project name, or run path. Show declared inventory separately from equipment actually observed during a run; missing G3/equipment data must not hide the declared inventory or imply physical presence. Resolve optional images through the keyless Wikidata/Wikimedia path only for unambiguous matches, cache and attribute images in the project, and allow an explicit project-local override without changing GT/manifest schemas. Never display G3 endpoint/user/workspace details or scan unrelated projects. |
| 6 | **Contextual runtime/MCP/telemetry workflows** | Move common tasks from the generic CLI action catalog into project/global settings. Keep global MCP installation separate from per-project activation; retain the generic action catalog as the advanced fallback. |
| 7 | **Launcher sidebar and install helpers** | Improve GUI-app/editor launchers, missing-tool status, no-sudo install recipes, and PATH refresh after installs. The current terminal selector handles installed CLI launchers on Linux/WSL. Native Windows-to-WSL launching and native macOS PTY remain deferred as previously directed. |
| 8 | **Native packaging** | After browser workspace acceptance, scope per-OS installers and native shells separately. Do not block the browser-based workspace on this work. |

The watchdog is the recommended next slice because it makes report, cycle,
telemetry, and verification updates visible without manual refresh while keeping
the existing project files as the source of truth.

# Align the workspace UI with the v0.9.6 full-flow project

The workspace supports the current V-SIL v4 project shape used by CodeAnvil
0.9.6/0.9.7, with no v3 artifact paths or presentation fallbacks. The saved
`0.9.6-full-flow-hackrf-rpi-mvp` project is the reference contract. Its manifest
does not declare a tool version, so support is determined by the v4 structure,
not a guessed version field.

## Quick path

1. Read the saved project's manifest, eight cycle reports, and S3/G3 artifacts.
2. Align the workspace API, artifact inventory, stage strip, and prototype freshness check.
3. Add a Telemetry & VL-2 view for actual JSONL samples, v2 measurement records,
   captured test logs, and VL-2 claims recorded by G3.
4. Use uPlot 1.6.32 for responsive canvas time-series charts with cursor/legend
   inspection, drag zoom, and reset zoom; keep textual evidence alongside plots.
5. Update documentation to describe current v4 support and the saved snapshot's
   actual evidence limits.

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

## Acceptance criteria

- [x] The saved full-flow project defines the current eight-report chain and S3/G3 artifacts.
- [x] The progress strip renders all eight stages in configured order; missing reports remain missing.
- [x] The prototype is current only when its S3/G3 baseline matches the latest selected-cycle reports and G3 remains PASS/current.
- [x] Retired S2/G2 artifact locations are rejected; no v3 workspace fallback remains.
- [x] Telemetry JSONL, v2 measurements, and captured text logs are discovered through bounded, project-contained reads.
- [x] uPlot 1.6.32 is pinned and renders responsive canvas plots with cursor/legend, drag zoom, reset, timestamps/sample indices, and true gaps for unavailable points.
- [x] Measurement values, units, criteria, source paths, and authored results remain visible beside the plots.
- [x] G3 VL-2 module/path results and the honesty statement are shown without upgrading blocked/inconclusive/no-evidence results.
- [x] The 0.9.6 snapshot shows no JSONL or v2 measurement records, keeps its manual readings unplotted, and does not imply VL-2 PASS.
- [x] Documentation describes v4 workspace support and distinguishes historical fixtures from supported projects.

Implementation and production asset build are complete. `pnpm install --frozen-lockfile`,
the frontend production build, Python syntax compilation, and `git diff --check` passed.
The automated test suite was not run.

## Follow-on backlog from the earlier UI plan

These proposals come from the [2026-11-10 UI plan](../ui/2026-11-10_2036_ui.md),
the [2026-11-11 artifact audit](../ui/2026-11-11_current_project_ui_audit.md),
and the [terminal handoff](../ui/2026-11-11_terminal_handoff.md). They are not
part of the completed v4 alignment above. Prioritize them in this order:

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

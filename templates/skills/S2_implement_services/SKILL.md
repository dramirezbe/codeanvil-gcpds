---
name: s2-implement-services
description: "Trigger: S2, implement services, build the code, verification kit, VL-0. From a G1-passed design, build the services and the verification kit, prove the VL-0 floor and write the VL-1 tests."
license: Apache-2.0
compatibility: "No scripts of its own. Reads the S1 design, .codeanvil/GT/SyRS.md and .codeanvil/project.yaml. Writes src/, verification/, root manifests, .codeanvil/report/<cycle-name>/S2.md and S2_artifacts/."
metadata:
  author: "gcpds"
  version: "1.0"
  gate: "S2"
  pipeline: "V-SIL"
---

# S2 — Implement the Services and the Verification Kit

Turn the G1-approved design into running code plus the verification kit, prove the VL-0 floor and
leave the VL-1 tests ready for G2. The agent runs every test itself: the Mock HAL and the kit exist
so it can, without hardware or a human in the loop. A human judges the result at G2.

## Prerequisite and Cycle

Resolve the active cycle from `.codeanvil/project.yaml` (`cycle:`); if missing, ask the user.
If the latest iteration of `.codeanvil/report/<cycle-name>/RFD.md` holds a line
`Superseded by cycle: <name>`, this cycle is **closed** by an RFD and read-only: return exactly
`Cycle closed by RFD. Continue in cycle <name>.` and write nothing. Otherwise check, in this order,
writing **no iteration** when you stop:

1. `.codeanvil/report/<cycle-name>/G1.md` is missing, its latest iteration is not `HITL: PASS`, or
   `codeanvil status` marks `G1` or any earlier report of the cycle `stale`: return exactly
   `G1 must pass first. Run the G1 skill.`
2. S2's own latest iteration is `FEEDBACK` with `Verdict: design defect` and its `Based on` line
   names the current latest G1 iteration: the design was not reworked. Return exactly
   `S1 must rework first. Run the S1 skill.`
3. The latest `G2.md` iteration is `FEEDBACK` with `Verdict: RFD`: return exactly
   `Cycle suspended by RFD. Run the RFD skill.`, unless the latest `RFD.md` iteration states
   `Outcome: Withdrawn`.

## Inputs

| Path | Role |
|------|------|
| `.codeanvil/design/SDD.md` | Read-only: Meta `HAL mode` and `Toolchain`, §1.3.4 kit, §1.5, §1.6 HAL ladder, §1.7 telemetry, §2.2 order, §3 contracts and vectors, §4 traceability |
| `.codeanvil/GT/SyRS.md` | Read-only: `SYS-*` thresholds for the VL-1 tests |
| `.codeanvil/report/<cycle-name>/G2.md` | Rework only: latest iteration with `Verdict: module defect` |
| `.codeanvil/report/<cycle-name>/G1.md` | Rework only: the latest PASS iteration's impact map (files to edit vs paths to retest only) |
| `templates/skills/S2_implement_services/references/project_layout.md` | Locked trees: Python, TypeScript, root manifests, kit |
| `templates/skills/S2_implement_services/references/logger.py` | Locked Python logger, copied unchanged |
| `templates/skills/S2_implement_services/references/logger.ts` | Locked TypeScript logger, copied unchanged |
| `templates/skills/S2_implement_services/references/telemetry_collector.py` | Locked telemetry collector, copied unchanged to `verification/telemetry/` |

## Hard Rules

- Implement only what the design declares, with the design's `Toolchain`; never choose another.
  A missing interface, an undeclared dependency, an incomplete contract or an empty or incomplete
  `Toolchain` is a **design defect**: write `| HITL | FEEDBACK |` with the line
  `Verdict: design defect` and the S1 sections to rework, then stop. Never edit the design or GT.
- Only Python with uv and pytest, and TypeScript with pnpm and vitest. No `requirements.txt`, no
  npm or yarn lockfile.
- Each service is `src/<package>/`, exactly as `project_layout.md` shows.
- Delivered code never depends on the scaffolding tool. Copy `logger.py` to every Python service's
  `config/logger.py`, `logger.ts` to every TypeScript service's `config/logger.ts`, and
  `telemetry_collector.py` to `verification/telemetry/`, unchanged, and never edit them. Every
  Python module logs with `log = get_logger(__name__)`; every TypeScript module with
  `getLogger("<package>.<module>")`. No `print`, no bare `console.log`.
- The kit is never shipped: no service imports or depends on anything under `verification/`. Kit
  Python dependencies go only in the dev group, so `uv sync --frozen --no-dev` starts every
  service without them; no service `package.json` lists a kit package. The telemetry collector is
  mandatory in every test run and never lives under `src/`.
- Implement design §0.5 as a real system entry point. Every service's package entry point starts
  its runtime loop, and a multi-service launcher starts the complete system and stops its children.
  In `mock-only`, ship a runtime Mock HAL or explicit demo bundle; the only working entry point
  must not import the non-shipped verification kit. A command that only logs instructions fails S2.
- Expected values come from the design's §3 vectors and `verification/golden/manifest.md`, never
  computed by the agent. Changing a vector invalidates the evidence that used it.
- In `mock+real`, the Real HW HAL's VL-0 tests use the fake device API; S2 never needs the hardware.
- Report only results of runs that actually happened, with their command.
- **Infeasibility is reported through G2.** S2 never runs the RFD skill. When a requirement looks
  unreachable on the declared COTS platform, record it in `test_run.md` under
  `Possible infeasibility` with the requirement IDs and the run that shows it, and finish the pass.
- **Resume, do not restart.** On a re-run, continue from what already exists in `src/` and
  `verification/`: re-run its tests, keep what passes, build what is missing. Never rewrite working
  code to start over.

## Pause Schedule

Ask the pause schedule at the start of **every** iteration, before any code, with your runtime's
native question tool (`AskUserQuestion` in Claude Code): one single-select question in English, with
no option preselected.

| Option | Pauses |
|--------|--------|
| Per layer and module | Per service: after the kit and its base, after each module and its tests, after integration |
| Per layer (recommended) | Per service: after the kit and its base, once after all its modules, after integration |
| Per service | Once after each completed service |

Recommend **Per layer** in one line: it pauses where a wrong contract is cheapest to catch, without
one stop per module. In the Steps below, the kit and its base end step 2, the modules end step 3, and
the integration is the producer and consumer contract tests at the start of step 4. If the runtime
has no question tool, ask the same question in chat and wait for the reply; never assume or default
an answer. A rework asks again.

Every schedule adds one pause after cross-service integration and before the `PATH-*` tests. At each
pause the human answers `continue`, `rework` or `stop`, through the same question tool or in chat
when it is unavailable.

- `continue`: go on to the next pause.
- `rework`: fix what the human names in the current layer or module, re-run its tests, then pause
  again.
- `stop`: write no iteration and return
  `S2 stopped at the human's request. Run the S2 skill to resume.`

Record every answer as a checkpoint line in the iteration's Description, never as a gate verdict:
`Checkpoint: <pause point> — <continue|rework|stop> — <note>`. A `stop` writes no `S2.md`; the next
run resumes from `src/` under **Resume, do not restart**.

## Module Subagents

S2 works without subagents. When the runtime has them, the parent may delegate one module at a time;
it keeps the kit, the bases, the contracts, the integration and the pause schedule.

- One subagent gets one module, its contract and its vectors. It implements the module, runs its
  unit, bottom-up and sandwich tests, and edits no file outside that module.
- It returns the changed files, every command it ran and pass/fail per test.
- Run modules in parallel only when their §2.2 dependencies are ready and their files do not
  overlap. Default concurrency is 1.

## Steps

Before step 1 of every iteration, ask the pause schedule as **Pause Schedule** says above.

1. **ML (future work).** If design §1.5 exists, stop before any code with exactly
   `ML integration is future work. Remove design §1.5 for this round.` and write no iteration.
2. **Initial layer: all placeholders before any module.** Create the trees and root manifests of
   `project_layout.md` for the design's `Toolchain`, lock dependencies (`uv lock`, `pnpm install`)
   and copy the logger to every service's `config/`. Build `verification/run.sh` and every tool of
   design §1.3.4 before any module: Mock HAL with its VL-0 vectors and VL-1 synthetic generator,
   golden vectors with `verification/golden/manifest.md`, the telemetry collector, one stub or fake
   peer per contract, drivers, and the Real HW HAL with a fake device API only in `mock+real`. Then
   build the base layer of each service and run its unit tests and the **top-down** test (base + all
   stubs) with the telemetry collector recording. Finally, run a **cross-service placeholder
   integration**: start every service with its stubs connected through the real inter-service
   interfaces and verify that the contract handshakes succeed end-to-end (types, formats, ports and
   protocols). No module code runs yet — this proves the interface scaffolding is sound before step 3
   invests in real implementations. A type or format mismatch at this point is a design defect.
3. **Modules in DAG order (§2.2).** Per module: implement against its contract, unit test, then the
   **bottom-up** test with a driver through the base, then the **sandwich** test (base → module →
   base: the real base calls the real module and the module calls back through the real base,
   verifying that types, formats and contracts match in both directions), then replace its stub.
4. **Services and paths.** Producer and consumer contract tests with fake peers, then the pause
   after cross-service integration, then each `PATH-*` with the real service processes and Mock HAL
   input.
   Implement §0.5 and write a VL-0 smoke test that starts the actual entry point, connects the
   real service processes, observes a valid update, and shuts down cleanly. Run the documented
   command with runtime dependencies only (`uv sync --frozen --no-dev` for Python). Keep the
   command, URL and observed result for `test_run.md`; do not touch `test_run.md` before step 6
   has backed up the previous one.
5. **VL-1 tests, written, not claimed.** For every module and `PATH-*` with `required_vl` VL-1 or
   higher, write a test fed by the Mock HAL synthetic generator that measures the metric against
   its `SYS-*` threshold, with the telemetry collector attached. Run them only to check they
   execute; never report their result as evidence. The VL-1 claim belongs to G2.
6. **Back up the last test run before overwriting it.** Run `codeanvil backup S2` from the project
   root. If it exits nonzero, stop and show its message; write no iteration. Cite the printed
   backup path in the iteration's Description. Backups never cover `src/` or `verification/`:
   code recovery relies on git.
7. **Floor run.** Run `verification/run.sh vl0`: the whole VL-0 suite with the telemetry collector
   attached. Fix failures (step 3) until it exits 0. Write `test_run.md`.
8. Write the iteration and return `S2 complete. Run the G2 skill.`

Rework, module defect: a G2 iteration with `Verdict: module defect` names the modules to fix,
including a missing VL-1 test. Redo step 3 (unit, bottom-up and sandwich) or 5 for them, then
steps 6 and 7.

Rework, design defect: a G2 iteration with `Verdict: design defect` routes through S1 and G1; S2
runs again only after G1 passes. Work from the latest G1 PASS iteration's impact map and go
bottom-up: revise the affected contract and its stub first, then the owning module (unit,
bottom-up, sandwich), then replace the stub. Preserve every module the impact map does not name.
Rerun the affected `PATH-*` and the changed VL-1 tests, then back up and run the full VL-0 floor
(steps 6 and 7). Record
in `S2.md` the changed IDs, files, commands, results and the G2 iteration it answers.

## Test Run Contract

Write `.codeanvil/report/<cycle-name>/S2_artifacts/test_run.md`, overwritten on every pass:

- the two commands G2 runs, exactly `verification/run.sh vl0` and `verification/run.sh vl1`;
- the last VL-0 run: command, exit code, passed, failed and skipped counts per service;
- the §0.5 runnable entry point, its smoke-test command and result, and the URL and visible
  behaviour a user should expect;
- the environment: OS, CPU, language and tool versions, `HAL mode`;
- the telemetry collector's summary for that run;
- `Possible infeasibility`: requirement IDs and the run that shows it, or `None`.

## Report Contract

Write exactly one file: `.codeanvil/report/<cycle-name>/S2.md`, append-only.

- First run: header plus `## Iteration 1`; later runs append `## Iteration <N>`.
- Header: a `| Field | Value |` table with `Gate` = `S2`, `Cycle`, `Document` (the `test_run.md`
  path) and `Created` = `codeanvil now`.
- Iteration: a `| Field | Value |` table with `Date` = `codeanvil now`, `Timestamp` =
  `codeanvil now --machine`, `Iteration`, `Cycle`, and exactly one row written as
  `| HITL | PASS |` or `| HITL | FEEDBACK |` (never both in one row, which `codeanvil status`
  reads as `UNKNOWN`). Then `### Description`.
- The Description starts with the exact line `Based on: G1 iteration <N>`, where `N` is the latest
  G1 iteration when the work starts, followed by the services built, the `test_run.md` path and,
  on rework, the G2 iteration it answers. A design defect adds the line `Verdict: design defect`
  and the S1 sections to rework.
- S2 is a **stage**: `PASS` means "delivered with VL-0 evidence" and needs a last
  `verification/run.sh vl0` that exited 0. The human verdict belongs to G2.

## Output Contract

Return the services built, the last VL-0 run counts, any `Possible infeasibility`, the report path
with the iteration number, and the next step (`S2 complete. Run the G2 skill.`), or the design
defect and `Run the S1 skill.`

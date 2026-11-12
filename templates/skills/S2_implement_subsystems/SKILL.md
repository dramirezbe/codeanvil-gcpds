---
name: s2-implement-subsystems
description: "Trigger: S2, implement subsystems, build the code, verification kit, VL-0. From a G1-passed design, build the subsystems and the verification kit, prove the VL-0 floor and write the VL-1 tests."
license: Apache-2.0
compatibility: "Telemetry is collected by the `codeanvil telemetry` subcommand, part of CodeAnvil itself (not a skill script). Reads the S1 design, .codeanvil/GT/SyRS.md and .codeanvil/project.yaml. Writes src/, verification/, root manifests, .codeanvil/report/<cycle-name>/S2.md and S2_artifacts/."
metadata:
  author: "gcpds"
  version: "1.1"
  gate: "S2"
  runtime: []
  pipeline: "V-SIL"
---

# S2 — Implement the Subsystems and the Verification Kit

Turn the G1-approved design into running code plus the verification kit, prove the VL-0 floor and
leave the VL-1 tests ready for G2. The Mock HAL and the kit let the agent test without real device
inputs. S2 runs locally; the real-hardware stage (VL-2) and any remote deployment belong to G2. A human judges at G2.

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

## Pre-S2 MCP Capability Analysis

Run once, after the prerequisites pass and before the pause schedule or any code. Read the approved
`.codeanvil/design/SDD.md` and decide which MCP servers the project needs. This is design-driven:
there is no default list.

| The SDD shows | Propose | Used for |
|---------------|---------|----------|
| RF / DSP / SDR design: measurands, methods, GNU Radio flows | `codeanvil mcp add marconi` | In S2 only (never in S1): generate a GNU Radio flowgraph `.grc` and its generated `.py` with few tokens, then adapt that output into the general `src/` code |
| VL-2 and an embedded-Linux `HWC-*` (Raspberry Pi, Jetson, other SBC) | `codeanvil mcp add vsil_hil_mcp` | At G2, for the real-hardware stage |

- Check which of these are already present (`codeanvil mcp list`). Present MCPs are skipped, so the
  step is idempotent; projects created with `--mcp` already have them. If none is needed or missing,
  continue to the pause schedule.
- Each `codeanvil mcp add` needs the user's **explicit authorization**; ask before running it.
- MCP tools load only when the agent session starts. After adding any MCP, tell the user to
  **restart the agent manually** and run the S2 skill again; stop without writing an iteration. The
  re-run finds the MCP present and proceeds. This is safe because `codeanvil status` is
  report-driven and stateless: the restart causes no error.
- If a needed MCP's system dependency is **missing** (for example gnuradio for `marconi`), help the
  user install it: research how for their OS and give the exact commands. Do not silently degrade.
  Hand-writing the RF/DSP code without GNU Radio is only **suggested**, and done only if the user
  explicitly asks.

## Inputs

| Path | Role |
|------|------|
| `.codeanvil/design/SDD.md` | Read-only: Meta `Target(s)`, `HAL mode` and `Toolchain`, §1.3.4 kit, §1.5, §1.6 HAL ladder, §1.7 telemetry per target, §2.2 order, §3 contracts and vectors, §4 traceability |
| `.codeanvil/project.yaml` | Read-only: the active cycle. No `targets:` exist yet — the remote target and its credentials are created later, at G2, by `credential-setup` |
| `.codeanvil/GT/SyRS.md` | Read-only: `SYS-*` thresholds for the VL-1 tests |
| `.codeanvil/report/<cycle-name>/G2.md` | Rework only: latest iteration with `Verdict: module defect` |
| `.codeanvil/report/<cycle-name>/G1.md` | Rework only: the latest PASS iteration's impact map (files to edit vs paths to retest only) |
| `templates/skills/S2_implement_subsystems/references/project_layout.md` | Locked trees: Python, TypeScript, root manifests, kit |
| `templates/skills/S2_implement_subsystems/references/logger.py` | Locked Python logger, copied unchanged |
| `templates/skills/S2_implement_subsystems/references/logger.ts` | Locked TypeScript logger, copied unchanged |
| `codeanvil telemetry` | Telemetry collector shipped with CodeAnvil, started by `verification/run.sh`; verification kit, never delivered |

## Hard Rules

- Implement only what the design declares, with the design's `Toolchain`; never choose another.
  A missing interface, an undeclared dependency, an incomplete contract or an empty or incomplete
  `Toolchain` is a **design defect**: write `| HITL | FEEDBACK |` with the line
  `Verdict: design defect` and the S1 sections to rework, then stop. Never edit the design or GT.
- Only Python with uv and pytest, and TypeScript with pnpm and vitest. No `requirements.txt`, no
  npm or yarn lockfile.
- Each subsystem is `src/<package>/`, exactly as `project_layout.md` shows.
- Delivered code never depends on the scaffolding tool. Copy `logger.py` to every Python subsystem's
  `config/logger.py` and `logger.ts` to every TypeScript subsystem's `config/logger.ts`, unchanged,
  and never edit them. The telemetry collector is the exception because it is kit, not delivered
  code: `run.sh` starts it as `codeanvil telemetry`, and only its JSONL readings land in `verification/telemetry/`. Every
  Python module logs with `log = get_logger(__name__)`; every TypeScript module with
  `getLogger("<package>.<module>")`. No `print`, no bare `console.log`.
- The kit is never shipped: no subsystem imports or depends on anything under `verification/`. Kit
  Python dependencies go only in the dev group, so `uv sync --frozen --no-dev` starts every
  subsystem without them; no subsystem `package.json` lists a kit package. The telemetry collector is
  mandatory in every test run and never lives under `src/`.
- Implement design §0.5 as a real system entry point. Every subsystem's package entry point starts
  its runtime loop, and a multi-subsystem launcher starts the complete system and stops its children.
  In `mock-only`, ship a runtime Mock HAL or explicit demo bundle; the only working entry point
  must not import the non-shipped verification kit. A command that only logs instructions fails S2.
- Expected values come from the design's §3 vectors and `verification/golden/manifest.md`, never
  computed by the agent. Changing a vector invalidates the evidence that used it.
- In `mock+real`, the Real HW HAL's VL-0 tests use the fake device API; S2 never needs the hardware.
- S2 runs locally. `Target(s)` is design intent (the device deduced from the `HWC-*` blocks, or
  `local`); a missing or ambiguous target intent, missing target envelope or contradictory subsystem
  placement is a **design defect**; stop rather than guess. Diagnose tool/environment faults as
  operational problems within scope; if they prevent testing, explain and pause rather than
  inventing a product defect. Different versions alone do not block delivery.
- Report only results of runs that actually happened, with their command.
- **Infeasibility is reported through G2.** S2 never runs the RFD skill. When a requirement looks
  unreachable on the declared COTS platform, record it in `test_run.md` under
  `Possible infeasibility` with the requirement IDs and the run that shows it, and finish the pass.
- **Resume, do not restart.** On a re-run, continue from what already exists in `src/` and
  `verification/`: re-run its tests, keep what passes, build what is missing. Never rewrite working
  code to start over.

## Execution (local)

S2 runs **locally**, through the runtime's normal tools: there is no remote deployment, enrollment
or real-hardware test at S2. `project.yaml` has no `targets:` yet — the remote target and its
credentials are created at G2 (`credential-setup`), and only if the design declares VL-2. In
`mock+real` the Real HW HAL is exercised only through its fake device API at VL-0; the actual
device, deployment and the pre-HW review belong to G2.

## Real HW HAL and VL-2 scripts (implemented at S2, run at G2)

In `mock+real`, **implement** the declared Real HW HAL — device/driver/capability observation,
unsupported-configuration checks and safe disconnect — and exercise its failure paths with the fake
device API at VL-0. S2 builds the code, never the measurement, and never touches the real device.
Never label synthetic or failed-device data as a real measurement.

**Write** `verification/run.sh vl2` and the measurement scripts that measure the GT metric — choose
tools and justify resolution against its tolerance — and record their arguments in `test_run.md`
for G2 to run. Functional HW tests need no universal oracle or calibration; when the requirement or
conclusion needs calibration/corrections, the script obtains those inputs or marks the affected
result inconclusive — never widen tolerances or invent readings. Preserve design vectors and golden
manifest governance. The vl2 script uses run ID `<cycle>_<iteration>_<codeanvil now --machine>` and
stores `<cycle>_<iteration>_<timestamp>.jsonl`, `measurement.json` v2 and script outputs under
`verification/telemetry/<run_id>/`, following this skill's locked
`templates/skills/S2_implement_subsystems/references/machine_evidence.md` and basic checker. **G2 runs
these scripts on the enrolled target**; S2 only implements them, and a required missing test returns
from G2 to S2 to implement it.

## Pause Schedule

Ask the pause schedule at the start of **every** iteration, before any code, with your runtime's
native question tool (`AskUserQuestion` in Claude Code): one single-select question in English, with
no option preselected.

| Option | Pauses |
|--------|--------|
| Per layer and module | Per subsystem: after the kit and its base, after each module and its tests, after integration |
| Per layer (recommended) | Per subsystem: after the kit and its base, once after all its modules, after integration |
| Per subsystem | Once after each completed subsystem |

Recommend **Per layer** in one line: it pauses where a wrong contract is cheapest to catch, without
one stop per module. In the Steps below, the kit and its base end step 2, the modules end step 3, and
the integration is the producer and consumer contract tests at the start of step 4. If the runtime
has no question tool, ask the same question in chat and wait for the reply; never assume or default
an answer. A rework asks again.

Every schedule adds one pause after cross-subsystem integration and before the `PATH-*` tests. At each
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
   and copy the logger to every subsystem's `config/`. Build `verification/run.sh` and every tool of
   design §1.3.4 before any module: Mock HAL with its VL-0 vectors and VL-1 synthetic generator,
   golden vectors with `verification/golden/manifest.md`, the telemetry collector, one stub or fake
   peer per contract, drivers, and the Real HW HAL with a fake device API only in `mock+real`. Then
   build the base layer of each subsystem and run its unit tests and the **top-down** test (base + all
   stubs) with the telemetry collector recording. Finally, run a **cross-subsystem placeholder
   integration**: start every subsystem with its stubs connected through the real inter-subsystem
   interfaces and verify that the contract handshakes succeed end-to-end (types, formats, ports and
   protocols). No module code runs yet — this proves the interface scaffolding is sound before step 3
   invests in real implementations. A type or format mismatch at this point is a design defect.
3. **Modules in DAG order (§2.2).** Per module: implement against its contract, unit test, then the
   **bottom-up** test with a driver through the base, then the **sandwich** test (base → module →
   base: the real base calls the real module and the module calls back through the real base,
   verifying that types, formats and contracts match in both directions), then replace its stub.
4. **Subsystems and paths.** Producer and consumer contract tests with fake peers, then the pause
   after cross-subsystem integration, then each `PATH-*` with the real subsystem processes and Mock HAL
   input.
   Implement §0.5 and write a VL-0 smoke test that starts the actual entry point, connects the
   real subsystem processes, observes a valid update, and shuts down cleanly. Run the documented
   command locally with the Mock HAL and runtime dependencies only (`uv sync --frozen --no-dev`
   for Python). Keep the command, URL and observed result for `test_run.md`; do not touch
   `test_run.md` before step 6 has backed up the previous one.
5. **VL-1 tests, written, not claimed.** For every module and `PATH-*` with `required_vl` VL-1 or
   higher, write a test fed by the Mock HAL synthetic generator that measures the metric against
   its `SYS-*` threshold, with the telemetry collector attached. Run them only to check they
   execute; never report their result as evidence. The VL-1 claim belongs to G2.
6. **Back up the last test run before overwriting it.** Run `codeanvil backup S2` from the project
   root. If it exits nonzero, stop and show its message; write no iteration. Cite the printed
   backup path in the iteration's Description. Backups never cover `src/` or `verification/`:
   code recovery relies on git.
7. **Floor run.** Run `verification/run.sh vl0` **locally**: the whole VL-0 suite with telemetry
   captured. Fix failures (step 3) and rerun. Investigate missing telemetry and decide whether
   affected measures need repetition; unaffected evidence may remain usable. Write `test_run.md`
   with the decision and last real run.
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

- exact `verification/run.sh vl0` and `verification/run.sh vl1` commands and, in `mock+real`, the
  `verification/run.sh vl2` command/scripts and structural-record checker that G2 will run;
- the local host OS, architecture and tool versions; the intended device (from the `HWC-*` blocks)
  and the capabilities the G2 real-hardware run will need;
- last VL-0 command, exit code and passed/failed/skipped counts per subsystem;
- §0.5 entry point, smoke command/result, URL and visible behaviour;
- actual run IDs, times and telemetry/script output paths;
- telemetry summary, any missing signals, investigated cause, affected claims and repeat/continue
  decision. A collector exit 0 does not certify full coverage; never use missing readings as zero.
  Readers may skip a torn final JSONL line with notice; earlier corruption needs investigation;
- `Possible infeasibility`: requirement IDs and the run showing it, or `None`.

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
  G1 iteration when the work starts, followed by the subsystems built, the `test_run.md` path and,
  on rework, the G2 iteration it answers. A design defect adds the line `Verdict: design defect`
  and the S1 sections to rework.
- S2 is a **stage**: `PASS` means "delivered with VL-0 evidence" and needs a last
  `verification/run.sh vl0` that exited 0. The human verdict belongs to G2.

## Output Contract

Return the subsystems built, the last VL-0 run counts, any `Possible infeasibility`, the report path
with the iteration number, and the next step (`S2 complete. Run the G2 skill.`), or the design
defect and `Run the S1 skill.`

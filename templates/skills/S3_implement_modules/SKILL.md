---
name: s3-implement-modules
description: "Trigger: S3, implement subsystems, build the code, verification kit, VL-0. From G2-approved scope plans, build the subsystems and the verification kit, prove the VL-0 floor and write the VL-1 tests."
license: Apache-2.0
compatibility: "Telemetry is collected by the `codeanvil telemetry` subcommand, part of CodeAnvil itself (not a skill script). Reads the S1 design, .codeanvil/GT/SyRS.md and .codeanvil/project.yaml. Writes src/, verification/, root manifests, .codeanvil/report/<cycle-name>/S3.md and S3_artifacts/."
metadata:
  author: "gcpds"
  version: "1.5"
  gate: "S3"
  runtime: []
  pipeline: "V-SIL"
---

# S3 — Implement the Subsystems and the Verification Kit

Implement the G2-approved scope plans as running code plus the verification kit, prove its VL-0 floor and
leave the VL-1 tests ready for G3. The Mock HAL and the kit let the agent test without real device
inputs. S3 runs locally; the real-hardware stage (VL-2) and any remote deployment belong to G3. A human judges at G3.

## Prerequisite and Cycle

Resolve the active cycle from `.codeanvil/project.yaml` (`cycle:`); if missing, ask the user.
If the latest iteration of `.codeanvil/report/<cycle-name>/RFD.md` holds a line
`Superseded by cycle: <name>`, this cycle is **closed** by an RFD and read-only: return exactly
`Cycle closed by RFD. Continue in cycle <name>.` and write nothing. Otherwise check, in this order,
writing **no iteration** when you stop:

1. Require latest G2 PASS for the selected S2 scope, else return exactly
   `G2 must pass first. Run the G2 skill.` Run `codeanvil custody verify --cycle <cycle> --gate G2`;
   stale inputs stop without an iteration. Compare G2 inputs to S2 outputs.
   Invalid upstream reports are repaired through their owning S2/G2 skills; S3 never appends
   replacement upstream verdicts itself. A metadata correction does not transfer a human PASS
   to a new delivery. Recheck custody after the required review before resuming code.
2. Own latest FEEDBACK with `Verdict: plan defect` requires a newer S2/G2 delivery.
   A design defect requires S1/G1 rework then S2/G2. Return the named prerequisite when missing.
3. Latest G3 `Verdict: RFD` returns `Cycle suspended by RFD. Run the RFD skill.` unless RFD was withdrawn.

## Pre-S3 MCP Capability Analysis

Run once on the first `slice 0`, after the prerequisites pass and before the pause schedule or any code. Read the approved
`.codeanvil/design/SDD.md` and decide which MCP servers the project needs. This is design-driven:
there is no default list.

| The SDD shows | Propose | Used for |
|---------------|---------|----------|
| RF / DSP / SDR design: measurands, methods, GNU Radio flows | `codeanvil mcp add marconi` | In S3 only (never in S1): generate a GNU Radio flowgraph `.grc` and its generated `.py` with few tokens, then adapt that output into the general `src/` code |
| VL-2 and an embedded-Linux `HWC-*` (Raspberry Pi, Jetson, other SBC) | `codeanvil mcp add vsil_hil_mcp` | At G3, for the real-hardware stage |

- Check which of these are already present (`codeanvil mcp list`). Present MCPs are skipped, so the
  step is idempotent; projects created with `--mcp` already have them. If none is needed or missing,
  continue to the pause schedule.
- Each `codeanvil mcp add` needs the user's **explicit authorization**; ask before running it.
- MCP tools load only when the agent session starts. After adding any MCP, tell the user to
  **restart the agent manually** and run the S3 skill again; stop without writing an iteration. The
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
| `.codeanvil/project.yaml` | Read-only: the active cycle. No `targets:` exist yet — the remote target and its credentials are created later, at G3, by `credential-setup` |
| `.codeanvil/plans/<SUB-xxx>/<module_id>/PLAN.md` | G2-approved immutable module plan and exact Context set |
| `.codeanvil/plans/INFRA-PLAN.md`, `INTEGRATION-PLAN.md` | Parent-owned slice 0/system plans, selected by Scope |
| `.codeanvil/GT/SyRS.md` | Read-only: `SYS-*` thresholds for the VL-1 tests |
| `.codeanvil/report/<cycle-name>/G3.md` | Rework only: latest iteration with `Verdict: module defect`; its `### Description` change list is the exact instruction |
| `.codeanvil/report/<cycle-name>/G1.md` | Rework only: the latest PASS iteration's impact map (files to edit vs paths to retest only) |
| `templates/skills/S3_implement_modules/references/project_layout.md` | Locked trees: Python, TypeScript, root manifests, kit |
| `templates/skills/S3_implement_modules/references/logger.py` | Locked Python logger, copied unchanged |
| `templates/skills/S3_implement_modules/references/logger.ts` | Locked TypeScript logger, copied unchanged |
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
- On `system`, implement design §0.5 as a real system entry point: package runtime loops,
  multi-subsystem launcher and clean child shutdown. In `mock-only`, ship a runtime Mock HAL
  or explicit demo bundle independent of the non-shipped verification kit. A command that only
  logs instructions fails S3. Earlier slices prove their own scope, not the final system.
- Treat G2-approved plans as immutable inputs. Only S2 may change a plan during authorized
  rework, followed by a new G2 review. Record implementation notes in S3.md, never in PLAN.md.
- Expected values come from the design's §3 vectors and `verification/golden/manifest.md`, never
  computed by the agent. Changing a vector invalidates the evidence that used it.
- In `mock+real`, the Real HW HAL's VL-0 tests use the fake device API; S3 never needs the hardware.
- S3 runs locally. `Target(s)` is design intent (the device deduced from the `HWC-*` blocks, or
  `local`); a missing or ambiguous target intent, missing target envelope or contradictory subsystem
  placement is a **design defect**; stop rather than guess. Diagnose tool/environment faults as
  operational problems within scope; if they prevent testing, explain and pause rather than
  inventing a product defect. Different versions alone do not block delivery.
- Report only results of runs that actually happened, with their command.
- **Infeasibility is reported through G3.** S3 never runs the RFD skill. When a requirement looks
  unreachable on the declared COTS platform, record it in `test_run.md` under
  `Possible infeasibility` with the requirement IDs and the run that shows it, and finish the pass.
- **Resume, do not restart.** On a re-run, continue from what already exists in `src/` and
  `verification/`: re-run its tests, keep what passes, build what is missing. Never rewrite working
  code to start over.

## Execution Continuity

After the pause schedule is selected, or a checkpoint receives `continue` or `rework`, execute
the authorized work **in the same turn** until the next scheduled pause, completion or a concrete
blocker. Progress updates do not end the turn: never return only a promise to continue, a summary
of files read or "implementation is not finished" while an authorized next action remains.
`Per module` is valid for `slice 0`: implement the parent-owned infrastructure and its checks
before its infrastructure checkpoint. Do not ask for a "compatible" replacement schedule or
pause before writing code merely because this scope implements no modules.

- Resume the same in-progress iteration with its selected schedule and answered checkpoints;
  do not ask for the same answer again or treat resumption as a new iteration. With **Per
  slice**, implement and check the authorized slice before pausing.
  The module-defect rework route still asks no pause-schedule question.
- Read the approved contract and its explicitly referenced normative schemas/annexes before
  declaring a design defect. Existing code that differs from an available, consistent contract
  is implementation work; correct it within the authorized scope. Do not invent a replacement
  schema, edit GT/design or leave "schema reconciliation pending" without identifying the issue.
- Before ending the turn, identify the boundary reached below. A status question during active
  work gets a brief update, then work continues unless the human explicitly pauses or redirects it.

| Boundary | Required action |
|----------|-----------------|
| Scheduled checkpoint or explicit human stop | Show completed scope and actual checks, preserve pending work and follow Pause Schedule. `continue` authorizes work to the next checkpoint, not HW or G3 acceptance. |
| S3 complete | Finish the floor run, backup and report contracts; only then return the completion message. |
| Missing or contradictory design contract | Name exact files, sections, fields and affected modules; append the design-defect FEEDBACK and route to S1 under Hard Rules. |
| Operational blocker, required permission/input/restart or runtime limit | Show the failed command/error or exact missing input, attempts made, affected scope and concrete action needed to resume. Apply the existing prerequisite/MCP/ML/backup rules where applicable; preserve work without a fabricated iteration or verdict. |

### Continuation responses and unblocking options

At a continuation checkpoint, trim surrounding whitespace and compare the whole reply without
case sensitivity: `continue`, `y`, `yes`, `ok` and `run` all mean `continue` (including `Y` and
`RUN`). Execute the already presented scope without asking for the literal word again. Record
the canonical `continue` checkpoint and preserve the original reply verbatim in its note.
Do not match substrings or treat a negated/conditional reply as unconditional authorization.
These replies do not select a pause schedule, waive a prerequisite or authorize HW/G3 acceptance.

For a blocker, offer one recommended concrete way forward and up to two useful alternatives,
with each option's action, scope and check for success. Repair an operational issue within
existing authorization directly; ask only for missing input, permission or a real choice.
A bare affirmative accepts a single clearly presented proposal; if several incompatible actions
remain possible, ask which one. For a missing contract, offer the required S1 rework or obtaining
the missing reference; never offer to guess the schema or bypass a gate. After the selected
action is authorized and the blocker resolved, resume to the next scheduled boundary.

## Execution (local)

S3 runs **locally**, through the runtime's normal tools: there is no remote deployment, enrollment
or real-hardware test at S3. `project.yaml` has no `targets:` yet — the remote target and its
credentials are created at G3 (`credential-setup`), and only if the design declares VL-2. In
`mock+real` the Real HW HAL is exercised only through its fake device API at VL-0; the actual
device, deployment and the pre-HW review belong to G3.

## Real HW HAL and VL-2 scripts (implemented at S3, run at G3)

In `mock+real`, **implement** the declared Real HW HAL — device/driver/capability observation,
unsupported-configuration checks and safe disconnect — and exercise its failure paths with the fake
device API at VL-0. S3 builds the code, never the measurement, and never touches the real device.
Never label synthetic or failed-device data as a real measurement.

**Write** `verification/run.sh vl2` and the measurement scripts that measure the GT metric — choose
tools and justify resolution against its tolerance — and record their arguments in `test_run.md`
for G3 to run. Functional HW tests need no universal oracle or calibration; when the requirement or
conclusion needs calibration/corrections, the script obtains those inputs or marks the affected
result inconclusive — never widen tolerances or invent readings. Preserve design vectors and golden
manifest governance. The vl2 script uses run ID `<cycle>_<iteration>_<codeanvil now --machine>` and
stores `<cycle>_<iteration>_<timestamp>.jsonl`, `measurement.json` v2 and script outputs under
`verification/telemetry/<run_id>/`, following this skill's locked
`templates/skills/S3_implement_modules/references/machine_evidence.md` and basic checker. **G3 runs
these scripts on the enrolled target**; S3 only implements them, and a required missing test returns
from G3 to S3 to implement it.

## Pause Schedule

Ask the pause schedule at the start of **every** iteration, before any code, with your runtime's
native question tool (`AskUserQuestion` in Claude Code): one single-select question in English, with
no option preselected.
Reuse a choice already supplied for the same in-progress iteration; selecting a schedule is
authorization to work to its first applicable checkpoint, not a checkpoint in itself.

| Option | Pauses |
|--------|--------|
| Per module | Pause after infrastructure, each completed module and integration |
| Per slice (recommended) | Pause after the completed slice |

Ask using the native question tool, or chat if unavailable; wait for an actual answer.
A module-defect rework follows G3's fixed change list without asking a new schedule.
If the runtime has no question tool, ask in chat and wait for the reply.

For `system` only, every schedule adds one pause after cross-subsystem integration and before the `PATH-*` tests.
Earlier scopes have no PATH checkpoint. Apply this scope matrix and the precise
[checkpoint procedure](references/pause_schedule.md); do not pause twice at one boundary:

| Scope | Per module | Per slice |
|-------|------------|-----------|
| slice 0 | After bases, kit, stubs, placeholder integration and the scope VL-0 checks; no module implementation or delegation | After the completed infrastructure slice and its checks |
| slice k (k >= 1) | After each approved module's implementation and prescribed checks; no repeated infrastructure pause | After all approved modules and the full built VL-0 floor |
| system | After cross-subsystem integration, before PATH tests; no invented module checkpoints | Before PATH tests and after completed system scope/checks |

At each
pause the human answers `continue`, `rework` or `stop`, through the same question tool or in chat
when it is unavailable.

- `continue`: go on to the next pause.
- `rework`: fix what the human names in the current layer or module, re-run its tests, then pause
  again.
- `stop`: write no iteration and return
  `S3 stopped at the human's request. Run the S3 skill to resume.`

Record every answer as a checkpoint line in the iteration's Description, never as a gate verdict:
`Checkpoint: <pause point> — <continue|rework|stop> — <note>`. A `stop` writes no `S3.md`; the next
run resumes from `src/` under **Resume, do not restart**.
After the final answered checkpoint, finish the remaining floor/evidence/report steps and hand
off to G3; do not restart the schedule or invent another confirmation before publication.

## Module Subagents — mandatory fresh context

For each module invoke `vsil-implementor` with only its PLAN.md and the exact Context set.
Never pass full GT, full SDD, other module source or S3 conversation history.
Without subagents, stop at a context handoff: run one fresh session per module and record
`Implementor: fresh session`. The current parent must not implement the module itself.
The parent owns bases, kit, manifests, integration, golden manifest and human checkpoints.
The implementor edits only the plan's declared module source, own tests and own stub.
Snapshot the working diff before delegation and inspect `git diff --name-only` plus untracked
files afterwards. Compare the incremental changed paths to the allowed set; out-of-scope
writes must be resolved before accepting the result. Never discard unrelated human edits.
Default concurrency is 1; parallel work is allowed only within a slice with disjoint files.
Collect changed paths, exact commands, exit codes, criteria and blockers per module.

## Scope execution

- `slice 0`: parent implements INFRA-PLAN.md (bases, kit, loggers, stubs and top-down
  placeholder integration). Run steps 1–2 and the scope's VL-0 checks; do not implement modules.
  Both pause options are admitted. No module implementor is required for this parent-owned work.
- `slice k`: delegate only the modules named in BACKLOG for k; run step 3 for each in fresh
  context, inspect write scope, then full `verification/run.sh vl0`. Do not implement future slices.
  Within step 3 also write and exercise the current module's VL-1 tests (when required) and
  prepare its VL-2 scripts using the fake device API. Do not defer these to system scope;
  development runs only check executability, and G3 supplies independent evidence.
- `system`: parent implements INTEGRATION-PLAN.md, cross-subsystem contract tests, PATH-* tests,
  root entry point and smoke, VL-1 paths (steps 4–5). Keep the pause before PATH-*.
- All scopes back up S3 artifacts, update test_run.md for the current scope and record only
  actual execution evidence. A missing/incoherent plan is `Verdict: plan defect` → S2;
  missing interfaces/contracts are `Verdict: design defect` → S1.
- S3 never changes a reviewed plan, GT or SDD. Record
  `Proposed delta: <type> <target> — <reason>` for G3. The parent writes returned implementation
  notes in S3.md (module ID, changed paths, commands/results and deviations), outside the plan.

## Steps

Execute only the steps selected by Scope execution above. Before work, resolve the pause schedule
as **Pause Schedule** says above; retain an already answered choice on resume.

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
5. **System VL-1 tests, written, not claimed.** Write the contract and `PATH-*` tests required
   by INTEGRATION-PLAN.md, measuring each declared `SYS-*` threshold with telemetry.
   Module-level VL-1 tests were already delivered in their module slices under step 3.
   Run these development checks only to prove executability; the VL-1 claim belongs to G3.
6. **Back up the last test run before overwriting it.** Run `codeanvil backup S3` from the project
   root. If it exits nonzero, stop and show its message; write no iteration. Cite the printed
   backup path in the iteration's Description. Backups never cover `src/` or `verification/`:
   code recovery relies on git.
7. **Floor run.** Run `verification/run.sh vl0` **locally**: the whole VL-0 suite with telemetry
   captured. Fix failures (step 3) and rerun. Investigate missing telemetry and decide whether
   affected measures need repetition; unaffected evidence may remain usable. Write `test_run.md`
   with the decision and last real run.
8. Write the iteration and return `S3 complete. Run the G3 skill.`

The same parent agent resumes S3 using the recorded reasons, evidence and correction
suggestions in the source feedback's `### Description`; it is the rework input, not
a request for the user to restate the task. Preserve fresh per-module implementation
contexts and the approved plan/allowed-path boundaries.

Rework, module defect: read the change list in the latest `G3.md` iteration's `### Description`
(the enumerated items after its `Based on:` line) and apply exactly those changes — only the
subsystems/modules/files it names — then re-run the affected tests. Do not ask the human and do not
redesign; the G3 report Description is the instruction. The listed modules are the ones to fix,
including a missing VL-1 test: redo step 3 (unit, bottom-up and sandwich) or 5 for them, then
steps 6 and 7. This route does **not** ask the Pause Schedule — the change set is fixed by the G3
Description, so there is nothing to interrogate.

Rework, design defect: a G3 iteration with `Verdict: design defect` routes through S1 and G1; S3
runs again only after G1 and the reworked S2/G2 pass. Work from the latest G1 PASS iteration's impact map and go
bottom-up: revise the affected contract and its stub first, then the owning module (unit,
bottom-up, sandwich), then replace the stub. Preserve every module the impact map does not name.
Rerun the affected `PATH-*` and the changed VL-1 tests, then back up and run the full VL-0 floor
(steps 6 and 7). Record
in `S3.md` the changed IDs, files, commands, results and the G3 iteration it answers.

## Test Run Contract

Write `.codeanvil/report/<cycle-name>/S3_artifacts/test_run.md`, overwritten on every pass:

- Scope and built module list; exact `verification/run.sh vl0` command for the full built floor;
- Exact `verification/run.sh vl1` and (when declared) `verification/run.sh vl2` commands,
  module selectors, criteria and expected results only for levels declared
  for this scope; earlier module evidence is linked by G3 iteration. Do not require future paths
  or unimplemented modules. In `mock+real`, include reviewed HW scripts/structural checker;
- the local host OS, architecture and tool versions; the intended device (from the `HWC-*` blocks)
  and the capabilities the G3 real-hardware run will need;
- last VL-0 command, exit code and passed/failed/skipped counts per subsystem;
- `slice 0`: base/stub startup and contract-handshake smoke, with no claim of a complete system;
  `slice k`: built-module regression and its module acceptance tests, no future PATH-* requirement;
  `system`: §0.5 entry point, smoke command/result, URL, visible behaviour and clean shutdown;
- actual run IDs, times and telemetry/script output paths;
- telemetry summary, any missing signals, investigated cause, affected claims and repeat/continue
  decision. A collector exit 0 does not certify full coverage; never use missing readings as zero.
  Readers may skip a torn final JSONL line with notice; earlier corruption needs investigation;
- `Possible infeasibility`: requirement IDs and the run showing it, or `None`.

## Report Contract

Write exactly one file: `.codeanvil/report/<cycle-name>/S3.md`, append-only.

- First run: header plus `## Iteration 1`; later runs append `## Iteration <N>`.
- Header: a `| Field | Value |` table with `Gate` = `S3`, `Cycle`, `Document` (the `test_run.md`
  path) and `Created` = `codeanvil now`.
- Iteration: a `| Field | Value |` table with `Date` = `codeanvil now`, `Timestamp` =
  `codeanvil now --machine`, `Iteration`, `Cycle`, and exactly one row written as
  `| HITL | PASS |` or `| HITL | FEEDBACK |` (never both in one row, which `codeanvil status`
  reads as `UNKNOWN`). Then `### Description`.
- The Description starts with the exact line `Based on: G2 iteration <N>`, where `N` is the latest
  G2 iteration when the work starts, followed by the subsystems built, the `test_run.md` path and,
  on rework, the G3 iteration it answers. A design defect adds the line `Verdict: design defect`
  and the S1 sections to rework.
- S3 is a **stage**: `PASS` means "delivered with VL-0 evidence" and needs a last
  `verification/run.sh vl0` that exited 0. The human verdict belongs to G3.

## Output Contract

Return the subsystems built, the last VL-0 run counts, any `Possible infeasibility`, the report path
with the iteration number, and the next step (`S3 complete. Run the G3 skill.`), or the design
defect and `Run the S1 skill.`

## Scope evidence additions

Description starts with Based on G2, then `Scope: slice <k>` or `Scope: system`.
Record Input lines for each immutable scope plan, Output lines for delivered source/kit
and `.codeanvil/report/<cycle>/S3_artifacts/test_run.md`,
and `Implementor: <SUB/module> — <subagent | fresh session>` per module.
`test_run.md` includes Scope and per-module command/criteria rows, plus Possible infeasibility.
All digests and golden manifest cells come from `codeanvil custody digest`, pasted verbatim.
Before and after this delivery run `codeanvil custody verify --cycle <cycle> --gate G2`.
Do not use full-cycle verify as a delivery gate: the previous G3's source/kit inputs describe
an earlier slice and legitimately differ after implementation. Global verify remains a diagnostic;
it must still disclose those mismatches. G3 compares this delivery's Output lines to current files.
Have run.sh execute
`codeanvil custody verify-manifest verification/golden/manifest.md` before every test level.

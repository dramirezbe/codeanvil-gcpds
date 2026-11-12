---
name: s2-implement-services
description: "Trigger: S2, implement services, build the code, verification kit, VL-0. From a G1-passed design, build the services and the verification kit, prove the VL-0 floor and write the VL-1 tests."
license: Apache-2.0
compatibility: "Telemetry is collected by the `codeanvil telemetry` subcommand, part of CodeAnvil itself (not a skill script). Reads the S1 design, .codeanvil/GT/SyRS.md and .codeanvil/project.yaml. Writes src/, verification/, root manifests, .codeanvil/report/<cycle-name>/S2.md and S2_artifacts/."
metadata:
  author: "gcpds"
  version: "1.1"
  gate: "S2"
  runtime: []
  pipeline: "V-SIL"
---

# S2 — Implement the Services and the Verification Kit

Turn the G1-approved design into running code plus the verification kit, prove the VL-0 floor and
leave the VL-1 tests ready for G2. The Mock HAL and the kit let the agent test without real device
inputs. It runs locally or on the declared remote compute unit (PIL). A human judges at G2.

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
| `.codeanvil/design/SDD.md` | Read-only: Meta `Target(s)`, `HAL mode` and `Toolchain`, §1.3.4 kit, §1.5, §1.6 HAL ladder, §1.7 telemetry per target, §2.2 order, §3 contracts and vectors, §4 traceability |
| `.codeanvil/project.yaml` | Read-only: declared `targets:` and the active cycle; credentials stay with the MCP custodian |
| `.codeanvil/GT/SyRS.md` | Read-only: `SYS-*` thresholds for the VL-1 tests |
| `.codeanvil/report/<cycle-name>/G2.md` | Rework only: latest iteration with `Verdict: module defect` |
| `.codeanvil/report/<cycle-name>/G1.md` | Rework only: the latest PASS iteration's impact map (files to edit vs paths to retest only) |
| `templates/skills/S2_implement_services/references/project_layout.md` | Locked trees: Python, TypeScript, root manifests, kit |
| `templates/skills/S2_implement_services/references/logger.py` | Locked Python logger, copied unchanged |
| `templates/skills/S2_implement_services/references/logger.ts` | Locked TypeScript logger, copied unchanged |
| `codeanvil telemetry` | Telemetry collector shipped with CodeAnvil, started by `verification/run.sh`; verification kit, never delivered |

## Hard Rules

- Implement only what the design declares, with the design's `Toolchain`; never choose another.
  A missing interface, an undeclared dependency, an incomplete contract or an empty or incomplete
  `Toolchain` is a **design defect**: write `| HITL | FEEDBACK |` with the line
  `Verdict: design defect` and the S1 sections to rework, then stop. Never edit the design or GT.
- Only Python with uv and pytest, and TypeScript with pnpm and vitest. No `requirements.txt`, no
  npm or yarn lockfile.
- Each service is `src/<package>/`, exactly as `project_layout.md` shows.
- Delivered code never depends on the scaffolding tool. Copy `logger.py` to every Python service's
  `config/logger.py` and `logger.ts` to every TypeScript service's `config/logger.ts`, unchanged,
  and never edit them. The telemetry collector is the exception because it is kit, not delivered
  code: `run.sh` starts it as `codeanvil telemetry`, and only its JSONL readings land in `verification/telemetry/`. Every
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
- Follow design `Target(s)` and the execution contract below. A missing or ambiguous target,
  missing target envelope or contradictory service placement is a **design defect**; stop rather
  than substitute the developer host. A connection, deployment or version failure is a setup
  blocker: show it, keep working files and write no delivered PASS until it is resolved.
- Report only results of runs that actually happened, with their command.
- **Infeasibility is reported through G2.** S2 never runs the RFD skill. When a requirement looks
  unreachable on the declared COTS platform, record it in `test_run.md` under
  `Possible infeasibility` with the requirement IDs and the run that shows it, and finish the pass.
- **Resume, do not restart.** On a re-run, continue from what already exists in `src/` and
  `verification/`: re-run its tests, keep what passes, build what is missing. Never rewrite working
  code to start over.

## Execution target and deployment

No `targets:` means **local** execution through the runtime's normal tools. Otherwise select the
named target(s) from the approved SDD; a sole declared target may be implicit, several require
explicit names on every MCP call. Remote VL-0/VL-1 remain **VERIFIED (PIL)** with Mock HAL inputs,
even in `mock-only`; executing on the real processor is not real-RF or VL-2 validation.

Deployment identity is required for remote PIL **or any planned VL-2 capture**, including local
PC-to-device HIL with no `targets:` block. Local VL-0/VL-1 alone do not require a manifest. For
local VL-2 use target name `local` and the observed host CodeAnvil version; generate/test the
checker, record the clean input revision and generate the manifest as in steps 3–4 below. Run
the same pre/post identity checks locally, without `code_sync`, SSH or MCP. The capture record's
expected deployment digest is the host manifest SHA-256, exactly as for a remote capture.

For each remote target, S2 prepares the complete deployment before G2:

1. Read host, user, port (default 22), workspace, OS, architecture and device from the declaration.
   Use `vsil_hil_mcp` tools only; never read private keys or issue a parallel direct SSH command.
   Missing access requires the human bootstrap path, never autonomous enrollment.
2. Call `probe_target(target="<name>")` and record the observed OS, architecture and CodeAnvil
   version; require exit 0 and `metadata.version_match: true`. Its expected version must match
   the host version. A declared device or optional USB enumeration is not a HAL capability probe.
   Record actual values; missing or unequal
   versions block delivery. Project dependencies belong in the target project environment,
   including kit dev dependencies for verification, separate from the CodeAnvil runtime.
3. Finish code and kit changes, including generating and testing
   `verification/check_deployment.py`, then record the clean git revision of the delivered source
   and kit inputs (commit only with the user's authorization). Reports and telemetry generated by
   the run are not part of that input revision. If no committed input baseline is available,
   report the gap and do not claim a reproducible remote delivery.
4. Build `verification/deployment_manifest.json` against that final revision as specified in
   `project_layout.md`; record the SHA-256 of the manifest in `test_run.md`. Do not create or edit
   the checker after taking this baseline.
   `code_sync(target="<name>")` deploys this baseline; it must succeed before running anything.
5. Through `ssh_exec_cmd`, run the exact preflight and level commands from the target workspace.
   The preflight checks the deployed input hashes and must exit 0. Then run
   `verification/run.sh vl0` with telemetry on that compute unit and `fetch_evidence` afterward.
   Remote fetches return `local_path`, a new host snapshot under
   `verification/telemetry/<target>/fetch-<unique>/`; record and use that path rather than
   constructing a destination. Local files stay directly in `verification/telemetry/`. Match
   only this run's evidence within the snapshot; it may include older remote files. Do not mix
   their readings. Recompute the manifest and redeploy
   after any input change; G2 is given the final deployed baseline and never repairs it.

Privileged setup uses `ssh_exec_cmd_trusted` only with authorization under the host runtime's
permission policy. A distinct tool name alone does not guarantee an approval prompt. Never
smuggle privileged work inside a script to evade that policy.

## Real HW capture (conditional VL-2)

In `mock+real`, implement the SDD's Real HW HAL, its non-transmitting identity/driver/capability
probe, capability checks before configuration/acquisition and safe disconnect. Test unsupported
requests and probe/driver failures through the fake device API at VL-0. Never replace a device
failure with synthetic data labelled as real.

Only when the GT supplies the oracle, `PROTO-*`, correction chains and uncertainty/tolerance
budgets, implement `verification/run.sh vl2 --run-id <id>` and record its exact arguments in
`test_run.md`. It writes exclusive per-run `verification/telemetry/<run-id>/measurement.json`,
telemetry and checksummed capture/probe files according to G2's machine-evidence contract:
`templates/skills/S2_implement_services/references/machine_evidence.md` (locked shared assets
copied into this skill by the scaffold). Refuse an existing
run ID; a failed capture cannot be overwritten into passing evidence. If lab prerequisites are
missing, VL-2 remains blocked; do not fill placeholders or invent a reference.

S2 prepares the command and authorization requirements, including RF/TX consequences, rather
than silently running real hardware. A human or authorized operator performs the capture.
G2 requests a separate fresh run and validates its record; S2's development capture is not G2
evidence. Record the exact host validator command with expected target, run ID, deployment
digest, version and host request timestamp (`--not-before`), resolved from G2's capture request.

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
7. **Floor run.** Run `verification/run.sh vl0` on each designed execution target: the whole VL-0
   suite with telemetry captured there. For remote execution follow **Execution target and
   deployment** first and fetch the evidence. Fix failures (step 3), redeploy changed inputs and
   rerun until exit 0 with usable telemetry. Write `test_run.md`.
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

- the level commands G2 runs, exactly `verification/run.sh vl0` and `verification/run.sh vl1`;
  remote records also give the named MCP target, exact `cd <workspace> && <command>` payloads,
  read-only version/OS/architecture probes and the deployment preflight:
  `python3 verification/check_deployment.py --expected <manifest-SHA256>`;
  list `probe_target` as the remote metadata preflight. In `mock+real`, also give the conditional
  VL-2 operator command and host record-validation command; these do not authorize the fresh
  verifier to touch real device inputs;
- a target block per execution target: local/remote, name, host, user, port, workspace, observed
  OS and architecture, declared device, host and target CodeAnvil versions and their parity;
  local records name the actual host rather than filling remote fields with invented values;
- for remote PIL or planned VL-2 (including local): clean delivered git revision, manifest path
  and SHA-256, selected input roots and preflight results; remote records additionally include
  successful sync. Give exact per-run telemetry paths and hashes in either case;
- the last VL-0 run: command, exit code, passed, failed and skipped counts per service;
- the §0.5 runnable entry point, its smoke-test command and result, and the URL and visible
  behaviour a user should expect;
- the environment: OS, CPU, language and tool versions, `HAL mode`;
- the telemetry collector's summary for that run, marking missing, empty or corrupt evidence
  `unavailable`. A collector exit 0 does not prove evidence exists. JSONL readers may skip only
  a torn final line and must disclose it; earlier corruption or unavailable required signals
  cannot support an in-envelope result;
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

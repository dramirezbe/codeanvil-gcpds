# T3 OpenCode S1/G1 review holdout — 2026-11-05

This is the central record of the T3 OpenCode test observations across S1,
G1, S2 and G2. It stays in the CodeAnvil source repository, outside the
scaffolded test project, so the G2 verifier did not receive the earlier
review as context.

## Methodology outcome

The G2 → S1 design-defect route is defined, but S2 needs a bounded method for
changing code that already exists. The proposed method is recorded below under
**“Proposal: bounded code rework after a design change”**: preserve the old
design, describe the change by stable IDs, review its impact, update only the
affected modules and contracts, then rerun affected paths and the full VL-0
floor. It remains a proposal until the S1, G1, S2 and G2 skills enforce it.
The G2 audit also motivates a ready-to-use telemetry collector, described at
the end of this report, so S2 does not have to invent one for each project.

## Baseline

- Test project: `/home/javastral/GIT/UNAL/sandbox-vsil-opencode.QhpdEN/fm_occupancy_mock`
- Cycle: `01_fm_occupancy_mock`
- S1: iteration 1, `HITL: PASS` (delivered)
- G1: iteration 1, `HITL: PASS`, human answer `PASS` by D. Ramírez
- The human verdict is recorded correctly. The findings below concern the
  design and the completeness of the agent's review.

| Artifact in test project | SHA-256 at review |
|--------------------------|------------------|
| `GT/G0_StRS.md` | `f98de6b36c6139926e22755f79768697579a1314333257e8d94f78f5c90c07b1` |
| `GT/G0_SyRS.md` | `0ad3d83c46e129725ce81ee54c526a73b7e888337e6305430c1881a8aeb1fd35` |
| `.codeanvil/report/01_fm_occupancy_mock/S1_artifacts/S1_design.md` | `8e38efcc09e23322b6c8650ccf34e8d0d67ba709c8048c2fa5e15f264b37b89c` |
| `.codeanvil/report/01_fm_occupancy_mock/S1_artifacts/S1_graph.html` | `6420deddbccb785fb21922450ee4fe89a675194f2acba322904b99f2982920fe` |
| `.codeanvil/report/01_fm_occupancy_mock/G1.md` | `06c55c910e90ebe77558992d2e0a26ac2be3b243f53c565423eac60e7c268a66` |

## Findings to compare

### F1 — Hardware is absent from the review graph

`S1_design.md:25-30` lists HW-001 through HW-004. `S1_graph.html:49` sets
`const hardware = []`, so the interactive graph omits all four devices.
`G1_CHECKLIST.md:12` calls a missing device an **open** finding, but `G1.md:30`
marks the graph `ok`. G2 verifies delivered software; graph completeness belongs
to G1 and is outside G2's required checks.

### F2 — HAL output type conflicts with the capture contract

`S1_design.md:127` defines `HalFrame.samples` as `np.ndarray[complex64]`.
`S1_design.md:189-190` says `capture` receives raw uint8 I/Q and converts it;
`S1_design.md:425-428` defines `iq_stream.v1` as interleaved uint8 bytes.
`GT/G0_SyRS.md:177-190` requires that conversion. One interface cannot provide
both types as written. G2 can expose this only if the S2 implementation or its
tests exercise the HAL-to-capture boundary and report the contradiction.

### F3 — Continuous capture has no explicit update-window policy

`S1_design.md:116-118` and `:127` say one 65,536-sample frame arrives every
0.5 s. `S1_design.md:426-428` also claims continuous capture at 2.4 MS/s.
That rate produces 1,200,000 samples per 0.5 s. The design does not say how
the stream is drained, buffered, or reduced to the 65,536 samples used for an
update. `GT/G0_StRS.md:418-432` describes a rate without dropped samples.
G2 can expose the gap only if `verification/run.sh` tests full-rate production,
window selection, and loss accounting; a Mock HAL that emits only 65,536
samples per 0.5 s cannot test it.

### F4 — G1 claims a VL-0 latency path that is not declared

`G1_CHECKLIST.md:22` asks for a VL-0 connected-process test for each
cross-service SYS requirement. `S1_design.md:648` assigns the latency
requirement `SYS-QOS-001` to PATH-004 at VL-1 only. `G1.md:40` says VL-0
connected-process tests exist for all paths. G2 follows the declared path
levels and is not required to repeat G1's checklist.

### F5 — G1 misclassified the declined TypeScript tool install

`G1_CHECKLIST.md:26` and the G1 skill's toolchain step require an **open**
finding when a missing tool's installation is refused. The user declined a
global `tsc` installation; `G1.md:44` records the missing compiler as an
advisory while marking G1.14 `pass`. A project-local TypeScript dev dependency
may be sufficient for S2, but the current G1 rule does not say that. This is a
G1 process and rule-design issue, not an expected G2 detection.

## Scoring rule for the G2 comparison

For each finding, record whether S2 resolved it, G2 independently identified
it, or it remained latent. Use the S2 `test_run.md`, the fresh G2 console
result, and the G2 report as evidence. Count a G2 detection only when G2 names
the root cause or a test fails on that cause without receiving this review.
Do not score F1, F4, or F5 as G2 misses: they are outside G2's required scope.
F2 and F3 are conditional checks because G2 runs only the tests supplied by S2.

## G2 comparison — 2026-11-05

OpenCode's independent G2 run reported 17 VL-0 and 10 VL-1 tests passing and
recommended `PASS`. It named none of F1–F5 before the human supplied the review
findings in chat. After the human initially chose `RFD`, the agent correctly
explained that these are remediable design and review defects, then recorded
`FEEDBACK` with `Verdict: design defect` in G2 iteration 1. The report repeats
the supplied findings; this is **human detection with correct routing**, not an
independent G2 detection.

| Finding | Outcome at G2 |
|---------|---------------|
| F1 graph | Repeated after human feedback. Remains a G1 review miss. |
| F2 HAL type | Repeated after human feedback. The Mock HAL converts uint8 to complex64 before yielding a `HalFrame`; `run_pipeline` consumes complex64 directly. The `capture` conversion function is tested separately, so the design's raw-byte capture boundary remains unresolved. |
| F3 capture buffering | Repeated after human feedback. The generator emits exactly 65,536 samples per update and the pipeline has no full-rate buffering or selection policy. The tests do not exercise 1,200,000 samples per 0.5 s. |
| F4 VL-0 latency claim | A nominal VL-0 PATH-004 test was added, but it asserts hardcoded 20/5/30 ms values and separately times only DSP processing. It does not measure connected-process or end-to-end latency. |
| F5 TypeScript tool | S2 installed TypeScript as a project dev dependency, so compilation is available. G1's earlier classification remains inaccurate under its current rule. |

### Additional G2 misses found while comparing evidence

- **Declared VL-1 paths lack corresponding VL-1 tests.** PATH-002 and PATH-004
  are declared VL-1 in the S1 design and G2 report. The six Python VL-1 tests
  cover detector scenes; the four TypeScript VL-1 tests cover jsdom rendering.
  No VL-1 test runs PATH-002 across both services or measures PATH-004's 60 s
  p95 latency. The G2 skill's hard rule says a declared VL-1 path with no VL-1
  test is a module defect routed to S2, yet G2 marked both paths `pass`.
- **Dropped-buffer and scheduling readings are synthetic.**
  `verification/telemetry/telemetry.py:67-68` writes `dropped = 0` and
  `sched_ms = 0.0` on every sample; `verification/run.sh:70` also prints
  `dropped: 0` unconditionally. G2 reported dropped buffers as measured and
  in envelope. Its `N/A` for WSL2 temperature is appropriately qualified.
- **The FEEDBACK route is right, but the rework pointers are wrong.**
  `G2.md:97-99` calls the HAL ladder §1.5 and the module table §1.6.
  In the design they are §1.6 and §1.4, respectively. The G2 report also
  omits the human answer verbatim, which its skill requires.

Evidence inspected: test project `.codeanvil/report/01_fm_occupancy_mock/G2.md`,
`S2_artifacts/test_run.md`, `verification/fm_edge/test/test_paths.py`,
`verification/fm_edge/test/test_vl1.py`, `verification/dashboard/test/vl1.test.ts`,
`verification/fm_edge/mock_hal/hal.py`, `verification/fm_edge/mock_hal/generator.py`,
`src/fm_edge/main.py`, and the telemetry files above. This comparison is
read-only with respect to the test project.

## S2 workflow observation and questions — 2026-11-05

Status: design notes only; no S2 skill change has been made. The user observed
that S2 delivered two services, seven modules and the verification kit in one
uninterrupted execution, and is not confident that every required step ran.
`S2.md` lists the final artifacts and VL-0 result, but does not record separate
evidence for the kit and base, the top-down test, unit and bottom-up tests per
module, stub replacement, or integration of each `PATH-*`. This does **not**
prove those steps were skipped; the session trace and artifacts need an audit.

The current S2 skill requires this order: kit and base first; modules in DAG
order, each with unit and bottom-up tests before stub replacement; service
contracts and paths; VL-1 tests for declared modules and paths; then the final
VL-0 run. The test showed a need for visible checkpoints during that sequence.

### Proposed question at S2 start

**«¿Con qué frecuencia quieres que S2 pause para revisar el avance?»**

| Option | Proposed pauses |
|--------|-----------------|
| Entre capas y por módulo | For each service: after the kit and base, after every module and its tests, and after integration. |
| Entre capas | For each service: after the kit and base, once after all its modules and tests, and after integration. |
| Por servicio | Once after each completed service, including its base, modules and internal tests. |

These are S2 review points, not new `HITL: PASS` gate verdicts. Cross-service
integration and `PATH-*` can be completed only after their participating
services exist. The shared kit should be built once even if pauses repeat for
each service.

### Proposed subagent granularity

Organize optional implementation subagents around **modules**, rather than
whole services. The parent agent owns the shared kit, bases, contracts,
integration, and selected pause schedule. A module subagent receives one
module and its contract, implements it, runs its unit and bottom-up tests, and
returns the evidence. Parallel work is limited to modules whose DAG
dependencies are ready and whose files do not overlap. S2 must also work in a
runtime without subagents.

### Questions to decide before changing S2

1. Which of the three pause schedules should be recommended by default?
2. Is the schedule selected once per S2 cycle, or again on each rework?
3. At a pause, does the user choose `continue`, `rework`, or `stop`; where is
   that recorded without adding a new gate?
4. Does each service's “integration” mean internal integration only, with an
   additional pause for cross-service integration and `PATH-*`?
5. How many module subagents may run concurrently, and what minimum evidence
   must each return before S2 advances?

## Forced G2 feedback to S1 — route check

The human chose `FEEDBACK (design defect)` after G2's tests passed. This is a
valid G2 verdict: the human decides the gate. The cycle remains
`01_fm_occupancy_mock`; no RFD was recorded. Immediately afterward,
`codeanvil status` showed S1 delivered at iteration 1, G1 PASS at iteration 1,
S2 delivered at iteration 1, and G2 FEEDBACK at iteration 1.

The intended re-entry in the **same cycle** is S1 iteration 2 (rewrite design
and graph from the G2 findings), G1 iteration 2 (new human review), S2
iteration 2 (update code and evidence for the new design), then G2 iteration 2
(fresh verification and human verdict). G0 stays at PASS if the GT pair is
unchanged. `codeanvil status` marks downstream reports stale by comparing each
`Based on: <gate> iteration <N>` link with its predecessor's latest iteration;
it does not reset earlier verdicts automatically.

The skills express this route, but two instructions make it fragile:

- G2's decision table routes `FEEDBACK` with `Verdict: design defect` to S1,
  while its prerequisite check for a repeated G2 call says `S2 must rework
  first` for **any** unchanged G2 FEEDBACK. This gives the wrong immediate
  instruction for a design defect.
- S2's explicit rework paragraph covers G2 `module defect`, but does not
  explicitly say how to propagate a revised S1 design after G1 passes again.
  G2 will block while S2 is stale, yet the S2 agent needs a clear requirement
  to reconcile the new design with code, tests and `test_run.md` before
  appending S2 iteration 2.

The G2 report also names the wrong S1 sections for two findings (HAL ladder is
§1.6, module cards are §1.4) and writes `Verdict: design defect` as a Markdown
heading rather than a standalone line. These do not change the human verdict,
but can misdirect or weaken exact-text re-entry.

## Proposal: bounded code rework after a design change

The current S2 instruction, “resume, do not restart,” protects existing code
but does not tell the agent **which** files to change after S1 revises the
design. A controlled return needs a change set and an impact map before S2
edits code. This is a methodology proposal, not yet implemented in the skills.

1. **Preserve the prior baseline.** Before S1 overwrites `S1_design.md` and
   `S1_graph.html`, keep an immutable copy keyed by S1 iteration and record
   its digests. The existing S1 skill overwrites both artifacts, so it cannot
   otherwise produce a reliable old-versus-new comparison in a project without
   Git history.
2. **S1 emits a design change set.** For each changed `SYS-*`, contract,
   service, module or `PATH-*` ID, record the old and new decision, the reason,
   and whether an interface changed. Keep stable IDs for unchanged elements.
   A graph-only correction is explicitly marked as having no code impact.
3. **G1 reviews the change set and its impact map.** Trace changed contracts
   to producers, consumers, stubs and tests; follow the §2.2 DAG to identify
   downstream regression tests. Distinguish files that must be edited from
   paths that only need to be retested. An unexplained impact is an open G1
   finding.
4. **S2 updates one bounded work unit at a time.** First revise the affected
   contract and stub or fake peer. Then update the owning module, run its unit
   and bottom-up tests, and replace the stub. A module subagent owns only that
   module's files and evidence. Producer and consumer changes meet at the
   integration step; the parent agent resolves shared files. Preserve
   unaffected modules and passing tests.
5. **Close the evidence.** Rerun affected `PATH-*` tests and every changed
   VL-1 test, then the complete VL-0 floor. S2 iteration 2 records changed
   IDs, files, commands and results, plus the G2 feedback it answers. G2
   verifies from a fresh context and checks that each declared path has its
   required test before another human verdict.

For this T3 case, the missing hardware nodes change only the S1 graph. The
HAL type decision affects `hal_port`, capture, the Mock HAL, their contract
tests and dependent paths. The full-rate window policy affects capture,
buffering, Mock HAL timing, dropped-buffer telemetry and latency evidence.
The TypeScript tool classification is a G1 review-rule issue. This map limits
code edits while still requiring regression checks on every affected path.

## G2 skill compliance audit of the OpenCode run

Conclusion: G2 followed the visible outer sequence, but **did not complete the
evidence checks required for a PASS recommendation**. This audit uses the chat
transcript, the scaffolded G2 skill, `G2.md`, `test_run.md`, the test sources and
the telemetry files. The pasted transcript ends before the human verdict; the
later G2 report records `FEEDBACK`.

| Skill step | Observation | Assessment |
|------------|-------------|------------|
| Prerequisite and skill load | Ran `codeanvil status`, saw S2 iteration 1 delivered, loaded G2. | Followed. |
| Declare levels (§Steps 1) | Copied every `required_vl` into `Declared`, including four VL-1 items, without asking the human to declare a level in the shown exchange. The skill says the human declares it, default VL-0. | Missed. |
| Fresh verifier (§Who runs what) | Invoked `vsil-verifier`; G2 records `Verifier: vsil-verifier`. The shortened transcript does not show the subagent's exact command log or prove what context it received. | Invoked; isolation and exact commands cannot be fully audited from the excerpt. |
| G2.0/G2.1 runs | Reports 17 VL-0 and 10 VL-1 passing tests. Telemetry files contain 4 and 10 samples, consistent with fresh runs. | Aggregate executions supported; per-item coverage still needs checking. |
| G2.2 | `mock-only`; no VL-2 declaration or real-hardware claim. | Correctly not run. |
| Required VL-1 coverage (§Hard Rules) | Python VL-1 tests cover six detector scenes; TypeScript VL-1 tests cover four jsdom cases. No VL-1 test exercises PATH-002 across both services or PATH-004's 60 s p95 latency. G2 nevertheless marked both `pass`; the skill requires `missing test` and a module-defect route. | Missed. |
| Telemetry (§Steps 5) | CPU and memory samples exist; WSL2 temperature is reported unavailable. `dropped` and `sched_ms` are constants written by the telemetry script, so `dropped: 0` is not measured evidence. | Partly checked; the all-in-envelope claim is overstated. |
| Infeasibility (§Steps 6) | `test_run.md` says `None`, which G2 reported. | Followed. |
| Present and ask (§Steps 7–8) | Presented the table, honesty draft and recommendation, then asked for a human verdict. The later report records FEEDBACK and the decider, but omits the human answer verbatim. | Presentation followed; report contract incomplete. |

The 27 passing tests establish that those tests passed. They do not establish
that every declared module and path was verified at its declared level. In
particular, the nominal VL-0 PATH-004 test asserts hardcoded latency values,
and no VL-1 test measures end-to-end latency. G2's initial `PASS`
recommendation should therefore have identified missing evidence before the
human supplied the S1/G1 findings.

## Telemetry observation and ready-to-use collector proposal

**Observed in this test.** S2 generated `verification/telemetry/telemetry.py`
for the scaffolded project. It writes `dropped = 0` and `sched_ms = 0.0` as
constants, while `verification/run.sh` prints `dropped: 0` unconditionally.
G2 treated the dropped-buffer zero as an in-envelope measurement. A green
telemetry field must represent an observed value, not a placeholder.

**Proposed change to CodeAnvil.** Ship a versioned, quiet telemetry collector
with the S2 skill as a ready asset. S2 copies and configures it; the agent
does not write a new collector. Normal operation writes a machine-readable
evidence file and emits no progress chatter. Errors produce a nonzero exit
status and a short diagnostic. The collector detects a host profile such as
PC, Raspberry Pi or Jetson, then probes the sensors relevant to that profile.

| Concern | Required behaviour |
|---------|--------------------|
| Common metrics | Record timestamp, host profile, target process, process and system CPU/memory, units, measurement source and collector version. |
| Platform metrics | Record available temperature, throttling, power or accelerator readings when the detected host exposes them; mark unsupported sensors explicitly. |
| Application counters | Read dropped IQ buffers, queue depth and pipeline scheduling latency from actual HAL/service instrumentation. A host-only collector cannot infer these values. |
| Missing data | Write `unavailable` with a reason; never replace a missing measurement with zero. G2 treats required but unavailable evidence as incomplete. |
| Evidence contract | Attach the collector output to each VL run and let G2 compare measured values with the design's §1.7 envelope. |

An MCP server is a possible **interface** for starting, stopping and reading
the collector. Keep a deterministic command-line core so the same evidence
works in every supported agent runtime and from `verification/run.sh`; an MCP
facade can call that core where available. The choice of MCP packaging, host
probes and optional dependencies still needs design and cross-platform tests.

## S1 artifact location and GT document names

**Observed in T3.** S1 wrote its complete design to
`.codeanvil/report/01_fm_occupancy_mock/S1_artifacts/S1_design.md` and its graph
to the adjacent `S1_graph.html`. The project's `GT/` contained
`build_package.md`, `G0_StRS.md` and `G0_SyRS.md`; it had no SRS. The stage
report and the product design therefore live under the same `report/` tree,
although they have different purposes. The `G0_` prefixes name a gate that
validated the documents, not the documents themselves.

**Recommended names and locations before S2:**

| Path | Role | Produced/reviewed by |
|------|------|----------------------|
| `GT/build_package.md` | Source material for normalisation; keep its existing name. | Project author / S0 input |
| `GT/StRS.md` | Stakeholder requirements and COTS constraints. | S0 / G0 |
| `GT/SyRS.md` | System requirements traced to StRS. | S0 / G0 |
| `GT/SRS.md` *(only when needed)* | Distinct software requirements allocated from SyRS, with explicit `SYS-*` traces and acceptance criteria. | S1 / G1 |
| `design/SDD.md` | Complete software design: service boundaries, modules, contracts, build order, verification profiles, decisions and risks. | S1 / G1 |
| `design/dependency_graph.html` | Visual companion to the SDD; the SDD links to it. | S1 / G1 |
| `.codeanvil/report/<cycle>/S1.md`, `G1.md` | Iteration evidence and human verdict, with paths and digests of the reviewed documents. | S1 / G1 |

`SRS` means **Software Requirements Specification**; `SDD` means **Software
Design Description**. The current `S1_design.md` is an SDD in substance, so
move its content to `design/SDD.md` rather than renaming it to `SRS.md`.
Create `GT/SRS.md` only if S1 derives software requirements that add useful
detail beyond `GT/SyRS.md`; do not create a duplicate document merely to fill
out the acronym set. The minimum reviewed baseline before implementation is
therefore `GT/StRS.md`, `GT/SyRS.md` and `design/SDD.md`. If an SRS exists, G1
also reviews it and S2 traces implementation to it. G0 remains the structural
gate for the StRS/SyRS pair; it does not silently validate the later SRS or SDD.

**Migration is one work unit.** Update the active S0, G0, S1, G1, S2 and G2
skill paths and report contracts together; update locked template names,
`project.yaml` document pointers, scaffold generation, CLI/help text, path
rewriting, documentation and tests. S2 and G2 must resolve the G1-approved SDD
and optional SRS from the recorded paths and digests. Preserve earlier SDD/SRS
revisions by cycle and iteration so G2-to-S1 feedback can produce a reliable
design diff and a bounded S2 code change set. Existing scaffolded projects
need an explicit migration or must finish their current cycle on the old
paths; do not rename files underneath an active agent. This T3 test project is
left untouched. This section records a proposal, not a completed source
migration.

## Final G2 handoff: runnable prototype and validation reports

**Observed after the rework loop.** `codeanvil status` reports S0 iteration 2,
G0 iteration 2 PASS, S1 iteration 2, G1 iteration 2 PASS, S2 iteration 2 and
G2 iteration 2 PASS. G2 wrote
`.codeanvil/report/01_fm_occupancy_mock/G2_artifacts/verified_prototype.md`.
That file lists the services, verification levels, telemetry and future work,
but gives no steps for a person to start the two services and see a live
spectrum, waterfall and channel table.

**Concrete run gap in T3.** `src/fm_edge/main.py` defines `run_pipeline()`, but
its `main()` only logs startup instructions; `python main.py` or the packaged
`fm_edge` command does not start the WebSocket pipeline. The working Mock HAL
launcher is `verification/fm_edge/demo.py`, and `verification/` is explicitly
marked as never shipped. The dashboard does provide `pnpm build` and `pnpm
dev` scripts in `src/dashboard/package.json`, and connects to port 8765. Thus
the current sandbox can be previewed with the kit, but the delivered service
has no self-contained runnable entry point in this mock-only cycle. G2 PASS
records the verification verdict; it should not be presented as proof that
`python main.py` launches the product.

**Proposed handoff contract.** On G2 PASS, put the reader-facing output under
the project root, scoped by cycle:

| Path | Content |
|------|---------|
| `reports/<cycle>/verified_prototype.md` | Verdict, exact source revision, HAL mode, delivered services, known limits, and the tested system entry point with expected URL and visible behaviour. |
| `reports/<cycle>/validation_levels.md` | One row per module and `PATH-*`: required and achieved VL, environment, exact test IDs/commands, pass/fail, measured criterion, telemetry/evidence path, and unverified claims. Separate VL-0, VL-1 and VL-2 summaries. |
| `.codeanvil/report/<cycle>/G2.md` | Append-only gate state and human verdict; link to the two reader-facing reports and record their digests. |

**System entry point is required.** S1 must name one project-root command or
launcher that starts a usable end-to-end system, plus the selected HAL mode,
configuration, ports, expected URL and shutdown behaviour. For this two-service
project, the entry point may orchestrate both processes or give a small
interactive launcher; service-specific commands remain documented for
debugging. G1 checks that the entry point is defined and feasible. S2
implements it and includes a smoke test that starts the backend, starts the
dashboard, observes at least one valid update through their real interface,
then shuts down cleanly. G2 runs the implemented entry point, records its
exact command and outcome, and includes instructions to inspect the spectrum,
waterfall and channel table. A launcher that only prints startup messages does
not satisfy this criterion.

For a mock-only build, the entry point must select an explicit **demo mode**
with a Mock HAL and publish the same WebSocket contract as the delivered
backend. A possible target is `./run-demo` at the project root, internally
starting the Python service and the dashboard, then printing the local URL.
The exact syntax is a design choice; the gate must report the command actually
implemented and tried. Keep demo mode clearly labelled VL-1/Mock HAL, with no
real-hardware claim. If `verification/` is never shipped, put the runtime Mock
HAL needed by this entry point in the delivered demo/product package or ship
a clearly named demo bundle. Do not make the only working entry point depend
on a verification-only file.

For this T3 sandbox today, the kit advertises
`PYTHONPATH=.:src uv run python verification/fm_edge/demo.py --scene SC-2` from
the project root, then `pnpm build && pnpm dev` from `src/dashboard`, opening
the URL printed by Vite. That is an observed script recipe, not a newly run
smoke test in this review. The validation-level report must link individual
evidence rather than assigning the same aggregate `verification/run.sh vl1`
result to every VL-1 path. This proposal is not yet implemented in the
methodology; the active test project remains untouched.

### Deferred VL-2 machine-to-machine interface

A future `mock+real` cycle will also need a machine-to-machine (M2M) interface
for controlling and observing the real COTS setup at VL-2. Define its
commands, device identity, measurements, evidence format and failure handling
when that cycle is designed. It is deferred from this mock-only T3 handoff;
the system entry point and VL-0/VL-1 reporting above do not depend on it.

## Closure audit of the 2026-11-05 full-flow plan

The primary plan is `odd/tasks/2026-11-05_1421_vsil_v3_full_flow.md` on
`feat/vsil-v3-full-flow`. The T3 OpenCode project completed the report chain:
S0 and G0 at iteration 2, S1 and G1 at iteration 2, S2 and G2 at iteration 2,
with G2 `HITL: PASS`. This establishes that an agent and a human traversed the
chain, including one G2-to-S1 rework loop.

The **feature plan is not ready to mark done**:

| Plan checkpoint | Closure evidence |
|-----------------|------------------|
| T1–T7, T9–T10 implementation | Recorded as done in the feature plan and pushed on the feature branch. |
| T8 end-to-end acceptance | The report chain passed, but the T8 procedure requires `uv sync --frozen --no-dev && uv run fm_edge` to start without kit dependencies. `fm_edge.main:main` currently only logs; the working Mock HAL launcher lives under the non-shipped `verification/` kit. The failure probes listed in the T8 plan also have no complete result record in the feature-plan Log. T8 is therefore partially demonstrated, not fully accepted. |
| Merge and T11 release | GitHub shows `feat/vsil-v3-full-flow` separate from `main`; `main` still has version `0.3.0`. The planned merge, `0.4.0` bump, tag and release have not happened. |

The later proposals in this holdout (document names, S2 checkpoints,
telemetry collector, reader-facing `reports/`, and VL-2 M2M) are future
methodology work unless explicitly added to this feature's scope. They need
not be completed to close the original plan, but the runnable entry point is
already an explicit T8 acceptance criterion. Keep the plan open until that
criterion is met, T8 evidence is recorded, and T11 is delivered or explicitly
removed from scope by the plan owner.

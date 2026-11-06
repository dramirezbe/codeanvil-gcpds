# T3 OpenCode S1/G1 review holdout — 2026-11-05

This is the central record of the T3 OpenCode test observations across S1,
G1, S2 and G2. It stays in the CodeAnvil source repository, outside the
scaffolded test project, so the G2 verifier did not receive the earlier
review as context.

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

# T3 OpenCode S1/G1 review holdout — 2026-11-05

Keep this review in the CodeAnvil source repository while the OpenCode sandbox
continues through S2 and G2. Compare it with G2's independent findings after
G2 finishes. Do not copy it into the scaffolded test project or give it to the
G2 verifier as context.

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

## How to score the later G2 run

For each finding, record whether S2 resolved it, G2 independently identified
it, or it remained latent. Use the S2 `test_run.md`, the fresh G2 console
result, and the G2 report as evidence. Count a G2 detection only when G2 names
the root cause or a test fails on that cause without receiving this review.
Do not score F1, F4, or F5 as G2 misses: they are outside G2's required scope.
F2 and F3 are conditional checks because G2 runs only the tests supplied by S2.

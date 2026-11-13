# G1 checklist — design review

G1 answers one question: **are all implementation-critical design choices resolved?** The agent
runs no script: it fills every row by reading the design and the GT in full and by running the
tools itself, and marks each finding `open` (must be resolved before S2 in the agent's
view) or `advisory`. The human decides. Show `open` findings first. Never hide or soften one.

Section numbers (§) refer to the S1 design document.

| Row | Agent checks and shows | Marked `open` when |
|-----|------------------------|--------------------|
| Graph | Dark `dependency_graph.html` and light `dependency_graph_light.html` show the same subsystems, modules, devices and subsystem contracts, and their text panels match `.codeanvil/project.yaml` | Something is missing or differs, because the human would review the wrong picture. A missing file or theme variant is `advisory` |
| G1.1 DAG | Derives the topological order from the §1.4 cards and compares it with §2.2. Subsystem contracts (§3.4) create no edge: runtime message loops do not create implementation dependency cycles | A cycle exists |
| G1.2 interface completeness | Each contract named by a card exists in §3, with all fields | An implementer would have to ask the designer |
| G1.3 requirement coverage | `SYS-*` in §4.1, `NRM-*` in §4.3, cross-subsystem `SYS-*` in §4.4 | A requirement is uncovered. A module without `SYS-*` is `advisory` |
| G1.4 stub feasibility | Each stub or fake-peer recipe in §3 can be generated from the contract alone. Warning signs: "reasonable data", no edge cases, data that exists only at VL-2, a "stream" with no rate or buffer size | An implementer could not write the stub |
| G1.5 verification profile | `hw_dependency: true` means `VL-2`, and appears only in `mock+real`; each `PATH-*` names level, environment and measurable criterion | Any mismatch |
| G1.6 decision quality | Per `DEC-*`: clear context, real alternatives, honest consequences, a rationale that survives questioning | An implementation-critical choice is unresolved; otherwise `advisory` |
| G1.7 COTS coherence | Topology (§0.2) vs inventory (§0.1) vs deployment (§0.4); `PHY-*` cover every connection; inherited budgets in §3.1 agree with `PHY-*`; the HAL is the only hardware contact; the links of §0.4 support the §3.4 contracts | A module touches hardware outside the HAL, a budget contradicts a `PHY-*`, or a link cannot carry its contract |
| G1.8 risks | Per `RSK-*`: credible evidence, viable mitigation. Apply the defect-or-RFD test to each | The test points to RFD: the recommendation names it, with `ANALYSIS (no VL)` evidence. Otherwise `advisory` |
| G1.9 topology, state, loops | Each subsystem has responsibility, deployment and ports; each message of §2.3 has a versioned §3.4 contract; state owner, timeout, acknowledgement, idempotency and safe disconnect are defined. One subsystem passes if it has no external edge | Any is undefined |
| G1.10 end-to-end paths | Each cross-subsystem `SYS-*` has a `PATH-*` with an owner; its budget is split across modules and link; a VL-0 test with connected processes and simulated inputs exists | Either is missing |
| G1.11 HAL ladder | `HAL mode` is `mock-only` or `mock+real`. `Target(s)` states the target **intent** (the device deduced from the `HWC-*` blocks, or `local`), not an enrolled `project.yaml` row; §0.4 and §1.6 resolve every subsystem, path and level to `local` or that intended device, and multiple candidates require selection. VL-0/VL-1 run locally with Mock HAL and remain VERIFIED; VL-2 is real hardware at G2. Mock HAL vectors/generator and golden manifest include id, SHA-256, parameters, simulated condition and expected output. In `mock+real`, the Real HW HAL uses the same port, has device/driver observation, capability checks and safe stop; its scripts measure actual GT criteria with adequate resolution. Cite `PROTO-*`, §4 corrections, §5 uncertainty/tolerances and calibration only when the requirement or conclusion needs them | A target intent is undeclared/ambiguous, a required item is missing or Mock HAL results are presented as VL-2. Required calibration/lab inputs absent from GT are open for that claim; functional tests do not universally require an oracle. Real HW HAL items in `mock-only` are `advisory`, never `open` |
| G1.12 Telemetry companion | §1.7 declares signals, interval, resource budget, the operating envelope per execution target (with COTS basis) and evidence attachment on that compute unit. Host readings cannot stand in for a remote target. Missing telemetry is diagnosed; decide which results need repetition and which remain supported. The companion lives under `verification/telemetry/`, never under `src/`, and is not a module | A target envelope/source or the diagnosis policy is absent, or it appears as a module |
| G1.13 ML readiness | Only if §1.5 exists: weights with digest, training data source and labelling, runtime and COTS budget, implementable inputs and outputs, metrics with dataset and conditions, a deterministic fake response. Supplied metrics are not judged as G2 evidence | Any is missing |
| G1.14 Toolchain availability | Observe runtimes/package managers on every named execution target, using local tools or `ssh_exec_cmd` and `probe_target`. Record actual OS/architecture/versions and required capabilities; do not substitute host observations or require exact CodeAnvil SemVer equality. S2 or the G2 parent updates needed tools/dependencies automatically after the mandatory pre-HW review, from the tool and project's respective published refs | The approved plan cannot provide a required tool/capability, or the environment choice cannot support the test; missing installable dependencies become preparation work, not a pre-G1 installation deadlock |
| G1.15 Runnable entry point | §0.5 gives one project-root command for the complete system, every subsystem it starts, the selected HAL, URL, visible result and clean shutdown; the runtime HAL is available without importing the non-shipped verification kit | The command cannot start a usable system from the delivered files, or any subsystem entry point only prints instructions |
| G1.16 Change impact | On rework: the S1 design change set lists each changed ID with its old and new decision and its interface flag, and the impact map names the files to edit and the `PATH-*` or VL-1 tests to retest only | A changed interface has an empty impact map, or an impact the change set does not explain |
| Kit | §1.3.4 lists every tool S2 must build first (Mock HAL, golden vectors and manifest, telemetry companion, stubs, fake peers, drivers; in `mock+real` also the Real HW HAL with a fake device API), each at its `verification/` or `src/<subsystem>/` path. The design Meta `Toolchain` row gives every subsystem `SUB-xxx: <package> · <language> · <package manager> · <test runner>` from the allowed pairs (Python · uv · pytest, TypeScript · pnpm · vitest), runnable on its deployment target | A tool S2 needs is absent, a path breaks the `src/<subsystem>/` and `verification/` layout, or a subsystem's `Toolchain` entry is missing or incomplete |

**Defect or RFD (G1.8).** If the requirement is achievable, the design is wrong: it is a defect
and returns to S1. If it is infeasible on the declared COTS platform under any partitioning, it is
an RFD.

## Filled form (written into the report Description)

```markdown
Based on: S1 iteration <N>
GT digests (information only): <match | differ | design records none>
Graph: <path> — <ok | open: ... | advisory: file missing>

| Row | Result | Finding | Level |
|-----|--------|---------|-------|
| G1.1 | ... | ... | open / advisory / none |

Recommendation: <PASS | FEEDBACK | RFD> — <reason>
Human answer (verbatim): <...>
Decided by: <name>
Verdict: RFD            <- only when the answer is RFD
Sections to rework: <§ list>   <- only when the answer is FEEDBACK or RFD
```

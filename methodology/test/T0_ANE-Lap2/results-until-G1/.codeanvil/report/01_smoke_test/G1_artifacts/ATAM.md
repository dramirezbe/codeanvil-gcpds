# ATAM Trade Study — G1 Job 5

| Field | Value |
|---|---|
| Cycle | 01_smoke_test |
| Candidates evaluated | `Arch_01` Layered Modular Pipeline (4.10) · `Arch_02` Event-Driven Service Mesh (4.05) |
| Eliminated | `Arch_03` Deterministic Real-Time Pipeline (3.57) — structural cost in maintainability, portability, usability |
| Inputs | `ASR.md`, `Arch_01.md`, `Arch_02.md`, `QA_matrix.md` |

## 1. Business and Quality Goals

| Goal | Source | Measure |
|---|---|---|
| G-1 Accurate, traceable spectrum measurements | STK-MED-*, NRM-GUM-001 | Every reported measurand has calibration context + GUM budget |
| G-2 Unattended operation at remote sites | STK-AUT-001, STK-MON-*, STK-SOP-001 | No operator on site; recover from faults; OTA capable |
| G-3 Real-time visibility up to 20 MHz | STK-RNG-002, HWC-BUS-001 | ≤ 1 s processing latency; gaps explicitly counted |
| G-4 Field-deployable within a small team | Project context | Maintainable by ≤ 5 engineers; testable without hardware |
| G-5 Regulatory defensibility | NRM-ITU-001/002, NRM-ICNIRP-001 | ITU methods, ICNIRP annotations, auditable records |

## 2. Architectural Approaches

**A1 — Layered Modular Pipeline.** One process; domain core with ports and
adapters; stage threads connected by bounded SPSC rings; SQLite as the single
metadata writer; systemd supervises the process.

**A2 — Event-Driven Service Mesh.** Ten process-isolated services over ZeroMQ
with protobuf contracts; per-service cgroups and heartbeats; durable outbox;
per-service OTA.

## 3. Sensitivity Points

A sensitivity point is a design decision where a small change materially moves
one or more quality attributes.

| ID | Decision | Affected QA | Why it is sensitive |
|---|---|---|---|
| SP-1 | Acquisition thread priority and core isolation | Performance, Reliability | On a 4-core Pi, letting storage/network IRQs share the acquisition core converts throughput into drop bursts |
| SP-2 | Queue depth and drop policy | Performance, Reliability, Functional | Unbounded queues hide overload until OOM; drop-oldest must preserve sequence/gap semantics |
| SP-3 | IPC transport in A2 | Performance, Maintainability | Socket copies at 40 MB/s are material on the Pi; shared memory recovers throughput but erodes the clean service boundary |
| SP-4 | Single writer for persistence | Reliability, Functional | Concurrent writers to SQLite or the data volume risk corruption and orphaned IQ segments |
| SP-5 | OTA granularity | Reliability, Availability, Security | Whole-app replacement is simpler but restarts acquisition; per-service OTA reduces blast radius but multiplies consistency risk |
| SP-6 | Calibration context propagation | Functional, Accuracy | A measurement published without its calibration/antenna-factor version is not defensible, regardless of numeric accuracy |
| SP-7 | Antenna/probe settle and interlock | Functional, Accuracy | Switching during capture corrupts traces; settle time must be enforced before the first sample |

## 4. Tradeoff Points

| ID | Tradeoff | A1 position | A2 position |
|---|---|---|---|
| TP-1 | Fault isolation vs latency/memory | One fault domain; minimal copies | Strong isolation; IPC cost and memory overhead on 4 GB |
| TP-2 | Independent deploy vs consistency | Atomic whole-app deploy; simple state | Per-service OTA; higher availability, harder consistency |
| TP-3 | Dynamic scaling vs determinism | Fixed thread roles; predictable | Elastic DSP workers; jitter and cgroup tuning |
| TP-4 | Contract clarity vs in-process simplicity | Ports only; cheap calls | Explicit protobuf contracts; more ceremony |
| TP-5 | Real-time spectrum vs raw IQ recording | Mode switch with gap accounting | Same physical limit; extra hand-off adds risk |
| TP-6 | Centralized calibration vs local ownership | One calibration service in-process | `cald` service; stronger boundary, extra dependency for every record |

## 5. Condition Group Satisfaction

| Group | A1 | A2 | Notes |
|---|---|---|---|
| CG-01 RF Acquisition & Front-End Integrity | Strong | Strong | Both isolate SDR ownership; A1 has fewer hand-offs before FFT |
| CG-02 Spectrum Parameterization | Strong | Strong | A2 validates against a capability descriptor; A1 validates in-process |
| CG-03 Measurement & Signal Analysis | Strong | Adequate | A2's measurand path crosses dspd → measd, adding latency and failure modes |
| CG-04 Geolocation, Time & Units | Strong | Strong | A2's `navd` centralizes; A1's `GeoTimeService` equivalent |
| CG-05 Storage & Data Throughput | Adequate | Adequate | Both bounded by USB 2.0; A2 adds bus copies on the same cores |
| CG-06 Connectivity & Remote Operations | Strong | Strong | A2's `uplinkd` is a cleaner boundary; A1's `LinkManager` is sufficient |
| CG-07 Antennas & Radiation Measurement | Strong | Strong | Antenna factor and probe selection are equivalent in both |
| CG-08 Power, Thermal & Compute | Adequate | Adequate | Neither solves the energy budget alone; policy must be validated |
| CG-09 Health Monitoring & Scheduled Operation | Adequate | Strong | A2's heartbeat/restart model is its clearest advantage |
| CG-10 Calibration, Accuracy & Normative Compliance | Strong | Adequate | A2 must propagate `cald` context across services; A1 enforces in one pipeline |

**Coverage verdict:** both satisfy all ten groups; A1 is stronger on the
measurement/calibration path, A2 is stronger on supervision.

## 6. Risk Catalog

| ID | Risk | Probability | Impact | Response | Residual |
|---|---|---|---|---|---|
| R-01 | USB 2.0 cannot sustain 40 MB/s; raw IQ recording drops samples | Certain | High | Explicit capture modes, gap counters, data-quality metric in every trace; record at ≤ 12 MS/s or duty-cycled | Accepted and documented as an SRS gap |
| R-02 | A1 single process crashes and stops acquisition | Medium | High | systemd restart, hardware watchdog, crash-only state recovery, atomic file publication | Short acquisition gap |
| R-03 | A1 I/O or DSP jitter steals acquisition CPU | High | High | Pin acquisition core, move IRQs, bound queues, separate storage core, monitor deadline misses | Requires tuning per unit |
| R-04 | A2 IPC copies and memory pressure destabilize 20 MS/s path | High | High | Shared-memory fast path, cgroup limits, fewer workers | Complexity increases; determinism still not guaranteed |
| R-05 | A2 cross-service consistency (scan, calibration, gaps) | Medium | High | Idempotency keys, versioned contracts, single writer per table | Integration test burden |
| R-06 | Thermal throttling on Pi 4B changes timing | Medium | Medium | Thermal telemetry, degradation ladder, operating-temperature validation | Reduced capability in heat |
| R-07 | Calibration/uncertainty error undermines defensibility | Medium | High | GUM engine tests, calibration version stamping, review of correction chains | Depends on metrology review |
| R-08 | OTA bricks a remote unit | Low | High | A/B partitions, signed bundles, self-test + rollback | Recovery requires site visit if both slots fail |
| R-09 | Antenna/probe switch during capture corrupts data | Medium | Medium | Interlock + settle state machine, capture gated on switch completion | Timing tuning |
| R-10 | LTE-exposed attack surface | Medium | High | Default-deny inbound, SSH key-only, signed OTA, no listening services except read-only API | Depends on deployment network |

## 7. Risk Themes

- **Performance under a hard bus limit** dominates both candidates. No
  architecture can create USB 2.0 bandwidth; the differentiator is whether the
  design accounts for gaps honestly and preserves measurement metadata.
- **Reliability is A2's strength**, but its isolation benefit is partly consumed
  by new failure modes (IPC, cgroups, OTA orchestration) on a small device.
- **Maintainability and metrological traceability favor A1**, which matters for a
  small team and for regulatory defensibility.
- **A3's determinism is valuable as tactics, not as the whole architecture.**
  Core pinning, preallocated rings, and deadline monitoring can be adopted inside
  A1 without paying A3's full maintainability cost.

## 8. Verdict

**Selected baseline: A1 — Layered Modular Pipeline**, with two explicit
borrowings:

1. **From A3:** pin the acquisition thread to a dedicated core, preallocate the
   IQ rings, move USB/network IRQs off that core, and publish deadline/gap
   counters. This addresses R-03 without adopting PREEMPT_RT or a static plan.
2. **From A2:** keep adapter contracts versioned and explicit, and run the
   process under systemd with heartbeat/watchdog restart semantics. This
   mitigates R-02 without paying IPC costs.

**Why not A2:** its 0.05-point QA lead is within noise, while its IPC/memory risk
(R-04) and integration consistency risk (R-05) act directly on the hardest
constraint (20 MS/s on a 4 GB Pi) and on the small-team maintainability goal.
A2's reliability advantage is real but can be substantially recovered in A1 with
supervision and crash-only design.

**Why not A3:** best raw timing, but its maintainability/portability/usability
costs are structural and disproportionate for this team and deployment.

**Accepted tradeoffs:** single fault domain (mitigated), whole-app OTA (simpler,
brief acquisition interruption), fixed thread roles (predictable, less elastic).

**Conditions of selection:** the SRS must record the USB 2.0 recording gap
explicitly, define gap semantics as part of the data contract, and require
deadline/gap telemetry in every trace.

# G1 Review Package — Rev 1

| Field | Value |
|---|---|
| Project | Edge Sensor — Spectrum Monitoring Subsystem (Phase 2) |
| Organization | National Spectrum Agency (ANE) — Colombia |
| Cycle | `01_smoke_test` |
| Gate | G1 — Design Synthesis |
| Package revision | Rev 1 |
| Baseline selected | `Arch_01` Layered Modular Pipeline (ATAM verdict) |
| SRS | `GT/G1_SRS.md` v1.0.0 (`SRS-ANE-EDGE-001`) |

## 1. GT Basis

| Item | Value |
|---|---|
| StRS | `GT/G0_StRS.md` — `STRS-ANE-EDGE-001` v2.0.0 |
| SyRS | `GT/G0_SyRS.md` — `SYRS-ANE-EDGE-001` v2.0.0 |
| G0 verdict | `HITL: PASS` (iteration 1) |
| CC verdict | `HITL: PASS` (iteration 1) |
| Snapshot manifest | `6027d645781a27d12a174b51bc91da37ab373e159689dc297ee061c51139ca9f` |
| Sealed files | 3 files, 122 556 bytes |
| GT integrity at G1 start | PASS (`source_snapshot.py verify --strict`) |

The G0 pair was not modified during G1. `GT/G1_SRS.md` is the new G1
deliverable; the CC snapshot was taken before it existed, so a re-seal is
required before the next gate that verifies the `GT/**` scope.

## 2. ASR Catalog

| Metric | Value |
|---|---|
| Total ASRs | 91 |
| STK / NRM / HWC / SYS | 43 / 4 / 17 / 27 |
| Condition Groups | 10 |
| MUST / SHOULD / COULD | 77 / 14 / 1 |

| Group | Name | ASRs |
|---|---|---:|
| CG-01 | RF Acquisition & Front-End Integrity | 13 |
| CG-02 | Spectrum Parameterization | 8 |
| CG-03 | Measurement & Signal Analysis | 16 |
| CG-04 | Geolocation, Time & Units | 10 |
| CG-05 | Storage & Data Throughput | 6 |
| CG-06 | Connectivity & Remote Operations | 9 |
| CG-07 | Antennas & Radiation Measurement | 7 |
| CG-08 | Power, Thermal & Compute Resources | 6 |
| CG-09 | Health Monitoring & Scheduled Operation | 5 |
| CG-10 | Calibration, Accuracy & Normative Compliance | 11 |

Full catalog: `G1_artifacts/ASR.md`.

## 3. Candidates and Scores

| Candidate | Style | Functional | Performance | Compatibility | Usability | Reliability | Security | Maintainability | Portability | Weighted |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| A1 | Layered Modular Pipeline | 5 | 4 | 4 | 3 | 4 | 4 | 5 | 4 | **4.10** |
| A2 | Event-Driven Service Mesh | 4 | 3 | 5 | 4 | 5 | 4 | 3 | 4 | **4.05** |
| A3 | Deterministic Real-Time Pipeline | 5 | 5 | 3 | 2 | 4 | 4 | 2 | 2 | **3.57** |

Scores use ISO 25010 rows, MUST/SHOULD/COULD weights 3/2/1, and
highest-priority aggregation per row. Full evidence: `QA_matrix.md`.

## 4. Selection Rationale

**Selected: A1 — Layered Modular Pipeline**, with two borrowings:

1. **From A3:** pin the acquisition thread, preallocate bounded IQ rings, steer
   USB/network IRQs away from the acquisition core, and publish deadline/gap
   counters.
2. **From A2:** versioned adapter contracts and systemd heartbeat/watchdog
   restart supervision.

The A1–A2 gap (0.05) is within noise. ATAM examined the sensitivity and
tradeoff points and found that A2's reliability advantage is partly consumed by
IPC/memory pressure and cross-service consistency risk on a 4 GB Pi, while A1's
maintainability and measurement traceability are materially better for a small
team. A3's determinism is valuable as tactics, not as the whole architecture.

Full study: `ATAM.md`.

## 5. Accepted Tradeoffs

| Tradeoff | Decision | Rationale |
|---|---|---|
| Fault isolation vs latency/memory | Single process, supervised restart | Preserves the 20 MS/s path on 4 cores; restart gap accepted and recorded |
| Independent OTA vs consistency | Whole-app A/B OTA | Simpler state; brief acquisition interruption accepted |
| Dynamic scaling vs determinism | Fixed thread roles | Predictable timing; capacity validated at integration |
| Real-time spectrum vs raw IQ recording | Mode switch with gap accounting | Physical USB limit; data quality is explicit, never hidden |
| Centralized calibration vs local ownership | One calibration service | Every record gets one context; defensible reporting |

## 6. Risks and Responses

| ID | Risk | Response | Residual |
|---|---|---|---|
| R-01 | USB 2.0 cannot sustain 40 MB/s at 20 MS/s | Capture modes, gap counters, data-quality metric in every trace | Accepted; SRS gap |
| R-02 | Single process stops acquisition | systemd restart, hardware watchdog, crash-only recovery | Short gap |
| R-03 | DSP/storage jitter steals acquisition CPU | Core pinning, IRQ steering, bounded rings, deadline telemetry | Tuning per unit |
| R-04 | A2 IPC/memory pressure (not selected) | — | Avoided by selection |
| R-05 | A2 cross-service consistency (not selected) | — | Avoided by selection |
| R-06 | Thermal throttling | Telemetry, degradation ladder, temperature validation | Reduced capability in heat |
| R-07 | Calibration/uncertainty error | GUM engine tests, version stamping, correction review | Metrology review |
| R-08 | OTA bricks remote unit | A/B slots, signed bundles, self-test + rollback | Site visit if both slots fail |
| R-09 | Antenna switch during capture | Settle interlock, capture gated on completion | Timing tuning |
| R-10 | LTE-exposed attack surface | Default-deny, SSH key-only, signed OTA, read-only API | Network-dependent |

## 7. Modules (ADD Summary)

29 components in five layers:

- **Adapters (10):** SDR, GNSS, clock, links, OTA, storage, filesystem,
  antenna, power, environmental sensors.
- **Services (15):** scheduler, acquisition, DSP, measurement, detection,
  calibration, geo/time, storage, link, OTA, health, power, antenna, EMC, API.
- **Kernel (4):** config, units, uncertainty, diagnostics.
- **Interfaces (10):** `IIQSource`, `ISpectrumSink`, `IMeasurandSink`,
  `ICalibrationContext`, `ITimePosition`, `IRecordStore`, `ILink`,
  `IAntennaControl`, `IHealthReport`, `IPowerBudget`.
- **Graph:** 75 edges, verified acyclic; single owners for SDR, data volume,
  time, calibration, and health.

Full decomposition: `ADD.md`.

## 8. SRS Summary

| Metric | Value |
|---|---|
| Document | `GT/G1_SRS.md` (`SRS-ANE-EDGE-001` v1.0.0) |
| REQ blocks | 31 across 11 module groups |
| SYS coverage | 27/27 |
| Test cases | 31 |
| Structural validation | PASS — 0 errors, 0 warnings |
| Dependencies | Resolve; acyclic |
| Traceability | Every REQ → SYS → STK; §8 complete |

## 9. SRS Gap List

| ID | Gap | Upstream source | Impact | Disposition |
|---|---|---|---|---|
| GAP-01 | USB 2.0 sustains below the 40 MB/s needed for 20 MS/s CS8; gapless raw IQ recording is physically impossible | `HWC-BUS-001`, `HWC-DRV-001`, `STK-ALM-003` | Raw recording is decimated or duty-cycled; gaps are explicit | Accepted in SRS; stakeholder confirmation needed |
| GAP-02 | GPS module is TBD; `HWC-GPS-001/002` source refs are TBD | `HWC-GPS-001`, `HWC-GPS-002` | Position accuracy and protocol assumptions provisional | Resolve at hardware selection |
| GAP-03 | 4G/5G modem and antenna multiplexer are TBD | `HWC-*` inventory, `STK-RED-001`, `STK-ANT-001` | Link and antenna interface details provisional | Resolve at procurement |
| GAP-04 | HackRF DANL characterization not yet measured (`REF-MEAS-001` “to be performed”) | `HWC-SDR-004`, `STK-CAR-001` | Detection thresholds and DANL claims provisional | Measurement campaign before verification |
| GAP-05 | USB sustained-throughput measurement not yet performed (`REF-MEAS-002`) | `HWC-BUS-001` | Gap thresholds and recording modes provisional | Measurement campaign before verification |
| GAP-06 | No numeric retention capacity or retention period upstream | `STK-ALM-001`, `STK-ALM-003` | Retention policy is configurable but unquantified | Stakeholder decision needed |
| GAP-07 | OTA signing keys and update server are outside the GT | `STK-SOP-001`, `SYS-NET-004` | Signature trust root and distribution unspecified | Define in deployment/operations |
| GAP-08 | ICNIRP compliance status is PENDING upstream | `NRM-ICNIRP-001` | ICNIRP output is annotation only, not a compliance claim | Stakeholder confirmation |
| GAP-09 | Thermal degradation thresholds are not quantified upstream | `HWC-CPU-003` | Degradation ladder thresholds provisional | Validate across operating range |
| GAP-10 | Time-sync accuracy target (1 ms) is derived, not explicit upstream | `STK-SIN-001`, `SYS-CAL-001` | Compliant-record gating depends on this target | Confirm with metrology |

No GT file was edited to close a gap. All gaps are recorded here for the next
cycle or stakeholder decision.

## 10. Custody Status

- G0 pair unchanged since CC sealing; G1 wrote only `GT/G1_SRS.md`.
- `GT/G1_SRS.md` creation recorded in the custody ledger at seq 3
  (`e23d2b90578d…`); ledger verify PASS with 3 entries.
- The CC snapshot scope is `GT/**`; it does not yet include `G1_SRS.md`.
- **Action required before the next gate:** explicit authorization to re-seal
  the GT set with `G1_SRS.md`, recorded as a further custody ledger entry with
  the reason. Do not re-seal silently.

## 11. Recommendation

**Recommend G1 PASS.** The design is traceable end to end, the SRS passes all
seven structural validation rules, the selected architecture is justified
against alternatives, and the known physical and upstream gaps are explicit
rather than hidden.

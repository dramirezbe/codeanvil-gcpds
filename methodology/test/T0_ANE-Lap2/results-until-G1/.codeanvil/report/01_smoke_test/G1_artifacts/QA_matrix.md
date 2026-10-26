# QA × Architecture Matrix — G1 Job 4

| Field | Value |
|---|---|
| Cycle | 01_smoke_test |
| Candidates | `Arch_01` Layered Modular Pipeline · `Arch_02` Event-Driven Service Mesh · `Arch_03` Deterministic Real-Time Pipeline |
| Scale | 0 = unacceptable · 1 = very weak · 2 = weak · 3 = adequate · 4 = strong · 5 = excellent |
| Priority weights | MUST = 3 · SHOULD = 2 · COULD = 1 |

## Scoring Method

Rows are the eight ISO/IEC 25010:2011 quality characteristics. Each row is
mapped to the ASRs it exercises. The **row weight is the highest priority among
those ASRs** (highest-priority aggregation): a row touching any MUST ASR weighs
3, otherwise any SHOULD weighs 2, otherwise 1.

Cell scores are 0–5 and must be justified by architecture evidence, not
preference. The weighted total is:

```
Total = Σ(row weight × cell score) / Σ(row weight)      (0–5 scale)
```

No row is allowed to be scored without naming the ASR evidence behind it.

## Matrix

| ISO 25010 characteristic | Evidence ASRs | Weight | A1 Layered | A2 Mesh | A3 Real-Time |
|---|---|---:|---:|---:|---:|
| Functional suitability | CG-01/02/03/07; STK-MED-*, SYS-MEAS-*, STK-RNI-* | 3 | **5** | 4 | **5** |
| Performance efficiency | STK-RNG-002, HWC-BUS-001, HWC-DRV-001, STK-MED-004 | 3 | 4 | 3 | **5** |
| Compatibility | CG-06; STK-RED-001…004, STK-SOP-001 | 3 | 4 | **5** | 3 |
| Usability | STK-PAR-005, STK-SOP-001, SYS-NAV-001 | 3 | 3 | **4** | 2 |
| Reliability | CG-09; STK-MON-001/002, STK-AUT-001, SYS-STO-001 | 3 | 4 | **5** | 4 |
| Security | STK-SOP-001 (remote access/OTA) | 3 | 4 | 4 | 4 |
| Maintainability | Derived design preference (no direct ASR) | 2 | **5** | 3 | 2 |
| Portability | HWC-CPU/SDR platform constraints; replayability | 1 | **4** | 4 | 2 |
| **Weighted total** | | **21** | **4.10** | **4.05** | **3.57** |
| **Rank** | | | **1** | **2** | **3** |

## Row Evidence and Score Justification

### Functional suitability — weight 3

- **A1 = 5.** One domain core owns every measurand and detector; no cross-service
  contract can drop a requirement. The layering keeps measurement logic in one
  testable place.
- **A2 = 4.** Each measurand has a clear owning service, but scan metadata,
  calibration version, and gap counters cross three contracts; an integration
  defect can lose functional context even when each service is correct.
- **A3 = 5.** Dedicated DSP and measurement stages cover all CG-01/02/03/07
  behaviours with explicit budgets; nothing is deferred to a best-effort layer.

### Performance efficiency — weight 3

- **A1 = 4.** In-process zero-copy frames and a dedicated acquisition thread meet
  the 20 MS/s spectrum path; the shared process can still suffer from allocator
  and I/O jitter.
- **A2 = 3.** IPC copies and PUSH/PULL hand-offs add latency and memory bandwidth
  pressure on a 4-core Pi; the design may need a shared-memory fast path, which
  is extra complexity.
- **A3 = 5.** Pinned cores, SCHED_FIFO, preallocated hugepage rings, and IRQ
  affinity are designed specifically for the latency and throughput envelope.

### Compatibility — weight 3

- **A1 = 4.** Adapters isolate SoapySDR, ModemManager, gpsd, and NetworkManager;
  vendor types do not leak into the core.
- **A2 = 5.** Protobuf contracts and one-owner-per-link services make
  interoperability explicit and independently testable.
- **A3 = 3.** Static scan plans and a single process make external integration
  more rigid; adding a new link or SDR requires recompiling the pipeline.

### Usability — weight 3

- **A1 = 3.** CLI + read-only REST is workable for a trained operator but thin for
  field setup.
- **A2 = 4.** `apid` offers job submission, status, and health per service; the
  operator sees which unit degraded.
- **A3 = 2.** Operability is secondary to determinism; diagnosis requires tracing
  the deadline monitor.

### Reliability — weight 3

- **A1 = 4.** Bounded queues, crash-only restart, atomic publication, and SQLite
  recovery; one process is still one fault domain.
- **A2 = 5.** Per-service restart, heartbeat TTL, durable outbox, and acquisition
  continuing while storage/uplink are down. This is the candidate's strongest row.
- **A3 = 4.** Hardware watchdog and degradation ladder are strong, but a fault in
  the single process takes the whole pipeline down until restart.

### Security — weight 3

- **A1 = 4.** No inbound services by default, SSH key-only, signed OTA.
- **A2 = 4.** Loopback-only services and signed inter-service messages, but a
  larger local attack surface from many sockets and units.
- **A3 = 4.** Single process and read-only local API, signed OTA; remote debugging
  is harder but the surface is small.

### Maintainability — weight 2

- **A1 = 5.** One deployable, explicit ports, fake adapters for tests, golden
  traces; a small team can hold the whole design.
- **A2 = 3.** Narrow contracts help, but ten units, cgroup tuning, OTA
  consistency, and distributed debugging raise the operational burden.
- **A2 note:** the lower score is about total cost of ownership, not code quality.
- **A3 = 2.** Real-time constraints (no allocation, SCHED_FIFO, priority rules)
  make changes risky; specialist knowledge is required.

### Portability — weight 1

- **A1 = 4.** Domain core replays recorded IQ on a workstation; adapters isolate
  platform APIs.
- **A2 = 4.** Services can move to a larger edge node, but cgroup and systemd
  assumptions travel with them.
- **A3 = 2.** PREEMPT_RT, core pinning, and hugepage assumptions are tied to the
  Pi 4B and its kernel.

## Sensitivity

The A1–A2 gap is only 0.05 points (86 vs. 85 weighted points). A one-point change
in either Reliability or Performance would swap the ranking. A3 trails because
its maintainability, portability, and usability costs are structural, not
incidental. The top two candidates therefore advance to the ATAM trade study,
where the close score and the A2 IPC risk are examined explicitly.

# Architecture Candidate 02 — Event-Driven Service Mesh

| Field | Value |
|---|---|
| Cycle | 01_smoke_test |
| Generation order | 02 |
| Style | Process-isolated services over a local message bus |
| Primary driver | Fault isolation, independent update, and elastic DSP capacity |
| ASR basis | 91 ASRs in 10 Condition Groups (`ASR.md`) |

## 1. Context and Drivers

The sensor runs unattended at remote sites where a failed process must not take
down the whole instrument. It also has bursty workloads: wideband acquisition is
constant, but measurement, uplink, and reporting have different cadences. This
candidate decomposes the sensor into **supervised services** that communicate
through a brokerless message bus (ZeroMQ) using protobuf messages.

The trade is explicit: process isolation buys fault containment and independent
OTA, at the cost of IPC copies, scheduling jitter, memory footprint, and more
operational surface on a 4 GB Raspberry Pi.

## 2. Architecture Overview

```
            +-----------------------------+
            |        supervisord          |
            | health · restart · policy   |
            +--------------+--------------+
                           |
   +-----------+   +-------+--------+   +-----------+
   |  acqd     |   |    dspd        |   |  measd    |
   | SDR + GPS |-->| N worker procs |-->| measurands|
   +-----+-----+   +-------+--------+   +-----+-----+
         |                 |                  |
         |  PUB frames     |  PUSH results    |  PUSH records
         v                 v                  v
   +---------------------------------------------------+
   |              busd (ZeroMQ brokerless)              |
   +----+----------------+----------------+-------------+
        |                |                |
   +----v----+      +----v-----+     +----v------+
   | stored  |      | uplinkd  |     |  apid     |
   | SQLite  |      | LTE/WiFi |     | REST/MQTT |
   | IQ files|      | /Eth/OTA |     | status    |
   +---------+      +----------+     +-----------+
```

Each service is a separate systemd unit with its own cgroup memory/CPU limits.
`acqd` owns the SDR; only it touches the HackRF. `dspd` scales worker processes
by CPU quota. `stored` is the only writer to the data volume. `uplinkd` owns all
WAN links. `supervisord` observes heartbeats and restarts units with backoff.

## 3. Components and Responsibilities

| Service | Responsibility | ASRs |
|---|---|---|
| `acqd` | SDR configuration, IQ framing, timestamping, gap detection; publishes frames with sequence IDs | HWC-SDR-001…007, HWC-BUS-001, HWC-DRV-001 |
| `dspd` (N workers) | FFT/window/detector pipeline, decimation, demodulation, trace production | STK-PAR-001…004, STK-MED-001/006, SYS-DSP-001/002 |
| `measd` | OBW, channel power, modulation metrics, RDS decode, audio extraction, detection rules | STK-MED-003…007, STK-VER-001/002, SYS-MEAS-001…005, SYS-VER-001/002 |
| `stored` | SQLite metadata, trace/IQ segmentation, retention, integrity manifests | STK-ALM-001/003, HWC-STR-001, SYS-STO-001 |
| `uplinkd` | Link selection/failover, store-and-forward upload, OTA staging and rollback | STK-RED-001…004, STK-SOP-001, SYS-NET-001…004 |
| `navd` | GNSS/manual position, NTP discipline, unit conversion service | STK-PAR-005/006, STK-GPS-001/002, STK-SIN-001, SYS-NAV-001/002, SYS-DSP-003 |
| `cald` | Calibration tables, antenna factors, GUM uncertainty budgets | STK-CAL-001, STK-CAR-001…005, NRM-GUM-001, SYS-CAL-001 |
| `rfguard` | EMC spur catalog, internal-spur flagging, antenna/probe arbitration | STK-EMC-001, STK-ANT-001/002, SYS-RF-001, SYS-ANT-001/002 |
| `supervisord` | Heartbeats, restart policy, thermal/power load shedding, scheduled scans | STK-MON-001/002, STK-PRG-001, STK-AUT-001, SYS-MON-001/002, SYS-PWR-001 |
| `apid` | Read-only REST/MQTT status, job submission, audit log | STK-SOP-001, SYS-NET-004 |

## 4. Data Flow, Backpressure, and Failure Semantics

- **Frames:** `acqd` publishes on a PUB socket with topic `iq.<band>`. A sequence
  number and monotonic timestamp travel with every frame.
- **Work distribution:** `dspd` uses PUSH/PULL with a fixed high-water mark;
  workers acknowledge batches. If no worker is available, `acqd` drops oldest
  frames and increments a gap counter rather than blocking the SDR.
- **Results:** `measd` publishes immutable records keyed by `(scan_id, frame_id)`.
  `stored` commits metadata before acknowledging; IQ segments are written to a
  staging file and atomically renamed.
- **Uplink:** `uplinkd` maintains a durable outbox in SQLite. Delivery is
  at-least-once with idempotency keys; link loss never blocks acquisition.
- **Failure:** every service has a heartbeat TTL. `supervisord` restarts a dead
  unit and marks the current scan degraded. `stored` loss does not stop
  acquisition; `acqd` loss is reported as a sensor fault.

The 20 MS/s ceiling over USB 2.0 is handled exactly as in any candidate: full-rate
spectrum processing discards samples after FFT; raw recording is limited to
≤ 12 MS/s or duty-cycled windows, with gaps recorded explicitly.

## 5. Deployment and Technology

- C++17 services with `cppzmq` and protobuf; Python only for `apid` and tests.
- One systemd unit per service, cgroup limits, `Restart=on-failure`, watchdog.
- SQLite WAL shared by `stored`, `cald`, and `uplinkd` through separate
  connections; single-writer discipline per table.
- OTA: A/B root partitions plus per-service bundle signing; `uplinkd` stages,
  `supervisord` drains and switches, rollback on failed health check.
- Observability: structured JSON logs to journald, Prometheus node exporter,
  per-service metrics (queue depth, drops, latency percentiles).

## 6. Condition Group Coverage

| Group | Mechanism in this candidate |
|---|---|
| CG-01 RF Acquisition & Front-End Integrity | `acqd` exclusively owns the SDR and enforces tuner/gain/rate invariants; `rfguard` injects the internal-spur catalog into detection |
| CG-02 Spectrum Parameterization | `dspd` workers validate span/RBW/VBW against a capability descriptor published by `acqd` before accepting a job |
| CG-03 Measurement & Signal Analysis | `dspd` produces traces and demodulated streams; `measd` owns all measurands and detection rules as independent consumers |
| CG-04 Geolocation, Time & Units | `navd` is the single source of position/time; every record carries `navd`'s fix ID and unit canonicalization |
| CG-05 Storage & Data Throughput | `stored` is the sole data-volume writer; `acqd` and `dspd` apply credit-based flow control and gap accounting |
| CG-06 Connectivity & Remote Operations | `uplinkd` owns link arbitration and durable outbox; OTA is isolated from acquisition |
| CG-07 Antennas & Radiation Measurement | `rfguard` arbitrates antenna/probe selection; `cald` supplies antenna factor; `measd` computes field strength and ICNIRP annotation |
| CG-08 Power, Thermal & Compute | `supervisord` reads power/thermal telemetry, scales `dspd` workers, and suspends scans when the energy budget is exhausted |
| CG-09 Health Monitoring & Scheduled Operation | `supervisord` heartbeats, restart policy, and schedule engine; `apid` exposes health and scan state |
| CG-10 Calibration, Accuracy & Normative Compliance | `cald` centralizes corrections and GUM budgets; `measd` refuses to publish a measurand without a calibration context |

## 7. Quality Attribute Strategy

- **Reliability:** fault containment per service; restart with backoff; durable
  outbox; acquisition continues when storage or uplink is down.
- **Performance:** parallel `dspd` workers use all four cores; zero-copy within a
  worker; shared-memory transport considered for the IQ path if IPC copies
  exceed budget.
- **Maintainability:** narrow protobuf contracts; each service independently
  testable and deployable; interface versioning enforced at startup.
- **Security:** services bind to loopback only; signed messages between units;
  `uplinkd` is the only egress; OTA bundles signed and verified before staging.
- **Operability:** per-service metrics, cgroup limits, and independent restart
  make remote diagnosis practical.

## 8. Risks and Weaknesses

- More moving parts on a 4 GB device: memory pressure and cgroup tuning are
  first-class engineering work.
- IPC copies and scheduler jitter can threaten the 20 MS/s real-time path; the
  design needs shared-memory fast paths or a dedicated core for `acqd`.
- Cross-service consistency (scan metadata, calibration version, gap counters)
  requires disciplined contracts and idempotency.
- Boot ordering and OTA consistency across units are harder than in a monolith.
- Debugging a distributed pipeline on a headless remote sensor is slower.

## 9. Traceability Notes

Each ASR is owned by exactly one service in §3, with cross-cutting ASRs
(calibration, time, power) owned by their service and consumed via contracts.
The service contracts become the interface section of the SRS. Any ASR that
cannot be satisfied by a service boundary is escalated as an SRS gap at Job 7.

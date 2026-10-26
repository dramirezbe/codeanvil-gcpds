# Architecture Candidate 03 — Deterministic Real-Time Pipeline

| Field | Value |
|---|---|
| Cycle | 01_smoke_test |
| Generation order | 03 |
| Style | Single multi-threaded process on PREEMPT_RT Linux; time-triggered, zero-copy |
| Primary driver | Predictable latency, throughput, and gap accounting at 20 MS/s |
| ASR basis | 91 ASRs in 10 Condition Groups (`ASR.md`) |

## 1. Context and Drivers

The hardest requirements are temporal: 20 MHz real-time monitoring with
≤ 1 s processing latency, gapless trace cadence, and reliable detection when the
USB 2.0 bus cannot carry the full 40 MB/s IQ stream. General-purpose Linux
scheduling can turn a well-laid-out pipeline into unpredictable drop bursts.
This candidate makes **time and memory behaviour the primary design axis**.

It runs one process on a PREEMPT_RT kernel, pins threads to cores, uses
pre-allocated hugepage buffers, and drives acquisition from a periodic timer.
Measurement and storage are consumers with explicit budgets; anything that
misses its deadline is recorded as a missed deadline rather than silently
perturbing acquisition.

## 2. Architecture Overview

```
 CPU 0                  CPU 1                 CPU 2                CPU 3
+-----------+       +------------+       +-------------+      +-------------+
| acq thread|       | dsp thread |       | meas thread |      | io/comms    |
| SCHED_FIFO|       | SCHED_FIFO |       | SCHED_FIFO  |      | SCHED_OTHER |
| SDR + GPS |       | FFT/demod  |       | measurands  |      | storage/net |
+-----+-----+       +-----+------+       +------+------+      +------+------+
      |                   |                     |                    |
      v                   v                     v                    v
  [ring A: IQ]       [ring B: spectra]     [ring C: records]    [outbox + files]
      SPSC                SPSC                  SPSC              SQLite WAL

  timer tick (1 ms) --> deadline monitor --> health/watchdog --> fail-safe policy
```

- **Acquisition thread (CPU 0):** highest priority, never allocates, never
  blocks on I/O. It reads the SDR, stamps frames, and publishes to ring A.
- **DSP thread (CPU 1):** FFT batches, detector traces, decimation, and
  demodulation; publishes spectra to ring B.
- **Measurement thread (CPU 2):** OBW, channel power, modulation, RDS, detection
  rules, uncertainty; publishes records to ring C.
- **I/O thread (CPU 3):** writes files/SQLite, uploads, handles OTA staging;
  best-effort and throttled so it cannot steal acquisition cycles.
- **Deadline monitor:** a low-rate thread that checks per-stage progress
  counters; missed deadlines increment counters and trigger degradation.

## 3. Components and Responsibilities

| Component | Responsibility | ASRs |
|---|---|---|
| `AcquisitionEngine` | Timer-driven retune/capture, gain steps, CS8 framing, sequence and gap counters | HWC-SDR-001…007, HWC-BUS-001, HWC-DRV-001 |
| `DspPipeline` | Window/FFT/average, RBW/VBW realization, decimation, AM/FM demod, RDS bit recovery | STK-PAR-001…004, STK-MED-001/005/006, SYS-DSP-001/002, SYS-MEAS-004/005 |
| `MeasurementEngine` | Trace statistics, OBW, channel power, modulation metrics, audio extraction | STK-MED-003/004/007, STK-SRV-002, SYS-MEAS-001…003, SYS-VER-002 |
| `DetectionEngine` | Threshold rules, intermod products, interference classification, EMC spur catalog | STK-EMC-001, STK-PAR-007, STK-VER-001/002, SYS-DSP-004, SYS-VER-001 |
| `CalibrationEngine` | Corrections, antenna factor, GUM budgets, ITU method metadata | STK-CAL-001, STK-CAR-001…005, NRM-GUM-001, SYS-CAL-001 |
| `NavigationClock` | GNSS/manual position, PPS/NTP discipline, monotonic time base | STK-PAR-005/006, STK-GPS-001/002, STK-SIN-001, SYS-NAV-001/002, SYS-DSP-003 |
| `PersistenceEngine` | Segmented IQ, trace records, metadata journal, retention | STK-ALM-001/003, HWC-STR-001, SYS-STO-001 |
| `LinkEngine` | Ethernet/WiFi/LTE arbitration, outbox, OTA staging | STK-RED-001…004, STK-SOP-001, SYS-NET-001…004 |
| `AntennaManager` | Band antenna/probe switch, antenna-factor selection | STK-ANT-001/002, STK-RNI-001/002, SYS-ANT-001/002 |
| `HealthGovernor` | Deadline/thermal/power monitoring, fail-safe degradation, watchdog kick | STK-MON-001/002, STK-AUT-001, STK-PRG-001, SYS-MON-001/002, SYS-PWR-001 |
| `Scheduler` | Time-triggered scan plan, dwell and retune budgets | STK-PRG-001, SYS-MON-002 |

## 4. Timing, Buffering, and Degradation Policy

- **Time-triggered acquisition:** a 1 ms tick advances a scan plan; retune and
  gain changes occur only at frame boundaries. Every frame has a deadline.
- **Pre-allocated memory:** rings A/B/C are allocated at startup in hugepages;
  sizes derive from worst-case latency budgets (2 s, 1 s, 5 s respectively).
- **Zero-copy:** frames are handed by index, never copied; consumers return
  buffers to a free list.
- **Backpressure:** acquisition never waits. If ring B is full, the DSP stage
  drops the oldest spectrum frame and marks the trace; if ring A is full, the
  SDR adapter drops samples and records an explicit gap.
- **Degradation ladder:** normal → reduced FFT rate → reduced span → spectrum-only
  (no raw IQ) → idle. Transitions are logged with the triggering metric.
- **Throughput truth:** 20 MS/s CS8 is 40 MB/s, above the measured USB ceiling;
  the acquisition engine therefore counts gaps continuously and the reporting
  layer publishes a data-quality metric with every trace.

## 5. Deployment and Technology

- PREEMPT_RT kernel; `SCHED_FIFO` priorities 80/70/60 for acq/dsp/meas, I/O at
  `SCHED_OTHER`; IRQ affinity moves USB and network interrupts off CPU 0.
- C++17, no exceptions or heap allocation on real-time threads; fixed-capacity
  containers; FFTW with NEON; `mlockall` for the process.
- SQLite WAL for metadata; raw IQ in preallocated segmented files with an
  fsync-on-close journal; atomic rename for publication.
- `chrony` with PPS when available; GNSS time is cross-checked against NTP.
- OTA: dual root partitions; update is staged by the I/O thread and applied only
  during a planned maintenance window, with automatic rollback on failed
  self-test.

## 6. Condition Group Coverage

| Group | Mechanism in this candidate |
|---|---|
| CG-01 RF Acquisition & Front-End Integrity | Timer-driven `AcquisitionEngine` owns all tuner/gain state; EMC spur catalog is part of `DetectionEngine`; antenna switch settles before capture |
| CG-02 Spectrum Parameterization | Span/RBW/VBW are compiled into a validated scan plan; impossible combinations are rejected at plan load, not at runtime |
| CG-03 Measurement & Signal Analysis | Dedicated DSP and measurement stages with fixed worst-case budgets; all measurands and demodulators execute in the pipeline |
| CG-04 Geolocation, Time & Units | `NavigationClock` provides one monotonic time base and one position fix per record; unit conversion is a pure function at record build |
| CG-05 Storage & Data Throughput | I/O thread isolated on CPU 3; preallocated IQ segments; acquisition gap counters are first-class metadata |
| CG-06 Connectivity & Remote Operations | `LinkEngine` runs best-effort off the real-time cores; outbox persists across reboots; OTA never overlaps an active scan |
| CG-07 Antennas & Radiation Measurement | `AntennaManager` enforces settle time and antenna-factor selection; field strength and ICNIRP annotation computed in `MeasurementEngine` |
| CG-08 Power, Thermal & Compute | `HealthGovernor` reads INA219/thermal zones and walks the degradation ladder; scan plan carries an energy budget |
| CG-09 Health Monitoring & Scheduled Operation | `Scheduler` + `HealthGovernor`; hardware watchdog kicked only when all stage deadlines are met |
| CG-10 Calibration, Accuracy & Normative Compliance | `CalibrationEngine` runs before publication; a record without a valid calibration context is marked invalid, never reported as measured |

## 7. Quality Attribute Strategy

- **Performance:** deterministic core allocation, zero-copy rings, IRQ affinity,
  and FFT batch sizing tuned to cache; latency measured per stage, not assumed.
- **Reliability:** hardware watchdog tied to deadline health; fail-safe ladder;
  acquisition continues in spectrum-only mode when storage or uplink degrades.
- **Maintainability:** smaller code surface than a service mesh, but real-time
  constraints demand discipline; static analysis and deadline tests in CI.
- **Security:** single process, no listening services except a read-only local
  API; signed OTA; SSH key-only access.
- **Testability:** the pipeline can replay recorded IQ with a virtual clock,
  which makes deadline behaviour reproducible on a workstation.

## 8. Risks and Weaknesses

- Real-time engineering is specialized; priority inversions and driver latency
  can defeat the design if USB and network IRQs are not isolated.
- Thermal throttling on the Pi 4B changes CPU capacity; the degradation ladder
  must be validated across the operating-temperature range.
- Static scan plans reduce flexibility for ad-hoc operator requests; the design
  needs a safe admission path for new jobs.
- OTA on a real-time single process requires a reboot window, reducing
  availability compared with per-service updates.
- Debugging a SCHED_FIFO pipeline on a remote unit is harder; tracing must be
  designed in from the start.

## 9. Traceability Notes

Every ASR maps to a stage or governor in §3. Temporal ASRs (latency, gap
accounting, scheduled scans) are first-class design inputs rather than
afterthoughts. Where an ASR's numeric target cannot be met on the Pi 4B + HackRF
combination (notably sustained 40 MB/s recording), the SRS records the gap and
the data-quality semantics instead of claiming compliance.

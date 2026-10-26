# Architecture Candidate 01 — Layered Modular Pipeline

| Field | Value |
|---|---|
| Cycle | 01_smoke_test |
| Generation order | 01 |
| Style | Layered monolith with ports-and-adapters; single process |
| Primary driver | Maintainability, traceability, and testability under a small team |
| ASR basis | 91 ASRs in 10 Condition Groups (`ASR.md`) |

## 1. Context and Drivers

The sensor must acquire 1 MHz–6 GHz spectrum through a HackRF One, sustain up to
20 MHz instantaneous bandwidth over USB 2.0, compute measurements locally, store
traces and raw IQ, and operate unattended over LTE/WiFi/Ethernet with GPS and
battery power. The dominant constraints are the USB 2.0 throughput ceiling
(~32 MB/s sustained versus 40 MB/s for 20 MS/s CS8) and the Raspberry Pi 4B's
shared USB bus, quad-core CPU, and thermal envelope.

Candidate 01 treats the product as a **modular monolith**: one deployable
process, strict layers, and adapter boundaries at every external interface. The
goal is a design a small team can reason about, test on a desk, and certify
against ITU/GUM without distributed-systems overhead.

## 2. Architecture Overview

```
+---------------------------------------------------------------+
| Presentation / API                                             |
|  local CLI · REST (read-only) · SSH tunnel · MQTT status       |
+---------------------------------------------------------------+
| Application Services                                           |
|  ScanScheduler · MeasurementOrchestrator · CalibrationService  |
|  HealthSupervisor · UplinkManager · PowerPolicy                |
+---------------------------------------------------------------+
| Domain Core                                                    |
|  SpectrumEngine · Detectors · Demodulators · Measurands        |
|  UncertaintyEngine (GUM) · TraceBuilder · EventDetector        |
+---------------------------------------------------------------+
| Ports (interfaces)                                             |
|  SdrPort · GnssPort · ClockPort · StorePort · LinkPort ·       |
|  PowerPort · AntennaPort · SensorPort                          |
+---------------------------------------------------------------+
| Adapters                                                       |
|  SoapySDR/libhackrf · gpsd · chrony/NTP · SQLite+filesystem ·  |
|  ModemManager · NetworkManager · INA219 · antenna switch ·     |
|  temperature/fan sensors                                       |
+---------------------------------------------------------------+
```

The dependency rule points inward: adapters depend on ports, the domain core
depends on nothing external, and application services coordinate domain objects.
No domain code includes a driver header.

## 3. Components and Responsibilities

| Component | Responsibility | ASRs |
|---|---|---|
| `ScanScheduler` | Executes scheduled and on-demand scans; enforces dwell, retune, and antenna selection order | STK-PRG-001, SYS-MON-002 |
| `AcquisitionAdapter` | Configures tuner, sample rate, gain; streams CS8 IQ; timestamps frames; detects dropped samples | HWC-SDR-001…007, HWC-BUS-001 |
| `SpectrumEngine` | Windowing, FFT, averaging, detector traces (max/min/avg), RBW/VBW mapping | STK-PAR-001…004, SYS-DSP-001/002 |
| `MeasurementService` | Occupied bandwidth, channel power, modulation index/depth, RDS, audio extraction | STK-MED-001…007, SYS-MEAS-001…005 |
| `DetectionService` | Threshold rules, intermodulation products, interference classification | STK-PAR-007, STK-VER-001/002, SYS-DSP-004, SYS-VER-001 |
| `CalibrationService` | Loads antenna factor and cable loss tables, applies amplitude/frequency corrections, computes GUM budgets | STK-CAL-001, STK-CAR-001…005, NRM-GUM-001, SYS-CAL-001 |
| `GeoTimeService` | Manual coordinates, GNSS fixes, NTP/chrony discipline, position stamping | STK-PAR-005, STK-GPS-001/002, STK-SIN-001, SYS-NAV-001/002 |
| `StoreService` | SQLite metadata, trace files, raw IQ segments, retention policy | STK-ALM-001/003, HWC-STR-001, SYS-STO-001 |
| `LinkManager` | LTE/WiFi/Ethernet selection and failover, store-and-forward upload, OTA staging | STK-RED-001…004, STK-SOP-001, SYS-NET-001…004 |
| `HealthSupervisor` | Watchdogs, temperature, disk, modem and SDR liveness, degraded-mode policy | STK-MON-001/002, SYS-MON-001 |
| `PowerPolicy` | Battery/solar budget, load shedding, scheduled sleep between scans | STK-AUT-001, HWC-PWR-001, SYS-PWR-001 |
| `AntennaController` | Band-specific antenna selection, active radiation probe, antenna-factor lookup | STK-ANT-001/002, STK-RNI-001/002, SYS-ANT-001/002 |
| `EmcGuard` | Flags known internal spurs, enforces shielding/filtering assumptions in reports | STK-EMC-001, SYS-RF-001 |

## 4. Data Flow and Buffering

1. **Acquire:** the SDR adapter fills fixed 1 MiB frames in a lock-free SPSC ring
   (capacity ≈ 2 s at 10 MS/s). Each frame carries a monotonic sequence number.
2. **Process:** the DSP stage consumes frames, computes traces and measurements,
   and emits immutable result records.
3. **Persist:** traces go to SQLite/Parquet; raw IQ is written only when the
   scheduler enables recording. Metadata is committed before the IQ segment.
4. **Upload:** the link manager uploads completed records; failures fall back to
   store-and-forward.

Because USB 2.0 cannot sustain 40 MB/s indefinitely, the acquisition adapter
implements two explicit modes:

- **Real-time spectrum mode:** capture at 20 MS/s, compute and discard samples;
  gap counters are included in every trace.
- **Recording mode:** decimate to ≤ 12 MS/s or duty-cycle raw capture so that
  aggregate throughput stays below the measured USB ceiling; gaps are recorded
  as first-class metadata.

No stage silently blocks the acquisition thread: when a downstream queue is
full, the policy is drop-oldest with a gap marker, never unbounded growth.

## 5. Deployment and Technology

- C++17 domain core and DSP (FFT via FFTW/KissFFT, NEON-friendly), Python only
  for tooling and tests.
- SQLite in WAL mode; raw IQ in segmented files with a sidecar manifest.
- systemd unit for the single process; `chrony` for time; `ModemManager` and
  `NetworkManager` for links; `gpsd` for GNSS.
- Configuration validated at startup against a versioned schema; every applied
  calibration and configuration is stamped into measurement metadata.

## 6. Condition Group Coverage

| Group | Mechanism in this candidate |
|---|---|
| CG-01 RF Acquisition & Front-End Integrity | `AcquisitionAdapter` owns tuner/gain/rate; `EmcGuard` flags internal spurs; antenna port selection before each band |
| CG-02 Spectrum Parameterization | `SpectrumEngine` maps requested span/RBW/VBW to FFT length, window, and decimation; rejects impossible combinations before retuning |
| CG-03 Measurement & Signal Analysis | `MeasurementService` + `DetectionService` implement traces, OBW, channel power, RDS, AM/FM demod, modulation metrics, intermod/interference rules |
| CG-04 Geolocation, Time & Units | `GeoTimeService` merges manual/GNSS position, disciplines time, and converts units at the reporting boundary |
| CG-05 Storage & Data Throughput | `StoreService` writes metadata-first, segments IQ, applies retention; acquisition modes keep USB below ceiling |
| CG-06 Connectivity & Remote Operations | `LinkManager` priority order Ethernet → WiFi → LTE, health-checked failover, staged OTA with rollback |
| CG-07 Antennas & Radiation Measurement | `AntennaController` selects band antenna/probe, loads antenna factor, computes field strength and ICNIRP annotations |
| CG-08 Power, Thermal & Compute | `PowerPolicy` budgets energy per scan, sheds non-essential loads, schedules sleep; thermal limits reduce sample rate |
| CG-09 Health Monitoring & Scheduled Operation | `HealthSupervisor` + `ScanScheduler` expose health, restart stuck stages, run unattended schedules |
| CG-10 Calibration, Accuracy & Normative Compliance | `CalibrationService` applies corrections and GUM budgets; reports carry ITU method references and uncertainty |

## 7. Quality Attribute Strategy

- **Performance:** zero-copy frames inside the process; FFT batches sized to L2;
  no per-sample allocation; acquisition thread isolated from storage I/O.
- **Reliability:** watchdog per stage; bounded queues; crash-only restart of the
  process with state recovered from SQLite; atomic file publication.
- **Maintainability:** one deployable, explicit ports, domain core testable with
  fake adapters; golden-file tests for traces and measurements.
- **Security:** no inbound ports by default; SSH key-only access; signed OTA
  bundles; secrets in root-owned environment files.
- **Portability:** SDR and modem adapters isolate vendor APIs; the domain core
  can run against recorded IQ on a workstation.

## 8. Risks and Weaknesses

- A single process is a single fault domain: a DSP crash interrupts acquisition
  unless supervised and restarted quickly.
- Thread-level coupling makes CPU contention visible as dropped samples; the
  design must reserve cores and measure jitter continuously.
- Layering can become ceremonial if adapters leak vendor types into the core.
- The 20 MS/s + raw-storage combination remains physically impossible over
  USB 2.0; this candidate makes the tradeoff explicit rather than hiding it.

## 9. Traceability Notes

Every ASR in `ASR.md` is assigned to a component in §3. CG coverage is complete;
no Condition Group is left to an external system. Design decisions that cannot
meet an ASR (for example sustained 40 MB/s recording) are recorded as explicit
SRS gaps at Job 7 rather than silently weakened.

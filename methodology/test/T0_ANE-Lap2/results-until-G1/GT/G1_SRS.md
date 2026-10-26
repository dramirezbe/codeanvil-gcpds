# Edge Sensor — Spectrum Monitoring Subsystem (Phase 2)

## Software Requirements Specification (SRS)

> **Standard:** IEEE/ISO/IEC 29148:2018 §9.6 — *Software requirements specification.*
>
> **Template version:** 4.0.0
> **Creation date:** 2026-10-26
> **Last modified:** 2026-10-26
> **Document status:** `DRAFT`

---

## Document Metadata

| Field                  | Value                                                      |
|------------------------|------------------------------------------------------------|
| **Document ID**        | `SRS-ANE-EDGE-001`                                         |
| **Project**            | Edge Sensor — Spectrum Monitoring Subsystem (Phase 2)      |
| **Organization**       | National Spectrum Agency (ANE) — Colombia                  |
| **Version**            | 1.0.0                                                      |
| **Classification**     | `INTERNAL`                                                 |
| **Author(s)**          | AI-assisted design (OpenCode G1 agent)                     |
| **Reviewer(s)**        | G1 HITL reviewer                                           |
| **Approver(s)**        | ANE project stakeholder                                    |

### Companion Documents

| Document ID            | Title                                              | Relationship                    |
|------------------------|----------------------------------------------------|---------------------------------|
| `STRS-ANE-EDGE-001`    | Edge Sensor Stakeholder Requirements Specification | G0-validated upstream contract  |
| `SYRS-ANE-EDGE-001`    | Edge Sensor System Requirements Specification      | G0-validated upstream contract  |
| `SRS-ANE-001`          | Full-System SRS (Phase 2)                          | Parent system requirements      |

> **Note:** The SRS is the software engineering output of G1. Every REQ- block
> traces back to a SyRS SYS- block; the design does not invent requirements the
> upstream pair does not justify.

### Change Log

| Version | Date       | Author                  | Change Description               |
|---------|------------|-------------------------|----------------------------------|
| 0.1.0   | 2026-10-26 | AI-assisted design      | Initial creation                 |
| 1.0.0   | 2026-10-26 | AI-assisted design      | G1 review baseline               |

---

## 1. Introduction

### 1.1 Purpose

This document specifies the software requirements for the edge sensor that runs
on the HackRF One + Raspberry Pi 4B node. It is addressed to the implementation
team, the G1/G2 reviewers, and the ANE stakeholders who will accept the node.
It is the authoritative software contract derived from the G0-validated StRS and
SyRS.

### 1.2 Scope

In scope: SDR acquisition, DSP and measurement, detection, local storage,
connectivity and OTA, GNSS/time, antennas and radiation measurement, power-aware
operation, health monitoring, and calibration/uncertainty computation on the
node.

Out of scope: the cloud backend, web frontend, central ANE database, integration
APIs, cross-site report generation, and any function that requires an active
server connection. Those belong to `SRS-ANE-001` and downstream systems.

### 1.3 Definitions, Acronyms, and Abbreviations

| Term       | Definition                                                          |
|------------|---------------------------------------------------------------------|
| SRS        | Software Requirements Specification (this document)                 |
| StRS       | Stakeholder Requirements Specification — upstream (G0)              |
| SyRS       | System Requirements Specification — upstream (G0)                   |
| ASR        | Architecturally Significant Requirement                             |
| ANE        | National Spectrum Agency (Agencia Nacional del Espectro)            |
| DANL       | Displayed Average Noise Level                                       |
| GUM        | Guide to the Expression of Uncertainty in Measurement (JCGM 100)    |
| ICNIRP     | International Commission on Non-Ionizing Radiation Protection       |
| ITU        | International Telecommunication Union                               |
| OBW        | Occupied Bandwidth                                                  |
| RBW / VBW  | Resolution Bandwidth / Video Bandwidth                              |
| SDR        | Software-Defined Radio (HackRF One)                                 |
| CS8        | Complex signed 8-bit IQ sample format                               |
| OTA        | Over-The-Air software update                                        |
| WAL        | SQLite Write-Ahead Logging mode                                     |

### 1.4 References

| Ref ID     | Document                                                               | Version / Date      |
|------------|------------------------------------------------------------------------|---------------------|
| `REF-001`  | ITU-R SM.1537 — Automation and requirements of monitoring stations     | In force            |
| `REF-002`  | ITU-R SM.1138 — Monitoring sensitivity and selectivity                 | In force            |
| `REF-003`  | ITU-T K.113 — Electric field measurement in urban environments         | In force            |
| `REF-004`  | ITU-T K.100 — Assessment of human exposure to electromagnetic fields   | In force            |
| `REF-007`  | IEEE/ISO/IEC 29148:2018 — Requirements engineering                     | 2018                |
| `REF-DS-001` | HackRF One Datasheet / Specifications                                | Rev 2024            |
| `REF-DS-002` | Raspberry Pi 4 Model B Datasheet                                     | Rev 2023            |
| `REF-DRV-001` | libhackrf API Documentation                                         | v2024.02.1          |
| `REF-DRV-002` | SoapySDR API Documentation                                          | v0.8                |
| `REF-GUM`     | JCGM 100:2008 — Evaluation of measurement data (GUM)                | 2008                |
| `REF-ICNIRP`  | ICNIRP 2010 — Exposure limits for time-varying fields               | 2010                |
| `REF-SYRS`    | `SYRS-ANE-EDGE-001` — Companion System Requirements Specification   | 2.0.0 / 2026-10-22  |
| `REF-STRS`    | `STRS-ANE-EDGE-001` — Companion Stakeholder Requirements Specification | 2.0.0 / 2026-10-22 |

### 1.5 Document Overview

Section 2 describes the software architecture, library selections, and
implementation constraints. Section 3 holds the REQ- blocks grouped by module.
Sections 4–6 define algorithms, schemas, interfaces, and error behavior.
Section 7 lists the test specifications, and Section 8 closes traceability from
every REQ- block to its SYS- and STK- roots.

---

## 2. Software Design Specification

### 2.1 Software Architecture Overview

The software follows the ATAM-selected **Layered Modular Pipeline** (`Arch_01`)
with timing discipline borrowed from the real-time candidate and contract
discipline borrowed from the service-mesh candidate. It is a single process
with five layers:

```
API / Operations      C-SVC-API, C-SVC-HEALTH, C-SVC-POWER, C-SVC-OTA
Application services  C-SVC-SCHED, C-SVC-ACQ, C-SVC-DSP, C-SVC-MEAS,
                      C-SVC-DET, C-SVC-CAL, C-SVC-NAV, C-SVC-STORE,
                      C-SVC-LINK, C-SVC-ANT, C-SVC-EMC
Kernel                C-KRN-CONFIG, C-KRN-UNITS, C-KRN-UNCERT, C-KRN-DIAG
Ports                 IIQSource, ISpectrumSink, IMeasurandSink,
                      ICalibrationContext, ITimePosition, IRecordStore,
                      ILink, IAntennaControl, IHealthReport, IPowerBudget
Adapters              SDR, GNSS, clock, links, OTA, storage, filesystem,
                      antenna, power, environmental sensors
```

Data flow: `C-SVC-ACQ` produces framed CS8 IQ → `C-SVC-DSP` computes traces and
demodulated streams → `C-SVC-MEAS` and `C-SVC-DET` produce measurands and
events → `C-SVC-STORE` persists metadata-first and `C-SVC-LINK` uploads from a
durable outbox. `C-SVC-CAL` and `C-SVC-NAV` supply calibration and time/position
context to every record. `C-SVC-HEALTH` supervises deadlines and drives the
degradation ladder.

Bounded SPSC rings connect stages. Acquisition never blocks: drop-oldest with a
sequence gap is the policy, and the gap flag is part of every derived record.
The acquisition thread is pinned to a dedicated core and USB/network IRQs are
steered away from it. This is the A3 borrowing that addresses risk R-03.

### 2.2 Library and Framework Selections

| Library / Framework | Version | Purpose | Selection Rationale | Alternatives Considered |
|---------------------|---------|---------|---------------------|-------------------------|
| SoapySDR | 0.8.x | SDR abstraction and streaming | Stable vendor-neutral API with a HackRF backend; isolates libhackrf and allows replay through a file source | Direct libhackrf (vendor lock-in), UHD (no HackRF support) |
| FFTW | 3.3.10 | FFT and windowing | Mature, fast on ARMv8 with NEON; predictable planning; widely validated numerically | KissFFT (slower), liquid-dsp (larger surface), numpy (runtime cost) |
| SQLite | 3.45.x | Metadata and configuration store | ACID, WAL concurrency, single-file backup, no server process on a constrained node | PostgreSQL (too heavy), flat JSON (no transactions) |
| libgps (gpsd) | 3.25 | GNSS fix ingestion | Standard NMEA/UBX client, separates device handling from application logic | Custom serial parser (more code, more risk) |
| ModemManager | 1.22 | LTE/5G modem control | D-Bus API covers attach, signal, and SIM state; avoids vendor AT commands | Raw AT commands (fragile), vendor SDKs (lock-in) |
| NetworkManager | 1.46 | Ethernet/WiFi link management | Declarative connection profiles, D-Bus state signals, carrier detection | wpa_supplicant directly (missing Ethernet/routing), systemd-networkd (less WiFi support) |
| OpenSSL | 3.2 | OTA signature verification and TLS | FIPS-adjacent, well-audited primitives; libcrypto covers Ed25519/RSA verification | libsodium (fewer TLS facilities), mbedTLS (smaller ecosystem) |
| Catch2 | 3.6 | Unit and integration tests | Header-friendly, expressive assertions, works with CTest on ARM | GoogleTest (heavier), custom harness (reinvention) |

### 2.3 Implementation Constraints

- Language: C++17 for runtime components; Python 3.11 only for tooling and
  test orchestration.
- Target: Raspberry Pi 4B, 4 GB RAM, quad-core Cortex-A72, Linux 6.x; no GPU
  compute assumptions.
- Memory budget: resident set ≤ 1.5 GB under nominal load; no dynamic allocation
  on the acquisition thread; preallocated IQ rings.
- Bus limit: USB 2.0 measured sustained throughput is below the 40 MB/s needed
  for 20 MS/s CS8; the software must represent gaps explicitly and never claim
  gapless raw recording.
- Time base: monotonic clock for intervals; UTC for records; NTP/PPS discipline
  when available.
- Security: no inbound listening service except a read-only local API; SSH
  key-only; OTA bundles signed and verified before staging.
- Thermal: the software must degrade gracefully when the SoC throttles and must
  record the throttling state with affected measurements.

---

## 3. Software Requirements

### Block ID Convention

```
REQ-[SUB]-[NNN]
```

| Segment | Rule                                    | Example             |
|---------|-----------------------------------------|---------------------|
| `SUB`   | 2–4 uppercase letters — module group    | `ACQ`, `DSP`, `NET` |
| `NNN`   | 3-digit zero-padded sequence            | `001`, `042`        |

> **Regex:** `^REQ-[A-Z]{2,4}-\d{3}$`
> Every block carries a `Traces to` field naming the SyRS `SYS-` block(s) it
> derives from. No REQ- block exists without upstream justification.

### Fields per Block

| Field                  | Required | Type              | Description                                                     |
|------------------------|----------|-------------------|-----------------------------------------------------------------|
| `id`                   | yes      | string            | Unique ID per the convention above                              |
| `title`                | yes      | string (≤120 ch)  | Descriptive name                                                |
| `type`                 | yes      | enum              | `FUNCTIONAL` \| `NON_FUNCTIONAL` \| `INTERFACE` \| `CONSTRAINT` |
| `priority`             | yes      | enum              | `MUST` \| `SHOULD` \| `COULD` \| `WONT`                         |
| `status`               | yes      | enum              | `PROPOSED` \| `APPROVED` \| `IMPLEMENTED` \| `VERIFIED` \| `REJECTED` |
| `verification`         | yes      | enum              | `INSPECTION` \| `DEMONSTRATION` \| `TEST` \| `ANALYSIS`         |
| `traces_to`            | yes      | string[]          | SyRS `SYS-` block ID(s) this requirement derives from           |
| `library`              | no       | string            | Library/framework used to satisfy it (listed in §2.2)           |
| `dependencies`         | no       | string[]          | IDs of REQ- blocks this one depends on                          |
| `notes`                | no       | string            | Technical remarks                                               |

### Block Format

Each requirement is a `REQ-[SUB]-[NNN]` block with a field table, a SHALL
description, numbered acceptance criteria, and a test specification reference.

### 3.1 Acquisition (ACQ)

**`REQ-ACQ-001` — Wideband spectrum acquisition**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                              |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `TEST`                                                    |
| **Traces to**          | `SYS-RF-002`                                              |
| **Library**            | SoapySDR                                                  |
| **Dependencies**       | —                                                         |

**Description:**
The software SHALL configure and stream from the SDR across 1 MHz–6 GHz in
tuning bands, applying the band plan and per-band sensitivity metadata before
the first sample of each band.

**Acceptance Criteria:**

1. [ ] Every configured band from 1 MHz to 6 GHz is tuned and captured.
2. [ ] Trace metadata identifies band edges where sensitivity is degraded.

**Test Specification:**
`TC-001` — sweep the full range against a calibrated signal generator.

**Notes:**
Band plan derived from `HWC-SDR-001`; no pre-selection filters exist, so band
transitions must be explicit in metadata.

---

**`REQ-ACQ-002` — Real-time 20 MHz capture with gap accounting**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                              |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `TEST`                                                    |
| **Traces to**          | `SYS-RF-003`                                              |
| **Library**            | SoapySDR                                                  |
| **Dependencies**       | `REQ-ACQ-001`                                             |

**Description:**
The software SHALL capture up to 20 MS/s in CS8 format, stamp every frame with
a monotonic sequence number and timestamp, detect dropped samples, and expose a
gap flag and cumulative gap count to downstream stages within 1 second.

**Acceptance Criteria:**

1. [ ] A 20 MHz wide signal is captured and processed with latency ≤ 1 s.
2. [ ] Induced USB overruns produce frame gap flags and a non-zero gap count.
3. [ ] No downstream stage blocks the acquisition thread.

**Test Specification:**
`TC-002` — capture a 20 MHz noise signal while injecting bus load; assert gaps
are flagged and latency remains ≤ 1 s.

**Notes:**
USB 2.0 throughput is below the 40 MB/s required for sustained 20 MS/s CS8;
gaps are a first-class output, not an error to hide.

---

**`REQ-ACQ-003` — Internal spur and ambient survey annotation**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                              |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `TEST`                                                    |
| **Traces to**          | `SYS-RF-001`                                              |
| **Library**            | —                                                         |
| **Dependencies**       | `REQ-ACQ-001`                                             |

**Description:**
The software SHALL maintain an internal-spur catalog and annotate any trace
whose bins overlap a catalogued spur, and SHALL execute an ambient EMC survey
for the configured dwell time, storing the result with its survey parameters.

**Acceptance Criteria:**

1. [ ] Traces overlapping a catalogued spur carry a spur annotation.
2. [ ] An ambient survey completes for the configured dwell and is persisted.

**Test Specification:**
`TC-003` — inject a known internal spur and confirm annotation; run a 60 s
ambient survey and confirm the stored record.

---

### 3.2 Spectrum Processing (DSP)

**`REQ-DSP-001` — Span and RBW configuration**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                              |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `TEST`                                                    |
| **Traces to**          | `SYS-DSP-001`                                             |
| **Library**            | —                                                         |
| **Dependencies**       | `REQ-ACQ-001`                                             |

**Description:**
The software SHALL accept start frequency, stop frequency, and requested RBW,
derive FFT length, window, and decimation, and reject any combination the
hardware cannot realize before retuning, returning a diagnostic naming the
limiting parameter.

**Acceptance Criteria:**

1. [ ] Valid span/RBW requests apply to the next sweep.
2. [ ] An impossible request (for example RBW below the sample-rate limit) is
   rejected with the limiting parameter named.

**Test Specification:**
`TC-004` — apply valid and invalid span/RBW combinations and assert acceptance
or diagnostic.

---

**`REQ-DSP-002` — RBW and VBW realization**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                              |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `TEST`                                                    |
| **Traces to**          | `SYS-DSP-002`                                             |
| **Library**            | FFTW                                                      |
| **Dependencies**       | `REQ-DSP-001`                                             |

**Description:**
The software SHALL realize the selected RBW and VBW on the next sweep, with
measured RBW within ±10% of the requested value for supported combinations.

**Acceptance Criteria:**

1. [ ] RBW/VBW changes are reflected in the next sweep.
2. [ ] Measured RBW is within ±10% of the request across the supported matrix.

**Test Specification:**
`TC-005` — sweep RBW/VBW combinations and measure the response to a CW tone.

---

**`REQ-DSP-003` — Spectral trace computation**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                              |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `TEST`                                                    |
| **Traces to**          | `SYS-MEAS-001`                                            |
| **Library**            | FFTW                                                      |
| **Dependencies**       | `REQ-DSP-002`                                             |

**Description:**
The software SHALL compute max-hold, min-hold, and average traces with a
selectable detector, a configurable number of FFT averages, a monotonic
timestamp, and the gap, calibration, and configuration metadata required by the
record schema.

**Acceptance Criteria:**

1. [ ] Max, min, and average traces are produced for a configured capture.
2. [ ] Every trace carries timestamp, gap count, calibration version, and
   configuration version.

**Test Specification:**
`TC-006` — compute all detector traces from recorded IQ and compare against
golden outputs.

---

### 3.3 Measurement (MEAS)

**`REQ-MEAS-001` — Occupied bandwidth**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                              |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `TEST`                                                    |
| **Traces to**          | `SYS-MEAS-002`                                            |
| **Library**            | —                                                         |
| **Dependencies**       | `REQ-DSP-003`                                             |

**Description:**
The software SHALL compute occupied bandwidth containing 99% of integrated
power by default, with 90% and 95% selectable, following the ITU-R SM.1537
method, and SHALL report the result with its uncertainty.

**Acceptance Criteria:**

1. [ ] OBW is within ±1 RBW of the reference value for a calibrated signal.
2. [ ] The 90/95/99% selections produce consistent, monotonic results.

**Test Specification:**
`TC-007` — measure OBW of a calibrated modulated signal and compare with the
reference analyzer.

---

**`REQ-MEAS-002` — Channel power**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                              |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `TEST`                                                    |
| **Traces to**          | `SYS-MEAS-003`                                            |
| **Library**            | —                                                         |
| **Dependencies**       | `REQ-DSP-003`                                             |

**Description:**
The software SHALL integrate power over the configured channel bandwidth and
report channel power in dBm with a GUM-consistent uncertainty.

**Acceptance Criteria:**

1. [ ] Channel power is within ±1 dB of the calibrated reference.
2. [ ] Every result includes its uncertainty and integration bandwidth.

**Test Specification:**
`TC-008` — measure channel power of a calibrated signal at three levels.

---

**`REQ-MEAS-003` — RDS decoding in FM**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                              |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `TEST`                                                    |
| **Traces to**          | `SYS-MEAS-004`                                            |
| **Library**            | —                                                         |
| **Dependencies**       | `REQ-MEAS-004`                                            |

**Description:**
The software SHALL decode RDS groups from FM broadcasts, recover PI, PS, and
RadioText where present, verify group CRCs, and report block error rate.

**Acceptance Criteria:**

1. [ ] A reference RDS broadcast yields the correct PI and PS.
2. [ ] CRC failures are counted and reported as block error rate.

**Test Specification:**
`TC-009` — decode a recorded RDS capture and compare PI/PS/RT with the reference.

---

**`REQ-MEAS-004` — AM and FM demodulation and modulation metrics**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                              |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `TEST`                                                    |
| **Traces to**          | `SYS-MEAS-005`                                            |
| **Library**            | —                                                         |
| **Dependencies**       | `REQ-DSP-003`                                             |

**Description:**
The software SHALL demodulate AM and FM signals and compute modulation depth
(AM), frequency deviation (FM), and modulation index where applicable, reporting
each with its measurement bandwidth.

**Acceptance Criteria:**

1. [ ] AM modulation depth is within ±2 percentage points of the reference.
2. [ ] FM deviation is within ±5% of the reference.

**Test Specification:**
`TC-010` — demodulate calibrated AM/FM signals with known modulation and compare.

---

**`REQ-MEAS-005` — Audio extraction for verification**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                              |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `TEST`                                                    |
| **Traces to**          | `SYS-VER-002`                                             |
| **Library**            | —                                                         |
| **Dependencies**       | `REQ-MEAS-004`                                             |

**Description:**
The software SHALL extract demodulated audio to 48 kHz mono WAV segments of at
most 60 seconds, labelled with frequency, timestamp, and demodulation mode.

**Acceptance Criteria:**

1. [ ] A 60 s FM capture produces a playable WAV with correct duration.
2. [ ] The file name and sidecar carry frequency, timestamp, and mode.

**Test Specification:**
`TC-011` — extract audio from a recorded FM signal and verify duration and metadata.

---

### 3.4 Detection (DET)

**`REQ-DET-001` — Detection threshold configuration**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                              |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `TEST`                                                    |
| **Traces to**          | `SYS-DSP-004`                                             |
| **Library**            | —                                                         |
| **Dependencies**       | `REQ-DSP-003`                                             |

**Description:**
The software SHALL evaluate declarative detection rules with absolute or
noise-floor-relative thresholds, hysteresis, and dwell time, and SHALL emit a
detection event only when the rule is satisfied for the configured dwell.

**Acceptance Criteria:**

1. [ ] A signal above threshold for the dwell emits exactly one event.
2. [ ] A signal below threshold or shorter than the dwell emits none.

**Test Specification:**
`TC-012` — replay traces with known signals and assert event counts.

---

**`REQ-DET-002` — Intermodulation detection**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                              |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `TEST`                                                    |
| **Traces to**          | `SYS-VER-001`                                             |
| **Library**            | —                                                         |
| **Dependencies**       | `REQ-DET-001`, `REQ-MEAS-001`                             |

**Description:**
The software SHALL enumerate second- and third-order intermodulation products
from the configured carrier list, check for spectral energy within the RBW plus
a configured guard at each product frequency, and flag matching products.

**Acceptance Criteria:**

1. [ ] Known two-tone products are flagged at the correct frequencies.
2. [ ] Products outside the guard band are not flagged.

**Test Specification:**
`TC-013` — inject two tones and a product tone; assert detection at the product.

---

**`REQ-DET-003` — Interference classification**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                              |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `TEST`                                                    |
| **Traces to**          | `SYS-VER-001`                                             |
| **Library**            | —                                                         |
| **Dependencies**       | `REQ-DET-002`, `REQ-MEAS-002`                             |

**Description:**
The software SHALL classify each detection as narrowband, wideband, pulsed, or
continuous using occupied bandwidth, duty cycle, and duration, and SHALL persist
the classification with the event.

**Acceptance Criteria:**

1. [ ] A CW tone is classified as narrowband and continuous.
2. [ ] A pulsed wideband source is classified as pulsed and wideband.

**Test Specification:**
`TC-014` — replay recorded narrowband, wideband, and pulsed sources.

---

### 3.5 Geolocation and Time (NAV)

**`REQ-NAV-001` — Manual coordinate entry**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                              |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `TEST`                                                    |
| **Traces to**          | `SYS-NAV-001`                                             |
| **Library**            | —                                                         |
| **Dependencies**       | —                                                         |

**Description:**
The software SHALL accept manual latitude, longitude, and altitude, validate
latitude in −90…+90 degrees, longitude in −180…+180 degrees, and altitude in
−500…9000 m, persist the value, and stamp subsequent records with its source.

**Acceptance Criteria:**

1. [ ] Valid coordinates are stored and stamped on the next record.
2. [ ] Out-of-range coordinates are rejected with a field-specific diagnostic.

**Test Specification:**
`TC-015` — submit valid and invalid coordinate sets.

---

**`REQ-NAV-002` — GNSS position and time**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                              |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `TEST`                                                    |
| **Traces to**          | `SYS-NAV-002`                                             |
| **Library**            | libgps                                                    |
| **Dependencies**       | —                                                         |

**Description:**
The software SHALL ingest GNSS fixes, use a valid fix in preference to manual
coordinates, mark the position source, and provide UTC time with the fix; when
the fix is lost it SHALL fall back to manual coordinates without blocking
acquisition.

**Acceptance Criteria:**

1. [ ] A valid fix is used and marked as GNSS in subsequent records.
2. [ ] Fix loss falls back to manual coordinates and records the fallback.
3. [ ] Horizontal accuracy is ≤ 3 m (CEP 50%) in open sky.

**Test Specification:**
`TC-016` — compare GNSS fixes with a surveyed reference point.

---

**`REQ-NAV-003` — Measurement unit conversion**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                              |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `TEST`                                                    |
| **Traces to**          | `SYS-DSP-003`                                             |
| **Library**            | —                                                         |
| **Dependencies**       | —                                                         |

**Description:**
The software SHALL convert among dBm, dBµV, dBµV/m, W, and V/m using documented
formulas and impedance assumptions, with a round-trip error ≤ 0.01 dB.

**Acceptance Criteria:**

1. [ ] Each supported conversion round-trips within ±0.01 dB.
2. [ ] The unit and formula version are recorded with the converted value.

**Test Specification:**
`TC-017` — convert a matrix of values and assert round-trip error.

---

### 3.6 Storage (STO)

**`REQ-STO-001` — Measurement record storage**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                              |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `TEST`                                                    |
| **Traces to**          | `SYS-STO-001`                                             |
| **Library**            | SQLite                                                    |
| **Dependencies**       | —                                                         |

**Description:**
The software SHALL persist every measurement as an immutable record with
metadata committed before any payload acknowledgement, using SQLite WAL mode,
and SHALL include a content hash and schema version in each record.

**Acceptance Criteria:**

1. [ ] A measurement is queryable by scan ID, timestamp, and frequency.
2. [ ] Metadata is committed before the payload is acknowledged.
3. [ ] An interrupted write leaves no partially valid record.

**Test Specification:**
`TC-018` — write records, interrupt a write, and verify database consistency.

---

**`REQ-STO-002` — Raw IQ segmented storage and retention**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                              |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `TEST`                                                    |
| **Traces to**          | `SYS-STO-001`                                             |
| **Library**            | —                                                         |
| **Dependencies**       | `REQ-STO-001`                                             |

**Description:**
The software SHALL store raw IQ in bounded segments with a sidecar manifest,
publish each segment by atomic rename after fsync, and enforce retention by age
and total size without deleting segments that are pending upload.

**Acceptance Criteria:**

1. [ ] A recorded segment has a manifest matching its byte length and hash.
2. [ ] Retention removes only expired, uploaded segments.
3. [ ] An interrupted segment is quarantined and not reported as valid.

**Test Specification:**
`TC-019` — record, interrupt, retain, and verify segment integrity.

---

### 3.7 Connectivity (NET)

**`REQ-NET-001` — Cellular backhaul link**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `INTERFACE`                                               |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `TEST`                                                    |
| **Traces to**          | `SYS-NET-001`                                             |
| **Library**            | ModemManager                                              |
| **Dependencies**       | —                                                         |

**Description:**
The software SHALL bring up the cellular modem, attach to the network, obtain an
IP address, expose link state, and retry attachment with exponential backoff
after failure.

**Acceptance Criteria:**

1. [ ] The modem attaches and obtains an address on a valid SIM.
2. [ ] Failed attachment retries with backoff and reports link state.

**Test Specification:**
`TC-020` — attach with a test SIM and simulate attach failure.

---

**`REQ-NET-002` — WiFi link**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `INTERFACE`                                               |
| **Priority**           | `SHOULD`                                                  |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `TEST`                                                    |
| **Traces to**          | `SYS-NET-002`                                             |
| **Library**            | NetworkManager                                            |
| **Dependencies**       | —                                                         |

**Description:**
The software SHALL associate with the configured WiFi network using WPA2 or
WPA3, obtain an address, and expose link state, preferring WiFi over cellular
when both are available.

**Acceptance Criteria:**

1. [ ] The node associates and obtains an address on the configured network.
2. [ ] WiFi is preferred over cellular when its signal meets the configured floor.

**Test Specification:**
`TC-021` — associate to a test access point and verify preference.

---

**`REQ-NET-003` — Ethernet fallback and routing**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `INTERFACE`                                               |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `TEST`                                                    |
| **Traces to**          | `SYS-NET-003`                                             |
| **Library**            | NetworkManager                                            |
| **Dependencies**       | `REQ-NET-001`, `REQ-NET-002`                              |

**Description:**
The software SHALL select the active link in the order Ethernet, WiFi, cellular;
fail over within 5 seconds of carrier loss; and upload each record exactly once
using idempotency keys across link changes.

**Acceptance Criteria:**

1. [ ] Ethernet carrier presence pre-empts WiFi and cellular.
2. [ ] Carrier loss triggers failover within 5 s.
3. [ ] A record interrupted by failover is uploaded once, not duplicated.

**Test Specification:**
`TC-022` — switch links during an upload and verify single delivery.

---

**`REQ-NET-004` — Remote access and OTA update**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `INTERFACE`                                               |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `TEST`                                                    |
| **Traces to**          | `SYS-NET-004`                                             |
| **Library**            | OpenSSL                                                   |
| **Dependencies**       | `REQ-NET-003`                                             |

**Description:**
The software SHALL provide SSH key-only remote access and SHALL stage only
signature-verified OTA bundles into an inactive A/B slot, run a self-test after
switch, and roll back automatically if the self-test fails.

**Acceptance Criteria:**

1. [ ] An unsigned or invalid bundle is rejected before staging.
2. [ ] A failed post-switch self-test restores the previous slot.
3. [ ] Password authentication is disabled on SSH.

**Test Specification:**
`TC-023` — sign, stage, switch, and simulate self-test failure.

---

### 3.8 Antennas and Radiation (ANT)

**`REQ-ANT-001` — Band antenna selection**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                              |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `TEST`                                                    |
| **Traces to**          | `SYS-ANT-001`                                             |
| **Library**            | —                                                         |
| **Dependencies**       | —                                                         |

**Description:**
The software SHALL select the antenna or probe port for the configured band,
enforce the configured settle time before capture, and record the selected port
and antenna-factor table version with the measurement.

**Acceptance Criteria:**

1. [ ] Each band selects its mapped port and records the port ID.
2. [ ] Capture starts only after the settle interval has elapsed.

**Test Specification:**
`TC-024` — switch across bands and verify port and settle gating.

---

**`REQ-ANT-002` — Field strength and radiation measurement**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                              |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `TEST`                                                    |
| **Traces to**          | `SYS-ANT-002`                                             |
| **Library**            | —                                                         |
| **Dependencies**       | `REQ-ANT-001`, `REQ-CAL-001`                              |

**Description:**
The software SHALL compute electric field strength in dBµV/m from received
power, antenna factor, and cable loss, support the active radiation probe, and
annotate results with the applicable ICNIRP reference level where configured.

**Acceptance Criteria:**

1. [ ] Field strength is within ±2 dB of a calibrated reference field.
2. [ ] Results include antenna factor, cable loss, and ICNIRP annotation flag.

**Test Specification:**
`TC-025` — measure a calibrated field in a TEM cell.

---

### 3.9 Power (PWR)

**`REQ-PWR-001` — Power budget and load shedding**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `NON_FUNCTIONAL`                                          |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `TEST`                                                    |
| **Traces to**          | `SYS-PWR-001`                                             |
| **Library**            | —                                                         |
| **Dependencies**       | —                                                         |

**Description:**
The software SHALL estimate the remaining energy budget from battery and solar
telemetry, enforce the allowed scan duty cycle, shed non-essential loads (WiFi,
raw IQ recording) at configured thresholds, and report the current power state
with every scan.

**Acceptance Criteria:**

1. [ ] The duty cycle is reduced when the energy budget falls below threshold.
2. [ ] Load shedding disables the configured non-essential functions.
3. [ ] Power state is attached to each scan record.

**Test Specification:**
`TC-026` — simulate battery depletion and assert the load-shed sequence.

---

### 3.10 Monitoring and Scheduling (MON)

**`REQ-MON-001` — Health and connectivity monitoring**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `NON_FUNCTIONAL`                                          |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `TEST`                                                    |
| **Traces to**          | `SYS-MON-001`                                             |
| **Library**            | —                                                         |
| **Dependencies**       | `REQ-ACQ-002`, `REQ-STO-001`, `REQ-NET-003`               |

**Description:**
The software SHALL monitor SDR liveness, DSP deadline misses, storage capacity,
link state, temperature, and power, expose a consolidated health report, and
mark the affected scan degraded when a monitored resource fails.

**Acceptance Criteria:**

1. [ ] Killing the SDR stream is detected and reported within 5 s.
2. [ ] A missed DSP deadline is reflected in the health report and scan metadata.
3. [ ] Disk and thermal thresholds trigger the documented degraded state.

**Test Specification:**
`TC-027` — fault-inject SDR, disk, and link failures and assert health states.

---

**`REQ-MON-002` — Scheduled spectrum scan**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                              |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `TEST`                                                    |
| **Traces to**          | `SYS-MON-002`                                             |
| **Library**            | —                                                         |
| **Dependencies**       | `REQ-DSP-001`, `REQ-PWR-001`                              |

**Description:**
The software SHALL execute a persisted scan schedule with configured dwell and
retune budgets, resume schedules after power loss without duplicating completed
scans, and record each scheduled run with its plan version.

**Acceptance Criteria:**

1. [ ] A schedule executes at the configured times with the configured dwell.
2. [ ] A power interruption mid-scan resumes without duplicating completed runs.
3. [ ] Each run records the plan version and actual dwell.

**Test Specification:**
`TC-028` — run a schedule, interrupt power, and verify resume behavior.

---

### 3.11 Calibration and Uncertainty (CAL)

**`REQ-CAL-001` — Calibration corrections**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                              |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `TEST`                                                    |
| **Traces to**          | `SYS-CAL-001`                                             |
| **Library**            | —                                                         |
| **Dependencies**       | —                                                         |

**Description:**
The software SHALL load frequency-response, antenna-factor, and cable-loss
calibration tables, apply their corrections to measurements, stamp the table
version and validity interval on every corrected record, and reject an expired
table for compliant reporting.

**Acceptance Criteria:**

1. [ ] Corrected values match the reference correction within ±0.1 dB.
2. [ ] The table version and validity interval are recorded.
3. [ ] An expired table marks the record non-compliant, not silently valid.

**Test Specification:**
`TC-029` — apply calibration tables and verify corrections and version stamps.

---

**`REQ-CAL-002` — Uncertainty budget**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `NON_FUNCTIONAL`                                          |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `ANALYSIS`                                                |
| **Traces to**          | `SYS-CAL-001`                                             |
| **Library**            | —                                                         |
| **Dependencies**       | `REQ-CAL-001`                                             |

**Description:**
The software SHALL compute a GUM combined standard uncertainty from typed
contributions (calibration, noise, mismatch, drift), report expanded uncertainty
at coverage factor k = 2, and store the contribution list with each measurand.

**Acceptance Criteria:**

1. [ ] Combined uncertainty matches the GUM reference calculation within 1%.
2. [ ] Expanded uncertainty uses k = 2 and is labelled as such.
3. [ ] The contribution list is persisted with the record.

**Test Specification:**
`TC-030` — compare against a worked GUM example.

---

**`REQ-CAL-003` — Time synchronization**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `NON_FUNCTIONAL`                                          |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `TEST`                                                    |
| **Traces to**          | `SYS-CAL-001`                                             |
| **Library**            | —                                                         |
| **Dependencies**       | `REQ-NAV-002`                                             |

**Description:**
The software SHALL discipline the system clock using NTP and PPS when available,
maintain a monotonic time base for intervals, report the current offset, and
refuse to stamp a compliant record when the absolute offset exceeds 1 ms.

**Acceptance Criteria:**

1. [ ] Clock offset is reported before and after discipline.
2. [ ] Records with offset above 1 ms are marked non-compliant.
3. [ ] Monotonic intervals are unaffected by UTC step changes.

**Test Specification:**
`TC-031` — step the reference clock and verify offset handling.

---

## 4. Algorithms and Data Schemas

### 4.1 Algorithms

| Algorithm | Used By (Blocks) | Inputs | Outputs | Notes |
|-----------|------------------|--------|---------|-------|
| Windowed FFT with configurable length | `REQ-DSP-002`, `REQ-DSP-003` | CS8 IQ frames, FFT length, window | Complex spectrum | FFTW plan cached per geometry; no per-frame allocation |
| Detector trace aggregation | `REQ-DSP-003` | Spectrum frames, detector mode | Max/min/average trace | Running max/min; exponential average |
| 99% occupied bandwidth | `REQ-MEAS-001` | Trace power bins, RBW | OBW in Hz | Cumulative power until 0.5% below and 99.5% above |
| Channel power integration | `REQ-MEAS-002` | Trace bins, channel bandwidth | Power in dBm | Sum of bin powers with RBW correction |
| FM quadrature demodulation | `REQ-MEAS-004` | IQ stream | Audio, deviation | Phase difference; de-emphasis optional |
| AM envelope demodulation | `REQ-MEAS-004` | IQ stream | Audio, depth | Envelope magnitude; DC removal |
| RDS group decoder | `REQ-MEAS-003` | 57 kHz subcarrier stream | PI, PS, RT, BER | CRC-10 per group; block sync state machine |
| Intermodulation product enumeration | `REQ-DET-002` | Carrier list, orders | Product frequencies | 2f1−f2, f1+f2, 2f1+f2, etc.; deduplicated |
| Threshold state machine | `REQ-DET-001` | Trace bins, rules, dwell | Events | Hysteresis and dwell counters |
| GUM combined uncertainty | `REQ-CAL-002` | Contribution list | u_c, U | Root-sum-square; sensitivity coefficients |
| Calibration correction | `REQ-CAL-001` | Raw value, tables | Corrected value | Frequency interpolation; validity check |
| Gap accounting | `REQ-ACQ-002` | Frame sequence numbers | Gap count, flags | Expected-vs-observed sequence |
| Link selection | `REQ-NET-003` | Carrier, signal, policy | Active link | Priority Ethernet > WiFi > cellular |

### 4.2 Data Schemas

| Schema | Used By (Blocks) | Format | Fields | Versioning |
|--------|------------------|--------|--------|------------|
| `IQFrame` | `REQ-ACQ-002`, `REQ-DSP-003` | Binary header + CS8 payload | sequence, timestamp_ns, center_hz, sample_rate, gap_flag, payload_bytes | `schema_version` in header |
| `SpectrumTrace` | `REQ-DSP-003` | JSON + binary bins | trace_id, scan_id, start_hz, stop_hz, rbw_hz, vbw_hz, detector, bins, gap_count, cal_version, config_version | SemVer in `schema_version` |
| `MeasurandRecord` | `REQ-MEAS-*`, `REQ-CAL-002` | JSON | measurand_id, value, unit, uncertainty, k_factor, cal_version, time_fix_id, config_version | SemVer |
| `CalibrationContext` | `REQ-CAL-001`, `REQ-ANT-002` | JSON | table_version, valid_from, valid_to, antenna_factor, cable_loss, frequency_points | Dated table version |
| `TimePosition` | `REQ-NAV-002`, `REQ-CAL-003` | JSON | fix_id, source, lat, lon, alt_m, utc, monotonic_ns, offset_ns | `schema_version` |
| `ScanPlan` | `REQ-MON-002` | JSON | plan_version, entries[], dwell_s, retune_s, antenna_port, link_policy | Semantic plan version |
| `HealthReport` | `REQ-MON-001` | JSON | component, state, deadline_misses, temperature_c, power_state, timestamp | `schema_version` |
| `OtaManifest` | `REQ-NET-004` | JSON + signature | bundle_version, slot, sha256, signature, min_self_test | Signed manifest version |

---

## 5. Interfaces

### 5.1 External Interfaces

| Interface | Peer | Protocol / Physical | Requirements |
|-----------|------|---------------------|--------------|
| SDR control and IQ | HackRF One | USB 2.0, SoapySDR | `REQ-ACQ-001`, `REQ-ACQ-002` |
| GNSS | GPS module | Serial UART, NMEA/UBX via gpsd | `REQ-NAV-002` |
| Cellular | 4G/5G modem | USB, ModemManager D-Bus | `REQ-NET-001` |
| WiFi | Access point | 802.11, WPA2/WPA3, NetworkManager | `REQ-NET-002` |
| Ethernet | Site network | 1000BASE-T, NetworkManager | `REQ-NET-003` |
| Antenna switch | Antenna multiplexer | GPIO | `REQ-ANT-001` |
| Power telemetry | Battery/solar monitor | I2C (INA219-class) | `REQ-PWR-001` |
| Storage | SSD/microSD | Block device, filesystem | `REQ-STO-001`, `REQ-STO-002` |

### 5.2 Internal Interfaces

| Interface | Provider → Consumer | Contract |
|-----------|---------------------|----------|
| `IIQSource` | `C-SVC-ACQ` → `C-SVC-DSP` | frame index, sequence, timestamp, gap flag, CS8 view |
| `ISpectrumSink` | `C-SVC-DSP` → `C-SVC-MEAS` | trace bins, RBW/VBW, detector, config version |
| `IMeasurandSink` | `C-SVC-MEAS` → `C-SVC-STORE`/`C-SVC-LINK` | measurand, unit, uncertainty, calibration context |
| `ICalibrationContext` | `C-SVC-CAL` → `C-SVC-MEAS`/`C-SVC-ANT` | table version, validity, antenna factor, cable loss |
| `ITimePosition` | `C-SVC-NAV` → record producers | fix ID, position, UTC, monotonic offset, source |
| `IRecordStore` | `C-SVC-STORE` → producers | commit, read, retention |
| `ILink` | `C-SVC-LINK` → `C-SVC-OTA`/`C-SVC-API` | link state, send, outbox depth, idempotency key |
| `IAntennaControl` | `C-SVC-ANT` → `C-SVC-ACQ` | select port, settle-complete, interlock |
| `IHealthReport` | `C-SVC-HEALTH` → `C-SVC-API`/`C-SVC-OTA` | heartbeats, deadline misses, thermal/power, verdict |
| `IPowerBudget` | `C-SVC-POWER` → `C-SVC-SCHED` | remaining energy, allowed duty cycle, shed tier |

### 5.3 Data Interfaces

Persisted data uses the schemas in §4.2. File formats: SQLite for metadata,
segmented binary for IQ, JSON for records and manifests, WAV for extracted
audio. All records carry a schema version and content hash. Uploads use HTTPS
with idempotency keys; OTA bundles use signed manifests.

---

## 6. Error Behavior

| Failure Mode | Trigger | Detected By (Blocks) | Behavior |
|--------------|---------|----------------------|----------|
| USB sample overrun | Sustained throughput above bus ceiling | `REQ-ACQ-002` | Drop oldest frame, set gap flag, increment gap count, continue |
| SDR disconnect | USB reset or device removal | `REQ-MON-001` | Mark scan degraded, attempt re-open with backoff, report health fault |
| Impossible scan request | Span/RBW beyond capability | `REQ-DSP-001` | Reject before retune, name the limiting parameter, keep previous plan |
| GNSS fix loss | Antenna obstruction or receiver fault | `REQ-NAV-002` | Fall back to manual coordinates, mark source, continue capture |
| Clock offset exceeds limit | NTP/PPS unavailable or drifted | `REQ-CAL-003` | Mark records non-compliant, report offset, continue local capture |
| Storage full | Retention cannot free space | `REQ-STO-002`, `REQ-MON-001` | Stop raw recording, keep metadata, shed load, report health |
| Link loss | Carrier or modem failure | `REQ-NET-003` | Queue in durable outbox, fail over, upload once on recovery |
| Thermal throttling | SoC temperature above threshold | `REQ-MON-001` | Walk degradation ladder, record throttling state with measurements |
| Expired calibration | Table validity ended | `REQ-CAL-001` | Mark records non-compliant, continue acquisition, require update |
| OTA self-test failure | New slot fails health check | `REQ-NET-004` | Roll back to previous slot, keep bundle for diagnosis |
| Antenna switch fault | No settle feedback | `REQ-ANT-001` | Abort capture for that band, report fault, do not publish trace |
| Process crash | Software fault or watchdog | `REQ-MON-001` | systemd restart, recover state from SQLite, mark in-flight scans interrupted |

---

## 7. Test Specifications

| Test Case | Requirement | Type | Stimulus | Expected Result |
|-----------|-------------|------|----------|-----------------|
| `TC-001` | `REQ-ACQ-001` | SYSTEM | Calibrated signal generator across 1 MHz–6 GHz | Every band captured with edge metadata |
| `TC-002` | `REQ-ACQ-002` | SYSTEM | 20 MHz noise plus induced USB load | Latency ≤ 1 s; gaps flagged and counted |
| `TC-003` | `REQ-ACQ-003` | SYSTEM | Known spur plus 60 s ambient survey | Spur annotated; survey persisted |
| `TC-004` | `REQ-DSP-001` | UNIT | Valid and impossible span/RBW sets | Valid applied; invalid rejected with parameter |
| `TC-005` | `REQ-DSP-002` | UNIT | RBW/VBW matrix against CW tone | Measured RBW within ±10% |
| `TC-006` | `REQ-DSP-003` | UNIT | Recorded IQ with known traces | Max/min/average match golden files |
| `TC-007` | `REQ-MEAS-001` | UNIT | Calibrated modulated signal | OBW within ±1 RBW of reference |
| `TC-008` | `REQ-MEAS-002` | UNIT | Calibrated signal at three levels | Channel power within ±1 dB |
| `TC-009` | `REQ-MEAS-003` | INTEGRATION | Recorded RDS broadcast | Correct PI/PS/RT; BER reported |
| `TC-010` | `REQ-MEAS-004` | UNIT | Calibrated AM/FM signals | Depth ±2 points; deviation ±5% |
| `TC-011` | `REQ-MEAS-005` | INTEGRATION | 60 s FM capture | Playable WAV with correct metadata |
| `TC-012` | `REQ-DET-001` | UNIT | Traces above/below threshold | Exactly one event for qualifying signal |
| `TC-013` | `REQ-DET-002` | UNIT | Two tones plus product tone | Product flagged; out-of-guard ignored |
| `TC-014` | `REQ-DET-003` | UNIT | Narrowband, wideband, pulsed sources | Correct classifications persisted |
| `TC-015` | `REQ-NAV-001` | UNIT | Valid and invalid coordinates | Valid stored; invalid field-specific error |
| `TC-016` | `REQ-NAV-002` | SYSTEM | GNSS fixes at surveyed point | Source marked GNSS; CEP ≤ 3 m |
| `TC-017` | `REQ-NAV-003` | UNIT | Conversion matrix | Round-trip error ≤ 0.01 dB |
| `TC-018` | `REQ-STO-001` | INTEGRATION | Write records and interrupt | Consistent DB; no partial record |
| `TC-019` | `REQ-STO-002` | INTEGRATION | Record, interrupt, retain | Manifest matches; only expired uploaded segments removed |
| `TC-020` | `REQ-NET-001` | SYSTEM | Test SIM and attach failure | Attach or backoff with link state |
| `TC-021` | `REQ-NET-002` | SYSTEM | Test AP and signal floor | Association; WiFi preferred |
| `TC-022` | `REQ-NET-003` | SYSTEM | Link switch during upload | Failover ≤ 5 s; single delivery |
| `TC-023` | `REQ-NET-004` | SYSTEM | Signed, invalid, and failing bundles | Reject invalid; rollback on failure |
| `TC-024` | `REQ-ANT-001` | INTEGRATION | Band switch across ports | Correct port; capture after settle |
| `TC-025` | `REQ-ANT-002` | SYSTEM | Calibrated field in TEM cell | Field within ±2 dB; metadata present |
| `TC-026` | `REQ-PWR-001` | SYSTEM | Simulated battery depletion | Duty cycle reduced; shed sequence correct |
| `TC-027` | `REQ-MON-001` | INTEGRATION | SDR, disk, and link fault injection | Health states and degraded scans correct |
| `TC-028` | `REQ-MON-002` | SYSTEM | Schedule run plus power interruption | Resume without duplicate runs |
| `TC-029` | `REQ-CAL-001` | TEST | Calibration tables and expired table | Corrections within ±0.1 dB; expired non-compliant |
| `TC-030` | `REQ-CAL-002` | TEST | Worked GUM example | Combined uncertainty within 1%; k = 2 |
| `TC-031` | `REQ-CAL-003` | SYSTEM | Clock step and PPS loss | Offset reported; > 1 ms non-compliant |

---

## 8. Traceability

| Requirement ID | SyRS Traces | StRS Root(s) | Test Case | Component |
|----------------|-------------|--------------|-----------|-----------|
| `REQ-ACQ-001` | `SYS-RF-002` | `STK-RNG-001` | `TC-001` | `C-SVC-ACQ` |
| `REQ-ACQ-002` | `SYS-RF-003` | `STK-RNG-002` | `TC-002` | `C-SVC-ACQ` |
| `REQ-ACQ-003` | `SYS-RF-001` | `STK-EMC-001` | `TC-003` | `C-SVC-EMC` |
| `REQ-DSP-001` | `SYS-DSP-001` | `STK-PAR-001`, `STK-PAR-003` | `TC-004` | `C-SVC-DSP` |
| `REQ-DSP-002` | `SYS-DSP-002` | `STK-PAR-002`, `STK-PAR-004` | `TC-005` | `C-SVC-DSP` |
| `REQ-DSP-003` | `SYS-MEAS-001` | `STK-MED-001` | `TC-006` | `C-SVC-DSP` |
| `REQ-MEAS-001` | `SYS-MEAS-002` | `STK-MED-003` | `TC-007` | `C-SVC-MEAS` |
| `REQ-MEAS-002` | `SYS-MEAS-003` | `STK-MED-004` | `TC-008` | `C-SVC-MEAS` |
| `REQ-MEAS-003` | `SYS-MEAS-004` | `STK-MED-005` | `TC-009` | `C-SVC-MEAS` |
| `REQ-MEAS-004` | `SYS-MEAS-005` | `STK-MED-006`, `STK-MED-007` | `TC-010` | `C-SVC-MEAS` |
| `REQ-MEAS-005` | `SYS-VER-002` | `STK-SRV-002` | `TC-011` | `C-SVC-MEAS` |
| `REQ-DET-001` | `SYS-DSP-004` | `STK-PAR-007` | `TC-012` | `C-SVC-DET` |
| `REQ-DET-002` | `SYS-VER-001` | `STK-VER-001`, `STK-VER-002` | `TC-013` | `C-SVC-DET` |
| `REQ-DET-003` | `SYS-VER-001` | `STK-VER-001`, `STK-VER-002` | `TC-014` | `C-SVC-DET` |
| `REQ-NAV-001` | `SYS-NAV-001` | `STK-PAR-005` | `TC-015` | `C-SVC-NAV` |
| `REQ-NAV-002` | `SYS-NAV-002` | `STK-GPS-001`, `STK-GPS-002` | `TC-016` | `C-SVC-NAV` |
| `REQ-NAV-003` | `SYS-DSP-003` | `STK-PAR-006` | `TC-017` | `C-KRN-UNITS` |
| `REQ-STO-001` | `SYS-STO-001` | `STK-ALM-001`, `STK-ALM-003` | `TC-018` | `C-SVC-STORE` |
| `REQ-STO-002` | `SYS-STO-001` | `STK-ALM-001`, `STK-ALM-003` | `TC-019` | `C-SVC-STORE` |
| `REQ-NET-001` | `SYS-NET-001` | `STK-RED-001` | `TC-020` | `C-SVC-LINK` |
| `REQ-NET-002` | `SYS-NET-002` | `STK-RED-002` | `TC-021` | `C-SVC-LINK` |
| `REQ-NET-003` | `SYS-NET-003` | `STK-RED-003`, `STK-RED-004` | `TC-022` | `C-SVC-LINK` |
| `REQ-NET-004` | `SYS-NET-004` | `STK-SOP-001` | `TC-023` | `C-SVC-OTA` |
| `REQ-ANT-001` | `SYS-ANT-001` | `STK-ANT-001`, `STK-ANT-002` | `TC-024` | `C-SVC-ANT` |
| `REQ-ANT-002` | `SYS-ANT-002` | `STK-RNI-001`, `STK-RNI-002` | `TC-025` | `C-SVC-ANT` |
| `REQ-PWR-001` | `SYS-PWR-001` | `STK-AUT-001` | `TC-026` | `C-SVC-POWER` |
| `REQ-MON-001` | `SYS-MON-001` | `STK-MON-001`, `STK-MON-002` | `TC-027` | `C-SVC-HEALTH` |
| `REQ-MON-002` | `SYS-MON-002` | `STK-PRG-001` | `TC-028` | `C-SVC-SCHED` |
| `REQ-CAL-001` | `SYS-CAL-001` | `STK-CAL-001`, `STK-CAR-001`, `STK-CAR-002`, `STK-CAR-003`, `STK-CAR-004`, `STK-CAR-005` | `TC-029` | `C-SVC-CAL` |
| `REQ-CAL-002` | `SYS-CAL-001` | `STK-CAL-001`, `STK-CAR-001`, `STK-CAR-002`, `STK-CAR-003`, `STK-CAR-004`, `STK-CAR-005` | `TC-030` | `C-KRN-UNCERT` |
| `REQ-CAL-003` | `SYS-CAL-001` | `STK-SIN-001` | `TC-031` | `C-SVC-NAV` |

---

## G1 Validation Rules (structural)

Compliance status for this document:

1. **Metadata** — Document ID, Project, Organization, Version (SemVer), and
   Classification are present and non-placeholder.
2. **Required sections** — all template sections exist.
3. **ID format** — every block matches `^REQ-[A-Z]{2,4}-\d{3}$` and is unique.
4. **Traceability upstream** — every `Traces to` value resolves to a `SYS-`
   block in `GT/G0_SyRS.md`.
5. **Testable SHALL** — every block has a SHALL/SHOULD description, at least one
   acceptance criterion, and a §7 test case.
6. **Justified selections** — every §2.2 library row has a non-empty rationale.
7. **Internal consistency** — dependencies resolve to REQ- blocks and form an
   acyclic graph; §8 lists every REQ- block.

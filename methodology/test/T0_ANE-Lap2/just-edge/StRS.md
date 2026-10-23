# PROJECT: Edge Sensor — ANE Spectrum Monitoring System

## Stakeholder Requirements Specification (StRS)

> **Standard:** IEEE/ISO/IEC 29148:2018 — *Systems and software engineering — Life cycle processes — Requirements engineering.*
>
> **Template version:** 3.0.0  
> **Creation date:** 2026-10-13  
> **Last modified:** 2026-10-13  
> **Document status:** `APPROVED`

---

## Document Metadata

| Field                  | Value                                                      |
|------------------------|------------------------------------------------------------|
| **Document ID**        | `STRS-ANE-EDGE-001`                                        |
| **Project**            | Edge Sensor — Spectrum Monitoring Subsystem (Phase 2)      |
| **Organization**       | National Spectrum Agency (ANE) — Colombia                  |
| **Version**            | 2.0.0                                                     |
| **Classification**     | `INTERNAL`                                                |
| **Author(s)**          | _To be defined_                                           |
| **Reviewer(s)**        | _To be defined_                                           |
| **Approver(s)**        | _To be defined_                                           |

### Companion Documents

| Document ID            | Title                                                   | Relationship              |
|------------------------|---------------------------------------------------------|---------------------------|
| `SYRS-ANE-EDGE-001`   | Edge Sensor System Requirements Specification           | Per-measurand derived specification (G0 pair) |
| `SRS-ANE-001`         | Full-System SRS (Phase 2)                               | Parent system requirements |

> **Note:** This document merges the former Hardware Constraints Specification: COTS platform limits live in §1.6/§2.6/§2.7 and as HWC- blocks in §3. The companion SyRS-ANE-EDGE-001 derives per-measurand specifications from this document.

### Change Log

| Version | Date       | Author                 | Change Description                          |
|---------|------------|------------------------|---------------------------------------------|
| 0.1.0   | 2026-10-13 | AI-assisted generation | Initial extraction from SRS-ANE-001         |
| 1.0.0   | 2026-10-13 | AI-assisted generation | Approved — IEEE 29148 v3 structure          |
| 2.0.0   | 2026-10-22 | Migration              | StRS per IEEE 29148 §9.4 — merged HCS, inline compliance |

---

## 1. Introduction

### 1.1 Purpose

This document specifies the requirements for the **edge sensor** as a self-contained subsystem of the ANE Spectrum Monitoring System. It covers exclusively what runs on the embedded node (HackRF One + Raspberry Pi): SDR driver, DSP pipeline (PSD, FFT, traces), demodulation, network connectivity (4G/5G, WiFi, Ethernet), GPIO multiplexing, GPS, local storage, autonomous power, and calibration.

**It excludes:** the cloud backend, the web frontend, integration APIs, the ANE centralized database, report generation, and any logic that requires an active connection to the server.

### 1.2 Scope

The edge sensor is an autonomous spectrum-monitoring node based on an SDR (HackRF One) running on a Raspberry Pi. It captures, processes, and locally stores spectral data in the 1 MHz – 6 GHz range. It operates independently on solar/battery power with 4G/5G/WiFi/Ethernet connectivity.

**The edge sensor does NOT include:** a web graphical interface, a centralized dashboard, comparison against the authorized-emissions database, formal report generation, or a REST API for external consumption.

### 1.3 Definitions, Acronyms, and Abbreviations

| Term       | Definition                                                                           |
|------------|--------------------------------------------------------------------------------------|
| ANE        | National Spectrum Agency (Agencia Nacional del Espectro, Colombia)                   |
| SDR        | Software Defined Radio                                                               |
| RBW        | Resolution Bandwidth                                                                 |
| VBW        | Video Bandwidth                                                                      |
| DANL       | Displayed Average Noise Level                                                        |
| RDS        | Radio Data System (FM radio data)                                                   |
| OBW        | Occupied Bandwidth                                                                   |
| PSD        | Power Spectral Density                                                               |
| FFT        | Fast Fourier Transform                                                               |
| CS8        | Complex Signed 8-bit — the HackRF IQ sample format                                  |
| AF         | Antenna Factor                                                                       |
| HCS        | Hardware Constraints Specification — companion document                              |
| OTA        | Over The Air — remote software update                                               |

### 1.4 References

| Ref ID     | Document                                                               | Version / Date      |
|------------|------------------------------------------------------------------------|---------------------|
| `REF-001`  | ITU-R SM.1537 — Automation and requirements of monitoring stations     | In force            |
| `REF-002`  | ITU-R SM.1138 — Monitoring sensitivity and selectivity                 | In force            |
| `REF-003`  | ITU-T K.113 — Electric field measurement in urban environments         | In force            |
| `REF-004`  | ITU-T K.100 — Assessment of human exposure to electromagnetic fields   | In force            |
| `REF-007`  | IEEE/ISO/IEC 29148:2018 — Requirements engineering                     | 2018                |
| `REF-DS-001`  | HackRF One Datasheet / Specifications                           | Rev 2024                |
| `REF-DS-002`  | Raspberry Pi 4 Model B Datasheet                                | Rev 2023                |
| `REF-DS-003`  | BCM2711 (RPi 4B SoC) Datasheet                                 | Broadcom, 2019          |
| `REF-DRV-001` | libhackrf API Documentation                                    | v2024.02.1              |
| `REF-DRV-002` | SoapySDR API Documentation                                     | v0.8                    |
| `REF-DRV-003` | Linux USB 2.0 Subsystem Documentation                           | Kernel 6.x              |
| `REF-MEAS-001`| HackRF DANL Characterization (measured)                         | _To be performed_       |
| `REF-MEAS-002`| USB 2.0 Sustained Throughput Test (measured)                    | _To be performed_       |
| `REF-GUM`     | JCGM 100:2008 — Evaluation of measurement data (GUM)            | 2008                    |
| `REF-ICNIRP`  | ICNIRP 2010 — Exposure limits for time-varying electric and magnetic fields | 2010     |
| `REF-SYRS`    | SYRS-ANE-EDGE-001 — Companion System Requirements Specification  | 2.0.0 / 2026-10-22      |

### 1.5 Document Overview

Section 3 contains specific requirements organized by subsystem. Section 4 covers external interfaces. Section 5 covers non-functional requirements. Section 6 presents the traceability matrix.
### 1.6 Hardware Inventory

| Component ID | Component Name         | Role in System                        | Manufacturer       | Part Number         |
|-------------|------------------------|---------------------------------------|---------------------|---------------------|
| `HW-SDR`   | HackRF One             | SDR receiver / transmitter            | Great Scott Gadgets  | HackRF One          |
| `HW-CPU`   | Raspberry Pi 4 Model B | Embedded processing platform          | Raspberry Pi Foundation | RPi 4B 4GB/8GB  |
| `HW-GPS`   | GPS Module (TBD)       | Geolocation and timing                | TBD                 | TBD                 |
| `HW-4G5G`  | 4G/5G Modem (TBD)     | Mobile data connectivity              | TBD                 | TBD                 |
| `HW-MUX`   | Antenna Multiplexer    | RF path switching between antennas    | TBD                 | TBD                 |
| `HW-PWR`   | Solar + Battery System | Autonomous power supply               | TBD                 | TBD                 |
| `HW-STR`   | SSD / microSD          | Local data storage                    | TBD                 | TBD                 |


---

## 2. Overall System Description

### 2.1 Product Perspective

This document describes the edge sensor as a subsystem of the full system (SRS-ANE-001). The sensor operates as an autonomous node for spectral acquisition and preprocessing.

#### 2.1.1 Context Diagram

```
                    ┌─────────────────────────────────────────────┐
                    │            EDGE SENSOR (RPi + HackRF)       │
                    │                                             │
 ┌─────────┐  SMA  │  ┌──────────┐   USB    ┌──────────────┐    │
 │ Antennas │◄─────►│  │ HackRF   │◄────────►│  Raspberry   │    │
 │ (band)   │       │  │ One      │  IQ raw  │  Pi          │    │
 └─────────┘       │  └──────────┘          │              │    │
                    │                        │  ┌─────────┐ │    │
 ┌─────────┐  UART │                        │  │ DSP     │ │    │
 │ GPS     │◄──────┤                        │  │ Pipeline│ │    │
 └─────────┘       │                        │  └─────────┘ │    │
                    │                        │  ┌─────────┐ │    │
 ┌─────────┐  GPIO │                        │  │ Storage │ │    │
 │ Mux/    │◄──────┤                        │  │ (local) │ │    │
 │ Switch  │       │                        │  └─────────┘ │    │
 └─────────┘       │                        └──────────────┘    │
                    │                               │            │
 ┌─────────┐  USB  │                          ┌────┴─────┐      │
 │ 4G/5G   │◄──────┤                          │ Failover │      │
 │ Module  │       │                          │ Network  │      │
 └─────────┘       │                          └──────────┘      │
                    │                                             │
 ┌─────────┐       │  ┌───────────────────────────────────┐      │
 │ Solar + │◄──────┤  │ Battery Manager + Charge Control  │      │
 │ Battery │       │  └───────────────────────────────────┘      │
 └─────────┘       └─────────────────────────────────────────────┘
```

### 2.2 Product Functions

Real-time spectrum capture (1 MHz–6 GHz), DSP processing (FFT, PSD, traces, RBW/VBW), FM/AM demodulation, signal-parameter measurement (OBW, channel power, modulation), intermodulation and interference detection, local forensic storage (JSON + CS8), autonomous connectivity management (4G/WiFi/ETH failover), NTP synchronization, and node health monitoring.

### 2.3 User Characteristics

| User Type         | Description                                      | Technical Level |
|-------------------|--------------------------------------------------|-----------------|
| Spectrum engineer | Configures the sensor parameters via remote access | `EXPERT`        |
| Field technician  | Installs, calibrates, and maintains the sensor   | `TECHNICAL`     |

### 2.4 Constraints

Summary of hardware constraints (see HCS-ANE-EDGE-001 for parametric details):

- **RF front-end:** HackRF One — 1 MHz to 6 GHz, 20 MHz instantaneous BW, 8-bit IQ (CS8), manual gain only.
- **Processing:** Raspberry Pi 4B — 4× Cortex-A72 @ 1.8 GHz, 4/8 GB RAM.
- **Data bus:** USB 2.0 (~32 MB/s sustained vs. 40 MB/s IQ rate).
- **Power:** Solar + battery, ~15 W total system consumption.

### 2.5 Assumptions and Dependencies

- The ANE provides data SIM cards for mobile connectivity.
- Sensors are deployed at sites with mains power or viable solar.
- Antennas are correctly connected and calibrated for the operating band.
### 2.6 Block Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                    EDGE SENSOR NODE                               │
│                                                                   │
│  ┌─────────────┐    USB 2.0     ┌──────────────────────┐         │
│  │  HackRF One │◄──────────────►│  Raspberry Pi 4B     │         │
│  │  [HW-SDR]   │   IQ (CS8)    │  [HW-CPU]            │         │
│  └──────┬──────┘               │                      │         │
│         │ SMA                   │  ┌────────────────┐  │         │
│  ┌──────┴──────┐               │  │ DSP Pipeline   │  │         │
│  │ Antenna Mux │               │  │ (software)     │  │         │
│  │ [HW-MUX]   │               │  └────────────────┘  │         │
│  └──────┬──────┘               │                      │         │
│         │ SMA                   │  ┌────────────────┐  │         │
│  ┌──────┴──────┐               │  │ Storage        │  │         │
│  │  Antennas   │               │  │ [HW-STR]       │  │         │
│  │  (per band) │               │  └────────────────┘  │         │
│  └─────────────┘               └──────────┬───────────┘         │
│                                           │                      │
│  ┌─────────────┐  UART/USB    ┌──────────┴──────────┐           │
│  │ GPS Module  │◄────────────►│  Peripheral Bus     │           │
│  │ [HW-GPS]   │              │  (USB/UART/GPIO)    │           │
│  └─────────────┘              └──────────┬──────────┘           │
│                                          │                       │
│  ┌─────────────┐  USB         ┌──────────┴──────────┐           │
│  │ 4G/5G Modem │◄────────────►│  Network Manager    │           │
│  │ [HW-4G5G]  │              │  (software)         │           │
│  └─────────────┘              └─────────────────────┘           │
│                                                                   │
│  ┌────────────────────────────────────────────┐                  │
│  │ Solar Panel + Battery + Charge Manager     │                  │
│  │ [HW-PWR]                                   │                  │
│  └────────────────────────────────────────────┘                  │
└──────────────────────────────────────────────────────────────────┘
```

### 2.7 Bus and Interface Topology

| From       | To         | Bus/Protocol | Data Rate (theoretical) | Data Rate (sustained) |
|------------|------------|-------------|-------------------------|----------------------|
| HW-SDR     | HW-CPU     | USB 2.0     | 480 Mbps                | ~256 Mbps (~32 MB/s) |
| HW-GPS     | HW-CPU     | UART / USB  | 9600 baud (NMEA)        | < 1 KB/s             |
| HW-4G5G   | HW-CPU     | USB         | Varies by modem         | Carrier-dependent    |
| HW-MUX     | HW-CPU     | GPIO        | N/A (control signals)   | N/A                  |
| HW-STR     | HW-CPU     | USB 3.0 / microSD | 5 Gbps / 104 MB/s | ~400 MB/s / ~90 MB/s |


---

## 3. Specific Requirements

---

### 3.1 Sensor RF Architecture

#### 3.1.1 Electromagnetic Compatibility

---

**`STK-EMC-001` — Sensor EMC optimization**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `NON_FUNCTIONAL`                                          |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `TEST`                                                   |
| **Standard(s)**        | —                                                        |
| **Dependencies**       | —                                                        |
| **Phase**              | 2025–2026                                                |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `NOT_APPLICABLE` |

**Description:**  
The system SHALL incorporate filtering in the sensor's receive path and RF shielding to prevent spurious signals generated by its own electronics from appearing in measurement results.

**Acceptance Criteria:**

1. [ ] Internal spurious emissions are ≥ 10 dB below the operating noise floor.
2. [ ] RF shielding is implemented between internal modules.
3. [ ] A before/after comparative measurement demonstrates reduction in EMC artifacts.

**Notes:**  
The HackRF lacks pre-selection filters, so its broadband front-end is susceptible to internal EMI. An RF gasket + board-level shielding provides physical mitigation. The DSP pipeline characterizes known internal spurious frequencies and flags them.

---

#### 3.1.2 Spectral Range

---

**`STK-RNG-001` — Frequency-range coverage**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `DEMONSTRATION`                                          |
| **Standard(s)**        | ITU-R SM.1537; `REF-001`                                 |
| **Dependencies**       | —                                                        |
| **Phase**              | 2025–2026                                                |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `NOT_APPLICABLE` |

**Description:**  
The system SHALL capture emissions from 1 MHz up to 6 GHz.

**Acceptance Criteria:**

1. [ ] The system receives and processes signals in the 1 MHz – 6 GHz range.
2. [ ] Sensitivity at 1 MHz and 6 GHz is verifiable with a calibrated signal generator.

**Notes:**  
Sensitivity degrades at band edges (below 10 MHz and above 4 GHz). Characterization per band is required.

---

**`STK-RNG-002` — Real-time monitoring bandwidth**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `TEST`                                                   |
| **Standard(s)**        | —                                                        |
| **Dependencies**       | —                                                        |
| **Phase**              | 2025–2026                                                |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `NOT_APPLICABLE` |

**Description:**  
The system SHALL provide real-time monitoring with a configurable bandwidth between 6 MHz and 20 MHz, and an automatic mode fixed at 20 MHz.

**Acceptance Criteria:**

1. [ ] Bandwidth configurable between 6 MHz and 20 MHz in discrete steps.
2. [ ] In automatic mode, the span is fixed at 20 MHz.
3. [ ] DSP pipeline processes the full bandwidth with latency ≤ 1 second.

**Notes:**  
At 20 MS/s, sample drops are possible due to the USB 2.0 bottleneck (~32 MB/s sustained vs. 40 MB/s IQ rate). The DSP pipeline tolerates or detects them.

---

### 3.2 DSP Parameterization

#### 3.2.1 Frequency and Resolution Parameters

---

**`STK-PAR-001` — Parameterizable frequency range**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `DEMONSTRATION`                                          |
| **Standard(s)**        | —                                                        |
| **Dependencies**       | `STK-RNG-001`                                           |
| **Phase**              | 2025–2026                                                |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `NOT_APPLICABLE` |

**Description:**  
The system SHALL allow the user to define frequency ranges within the 1 MHz – 6 GHz envelope (center+span or start+stop).

**Acceptance Criteria:**

1. [ ] Center frequency + span, or start + stop frequency, are configurable.
2. [ ] The system validates that the requested range is within hardware limits.
3. [ ] Range changes are applied in real time without restart.

---

**`STK-PAR-002` — RBW configuration**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `TEST`                                                   |
| **Standard(s)**        | —                                                        |
| **Dependencies**       | `STK-PAR-001`                                           |
| **Phase**              | 2025–2026                                                |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `NOT_APPLICABLE` |

**Description:**  
The system SHALL allow the resolution bandwidth (RBW) to be configured over a defined range (≥ 6 discrete values).

**Acceptance Criteria:**

1. [ ] RBW is user-configurable across ≥ 6 discrete values.
2. [ ] Changing RBW updates the DSP pipeline in real time.

---

**`STK-PAR-003` — Frequency-resolution steps**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `TEST`                                                   |
| **Standard(s)**        | —                                                        |
| **Dependencies**       | `STK-PAR-002`                                           |
| **Phase**              | 2025–2026                                                |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `NOT_APPLICABLE` |

**Description:**  
The system SHALL offer resolution steps of 500 Hz, with a minimum resolution of 10 Hz.

**Acceptance Criteria:**

1. [ ] Frequency step is configurable in 500 Hz increments.
2. [ ] Minimum achievable resolution is 10 Hz.
3. [ ] Step accuracy is verified against a signal generator.

**Notes:**  
10 Hz resolution at 20 MS/s requires a 2,000,000-point FFT — computationally intensive. May require reduced sample rates for the finest resolutions.

---

**`STK-PAR-004` — VBW configuration**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `TEST`                                                   |
| **Standard(s)**        | —                                                        |
| **Dependencies**       | `STK-PAR-002`                                           |
| **Phase**              | 2025–2026                                                |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `NOT_APPLICABLE` |

**Description:**  
The system SHALL implement Video Bandwidth (VBW) filters suited to fine or averaged analysis.

**Acceptance Criteria:**

1. [ ] VBW is configurable independently of RBW.
2. [ ] Filters for fine and averaged analysis are available.
3. [ ] DSP output shows a perceptible difference between modes.

---

#### 3.2.2 Location and Units

---

**`STK-PAR-005` — Manual entry of GPS coordinates**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `DEMONSTRATION`                                          |
| **Standard(s)**        | —                                                        |
| **Dependencies**       | —                                                        |
| **Phase**              | 2025–2026                                                |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `NOT_APPLICABLE` |

**Description:**  
The system SHALL allow the sensor's location coordinates to be entered manually when automatic GPS is unavailable.

**Acceptance Criteria:**

1. [ ] Latitude and longitude can be entered manually.
2. [ ] Manual coordinates are associated with measurements.
3. [ ] The system records whether the location source is GPS or manual.

---

**`STK-PAR-006` — Measurement unit conversion**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `DEMONSTRATION`                                          |
| **Standard(s)**        | —                                                        |
| **Dependencies**       | —                                                        |
| **Phase**              | 2025–2026                                                |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `NOT_APPLICABLE` |

**Description:**  
The system SHALL allow selection and conversion of measurement units: frequency (Hz, kHz, MHz, GHz), power (dBm, dBmV, dBµV, V, W), and field/power density (V/m, W/m², dBµV/m).

**Acceptance Criteria:**

1. [ ] All listed units are available as output options.
2. [ ] Conversion error < 0.01 dB.

---

#### 3.2.3 Thresholds and Detection

---

**`STK-PAR-007` — Analysis and detection thresholds**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `TEST`                                                   |
| **Standard(s)**        | —                                                        |
| **Dependencies**       | —                                                        |
| **Phase**              | 2025–2026                                                |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `NOT_APPLICABLE` |

**Description:**  
The system SHALL allow detection thresholds to be parameterized and SHALL distinguish the noise floor from signal occupancy.

**Acceptance Criteria:**

1. [ ] User can define a power threshold in dBm for signal detection.
2. [ ] The algorithm distinguishes the noise floor from active signals.
3. [ ] Signals above the threshold are flagged in the output data.

**Notes:**  
Detection sensitivity is bounded by the receiver's DANL (~−100 dBm/Hz).

---

### 3.3 Signal Processing (DSP)

#### 3.3.1 Indicators and Traces

---

**`STK-MED-001` — Spectral traces**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `DEMONSTRATION`                                          |
| **Standard(s)**        | ITU-R SM.1537; `REF-001`                                 |
| **Dependencies**       | `STK-PAR-001`                                           |
| **Phase**              | 2025–2026                                                |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `NOT_APPLICABLE` |

**Description:**  
The system SHALL compute spectral traces: max hold, min hold, average, and RMS; with peak, average, and RMS detection modes.

**Acceptance Criteria:**

1. [ ] Max trace retains the highest value per bin.
2. [ ] Min trace retains the lowest value per bin.
3. [ ] Average trace computes the arithmetic mean over N sweeps (N configurable).
4. [ ] Detection modes (peak, average, RMS) are selectable.

---

#### 3.3.2 Signal Measurements

---

**`STK-MED-003` — Occupied-bandwidth measurement**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `TEST`                                                   |
| **Standard(s)**        | ITU-R SM.1537; `REF-001`                                 |
| **Dependencies**       | `STK-MED-001`                                           |
| **Phase**              | 2025–2026                                                |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `NOT_APPLICABLE` |

**Description:**  
The system SHALL measure the occupied bandwidth (OBW) using the –X dB and 99% methods.

**Acceptance Criteria:**

1. [ ] –X dB method: bandwidth where the signal falls X dB below peak.
2. [ ] 99% method: bandwidth containing 99% of total signal power.
3. [ ] Results expressed in the selected frequency unit.

**Notes:**  
OBW measurement limited to signals within the 20 MHz instantaneous BW. Wider signals require sweep mode.

---

**`STK-MED-004` — Channel power measurement**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `TEST`                                                   |
| **Standard(s)**        | —                                                        |
| **Dependencies**       | `STK-RNG-002`                                           |
| **Phase**              | 2025–2026                                                |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `NOT_APPLICABLE` |

**Description:**  
The system SHALL perform channel-power measurements for emissions up to 20 MHz wide.

**Acceptance Criteria:**

1. [ ] Channel-power measurement is selectable via configuration.
2. [ ] Channel width configurable up to 20 MHz.
3. [ ] Result expressed in selected power units.

---

#### 3.3.3 Sound Broadcasting

---

**`STK-MED-005` — RDS reading in FM**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `DEMONSTRATION`                                          |
| **Standard(s)**        | —                                                        |
| **Dependencies**       | —                                                        |
| **Phase**              | 2025–2026                                                |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `NOT_APPLICABLE` |

**Description:**  
The system SHALL decode and extract RDS information from FM signals (PI, PS, RT fields).

**Acceptance Criteria:**

1. [ ] Basic RDS fields (PI, PS, RT) are decoded.
2. [ ] RDS data is included in the output alongside FM measurements.

---

**`STK-MED-006` — FM and AM demodulation**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `DEMONSTRATION`                                          |
| **Standard(s)**        | —                                                        |
| **Dependencies**       | `STK-RNG-001`                                           |
| **Phase**              | 2025–2026                                                |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `NOT_APPLICABLE` |

**Description:**  
The system SHALL demodulate FM and AM signals in real time, producing digital audio.

**Acceptance Criteria:**

1. [ ] FM audio demodulated with audible quality.
2. [ ] AM audio demodulated with audible quality (from 1 MHz).
3. [ ] Demodulated audio is stored locally or transmitted as a stream.

**Notes:**  
AM reception at 1 MHz is at the lower edge of the receiver's range. Sensitivity degradation below 10 MHz may affect AM quality.

---

**`STK-MED-007` — AM and FM modulation measurement**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `TEST`                                                   |
| **Standard(s)**        | —                                                        |
| **Dependencies**       | `STK-MED-006`                                           |
| **Phase**              | 2025–2026                                                |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `NOT_APPLICABLE` |

**Description:**  
The system SHALL measure AM modulation depth (%) and FM frequency deviation (kHz) in real time.

**Acceptance Criteria:**

1. [ ] AM modulation depth computed as percentage.
2. [ ] FM frequency deviation computed in kHz.
3. [ ] Values update in real time during demodulation.

---

### 3.4 Local (Edge) Detection

#### 3.4.1 Signal-Parameter Verification

---

**`STK-VER-001` — Intermodulation detection**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `TEST`                                                   |
| **Standard(s)**        | —                                                        |
| **Dependencies**       | `STK-MED-001`                                           |
| **Phase**              | 2025–2026                                                |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `NOT_APPLICABLE` |

**Description:**  
The system SHALL detect intermodulation products in AM, FM, and the aeronautical band (108–137 MHz), and perform IF verification.

**Acceptance Criteria:**

1. [ ] 2nd- and 3rd-order intermodulation products are computed for detected emissions.
2. [ ] Suspected IM products are flagged in the spectral output.
3. [ ] IF verification is performed automatically.

**Notes:**  
The detection algorithm must distinguish receiver-generated IM from real over-the-air products, since the HackRF has no pre-selection filters.

---

**`STK-VER-002` — Interference detection**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `TEST`                                                   |
| **Standard(s)**        | —                                                        |
| **Dependencies**       | `STK-PAR-007`                                           |
| **Phase**              | 2025–2026                                                |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `NOT_APPLICABLE` |

**Description:**  
The system SHALL detect interference (signals exceeding the channel average by > 3 dB) and generate a local record.

**Acceptance Criteria:**

1. [ ] Signals > 3 dB above the average are detected as potential interference.
2. [ ] A local record is generated with frequency, power, and duration.
3. [ ] Detection runs continuously without manual intervention.

---

#### 3.4.2 Audio Extraction

---

**`STK-SRV-002` — Audio extraction for verification**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `DEMONSTRATION`                                          |
| **Standard(s)**        | —                                                        |
| **Dependencies**       | `STK-MED-006`                                           |
| **Phase**              | 2025–2026                                                |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `NOT_APPLICABLE` |

**Description:**  
The system SHALL demodulate and store FM/AM audio locally for forensic analysis.

**Acceptance Criteria:**

1. [ ] Audio stored in a standard format (WAV or MP3).
2. [ ] Audio files associated with measurement metadata (frequency, timestamp, location).

---

### 3.5 Local Storage

---

**`STK-ALM-001` — Local historical storage**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `DEMONSTRATION`                                          |
| **Standard(s)**        | ITU-R SM.1537; `REF-001`                                 |
| **Dependencies**       | —                                                        |
| **Phase**              | 2025–2026                                                |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `NOT_APPLICABLE` |

**Description:**  
The system SHALL provide local historical storage for forensic analysis, including spectral data with timestamp and GPS location.

**Acceptance Criteria:**

1. [ ] Monitoring data stored locally with timestamp and GPS coordinates.
2. [ ] Historical data queryable by date range, frequency, and location.
3. [ ] Data integrity verifiable (checksum or hash).

---

**`STK-ALM-003` — Raw IQ storage**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `DEMONSTRATION`                                          |
| **Standard(s)**        | —                                                        |
| **Dependencies**       | —                                                        |
| **Phase**              | 2025–2026                                                |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `NOT_APPLICABLE` |

**Description:**  
The system SHALL store CS8 raw IQ files with metadata for forensic evidence.

**Acceptance Criteria:**

1. [ ] The sensor has accessible additional storage (USB 3.0 SSD recommended).
2. [ ] CS8 files stored with metadata (timestamp, frequency, coordinates).
3. [ ] Local storage is remotely accessible for download.

**Notes:**  
Raw CS8 at 20 MS/s = 40 MB/s. Storage must sustain ≥ 40 MB/s writes.

---

### 3.6 Edge Connectivity

#### 3.6.1 Network Interfaces

---

**`STK-RED-001` — 4G/5G module**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `DEMONSTRATION`                                          |
| **Standard(s)**        | —                                                        |
| **Dependencies**       | —                                                        |
| **Phase**              | 2025–2026                                                |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `NOT_APPLICABLE` |

**Description:**  
The system SHALL support a 4G/5G mobile-connectivity module with a data SIM card, with multi-carrier service.

**Acceptance Criteria:**

1. [ ] Supports 4G and 5G networks.
2. [ ] Works with SIM cards from ≥ 2 Colombian carriers.
3. [ ] Connection established automatically at power-on.

---

**`STK-RED-002` — WiFi connection**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `SHOULD`                                                  |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `DEMONSTRATION`                                          |
| **Standard(s)**        | —                                                        |
| **Dependencies**       | —                                                        |
| **Phase**              | 2025–2026                                                |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `NOT_APPLICABLE` |

**Description:**  
The system SHALL enable WiFi connectivity, configurable via Ethernet cable.

**Acceptance Criteria:**

1. [ ] Sensor connects to configured WiFi networks.
2. [ ] WiFi configuration performed initially over Ethernet.

---

**`STK-RED-003` — Accessible Ethernet port**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `INSPECTION`                                             |
| **Standard(s)**        | —                                                        |
| **Dependencies**       | —                                                        |
| **Phase**              | 2025–2026                                                |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `NOT_APPLICABLE` |

**Description:**  
The system SHALL provide an externally accessible Ethernet port (≥ 100 Mbps) without requiring the enclosure to be opened.

**Acceptance Criteria:**

1. [ ] Ethernet port externally accessible without tools.
2. [ ] Port supports ≥ 100 Mbps.

---

**`STK-RED-004` — Network auto-routing**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `TEST`                                                   |
| **Standard(s)**        | —                                                        |
| **Dependencies**       | `STK-RED-001`, `STK-RED-002`, `STK-RED-003`           |
| **Phase**              | 2025–2026                                                |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `NOT_APPLICABLE` |

**Description:**  
The system SHALL implement automatic network routing with failover/priority among 4G/5G, WiFi, and Ethernet.

**Acceptance Criteria:**

1. [ ] System selects the available channel with highest priority.
2. [ ] Failover occurs without manual intervention.
3. [ ] Priority order is configurable.

---

#### 3.6.2 Support and GPS

---

**`STK-SOP-001` — Remote access and OTA update**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `DEMONSTRATION`                                          |
| **Standard(s)**        | —                                                        |
| **Dependencies**       | `STK-RED-004`                                           |
| **Phase**              | 2025–2026                                                |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `NOT_APPLICABLE` |

**Description:**  
The system SHALL allow remote IP access (SSH or equivalent) and OTA software updates with automatic rollback on failure.

**Acceptance Criteria:**

1. [ ] Remote access via SSH or secure equivalent.
2. [ ] Software updates without physical access.
3. [ ] Automatic rollback on update failure.

---

**`STK-GPS-001` — GPS location redundancy**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `TEST`                                                   |
| **Standard(s)**        | —                                                        |
| **Dependencies**       | `STK-PAR-005`                                           |
| **Phase**              | 2025–2026                                                |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `NOT_APPLICABLE` |

**Description:**  
The system SHALL continue reporting automatic GPS location even when manual coordinates are configured, storing both sources.

**Acceptance Criteria:**

1. [ ] GPS reports location regardless of manual parameterization.
2. [ ] Both location sources are stored in measurement records.

---

**`STK-GPS-002` — GPS accuracy**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `NON_FUNCTIONAL`                                         |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `TEST`                                                   |
| **Standard(s)**        | —                                                        |
| **Dependencies**       | —                                                        |
| **Phase**              | 2025–2026                                                |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `NOT_APPLICABLE` |

**Description:**  
The system SHALL achieve a horizontal GPS accuracy ≤ 3 m (CEP 50%) under open sky.

**Acceptance Criteria:**

1. [ ] Horizontal accuracy ≤ 3 m (CEP 50%) under open-sky conditions.
2. [ ] Accuracy verified against a reference GPS receiver.

---

### 3.7 Antennas and Radiation Measurement

#### 3.7.1 Antennas

---

**`STK-ANT-001` — Band-specific antennas**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `INSPECTION`                                             |
| **Standard(s)**        | —                                                        |
| **Dependencies**       | `STK-RNG-001`                                           |
| **Phase**              | 2025–2026                                                |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `NOT_APPLICABLE` |

**Description:**  
The system SHALL incorporate specific antennas optimized for DTT and mobile-telephony downlink (> 2 GHz), each with a documented antenna factor (AF).

**Acceptance Criteria:**

1. [ ] DTT-specific antenna provided.
2. [ ] Antenna for frequencies > 2 GHz verified.
3. [ ] Each antenna has a documented and calibrated AF.

---

**`STK-ANT-002` — Active antenna for non-ionizing radiation**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `TEST`                                                   |
| **Standard(s)**        | ITU-T K.113, K.100; `REF-003`, `REF-004`                 |
| **Dependencies**       | —                                                        |
| **Phase**              | 2025–2026                                                |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `NOT_APPLICABLE` |

**Description:**  
The system SHALL incorporate an active antenna with coverage up to 6 GHz, SAW filter, flat response (≤ 2 dB variation), and known AF.

**Acceptance Criteria:**

1. [ ] Frequency range covers up to 6 GHz.
2. [ ] Includes a SAW filter.
3. [ ] Flat frequency response (variation ≤ 2 dB).
4. [ ] Manufacturer-documented AF.

---

#### 3.7.2 Non-Ionizing Radiation Measurement

---

**`STK-RNI-001` — Radiation measurement units**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `DEMONSTRATION`                                          |
| **Standard(s)**        | ITU-T K.113, K.100; `REF-003`, `REF-004`                 |
| **Dependencies**       | `STK-ANT-002`                                           |
| **Phase**              | 2025–2026                                                |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `NOT_APPLICABLE` |

**Description:**  
The system SHALL support measurement units for non-ionizing radiation: S (W/m²), A/m, V/m, dBµV/m, dBA/m.

**Acceptance Criteria:**

1. [ ] All listed units available as display options.
2. [ ] Conversions between units are correct.

---

**`STK-RNI-002` — Field-strength measurement**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `TEST`                                                   |
| **Standard(s)**        | ITU-T K.113, K.100; `REF-003`, `REF-004`                 |
| **Dependencies**       | `STK-ANT-002`, `STK-RNI-001`                           |
| **Phase**              | 2025–2026                                                |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `NOT_APPLICABLE` |

**Description:**  
The system SHALL measure field strength using the antenna factor: E [V/m] = V_measured [V] × AF.

**Acceptance Criteria:**

1. [ ] Field measurement uses the AF of the connected antenna.
2. [ ] Results presented in V/m and dBµV/m.

**Notes:**  
Amplitude accuracy requires a software calibration table mapping gain settings to correction factors, since the HackRF has no AGC.

---

### 3.8 Power and Autonomy

---

**`STK-AUT-001` — Autonomous power**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `DEMONSTRATION`                                          |
| **Standard(s)**        | —                                                        |
| **Dependencies**       | —                                                        |
| **Phase**              | 2025–2026                                                |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `NOT_APPLICABLE` |

**Description:**  
The system SHALL integrate autonomous power modules (solar panel + battery + charge manager) for continuous operation.

**Acceptance Criteria:**

1. [ ] Sensor operates on solar + battery without external source.
2. [ ] Battery manager with charge indicator included.
3. [ ] Solar-panel design is discreet.

**Notes:**  
Total system consumption ~15 W. Solar + battery sizing must account for worst-case irradiance in Colombia.

---

### 3.9 Sensor Health Monitoring

---

**`STK-MON-001` — Sensor health monitoring**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `DEMONSTRATION`                                          |
| **Standard(s)**        | —                                                        |
| **Dependencies**       | —                                                        |
| **Phase**              | 2025–2026                                                |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `NOT_APPLICABLE` |

**Description:**  
The system SHALL monitor and record sensor health: disk usage, RAM, CPU, and temperature.

**Acceptance Criteria:**

1. [ ] Disk, RAM, CPU, and temperature are monitored.
2. [ ] Local alerts generated when thresholds are exceeded.
3. [ ] Health data stored locally with timestamp.

**Notes:**  
RPi throttles above 80 °C. Alert thresholds should warn before throttle onset.

---

**`STK-MON-002` — Network and connectivity monitoring**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `TEST`                                                   |
| **Standard(s)**        | —                                                        |
| **Dependencies**       | —                                                        |
| **Phase**              | 2025–2026                                                |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `NOT_APPLICABLE` |

**Description:**  
The system SHALL measure and record IP-connection quality: RTT, channel status, available bandwidth, and packet loss.

**Acceptance Criteria:**

1. [ ] RTT measured periodically (configurable interval).
2. [ ] Alive/Not Alive status detected per interface.
3. [ ] Local record generated when RTT or packet loss exceeds thresholds.

---

**`STK-PRG-001` — Scheduled spectrum scan**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `DEMONSTRATION`                                          |
| **Standard(s)**        | ITU-R SM.1537; `REF-001`                                 |
| **Dependencies**       | `STK-PAR-001`                                           |
| **Phase**              | 2025–2026                                                |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `NOT_APPLICABLE` |

**Description:**  
The system SHALL allow parameterized spectrum scans to be scheduled, run locally, and stored.

**Acceptance Criteria:**

1. [ ] Scans scheduled with defined parameters (frequency, RBW, VBW, duration, repetition).
2. [ ] Results stored locally.
3. [ ] Scans execute within ≤ 1 minute of scheduled time.

---

### 3.10 Accuracy and Calibration

#### 3.10.1 Synchronization and Calibration

---

**`STK-SIN-001` — NTP synchronization**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `NON_FUNCTIONAL`                                         |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `TEST`                                                   |
| **Standard(s)**        | —                                                        |
| **Dependencies**       | `STK-RED-004`                                           |
| **Phase**              | 2025–2026                                                |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `NOT_APPLICABLE` |

**Description:**  
The system SHALL synchronize to an NTP server with a time offset ≤ 100 ms.

**Acceptance Criteria:**

1. [ ] Synchronizes with NTP when network is available.
2. [ ] Time offset ≤ 100 ms.
3. [ ] Synchronization status queryable locally.

---

**`STK-CAL-001` — Calibration procedures**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `NON_FUNCTIONAL`                                         |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `ANALYSIS`                                               |
| **Standard(s)**        | —                                                        |
| **Dependencies**       | —                                                        |
| **Phase**              | 2025–2026                                                |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `NOT_APPLICABLE` |

**Description:**  
The system SHALL include calibration procedures for frequency, receive gain, IQ balance, and DC-offset correction.

**Acceptance Criteria:**

1. [ ] Documented frequency-calibration procedure.
2. [ ] Documented gain-calibration procedure.
3. [ ] Documented IQ-balance and DC-offset correction procedure.
4. [ ] Each calibration produces a dated record with results.

**Notes:**  
Calibration uses external reference sources (signal generator) to build correction tables that compensate for gain uncertainty.

---

#### 3.10.2 System Characterization

---

**`STK-CAR-001` — DANL**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `NON_FUNCTIONAL`                                         |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `TEST`                                                   |
| **Standard(s)**        | ITU-R SM.1138; `REF-002`                                 |
| **Dependencies**       | —                                                        |
| **Phase**              | 2025–2026                                                |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `NOT_APPLICABLE` |

**Description:**  
The system SHALL achieve a DANL ≤ –100 dBm across the operating range.

**Acceptance Criteria:**

1. [ ] Measured DANL ≤ –100 dBm over ≥ 90% of the frequency range.
2. [ ] Measurement performed with 50 Ω load and documented per band.

**Notes:**  
Software averaging improves effective DANL at the cost of temporal resolution.

---

**`STK-CAR-002` — Dynamic range**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `NON_FUNCTIONAL`                                         |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `TEST`                                                   |
| **Standard(s)**        | ITU-R SM.1138; `REF-002`                                 |
| **Dependencies**       | `STK-CAR-001`                                           |
| **Phase**              | 2025–2026                                                |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `NOT_APPLICABLE` |

**Description:**  
The system SHALL achieve a dynamic range ≥ 80 dB.

**Acceptance Criteria:**

1. [ ] Measured dynamic range ≥ 80 dB in a two-tone test.
2. [ ] Test setup and results documented.

**Notes:**  
The 8-bit ADC provides ~48 dB single-capture SFDR. The ≥ 80 dB target is achieved via gain-stepped captures at multiple LNA/VGA settings + spectral averaging.

---

**`STK-CAR-003` — Frequency accuracy**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `NON_FUNCTIONAL`                                         |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `TEST`                                                   |
| **Standard(s)**        | —                                                        |
| **Dependencies**       | —                                                        |
| **Phase**              | 2025–2026                                                |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `NOT_APPLICABLE` |

**Description:**  
The system SHALL achieve a frequency accuracy of ± 2 ppm.

**Acceptance Criteria:**

1. [ ] Measured frequency error ≤ ± 2 ppm against a calibrated reference.
2. [ ] Measurement at room temperature (20–25 °C).

**Notes:**  
The stock oscillator is ± 20 ppm. A TCXO replacement (± 0.5–2 ppm) or GPS-disciplined correction is used.

---

**`STK-CAR-004` — Oscillator aging**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `NON_FUNCTIONAL`                                         |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `ANALYSIS`                                               |
| **Standard(s)**        | —                                                        |
| **Dependencies**       | `STK-CAR-003`                                           |
| **Phase**              | 2025–2026                                                |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `NOT_APPLICABLE` |

**Description:**  
The system SHALL meet a frequency drift due to oscillator aging ≤ 1 ppm/year.

**Acceptance Criteria:**

1. [ ] Selected oscillator has aging spec ≤ 1 ppm/year.
2. [ ] Oscillator type and aging spec documented.

---

**`STK-CAR-005` — Amplitude accuracy**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `NON_FUNCTIONAL`                                         |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `TEST`                                                   |
| **Standard(s)**        | —                                                        |
| **Dependencies**       | —                                                        |
| **Phase**              | 2025–2026                                                |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `NOT_APPLICABLE` |

**Description:**  
The system SHALL achieve a typical amplitude accuracy of ± 1 dB.

**Acceptance Criteria:**

1. [ ] Amplitude error ≤ ± 1 dB over ≥ 90% of the frequency range.
2. [ ] Amplitude linearity verified in 10 dB steps.

**Notes:**  
Requires per-frequency, per-gain-setting calibration tables built using external reference sources.
---

### 3.11 Normative Basis

**`NRM-ITU-001` — Monitoring-station automation requirements**

| Field | Value |
|-------|-------|
| **Priority** | `MUST` |
| **Status** | `APPROVED` |
| **Standard(s)** | ITU-R SM.1537 |
| **Clause** | §5 |
| **Compliance** | `COMPLIANT` |

**Description:**

The system SHALL implement the monitoring-station automation requirements of ITU-R SM.1537 (REF-001).

**Acceptance Criteria:**

1. [ ] Station automation and reporting match the ITU-R SM.1537 station requirements.

**`NRM-ITU-002` — Monitoring sensitivity and selectivity**

| Field | Value |
|-------|-------|
| **Priority** | `MUST` |
| **Status** | `APPROVED` |
| **Standard(s)** | ITU-R SM.1138 |
| **Clause** | §4 |
| **Compliance** | `COMPLIANT` |

**Description:**

The system SHALL meet the sensitivity and selectivity requirements of ITU-R SM.1138 (REF-002) for monitored bands.

**Acceptance Criteria:**

1. [ ] Achieved DANL and selectivity meet ITU-R SM.1138 for each monitored band.

**`NRM-GUM-001` — Measurement uncertainty evaluation**

| Field | Value |
|-------|-------|
| **Priority** | `MUST` |
| **Status** | `APPROVED` |
| **Standard(s)** | JCGM 100:2008 (GUM) |
| **Clause** | §4 |
| **Compliance** | `COMPLIANT` |

**Description:**

The system SHALL evaluate measurement uncertainty of reported quantities in accordance with JCGM 100:2008 (REF-GUM).

**Acceptance Criteria:**

1. [ ] Every reported measurand carries a GUM-consistent uncertainty budget.

**`NRM-ICNIRP-001` — Human-exposure context for field measurements**

| Field | Value |
|-------|-------|
| **Priority** | `SHOULD` |
| **Status** | `APPROVED` |
| **Standard(s)** | ICNIRP 2010 |
| **Clause** | §4 |
| **Compliance** | `PENDING` |

**Description:**

The system SHOULD report field-strength results with reference to ICNIRP 2010 exposure guidelines (REF-ICNIRP) where applicable.

**Acceptance Criteria:**

1. [ ] Field-strength reports optionally annotate ICNIRP 2010 reference levels.

---

### 3.12 SDR Receiver (HackRF One)

---

**`HWC-SDR-001` — Frequency range**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Component**          | `HW-SDR`                                                  |
| **Parameter**          | Operating frequency range                                 |
| **Limit type**         | `RANGE`                                                   |
| **Value min**          | 1 MHz                                                     |
| **Value max**          | 6 GHz                                                     |
| **Source**             | `DATASHEET`                                               |
| **Source ref**         | `REF-DS-001` — Specifications                             |
| **Impact**             | `HARD`                                                    |
| **Status**             | `CONFIRMED`                                               |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `NOT_APPLICABLE` |

**Notes:**  
Sensitivity degrades significantly below 10 MHz and above 4 GHz.

---

**`HWC-SDR-002` — Maximum instantaneous bandwidth**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Component**          | `HW-SDR`                                                  |
| **Parameter**          | Maximum instantaneous (real-time) bandwidth               |
| **Limit type**         | `MAX`                                                     |
| **Value**              | 20 MHz                                                    |
| **Source**             | `DATASHEET`                                               |
| **Source ref**         | `REF-DS-001` — Specifications                             |
| **Impact**             | `HARD`                                                    |
| **Status**             | `CONFIRMED`                                               |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `NOT_APPLICABLE` |

**Notes:**  
Wider spans require frequency hopping (sweep mode), which introduces temporal gaps.

---

**`HWC-SDR-003` — ADC resolution**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Component**          | `HW-SDR`                                                  |
| **Parameter**          | ADC resolution / IQ sample format                         |
| **Limit type**         | `FIXED`                                                   |
| **Value**              | 8 bit I + 8 bit Q (CS8)                                  |
| **Source**             | `DATASHEET`                                               |
| **Source ref**         | `REF-DS-001`; `REF-DRV-001`                               |
| **Impact**             | `HARD`                                                    |
| **Status**             | `CONFIRMED`                                               |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `NOT_APPLICABLE` |

**Notes:**  
8-bit resolution yields a theoretical SFDR of ~48 dB (6.02 × 8). Achieving higher dynamic range requires software techniques: averaging, dithering, or gain-stepped captures.

---

**`HWC-SDR-004` — DANL**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Component**          | `HW-SDR`                                                  |
| **Parameter**          | Displayed Average Noise Level                             |
| **Limit type**         | `MIN`                                                     |
| **Value**              | −100 dBm/Hz (approximate, frequency-dependent)            |
| **Source**             | `MEASURED`                                                |
| **Source ref**         | `REF-MEAS-001` — To be performed                          |
| **Impact**             | `SOFT`                                                    |
| **Status**             | `PRELIMINARY`                                             |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `NOT_APPLICABLE` |

**Notes:**  
DANL varies by frequency band and gain setting. Formal characterization per band is required. Software averaging can improve effective DANL at the cost of temporal resolution.

---

**`HWC-SDR-005` — Frequency accuracy (oscillator)**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Component**          | `HW-SDR`                                                  |
| **Parameter**          | Local oscillator frequency accuracy                       |
| **Limit type**         | `MAX`                                                     |
| **Value**              | ± 20 ppm (uncompensated, typical)                         |
| **Source**             | `DATASHEET`                                               |
| **Source ref**         | `REF-DS-001` — Crystal oscillator specifications          |
| **Impact**             | `SOFT`                                                    |
| **Status**             | `CONFIRMED`                                               |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `NOT_APPLICABLE` |

**Notes:**  
Stock crystal is ± 20 ppm. Can be replaced with a TCXO (± 0.5–2 ppm) or compensated via GPS-disciplined correction.

---

**`HWC-SDR-006` — Gain control (no AGC)**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Component**          | `HW-SDR`                                                  |
| **Parameter**          | Gain control mechanism                                    |
| **Limit type**         | `ENUM`                                                    |
| **Value**              | Manual LNA gain (0–40 dB), VGA gain (0–62 dB), no AGC    |
| **Source**             | `DRIVER_API`                                              |
| **Source ref**         | `REF-DRV-001` — hackrf_set_lna_gain(), hackrf_set_vga_gain() |
| **Impact**             | `SOFT`                                                    |
| **Status**             | `CONFIRMED`                                               |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `NOT_APPLICABLE` |

**Notes:**  
Gain must be set manually or via software-controlled stepping. Amplitude accuracy requires calibration tables mapping gain settings to correction factors across frequency.

---

**`HWC-SDR-007` — No pre-selection filters**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Component**          | `HW-SDR`                                                  |
| **Parameter**          | RF front-end filtering                                    |
| **Limit type**         | `FIXED`                                                   |
| **Value**              | No band-pass pre-selection filters                        |
| **Source**             | `DATASHEET`                                               |
| **Source ref**         | `REF-DS-001` — Block diagram                              |
| **Impact**             | `SOFT`                                                    |
| **Status**             | `CONFIRMED`                                               |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `NOT_APPLICABLE` |

**Notes:**  
Susceptible to out-of-band interference, image frequencies, and intermodulation products. Detection algorithms must account for artifacts generated by the receiver itself.

---

### 3.13 Embedded Platform (Raspberry Pi 4B)

---

**`HWC-CPU-001` — Processing capacity**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Component**          | `HW-CPU`                                                  |
| **Parameter**          | CPU cores and clock speed                                 |
| **Limit type**         | `FIXED`                                                   |
| **Value**              | 4× ARM Cortex-A72 @ 1.8 GHz                              |
| **Source**             | `DATASHEET`                                               |
| **Source ref**         | `REF-DS-002`; `REF-DS-003`                                |
| **Impact**             | `HARD`                                                    |
| **Status**             | `CONFIRMED`                                               |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `NOT_APPLICABLE` |

**Notes:**  
At 20 MHz BW / 20 MS/s, a 2048-point FFT produces ~9,765 FFTs/second. Profiling under load is required to verify processing budget.

---

**`HWC-CPU-002` — RAM capacity**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Component**          | `HW-CPU`                                                  |
| **Parameter**          | System RAM                                                |
| **Limit type**         | `FIXED`                                                   |
| **Value**              | 4 GB or 8 GB (model-dependent)                            |
| **Source**             | `DATASHEET`                                               |
| **Source ref**         | `REF-DS-002`                                              |
| **Impact**             | `HARD`                                                    |
| **Status**             | `CONFIRMED`                                               |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `NOT_APPLICABLE` |

**Notes:**  
Must accommodate OS, DSP pipeline buffers, IQ sample buffers, trace storage, and network stack simultaneously.

---

**`HWC-CPU-003` — Operating temperature**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Component**          | `HW-CPU`                                                  |
| **Parameter**          | Operating temperature                                     |
| **Limit type**         | `RANGE`                                                   |
| **Value min**          | 0 °C                                                      |
| **Value max**          | 50 °C (throttles above 80 °C)                             |
| **Source**             | `DATASHEET`                                               |
| **Source ref**         | `REF-DS-002` — Thermal specifications                     |
| **Impact**             | `SOFT`                                                    |
| **Status**             | `CONFIRMED`                                               |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `NOT_APPLICABLE` |

**Notes:**  
Colombian field deployments may exceed 50 °C ambient inside an enclosed housing. Thermal management (heatsink, ventilation, or duty-cycling) is required.

---

### 3.14 Data Bus (USB 2.0: SDR ↔ RPi)

---

**`HWC-BUS-001` — USB 2.0 sustained throughput**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Component**          | `HW-SDR`, `HW-CPU`                                       |
| **Parameter**          | Sustained data throughput (SDR → RPi)                     |
| **Limit type**         | `MAX`                                                     |
| **Value**              | ~32 MB/s sustained (measured)                             |
| **Source**             | `MEASURED`                                                |
| **Source ref**         | `REF-MEAS-002` — To be performed                          |
| **Impact**             | `HARD`                                                    |
| **Status**             | `PRELIMINARY`                                             |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `NOT_APPLICABLE` |

**Notes:**  
USB 2.0 theoretical: 480 Mbps = 60 MB/s. Practical sustained: ~32 MB/s. HackRF at 20 MS/s × 2 bytes = 40 MB/s exceeds this. Sample drops at sustained 20 MS/s are possible.

---

### 3.15 GPS Module

---

**`HWC-GPS-001` — Horizontal accuracy**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Component**          | `HW-GPS`                                                  |
| **Parameter**          | Horizontal position accuracy (CEP 50%)                    |
| **Limit type**         | `MAX`                                                     |
| **Value**              | ≤ 3 m (open sky, target)                                  |
| **Source**             | `DATASHEET`                                               |
| **Source ref**         | _TBD — depends on selected GPS module_                    |
| **Impact**             | `HARD`                                                    |
| **Status**             | `PRELIMINARY`                                             |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `NOT_APPLICABLE` |

---

**`HWC-GPS-002` — GPS output protocol**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Component**          | `HW-GPS`                                                  |
| **Parameter**          | Data output protocol                                      |
| **Limit type**         | `FIXED`                                                   |
| **Value**              | NMEA 0183 over UART (9600 baud default)                   |
| **Source**             | `DATASHEET`                                               |
| **Source ref**         | _TBD — depends on selected GPS module_                    |
| **Impact**             | `INFORMATIONAL`                                           |
| **Status**             | `PRELIMINARY`                                             |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `NOT_APPLICABLE` |

**Notes:**  
Standard NMEA sentences (GGA, RMC, GSA). Parsing library required for timestamp and position extraction.

---

### 3.16 Power System

---

**`HWC-PWR-001` — System power consumption**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Component**          | `HW-PWR`                                                  |
| **Parameter**          | Total system power consumption (all components active)    |
| **Limit type**         | `MAX`                                                     |
| **Value**              | ~15 W (estimated: RPi 6W + HackRF 2.5W + peripherals)    |
| **Source**             | `DERIVED`                                                 |
| **Source ref**         | `REF-DS-001` + `REF-DS-002` — Power specifications        |
| **Impact**             | `HARD`                                                    |
| **Status**             | `PRELIMINARY`                                             |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `NOT_APPLICABLE` |

**Notes:**  
Solar panel and battery sizing must exceed 15 W for 24/7 autonomous operation. Actual measurement under full DSP load is required.

---

### 3.17 Storage

---

**`HWC-STR-001` — Storage write speed**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Component**          | `HW-STR`                                                  |
| **Parameter**          | Sustained sequential write speed                          |
| **Limit type**         | `MIN`                                                     |
| **Value**              | ≥ 40 MB/s (required to store raw CS8 at 20 MS/s)         |
| **Source**             | `DERIVED`                                                 |
| **Source ref**         | IQ rate: 20 MS/s × 2 bytes = 40 MB/s                     |
| **Impact**             | `HARD`                                                    |
| **Status**             | `PRELIMINARY`                                             |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `NOT_APPLICABLE` |

**Notes:**  
USB 3.0 SSD easily meets this; microSD may not. Burst recording (limited duration) is an alternative.

---

### 3.18 Derived Constraints

---

**`HWC-DRV-001` — IQ throughput budget (end-to-end)**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Component**          | `HW-SDR`, `HW-CPU`, `HW-STR`                             |
| **Parameter**          | End-to-end IQ data flow budget                            |
| **Limit type**         | `FIXED`                                                   |
| **Value**              | 20 MS/s × 2 B = 40 MB/s (SDR → USB → RAM → DSP → Storage) |
| **Source**             | `DERIVED`                                                 |
| **Source ref**         | `HWC-SDR-002` + `HWC-BUS-001` + `HWC-STR-001`           |
| **Impact**             | `HARD`                                                    |
| **Status**             | `PRELIMINARY`                                             |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `NOT_APPLICABLE` |

**Notes:**  
The USB 2.0 bottleneck (~32 MB/s) is the weakest link in the 40 MB/s chain. Mitigations: (1) accept occasional drops in non-forensic mode, (2) reduce sample rate for continuous recording, (3) use burst capture for forensic storage.

---

**`HWC-DRV-002` — Dynamic range via software enhancement**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Component**          | `HW-SDR`                                                  |
| **Parameter**          | Achievable dynamic range with software techniques         |
| **Limit type**         | `RANGE`                                                   |
| **Value min**          | ~48 dB (single capture, limited by 8-bit ADC)             |
| **Value max**          | ~90 dB (with gain stepping + averaging, estimated)        |
| **Source**             | `DERIVED`                                                 |
| **Source ref**         | `HWC-SDR-003` + `HWC-SDR-006`                            |
| **Impact**             | `SOFT`                                                    |
| **Status**             | `PRELIMINARY`                                             |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `NOT_APPLICABLE` |

**Notes:**  
The ≥ 80 dB target is achievable with: (1) gain-stepped captures at multiple LNA/VGA settings, (2) spectral averaging over N sweeps, (3) software dithering. Must be validated experimentally.


---

## 4. External Interface Requirements

### 4.1 Hardware Interfaces

- SDR: HackRF One (USB 2.0)
- Embedded platform: Raspberry Pi 4B
- GPS: Module TBD (UART/USB, ≤ 3 m accuracy)
- Antennas: SMA connectors
- 4G/5G module: USB with SIM slot
- WiFi: RPi integrated
- Ethernet: RJ45 externally accessible
- GPIO: antenna mux switching
- Power: solar panel + battery + charge manager
- Storage: USB 3.0 SSD or high-capacity microSD

### 4.2 Software Interfaces

- SDR driver: libhackrf / SoapySDR
- DSP pipeline: FFT, PSD, RBW/VBW filtering
- Scheduler: cron or equivalent
- Network manager: automatic failover
- NTP client

### 4.3 Communication Interfaces

- HackRF ↔ RPi: USB 2.0 (IQ stream)
- GPS ↔ RPi: UART/USB, NMEA 0183
- 4G/5G ↔ RPi: USB (AT commands + data)
- GPIO: antenna mux, status LEDs, battery sensors

---

## 5. Non-Functional Requirements

### 5.1 Performance

- DSP pipeline latency ≤ 1 second at 20 MHz bandwidth.
- Minimum frequency resolution: 10 Hz.
- Scheduled scans: tolerance ≤ 1 minute.

### 5.2 Reliability

- Network auto-routing for connectivity availability.
- Local storage for connectivity-loss scenarios.
- NTP sync offset ≤ 100 ms.

### 5.3 Maintainability

- OTA software updates with rollback.
- Remote SSH access for diagnostics.
- Documented calibration procedures.

### 5.4 Accuracy

- DANL ≤ –100 dBm.
- Dynamic range ≥ 80 dB.
- Frequency accuracy ± 2 ppm.
- Amplitude accuracy ± 1 dB.

---

## 6. Traceability

| Requirement ID   | Subsystem              | Standard Ref        | Test Case   |
|------------------|------------------------|---------------------|-------------|
| `STK-EMC-001`   | RF architecture        | —                   | _TC-001_    |
| `STK-RNG-001`   | Spectral range         | ITU-R SM.1537       | _TC-002_    |
| `STK-RNG-002`   | Bandwidth              | —                   | _TC-003_    |
| `STK-PAR-001`   | DSP parameterization   | —                   | _TC-004_    |
| `STK-PAR-002`   | DSP parameterization   | —                   | _TC-005_    |
| `STK-PAR-003`   | DSP parameterization   | —                   | _TC-006_    |
| `STK-PAR-004`   | DSP parameterization   | —                   | _TC-007_    |
| `STK-PAR-005`   | GPS                    | —                   | _TC-008_    |
| `STK-PAR-006`   | Units                  | —                   | _TC-009_    |
| `STK-PAR-007`   | Detection              | —                   | _TC-010_    |
| `STK-MED-001`   | DSP / traces           | ITU-R SM.1537       | _TC-011_    |
| `STK-MED-003`   | DSP / OBW              | ITU-R SM.1537       | _TC-012_    |
| `STK-MED-004`   | DSP / channel power    | —                   | _TC-013_    |
| `STK-MED-005`   | DSP / RDS              | —                   | _TC-014_    |
| `STK-MED-006`   | DSP / demodulation     | —                   | _TC-015_    |
| `STK-MED-007`   | DSP / modulation       | —                   | _TC-016_    |
| `STK-VER-001`   | Local detection        | —                   | _TC-017_    |
| `STK-VER-002`   | Local detection        | —                   | _TC-018_    |
| `STK-SRV-002`   | Forensic audio         | —                   | _TC-019_    |
| `STK-ALM-001`   | Local storage          | ITU-R SM.1537       | _TC-020_    |
| `STK-ALM-003`   | Local storage          | —                   | _TC-021_    |
| `STK-RED-001`   | Connectivity           | —                   | _TC-022_    |
| `STK-RED-002`   | Connectivity           | —                   | _TC-023_    |
| `STK-RED-003`   | Connectivity           | —                   | _TC-024_    |
| `STK-RED-004`   | Connectivity           | —                   | _TC-025_    |
| `STK-SOP-001`   | Maintenance            | —                   | _TC-026_    |
| `STK-GPS-001`   | GPS                    | —                   | _TC-027_    |
| `STK-GPS-002`   | GPS                    | —                   | _TC-028_    |
| `STK-ANT-001`   | Antennas               | —                   | _TC-029_    |
| `STK-ANT-002`   | Antennas               | ITU-T K.113, K.100  | _TC-030_    |
| `STK-RNI-001`   | Non-ionizing radiation | ITU-T K.113, K.100  | _TC-031_    |
| `STK-RNI-002`   | Non-ionizing radiation | ITU-T K.113, K.100  | _TC-032_    |
| `STK-AUT-001`   | Power                  | —                   | _TC-033_    |
| `STK-MON-001`   | Health monitoring      | —                   | _TC-034_    |
| `STK-MON-002`   | Health monitoring      | —                   | _TC-035_    |
| `STK-PRG-001`   | Local scheduler        | ITU-R SM.1537       | _TC-036_    |
| `STK-SIN-001`   | Synchronization        | —                   | _TC-037_    |
| `STK-CAL-001`   | Calibration            | —                   | _TC-038_    |
| `STK-CAR-001`   | Characterization       | ITU-R SM.1138       | _TC-039_    |
| `STK-CAR-002`   | Characterization       | ITU-R SM.1138       | _TC-040_    |
| `STK-CAR-003`   | Characterization       | —                   | _TC-041_    |
| `STK-CAR-004`   | Characterization       | —                   | _TC-042_    |
| `STK-CAR-005`   | Characterization       | —                   | _TC-043_    |
| `NRM-ITU-001` | Normative basis | ITU-R SM.1537 | _TC-N01_ |
| `NRM-ITU-002` | Normative basis | ITU-R SM.1138 | _TC-N02_ |
| `NRM-GUM-001` | Normative basis | JCGM 100:2008 | _TC-N03_ |
| `NRM-ICNIRP-001` | Normative basis | ICNIRP 2010 | _TC-N04_ |
| `HWC-SDR-001` | Platform constraints | — | _TC-H01_ |
| `HWC-SDR-002` | Platform constraints | — | _TC-H02_ |
| `HWC-SDR-003` | Platform constraints | — | _TC-H03_ |
| `HWC-SDR-004` | Platform constraints | — | _TC-H04_ |
| `HWC-SDR-005` | Platform constraints | — | _TC-H05_ |
| `HWC-SDR-006` | Platform constraints | — | _TC-H06_ |
| `HWC-SDR-007` | Platform constraints | — | _TC-H07_ |
| `HWC-CPU-001` | Platform constraints | — | _TC-H08_ |
| `HWC-CPU-002` | Platform constraints | — | _TC-H09_ |
| `HWC-CPU-003` | Platform constraints | — | _TC-H10_ |
| `HWC-BUS-001` | Platform constraints | — | _TC-H11_ |
| `HWC-GPS-001` | Platform constraints | — | _TC-H12_ |
| `HWC-GPS-002` | Platform constraints | — | _TC-H13_ |
| `HWC-PWR-001` | Platform constraints | — | _TC-H14_ |
| `HWC-STR-001` | Platform constraints | — | _TC-H15_ |
| `HWC-DRV-001` | Platform constraints | — | _TC-H16_ |
| `HWC-DRV-002` | Platform constraints | — | _TC-H17_ |

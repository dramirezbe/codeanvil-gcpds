# PROJECT: Edge Sensor — ANE Spectrum Monitoring System

## System Requirements Specification (SRS)

> **Template based on:** IEEE/ISO/IEC 29148:2018 — *Systems and software engineering — Life cycle processes — Requirements engineering*, adapted with elements of ETSI EN 303 645 (Cyber Security for IoT) and a deterministic structure for automated AI-based validation.
>
> **Methodology:** COTS-Reconciled Requirements Engineering. This SRS assumes that hardware has been selected and its constraints formally documented in the companion Hardware Constraints Specification (HCS-ANE-EDGE-001). Requirements in this document have been reconciled against the HCS — every requirement is feasible within the COTS envelope, and conflicts have been resolved prior to approval.
>
> **Template version:** 2.0.0  
> **Creation date:** 2026-10-13  
> **Last modified:** 2026-10-13  
> **Document status:** `IN_REVIEW`

---

## Document Metadata

| Field                  | Value                                                      |
|------------------------|------------------------------------------------------------|
| **Document ID**        | `SRS-ANE-EDGE-001`                                        |
| **Project**            | Edge Sensor — Spectrum Monitoring Subsystem (Phase 2)      |
| **Organization**       | National Spectrum Agency (ANE) — Colombia                  |
| **Version**            | 0.2.0                                                     |
| **Classification**     | `INTERNAL`                                                |
| **Author(s)**          | _To be defined_                                           |
| **Reviewer(s)**        | _To be defined_                                           |
| **Approver(s)**        | _To be defined_                                           |

### Companion Documents

| Document ID            | Title                                                   | Relationship              |
|------------------------|---------------------------------------------------------|---------------------------|
| `HCS-ANE-EDGE-001`    | Edge Sensor HW Constraints Specification                | COTS envelope for this SRS |
| `SRS-ANE-001`         | Full-System SRS (Phase 2)                               | Parent system requirements |

### Change Log

| Version | Date       | Author                 | Change Description                                      |
|---------|------------|------------------------|---------------------------------------------------------|
| 0.1.0   | 2026-10-13 | AI-assisted generation | Extraction of edge requirements from SRS-ANE-001        |
| 0.2.0   | 2026-10-13 | AI-assisted generation | COTS reconciliation: added hw_constraints and reconciliation fields; companion HCS-ANE-EDGE-001 created |

---

## 1. Introduction

### 1.1 Purpose

This document specifies the requirements for the **edge sensor** as a self-contained subsystem of the ANE Spectrum Monitoring System. It covers exclusively what runs on the embedded node (HackRF One + Raspberry Pi): the SDR driver, the DSP pipeline (PSD, FFT bins, traces), demodulation, network connectivity (4G/5G, WiFi, Ethernet), GPIO multiplexing, GPS, local storage, autonomous power, and calibration.

**It excludes:** the cloud backend, the web frontend, integration APIs, the ANE's centralized database, report generation, and any logic that requires an active connection to the server.

### 1.2 System Scope

The edge sensor is an autonomous spectrum-monitoring node based on an SDR (HackRF One) running on a Raspberry Pi. It captures, processes, and locally stores spectral data in the 1 MHz – 6 GHz range. It operates independently on solar/battery power with 4G/5G/WiFi/Ethernet connectivity.

**The edge sensor does NOT include:** a web graphical interface, a centralized dashboard, comparison against the authorized-emissions database, formal report generation, or a REST API for external consumption.

### 1.3 COTS-Reconciled Methodology

This SRS follows a COTS-Reconciled methodology:

1. Requirements originate from two streams: **ANE client needs** and **normative standards** (ITU-R, ITU-T, IEEE, ETSI).
2. Hardware was selected (COTS: HackRF One + Raspberry Pi 4B + peripherals) and its parametric constraints formally documented in **HCS-ANE-EDGE-001**.
3. Each requirement was reconciled against the HCS before approval — conflicts were resolved, mitigations documented, and no infeasible requirements remain.
4. The reconciliation status is recorded per requirement via the `hw_constraints` and `reconciliation` fields.

```
[ ANE (Client) ]       [ Norms (ITU-R, ITU-T, ETSI) ]
        │                        │
        └──────────┬─────────────┘
                   │  (Domain Requirements)
                   ▼
      ┌──────────────────────┐
      │    Reconciliation    │ ◄─── [ HCS-ANE-EDGE-001 ]
      │    (conflict check)  │      (HackRF, RPi, GPS, Power, Storage)
      └──────────┬───────────┘
                 │
                 ▼
    [ SRS-ANE-EDGE-001 — Reconciled ]
```

### 1.4 Definitions, Acronyms, and Abbreviations

| Term       | Definition                                                                           |
|------------|--------------------------------------------------------------------------------------|
| ANE        | National Spectrum Agency (Agencia Nacional del Espectro, Colombia)                   |
| SDR        | Software Defined Radio                                                               |
| RBW        | Resolution Bandwidth                                                                 |
| VBW        | Video Bandwidth                                                                      |
| DANL       | Displayed Average Noise Level                                                        |
| RDS        | Radio Data System (FM radio data)                                                   |
| NTP        | Network Time Protocol                                                                |
| EMC        | Electromagnetic Compatibility                                                        |
| OBW        | Occupied Bandwidth                                                                   |
| PSD        | Power Spectral Density                                                               |
| FFT        | Fast Fourier Transform                                                               |
| GPIO       | General Purpose Input/Output                                                         |
| ppm        | Parts per million                                                                    |
| SAW        | Surface Acoustic Wave (filter type)                                                 |
| OTA        | Over The Air — remote software update                                               |
| CS8        | Complex Signed 8-bit — the HackRF IQ sample format                                  |
| AF         | Antenna Factor                                                                       |
| HCS        | Hardware Constraints Specification — companion document                              |
| COTS       | Commercial Off-The-Shelf                                                             |

### 1.5 References

| Ref ID     | Document                                                               | Version / Date      |
|------------|------------------------------------------------------------------------|---------------------|
| `REF-001`  | ITU-R SM.1537 — Automation and requirements of monitoring stations     | In force            |
| `REF-002`  | ITU-R SM.1138 — Monitoring sensitivity and selectivity                 | In force            |
| `REF-003`  | ITU-T K.113 — Electric field measurement in urban environments         | In force            |
| `REF-004`  | ITU-T K.100 — Assessment of human exposure to electromagnetic fields   | In force            |
| `REF-007`  | IEEE/ISO/IEC 29148:2018 — Requirements engineering                     | 2018                |
| `REF-HCS`  | HCS-ANE-EDGE-001 — Companion HW Constraints Specification             | 0.1.0 / 2026-10-13  |
| `REF-FULL` | SRS-ANE-001 — Full-System SRS, Phase 2                                 | 0.1.0 / 2026-10-13  |

### 1.6 Document Overview

Section 3 contains the specific requirements of the edge sensor, organized by subsystem. Each requirement includes `hw_constraints` (referencing HCS-ANE-EDGE-001) and a `reconciliation` status. Section 4 covers external interfaces (summaries; details in HCS). Section 5 covers non-functional requirements. Section 6 presents traceability including HCS cross-references. Section 7 defines G0 structural validation (future work).

---

## 2. Overall System Description

### 2.1 Product Perspective

This document describes the edge sensor as a subsystem of the full system (see `REF-FULL`). The sensor operates as an autonomous node for spectral acquisition and preprocessing. The COTS hardware envelope is formally documented in `REF-HCS`.

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

The edge sensor provides: real-time spectrum capture (1 MHz–6 GHz), DSP processing (FFT, PSD, traces, RBW/VBW), FM/AM demodulation, signal-parameter measurement (OBW, channel power, modulation), local detection of intermodulation products and interference, local forensic storage (JSON + CS8), autonomous connectivity management (4G/WiFi/ETH failover), NTP synchronization, and node health monitoring.

### 2.3 User Characteristics

| User Type         | Description                                      | Technical Level |
|-------------------|--------------------------------------------------|-----------------|
| Spectrum engineer | Configures the sensor parameters via remote access | `EXPERT`        |
| Field technician  | Installs, calibrates, and maintains the sensor   | `TECHNICAL`     |

### 2.4 Constraints

Detailed parametric constraints are in **HCS-ANE-EDGE-001**. Summary:

- **RF front-end:** HackRF One — 1 MHz to 6 GHz, 20 MHz instantaneous BW, 8-bit IQ (CS8), no AGC, no pre-selection filters, stock oscillator ± 20 ppm.
- **Processing:** Raspberry Pi 4B — 4× Cortex-A72 @ 1.8 GHz, 4/8 GB RAM.
- **Data bus:** USB 2.0 bottleneck (~32 MB/s sustained vs. 40 MB/s IQ rate).
- **Power:** Solar + battery, ~15 W total system consumption.
- **Connectivity:** Dependent on 4G/5G coverage from Colombian carriers.

### 2.5 Assumptions and Dependencies

- The ANE provides data SIM cards for mobile connectivity.
- Sensors are deployed at sites with mains power or where a solar solution is viable.
- Antennas are correctly connected and calibrated for the operating band.
- The COTS hardware documented in HCS-ANE-EDGE-001 is the selected platform.

---

## 3. Specific Requirements

---

### 3.1 Sensor RF Architecture

#### 3.1.1 Electromagnetic Compatibility

---

**`ANAL-EMC-001` — Sensor EMC optimization**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `NON_FUNCTIONAL`                                          |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `TEST`                                                   |
| **New hardware**       | Yes (RF gasket)                                          |
| **Standard(s)**        | —                                                        |
| **Dependencies**       | —                                                        |
| **HW constraints**     | `HWC-SDR-007`                                             |
| **Reconciliation**     | `MITIGATED`                                               |
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL incorporate adjustments and filtering in the sensor's receive path to prevent spurious signals generated by its own electronics from appearing in the measurement results.

**Acceptance Criteria:**

1. [ ] The sensor's internal spurious emissions are at least 10 dB below the operating noise floor.
2. [ ] RF shielding (a gasket) is implemented between internal modules.
3. [ ] A before/after comparative measurement demonstrates a reduction in EMC artifacts.

**Notes:**  
Mitigation for HWC-SDR-007 (no pre-selection filters): the HackRF's broadband front-end picks up internal EMI. An RF gasket + board-level shielding provides physical mitigation. Software-side, the DSP pipeline should characterize known internal spurious frequencies and flag them.

---

#### 3.1.2 Spectral Range

---

**`ANAL-RNG-001` — Frequency-range extension**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `DEMONSTRATION`                                          |
| **New hardware**       | No                                                       |
| **Standard(s)**        | ITU-R SM.1537; `REF-001`                                 |
| **Dependencies**       | —                                                        |
| **HW constraints**     | `HWC-SDR-001`                                             |
| **Reconciliation**     | `AT_LIMIT`                                                |
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL extend the sensor's frequency range to capture emissions from 1 MHz up to 6 GHz.

**Acceptance Criteria:**

1. [ ] The system receives and processes signals in the 1 MHz – 6 GHz range.
2. [ ] Sensitivity at 1 MHz is verifiable with a calibrated signal generator.
3. [ ] Sensitivity at 6 GHz is verifiable with a calibrated signal generator.

**Notes:**  
Operates at the exact boundary of HWC-SDR-001 (1 MHz–6 GHz). Sensitivity degrades at band edges; characterization per REF-MEAS-001 is required. The upper limit depends on the connected antenna.

---

**`ANAL-RNG-002` — Real-time monitoring bandwidth**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `TEST`                                                   |
| **New hardware**       | No                                                       |
| **Standard(s)**        | —                                                        |
| **Dependencies**       | —                                                        |
| **HW constraints**     | `HWC-SDR-002`, `HWC-BUS-001`, `HWC-CPU-001`, `HWC-DRV-001` |
| **Reconciliation**     | `AT_LIMIT`                                                |
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL provide real-time monitoring with a minimum bandwidth of 20 MHz. It SHALL allow the bandwidth to be configured manually between 6 MHz and 20 MHz, and an automatic mode fixed at 20 MHz.

**Acceptance Criteria:**

1. [ ] The monitoring span can be configured between 6 MHz and 20 MHz in discrete steps.
2. [ ] In automatic mode, the span is fixed at 20 MHz.
3. [ ] The DSP pipeline processes the full bandwidth with a latency ≤ 1 second.

**Notes:**  
Multiple constraints converge: HWC-SDR-002 (20 MHz max BW), HWC-BUS-001 (USB 2.0 ~32 MB/s vs. 40 MB/s IQ), HWC-CPU-001 (processing budget), HWC-DRV-001 (end-to-end throughput). Operating at the hardware limit. Sample drops at sustained 20 MS/s are possible; the DSP pipeline must tolerate or detect them.

---

### 3.2 DSP Parameterization

#### 3.2.1 Frequency and Resolution Parameters

---

**`ANAL-PAR-001` — Parameterizable frequency range**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `DEMONSTRATION`                                          |
| **New hardware**       | No                                                       |
| **Standard(s)**        | —                                                        |
| **Dependencies**       | `ANAL-RNG-001`                                           |
| **HW constraints**     | `HWC-SDR-001`                                             |
| **Reconciliation**     | `BOUNDED`                                                 |
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL allow the user to enter frequency ranges to analyze within the available spectral range.

**Acceptance Criteria:**

1. [ ] The user can define a center frequency and span, or a start and stop frequency.
2. [ ] The system validates that the requested range is within the hardware limits (1 MHz–6 GHz per HWC-SDR-001).
3. [ ] Range changes are applied in real time without restarting the system.

**Notes:**  
Bounded by HWC-SDR-001 but not at the limit — user selects sub-ranges within the 1–6 GHz envelope.

---

**`ANAL-PAR-002` — RBW configuration**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `TEST`                                                   |
| **New hardware**       | No                                                       |
| **Standard(s)**        | —                                                        |
| **Dependencies**       | `ANAL-PAR-001`                                           |
| **HW constraints**     | —                                                         |
| **Reconciliation**     | `UNCONSTRAINED`                                           |
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL allow the resolution bandwidth (RBW) to be configured over a defined range.

**Acceptance Criteria:**

1. [ ] The RBW is user-configurable across a set of discrete values.
2. [ ] The available RBW ranges are documented (≥ 6 values).
3. [ ] Changing the RBW updates the DSP pipeline in real time.

**Notes:**  
RBW is purely a software/DSP parameter (FFT window size). No COTS constraint applies.

---

**`ANAL-PAR-003` — Frequency-resolution steps**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `TEST`                                                   |
| **New hardware**       | No                                                       |
| **Standard(s)**        | —                                                        |
| **Dependencies**       | `ANAL-PAR-002`                                           |
| **HW constraints**     | `HWC-CPU-001`                                             |
| **Reconciliation**     | `BOUNDED`                                                 |
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL offer resolution-change steps of 500 Hz, with a minimum resolution of 10 Hz.

**Acceptance Criteria:**

1. [ ] The frequency step is configurable in 500 Hz increments.
2. [ ] The minimum achievable resolution is 10 Hz.
3. [ ] The step accuracy is verified against a signal generator.

**Notes:**  
10 Hz resolution at 20 MS/s requires a 2,000,000-point FFT — computationally intensive on the RPi (HWC-CPU-001). May require reduced sample rates or offline processing for the finest resolutions.

---

**`ANAL-PAR-004` — VBW configuration**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `TEST`                                                   |
| **New hardware**       | Yes (filters)                                           |
| **Standard(s)**        | —                                                        |
| **Dependencies**       | `ANAL-PAR-002`                                           |
| **HW constraints**     | —                                                         |
| **Reconciliation**     | `UNCONSTRAINED`                                           |
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL implement Video Bandwidth (VBW) filters suited to the type of analysis (fine or average).

**Acceptance Criteria:**

1. [ ] The VBW is configurable independently of the RBW.
2. [ ] Filters are available for fine and averaged analysis.
3. [ ] The DSP output shows a perceptible difference between filtering modes.

**Notes:**  
VBW is implemented digitally in the DSP pipeline. No COTS hardware constraint applies. "New hardware: Yes" refers to potential analog filter stages, not a COTS limitation.

---

#### 3.2.2 Location and Units

---

**`ANAL-PAR-005` — Manual entry of GPS coordinates**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `DEMONSTRATION`                                          |
| **New hardware**       | No                                                       |
| **Standard(s)**        | —                                                        |
| **Dependencies**       | —                                                        |
| **HW constraints**     | `HWC-GPS-002`                                             |
| **Reconciliation**     | `UNCONSTRAINED`                                           |
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL allow the sensor's location coordinates to be entered manually when automatic GPS is unavailable.

**Acceptance Criteria:**

1. [ ] Latitude and longitude can be entered manually via the sensor configuration.
2. [ ] Manual coordinates are associated with the measurements taken.
3. [ ] The system records whether the location is automatic GPS or manual.

**Notes:**  
Manual entry is a software feature independent of GPS hardware constraints.

---

**`ANAL-PAR-006` — Conversion of measurement units**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `DEMONSTRATION`                                          |
| **New hardware**       | No                                                       |
| **Standard(s)**        | —                                                        |
| **Dependencies**       | —                                                        |
| **HW constraints**     | —                                                         |
| **Reconciliation**     | `UNCONSTRAINED`                                           |
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL allow the selection and conversion of measurement units: frequency (Hz, kHz, MHz, GHz), power (dBm, dBmV, dBµV, V, W), and electric field and power density (V/m, W/m², dBµV/m).

**Acceptance Criteria:**

1. [ ] All listed units are available as a sensor output parameter.
2. [ ] Conversion between units is mathematically correct (error < 0.01 dB).
3. [ ] A change of unit is applied to the DSP pipeline output data.

**Notes:**  
Pure software computation. No COTS constraint applies.

---

#### 3.2.3 Thresholds and Detection

---

**`ANAL-PAR-007` — Analysis and detection thresholds**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `TEST`                                                   |
| **New hardware**       | No                                                       |
| **Standard(s)**        | —                                                        |
| **Dependencies**       | —                                                        |
| **HW constraints**     | `HWC-SDR-004`                                             |
| **Reconciliation**     | `BOUNDED`                                                 |
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL allow detection thresholds to be parameterized and SHALL integrate algorithms to distinguish the noise floor from signal occupancy.

**Acceptance Criteria:**

1. [ ] The user can define a power threshold in dBm for signal detection.
2. [ ] The algorithm automatically distinguishes the noise floor from active signals.
3. [ ] Signals above the threshold are flagged in the sensor's output data.

**Notes:**  
Detection sensitivity is bounded by DANL (HWC-SDR-004). Signals below the noise floor cannot be detected regardless of threshold setting.

---

### 3.3 Signal Processing (DSP)

#### 3.3.1 Indicators and Traces

---

**`ANAL-MED-001` — Spectral indicators (traces)**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `DEMONSTRATION`                                          |
| **New hardware**       | No                                                       |
| **Standard(s)**        | ITU-R SM.1537; `REF-001`                                 |
| **Dependencies**       | `ANAL-PAR-001`                                           |
| **HW constraints**     | `HWC-CPU-001`                                             |
| **Reconciliation**     | `BOUNDED`                                                 |
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL compute spectral traces: maximum (max hold), minimum (min hold), average, and RMS, peak, and average detection modes.

**Acceptance Criteria:**

1. [ ] The maximum trace retains the highest value per frequency bin.
2. [ ] The minimum trace retains the lowest value per frequency bin.
3. [ ] The average trace computes the arithmetic mean over N sweeps (N configurable).
4. [ ] The RMS, peak, and average detection modes are selectable.

**Notes:**  
Trace accumulation is CPU-bound (HWC-CPU-001). Multiple simultaneous traces at 20 MHz BW must fit within the processing budget.

---

#### 3.3.2 Signal Measurements

---

**`ANAL-MED-003` — Occupied-bandwidth measurement**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `TEST`                                                   |
| **New hardware**       | No                                                       |
| **Standard(s)**        | ITU-R SM.1537; `REF-001`                                 |
| **Dependencies**       | `ANAL-MED-001`                                           |
| **HW constraints**     | `HWC-SDR-002`                                             |
| **Reconciliation**     | `BOUNDED`                                                 |
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL measure the occupied bandwidth (OBW) using the –X dB and 99% methods.

**Acceptance Criteria:**

1. [ ] –X dB method: measures the width where the signal falls X dB below the peak.
2. [ ] 99% method: measures the spectrum that contains 99% of the signal power.
3. [ ] Results are expressed in the selected frequency unit.

**Notes:**  
OBW measurement is limited to signals within the 20 MHz instantaneous BW (HWC-SDR-002). Wider signals require sweep mode with stitching.

---

**`ANAL-MED-004` — Channel power (up to 20 MHz)**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `TEST`                                                   |
| **New hardware**       | No                                                       |
| **Standard(s)**        | —                                                        |
| **Dependencies**       | `ANAL-RNG-002`                                           |
| **HW constraints**     | `HWC-SDR-002`                                             |
| **Reconciliation**     | `AT_LIMIT`                                                |
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL perform channel-power measurements for emissions up to 20 MHz wide.

**Acceptance Criteria:**

1. [ ] Channel-power measurement is selectable via a configuration parameter.
2. [ ] The measured channel width is configurable up to 20 MHz.
3. [ ] The result is expressed in the selected power units.

**Notes:**  
20 MHz channel power = full instantaneous BW of HWC-SDR-002. At the exact hardware limit.

---

#### 3.3.3 Sound Broadcasting

---

**`ANAL-MED-005` — RDS reading in FM**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `DEMONSTRATION`                                          |
| **New hardware**       | No                                                       |
| **Standard(s)**        | —                                                        |
| **Dependencies**       | —                                                        |
| **HW constraints**     | —                                                         |
| **Reconciliation**     | `UNCONSTRAINED`                                           |
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL decode and extract RDS information from FM signals.

**Acceptance Criteria:**

1. [ ] The system decodes basic RDS fields (PI, PS, RT).
2. [ ] The RDS information is included in the sensor's output data alongside the FM measurement.

**Notes:**  
Pure DSP software function. No COTS constraint applies.

---

**`ANAL-MED-006` — FM and AM demodulation**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `DEMONSTRATION`                                          |
| **New hardware**       | No                                                       |
| **Standard(s)**        | —                                                        |
| **Dependencies**       | `ANAL-RNG-001`                                           |
| **HW constraints**     | `HWC-SDR-001`                                             |
| **Reconciliation**     | `BOUNDED`                                                 |
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL demodulate FM and AM signals in real time, producing digital audio as output.

**Acceptance Criteria:**

1. [ ] FM audio is demodulated with audible quality.
2. [ ] AM audio is demodulated with audible quality (from 1 MHz).
3. [ ] The demodulated audio is stored locally or transmitted as a stream.

**Notes:**  
AM from 1 MHz is at the lower edge of HWC-SDR-001. Sensitivity degradation below 10 MHz may affect AM demodulation quality. Requires an additional antenna for AM band.

---

**`ANAL-MED-007` — AM and FM modulation measurement**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `TEST`                                                   |
| **New hardware**       | No                                                       |
| **Standard(s)**        | —                                                        |
| **Dependencies**       | `ANAL-MED-006`                                           |
| **HW constraints**     | —                                                         |
| **Reconciliation**     | `UNCONSTRAINED`                                           |
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL directly measure the AM modulation depth and the FM frequency deviation.

**Acceptance Criteria:**

1. [ ] The AM modulation depth is computed as a percentage.
2. [ ] The FM frequency deviation is computed in kHz.
3. [ ] The values update in real time during demodulation.

**Notes:**  
Computed in DSP from demodulated IQ. No additional COTS constraint beyond what applies to demodulation itself.

---

### 3.4 Local (Edge) Detection

#### 3.4.1 Signal-Parameter Verification

---

**`NORM-VER-001` — Intermodulation detection**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `TEST`                                                   |
| **New hardware**       | No                                                       |
| **Standard(s)**        | —                                                        |
| **Dependencies**       | `ANAL-MED-001`                                           |
| **HW constraints**     | `HWC-SDR-007`                                             |
| **Reconciliation**     | `MITIGATED`                                               |
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL detect intermodulation, including suspected products in AM, FM, and the aeronautical band (108–137 MHz), as well as IF verification.

**Acceptance Criteria:**

1. [ ] The system computes 2nd- and 3rd-order intermodulation products for detected emissions.
2. [ ] Suspected intermodulation products are flagged in the spectral output data.
3. [ ] IF verification is performed automatically.

**Notes:**  
Mitigation for HWC-SDR-007 (no pre-selection filters): the detection algorithm must distinguish receiver-generated intermodulation from real over-the-air products. This requires characterizing the HackRF's own IM products at known signal levels and frequencies.

---

**`NORM-VER-002` — Interference detection**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `TEST`                                                   |
| **New hardware**       | No                                                       |
| **Standard(s)**        | —                                                        |
| **Dependencies**       | `ANAL-PAR-007`                                           |
| **HW constraints**     | `HWC-SDR-004`                                             |
| **Reconciliation**     | `BOUNDED`                                                 |
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL detect interference, defined as signals exceeding the average level of the channel or band by more than 3 dB.

**Acceptance Criteria:**

1. [ ] Signals more than 3 dB above the average level are detected as potential interference.
2. [ ] A local record is generated with frequency, power, and duration data.
3. [ ] Detection runs continuously without external intervention.

**Notes:**  
Detection floor bounded by DANL (HWC-SDR-004). Interference below the noise floor is undetectable.

---

#### 3.4.2 Audio Extraction

---

**`NORM-SRV-002` — Audio extraction for verification**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `DEMONSTRATION`                                          |
| **New hardware**       | No                                                       |
| **Standard(s)**        | —                                                        |
| **Dependencies**       | `ANAL-MED-006`                                           |
| **HW constraints**     | `HWC-STR-001`                                             |
| **Reconciliation**     | `BOUNDED`                                                 |
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL demodulate and extract audio from FM and AM signals, storing it locally for later forensic analysis.

**Acceptance Criteria:**

1. [ ] The extracted audio is stored locally in a standard format (WAV or MP3).
2. [ ] The audio file is associated with the measurement metadata (frequency, timestamp, location).

**Notes:**  
Audio files are small compared to CS8 IQ captures; storage write speed (HWC-STR-001) is not a bottleneck here.

---

### 3.5 Local Storage

---

**`FORN-ALM-001` — Local historical storage for forensic analysis**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `DEMONSTRATION`                                          |
| **New hardware**       | No                                                       |
| **Standard(s)**        | ITU-R SM.1537; `REF-001`                                 |
| **Dependencies**       | —                                                        |
| **HW constraints**     | `HWC-STR-001`, `HWC-DRV-001`                             |
| **Reconciliation**     | `BOUNDED`                                                 |
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL provide local historical storage for forensic analysis, including spectral data with a timestamp and GPS location.

**Acceptance Criteria:**

1. [ ] Monitoring data is stored locally with a timestamp and GPS coordinates.
2. [ ] Historical data is queryable by date range, frequency, and location.
3. [ ] The integrity of the stored data is verifiable (checksum or hash).

**Notes:**  
Processed spectral data (PSD, traces) is much smaller than raw IQ and does not stress storage bandwidth. Raw CS8 storage at full rate is constrained by HWC-DRV-001 (end-to-end throughput).

---

**`FORN-ALM-003` — Expanded storage on the sensor**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `DEMONSTRATION`                                          |
| **New hardware**       | Yes                                                     |
| **Standard(s)**        | —                                                        |
| **Dependencies**       | —                                                        |
| **HW constraints**     | `HWC-STR-001`                                             |
| **Reconciliation**     | `AT_LIMIT`                                                |
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL add storage space to the sensor so that CS8 files (raw IQ) can be stored for later use as forensic evidence.

**Acceptance Criteria:**

1. [ ] The sensor has accessible additional storage.
2. [ ] CS8 files are stored with metadata (timestamp, frequency, coordinates).
3. [ ] Local storage is remotely accessible for download.

**Notes:**  
Raw CS8 at 20 MS/s = 40 MB/s. Storage must sustain ≥ 40 MB/s writes (HWC-STR-001). USB 3.0 SSD recommended; microSD may not meet sustained write requirements.

---

### 3.6 Edge Connectivity

#### 3.6.1 Network Interfaces

---

**`CONN-RED-001` — 4G/5G module**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `DEMONSTRATION`                                          |
| **New hardware**       | Yes                                                     |
| **Standard(s)**        | —                                                        |
| **Dependencies**       | —                                                        |
| **HW constraints**     | —                                                         |
| **Reconciliation**     | `UNCONSTRAINED`                                           |
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL add or replace the mobile-connectivity module to support a data SIM card provided by the ANE, with multi-carrier data service.

**Acceptance Criteria:**

1. [ ] The module supports 4G and 5G networks.
2. [ ] It works with SIM cards from at least 2 Colombian carriers.
3. [ ] The connection is established automatically when the sensor powers on.

**Notes:**  
The 4G/5G modem is new hardware selected to meet the requirement. No pre-existing COTS constraint applies — the modem is chosen to fit.

---

**`CONN-RED-002` — WiFi connection**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `SHOULD`                                                  |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `DEMONSTRATION`                                          |
| **New hardware**       | No                                                       |
| **Standard(s)**        | —                                                        |
| **Dependencies**       | —                                                        |
| **HW constraints**     | —                                                         |
| **Reconciliation**     | `UNCONSTRAINED`                                           |
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL enable a WiFi connection on the sensor, configurable via Ethernet cable.

**Acceptance Criteria:**

1. [ ] The sensor connects to configured WiFi networks.
2. [ ] WiFi configuration is performed initially over an Ethernet cable.
3. [ ] The WiFi connection is used as an alternative communication channel.

**Notes:**  
RPi 4B has built-in WiFi. No COTS constraint.

---

**`CONN-RED-003` — Accessible Ethernet port**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `INSPECTION`                                             |
| **New hardware**       | Yes                                                     |
| **Standard(s)**        | —                                                        |
| **Dependencies**       | —                                                        |
| **HW constraints**     | —                                                         |
| **Reconciliation**     | `UNCONSTRAINED`                                           |
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL provide access to an easily accessible Ethernet port without requiring the enclosure to be opened.

**Acceptance Criteria:**

1. [ ] The Ethernet port is externally accessible without tools.
2. [ ] The port supports a minimum speed of 100 Mbps.

**Notes:**  
Enclosure design requirement. The RPi Ethernet hardware is not the constraint — the physical access is.

---

**`CONN-RED-004` — Network auto-routing**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `TEST`                                                   |
| **New hardware**       | No                                                       |
| **Standard(s)**        | —                                                        |
| **Dependencies**       | `CONN-RED-001`, `CONN-RED-002`, `CONN-RED-003`           |
| **HW constraints**     | —                                                         |
| **Reconciliation**     | `UNCONSTRAINED`                                           |
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL implement automatic IP-network connection and routing with failover/priority among 4G/5G, WiFi, and Ethernet.

**Acceptance Criteria:**

1. [ ] The system automatically selects the available network channel with the highest priority.
2. [ ] Failover between channels occurs without manual intervention.
3. [ ] The priority order is configurable.

**Notes:**  
Software networking stack. No COTS constraint.

---

#### 3.6.2 Support and GPS

---

**`CONN-SOP-001` — Remote access and software update**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `DEMONSTRATION`                                          |
| **New hardware**       | No                                                       |
| **Standard(s)**        | —                                                        |
| **Dependencies**       | `CONN-RED-004`                                           |
| **HW constraints**     | —                                                         |
| **Reconciliation**     | `UNCONSTRAINED`                                           |
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL allow remote IP access and OTA software updates.

**Acceptance Criteria:**

1. [ ] The sensor can be accessed remotely via SSH or a secure equivalent.
2. [ ] Software updates are performed without physical access.
3. [ ] The update process includes automatic rollback in case of failure.

**Notes:**  
Pure software. No COTS constraint.

---

**`CONN-GPS-001` — GPS location redundancy**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `TEST`                                                   |
| **New hardware**       | No                                                       |
| **Standard(s)**        | —                                                        |
| **Dependencies**       | `ANAL-PAR-005`                                           |
| **HW constraints**     | `HWC-GPS-002`                                             |
| **Reconciliation**     | `UNCONSTRAINED`                                           |
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL continue to report location via GPS regardless of manual parameterization.

**Acceptance Criteria:**

1. [ ] GPS continues to report an automatic location even when manual coordinates are configured.
2. [ ] Both location sources are stored in the measurement records.

**Notes:**  
GPS NMEA output (HWC-GPS-002) is always available. Software stores both sources.

---

**`CONN-GPS-002` — GPS accuracy**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `NON_FUNCTIONAL`                                         |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `TEST`                                                   |
| **New hardware**       | Yes                                                     |
| **Standard(s)**        | —                                                        |
| **Dependencies**       | —                                                        |
| **HW constraints**     | `HWC-GPS-001`                                             |
| **Reconciliation**     | `BOUNDED`                                                 |
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL have a horizontal GPS accuracy of approximately 3 meters under open sky.

**Acceptance Criteria:**

1. [ ] Horizontal accuracy ≤ 3 m (CEP 50%) under open-sky conditions.
2. [ ] The accuracy is verified against a reference GPS receiver.

**Notes:**  
Drives GPS module selection (HWC-GPS-001). Module TBD — must meet ≤ 3 m spec.

---

### 3.7 Antennas and Radiation Measurement

#### 3.7.1 Antennas

---

**`ANTE-ANT-001` — New antennas for specific bands**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `INSPECTION`                                             |
| **New hardware**       | Yes                                                     |
| **Standard(s)**        | —                                                        |
| **Dependencies**       | `ANAL-RNG-001`                                           |
| **HW constraints**     | `HWC-SDR-001`                                             |
| **Reconciliation**     | `BOUNDED`                                                 |
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL incorporate specific antennas for signal reception to optimize reception across different bands.

**Acceptance Criteria:**

1. [ ] A specific antenna for DTT.
2. [ ] Verification of an antenna for frequencies > 2 GHz (mobile-telephony downlink).
3. [ ] Each antenna has a documented and calibrated antenna factor (AF).

**Notes:**  
Antennas selected to match the HackRF's 1–6 GHz range (HWC-SDR-001). Antenna switching via HW-MUX and GPIO.

---

**`ANTE-ANT-002` — Active antenna for non-ionizing radiation**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `TEST`                                                   |
| **New hardware**       | Yes                                                     |
| **Standard(s)**        | ITU-T K.113, K.100; `REF-003`, `REF-004`                 |
| **Dependencies**       | —                                                        |
| **HW constraints**     | `HWC-SDR-001`                                             |
| **Reconciliation**     | `BOUNDED`                                                 |
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL incorporate an active antenna with a frequency range up to 6 GHz, with a SAW filter, a flat response, and a known antenna factor.

**Acceptance Criteria:**

1. [ ] The active antenna's frequency range covers up to 6 GHz.
2. [ ] It includes a SAW filter.
3. [ ] A flat frequency response (variation ≤ 2 dB across the full range).
4. [ ] An antenna factor documented by the manufacturer.

**Notes:**  
Antenna range must match or exceed HWC-SDR-001 (6 GHz). The antenna factor is essential for field-strength computation (ANTE-RNI-002).

---

#### 3.7.2 Non-Ionizing Radiation Measurement

---

**`ANTE-RNI-001` — Measurement units for radiation**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `DEMONSTRATION`                                          |
| **New hardware**       | No                                                       |
| **Standard(s)**        | ITU-T K.113, K.100; `REF-003`, `REF-004`                 |
| **Dependencies**       | `ANTE-ANT-002`                                           |
| **HW constraints**     | —                                                         |
| **Reconciliation**     | `UNCONSTRAINED`                                           |
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL adopt measurement units for non-ionizing radiation: S (W/m²), A/m, V/m, dBµV/m, dBA/m.

**Acceptance Criteria:**

1. [ ] All listed units are available as a display option.
2. [ ] Conversions between units are correct.

**Notes:**  
Pure computation. No COTS constraint.

---

**`ANTE-RNI-002` — Field-strength measurement**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `TEST`                                                   |
| **New hardware**       | No                                                       |
| **Standard(s)**        | ITU-T K.113, K.100; `REF-003`, `REF-004`                 |
| **Dependencies**       | `ANTE-ANT-002`, `ANTE-RNI-001`                           |
| **HW constraints**     | `HWC-SDR-006`                                             |
| **Reconciliation**     | `MITIGATED`                                               |
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL measure field strength using the antenna factor (AF).

**Acceptance Criteria:**

1. [ ] The field measurement uses the AF of the connected antenna.
2. [ ] E [V/m] = V_measured [V] × AF.
3. [ ] Results are presented in V/m and dBµV/m.

**Notes:**  
Mitigation for HWC-SDR-006 (no AGC): amplitude accuracy for field-strength computation requires a software calibration table mapping gain settings to correction factors. The AF must be applied on top of this correction.

---

### 3.8 Power and Autonomy

---

**`POWR-AUT-001` — Autonomous power modules**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `DEMONSTRATION`                                          |
| **New hardware**       | Yes                                                     |
| **Standard(s)**        | —                                                        |
| **Dependencies**       | —                                                        |
| **HW constraints**     | `HWC-PWR-001`                                             |
| **Reconciliation**     | `BOUNDED`                                                 |
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL integrate autonomous power modules through sustainable solutions (solar + battery + charge manager).

**Acceptance Criteria:**

1. [ ] The sensor operates on solar + battery power without an external source.
2. [ ] It includes a battery manager with a charge indicator.
3. [ ] The solar-panel design is discreet.

**Notes:**  
Solar panel + battery must supply ≥ 15 W continuous (HWC-PWR-001) for 24/7 operation. Sizing must account for worst-case solar irradiance in Colombia.

---

### 3.9 Sensor Health Monitoring

---

**`GEST-MON-001` — Sensor health monitoring**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `DEMONSTRATION`                                          |
| **New hardware**       | No                                                       |
| **Standard(s)**        | —                                                        |
| **Dependencies**       | —                                                        |
| **HW constraints**     | `HWC-CPU-002`, `HWC-CPU-003`                              |
| **Reconciliation**     | `BOUNDED`                                                 |
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL measure and record sensor health variables (disk, RAM, CPU, temperature).

**Acceptance Criteria:**

1. [ ] At least: disk usage, RAM, CPU, and temperature are monitored.
2. [ ] Local alerts are generated when variables exceed configurable thresholds.
3. [ ] Health data is stored locally with a timestamp.

**Notes:**  
Temperature monitoring especially important: RPi throttles above 80 °C (HWC-CPU-003). Alert thresholds should warn before throttle onset.

---

**`GEST-MON-002` — Network and connectivity monitoring**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `TEST`                                                   |
| **New hardware**       | No                                                       |
| **Standard(s)**        | —                                                        |
| **Dependencies**       | —                                                        |
| **HW constraints**     | —                                                         |
| **Reconciliation**     | `UNCONSTRAINED`                                           |
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL measure and record IP-connection quality: RTT, channel status, available bandwidth, and packet loss.

**Acceptance Criteria:**

1. [ ] RTT is measured periodically (configurable interval).
2. [ ] The Alive/Not Alive status of each network interface is detected.
3. [ ] A local record is generated when RTT or packet loss exceeds thresholds.

**Notes:**  
Software network diagnostics. No COTS constraint.

---

**`GEST-PRG-001` — Scheduled spectrum scan**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `DEMONSTRATION`                                          |
| **New hardware**       | No                                                       |
| **Standard(s)**        | ITU-R SM.1537; `REF-001`                                 |
| **Dependencies**       | `ANAL-PAR-001`                                           |
| **HW constraints**     | —                                                         |
| **Reconciliation**     | `UNCONSTRAINED`                                           |
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL allow parameterized spectrum scans to be scheduled, run locally, and stored.

**Acceptance Criteria:**

1. [ ] Scans can be scheduled with defined parameters (frequency, RBW, VBW, duration, repetition).
2. [ ] Results are stored locally.
3. [ ] Scans run at the scheduled time with a tolerance ≤ 1 minute.

**Notes:**  
Local scheduler (cron or equivalent). No COTS constraint.

---

### 3.10 Accuracy and Calibration

#### 3.10.1 Synchronization and Calibration

---

**`CONF-SIN-001` — NTP synchronization**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `NON_FUNCTIONAL`                                         |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `TEST`                                                   |
| **New hardware**       | No                                                       |
| **Standard(s)**        | —                                                        |
| **Dependencies**       | `CONN-RED-004`                                           |
| **HW constraints**     | —                                                         |
| **Reconciliation**     | `UNCONSTRAINED`                                           |
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL synchronize to an NTP network clock for time-stamping.

**Acceptance Criteria:**

1. [ ] The sensor synchronizes with an NTP server when a network connection is established.
2. [ ] The time offset is ≤ 100 ms relative to the NTP server.
3. [ ] The synchronization status is queryable locally.

**Notes:**  
NTP client is software. No COTS constraint.

---

**`CONF-CAL-001` — Calibration procedures**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `NON_FUNCTIONAL`                                         |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `ANALYSIS`                                               |
| **New hardware**       | No                                                       |
| **Standard(s)**        | —                                                        |
| **Dependencies**       | —                                                        |
| **HW constraints**     | `HWC-SDR-006`                                             |
| **Reconciliation**     | `MITIGATED`                                               |
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL include calibration procedures for frequency, receive gain, IQ balance, and DC-offset correction.

**Acceptance Criteria:**

1. [ ] A documented frequency-calibration procedure.
2. [ ] A documented gain-calibration procedure.
3. [ ] A documented procedure for IQ-balance and DC-offset correction.
4. [ ] Each calibration produces a certificate or record with a date and result.

**Notes:**  
Mitigation for HWC-SDR-006 (no AGC/calibrated attenuator): calibration must use external reference sources (signal generator, known-level source) to build correction tables that compensate for the HackRF's gain uncertainty.

---

#### 3.10.2 System Characterization

---

**`CONF-CAR-001` — DANL (Displayed Average Noise Level)**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `NON_FUNCTIONAL`                                         |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `TEST`                                                   |
| **New hardware**       | No                                                       |
| **Standard(s)**        | ITU-R SM.1138; `REF-002`                                 |
| **Dependencies**       | —                                                        |
| **HW constraints**     | `HWC-SDR-004`                                             |
| **Reconciliation**     | `AT_LIMIT`                                                |
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL have a minimum DANL of –100 dBm across the operating range.

**Acceptance Criteria:**

1. [ ] The measured DANL is ≤ –100 dBm over at least 90% of the frequency range.
2. [ ] The measurement is performed with a 50 Ω load and documented per band.

**Notes:**  
At the exact limit of HWC-SDR-004 (estimated −100 dBm/Hz). Formal per-band characterization is required (REF-MEAS-001). Software averaging can improve effective DANL at the cost of temporal resolution.

---

**`CONF-CAR-002` — Dynamic range**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `NON_FUNCTIONAL`                                         |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `TEST`                                                   |
| **New hardware**       | No                                                       |
| **Standard(s)**        | ITU-R SM.1138; `REF-002`                                 |
| **Dependencies**       | `CONF-CAR-001`                                           |
| **HW constraints**     | `HWC-SDR-003`, `HWC-DRV-002`                             |
| **Reconciliation**     | `MITIGATED`                                               |
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL have a minimum dynamic range of ≥ 80 dB.

**Acceptance Criteria:**

1. [ ] Measured dynamic range ≥ 80 dB in a two-tone test.
2. [ ] The measurement is documented with the test setup and results.

**Notes:**  
Mitigation for HWC-SDR-003 (8-bit ADC, ~48 dB single-capture SFDR) and HWC-DRV-002 (achievable ~90 dB with software techniques). Requires gain-stepped captures at multiple LNA/VGA settings + spectral averaging. Must be validated experimentally.

---

**`CONF-CAR-003` — Frequency accuracy**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `NON_FUNCTIONAL`                                         |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `TEST`                                                   |
| **New hardware**       | No                                                       |
| **Standard(s)**        | —                                                        |
| **Dependencies**       | —                                                        |
| **HW constraints**     | `HWC-SDR-005`                                             |
| **Reconciliation**     | `MITIGATED`                                               |
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL have a maximum frequency accuracy of ± 2 ppm.

**Acceptance Criteria:**

1. [ ] Measured frequency error ≤ ± 2 ppm against a calibrated reference.
2. [ ] The measurement is performed at room temperature (20–25 °C).

**Notes:**  
Mitigation for HWC-SDR-005 (stock oscillator ± 20 ppm): replace with TCXO (± 0.5–2 ppm) or use GPS-disciplined frequency correction. One of these mitigations is required to meet the ± 2 ppm target.

---

**`CONF-CAR-004` — Delta aging (oscillator aging)**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `NON_FUNCTIONAL`                                         |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `ANALYSIS`                                               |
| **New hardware**       | Yes (oscillator change possible)                        |
| **Standard(s)**        | —                                                        |
| **Dependencies**       | `CONF-CAR-003`                                           |
| **HW constraints**     | `HWC-SDR-005`                                             |
| **Reconciliation**     | `MITIGATED`                                               |
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL meet a frequency drift due to aging of ≤ 1 ppm per year.

**Acceptance Criteria:**

1. [ ] The selected oscillator has an aging specification of ≤ 1 ppm/year.
2. [ ] The oscillator type and its aging specification are documented.

**Notes:**  
Mitigation: the TCXO or OCXO selected for CONF-CAR-003 must also meet ≤ 1 ppm/year aging. GPS-disciplined correction provides continuous compensation regardless of aging.

---

**`CONF-CAR-005` — Amplitude accuracy**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `NON_FUNCTIONAL`                                         |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `TEST`                                                   |
| **New hardware**       | No                                                       |
| **Standard(s)**        | —                                                        |
| **Dependencies**       | —                                                        |
| **HW constraints**     | `HWC-SDR-003`, `HWC-SDR-006`                              |
| **Reconciliation**     | `MITIGATED`                                               |
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL have a typical amplitude accuracy of ± 1 dB.

**Acceptance Criteria:**

1. [ ] Amplitude error ≤ ± 1 dB over at least 90% of the frequency range.
2. [ ] Amplitude linearity is verified in 10 dB steps.

**Notes:**  
Mitigation for HWC-SDR-003 (8-bit) + HWC-SDR-006 (no AGC/calibrated attenuators): requires per-frequency, per-gain-setting calibration tables built using external reference sources. Image noise artifacts must be characterized and compensated.

---

## 4. External Interface Requirements

### 4.1 Hardware Interfaces

_Detailed specifications are in HCS-ANE-EDGE-001. Summary:_

- SDR: HackRF One (USB 2.0, internal SPI)
- Embedded platform: Raspberry Pi 4B
- GPS: Module TBD (UART/USB, ≤ 3 m accuracy)
- Antennas: SMA connectors for band-specific and active antennas
- 4G/5G module: USB with SIM slot
- WiFi: RPi integrated or external USB
- Ethernet: externally accessible RJ45
- GPIO: antenna mux switching and peripheral control
- Power: solar panel + battery + charge manager
- Storage: USB 3.0 SSD or high-capacity microSD

### 4.2 Software Interfaces

- SDR driver: libhackrf / SoapySDR (see HCS REF-DRV-001, REF-DRV-002)
- DSP pipeline: FFT, PSD, RBW/VBW filtering
- Scheduler: cron or equivalent
- Network manager: automatic failover
- NTP client: time synchronization

### 4.3 Communication Interfaces

- HackRF ↔ RPi: USB 2.0 (see HWC-BUS-001, HWC-DRV-001)
- GPS ↔ RPi: UART/USB, NMEA (see HWC-GPS-002)
- 4G/5G ↔ RPi: USB (AT commands + data)
- GPIO: antenna mux, status LEDs, battery sensors

---

## 5. Non-Functional Requirements

### 5.1 Performance

- DSP pipeline latency ≤ 1 second for 20 MHz bandwidth (bounded by HWC-CPU-001, HWC-BUS-001).
- Minimum frequency resolution: 10 Hz (bounded by HWC-CPU-001).
- Scheduled scans: tolerance ≤ 1 minute.

### 5.2 Reliability

- Network auto-routing for connectivity availability (`CONN-RED-004`).
- Local storage in case of connectivity loss (`FORN-ALM-003`).
- NTP sync ≤ 100 ms offset (`CONF-SIN-001`).

### 5.3 Maintainability

- OTA software updates with rollback (`CONN-SOP-001`).
- Remote SSH access for diagnostics.
- Documented calibration procedures (`CONF-CAL-001`).

### 5.4 Accuracy

- DANL ≤ –100 dBm — at HWC-SDR-004 limit (`CONF-CAR-001`).
- Dynamic range ≥ 80 dB — mitigated via software (`CONF-CAR-002`).
- Frequency accuracy ± 2 ppm — mitigated via TCXO/GPS (`CONF-CAR-003`).
- Amplitude accuracy ± 1 dB — mitigated via calibration tables (`CONF-CAR-005`).

---

## 6. Traceability

| Requirement ID   | Subsystem              | Standard Ref        | HW Constraint(s)                        | Reconciliation  | New HW |
|------------------|------------------------|---------------------|-----------------------------------------|-----------------|--------|
| `ANAL-EMC-001`   | RF architecture        | —                   | `HWC-SDR-007`                           | `MITIGATED`     | Yes    |
| `ANAL-RNG-001`   | Spectral range         | ITU-R SM.1537       | `HWC-SDR-001`                           | `AT_LIMIT`      | No     |
| `ANAL-RNG-002`   | Bandwidth              | —                   | `HWC-SDR-002`, `HWC-BUS-001`, `HWC-CPU-001`, `HWC-DRV-001` | `AT_LIMIT` | No |
| `ANAL-PAR-001`   | DSP parameterization   | —                   | `HWC-SDR-001`                           | `BOUNDED`       | No     |
| `ANAL-PAR-002`   | DSP parameterization   | —                   | —                                       | `UNCONSTRAINED` | No     |
| `ANAL-PAR-003`   | DSP parameterization   | —                   | `HWC-CPU-001`                           | `BOUNDED`       | No     |
| `ANAL-PAR-004`   | DSP parameterization   | —                   | —                                       | `UNCONSTRAINED` | Yes    |
| `ANAL-PAR-005`   | GPS                    | —                   | `HWC-GPS-002`                           | `UNCONSTRAINED` | No     |
| `ANAL-PAR-006`   | Units                  | —                   | —                                       | `UNCONSTRAINED` | No     |
| `ANAL-PAR-007`   | Detection              | —                   | `HWC-SDR-004`                           | `BOUNDED`       | No     |
| `ANAL-MED-001`   | DSP / traces           | ITU-R SM.1537       | `HWC-CPU-001`                           | `BOUNDED`       | No     |
| `ANAL-MED-003`   | DSP / OBW              | ITU-R SM.1537       | `HWC-SDR-002`                           | `BOUNDED`       | No     |
| `ANAL-MED-004`   | DSP / channel power    | —                   | `HWC-SDR-002`                           | `AT_LIMIT`      | No     |
| `ANAL-MED-005`   | DSP / RDS              | —                   | —                                       | `UNCONSTRAINED` | No     |
| `ANAL-MED-006`   | DSP / demodulation     | —                   | `HWC-SDR-001`                           | `BOUNDED`       | No     |
| `ANAL-MED-007`   | DSP / modulation       | —                   | —                                       | `UNCONSTRAINED` | No     |
| `NORM-VER-001`   | Local detection        | —                   | `HWC-SDR-007`                           | `MITIGATED`     | No     |
| `NORM-VER-002`   | Local detection        | —                   | `HWC-SDR-004`                           | `BOUNDED`       | No     |
| `NORM-SRV-002`   | Forensic audio         | —                   | `HWC-STR-001`                           | `BOUNDED`       | No     |
| `FORN-ALM-001`   | Local storage          | ITU-R SM.1537       | `HWC-STR-001`, `HWC-DRV-001`           | `BOUNDED`       | No     |
| `FORN-ALM-003`   | Local storage          | —                   | `HWC-STR-001`                           | `AT_LIMIT`      | Yes    |
| `CONN-RED-001`   | Connectivity           | —                   | —                                       | `UNCONSTRAINED` | Yes    |
| `CONN-RED-002`   | Connectivity           | —                   | —                                       | `UNCONSTRAINED` | No     |
| `CONN-RED-003`   | Connectivity           | —                   | —                                       | `UNCONSTRAINED` | Yes    |
| `CONN-RED-004`   | Connectivity           | —                   | —                                       | `UNCONSTRAINED` | No     |
| `CONN-SOP-001`   | Maintenance            | —                   | —                                       | `UNCONSTRAINED` | No     |
| `CONN-GPS-001`   | GPS                    | —                   | `HWC-GPS-002`                           | `UNCONSTRAINED` | No     |
| `CONN-GPS-002`   | GPS                    | —                   | `HWC-GPS-001`                           | `BOUNDED`       | Yes    |
| `ANTE-ANT-001`   | Antennas               | —                   | `HWC-SDR-001`                           | `BOUNDED`       | Yes    |
| `ANTE-ANT-002`   | Antennas               | ITU-T K.113, K.100  | `HWC-SDR-001`                           | `BOUNDED`       | Yes    |
| `ANTE-RNI-001`   | Non-ionizing radiation | ITU-T K.113, K.100  | —                                       | `UNCONSTRAINED` | No     |
| `ANTE-RNI-002`   | Non-ionizing radiation | ITU-T K.113, K.100  | `HWC-SDR-006`                           | `MITIGATED`     | No     |
| `POWR-AUT-001`   | Power                  | —                   | `HWC-PWR-001`                           | `BOUNDED`       | Yes    |
| `GEST-MON-001`   | Health monitoring      | —                   | `HWC-CPU-002`, `HWC-CPU-003`           | `BOUNDED`       | No     |
| `GEST-MON-002`   | Health monitoring      | —                   | —                                       | `UNCONSTRAINED` | No     |
| `GEST-PRG-001`   | Local scheduler        | ITU-R SM.1537       | —                                       | `UNCONSTRAINED` | No     |
| `CONF-SIN-001`   | Synchronization        | —                   | —                                       | `UNCONSTRAINED` | No     |
| `CONF-CAL-001`   | Calibration            | —                   | `HWC-SDR-006`                           | `MITIGATED`     | No     |
| `CONF-CAR-001`   | Characterization       | ITU-R SM.1138       | `HWC-SDR-004`                           | `AT_LIMIT`      | No     |
| `CONF-CAR-002`   | Characterization       | ITU-R SM.1138       | `HWC-SDR-003`, `HWC-DRV-002`           | `MITIGATED`     | No     |
| `CONF-CAR-003`   | Characterization       | —                   | `HWC-SDR-005`                           | `MITIGATED`     | No     |
| `CONF-CAR-004`   | Characterization       | —                   | `HWC-SDR-005`                           | `MITIGATED`     | Yes    |
| `CONF-CAR-005`   | Characterization       | —                   | `HWC-SDR-003`, `HWC-SDR-006`           | `MITIGATED`     | No     |

---

## 7. G0 Structural Validation (Future Work)

> **Status:** `PLANNED` — This section defines the objective for automated AI-based structural validation of the SRS–HCS document pair. Implementation is deferred to a future phase.

### 7.1 Objective

G0 is an AI agent whose purpose is to structurally validate the consistency and completeness of the SRS–HCS document pair. G0 does NOT generate requirements; it reviews them.

### 7.2 G0 Input Contract

| Input                | Source Document      | Format                                    |
|----------------------|----------------------|-------------------------------------------|
| Requirements         | SRS-ANE-EDGE-001     | Requirement blocks per Section 3 schema   |
| COTS Constraints     | HCS-ANE-EDGE-001     | Constraint blocks per HCS Section 3 schema |
| Reconciliation status| SRS-ANE-EDGE-001     | `reconciliation` field per requirement    |

### 7.3 G0 Validation Rules (Planned)

1. **Structural completeness:** Every mandatory field is present and uses a valid enum value.
2. **ID uniqueness:** No duplicate IDs across the SRS–HCS pair.
3. **Cross-reference integrity:** Every `hw_constraints` ID in the SRS exists in the HCS, and vice versa.
4. **Reconciliation consistency:** If `hw_constraints` is non-empty, `reconciliation` cannot be `UNCONSTRAINED` (exception: when the constraint is `INFORMATIONAL` impact).
5. **Conflict detection:** If a requirement's quantitative parameter matches a constraint's limit, `reconciliation` must be `AT_LIMIT` or `MITIGATED`.
6. **Mitigation documentation:** If `reconciliation` is `MITIGATED`, `notes` must describe the mitigation.
7. **Dependency graph:** No circular dependencies. All referenced IDs exist.
8. **Traceability coverage:** Every requirement in Section 3 appears in the Section 6 matrix.

### 7.4 G0 Output

A **Conflict Analysis Matrix**:

| Conflict ID | Requirement      | Constraint      | Severity                         | Resolution           |
|-------------|-----------------|-----------------|----------------------------------|----------------------|
| `CON-001`   | `ANAL-RNG-001`  | `HWC-SDR-001`  | `OK` — boundary match           | None needed          |
| `CON-002`   | `CONF-CAR-002`  | `HWC-SDR-003`  | `WARNING` — 80 dB vs 48 dB ADC  | Gain stepping + averaging |
| `CON-003`   | `CONF-CAR-003`  | `HWC-SDR-005`  | `CONFLICT` — ±2 ppm vs ±20 ppm  | TCXO replacement or GPS discipline |
| `CON-004`   | `ANAL-RNG-002`  | `HWC-BUS-001`  | `WARNING` — 40 MB/s vs 32 MB/s  | Accept sample drops or reduce rate |

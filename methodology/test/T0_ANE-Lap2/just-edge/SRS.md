# PROJECT: Edge Sensor — ANE Spectrum Monitoring System

## System Requirements Specification (SRS)

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
| **Document ID**        | `SRS-ANE-EDGE-001`                                        |
| **Project**            | Edge Sensor — Spectrum Monitoring Subsystem (Phase 2)      |
| **Organization**       | National Spectrum Agency (ANE) — Colombia                  |
| **Version**            | 1.0.0                                                     |
| **Classification**     | `INTERNAL`                                                |
| **Author(s)**          | _To be defined_                                           |
| **Reviewer(s)**        | _To be defined_                                           |
| **Approver(s)**        | _To be defined_                                           |

### Companion Documents

| Document ID            | Title                                                   | Relationship              |
|------------------------|---------------------------------------------------------|---------------------------|
| `HCS-ANE-EDGE-001`    | Edge Sensor Hardware Constraints Specification          | Design constraints envelope |
| `SRS-ANE-001`         | Full-System SRS (Phase 2)                               | Parent system requirements |

> **Note:** The companion HCS-ANE-EDGE-001 documents the parametric limits of the HackRF One + Raspberry Pi 4B platform. This SRS was written with those limits already incorporated — every requirement is feasible within the hardware envelope.

### Change Log

| Version | Date       | Author                 | Change Description                          |
|---------|------------|------------------------|---------------------------------------------|
| 0.1.0   | 2026-10-13 | AI-assisted generation | Initial extraction from SRS-ANE-001         |
| 1.0.0   | 2026-10-13 | AI-assisted generation | Approved — IEEE 29148 v3 structure          |

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
| `REF-HCS`  | HCS-ANE-EDGE-001 — Companion HW Constraints Specification             | 1.0.0 / 2026-10-13  |

### 1.5 Document Overview

Section 3 contains specific requirements organized by subsystem. Section 4 covers external interfaces. Section 5 covers non-functional requirements. Section 6 presents the traceability matrix.

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
| **Standard(s)**        | —                                                        |
| **Dependencies**       | —                                                        |
| **Phase**              | 2025–2026                                                |

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

**`ANAL-RNG-001` — Frequency-range coverage**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `DEMONSTRATION`                                          |
| **Standard(s)**        | ITU-R SM.1537; `REF-001`                                 |
| **Dependencies**       | —                                                        |
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL capture emissions from 1 MHz up to 6 GHz.

**Acceptance Criteria:**

1. [ ] The system receives and processes signals in the 1 MHz – 6 GHz range.
2. [ ] Sensitivity at 1 MHz and 6 GHz is verifiable with a calibrated signal generator.

**Notes:**  
Sensitivity degrades at band edges (below 10 MHz and above 4 GHz). Characterization per band is required.

---

**`ANAL-RNG-002` — Real-time monitoring bandwidth**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `TEST`                                                   |
| **Standard(s)**        | —                                                        |
| **Dependencies**       | —                                                        |
| **Phase**              | 2025–2026                                                |

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

**`ANAL-PAR-001` — Parameterizable frequency range**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `DEMONSTRATION`                                          |
| **Standard(s)**        | —                                                        |
| **Dependencies**       | `ANAL-RNG-001`                                           |
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL allow the user to define frequency ranges within the 1 MHz – 6 GHz envelope (center+span or start+stop).

**Acceptance Criteria:**

1. [ ] Center frequency + span, or start + stop frequency, are configurable.
2. [ ] The system validates that the requested range is within hardware limits.
3. [ ] Range changes are applied in real time without restart.

---

**`ANAL-PAR-002` — RBW configuration**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `TEST`                                                   |
| **Standard(s)**        | —                                                        |
| **Dependencies**       | `ANAL-PAR-001`                                           |
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL allow the resolution bandwidth (RBW) to be configured over a defined range (≥ 6 discrete values).

**Acceptance Criteria:**

1. [ ] RBW is user-configurable across ≥ 6 discrete values.
2. [ ] Changing RBW updates the DSP pipeline in real time.

---

**`ANAL-PAR-003` — Frequency-resolution steps**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `TEST`                                                   |
| **Standard(s)**        | —                                                        |
| **Dependencies**       | `ANAL-PAR-002`                                           |
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL offer resolution steps of 500 Hz, with a minimum resolution of 10 Hz.

**Acceptance Criteria:**

1. [ ] Frequency step is configurable in 500 Hz increments.
2. [ ] Minimum achievable resolution is 10 Hz.
3. [ ] Step accuracy is verified against a signal generator.

**Notes:**  
10 Hz resolution at 20 MS/s requires a 2,000,000-point FFT — computationally intensive. May require reduced sample rates for the finest resolutions.

---

**`ANAL-PAR-004` — VBW configuration**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `TEST`                                                   |
| **Standard(s)**        | —                                                        |
| **Dependencies**       | `ANAL-PAR-002`                                           |
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL implement Video Bandwidth (VBW) filters suited to fine or averaged analysis.

**Acceptance Criteria:**

1. [ ] VBW is configurable independently of RBW.
2. [ ] Filters for fine and averaged analysis are available.
3. [ ] DSP output shows a perceptible difference between modes.

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
| **Standard(s)**        | —                                                        |
| **Dependencies**       | —                                                        |
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL allow the sensor's location coordinates to be entered manually when automatic GPS is unavailable.

**Acceptance Criteria:**

1. [ ] Latitude and longitude can be entered manually.
2. [ ] Manual coordinates are associated with measurements.
3. [ ] The system records whether the location source is GPS or manual.

---

**`ANAL-PAR-006` — Measurement unit conversion**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `DEMONSTRATION`                                          |
| **Standard(s)**        | —                                                        |
| **Dependencies**       | —                                                        |
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL allow selection and conversion of measurement units: frequency (Hz, kHz, MHz, GHz), power (dBm, dBmV, dBµV, V, W), and field/power density (V/m, W/m², dBµV/m).

**Acceptance Criteria:**

1. [ ] All listed units are available as output options.
2. [ ] Conversion error < 0.01 dB.

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
| **Standard(s)**        | —                                                        |
| **Dependencies**       | —                                                        |
| **Phase**              | 2025–2026                                                |

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

**`ANAL-MED-001` — Spectral traces**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `DEMONSTRATION`                                          |
| **Standard(s)**        | ITU-R SM.1537; `REF-001`                                 |
| **Dependencies**       | `ANAL-PAR-001`                                           |
| **Phase**              | 2025–2026                                                |

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

**`ANAL-MED-003` — Occupied-bandwidth measurement**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `TEST`                                                   |
| **Standard(s)**        | ITU-R SM.1537; `REF-001`                                 |
| **Dependencies**       | `ANAL-MED-001`                                           |
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL measure the occupied bandwidth (OBW) using the –X dB and 99% methods.

**Acceptance Criteria:**

1. [ ] –X dB method: bandwidth where the signal falls X dB below peak.
2. [ ] 99% method: bandwidth containing 99% of total signal power.
3. [ ] Results expressed in the selected frequency unit.

**Notes:**  
OBW measurement limited to signals within the 20 MHz instantaneous BW. Wider signals require sweep mode.

---

**`ANAL-MED-004` — Channel power measurement**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `TEST`                                                   |
| **Standard(s)**        | —                                                        |
| **Dependencies**       | `ANAL-RNG-002`                                           |
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL perform channel-power measurements for emissions up to 20 MHz wide.

**Acceptance Criteria:**

1. [ ] Channel-power measurement is selectable via configuration.
2. [ ] Channel width configurable up to 20 MHz.
3. [ ] Result expressed in selected power units.

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
| **Standard(s)**        | —                                                        |
| **Dependencies**       | —                                                        |
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL decode and extract RDS information from FM signals (PI, PS, RT fields).

**Acceptance Criteria:**

1. [ ] Basic RDS fields (PI, PS, RT) are decoded.
2. [ ] RDS data is included in the output alongside FM measurements.

---

**`ANAL-MED-006` — FM and AM demodulation**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `DEMONSTRATION`                                          |
| **Standard(s)**        | —                                                        |
| **Dependencies**       | `ANAL-RNG-001`                                           |
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL demodulate FM and AM signals in real time, producing digital audio.

**Acceptance Criteria:**

1. [ ] FM audio demodulated with audible quality.
2. [ ] AM audio demodulated with audible quality (from 1 MHz).
3. [ ] Demodulated audio is stored locally or transmitted as a stream.

**Notes:**  
AM reception at 1 MHz is at the lower edge of the receiver's range. Sensitivity degradation below 10 MHz may affect AM quality.

---

**`ANAL-MED-007` — AM and FM modulation measurement**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `TEST`                                                   |
| **Standard(s)**        | —                                                        |
| **Dependencies**       | `ANAL-MED-006`                                           |
| **Phase**              | 2025–2026                                                |

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

**`NORM-VER-001` — Intermodulation detection**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `TEST`                                                   |
| **Standard(s)**        | —                                                        |
| **Dependencies**       | `ANAL-MED-001`                                           |
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL detect intermodulation products in AM, FM, and the aeronautical band (108–137 MHz), and perform IF verification.

**Acceptance Criteria:**

1. [ ] 2nd- and 3rd-order intermodulation products are computed for detected emissions.
2. [ ] Suspected IM products are flagged in the spectral output.
3. [ ] IF verification is performed automatically.

**Notes:**  
The detection algorithm must distinguish receiver-generated IM from real over-the-air products, since the HackRF has no pre-selection filters.

---

**`NORM-VER-002` — Interference detection**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `TEST`                                                   |
| **Standard(s)**        | —                                                        |
| **Dependencies**       | `ANAL-PAR-007`                                           |
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL detect interference (signals exceeding the channel average by > 3 dB) and generate a local record.

**Acceptance Criteria:**

1. [ ] Signals > 3 dB above the average are detected as potential interference.
2. [ ] A local record is generated with frequency, power, and duration.
3. [ ] Detection runs continuously without manual intervention.

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
| **Standard(s)**        | —                                                        |
| **Dependencies**       | `ANAL-MED-006`                                           |
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL demodulate and store FM/AM audio locally for forensic analysis.

**Acceptance Criteria:**

1. [ ] Audio stored in a standard format (WAV or MP3).
2. [ ] Audio files associated with measurement metadata (frequency, timestamp, location).

---

### 3.5 Local Storage

---

**`FORN-ALM-001` — Local historical storage**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `DEMONSTRATION`                                          |
| **Standard(s)**        | ITU-R SM.1537; `REF-001`                                 |
| **Dependencies**       | —                                                        |
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL provide local historical storage for forensic analysis, including spectral data with timestamp and GPS location.

**Acceptance Criteria:**

1. [ ] Monitoring data stored locally with timestamp and GPS coordinates.
2. [ ] Historical data queryable by date range, frequency, and location.
3. [ ] Data integrity verifiable (checksum or hash).

---

**`FORN-ALM-003` — Raw IQ storage**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `DEMONSTRATION`                                          |
| **Standard(s)**        | —                                                        |
| **Dependencies**       | —                                                        |
| **Phase**              | 2025–2026                                                |

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

**`CONN-RED-001` — 4G/5G module**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `DEMONSTRATION`                                          |
| **Standard(s)**        | —                                                        |
| **Dependencies**       | —                                                        |
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL support a 4G/5G mobile-connectivity module with a data SIM card, with multi-carrier service.

**Acceptance Criteria:**

1. [ ] Supports 4G and 5G networks.
2. [ ] Works with SIM cards from ≥ 2 Colombian carriers.
3. [ ] Connection established automatically at power-on.

---

**`CONN-RED-002` — WiFi connection**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `SHOULD`                                                  |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `DEMONSTRATION`                                          |
| **Standard(s)**        | —                                                        |
| **Dependencies**       | —                                                        |
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL enable WiFi connectivity, configurable via Ethernet cable.

**Acceptance Criteria:**

1. [ ] Sensor connects to configured WiFi networks.
2. [ ] WiFi configuration performed initially over Ethernet.

---

**`CONN-RED-003` — Accessible Ethernet port**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `INSPECTION`                                             |
| **Standard(s)**        | —                                                        |
| **Dependencies**       | —                                                        |
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL provide an externally accessible Ethernet port (≥ 100 Mbps) without requiring the enclosure to be opened.

**Acceptance Criteria:**

1. [ ] Ethernet port externally accessible without tools.
2. [ ] Port supports ≥ 100 Mbps.

---

**`CONN-RED-004` — Network auto-routing**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `TEST`                                                   |
| **Standard(s)**        | —                                                        |
| **Dependencies**       | `CONN-RED-001`, `CONN-RED-002`, `CONN-RED-003`           |
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL implement automatic network routing with failover/priority among 4G/5G, WiFi, and Ethernet.

**Acceptance Criteria:**

1. [ ] System selects the available channel with highest priority.
2. [ ] Failover occurs without manual intervention.
3. [ ] Priority order is configurable.

---

#### 3.6.2 Support and GPS

---

**`CONN-SOP-001` — Remote access and OTA update**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `DEMONSTRATION`                                          |
| **Standard(s)**        | —                                                        |
| **Dependencies**       | `CONN-RED-004`                                           |
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL allow remote IP access (SSH or equivalent) and OTA software updates with automatic rollback on failure.

**Acceptance Criteria:**

1. [ ] Remote access via SSH or secure equivalent.
2. [ ] Software updates without physical access.
3. [ ] Automatic rollback on update failure.

---

**`CONN-GPS-001` — GPS location redundancy**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `TEST`                                                   |
| **Standard(s)**        | —                                                        |
| **Dependencies**       | `ANAL-PAR-005`                                           |
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL continue reporting automatic GPS location even when manual coordinates are configured, storing both sources.

**Acceptance Criteria:**

1. [ ] GPS reports location regardless of manual parameterization.
2. [ ] Both location sources are stored in measurement records.

---

**`CONN-GPS-002` — GPS accuracy**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `NON_FUNCTIONAL`                                         |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `TEST`                                                   |
| **Standard(s)**        | —                                                        |
| **Dependencies**       | —                                                        |
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL achieve a horizontal GPS accuracy ≤ 3 m (CEP 50%) under open sky.

**Acceptance Criteria:**

1. [ ] Horizontal accuracy ≤ 3 m (CEP 50%) under open-sky conditions.
2. [ ] Accuracy verified against a reference GPS receiver.

---

### 3.7 Antennas and Radiation Measurement

#### 3.7.1 Antennas

---

**`ANTE-ANT-001` — Band-specific antennas**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `INSPECTION`                                             |
| **Standard(s)**        | —                                                        |
| **Dependencies**       | `ANAL-RNG-001`                                           |
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL incorporate specific antennas optimized for DTT and mobile-telephony downlink (> 2 GHz), each with a documented antenna factor (AF).

**Acceptance Criteria:**

1. [ ] DTT-specific antenna provided.
2. [ ] Antenna for frequencies > 2 GHz verified.
3. [ ] Each antenna has a documented and calibrated AF.

---

**`ANTE-ANT-002` — Active antenna for non-ionizing radiation**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `TEST`                                                   |
| **Standard(s)**        | ITU-T K.113, K.100; `REF-003`, `REF-004`                 |
| **Dependencies**       | —                                                        |
| **Phase**              | 2025–2026                                                |

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

**`ANTE-RNI-001` — Radiation measurement units**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `DEMONSTRATION`                                          |
| **Standard(s)**        | ITU-T K.113, K.100; `REF-003`, `REF-004`                 |
| **Dependencies**       | `ANTE-ANT-002`                                           |
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL support measurement units for non-ionizing radiation: S (W/m²), A/m, V/m, dBµV/m, dBA/m.

**Acceptance Criteria:**

1. [ ] All listed units available as display options.
2. [ ] Conversions between units are correct.

---

**`ANTE-RNI-002` — Field-strength measurement**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `TEST`                                                   |
| **Standard(s)**        | ITU-T K.113, K.100; `REF-003`, `REF-004`                 |
| **Dependencies**       | `ANTE-ANT-002`, `ANTE-RNI-001`                           |
| **Phase**              | 2025–2026                                                |

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

**`POWR-AUT-001` — Autonomous power**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `DEMONSTRATION`                                          |
| **Standard(s)**        | —                                                        |
| **Dependencies**       | —                                                        |
| **Phase**              | 2025–2026                                                |

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

**`GEST-MON-001` — Sensor health monitoring**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `DEMONSTRATION`                                          |
| **Standard(s)**        | —                                                        |
| **Dependencies**       | —                                                        |
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL monitor and record sensor health: disk usage, RAM, CPU, and temperature.

**Acceptance Criteria:**

1. [ ] Disk, RAM, CPU, and temperature are monitored.
2. [ ] Local alerts generated when thresholds are exceeded.
3. [ ] Health data stored locally with timestamp.

**Notes:**  
RPi throttles above 80 °C. Alert thresholds should warn before throttle onset.

---

**`GEST-MON-002` — Network and connectivity monitoring**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `TEST`                                                   |
| **Standard(s)**        | —                                                        |
| **Dependencies**       | —                                                        |
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL measure and record IP-connection quality: RTT, channel status, available bandwidth, and packet loss.

**Acceptance Criteria:**

1. [ ] RTT measured periodically (configurable interval).
2. [ ] Alive/Not Alive status detected per interface.
3. [ ] Local record generated when RTT or packet loss exceeds thresholds.

---

**`GEST-PRG-001` — Scheduled spectrum scan**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `DEMONSTRATION`                                          |
| **Standard(s)**        | ITU-R SM.1537; `REF-001`                                 |
| **Dependencies**       | `ANAL-PAR-001`                                           |
| **Phase**              | 2025–2026                                                |

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

**`CONF-SIN-001` — NTP synchronization**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `NON_FUNCTIONAL`                                         |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `TEST`                                                   |
| **Standard(s)**        | —                                                        |
| **Dependencies**       | `CONN-RED-004`                                           |
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL synchronize to an NTP server with a time offset ≤ 100 ms.

**Acceptance Criteria:**

1. [ ] Synchronizes with NTP when network is available.
2. [ ] Time offset ≤ 100 ms.
3. [ ] Synchronization status queryable locally.

---

**`CONF-CAL-001` — Calibration procedures**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `NON_FUNCTIONAL`                                         |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `ANALYSIS`                                               |
| **Standard(s)**        | —                                                        |
| **Dependencies**       | —                                                        |
| **Phase**              | 2025–2026                                                |

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

**`CONF-CAR-001` — DANL**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `NON_FUNCTIONAL`                                         |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `TEST`                                                   |
| **Standard(s)**        | ITU-R SM.1138; `REF-002`                                 |
| **Dependencies**       | —                                                        |
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL achieve a DANL ≤ –100 dBm across the operating range.

**Acceptance Criteria:**

1. [ ] Measured DANL ≤ –100 dBm over ≥ 90% of the frequency range.
2. [ ] Measurement performed with 50 Ω load and documented per band.

**Notes:**  
Software averaging improves effective DANL at the cost of temporal resolution.

---

**`CONF-CAR-002` — Dynamic range**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `NON_FUNCTIONAL`                                         |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `TEST`                                                   |
| **Standard(s)**        | ITU-R SM.1138; `REF-002`                                 |
| **Dependencies**       | `CONF-CAR-001`                                           |
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL achieve a dynamic range ≥ 80 dB.

**Acceptance Criteria:**

1. [ ] Measured dynamic range ≥ 80 dB in a two-tone test.
2. [ ] Test setup and results documented.

**Notes:**  
The 8-bit ADC provides ~48 dB single-capture SFDR. The ≥ 80 dB target is achieved via gain-stepped captures at multiple LNA/VGA settings + spectral averaging.

---

**`CONF-CAR-003` — Frequency accuracy**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `NON_FUNCTIONAL`                                         |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `TEST`                                                   |
| **Standard(s)**        | —                                                        |
| **Dependencies**       | —                                                        |
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL achieve a frequency accuracy of ± 2 ppm.

**Acceptance Criteria:**

1. [ ] Measured frequency error ≤ ± 2 ppm against a calibrated reference.
2. [ ] Measurement at room temperature (20–25 °C).

**Notes:**  
The stock oscillator is ± 20 ppm. A TCXO replacement (± 0.5–2 ppm) or GPS-disciplined correction is used.

---

**`CONF-CAR-004` — Oscillator aging**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `NON_FUNCTIONAL`                                         |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `ANALYSIS`                                               |
| **Standard(s)**        | —                                                        |
| **Dependencies**       | `CONF-CAR-003`                                           |
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL meet a frequency drift due to oscillator aging ≤ 1 ppm/year.

**Acceptance Criteria:**

1. [ ] Selected oscillator has aging spec ≤ 1 ppm/year.
2. [ ] Oscillator type and aging spec documented.

---

**`CONF-CAR-005` — Amplitude accuracy**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `NON_FUNCTIONAL`                                         |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `TEST`                                                   |
| **Standard(s)**        | —                                                        |
| **Dependencies**       | —                                                        |
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL achieve a typical amplitude accuracy of ± 1 dB.

**Acceptance Criteria:**

1. [ ] Amplitude error ≤ ± 1 dB over ≥ 90% of the frequency range.
2. [ ] Amplitude linearity verified in 10 dB steps.

**Notes:**  
Requires per-frequency, per-gain-setting calibration tables built using external reference sources.

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
| `ANAL-EMC-001`   | RF architecture        | —                   | _TC-001_    |
| `ANAL-RNG-001`   | Spectral range         | ITU-R SM.1537       | _TC-002_    |
| `ANAL-RNG-002`   | Bandwidth              | —                   | _TC-003_    |
| `ANAL-PAR-001`   | DSP parameterization   | —                   | _TC-004_    |
| `ANAL-PAR-002`   | DSP parameterization   | —                   | _TC-005_    |
| `ANAL-PAR-003`   | DSP parameterization   | —                   | _TC-006_    |
| `ANAL-PAR-004`   | DSP parameterization   | —                   | _TC-007_    |
| `ANAL-PAR-005`   | GPS                    | —                   | _TC-008_    |
| `ANAL-PAR-006`   | Units                  | —                   | _TC-009_    |
| `ANAL-PAR-007`   | Detection              | —                   | _TC-010_    |
| `ANAL-MED-001`   | DSP / traces           | ITU-R SM.1537       | _TC-011_    |
| `ANAL-MED-003`   | DSP / OBW              | ITU-R SM.1537       | _TC-012_    |
| `ANAL-MED-004`   | DSP / channel power    | —                   | _TC-013_    |
| `ANAL-MED-005`   | DSP / RDS              | —                   | _TC-014_    |
| `ANAL-MED-006`   | DSP / demodulation     | —                   | _TC-015_    |
| `ANAL-MED-007`   | DSP / modulation       | —                   | _TC-016_    |
| `NORM-VER-001`   | Local detection        | —                   | _TC-017_    |
| `NORM-VER-002`   | Local detection        | —                   | _TC-018_    |
| `NORM-SRV-002`   | Forensic audio         | —                   | _TC-019_    |
| `FORN-ALM-001`   | Local storage          | ITU-R SM.1537       | _TC-020_    |
| `FORN-ALM-003`   | Local storage          | —                   | _TC-021_    |
| `CONN-RED-001`   | Connectivity           | —                   | _TC-022_    |
| `CONN-RED-002`   | Connectivity           | —                   | _TC-023_    |
| `CONN-RED-003`   | Connectivity           | —                   | _TC-024_    |
| `CONN-RED-004`   | Connectivity           | —                   | _TC-025_    |
| `CONN-SOP-001`   | Maintenance            | —                   | _TC-026_    |
| `CONN-GPS-001`   | GPS                    | —                   | _TC-027_    |
| `CONN-GPS-002`   | GPS                    | —                   | _TC-028_    |
| `ANTE-ANT-001`   | Antennas               | —                   | _TC-029_    |
| `ANTE-ANT-002`   | Antennas               | ITU-T K.113, K.100  | _TC-030_    |
| `ANTE-RNI-001`   | Non-ionizing radiation | ITU-T K.113, K.100  | _TC-031_    |
| `ANTE-RNI-002`   | Non-ionizing radiation | ITU-T K.113, K.100  | _TC-032_    |
| `POWR-AUT-001`   | Power                  | —                   | _TC-033_    |
| `GEST-MON-001`   | Health monitoring      | —                   | _TC-034_    |
| `GEST-MON-002`   | Health monitoring      | —                   | _TC-035_    |
| `GEST-PRG-001`   | Local scheduler        | ITU-R SM.1537       | _TC-036_    |
| `CONF-SIN-001`   | Synchronization        | —                   | _TC-037_    |
| `CONF-CAL-001`   | Calibration            | —                   | _TC-038_    |
| `CONF-CAR-001`   | Characterization       | ITU-R SM.1138       | _TC-039_    |
| `CONF-CAR-002`   | Characterization       | ITU-R SM.1138       | _TC-040_    |
| `CONF-CAR-003`   | Characterization       | —                   | _TC-041_    |
| `CONF-CAR-004`   | Characterization       | —                   | _TC-042_    |
| `CONF-CAR-005`   | Characterization       | —                   | _TC-043_    |

# PROJECT: Spectrum Monitoring System — Phase 2 Optimization

## System Requirements Specification (SRS)

> **Template based on:** IEEE/ISO/IEC 29148:2018 — *Systems and software engineering — Life cycle processes — Requirements engineering*, adapted with elements of ETSI EN 303 645 (Cyber Security for IoT) and a deterministic structure for automated AI-based validation.
>
> **Template version:** 1.0.0  
> **Creation date:** 2026-10-13  
> **Last modified:** 2026-10-13  
> **Document status:** `IN_REVIEW`

---

## Document Metadata

| Field                  | Value                                                      |
|------------------------|------------------------------------------------------------|
| **Document ID**        | `SRS-ANE-001`                                             |
| **Project**            | Phase 2 Roadmap — Spectrum Monitoring System Optimization  |
| **Organization**       | National Spectrum Agency (ANE) — Colombia                  |
| **Version**            | 0.1.0                                                     |
| **Classification**     | `INTERNAL`                                                |
| **Author(s)**          | _To be defined_                                           |
| **Reviewer(s)**        | _To be defined_                                           |
| **Approver(s)**        | _To be defined_                                           |

### Change Log

| Version | Date       | Author             | Change Description                                      |
|---------|------------|--------------------|---------------------------------------------------------|
| 0.1.0   | 2026-10-13 | AI-assisted generation | Extraction of approved (green) requirements from the Excel roadmap |

---

## 1. Introduction

### 1.1 Purpose

This document specifies the approved requirements for Phase 2 of the optimization of the ANE Spectrum Monitoring System. It includes only the requirements that were marked as approved (green) in the feature roadmap, excluding items under discussion, deferred, or discarded.

### 1.2 System Scope

The system is a radio-spectrum monitoring platform made up of remote SDR-based sensors (HackRF One on Raspberry Pi), a cloud management and visualization layer, and tools for spectral analysis, regulatory compliance, and artificial intelligence. Phase 2 optimizes the existing system (Phase 1) by extending its analysis, connectivity, reliability, and international-standards-compliance capabilities.

**In this phase, the system does NOT include:** emitter localization (DF/TDOA), measurement of exogenous variables (humidity/temperature), Doppler compensation, advanced IQ capture, GIS/ArcGIS integration, or fault detection for specific technologies (LTE, 5G, DAB).

### 1.3 Definitions, Acronyms, and Abbreviations

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
| TDOA       | Time Difference of Arrival                                                           |
| DF         | Direction Finding                                                                   |
| OBW        | Occupied Bandwidth                                                                   |
| RTT        | Round Trip Time — round-trip time of an IP packet                                   |
| ITU-R      | International Telecommunication Union — Radiocommunication Sector                    |
| CEPT       | European Conference of Postal and Telecommunications Administrations                 |
| SRS        | System Requirements Specification                                                    |
| HIL        | Hardware In the Loop                                                                 |
| HITL       | Human In the Loop                                                                    |
| ppm        | Parts per million                                                                    |
| SAW        | Surface Acoustic Wave (filter type)                                                 |
| AP         | Access Point                                                                         |
| TLS/SSL    | Transport Layer Security / Secure Sockets Layer                                      |

### 1.4 References

| Ref ID     | Document                                                               | Version / Date      |
|------------|------------------------------------------------------------------------|---------------------|
| `REF-001`  | ITU-R SM.1537 — Automation and requirements of monitoring stations     | In force            |
| `REF-002`  | ITU-R SM.1138 — Monitoring sensitivity and selectivity                 | In force            |
| `REF-003`  | ITU-T K.113 — Electric field measurement in urban environments         | In force            |
| `REF-004`  | ITU-T K.100 — Assessment of human exposure to electromagnetic fields   | In force            |
| `REF-005`  | CEPT/ERC/REC 70-03 — Shared use of licence-exempt spectrum             | In force            |
| `REF-006`  | ECC Report 260 — Protection for SRD services                           | In force            |
| `REF-007`  | IEEE/ISO/IEC 29148:2018 — Requirements engineering                     | 2018                |
| `REF-008`  | ETSI EN 303 645 — Cyber Security for Consumer IoT                      | V2.1.1 (2020-06)    |

### 1.5 Document Overview

Section 3 contains all the specific approved requirements, organized by the system's functional category. Section 4 details the external interfaces. Section 5 groups the cross-cutting non-functional requirements. Section 6 presents the traceability matrix. Section 7 defines the structural validation rules for automated processing.

---

## 2. Overall System Description

### 2.1 Product Perspective

This system is an evolution (Phase 2) of the ANE's existing spectrum-monitoring platform. It extends the capabilities of the on-site sensors based on HackRF One + Raspberry Pi, adds a cloud component for centralized management, and broadens the spectral-analysis range, the connectivity, and the compliance with international ITU standards.

#### 2.1.1 Context Diagram

```
┌─────────────┐      4G/5G/WiFi/ETH      ┌──────────────────┐
│  SDR Sensor  │◄────────────────────────►│   Cloud Backend   │
│  (HackRF +   │    Spectrum data,        │  (FastAPI/Node +  │
│   RPi)       │    telemetry, GPS        │   Docker)         │
└──────┬───────┘                          └────────┬──────────┘
       │                                           │
  ┌────┴────┐                                ┌─────┴──────┐
  │ Antennas │                                │  Frontend   │
  │ GPS      │                                │  (React/Vue │
  │ Battery  │                                │   + WebGL)  │
  │ 4G/WiFi  │                                └─────┬──────┘
  └─────────┘                                       │
                                               ┌────┴─────┐
                                               │ ANE       │
                                               │ Operator  │
                                               └──────────┘
```

### 2.2 Product Functions

The system provides: real-time spectrum monitoring (1 MHz–6 GHz), detection of unauthorized emissions, signal-parameter measurement (power, bandwidth, modulation), FM/AM demodulation, automated regulatory compliance, remote sensor management, forensic storage, and report generation.

### 2.3 User Characteristics

| User Type             | Description                                    | Technical Level |
|-----------------------|------------------------------------------------|-----------------|
| Spectrum engineer     | Configures and analyzes spectral measurements   | `EXPERT`        |
| Monitoring operator   | Oversees alerts and sensor status               | `TECHNICAL`     |
| IT administrator      | Manages cloud infrastructure and connectivity   | `TECHNICAL`     |
| ANE executive         | Consults reports and indicators                 | `BASIC`         |

### 2.4 Constraints

- Base hardware: HackRF One as the primary SDR (inherent DANL and dynamic-range limitations).
- Embedded platform: Raspberry Pi (low power, processing limitations).
- Connectivity: dependent on the 4G/5G coverage of Colombian carriers.
- Regulatory: mandatory compliance with ITU-R SM-series recommendations.

### 2.5 Assumptions and Dependencies

- The ANE provides data SIM cards for mobile connectivity.
- Sensors are deployed at sites with mains power or where a solar solution is viable.
- The cloud backend has Docker infrastructure with a defined growth plan.
- The ANE's authorized-emission databases are available for integration.

---

## 3. Specific Requirements

---

### 3.1 Spectral Analysis — Architecture and Security

#### 3.1.1 Information Security

---

**`ANAL-SEG-001` — TLS/SSL-encrypted communications**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `NON_FUNCTIONAL`                                         |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `TEST`                                                   |
| **New hardware**       | No                                                       |
| **Standard(s)**        | ETSI EN 303 645 §5.1; `REF-008`                         |
| **Dependencies**       | —                                                        |
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL use TLS/SSL protocols with a valid certificate on all communications between sensors and the backend, and between the backend and the frontend. It SHALL NOT transmit data in plain text.

**Acceptance Criteria:**

1. [ ] All HTTP connections use HTTPS with TLS ≥ 1.2.
2. [ ] Certificates are issued by a recognized CA or by the ANE's internal PKI.
3. [ ] An interception (MITM) test reveals no cleartext data.

**Notes:**  
A valid certificate is required. No exceptions for development environments in production.

---

#### 3.1.2 Electromagnetic Compatibility

---

**`ANAL-EMC-001` — Sensor EMC optimization**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `NON_FUNCTIONAL`                                         |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `TEST`                                                   |
| **New hardware**       | Yes (RF gasket)                                         |
| **Standard(s)**        | —                                                        |
| **Dependencies**       | —                                                        |
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL incorporate adjustments and filtering in the sensor's receive path to prevent spurious signals generated by its own electronics from appearing in the measurement results. The EMC adjustments SHALL be feasible on the current platform.

**Acceptance Criteria:**

1. [ ] The sensor's internal spurious emissions are at least 10 dB below the operating noise floor.
2. [ ] RF shielding (a gasket) is implemented between internal modules.
3. [ ] A before/after comparative measurement demonstrates a reduction in EMC artifacts.

**Notes:**  
Includes the implementation of an RF gasket. Analysis owner: Bernardo.

---

#### 3.1.3 Spectral Range

---

**`ANAL-RNG-001` — Frequency-range extension**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `DEMONSTRATION`                                          |
| **New hardware**       | No (the HackRF One supports the range)                  |
| **Standard(s)**        | ITU-R SM.1537; `REF-001`                                 |
| **Dependencies**       | —                                                        |
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL extend the sensor's frequency range to capture emissions from 1 MHz up to 6 GHz (or up to the limit of the SDR hardware).

**Acceptance Criteria:**

1. [ ] The system receives and processes signals in the 1 MHz – 6 GHz range.
2. [ ] Sensitivity at 1 MHz is verifiable with a calibrated signal generator.
3. [ ] Sensitivity at 6 GHz is verifiable with a calibrated signal generator.

**Notes:**  
The upper limit may depend on the model of the connected antenna. A specific antenna is required for the low bands (AM from 1 MHz).

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
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL provide real-time monitoring with a minimum bandwidth of 20 MHz. It SHALL allow the bandwidth to be configured manually between 6 MHz and 20 MHz, and an automatic mode fixed at 20 MHz.

**Acceptance Criteria:**

1. [ ] The monitoring span can be configured between 6 MHz and 20 MHz in discrete steps.
2. [ ] In automatic mode, the span is fixed at 20 MHz.
3. [ ] The real-time visualization updates with a latency ≤ 1 second.

**Notes:**  
Manual between 6 and 20 MHz; automatic at 20 MHz.

---

### 3.2 Spectral Analysis — Parameterization

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
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL allow the user to enter frequency ranges to analyze within the available spectral range (IF span).

**Acceptance Criteria:**

1. [ ] The user can define a center frequency and span, or a start and stop frequency.
2. [ ] The system validates that the requested range is within the hardware limits.
3. [ ] Range changes are applied in real time without restarting the system.

**Notes:**  
IF span = the frequency range on screen.

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
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL allow the resolution bandwidth (RBW) to be configured over a defined range (IF span = RBW).

**Acceptance Criteria:**

1. [ ] The RBW is user-configurable across a set of discrete values.
2. [ ] The available RBW ranges are documented (≥ 6 values).
3. [ ] Changing the RBW updates the visualization in real time.

**Notes:**  
Define ≥ 6 RBW options.

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
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL offer resolution-change steps of 500 Hz, with a minimum resolution of 10 Hz.

**Acceptance Criteria:**

1. [ ] The frequency step is configurable in 500 Hz increments.
2. [ ] The minimum achievable resolution is 10 Hz.
3. [ ] The step accuracy is verified against a signal generator.

**Notes:**  
Expand the range of resolutions in later phases as demand requires.

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
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL implement Video Bandwidth (VBW) filters suited to the type of analysis (fine or average) in order to smooth the displayed signal after the RBW processing.

**Acceptance Criteria:**

1. [ ] The VBW is configurable independently of the RBW.
2. [ ] Filters are available for fine and averaged analysis.
3. [ ] The visualization shows a perceptible difference between filtering modes.

**Notes:**  
Filtering applied after RBW to smooth the displayed signal.

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
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL allow the sensor's location coordinates to be entered manually when automatic GPS is unavailable or a correction is required.

**Acceptance Criteria:**

1. [ ] The user can enter latitude and longitude manually.
2. [ ] Manual coordinates are associated with the measurements taken.
3. [ ] The system visually indicates whether the location is automatic GPS or manual.

**Notes:**  
—

---

**`ANAL-PAR-006` — Parameterization of measurement units**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `DEMONSTRATION`                                          |
| **New hardware**       | No                                                       |
| **Standard(s)**        | —                                                        |
| **Dependencies**       | —                                                        |
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL allow the selection and conversion of measurement units: frequency (Hz, kHz, MHz, GHz), power (dBm, dBmV, dBµV, V, W), and electric field and power density (V/m, W/m², dBµV/m).

**Acceptance Criteria:**

1. [ ] All listed units are available in the configuration interface.
2. [ ] Conversion between units is mathematically correct (error < 0.01 dB).
3. [ ] A change of unit updates all visualizations simultaneously.

**Notes:**  
—

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
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL allow detection thresholds to be parameterized and SHALL integrate algorithms capable of distinguishing the noise floor from signal occupancy, in order to define the portion of the spectrum of interest.

**Acceptance Criteria:**

1. [ ] The user can define a power threshold in dBm for signal detection.
2. [ ] The algorithm automatically distinguishes the noise floor from active signals.
3. [ ] Signals above the threshold are visually highlighted in the interface.

**Notes:**  
Parameterize the threshold and, based on it, define the portion of the spectrum of interest.

---

### 3.3 Spectral Analysis — Measurement and Visualization

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
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL present spectral traces: maximum (max hold), minimum (min hold), average, and RMS, peak, and average detection modes.

**Acceptance Criteria:**

1. [ ] The maximum trace retains the highest value per frequency bin.
2. [ ] The minimum trace retains the lowest value per frequency bin.
3. [ ] The average trace computes the arithmetic mean over N sweeps (N configurable).
4. [ ] The RMS, peak, and average detection modes are selectable.

**Notes:**  
—

---

**`ANAL-MED-002` — Spectral markers**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `DEMONSTRATION`                                          |
| **New hardware**       | No                                                       |
| **Standard(s)**        | —                                                        |
| **Dependencies**       | `ANAL-MED-001`                                           |
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL add individual and delta-type markers over the spectral measurement, with a minimum of four simultaneous markers.

**Acceptance Criteria:**

1. [ ] At least 4 markers can be placed simultaneously.
2. [ ] Each marker shows frequency and power.
3. [ ] Delta markers show ΔPower and ΔFrequency between two points.

**Notes:**  
Each marker shows: freq, power. Delta shows: ΔPower and ΔFreq.

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
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL measure the occupied bandwidth (OBW) using the –X dB and 99% methods.

**Acceptance Criteria:**

1. [ ] –X dB method: measures the width where the signal falls X dB below the peak (X configurable).
2. [ ] 99% method: measures the spectrum that contains 99% of the signal power.
3. [ ] Results are shown in the selected frequency unit.

**Notes:**  
OBW = the spectrum that contains 99% of the signal. –X dB is where the signal falls X below the peak.

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
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL perform channel-power measurements for emissions up to 20 MHz wide.

**Acceptance Criteria:**

1. [ ] Channel-power measurement is user-selectable.
2. [ ] The measured channel width is configurable up to 20 MHz.
3. [ ] The result is expressed in the selected power units.

**Notes:**  
Channel-power measurements limited to 20 MHz in this phase. More than 20 MHz in a later phase.

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
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL decode and present the Radio Data System (RDS) information in FM signals.

**Acceptance Criteria:**

1. [ ] The system decodes basic RDS fields (PI, PS, RT).
2. [ ] The RDS information is shown in the interface alongside the FM signal.

**Notes:**  
Requires the ANE to confirm the feature (ANE column: YES).

---

**`ANAL-MED-006` — FM and AM demodulation and listening**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `DEMONSTRATION`                                          |
| **New hardware**       | No                                                       |
| **Standard(s)**        | —                                                        |
| **Dependencies**       | `ANAL-RNG-001`                                           |
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL demodulate and allow listening to FM and AM signals in real time.

**Acceptance Criteria:**

1. [ ] FM audio is demodulated with audible quality.
2. [ ] AM audio is demodulated with audible quality (from 1 MHz with the HackRF One).
3. [ ] Listening is available both locally and remotely via streaming.

**Notes:**  
AM is only possible with the HackRF One from 1 MHz upward; it requires an additional antenna.

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
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL directly measure the AM modulation depth and the FM frequency deviation.

**Acceptance Criteria:**

1. [ ] The AM modulation depth is presented as a percentage.
2. [ ] The FM frequency deviation is presented in kHz.
3. [ ] The values update in real time during demodulation.

**Notes:**  
AM only from 1 MHz upward with the HackRF One; it requires an additional antenna.

---

### 3.4 Regulatory Compliance — Detection and Alerts

#### 3.4.1 Unauthorized Emissions

---

**`NORM-DET-001` — Detection of unauthorized emissions**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `TEST`                                                   |
| **New hardware**       | No                                                       |
| **Standard(s)**        | ITU-R SM.1537; `REF-001`                                 |
| **Dependencies**       | `ANAL-PAR-007`                                           |
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL automatically detect and alert on unauthorized emissions by comparing them against the agency's database.

**Acceptance Criteria:**

1. [ ] The system compares detected emissions against the ANE's authorized-emissions database.
2. [ ] It generates an automatic alert when it detects an unregistered emission.
3. [ ] The alert includes frequency, power, timestamp, and the sensor's location.

**Notes:**  
Requires integration with the ANE database.

---

**`NORM-DET-002` — Authorized-bandwidth non-compliance**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `TEST`                                                   |
| **New hardware**       | No                                                       |
| **Standard(s)**        | ITU-R SM.1537; `REF-001`                                 |
| **Dependencies**       | `NORM-DET-001`, `ANAL-MED-003`                           |
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL detect and alert when an authorized emission exceeds the bandwidth limits permitted according to the agency's database.

**Acceptance Criteria:**

1. [ ] The system measures the OBW of authorized emissions and compares it against the database limits.
2. [ ] It generates an alert when the measured bandwidth exceeds the authorized value.
3. [ ] The report includes the measured bandwidth vs. the authorized one.

**Notes:**  
Requires the ANE database with per-emission bandwidth limits.

---

**`NORM-DET-003` — Authorized-power non-compliance**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `TEST`                                                   |
| **New hardware**       | No                                                       |
| **Standard(s)**        | ITU-R SM.1537; `REF-001`                                 |
| **Dependencies**       | `NORM-DET-001`                                           |
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL detect and alert when an authorized emission exceeds the authorized/legal power limits.

**Acceptance Criteria:**

1. [ ] The system measures the power of authorized emissions and compares it against the database limits.
2. [ ] It generates an alert when the measured power exceeds the authorized value.
3. [ ] The tolerance margin of the comparison is configurable.

**Notes:**  
Requires the ANE database with per-emission power limits.

---

#### 3.4.2 Additional AM/FM/Aeronautical Services

---

**`NORM-SRV-001` — AM and FM modulation quantification (compliance)**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `TEST`                                                   |
| **New hardware**       | No                                                       |
| **Standard(s)**        | —                                                        |
| **Dependencies**       | `ANAL-MED-007`                                           |
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL quantify the AM modulation depth and the FM frequency deviation to verify regulatory compliance in broadcasting services.

**Acceptance Criteria:**

1. [ ] The measured values are compared against configurable regulatory limits.
2. [ ] The system generates an alert when the parameters exceed the limits.

**Notes:**  
AM only from 1 MHz with the HackRF One; it requires an additional antenna.

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
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL demodulate and extract audio from FM and AM signals for use in compliance verification and forensic analysis.

**Acceptance Criteria:**

1. [ ] The extracted audio can be stored in a standard format (WAV or MP3).
2. [ ] The audio file is associated with the measurement metadata (frequency, timestamp, location).

**Notes:**  
AM only from 1 MHz with the HackRF One; it requires an additional antenna.

---

#### 3.4.3 Signal-Parameter Verification

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
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL detect intermodulation, including the identification of suspected intermodulation products in AM, FM, and the aeronautical mobile service band (108 MHz–137 MHz), as well as intermediate-frequency (IF) verification.

**Acceptance Criteria:**

1. [ ] The system computes 2nd- and 3rd-order intermodulation products for detected emissions.
2. [ ] Suspected intermodulation products are flagged in the spectral visualization.
3. [ ] IF verification is performed automatically.

**Notes:**  
Covers AM, FM, and the aeronautical band (108–137 MHz). ANE confirms (YES).

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
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL detect interference, defined as signals that exceed the average level of the channel or band by more than 3 dB.

**Acceptance Criteria:**

1. [ ] Signals more than 3 dB above the average level are detected as potential interference.
2. [ ] An automatic alert is generated with frequency, power, and duration data.
3. [ ] Remote control allows real-time verification.

**Notes:**  
Detection threshold: > 3 dB above the average level. ANE confirms (YES).

---

### 3.5 Management Tools

#### 3.5.1 Infrastructure Monitoring

---

**`GEST-MON-001` — Monitoring of sensors and remote stations**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `DEMONSTRATION`                                          |
| **New hardware**       | No                                                       |
| **Standard(s)**        | —                                                        |
| **Dependencies**       | —                                                        |
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL measure and alert on sensor health variables (disk, RAM, CPU, temperature) using the variables available in the operating system.

**Acceptance Criteria:**

1. [ ] At least the following are monitored: disk usage, RAM, CPU, and temperature.
2. [ ] Alerts are generated when variables exceed configurable thresholds.
3. [ ] The status of each sensor is displayed on a centralized dashboard.

**Notes:**  
—

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
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL measure and alert on IP-connection quality, including RTT, channel status (Alive/Not Alive), available bandwidth, and packet loss.

**Acceptance Criteria:**

1. [ ] RTT is measured periodically (configurable interval).
2. [ ] The Alive/Not Alive status of each sensor is detected.
3. [ ] An alert is generated when RTT or packet loss exceeds thresholds.

**Notes:**  
—

---

#### 3.5.2 Scheduling and Reports

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
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL allow parameterized spectrum scans (frequency, RBW, VBW, duration) to be scheduled and reviewed afterward.

**Acceptance Criteria:**

1. [ ] The user can schedule scans with defined parameters (frequency, RBW, VBW, duration, repetition).
2. [ ] The results of scheduled scans are stored for later review.
3. [ ] Scans run at the scheduled time with a tolerance ≤ 1 minute.

**Notes:**  
ANE confirms (YES).

---

**`GEST-REP-001` — Automatic report generation**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `DEMONSTRATION`                                          |
| **New hardware**       | No                                                       |
| **Standard(s)**        | —                                                        |
| **Dependencies**       | `ANAL-MED-001`, `NORM-DET-001`                           |
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL automatically generate spectrum-management reports using the defined monitoring variables, in specific formats defined by the agency.

**Acceptance Criteria:**

1. [ ] At least one report format is implemented according to ANE specifications.
2. [ ] The reports include spectrum data, alerts, location, and timestamp.
3. [ ] The reports are generated on demand and/or automatically at configured times.

**Notes:**  
More report formats in subsequent phases.

---

### 3.6 Forensic Analysis and Storage

---

**`FORN-ALM-001` — Historical storage for forensic analysis**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `DEMONSTRATION`                                          |
| **New hardware**       | No                                                       |
| **Standard(s)**        | ITU-R SM.1537; `REF-001`                                 |
| **Dependencies**       | —                                                        |
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL provide local and centralized historical storage for forensic, enforcement, or historical analysis, including spectral data with a timestamp and location.

**Acceptance Criteria:**

1. [ ] Monitoring data is stored with a timestamp and GPS coordinates.
2. [ ] Historical data is queryable by date range, frequency, and location.
3. [ ] The integrity of the stored data is verifiable.

**Notes:**  
With current hardware. ANE confirms (YES).

---

**`FORN-ALM-002` — Storage on ANE servers**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `DEMONSTRATION`                                          |
| **New hardware**       | No                                                       |
| **Standard(s)**        | —                                                        |
| **Dependencies**       | `FORN-ALM-001`                                           |
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL store the results of scheduled monitoring on the ANE's on-premises (ground) servers, with the ability to retain JSON files and optionally CS8 files (raw IQ).

**Acceptance Criteria:**

1. [ ] The results are transmitted to and stored on the ANE servers.
2. [ ] The JSON format is documented and parseable.
3. [ ] The decision to store CS8 is configurable according to available resources.

**Notes:**  
The ANE decides, depending on resources, whether to store only JSON or also CS8 files.

---

**`FORN-ALM-003` — Storage on sensors**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `DEMONSTRATION`                                          |
| **New hardware**       | Yes                                                     |
| **Standard(s)**        | —                                                        |
| **Dependencies**       | —                                                        |
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL add storage space to the sensors so that CS8 files can be stored for later use as forensic evidence.

**Acceptance Criteria:**

1. [ ] The sensors have accessible additional storage.
2. [ ] CS8 files are stored with metadata (timestamp, frequency, coordinates).
3. [ ] Local storage is remotely accessible for download.

**Notes:**  
Include the cost of the storage solution to be used.

---

### 3.7 Connectivity and Remote Support

#### 3.7.1 Network Interfaces

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
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL add or replace the mobile-connectivity module to support a data SIM card provided by the ANE, with multi-carrier data service (not restricted to a single carrier).

**Acceptance Criteria:**

1. [ ] The module supports 4G and 5G networks.
2. [ ] It works with SIM cards from at least 2 Colombian carriers.
3. [ ] The connection is established automatically when the sensor powers on.

**Notes:**  
Currently uses a 4.5G module limited to Movistar. The new module must be multi-carrier.

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
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL enable a WiFi connection on the sensor, configurable via Ethernet cable.

**Acceptance Criteria:**

1. [ ] The sensor connects to configured WiFi networks.
2. [ ] WiFi configuration is performed initially over an Ethernet cable.
3. [ ] The WiFi connection is used as an alternative communication channel.

**Notes:**  
Initial configuration must be done over an Ethernet cable.

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
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL provide access to an easily accessible Ethernet port without requiring the enclosure to be opened.

**Acceptance Criteria:**

1. [ ] The Ethernet port is externally accessible without tools.
2. [ ] The port supports a minimum speed of 100 Mbps.

**Notes:**  
It currently requires opening the enclosure to reach the port. ANE confirms (YES).

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
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL implement automatic IP-network connection and routing, using the various available channels (a failover/priority scheme among 4G/5G, WiFi, and Ethernet).

**Acceptance Criteria:**

1. [ ] The system automatically selects the available network channel with the highest priority.
2. [ ] Failover between channels occurs without manual intervention.
3. [ ] The priority order is configurable.

**Notes:**  
—

---

#### 3.7.2 Support and GPS

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
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL allow remote IP access to the sensors and Over-The-Air (OTA) software updates.

**Acceptance Criteria:**

1. [ ] Sensors can be accessed remotely via SSH or a secure equivalent.
2. [ ] Software updates are performed without physical access to the sensor.
3. [ ] The update process includes automatic rollback in case of failure.

**Notes:**  
ANE confirms (YES).

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
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL continue to report location via GPS regardless of the manual parameterization, providing redundancy.

**Acceptance Criteria:**

1. [ ] GPS continues to report an automatic location even when manual coordinates are configured.
2. [ ] Both location sources are stored in the measurement records.

**Notes:**  
—

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
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL have a horizontal GPS accuracy of approximately 3 meters under open sky.

**Acceptance Criteria:**

1. [ ] Horizontal accuracy ≤ 3 m (CEP 50%) under open-sky conditions.
2. [ ] The accuracy is verified against a reference GPS receiver.

**Notes:**  
May require a change of GPS hardware.

---

### 3.8 Antennas and Radiation Measurement

#### 3.8.1 Antennas

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
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL incorporate specific antennas for signal reception in order to optimize signal display across different bands.

**Acceptance Criteria:**

1. [ ] A specific antenna for DTT.
2. [ ] Verification of an antenna for frequencies > 2 GHz (mobile-telephony downlink).
3. [ ] Each antenna has a documented and calibrated antenna factor (AF).

**Notes:**  
Priority bands: 1. DTT, 2. Verify > 2 GHz mobile telephony (downlink), 3. Evaluate additional antennas as needed.

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
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL incorporate an active antenna with a frequency range up to 6 GHz, with a SAW filter, a flat response, and a known antenna factor, for non-ionizing radiation measurement.

**Acceptance Criteria:**

1. [ ] The active antenna's frequency range covers up to 6 GHz.
2. [ ] It includes a SAW filter.
3. [ ] A flat frequency response (variation ≤ 2 dB across the full range).
4. [ ] An antenna factor documented by the manufacturer.

**Notes:**  
ANE confirms (YES). Requires new hardware.

---

#### 3.8.2 Non-Ionizing Radiation Measurement

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
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL adopt the following measurement units for non-ionizing radiation: power density (S = W/m²), magnetic field strength (A/m), electric field strength (V/m), dBµV/m, and dBA/m.

**Acceptance Criteria:**

1. [ ] All listed units are available as a display option.
2. [ ] Conversions between units are correct.

**Notes:**  
—

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
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL measure the level and strength of the electric field, including the characterized antenna's data (antenna factor, AF) for its computation.

**Acceptance Criteria:**

1. [ ] The field measurement uses the antenna factor (AF) of the connected antenna.
2. [ ] The applied formula is: E [V/m] = V_measured [V] × AF.
3. [ ] Results are presented in V/m and dBµV/m.

**Notes:**  
Antenna factor AF = V_measured / E.

---

### 3.9 Power and Autonomy

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
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL integrate autonomous power modules through sustainable solutions, such as hybrid solar-and-battery systems, with a battery manager.

**Acceptance Criteria:**

1. [ ] The sensor operates on solar + battery power without an external source.
2. [ ] It includes a battery manager with a charge indicator.
3. [ ] The solar-panel design is discreet (not conspicuous).

**Notes:**  
Battery manager, small unobtrusive solar charging. Owner: Bernardo.

---

### 3.10 Accuracy and Reliability

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
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL synchronize to an NTP network clock for the time-stamping of samples.

**Acceptance Criteria:**

1. [ ] The sensor synchronizes with an NTP server when a network connection is established.
2. [ ] The time offset is ≤ 100 ms relative to the NTP server.
3. [ ] The synchronization status is visible in the monitoring interface.

**Notes:**  
ANE confirms (YES).

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
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL include calibration procedures for frequency, receive gain, IQ balance, and DC-offset correction.

**Acceptance Criteria:**

1. [ ] A documented frequency-calibration procedure.
2. [ ] A documented gain-calibration procedure.
3. [ ] A documented procedure for IQ-balance and DC-offset correction.
4. [ ] Each calibration produces a certificate or record with a date and result.

**Notes:**  
—

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
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL have a minimum DANL of –100 dBm across the operating range.

**Acceptance Criteria:**

1. [ ] The measured DANL is ≤ –100 dBm over at least 90% of the frequency range.
2. [ ] The measurement is performed with a 50 Ω load and documented per band.

**Notes:**  
Known HackRF limitations: it has neither a calibrated attenuator nor a known reference noise source. The commitment is to characterize the system and provide values that allow the reliability of the measurements to be determined.

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
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL have a minimum dynamic range of ≥ 80 dB.

**Acceptance Criteria:**

1. [ ] Measured dynamic range ≥ 80 dB in a two-tone test.
2. [ ] The measurement is documented with the test setup and results.

**Notes:**  
—

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
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL have a maximum frequency accuracy of ± 2 ppm.

**Acceptance Criteria:**

1. [ ] Measured frequency error ≤ ± 2 ppm against a calibrated reference.
2. [ ] The measurement is performed at room temperature (20–25 °C).

**Notes:**  
—

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
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL specify and meet a frequency drift due to aging of ≤ 1 ppm per year.

**Acceptance Criteria:**

1. [ ] The selected oscillator has an aging specification of ≤ 1 ppm/year.
2. [ ] The oscillator type and its aging specification are documented.

**Notes:**  
The HackRF starts with 20–50 ppm of error, uncompensated. An oscillator change is possible. Depends on the type of oscillator used.

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
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL have a typical amplitude accuracy of ± 1 dB, taking into account stability, linearity, and flat response.

**Acceptance Criteria:**

1. [ ] Amplitude error ≤ ± 1 dB over at least 90% of the frequency range.
2. [ ] Amplitude linearity is verified in 10 dB steps.

**Notes:**  
HackRF limitations: no AGC or calibrated attenuators, no pre-filters, image noise present.

---

### 3.11 Export and Integration

---

**`INTG-EXP-001` — Data export in CSV, JSON, and XML**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `DEMONSTRATION`                                          |
| **New hardware**       | No                                                       |
| **Standard(s)**        | —                                                        |
| **Dependencies**       | —                                                        |
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL export data in CSV, JSON, and XML formats for the processing of spectrum-monitoring results.

**Acceptance Criteria:**

1. [ ] All three formats (CSV, JSON, XML) are available for export.
2. [ ] The exported files include metadata (timestamp, location, measurement parameters).
3. [ ] The JSON and XML schemas are documented.

**Notes:**  
ANE confirms (YES).

---

**`INTG-API-001` — Standard API**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `DEMONSTRATION`                                          |
| **New hardware**       | No                                                       |
| **Standard(s)**        | —                                                        |
| **Dependencies**       | `ANAL-SEG-001`                                           |
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL provide APIs with a standard information-exchange format (at minimum JSON), in accordance with international spectrum-management standards.

**Acceptance Criteria:**

1. [ ] The API is documented (OpenAPI/Swagger or equivalent).
2. [ ] The primary exchange format is JSON.
3. [ ] The API implements authentication and authorization.

**Notes:**  
Review functions based on ITU standards for interoperability.

---

### 3.12 Standards Compliance

---

**`ESTD-ITU-001` — Compliance with ITU-R recommendations**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `CONSTRAINT`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `ANALYSIS`                                               |
| **New hardware**       | No                                                       |
| **Standard(s)**        | ITU-R SM.1537, SM.1138; `REF-001`, `REF-002`             |
| **Dependencies**       | —                                                        |
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL comply with the ITU-R recommendations, including but not limited to: SM.1537 (requirements for monitoring stations: accuracy, response time, scanning capability, storage) and SM.1138 (sensitivity, selectivity).

**Acceptance Criteria:**

1. [ ] Point-by-point conformance against SM.1537 is documented.
2. [ ] Point-by-point conformance against SM.1138 is documented.
3. [ ] Conformance gaps are identified and their resolution is planned.

**Notes:**  
SM.1537: accuracy, response time, scanning capability, storage. SM.1138: sensitivity, selectivity.

---

**`ESTD-ITU-002` — Compliance with CEPT/ERC standards**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `CONSTRAINT`                                             |
| **Priority**           | `SHOULD`                                                  |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `ANALYSIS`                                               |
| **New hardware**       | No                                                       |
| **Standard(s)**        | CEPT/ERC/REC 70-03, ECC Report 260; `REF-005`, `REF-006` |
| **Dependencies**       | —                                                        |
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHOULD integrate the technical standards of international bodies, such as CEPT/ERC/REC 70-03 (shared use of licence-exempt spectrum) and ECC Report 260 (protection for SRD services).

**Acceptance Criteria:**

1. [ ] The applicability of CEPT/ERC/REC 70-03 to the system is documented.
2. [ ] The applicability of ECC Report 260 to the system is documented.

**Notes:**  
CEPT/ERC/REC 70-03: shared use of licence-exempt spectrum (433 MHz, 2.4 GHz). ECC Report 260: protection for SRD services.

---

**`ESTD-RNI-001` — Electric-field compliance with ITU-T K.113/K.100**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `CONSTRAINT`                                             |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `ANALYSIS`                                               |
| **New hardware**       | No                                                       |
| **Standard(s)**        | ITU-T K.113, K.100; `REF-003`, `REF-004`                 |
| **Dependencies**       | `ANTE-ANT-002`, `ANTE-RNI-002`                           |
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL comply with ITU-T K.113 and K.100 for the measurement of the electric field in urban environments and the assessment of human exposure to electromagnetic fields.

**Acceptance Criteria:**

1. [ ] The electric-field measurement procedure follows the K.113 guidelines.
2. [ ] Exposure levels are assessed in accordance with K.100.
3. [ ] The measurement results include measurement uncertainty.

**Notes:**  
ANE confirms (YES). Standards for measuring the electric field in urban areas and assessing human exposure.

---

## 4. External Interface Requirements

### 4.1 User Interfaces

The frontend will be developed in React.js (or Vue.js) with the D3.js/Plotly.js visualization libraries and WebGL acceleration for real-time spectral rendering.

### 4.2 Hardware Interfaces

- SDR: HackRF One (USB, internal SPI interface)
- Embedded platform: Raspberry Pi
- GPS: GPS module with ≤ 3 m accuracy
- Antennas: SMA connectors for band-specific antennas and the active antenna
- Connectivity: 4G/5G module with SIM, WiFi, Ethernet RJ45
- Power: solar panel + battery + charge manager

### 4.3 Software Interfaces

- Backend: FastAPI or Node.js with WebSockets
- Containers: Docker
- Authorized-emission database: integration with the ANE database
- API: REST/JSON, documented with OpenAPI

### 4.4 Communication Interfaces

- Sensor ↔ Cloud: HTTPS (TLS ≥ 1.2), secure WebSockets
- Network protocols: TCP/IP over 4G/5G, WiFi, Ethernet
- NTP for time synchronization
- SSH for remote maintenance access

---

## 5. Non-Functional Requirements

### 5.1 Performance

- Real-time monitoring with a visualization latency ≤ 1 second.
- Monitoring bandwidth up to 20 MHz instantaneous.
- Scheduled scans run with a tolerance ≤ 1 minute.

### 5.2 Security

- All communications encrypted with TLS ≥ 1.2 (`ANAL-SEG-001`).
- Token-based authentication for the API (`INTG-API-001`).
- Secure session management.

### 5.3 Reliability / Availability

- Network auto-routing for high connectivity availability (`CONN-RED-004`).
- Local storage on the sensor for operation during connectivity loss (`FORN-ALM-003`).

### 5.4 Maintainability

- OTA software updates (`CONN-SOP-001`).
- Remote SSH access for diagnostics.
- Documented calibration procedures (`CONF-CAL-001`).

### 5.5 Portability

- Docker architecture for the cloud backend.
- Standard JSON APIs for interoperability.

---

## 6. Traceability

| Requirement ID   | Category               | Standard Ref              | New Hardware   |
|------------------|------------------------|---------------------------|----------------|
| `ANAL-SEG-001`   | Security               | ETSI EN 303 645           | No             |
| `ANAL-EMC-001`   | EMC                    | —                         | Yes            |
| `ANAL-RNG-001`   | Spectral range         | ITU-R SM.1537             | No             |
| `ANAL-RNG-002`   | Bandwidth              | —                         | No             |
| `ANAL-PAR-001`   | Parameterization       | —                         | No             |
| `ANAL-PAR-002`   | Parameterization       | —                         | No             |
| `ANAL-PAR-003`   | Parameterization       | —                         | No             |
| `ANAL-PAR-004`   | Parameterization       | —                         | Yes            |
| `ANAL-PAR-005`   | GPS                    | —                         | No             |
| `ANAL-PAR-006`   | Units                  | —                         | No             |
| `ANAL-PAR-007`   | Detection              | —                         | No             |
| `ANAL-MED-001`   | Measurement            | ITU-R SM.1537             | No             |
| `ANAL-MED-002`   | Measurement            | —                         | No             |
| `ANAL-MED-003`   | Measurement            | ITU-R SM.1537             | No             |
| `ANAL-MED-004`   | Measurement            | —                         | No             |
| `ANAL-MED-005`   | Broadcasting           | —                         | No             |
| `ANAL-MED-006`   | Broadcasting           | —                         | No             |
| `ANAL-MED-007`   | Broadcasting           | —                         | No             |
| `NORM-DET-001`   | Compliance             | ITU-R SM.1537             | No             |
| `NORM-DET-002`   | Compliance             | ITU-R SM.1537             | No             |
| `NORM-DET-003`   | Compliance             | ITU-R SM.1537             | No             |
| `NORM-SRV-001`   | Broadcasting           | —                         | No             |
| `NORM-SRV-002`   | Broadcasting           | —                         | No             |
| `NORM-VER-001`   | Verification           | —                         | No             |
| `NORM-VER-002`   | Verification           | —                         | No             |
| `GEST-MON-001`   | Management             | —                         | No             |
| `GEST-MON-002`   | Management             | —                         | No             |
| `GEST-PRG-001`   | Management             | ITU-R SM.1537             | No             |
| `GEST-REP-001`   | Management             | —                         | No             |
| `FORN-ALM-001`   | Storage                | ITU-R SM.1537             | No             |
| `FORN-ALM-002`   | Storage                | —                         | No             |
| `FORN-ALM-003`   | Storage                | —                         | Yes            |
| `CONN-RED-001`   | Connectivity           | —                         | Yes            |
| `CONN-RED-002`   | Connectivity           | —                         | No             |
| `CONN-RED-003`   | Connectivity           | —                         | Yes            |
| `CONN-RED-004`   | Connectivity           | —                         | No             |
| `CONN-SOP-001`   | Support                | —                         | No             |
| `CONN-GPS-001`   | GPS                    | —                         | No             |
| `CONN-GPS-002`   | GPS                    | —                         | Yes            |
| `ANTE-ANT-001`   | Antennas               | —                         | Yes            |
| `ANTE-ANT-002`   | Antennas               | ITU-T K.113, K.100        | Yes            |
| `ANTE-RNI-001`   | Non-ionizing radiation | ITU-T K.113, K.100        | No             |
| `ANTE-RNI-002`   | Non-ionizing radiation | ITU-T K.113, K.100        | No             |
| `POWR-AUT-001`   | Power                  | —                         | Yes            |
| `CONF-SIN-001`   | Synchronization        | —                         | No             |
| `CONF-CAL-001`   | Calibration            | —                         | No             |
| `CONF-CAR-001`   | Characterization       | ITU-R SM.1138             | No             |
| `CONF-CAR-002`   | Characterization       | ITU-R SM.1138             | No             |
| `CONF-CAR-003`   | Characterization       | —                         | No             |
| `CONF-CAR-004`   | Characterization       | —                         | Yes            |
| `CONF-CAR-005`   | Characterization       | —                         | No             |
| `INTG-EXP-001`   | Export                 | —                         | No             |
| `INTG-API-001`   | Integration            | —                         | No             |
| `ESTD-ITU-001`   | Standards              | ITU-R SM.1537, SM.1138    | No             |
| `ESTD-ITU-002`   | Standards              | CEPT/ERC/REC 70-03        | No             |
| `ESTD-RNI-001`   | Standards              | ITU-T K.113, K.100        | No             |

---

## 7. Structural Validation (for AI)

> This section defines the rules that an automated validator SHALL verify against this document.

### 7.1 Format Rules

| Rule ID  | Rule                                                                  | Severity  |
|----------|-----------------------------------------------------------------------|-----------|
| `V-001`  | Each requirement SHALL have a unique `id` with the format `[A-Z]{3,5}-[A-Z]{2,4}-\d{3}` | `ERROR`   |
| `V-002`  | Each requirement SHALL have all mandatory fields: Type, Priority, Status, Verification, Description, Acceptance Criteria | `ERROR`   |
| `V-003`  | The Description field SHALL begin with "The system SHALL" or "The system SHOULD" | `WARNING` |
| `V-004`  | The Acceptance Criteria SHALL have at least 1 verifiable element       | `ERROR`   |
| `V-005`  | The Type values SHALL be one of: `FUNCTIONAL`, `NON_FUNCTIONAL`, `INTERFACE`, `CONSTRAINT` | `ERROR`   |
| `V-006`  | The Priority values SHALL follow MoSCoW: `MUST`, `SHOULD`, `COULD`, `WONT` | `ERROR`   |
| `V-007`  | The Verification values SHALL be: `INSPECTION`, `DEMONSTRATION`, `TEST`, `ANALYSIS` | `ERROR`   |
| `V-008`  | The Status values SHALL be: `PROPOSED`, `APPROVED`, `IMPLEMENTED`, `VERIFIED`, `REJECTED` | `ERROR`   |
| `V-009`  | Referenced Dependencies SHALL exist as IDs in the document            | `ERROR`   |
| `V-010`  | No duplicate IDs SHALL exist anywhere in the document                 | `ERROR`   |
| `V-011`  | Each section 3.x SHALL contain at least one requirement               | `WARNING` |

### 7.2 Semantic Rules

| Rule ID  | Rule                                                                  | Severity  |
|----------|-----------------------------------------------------------------------|-----------|
| `S-001`  | Requirements with Priority `MUST` SHALL have Acceptance Criteria with quantitative values where applicable | `WARNING` |
| `S-002`  | Requirements with New hardware `Yes` SHALL specify the component in Notes | `WARNING` |
| `S-003`  | Requirements with a non-empty Standard(s) SHALL cite documents listed in §1.4 | `WARNING` |
| `S-004`  | There SHALL be no circular dependencies between requirements          | `ERROR`   |

### 7.3 Document Statistics

| Metric                           | Value |
|----------------------------------|-------|
| Total requirements               | 53    |
| FUNCTIONAL requirements          | 39    |
| NON_FUNCTIONAL requirements      | 11    |
| CONSTRAINT requirements          | 3     |
| MUST priority                    | 51    |
| SHOULD priority                  | 2     |
| Requiring new hardware           | 11    |
| With a reference to standards    | 18    |

---

## Annex A — Reference Standards

| Standard               | Body      | Title / Scope                                                         |
|------------------------|-----------|-----------------------------------------------------------------------|
| ITU-R SM.1537          | ITU       | Automation and requirements of spectrum-monitoring stations           |
| ITU-R SM.1138          | ITU       | Sensitivity and selectivity of monitoring equipment                   |
| ITU-T K.113            | ITU       | Electric field measurement in urban environments                      |
| ITU-T K.100            | ITU       | Assessment of human exposure to electromagnetic fields                |
| CEPT/ERC/REC 70-03     | CEPT      | Shared use of licence-exempt spectrum                                 |
| ECC Report 260         | CEPT      | Protection for SRD services                                          |
| IEEE/ISO/IEC 29148:2018| IEEE/ISO  | Requirements engineering — Life cycle processes                       |
| ETSI EN 303 645        | ETSI      | Cyber Security for Consumer IoT                                      |

## Annex B — Extended Glossary

| Term                | Definition                                                                                  |
|---------------------|---------------------------------------------------------------------------------------------|
| HackRF One          | Low-cost SDR, 1 MHz – 6 GHz range, 20 MHz instantaneous bandwidth                           |
| Raspberry Pi        | Single-board computer (SBC) used as the sensor's embedded platform                          |
| CS8                 | IQ-sample file format (Complex Signed 8-bit)                                                |
| IF span             | Frequency range visible on screen / under analysis                                           |
| OBW                 | Occupied Bandwidth — the bandwidth containing a defined percentage of the total power        |
| Antenna Factor (AF) | Ratio of the incident electric field to the voltage at the antenna terminals (V/m ÷ V)      |
| RF gasket           | Electromagnetic-shielding seal for isolation between compartments                            |
| Failover            | Automatic switchover to a backup channel when the primary channel fails                       |
| OTA                 | Over The Air — remote software update without physical access                               |

---

> **Usage note:** This document contains only the requirements marked as approved (green) in the Excel roadmap file "Resumen_Funcionalidades_ANE_Fase_2_lastEDITEDB.xlsx". Items marked in yellow (under discussion), gold (future interest), blue (to be analyzed), black (later phase), or other colors were deliberately excluded.

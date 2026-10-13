# PROJECT: Edge Sensor — ANE Spectrum Monitoring System

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
| **Document ID**        | `SRS-ANE-EDGE-001`                                        |
| **Project**            | Edge Sensor — Spectrum Monitoring Subsystem (Phase 2)      |
| **Organization**       | National Spectrum Agency (ANE) — Colombia                  |
| **Version**            | 0.1.0                                                     |
| **Classification**     | `INTERNAL`                                                |
| **Author(s)**          | _To be defined_                                           |
| **Reviewer(s)**        | _To be defined_                                           |
| **Approver(s)**        | _To be defined_                                           |

### Change Log

| Version | Date       | Author             | Change Description                                      |
|---------|------------|--------------------|---------------------------------------------------------|
| 0.1.0   | 2026-10-13 | AI-assisted generation | Extraction of edge requirements from SRS-ANE-001 (full system) |

---

## 1. Introduction

### 1.1 Purpose

This document specifies the requirements for the **edge sensor** as a self-contained subsystem of the ANE Spectrum Monitoring System. It covers exclusively what runs on the embedded node (HackRF One + Raspberry Pi): the SDR driver, the DSP pipeline (PSD, FFT bins, traces), demodulation, network connectivity (4G/5G, WiFi, Ethernet), GPIO multiplexing, GPS, local storage, autonomous power, and calibration.

**It excludes:** the cloud backend, the web frontend, integration APIs, the ANE's centralized database, report generation, and any logic that requires an active connection to the server.

### 1.2 System Scope

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

### 1.4 References

| Ref ID     | Document                                                               | Version / Date      |
|------------|------------------------------------------------------------------------|---------------------|
| `REF-001`  | ITU-R SM.1537 — Automation and requirements of monitoring stations     | In force            |
| `REF-002`  | ITU-R SM.1138 — Monitoring sensitivity and selectivity                 | In force            |
| `REF-003`  | ITU-T K.113 — Electric field measurement in urban environments         | In force            |
| `REF-004`  | ITU-T K.100 — Assessment of human exposure to electromagnetic fields   | In force            |
| `REF-007`  | IEEE/ISO/IEC 29148:2018 — Requirements engineering                     | 2018                |
| `REF-FULL` | SRS-ANE-001 — Full-System SRS, Phase 2                                 | 0.1.0 / 2026-10-13  |

### 1.5 Document Overview

Section 3 contains the specific requirements of the edge sensor, organized by subsystem: RF architecture, DSP parameterization, signal processing, local detection, on-device storage, network connectivity, antennas, power, health monitoring, and calibration. Section 6 presents traceability. Section 7 defines the structural validation rules.

---

## 2. Overall System Description

### 2.1 Product Perspective

This document describes the edge sensor as a subsystem of the full system (see `REF-FULL`). The sensor operates as an autonomous node for spectral acquisition and preprocessing. The requirements here are a filtered subset of the full SRS, including only those that run on or reside in the embedded node.

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

- Base hardware: HackRF One as the primary SDR (inherent DANL and dynamic-range limitations).
- Embedded platform: Raspberry Pi (low power, processing limitations).
- Connectivity: dependent on 4G/5G coverage from Colombian carriers.
- Power: solar + battery with a charge manager.

### 2.5 Assumptions and Dependencies

- The ANE provides data SIM cards for mobile connectivity.
- Sensors are deployed at sites with mains power or where a solar solution is viable.
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
| **New hardware**       | Yes (RF gasket)                                          |
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

#### 3.1.2 Spectral Range

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
3. [ ] The DSP pipeline processes the full bandwidth with a latency ≤ 1 second.

**Notes:**  
Manual between 6 and 20 MHz; automatic at 20 MHz.

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
3. [ ] Changing the RBW updates the DSP pipeline in real time.

**Notes:**  
Define ≥ 6 RBW options. RBW is implemented via the FFT window size.

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
The system SHALL implement Video Bandwidth (VBW) filters suited to the type of analysis (fine or average) in order to smooth the processed signal after the RBW computation.

**Acceptance Criteria:**

1. [ ] The VBW is configurable independently of the RBW.
2. [ ] Filters are available for fine and averaged analysis.
3. [ ] The DSP output shows a perceptible difference between filtering modes.

**Notes:**  
Filtering applied after RBW to smooth the signal. Implemented digitally in the DSP pipeline.

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

1. [ ] Latitude and longitude can be entered manually via the sensor configuration.
2. [ ] Manual coordinates are associated with the measurements taken.
3. [ ] The system records whether the location is automatic GPS or manual.

**Notes:**  
—

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
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL allow the selection and conversion of measurement units: frequency (Hz, kHz, MHz, GHz), power (dBm, dBmV, dBµV, V, W), and electric field and power density (V/m, W/m², dBµV/m).

**Acceptance Criteria:**

1. [ ] All listed units are available as a sensor output parameter.
2. [ ] Conversion between units is mathematically correct (error < 0.01 dB).
3. [ ] A change of unit is applied to the DSP pipeline output data.

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
3. [ ] Signals above the threshold are flagged in the sensor's output data.

**Notes:**  
Parameterize the threshold and, based on it, define the portion of the spectrum of interest.

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
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL compute spectral traces: maximum (max hold), minimum (min hold), average, and RMS, peak, and average detection modes.

**Acceptance Criteria:**

1. [ ] The maximum trace retains the highest value per frequency bin (FFT bin).
2. [ ] The minimum trace retains the lowest value per frequency bin.
3. [ ] The average trace computes the arithmetic mean over N sweeps (N configurable).
4. [ ] The RMS, peak, and average detection modes are selectable.

**Notes:**  
Operations over FFT bins. Max hold and min hold accumulate across successive sweeps.

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
3. [ ] Results are expressed in the selected frequency unit.

**Notes:**  
OBW is computed over the FFT bins of the PSD. –X dB is where the signal falls X below the peak.

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

1. [ ] Channel-power measurement is selectable via a configuration parameter.
2. [ ] The measured channel width is configurable up to 20 MHz.
3. [ ] The result is expressed in the selected power units.

**Notes:**  
Integration of the PSD over the channel bins. Limited to 20 MHz (the HackRF's instantaneous bandwidth).

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
The system SHALL decode and extract Radio Data System (RDS) information from FM signals.

**Acceptance Criteria:**

1. [ ] The system decodes basic RDS fields (PI, PS, RT).
2. [ ] The RDS information is included in the sensor's output data alongside the FM measurement.

**Notes:**  
RDS decoding is performed in the sensor's DSP pipeline.

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
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL demodulate FM and AM signals in real time, producing digital audio as output.

**Acceptance Criteria:**

1. [ ] FM audio is demodulated with audible quality.
2. [ ] AM audio is demodulated with audible quality (from 1 MHz with the HackRF One).
3. [ ] The demodulated audio is stored locally or transmitted as a stream.

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

1. [ ] The AM modulation depth is computed as a percentage.
2. [ ] The FM frequency deviation is computed in kHz.
3. [ ] The values update in real time during demodulation.

**Notes:**  
AM only from 1 MHz upward with the HackRF One; it requires an additional antenna.

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
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL detect intermodulation, including the identification of suspected intermodulation products in AM, FM, and the aeronautical mobile service band (108 MHz–137 MHz), as well as intermediate-frequency (IF) verification.

**Acceptance Criteria:**

1. [ ] The system computes 2nd- and 3rd-order intermodulation products for detected emissions.
2. [ ] Suspected intermodulation products are flagged in the spectral output data.
3. [ ] IF verification is performed automatically.

**Notes:**  
Covers AM, FM, and the aeronautical band (108–137 MHz). Computed locally over FFT bins.

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
2. [ ] A local record is generated with frequency, power, and duration data.
3. [ ] Detection runs continuously without external intervention.

**Notes:**  
Detection threshold: > 3 dB above the average level. Processed locally in the DSP pipeline.

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
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL demodulate and extract audio from FM and AM signals, storing it locally for later use in verification and forensic analysis.

**Acceptance Criteria:**

1. [ ] The extracted audio is stored locally in a standard format (WAV or MP3).
2. [ ] The audio file is associated with the measurement metadata (frequency, timestamp, location).

**Notes:**  
AM only from 1 MHz with the HackRF One; it requires an additional antenna.

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
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL provide local historical storage for forensic analysis, including spectral data with a timestamp and GPS location.

**Acceptance Criteria:**

1. [ ] Monitoring data is stored locally with a timestamp and GPS coordinates.
2. [ ] Historical data is queryable by date range, frequency, and location.
3. [ ] The integrity of the stored data is verifiable (checksum or hash).

**Notes:**  
Using current hardware.

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
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL add storage space to the sensor so that CS8 files (raw IQ) can be stored for later use as forensic evidence.

**Acceptance Criteria:**

1. [ ] The sensor has accessible additional storage.
2. [ ] CS8 files are stored with metadata (timestamp, frequency, coordinates).
3. [ ] Local storage is remotely accessible for download.

**Notes:**  
Include the cost of the storage solution to be used (high-capacity SSD/microSD).

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
It currently requires opening the enclosure to reach the port.

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
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL allow remote IP access to the sensor and Over-The-Air (OTA) software updates.

**Acceptance Criteria:**

1. [ ] The sensor can be accessed remotely via SSH or a secure equivalent.
2. [ ] Software updates are performed without physical access to the sensor.
3. [ ] The update process includes automatic rollback in case of failure.

**Notes:**  
—

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
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL incorporate specific antennas for signal reception in order to optimize reception across different bands.

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
Requires new hardware.

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
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL adopt the following measurement units for non-ionizing radiation: power density (S = W/m²), magnetic field strength (A/m), electric field strength (V/m), dBµV/m, and dBA/m.

**Acceptance Criteria:**

1. [ ] All listed units are available as a display option in the sensor output.
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
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL measure and record sensor health variables (disk, RAM, CPU, temperature) using the variables available in the operating system.

**Acceptance Criteria:**

1. [ ] At least the following are monitored: disk usage, RAM, CPU, and temperature.
2. [ ] Local alerts are generated when variables exceed configurable thresholds.
3. [ ] Health data is stored locally with a timestamp.

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
The system SHALL measure and record IP-connection quality, including RTT, channel status (Alive/Not Alive), available bandwidth, and packet loss.

**Acceptance Criteria:**

1. [ ] RTT is measured periodically (configurable interval).
2. [ ] The Alive/Not Alive status of each network interface is detected.
3. [ ] A local record is generated when RTT or packet loss exceeds thresholds.

**Notes:**  
—

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
The system SHALL allow parameterized spectrum scans (frequency, RBW, VBW, duration) to be scheduled, run locally on the sensor, and store their results for later retrieval.

**Acceptance Criteria:**

1. [ ] Scans can be scheduled with defined parameters (frequency, RBW, VBW, duration, repetition).
2. [ ] The results of scheduled scans are stored locally.
3. [ ] Scans run at the scheduled time with a tolerance ≤ 1 minute.

**Notes:**  
Local scheduler on the sensor (cron or equivalent).

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
| **Phase**              | 2025–2026                                                |

**Description:**  
The system SHALL synchronize to an NTP network clock for the time-stamping of samples.

**Acceptance Criteria:**

1. [ ] The sensor synchronizes with an NTP server when a network connection is established.
2. [ ] The time offset is ≤ 100 ms relative to the NTP server.
3. [ ] The synchronization status is queryable locally.

**Notes:**  
—

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
Known HackRF limitations: it has neither a calibrated attenuator nor a known reference noise source.

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

## 4. External Interface Requirements

### 4.1 Hardware Interfaces

- SDR: HackRF One (USB, internal SPI interface)
- Embedded platform: Raspberry Pi
- GPS: GPS module with ≤ 3 m accuracy (UART/USB)
- Antennas: SMA connectors for band-specific antennas and the active antenna
- 4G/5G module: USB connection with SIM slot
- WiFi: integrated into the RPi or an external USB module
- Ethernet: externally accessible RJ45
- GPIO: multiplexing for antenna switching and peripheral control
- Power: solar panel + battery + charge manager
- Storage: additional SSD/microSD for CS8

### 4.2 Software Interfaces

- SDR driver: libhackrf / SoapySDR
- DSP pipeline: FFT, PSD, and RBW/VBW filtering
- Scheduler: cron or equivalent for scheduled scans
- Network manager: automatic failover between network interfaces
- NTP client: time synchronization

### 4.3 Communication Interfaces

- HackRF ↔ RPi: USB 2.0 (480 Mbps; IQ raw at 20 MS/s × 8 bit = 40 MB/s)
- GPS ↔ RPi: UART/USB (NMEA sentences)
- 4G/5G ↔ RPi: USB (AT commands + data)
- GPIO: control of the antenna mux, status LEDs, and battery sensors

---

## 5. Non-Functional Requirements

### 5.1 Performance

- DSP pipeline with latency ≤ 1 second for 20 MHz of bandwidth.
- Minimum frequency resolution: 10 Hz.
- Scheduled scans run with a tolerance ≤ 1 minute.

### 5.2 Reliability

- Network auto-routing for high connectivity availability (`CONN-RED-004`).
- Local storage in case of connectivity loss (`FORN-ALM-003`).
- NTP sync with ≤ 100 ms offset (`CONF-SIN-001`).

### 5.3 Maintainability

- OTA software updates (`CONN-SOP-001`) with rollback.
- Remote SSH access for diagnostics.
- Documented calibration procedures (`CONF-CAL-001`).

### 5.4 Accuracy

- DANL ≤ –100 dBm (`CONF-CAR-001`).
- Dynamic range ≥ 80 dB (`CONF-CAR-002`).
- Frequency accuracy ± 2 ppm (`CONF-CAR-003`).
- Amplitude accuracy ± 1 dB (`CONF-CAR-005`).

---

## 6. Traceability

| Requirement ID   | Edge Subsystem           | Standard Ref              | New Hardware   |
|------------------|--------------------------|---------------------------|----------------|
| `ANAL-EMC-001`   | RF architecture          | —                         | Yes            |
| `ANAL-RNG-001`   | Spectral range           | ITU-R SM.1537             | No             |
| `ANAL-RNG-002`   | Bandwidth                | —                         | No             |
| `ANAL-PAR-001`   | DSP parameterization     | —                         | No             |
| `ANAL-PAR-002`   | DSP parameterization     | —                         | No             |
| `ANAL-PAR-003`   | DSP parameterization     | —                         | No             |
| `ANAL-PAR-004`   | DSP parameterization     | —                         | Yes            |
| `ANAL-PAR-005`   | GPS                      | —                         | No             |
| `ANAL-PAR-006`   | Units                    | —                         | No             |
| `ANAL-PAR-007`   | Detection                | —                         | No             |
| `ANAL-MED-001`   | DSP / traces             | ITU-R SM.1537             | No             |
| `ANAL-MED-003`   | DSP / OBW                | ITU-R SM.1537             | No             |
| `ANAL-MED-004`   | DSP / channel power      | —                         | No             |
| `ANAL-MED-005`   | DSP / RDS                | —                         | No             |
| `ANAL-MED-006`   | DSP / demodulation       | —                         | No             |
| `ANAL-MED-007`   | DSP / modulation         | —                         | No             |
| `NORM-VER-001`   | Local detection          | —                         | No             |
| `NORM-VER-002`   | Local detection          | —                         | No             |
| `NORM-SRV-002`   | Forensic audio           | —                         | No             |
| `FORN-ALM-001`   | Local storage            | ITU-R SM.1537             | No             |
| `FORN-ALM-003`   | Local storage            | —                         | Yes            |
| `CONN-RED-001`   | Connectivity             | —                         | Yes            |
| `CONN-RED-002`   | Connectivity             | —                         | No             |
| `CONN-RED-003`   | Connectivity             | —                         | Yes            |
| `CONN-RED-004`   | Connectivity             | —                         | No             |
| `CONN-SOP-001`   | Maintenance              | —                         | No             |
| `CONN-GPS-001`   | GPS                      | —                         | No             |
| `CONN-GPS-002`   | GPS                      | —                         | Yes            |
| `ANTE-ANT-001`   | Antennas                 | —                         | Yes            |
| `ANTE-ANT-002`   | Antennas                 | ITU-T K.113, K.100        | Yes            |
| `ANTE-RNI-001`   | Non-ionizing radiation   | ITU-T K.113, K.100        | No             |
| `ANTE-RNI-002`   | Non-ionizing radiation   | ITU-T K.113, K.100        | No             |
| `POWR-AUT-001`   | Power                    | —                         | Yes            |
| `GEST-MON-001`   | Health monitoring        | —                         | No             |
| `GEST-MON-002`   | Health monitoring        | —                         | No             |
| `GEST-PRG-001`   | Local scheduler          | ITU-R SM.1537             | No             |
| `CONF-SIN-001`   | Synchronization          | —                         | No             |
| `CONF-CAL-001`   | Calibration              | —                         | No             |
| `CONF-CAR-001`   | Characterization         | ITU-R SM.1138             | No             |
| `CONF-CAR-002`   | Characterization         | ITU-R SM.1138             | No             |
| `CONF-CAR-003`   | Characterization         | —                         | No             |
| `CONF-CAR-004`   | Characterization         | —                         | Yes            |
| `CONF-CAR-005`   | Characterization         | —                         | No             |


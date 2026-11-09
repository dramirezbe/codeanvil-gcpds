# FM Spectrum, Waterfall and Channel Detection (RTL-SDR → Raspberry Pi)

## Stakeholder Requirements Specification (StRS)

> **Standard:** IEEE/ISO/IEC 29148:2018 §9.4 — *Stakeholder requirements specification.*
>
> **Template version:** 4.0.0
> **Creation date:** 2026-11-05
> **Last modified:** 2026-11-05
> **Document status:** `DRAFT`

---

## Document Metadata

| Field                  | Value                                    |
|------------------------|------------------------------------------|
| **Document ID**        | `STRS-FMSWD-001`                         |
| **Project**            | FM Spectrum, Waterfall and Channel Detection (RTL-SDR → Raspberry Pi) · acronym FMSWD |
| **Organization**       | GCPDS — Universidad Nacional de Colombia |
| **Version**            | 2.0.1                                    |
| **Classification**     | `PUBLIC`                                 |
| **Author(s)**          | D. Ramírez (Stakeholder / author)        |
| **Reviewer(s)**        | GCPDS lab lead (reviewer and approver)   |
| **Approver(s)**        | GCPDS lab lead (reviewer and approver)   |

### Companion Documents

| Document ID            | Title                                    | Relationship                    |
|------------------------|------------------------------------------|---------------------------------|
| `SYRS-FMSWD-001`      | System Requirements Specification        | Derived per-measurand technical specification (G0 pair) |
| `S1-FMSWD-001`        | S1 design document                       | Software design output (S1)     |

> **Note:** The StRS is the system-level view: all subsystems, all frequency bands,
> all measurement types. It merges what used to be a separate hardware-constraints
> document (COTS platform envelope, §1.6/§2.6/§2.7 and the HWC- blocks) and carries
> compliance traceability inline on every block instead of a standalone compliance
> matrix. The SyRS derives per-measurand technical detail from this document; every
> stakeholder requirement (STK-) must be covered by at least one SyRS specification.

### Change Log

| Version | Date       | Author       | Change Description               |
|---------|------------|--------------|----------------------------------|
| 0.1.0   | 2026-11-05 | D. Ramírez   | Initial creation from Build Package v2.0.0 |
| 0.2.0   | 2026-11-05 | D. Ramírez   | Version bump from Build Package v2.0.1 |

---

## 1. Introduction

### 1.1 Purpose

This document specifies the stakeholder requirements for the FM Spectrum, Waterfall and Channel Detection system (FMSWD). Its audience is the design team, lab engineers, students, and the GCPDS lab lead who reviews and approves the requirements.

### 1.2 Scope

FMSWD: an RTL-SDR on a Raspberry Pi captures a fixed 2 MHz slice of the commercial FM band (default centre 98.0 MHz), computes its power spectrum, keeps a one-minute waterfall and detects which of the 10 FM channels in the slice are on air. A browser UI on the same LAN shows the three views live. New standalone system with two services: a DSP service on the Raspberry Pi and a UI service in the browser.

This cycle is verified with the Mock HAL and the labelled synthetic scenes only, up to VL-1. No real hardware is connected this cycle.

Out of scope: sweeping the whole band, audio demodulation, I/Q recording, calibrated dBm or field-strength measurement, any transmission, user accounts, access from outside the LAN.

Future work, not a requirement of this Build Package: an ML model that performs spectral localisation of the emitters. It is recorded here so it is not lost; nothing in this cycle depends on it.

### 1.3 Definitions, Acronyms, and Abbreviations

| Term       | Definition                                              |
|------------|---------------------------------------------------------|
| StRS       | Stakeholder Requirements Specification (this document)  |
| SyRS       | System Requirements Specification — companion document  |
| FMSWD      | FM Spectrum, Waterfall and Channel Detection             |
| FM         | Frequency Modulation                                    |
| FFT        | Fast Fourier Transform                                  |
| DSP        | Digital Signal Processing                               |
| UI         | User Interface                                          |
| COTS       | Commercial Off-The-Shelf                                |
| dBFS       | Decibels relative to full scale                         |
| I/Q        | In-phase / Quadrature                                   |
| RBW        | Resolution Bandwidth                                    |
| LAN        | Local Area Network                                      |
| ADC        | Analogue-to-Digital Converter                           |
| TCXO       | Temperature-Compensated Crystal Oscillator              |
| HAL        | Hardware Abstraction Layer                              |
| VL-0       | Verification Level 0 (golden vectors)                   |
| VL-1       | Verification Level 1 (labelled scenes)                  |

### 1.4 References

| Ref ID     | Document                                                | Version / Date  |
|------------|---------------------------------------------------------|-----------------|
| `REF-001`  | RTL-SDR Blog V4 user guide                              | 2023            |
| `REF-002`  | Raspberry Pi 4 Model B product brief                    | 2024            |
| `REF-003`  | ITU Radio Regulations Vol. 1                            | Edition 2024    |
| `REF-004`  | ITU-R BS.450-4                                          | 2019            |
| `REF-005`  | 47 CFR Part 73 §73.201                                  | —               |
| `REF-006`  | Welch 1967, IEEE Trans. Audio Electroacoust. 15(2)      | 1967            |
| `REF-007`  | Harris 1978, Proc. IEEE 66(1)                           | 1978            |
| `REF-008`  | ISO/IEC 25010:2023                                      | 2023            |

### 1.5 Document Overview

§2 describes the overall system: perspective, functions, users, constraints, assumptions, block diagram and bus topology. §3 contains the specific requirements as NRM-, STK- and HWC- blocks. §4 covers external interfaces. §5 covers non-functional requirements. §6 provides the traceability matrix.

### 1.6 Hardware Inventory

| Component ID | Component Name                        | Role in System                              | Manufacturer    | Part Number      |
|-------------|---------------------------------------|---------------------------------------------|-----------------|------------------|
| `HW-001`    | RTL-SDR Blog V4 (RTL2832U + R828D)   | RF front end, tuner, 8-bit I/Q ADC (receive only) | RTL-SDR Blog    | RTLSDR-BLOG-V4  |
| `HW-002`    | RTL-SDR Blog dipole antenna kit       | VHF receive antenna                         | RTL-SDR Blog    | DIPOLE-KIT       |
| `HW-003`    | Raspberry Pi 4 Model B, 4 GB         | Edge node: runs the DSP service and serves the UI | Raspberry Pi Foundation | RPI4-4GB |
| `HW-004`    | User laptop or PC with a browser      | Runs the UI over the LAN                    | generic         | generic          |

---

## 2. Overall System Description

### 2.1 Product Perspective

New standalone system. Two services: a DSP service on the Raspberry Pi (HW-003) and a UI service in the browser (HW-004). The RTL-SDR (HW-001) with antenna (HW-002) captures RF; the DSP service processes the samples and sends results over WebSocket to the browser UI.

### 2.2 Product Functions

- Live power spectrum of a fixed 2 MHz slice of the commercial FM band.
- Waterfall of the last 60 s of spectra.
- Per-channel detection: which of the 10 FM channels in the slice are on air, with occupancy over the last 60 s.
- Browser UI showing the three views live on a single page.

### 2.3 User Characteristics

| User Type       | Description                                          | Technical Level |
|-----------------|------------------------------------------------------|-----------------|
| Lab engineers   | Start the services, read the views, run the tests    | `TECHNICAL`     |
| Students        | Read the views                                       | `BASIC`         |

### 2.4 Constraints

The system is constrained by the COTS hardware platform: the RTL-SDR Blog V4 (HW-001) limits the tuning range, sample rate, I/Q resolution and introduces a DC spike; the Raspberry Pi 4 (HW-003) limits compute. Detailed hardware limits appear as HWC- blocks in §3.

### 2.5 Assumptions and Dependencies

- The Raspberry Pi runs only this software.
- The UI browser is a recent Chromium or Firefox on the same LAN.

### 2.6 Block Diagram

```
HW-002 (dipole antenna) ──RF analog──▶ HW-001 (RTL-SDR V4)
                                           │
                                       USB 2.0 bulk
                                           │
                                           ▼
                                      HW-003 (Raspberry Pi 4)
                                      [DSP service]
                                           │
                                   Ethernet / Wi-Fi LAN
                                   (HTTP + WebSocket)
                                           │
                                           ▼
                                      HW-004 (browser)
                                      [UI service]
```

### 2.7 Bus and Interface Topology

| From       | To         | Bus/Protocol      | Data Rate (theoretical)                    | Data Rate (sustained) |
|------------|------------|-------------------|--------------------------------------------|-----------------------|
| `HW-002`   | `HW-001`   | SMA coaxial (RF analog) | —                                     | —                     |
| `HW-001`   | `HW-003`   | USB 2.0 bulk      | 480 Mbit/s                                 | 4.8 MB/s at 2.4 MS/s × 2 B |
| `HW-003`   | `HW-004`   | Ethernet or Wi-Fi LAN (HTTP and WebSocket) | —                     | —                     |

---

## 3. Specific Requirements

### Block ID Convention

Each block uses a type prefix that names what the block is:

| Type | Prefix | Meaning | Regex |
|------|--------|---------|-------|
| Normative obligation | `NRM` | A binding obligation from a normative source (ITU, ICNIRP, ANE, GUM, ISO…) | `^NRM-[A-Z]{2,8}-\d{3}$` |
| COTS constraint | `HWC` | A parametric limit of the selected hardware platform | `^HWC-[A-Z]{2,4}-\d{3}$` |
| Stakeholder requirement | `STK` | A functional or non-functional stakeholder need | `^STK-[A-Z]{2,4}-\d{3}$` |

---

### 3.1 Normative Obligations: Radio Regulations

---

**`NRM-ITU-001` — Stay inside the Region 2 BROADCASTING allocation 88–108 MHz**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Priority**           | `MUST`                                                    |
| **Status**             | `PROPOSED`                                                |
| **Standard(s)**        | ITU Radio Regulations                                     |
| **Clause**             | Article 5, Table of Frequency Allocations, 88–108 MHz (Region 2) |
| **Compliance**         | `PENDING`                                                 |

**Description:**
The system SHALL stay inside the Region 2 BROADCASTING allocation 88–108 MHz.

**Acceptance Criteria:**

1. [ ] The observed slice lies within 88.0–108.0 MHz for every allowed centre.

---

**`NRM-FCC-001` — Use the FM channel raster**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Priority**           | `MUST`                                                    |
| **Status**             | `PROPOSED`                                                |
| **Standard(s)**        | 47 CFR Part 73                                            |
| **Clause**             | §73.201 Numerical designation of FM broadcast channels    |
| **Compliance**         | `PENDING`                                                 |

**Description:**
The system SHALL use the FM channel raster: channels of 200 kHz with centres on odd tenths of a MHz.

**Acceptance Criteria:**

1. [ ] The 10 channel centres of the slice are fc − 0.9 + 0.2·n MHz, n = 0…9.

---

**`NRM-ITU-002` — Resolve FM emissions with max. deviation ±75 kHz**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Priority**           | `SHOULD`                                                  |
| **Status**             | `PROPOSED`                                                |
| **Standard(s)**        | ITU-R BS.450-4                                            |
| **Clause**             | Annex 1, maximum frequency deviation                      |
| **Compliance**         | `PENDING`                                                 |

**Description:**
The system SHOULD resolve FM emissions with maximum deviation ±75 kHz.

**Acceptance Criteria:**

1. [ ] RBW ≤ 25 kHz (one third of 75 kHz).

---

### 3.2 Stakeholder Requirements: DSP

---

**`STK-DSP-001` — Live power spectrum**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                              |
| **Priority**           | `MUST`                                                    |
| **Status**             | `PROPOSED`                                                |
| **Verification**       | `TEST`                                                    |
| **Standard(s)**        | —                                                         |
| **Clause**             | —                                                         |
| **Compliance**         | `PENDING`                                                 |
| **Dependencies**       | `NRM-ITU-001`, `NRM-ITU-002`, `HWC-SDR-001`, `HWC-SDR-002` |

**Description:**
The system SHALL provide a live power spectrum of the 2 MHz slice, updated every 0.5 s.

**Acceptance Criteria:**

1. [ ] One spectrum per 0.5 s.
2. [ ] Golden vector GV-2 peaks at 0.0 ± 0.1 dBFS.

---

**`STK-DSP-002` — Waterfall**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                              |
| **Priority**           | `MUST`                                                    |
| **Status**             | `PROPOSED`                                                |
| **Verification**       | `TEST`                                                    |
| **Standard(s)**        | —                                                         |
| **Clause**             | —                                                         |
| **Compliance**         | `PENDING`                                                 |
| **Dependencies**       | `STK-DSP-001`                                             |

**Description:**
The system SHALL provide a waterfall of the last 60 s of spectra.

**Acceptance Criteria:**

1. [ ] 120 rows, newest on top, one row per update.

---

**`STK-DSP-003` — Per-channel detection**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                              |
| **Priority**           | `MUST`                                                    |
| **Status**             | `PROPOSED`                                                |
| **Verification**       | `TEST`                                                    |
| **Standard(s)**        | —                                                         |
| **Clause**             | —                                                         |
| **Compliance**         | `PENDING`                                                 |
| **Dependencies**       | `STK-DSP-001`, `NRM-FCC-001`                              |

**Description:**
The system SHALL provide per-channel detection: occupied or free at every update, and the occupancy (0–1) over the last 60 s.

**Acceptance Criteria:**

1. [ ] Every labelled scene of B.3 gives its expected result.

---

### 3.3 Stakeholder Requirements: UI

---

**`STK-UI-001` — UI latency**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `NON_FUNCTIONAL`                                          |
| **Priority**           | `MUST`                                                    |
| **Status**             | `PROPOSED`                                                |
| **Verification**       | `TEST`                                                    |
| **Standard(s)**        | —                                                         |
| **Clause**             | —                                                         |
| **Compliance**         | `PENDING`                                                 |
| **Dependencies**       | `STK-DSP-001`, `HWC-RPI-001`                              |

**Description:**
The system SHALL show each update within 1.0 s of the end of its capture.

**Acceptance Criteria:**

1. [ ] Capture end → UI render latency p95 ≤ 1.0 s over 60 s.

---

**`STK-UI-002` — One browser page with three views**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                              |
| **Priority**           | `SHOULD`                                                  |
| **Status**             | `PROPOSED`                                                |
| **Verification**       | `DEMONSTRATION`                                           |
| **Standard(s)**        | —                                                         |
| **Clause**             | —                                                         |
| **Compliance**         | `PENDING`                                                 |
| **Dependencies**       | `STK-DSP-001`, `STK-DSP-002`, `STK-DSP-003`              |

**Description:**
The system SHOULD provide one browser page with the three views: spectrum, waterfall, channel table.

**Acceptance Criteria:**

1. [ ] Page loads on a LAN browser.
2. [ ] The three views update with no reload.

---

### 3.4 Stakeholder Requirements: Software Platform

---

**`STK-SW-001` — Software platform constraint**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `CONSTRAINT`                                              |
| **Priority**           | `MUST`                                                    |
| **Status**             | `PROPOSED`                                                |
| **Verification**       | `INSPECTION`                                              |
| **Standard(s)**        | —                                                         |
| **Clause**             | —                                                         |
| **Compliance**         | `PENDING`                                                 |
| **Dependencies**       | `HWC-RPI-001`                                             |

**Description:**
The DSP service SHALL be in Python ≥ 3.12; the UI service SHALL be in TypeScript in the browser.

**Acceptance Criteria:**

1. [ ] Manifests: Python ≥ 3.12 for the DSP service, TypeScript for the UI.

---

### 3.5 Platform Constraints: SDR Front End

---

**`HWC-SDR-001` — Tuning range**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Component**          | `HW-001`                                                  |
| **Parameter**          | Tuning range                                              |
| **Limit type**         | `RANGE`                                                   |
| **Value min**          | 500 kHz                                                   |
| **Value max**          | 1.766 GHz                                                 |
| **Source**             | `DATASHEET`                                               |
| **Source ref**         | `REF-001` §Specifications                                 |
| **Impact**             | `HARD`                                                    |
| **Status**             | `CONFIRMED`                                               |
| **Standard(s)**        | —                                                         |
| **Clause**             | —                                                         |
| **Compliance**         | `PENDING`                                                 |

---

**`HWC-SDR-002` — Complex sample rate without dropped samples**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Component**          | `HW-001`                                                  |
| **Parameter**          | Complex sample rate without dropped samples               |
| **Limit type**         | `MAX`                                                     |
| **Value**              | 2.4 MS/s                                                  |
| **Source**             | `DATASHEET`                                               |
| **Source ref**         | `REF-001` §Specifications                                 |
| **Impact**             | `HARD`                                                    |
| **Status**             | `CONFIRMED`                                               |
| **Standard(s)**        | —                                                         |
| **Clause**             | —                                                         |
| **Compliance**         | `PENDING`                                                 |

---

**`HWC-SDR-003` — I/Q resolution**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Component**          | `HW-001`                                                  |
| **Parameter**          | I/Q resolution                                            |
| **Limit type**         | `FIXED`                                                   |
| **Value**              | 8 bit unsigned per I and Q, interleaved                   |
| **Source**             | `DATASHEET`                                               |
| **Source ref**         | `REF-001` §Specifications                                 |
| **Impact**             | `HARD`                                                    |
| **Status**             | `CONFIRMED`                                               |
| **Standard(s)**        | —                                                         |
| **Clause**             | —                                                         |
| **Compliance**         | `PENDING`                                                 |

---

**`HWC-SDR-004` — DC spike at the tuned centre**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Component**          | `HW-001`                                                  |
| **Parameter**          | DC spike at the tuned centre                              |
| **Limit type**         | `FIXED`                                                   |
| **Value**              | Present at every centre frequency                         |
| **Source**             | `DATASHEET`                                               |
| **Source ref**         | `REF-001` §Known issues                                   |
| **Impact**             | `SOFT`                                                    |
| **Status**             | `PRELIMINARY`                                             |
| **Standard(s)**        | —                                                         |
| **Clause**             | —                                                         |
| **Compliance**         | `PENDING`                                                 |

---

**`HWC-SDR-005` — Reference oscillator**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Component**          | `HW-001`                                                  |
| **Parameter**          | Reference oscillator                                      |
| **Limit type**         | `FIXED`                                                   |
| **Value**              | 1 ppm TCXO                                                |
| **Source**             | `DATASHEET`                                               |
| **Source ref**         | `REF-001` §Specifications                                 |
| **Impact**             | `INFORMATIONAL`                                           |
| **Status**             | `CONFIRMED`                                               |
| **Standard(s)**        | —                                                         |
| **Clause**             | —                                                         |
| **Compliance**         | `PENDING`                                                 |

---

### 3.6 Platform Constraints: Edge Compute

---

**`HWC-RPI-001` — Edge compute**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Component**          | `HW-003`                                                  |
| **Parameter**          | Edge compute                                              |
| **Limit type**         | `FIXED`                                                   |
| **Value**              | 4 cores ARM Cortex-A72 64-bit / 4 GB / Raspberry Pi OS 64-bit |
| **Source**             | `DATASHEET`                                               |
| **Source ref**         | `REF-002` §Specifications                                 |
| **Impact**             | `INFORMATIONAL`                                           |
| **Status**             | `CONFIRMED`                                               |
| **Standard(s)**        | —                                                         |
| **Clause**             | —                                                         |
| **Compliance**         | `PENDING`                                                 |

---

## 4. External Interface Requirements

### 4.1 User Interfaces

One browser page with three views: spectrum line plot, waterfall canvas, channel table. The browser is a recent Chromium or Firefox on the same LAN as HW-003 (see STK-UI-002).

### 4.2 Hardware Interfaces

HW-002 → HW-001: SMA coaxial (RF analog). HW-001 → HW-003: USB 2.0 bulk, 4.8 MB/s at 2.4 MS/s × 2 B. See §2.7.

### 4.3 Software Interfaces

DSP service: Python ≥ 3.12 + numpy, one SDR access path behind the HAL. UI service: TypeScript in the browser (see STK-SW-001).

### 4.4 Communication Interfaces

HW-003 → HW-004: Ethernet or Wi-Fi LAN (HTTP and WebSocket). The DSP service sends one JSON message per update over WebSocket.

---

## 5. Non-Functional Requirements

### 5.1 Performance

Capture end → UI render latency p95 ≤ 1.0 s over 60 s (see STK-UI-001).

### 5.2 Security

Not specified in the Build Package.

### 5.3 Reliability / Availability

Not specified in the Build Package.

### 5.4 Maintainability

Not specified in the Build Package.

### 5.5 Portability

Not specified in the Build Package.

---

## 6. Traceability

| Block ID           | Business Objective | Standard Ref                          | Compliance  | Test Case | Component     |
|--------------------|--------------------|---------------------------------------|-------------|-----------|---------------|
| `NRM-ITU-001`      | OBJ-001            | ITU Radio Regulations Art. 5          | `PENDING`   | —         | —             |
| `NRM-FCC-001`      | OBJ-003            | 47 CFR Part 73 §73.201               | `PENDING`   | —         | —             |
| `NRM-ITU-002`      | OBJ-001            | ITU-R BS.450-4 Annex 1               | `PENDING`   | —         | —             |
| `STK-DSP-001`      | OBJ-001            | —                                     | `PENDING`   | —         | —             |
| `STK-DSP-002`      | OBJ-002            | —                                     | `PENDING`   | —         | —             |
| `STK-DSP-003`      | OBJ-003            | —                                     | `PENDING`   | —         | —             |
| `STK-UI-001`       | OBJ-001            | —                                     | `PENDING`   | —         | —             |
| `STK-UI-002`       | OBJ-001, OBJ-002, OBJ-003 | —                              | `PENDING`   | —         | —             |
| `STK-SW-001`       | OBJ-004            | —                                     | `PENDING`   | —         | —             |
| `HWC-SDR-001`      | —                  | —                                     | `PENDING`   | —         | `HW-001`      |
| `HWC-SDR-002`      | —                  | —                                     | `PENDING`   | —         | `HW-001`      |
| `HWC-SDR-003`      | —                  | —                                     | `PENDING`   | —         | `HW-001`      |
| `HWC-SDR-004`      | —                  | —                                     | `PENDING`   | —         | `HW-001`      |
| `HWC-SDR-005`      | —                  | —                                     | `PENDING`   | —         | `HW-001`      |
| `HWC-RPI-001`      | —                  | —                                     | `PENDING`   | —         | `HW-003`      |

> Every block under §3 must appear in this table.

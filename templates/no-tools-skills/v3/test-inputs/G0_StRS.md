# [PROJECT: Real-Time FM Spectrogram (HackRF One)]

## Stakeholder Requirements Specification (StRS)

> **Standard:** IEEE/ISO/IEC 29148:2018 §9.4 — *Stakeholder requirements specification.*
>
> **Template version:** 4.0.0  
> **Creation date:** 2026-11-01  
> **Last modified:** 2026-11-01  
> **Document status:** `APPROVED`

---

## Document Metadata

| Field                  | Value                                    |
|------------------------|------------------------------------------|
| **Document ID**        | `STRS-FMSPEC-001`                        |
| **Project**            | Real-Time FM Spectrogram (HackRF One)    |
| **Organization**       | GCPDS — Universidad Nacional de Colombia |
| **Version**            | 1.0.0                                    |
| **Classification**     | `PUBLIC`                                 |
| **Author(s)**          | D. Ramírez (stakeholder)                 |
| **Reviewer(s)**        | GCPDS lab lead (reviewer)                |
| **Approver(s)**        | GCPDS lab lead (approver)                |

### Companion Documents

| Document ID        | Title                                    | Relationship                                  |
|--------------------|------------------------------------------|-----------------------------------------------|
| `SYRS-FMSPEC-001`  | System Requirements Specification        | Derived per-measurand technical specification (G0 pair) |
| `S1-FMSPEC-001`    | Layered Architecture Design (V-SIL v3 S1) | Design output (S1, reviewed at G1)            |

### Change Log

| Version | Date       | Author     | Change Description                         |
|---------|------------|------------|--------------------------------------------|
| 1.0.0   | 2026-11-01 | D. Ramírez | Normalised from Build Package FMSPEC (S0)   |

---

## 1. Introduction

### 1.1 Purpose

This document specifies the stakeholder requirements, normative obligations, and COTS
hardware constraints of a real-time FM-band spectrogram. Audience: the V-SIL design team
(S1), reviewers (G1), implementers (S2), and verifiers (G2).

### 1.2 Scope

The system receives the commercial FM broadcast band (88–108 MHz) with a HackRF One and
shows a live waterfall spectrogram on the host screen. It does NOT demodulate audio, does
NOT record I/Q to disk, does NOT perform calibrated (dBm) field-strength measurement, and
does NOT transmit. Benefit: a teaching and lab tool to observe FM band occupancy live.

### 1.3 Definitions, Acronyms, and Abbreviations

| Term       | Definition                                                         |
|------------|--------------------------------------------------------------------|
| StRS       | Stakeholder Requirements Specification (this document)             |
| SyRS       | System Requirements Specification — companion document             |
| SDR        | Software-Defined Radio                                             |
| dBFS       | Decibels relative to the full scale of the complex 8-bit ADC (0 dBFS = full-scale complex sinusoid) |
| RBW        | Resolution bandwidth — equivalent noise bandwidth of one FFT bin    |
| Waterfall  | Spectrogram display: time on the vertical axis, frequency horizontal, power as colour |
| Overflow   | Host failed to consume USB samples in time; samples are lost (libhackrf/GNU Radio reports it) |

### 1.4 References

| Ref ID     | Document                                                            | Version / Date  |
|------------|---------------------------------------------------------------------|-----------------|
| `REF-001`  | Great Scott Gadgets, *HackRF One* hardware documentation            | 2024.02.1       |
| `REF-002`  | Great Scott Gadgets, *libhackrf* API (`hackrf.h`)                   | 2024.02.1       |
| `REF-003`  | Great Scott Gadgets, *ANT500* product documentation                 | 2023            |
| `REF-004`  | ITU Radio Regulations, Volume 1 (Articles)                          | Edition 2024    |
| `REF-005`  | ITU-R BS.450-4, *Transmission standards for FM sound broadcasting at VHF* | 2019      |
| `REF-006`  | USB Implementers Forum, *Universal Serial Bus Specification Revision 2.0* | 2000      |

### 1.5 Document Overview

§1.6 lists the COTS hardware; §2 describes the system context, constraints, block diagram
and bus topology; §3 holds the NRM-, STK- and HWC- blocks; §4–§5 summarise interfaces and
non-functional requirements by reference to §3; §6 is the traceability table.

### 1.6 Hardware Inventory

| Component ID | Component Name        | Role in System                     | Manufacturer         | Part Number |
|-------------|-----------------------|------------------------------------|----------------------|-------------|
| `HW-001`    | HackRF One            | RF front end, tuner and 8-bit I/Q ADC (receive only) | Great Scott Gadgets | HACKRF-ONE |
| `HW-002`    | ANT500 telescopic antenna | VHF receive antenna            | Great Scott Gadgets  | ANT500      |
| `HW-003`    | Lab host PC           | Runs all software; drives the display | Generic x86-64     | 4-core / 8 GB / USB 2.0 |

---

## 2. Overall System Description

### 2.1 Product Perspective

New, standalone system. No interaction with other systems besides the host operating
system and the COTS hardware listed in §1.6.

### 2.2 Product Functions

- Acquire complex baseband I/Q around the FM band from the HackRF One.
- Estimate the power spectrum of each time slice.
- Render a scrolling waterfall with a frequency axis in MHz and a dBFS colour scale.
- Let the operator adjust RF gain and the colour dynamic range at runtime.

### 2.3 User Characteristics

| User Type       | Description                                        | Technical Level |
|-----------------|----------------------------------------------------|-----------------|
| Student         | Observes the FM band during lab sessions           | `BASIC`         |
| Lab engineer    | Starts the system, tunes gain, runs soak tests     | `TECHNICAL`     |

### 2.4 Constraints

Software only, on the COTS hardware of §1.6. Python 3.10+ with GNU Radio 3.10 or
libhackrf. Receive-only operation. The 20 MHz span needed for 88–108 MHz sits at the
HackRF maximum sample rate and near the USB 2.0 sustained-throughput ceiling (HWC blocks).

### 2.5 Assumptions and Dependencies

- Antenna and HackRF are in a location with line of sight to local FM transmitters.
- The host runs no other heavy USB or CPU load during operation.
- HackRF firmware and libhackrf versions per `REF-002` are installed.

### 2.6 Block Diagram

```
[HW-002 ANT500] --SMA (RF, 50 Ω)--> [HW-001 HackRF One] --USB 2.0 HS (int8 I/Q)--> [HW-003 Host PC] --> display
```

### 2.7 Bus and Interface Topology

| From     | To       | Bus/Protocol          | Data Rate (theoretical) | Data Rate (sustained) |
|----------|----------|-----------------------|-------------------------|-----------------------|
| `HW-002` | `HW-001` | SMA coaxial, RF analog | n/a                     | n/a                   |
| `HW-001` | `HW-003` | USB 2.0 High-Speed bulk | 480 Mbit/s             | ≈ 40 MB/s (= 20 MS/s × 2 B) |

---

## 3. Specific Requirements

### 3.1 Normative Obligations: ITU

---

**`NRM-ITU-001` — FM broadcasting band of interest is 88–108 MHz (Region 2)**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Standard(s)**        | ITU Radio Regulations (`REF-004`)                         |
| **Clause**             | Article 5, Table of Frequency Allocations, 88–108 MHz (Region 2) |
| **Compliance**         | `COMPLIANT`                                               |

**Description:**  
The system SHALL take the Region 2 BROADCASTING allocation 88–108 MHz as the band to be
observed.

**Acceptance Criteria:**

1. [ ] The observed span covers 88.0 MHz to 108.0 MHz.

---

**`NRM-ITU-002` — No unnecessary transmissions**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Standard(s)**        | ITU Radio Regulations (`REF-004`)                         |
| **Clause**             | No. 15.1                                                  |
| **Compliance**         | `COMPLIANT`                                               |

**Description:**  
The system SHALL NOT radiate; the SDR SHALL be operated in receive mode only.

**Acceptance Criteria:**

1. [ ] No code path enables the HackRF transmit mode.

---

**`NRM-ITU-003` — FM emission deviation of ±75 kHz**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Priority**           | `SHOULD`                                                  |
| **Status**             | `APPROVED`                                                |
| **Standard(s)**        | ITU-R BS.450-4 (`REF-005`)                                |
| **Clause**             | Annex 1, maximum frequency deviation                      |
| **Compliance**         | `COMPLIANT`                                               |

**Description:**  
The system SHOULD resolve FM emissions with a maximum frequency deviation of ±75 kHz as
distinct spectral features.

**Acceptance Criteria:**

1. [ ] Resolution bandwidth is at most one third of the 75 kHz deviation (≤ 25 kHz).

---

### 3.2 Stakeholder Requirements: Spectrogram

---

**`STK-SPEC-001` — Live waterfall of the full FM band**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                              |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `DEMONSTRATION`                                           |
| **Standard(s)**        | ITU Radio Regulations (`REF-004`)                         |
| **Clause**             | Article 5 (88–108 MHz, Region 2)                          |
| **Compliance**         | `COMPLIANT`                                               |
| **Dependencies**       | `NRM-ITU-001`, `HWC-SDR-001`, `HWC-SDR-002`               |

**Description:**  
The system SHALL display a live, scrolling waterfall spectrogram spanning 88.0–108.0 MHz on
the host screen.

**Acceptance Criteria:**

1. [ ] The frequency axis of the waterfall spans at least 88.0 to 108.0 MHz.
2. [ ] Known local FM stations appear at their licensed frequencies within ± 1 FFT bin.

---

**`STK-SPEC-002` — Update rate and latency**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `NON_FUNCTIONAL`                                          |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `TEST`                                                    |
| **Standard(s)**        | —                                                         |
| **Clause**             | —                                                         |
| **Compliance**         | `NOT_APPLICABLE`                                          |
| **Dependencies**       | `STK-SPEC-001`                                            |

**Description:**  
The system SHALL add at least 10 waterfall lines per second and SHALL show an on-air event
on screen within 500 ms of its arrival at the antenna.

**Acceptance Criteria:**

1. [ ] Measured line rate ≥ 10 lines/s over 60 s.
2. [ ] Measured end-to-end latency (sample timestamp → line rendered) ≤ 500 ms (95th percentile).

---

**`STK-SPEC-003` — Adjacent-channel resolution**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `NON_FUNCTIONAL`                                          |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `ANALYSIS`                                                |
| **Standard(s)**        | ITU-R BS.450-4 (`REF-005`)                                |
| **Clause**             | Annex 1, maximum frequency deviation                      |
| **Compliance**         | `COMPLIANT`                                               |
| **Dependencies**       | `NRM-ITU-003`                                             |

**Description:**  
The system SHALL have a resolution bandwidth of 25 kHz or finer so that FM stations 200 kHz
apart are displayed as separate traces.

**Acceptance Criteria:**

1. [ ] Analysis of FFT size, window and sample rate gives RBW ≤ 25 kHz.
2. [ ] Two synthetic tones 200 kHz apart are displayed as two distinct peaks.

---

**`STK-SPEC-004` — Axis units and colour scale**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                              |
| **Priority**           | `SHOULD`                                                  |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `TEST`                                                    |
| **Standard(s)**        | —                                                         |
| **Clause**             | —                                                         |
| **Compliance**         | `NOT_APPLICABLE`                                          |
| **Dependencies**       | `STK-SPEC-001`                                            |

**Description:**  
The system SHOULD label the frequency axis in MHz and map power in dBFS to colour with an
operator-adjustable range, default −80 to 0 dBFS.

**Acceptance Criteria:**

1. [ ] A −20 dBFS synthetic tone is reported at −20 ± 0.5 dBFS.
2. [ ] The colour range can be changed at runtime and defaults to −80…0 dBFS.

---

**`STK-SPEC-005` — Runtime gain control**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                              |
| **Priority**           | `COULD`                                                   |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `DEMONSTRATION`                                           |
| **Standard(s)**        | —                                                         |
| **Clause**             | —                                                         |
| **Compliance**         | `NOT_APPLICABLE`                                          |
| **Dependencies**       | `HWC-SDR-004`                                             |

**Description:**  
The system SHOULD let the operator change LNA and VGA gain while the waterfall is running.

**Acceptance Criteria:**

1. [ ] A gain change is visible in the waterfall within 1 s without restarting.

---

### 3.3 Stakeholder Requirements: Operation

---

**`STK-OPS-001` — Unattended operation without sample loss**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `NON_FUNCTIONAL`                                          |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `TEST`                                                    |
| **Standard(s)**        | —                                                         |
| **Clause**             | —                                                         |
| **Compliance**         | `NOT_APPLICABLE`                                          |
| **Dependencies**       | `HWC-BUS-001`                                             |

**Description:**  
The system SHALL run for 30 minutes unattended with at most 1 sample-overflow event per
10 minutes.

**Acceptance Criteria:**

1. [ ] 30-minute soak test: overflow events ≤ 3 and no crash.

---

**`STK-OPS-002` — Receive-only operation**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `CONSTRAINT`                                              |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `INSPECTION`                                              |
| **Standard(s)**        | ITU Radio Regulations (`REF-004`)                         |
| **Clause**             | No. 15.1                                                  |
| **Compliance**         | `COMPLIANT`                                               |
| **Dependencies**       | `NRM-ITU-002`                                             |

**Description:**  
The system SHALL operate the HackRF One in receive mode only.

**Acceptance Criteria:**

1. [ ] Code inspection finds no call that starts transmission (`hackrf_start_tx` or a GNU Radio sink to the HackRF).

---

**`STK-OPS-003` — Software platform**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `CONSTRAINT`                                              |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `INSPECTION`                                              |
| **Standard(s)**        | —                                                         |
| **Clause**             | —                                                         |
| **Compliance**         | `NOT_APPLICABLE`                                          |
| **Dependencies**       | `HWC-HOST-001`                                            |

**Description:**  
The system SHALL be implemented in Python 3.10 or later, using either GNU Radio 3.10 or
libhackrf for SDR access.

**Acceptance Criteria:**

1. [ ] The dependency list contains only Python ≥ 3.10 and GNU Radio 3.10 or libhackrf (plus pure-Python/numpy libraries).

---

### 3.4 Platform Constraints: SDR

---

**`HWC-SDR-001` — Tuning range**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Component**          | `HW-001`                                                  |
| **Parameter**          | Centre frequency                                          |
| **Limit type**         | `RANGE`                                                   |
| **Value min**          | 1 MHz                                                     |
| **Value max**          | 6 GHz                                                     |
| **Source**             | `DATASHEET`                                               |
| **Source ref**         | `REF-001` §Specifications                                 |
| **Impact**             | `HARD`                                                    |
| **Status**             | `CONFIRMED`                                               |
| **Standard(s)**        | —                                                         |
| **Clause**             | —                                                         |
| **Compliance**         | `NOT_APPLICABLE`                                          |

---

**`HWC-SDR-002` — Sample rate**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Component**          | `HW-001`                                                  |
| **Parameter**          | Complex sample rate (= instantaneous span)                |
| **Limit type**         | `RANGE`                                                   |
| **Value min**          | 2 MS/s                                                    |
| **Value max**          | 20 MS/s                                                   |
| **Source**             | `DATASHEET`                                               |
| **Source ref**         | `REF-001` §Specifications                                 |
| **Impact**             | `HARD`                                                    |
| **Status**             | `CONFIRMED`                                               |
| **Standard(s)**        | —                                                         |
| **Clause**             | —                                                         |
| **Compliance**         | `NOT_APPLICABLE`                                          |

**Notes:**  
The 20 MHz needed for 88–108 MHz is exactly the maximum rate; band edges fall on the
baseband filter roll-off.

---

**`HWC-SDR-003` — ADC resolution**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Component**          | `HW-001`                                                  |
| **Parameter**          | I/Q sample resolution                                     |
| **Limit type**         | `FIXED`                                                   |
| **Value**              | 8 bit signed per I and per Q                              |
| **Source**             | `DATASHEET`                                               |
| **Source ref**         | `REF-001` §Specifications                                 |
| **Impact**             | `HARD`                                                    |
| **Status**             | `CONFIRMED`                                               |
| **Standard(s)**        | —                                                         |
| **Clause**             | —                                                         |
| **Compliance**         | `NOT_APPLICABLE`                                          |

**Notes:**  
Ideal SQNR ≈ 6.02·8 + 1.76 ≈ 49.9 dB bounds the displayed dynamic range per bin before processing gain.

---

**`HWC-SDR-004` — Gain steps**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Component**          | `HW-001`                                                  |
| **Parameter**          | RX gain settings (LNA; VGA)                               |
| **Limit type**         | `ENUM`                                                    |
| **Value**              | LNA 0, 8, 16, 24, 32, 40 dB; VGA 0–62 dB in 2 dB steps    |
| **Source**             | `DRIVER_API`                                              |
| **Source ref**         | `REF-002` `hackrf_set_lna_gain`, `hackrf_set_vga_gain`    |
| **Impact**             | `HARD`                                                    |
| **Status**             | `CONFIRMED`                                               |
| **Standard(s)**        | —                                                         |
| **Clause**             | —                                                         |
| **Compliance**         | `NOT_APPLICABLE`                                          |

---

**`HWC-SDR-005` — DC spike at tuned centre**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Component**          | `HW-001`                                                  |
| **Parameter**          | DC offset artefact at 0 Hz baseband                       |
| **Limit type**         | `FIXED`                                                   |
| **Value**              | Present at every centre frequency (direct-conversion receiver) |
| **Source**             | `DATASHEET`                                               |
| **Source ref**         | `REF-001` §FAQ "DC spike"                                 |
| **Impact**             | `SOFT`                                                    |
| **Status**             | `CONFIRMED`                                               |
| **Standard(s)**        | —                                                         |
| **Clause**             | —                                                         |
| **Compliance**         | `NOT_APPLICABLE`                                          |

**Notes:**  
With a 98 MHz centre the spike falls inside the band; software mitigation required.

---

**`HWC-ANT-001` — Antenna frequency range**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Component**          | `HW-002`                                                  |
| **Parameter**          | Usable frequency range                                    |
| **Limit type**         | `RANGE`                                                   |
| **Value min**          | 75 MHz                                                    |
| **Value max**          | 1 GHz                                                     |
| **Source**             | `DATASHEET`                                               |
| **Source ref**         | `REF-003` §Specifications                                 |
| **Impact**             | `INFORMATIONAL`                                           |
| **Status**             | `CONFIRMED`                                               |
| **Standard(s)**        | —                                                         |
| **Clause**             | —                                                         |
| **Compliance**         | `NOT_APPLICABLE`                                          |

---

### 3.5 Platform Constraints: Bus and Host

---

**`HWC-BUS-001` — USB 2.0 sustained throughput**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Component**          | `HW-003`                                                  |
| **Parameter**          | Sustained USB 2.0 HS bulk throughput HackRF → host        |
| **Limit type**         | `MAX`                                                     |
| **Value**              | ≈ 40 MB/s (20 MS/s × 2 B/sample)                          |
| **Source**             | `DERIVED`                                                 |
| **Source ref**         | `REF-006` §5.8 bulk transfers; `REF-001` §Specifications  |
| **Impact**             | `SOFT`                                                    |
| **Status**             | `PRELIMINARY`                                             |
| **Standard(s)**        | —                                                         |
| **Clause**             | —                                                         |
| **Compliance**         | `NOT_APPLICABLE`                                          |

**Notes:**  
20 MS/s is at the practical ceiling; host USB controller and load decide whether overflows
occur. To be confirmed by measurement (MEASURED) during G2.2.

---

**`HWC-HOST-001` — Host compute and display**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Component**          | `HW-003`                                                  |
| **Parameter**          | CPU cores / RAM / display refresh                         |
| **Limit type**         | `FIXED`                                                   |
| **Value**              | 4 cores x86-64 / 8 GB / 1920×1080 at 60 Hz                |
| **Source**             | `MEASURED`                                                |
| **Source ref**         | `REF-001` §Host requirements; lab inventory sheet         |
| **Impact**             | `INFORMATIONAL`                                           |
| **Status**             | `CONFIRMED`                                               |
| **Standard(s)**        | —                                                         |
| **Clause**             | —                                                         |
| **Compliance**         | `NOT_APPLICABLE`                                          |

---

## 4. External Interface Requirements

### 4.1 User Interfaces

Waterfall window with MHz frequency axis, dBFS colour bar, colour-range control and gain
controls (`STK-SPEC-001`, `STK-SPEC-004`, `STK-SPEC-005`).

### 4.2 Hardware Interfaces

HackRF One over USB 2.0 HS (`HWC-SDR-001`…`HWC-SDR-005`, `HWC-BUS-001`); ANT500 over SMA (`HWC-ANT-001`).

### 4.3 Software Interfaces

GNU Radio 3.10 (gr-osmosdr) or libhackrf (`STK-OPS-003`).

### 4.4 Communication Interfaces

None (standalone).

---

## 5. Non-Functional Requirements

### 5.1 Performance

`STK-SPEC-002`, `STK-SPEC-003`.

### 5.2 Security

Receive-only (`STK-OPS-002`, `NRM-ITU-002`).

### 5.3 Reliability / Availability

`STK-OPS-001`.

### 5.4 Maintainability

Modular, layered software (decided at S1).

### 5.5 Portability

Python 3.10+ on Linux; `STK-OPS-003`.

---

## 6. Traceability

| Block ID       | Business Objective | Standard Ref          | Compliance       | Test Case | Component |
|----------------|--------------------|-----------------------|------------------|-----------|-----------|
| `NRM-ITU-001`  | OBJ-001 observe FM band | ITU RR Art. 5     | `COMPLIANT`      | TC-001    | HW-001    |
| `NRM-ITU-002`  | OBJ-003 safe lab use | ITU RR No. 15.1     | `COMPLIANT`      | TC-008    | HW-001    |
| `NRM-ITU-003`  | OBJ-001 observe FM band | ITU-R BS.450-4    | `COMPLIANT`      | TC-003    | HW-003    |
| `STK-SPEC-001` | OBJ-001 observe FM band | ITU RR Art. 5     | `COMPLIANT`      | TC-001    | HW-001, HW-003 |
| `STK-SPEC-002` | OBJ-002 live feel  | —                     | `NOT_APPLICABLE` | TC-002    | HW-003    |
| `STK-SPEC-003` | OBJ-001 observe FM band | ITU-R BS.450-4    | `COMPLIANT`      | TC-003    | HW-003    |
| `STK-SPEC-004` | OBJ-002 live feel  | —                     | `NOT_APPLICABLE` | TC-004    | HW-003    |
| `STK-SPEC-005` | OBJ-002 live feel  | —                     | `NOT_APPLICABLE` | TC-005    | HW-001    |
| `STK-OPS-001`  | OBJ-003 safe lab use | —                   | `NOT_APPLICABLE` | TC-006    | HW-001, HW-003 |
| `STK-OPS-002`  | OBJ-003 safe lab use | ITU RR No. 15.1     | `COMPLIANT`      | TC-008    | HW-001    |
| `STK-OPS-003`  | OBJ-004 maintainable | —                   | `NOT_APPLICABLE` | TC-009    | HW-003    |
| `HWC-SDR-001`  | OBJ-001 observe FM band | —                 | `NOT_APPLICABLE` | TC-001    | HW-001    |
| `HWC-SDR-002`  | OBJ-001 observe FM band | —                 | `NOT_APPLICABLE` | TC-001    | HW-001    |
| `HWC-SDR-003`  | OBJ-002 live feel  | —                     | `NOT_APPLICABLE` | TC-004    | HW-001    |
| `HWC-SDR-004`  | OBJ-002 live feel  | —                     | `NOT_APPLICABLE` | TC-005    | HW-001    |
| `HWC-SDR-005`  | OBJ-001 observe FM band | —                 | `NOT_APPLICABLE` | TC-007    | HW-001    |
| `HWC-ANT-001`  | OBJ-001 observe FM band | —                 | `NOT_APPLICABLE` | TC-001    | HW-002    |
| `HWC-BUS-001`  | OBJ-003 safe lab use | —                   | `NOT_APPLICABLE` | TC-006    | HW-003    |
| `HWC-HOST-001` | OBJ-002 live feel  | —                     | `NOT_APPLICABLE` | TC-002    | HW-003    |

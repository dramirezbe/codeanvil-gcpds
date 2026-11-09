# PROJECT: Edge Sensor — ANE Spectrum Monitoring System

## System Requirements Specification (SyRS)

> **Standard:** IEEE/ISO/IEC 29148:2018 §9.5 — *System requirements specification.*
>
> **Derived from:** STRS-ANE-EDGE-001 (Stakeholder Requirements Specification)

## Document Metadata

| Field                  | Value                                                      |
|------------------------|------------------------------------------------------------|
| **Document ID**        | `SYRS-ANE-EDGE-001`                                        |
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
| `STRS-ANE-EDGE-001`    | Edge Sensor Stakeholder Requirements Specification       | Parent stakeholder requirements (G0 pair) |

### Change Log

| Version | Date       | Author                 | Change Description                          |
|---------|------------|------------------------|---------------------------------------------|
| 2.0.0   | 2026-10-22 | Migration              | Initial SyRS per IEEE 29148 §9.5 — derived from StRS 2.0.0 |

---

## 1. Introduction

### 1.1 Purpose

This System Requirements Specification derives per-measurand technical requirements from the stakeholder requirements in STRS-ANE-EDGE-001. Each SYS- specification names the measurand, method, and the StRS blocks it discharges.

### 1.2 Scope

Scope covers measurement, detection, storage, connectivity, power, monitoring, and calibration specifications of the ANE edge sensor node.

### 1.3 Definitions, Acronyms, and Abbreviations

| Term | Definition |
|------|------------|
| Measurand | Quantity intended to be measured |
| GUM | Guide to the Expression of Uncertainty in Measurement (JCGM 100:2008) |
| RBW | Resolution bandwidth |

### 1.4 References

| Ref ID     | Document                                                               | Version / Date      |
|------------|------------------------------------------------------------------------|---------------------|
| `REF-001`  | ITU-R SM.1537 — Automation and requirements of monitoring stations     | In force            |
| `REF-002`  | ITU-R SM.1138 — Monitoring sensitivity and selectivity                 | In force            |
| `REF-003`  | ITU-T K.113 — Electric field measurement in urban environments         | In force            |
| `REF-004`  | ITU-T K.100 — Assessment of human exposure to electromagnetic fields   | In force            |
| `REF-GUM`  | JCGM 100:2008 — Evaluation of measurement data (GUM)                   | 2008                |
| `REF-007`  | IEEE/ISO/IEC 29148:2018 — Requirements engineering                     | 2018                |

### 1.5 Document Overview

Section 2 defines the measurement framework. Section 3 holds the SYS- specifications. Sections 4–6 hold correction chains, uncertainty budgets, and field protocols. Section 7 presents traceability.

---

## 2. Measurement Framework

### 2.1 Measurand Catalog

| Measurand ID | Quantity                          | Unit     |
|--------------|-----------------------------------|----------|
| `M-001`      | Ambient EM environment            | dBµV/m   |
| `M-002`      | Monitored frequency range         | Hz       |
| `M-003`      | Spectral density (PSD)            | dBm/Hz   |
| `M-004`      | Occupied bandwidth                | Hz       |
| `M-005`      | Channel power                     | dBm      |
| `M-006`      | Audio / RDS content               | —        |
| `M-007`      | Electric field strength           | dBµV/m   |
| `M-008`      | Noise floor (DANL)                | dBm      |
| `M-009`      | Position and time fix            | deg / ns |
| `M-010`      | Energy budget state               | Wh       |

### 2.2 Method Selection and Rationale

Measurement methods follow ITU-R SM.1537 (station automation and surveys) and ITU-R SM.1138 (sensitivity/selectivity). Field-strength methods follow ITU-T K.113. Uncertainty evaluation follows JCGM 100:2008 (GUM).

### 2.3 Normative-to-Method Mapping

| Standard(s)           | Clause | Measurand | Method                          |
|-----------------------|--------|-----------|---------------------------------|
| ITU-R SM.1537         | §5     | `M-001`–`M-006` | Automated survey sweeps  |
| ITU-R SM.1138         | §4     | `M-008`   | Sensitivity / selectivity characterization |
| ITU-T K.113           | §4     | `M-007`   | Calibrated field-strength measurement |
| JCGM 100:2008 (GUM)   | §4     | all       | Uncertainty budgets              |

---

## 3. System Requirements

**`SYS-RF-001` — EMC environment measurement**

| Field | Value |
|-------|-------|
| **Type** | `MEASUREMENT` |
| **Parameter** | Ambient EM environment at the sensor site |
| **Method** | Wideband survey per ITU-R SM.1537 |
| **Traces to** | `STK-EMC-001` |
| **Standard(s)** | ITU-R SM.1537 |

**Acceptance Criteria:**

1. [ ] Ambient survey completes and stores results for the configured dwell time.

**`SYS-RF-002` — Frequency-range coverage survey**

| Field | Value |
|-------|-------|
| **Type** | `MEASUREMENT` |
| **Parameter** | Monitored frequency range coverage |
| **Method** | Band survey per ITU-R SM.1537 |
| **Traces to** | `STK-RNG-001` |
| **Standard(s)** | ITU-R SM.1537 |

**Acceptance Criteria:**

1. [ ] Configured band is fully covered at the required RBW.

**`SYS-RF-003` — Real-time bandwidth monitoring**

| Field | Value |
|-------|-------|
| **Type** | `MEASUREMENT` |
| **Parameter** | Real-time instantaneous bandwidth |
| **Method** | Gapless capture at the ADC rate |
| **Traces to** | `STK-RNG-002` |
| **Standard(s)** | ITU-R SM.1537 |

**Acceptance Criteria:**

1. [ ] Real-time span meets the configured bandwidth without gaps.

**`SYS-DSP-001` — Frequency-range and resolution configuration**

| Field | Value |
|-------|-------|
| **Type** | `CONTROL` |
| **Parameter** | Start/stop frequency and RBW steps |
| **Method** | Tuner + decimation configuration |
| **Traces to** | `STK-PAR-001`, `STK-PAR-003` |
| **Standard(s)** | ITU-R SM.1537 |

**Acceptance Criteria:**

1. [ ] Operator can set frequency range and resolution steps within hardware limits.

**`SYS-DSP-002` — RBW/VBW configuration**

| Field | Value |
|-------|-------|
| **Type** | `CONTROL` |
| **Parameter** | Resolution and video bandwidth |
| **Method** | FFT length and window selection |
| **Traces to** | `STK-PAR-002`, `STK-PAR-004` |
| **Standard(s)** | ITU-R SM.1537 |

**Acceptance Criteria:**

1. [ ] RBW/VBW combinations apply and are reflected in the next sweep.

**`SYS-NAV-001` — Manual geolocation entry**

| Field | Value |
|-------|-------|
| **Type** | `NAVIGATION` |
| **Parameter** | Sensor latitude/longitude |
| **Method** | Operator entry with range validation |
| **Traces to** | `STK-PAR-005` |
| **Standard(s)** | IEEE/ISO/IEC 29148:2018 |

**Acceptance Criteria:**

1. [ ] Manual coordinates are validated, stored, and attached to measurements.

**`SYS-DSP-003` — Measurement unit conversion**

| Field | Value |
|-------|-------|
| **Type** | `MEASUREMENT` |
| **Parameter** | Reported measurement units |
| **Method** | Deterministic unit conversion on report |
| **Traces to** | `STK-PAR-006` |
| **Standard(s)** | IEEE/ISO/IEC 29148:2018 |

**Acceptance Criteria:**

1. [ ] Reported values convert between configured units without loss of precision.

**`SYS-DSP-004` — Detection threshold configuration**

| Field | Value |
|-------|-------|
| **Type** | `DETECTION` |
| **Parameter** | Analysis and detection thresholds |
| **Method** | CFAR-style thresholding per sweep |
| **Traces to** | `STK-PAR-007` |
| **Standard(s)** | ITU-R SM.1537 |

**Acceptance Criteria:**

1. [ ] Threshold changes apply to subsequent detections.

**`SYS-MEAS-001` — Spectral trace capture**

| Field | Value |
|-------|-------|
| **Type** | `MEASUREMENT` |
| **Parameter** | Spectral traces (PSD) |
| **Method** | Averaged FFT trace per ITU-R SM.1537 |
| **Traces to** | `STK-MED-001` |
| **Standard(s)** | ITU-R SM.1537 |

**Acceptance Criteria:**

1. [ ] Trace capture stores timestamped PSD data with configured averaging.

**`SYS-MEAS-002` — Occupied-bandwidth measurement**

| Field | Value |
|-------|-------|
| **Type** | `MEASUREMENT` |
| **Parameter** | Occupied bandwidth |
| **Method** | Power-percentage bandwidth per ITU-R SM.1537 |
| **Traces to** | `STK-MED-003` |
| **Standard(s)** | ITU-R SM.1537 |

**Acceptance Criteria:**

1. [ ] OBW is reported within the configured power percentage.

**`SYS-MEAS-003` — Channel-power measurement**

| Field | Value |
|-------|-------|
| **Type** | `MEASUREMENT` |
| **Parameter** | Channel power |
| **Method** | Integrated in-band power per ITU-R SM.1537 |
| **Traces to** | `STK-MED-004` |
| **Standard(s)** | ITU-R SM.1537 |

**Acceptance Criteria:**

1. [ ] Channel power integrates over the configured channel mask.

**`SYS-MEAS-004` — RDS decoding in FM**

| Field | Value |
|-------|-------|
| **Type** | `MEASUREMENT` |
| **Parameter** | RDS bits from FM broadcast |
| **Method** | RDS decode on demodulated FM |
| **Traces to** | `STK-MED-005` |
| **Standard(s)** | ITU-R SM.1537 |

**Acceptance Criteria:**

1. [ ] RDS program service fields decode when SNR allows.

**`SYS-MEAS-005` — Analog demodulation measurements**

| Field | Value |
|-------|-------|
| **Type** | `MEASUREMENT` |
| **Parameter** | FM/AM audio and modulation characteristics |
| **Method** | Envelope and quadrature demodulation |
| **Traces to** | `STK-MED-006`, `STK-MED-007` |
| **Standard(s)** | ITU-R SM.1537 |

**Acceptance Criteria:**

1. [ ] Demodulated audio and modulation metrics are produced per sweep.

**`SYS-VER-001` — Intermodulation and interference detection**

| Field | Value |
|-------|-------|
| **Type** | `DETECTION` |
| **Parameter** | Spurious and intermodulation products |
| **Method** | Multi-tone stimulus + spectral comparison |
| **Traces to** | `STK-VER-001`, `STK-VER-002` |
| **Standard(s)** | ITU-R SM.1138 |

**Acceptance Criteria:**

1. [ ] Intermodulation products are detected and flagged above threshold.

**`SYS-VER-002` — Audio extraction for verification**

| Field | Value |
|-------|-------|
| **Type** | `MEASUREMENT` |
| **Parameter** | Audio verification clips |
| **Method** | Demodulate + store bounded audio segment |
| **Traces to** | `STK-SRV-002` |
| **Standard(s)** | IEEE/ISO/IEC 29148:2018 |

**Acceptance Criteria:**

1. [ ] Operator can extract a bounded audio clip for a selected signal.

**`SYS-STO-001` — Measurement data storage**

| Field | Value |
|-------|-------|
| **Type** | `STORAGE` |
| **Parameter** | Historical measurement records |
| **Method** | Local time-series store with retention policy |
| **Traces to** | `STK-ALM-001`, `STK-ALM-003` |
| **Standard(s)** | IEEE/ISO/IEC 29148:2018 |

**Acceptance Criteria:**

1. [ ] Measurements persist locally and survive reboot within retention.

**`SYS-NET-001` — Cellular backhaul link**

| Field | Value |
|-------|-------|
| **Type** | `COMMUNICATION` |
| **Parameter** | 4G/5G data link |
| **Method** | Modem manager with failover |
| **Traces to** | `STK-RED-001` |
| **Standard(s)** | IEEE/ISO/IEC 29148:2018 |

**Acceptance Criteria:**

1. [ ] Sensor reaches the backend over the cellular link when registered.

**`SYS-NET-002` — WiFi link**

| Field | Value |
|-------|-------|
| **Type** | `COMMUNICATION` |
| **Parameter** | WiFi association |
| **Method** | wpa_supplicant station mode |
| **Traces to** | `STK-RED-002` |
| **Standard(s)** | IEEE/ISO/IEC 29148:2018 |

**Acceptance Criteria:**

1. [ ] Sensor associates and obtains an address on the configured WiFi network.

**`SYS-NET-003` — Ethernet fallback and routing**

| Field | Value |
|-------|-------|
| **Type** | `COMMUNICATION` |
| **Parameter** | Wired uplink and route selection |
| **Method** | NetworkManager priority-based routing |
| **Traces to** | `STK-RED-003`, `STK-RED-004` |
| **Standard(s)** | IEEE/ISO/IEC 29148:2018 |

**Acceptance Criteria:**

1. [ ] Traffic uses the highest-priority available uplink.

**`SYS-NET-004` — Remote access and OTA update**

| Field | Value |
|-------|-------|
| **Type** | `CONTROL` |
| **Parameter** | Remote management channel |
| **Method** | SSH + signed OTA package install |
| **Traces to** | `STK-SOP-001` |
| **Standard(s)** | IEEE/ISO/IEC 29148:2018 |

**Acceptance Criteria:**

1. [ ] Operator can reach the sensor remotely and apply a signed update.

**`SYS-NAV-002` — GNSS position and time**

| Field | Value |
|-------|-------|
| **Type** | `NAVIGATION` |
| **Parameter** | GPS position fix and NMEA stream |
| **Method** | GNSS receiver with NMEA parsing |
| **Traces to** | `STK-GPS-001`, `STK-GPS-002` |
| **Standard(s)** | IEEE/ISO/IEC 29148:2018 |

**Acceptance Criteria:**

1. [ ] Fixes meet the configured accuracy when satellites are visible.

**`SYS-ANT-001` — Band antenna selection**

| Field | Value |
|-------|-------|
| **Type** | `CONTROL` |
| **Parameter** | Antenna path per band |
| **Method** | Multiplexer switching per band table |
| **Traces to** | `STK-ANT-001`, `STK-ANT-002` |
| **Standard(s)** | ITU-R SM.1537 |

**Acceptance Criteria:**

1. [ ] Selected band routes to the configured antenna path.

**`SYS-ANT-002` — Field-strength and radiation measurement**

| Field | Value |
|-------|-------|
| **Type** | `MEASUREMENT` |
| **Parameter** | Electric field strength |
| **Method** | Calibrated antenna factor + receiver chain |
| **Traces to** | `STK-RNI-001`, `STK-RNI-002` |
| **Standard(s)** | ITU-T K.113 |

**Acceptance Criteria:**

1. [ ] Field strength is reported in the configured unit with traceable calibration.

**`SYS-PWR-001` — Autonomous power budget**

| Field | Value |
|-------|-------|
| **Type** | `POWER` |
| **Parameter** | Available energy and duty cycle |
| **Method** | Solar/battery budget model with load shedding |
| **Traces to** | `STK-AUT-001` |
| **Standard(s)** | IEEE/ISO/IEC 29148:2018 |

**Acceptance Criteria:**

1. [ ] Duty cycle stays within the modeled energy budget for the configured profile.

**`SYS-MON-001` — Health and connectivity monitoring**

| Field | Value |
|-------|-------|
| **Type** | `MONITORING` |
| **Parameter** | Sensor health and link status |
| **Method** | Periodic self-test + link heartbeat |
| **Traces to** | `STK-MON-001`, `STK-MON-002` |
| **Standard(s)** | IEEE/ISO/IEC 29148:2018 |

**Acceptance Criteria:**

1. [ ] Health and link status are reported at the configured interval.

**`SYS-MON-002` — Scheduled spectrum scan**

| Field | Value |
|-------|-------|
| **Type** | `CONTROL` |
| **Parameter** | Scan schedule |
| **Method** | Cron-like scheduler triggering configured sweeps |
| **Traces to** | `STK-PRG-001` |
| **Standard(s)** | ITU-R SM.1537 |

**Acceptance Criteria:**

1. [ ] Scheduled scans start within the configured tolerance.

**`SYS-CAL-001` — Time sync and amplitude calibration**

| Field | Value |
|-------|-------|
| **Type** | `MEASUREMENT` |
| **Parameter** | Timestamps, frequency reference, amplitude accuracy |
| **Method** | NTP sync + calibration procedure per GUM uncertainty evaluation |
| **Traces to** | `STK-SIN-001`, `STK-CAL-001`, `STK-CAR-001`, `STK-CAR-002`, `STK-CAR-003`, `STK-CAR-004`, `STK-CAR-005` |
| **Standard(s)** | JCGM 100:2008 (GUM) |

**Acceptance Criteria:**

1. [ ] Timestamps, frequency, and amplitude accuracy stay within the calibrated uncertainty budget.

---

## 4. Correction Chains

Correction chains account for antenna factor, cable loss, receiver gain, and temperature effects. Each SYS- block that reports a calibrated quantity references its correction chain here.

| Chain ID | Corrects                         | Inputs                        |
|----------|----------------------------------|-------------------------------|
| `CHN-ANT`| Antenna factor per band          | Antenna calibration data      |
| `CHN-RX` | Receiver gain / DANL             | REF-MEAS-001 characterization |
| `CHN-USB`| USB throughput derating          | REF-MEAS-002 measurement      |

---

## 5. Uncertainty Budgets

Uncertainty budgets follow JCGM 100:2008 (NRM-GUM-001). Every reported measurand (`M-*`) carries a budget combining antenna, receiver, and digitization contributions.

| Budget ID | Measurand | Dominant contributors      |
|-----------|-----------|----------------------------|
| `UNC-FS`  | `M-007`   | Antenna factor, gain stability |
| `UNC-PSD` | `M-003`   | DANL, RBW setting, averaging  |

---

## 6. Field Measurement Protocols

Field campaigns follow ITU-T K.113 for urban electric-field measurement and ITU-R SM.1537 for station operation. Protocols define site selection, dwell time, and data retention for each measurand group.

---

## 7. Traceability

| Specification ID | Traces to | Test Case |
|------------------|-----------|-----------|
| `SYS-RF-001` | `STK-EMC-001` | _TC-S01_ |
| `SYS-RF-002` | `STK-RNG-001` | _TC-S02_ |
| `SYS-RF-003` | `STK-RNG-002` | _TC-S03_ |
| `SYS-DSP-001` | `STK-PAR-001`, `STK-PAR-003` | _TC-S04_ |
| `SYS-DSP-002` | `STK-PAR-002`, `STK-PAR-004` | _TC-S05_ |
| `SYS-NAV-001` | `STK-PAR-005` | _TC-S06_ |
| `SYS-DSP-003` | `STK-PAR-006` | _TC-S07_ |
| `SYS-DSP-004` | `STK-PAR-007` | _TC-S08_ |
| `SYS-MEAS-001` | `STK-MED-001` | _TC-S09_ |
| `SYS-MEAS-002` | `STK-MED-003` | _TC-S10_ |
| `SYS-MEAS-003` | `STK-MED-004` | _TC-S11_ |
| `SYS-MEAS-004` | `STK-MED-005` | _TC-S12_ |
| `SYS-MEAS-005` | `STK-MED-006`, `STK-MED-007` | _TC-S13_ |
| `SYS-VER-001` | `STK-VER-001`, `STK-VER-002` | _TC-S14_ |
| `SYS-VER-002` | `STK-SRV-002` | _TC-S15_ |
| `SYS-STO-001` | `STK-ALM-001`, `STK-ALM-003` | _TC-S16_ |
| `SYS-NET-001` | `STK-RED-001` | _TC-S17_ |
| `SYS-NET-002` | `STK-RED-002` | _TC-S18_ |
| `SYS-NET-003` | `STK-RED-003`, `STK-RED-004` | _TC-S19_ |
| `SYS-NET-004` | `STK-SOP-001` | _TC-S20_ |
| `SYS-NAV-002` | `STK-GPS-001`, `STK-GPS-002` | _TC-S21_ |
| `SYS-ANT-001` | `STK-ANT-001`, `STK-ANT-002` | _TC-S22_ |
| `SYS-ANT-002` | `STK-RNI-001`, `STK-RNI-002` | _TC-S23_ |
| `SYS-PWR-001` | `STK-AUT-001` | _TC-S24_ |
| `SYS-MON-001` | `STK-MON-001`, `STK-MON-002` | _TC-S25_ |
| `SYS-MON-002` | `STK-PRG-001` | _TC-S26_ |
| `SYS-CAL-001` | `STK-SIN-001`, `STK-CAL-001`, `STK-CAR-001`, `STK-CAR-002`, `STK-CAR-003`, `STK-CAR-004`, `STK-CAR-005` | _TC-S27_ |

# FM Spectrum, Waterfall and Channel Detection (RTL-SDR → Raspberry Pi)

## System Requirements Specification (SyRS)

> **Standard:** IEEE/ISO/IEC 29148:2018 §9.5 — *System requirements specification.*
>
> **Template version:** 4.0.0
> **Creation date:** 2026-11-05
> **Last modified:** 2026-11-05
> **Document status:** `DRAFT`

---

## Document Metadata

| Field                  | Value                                    |
|------------------------|------------------------------------------|
| **Document ID**        | `SYRS-FMSWD-001`                         |
| **Project**            | FM Spectrum, Waterfall and Channel Detection (RTL-SDR → Raspberry Pi) · acronym FMSWD |
| **Organization**       | GCPDS — Universidad Nacional de Colombia |
| **Version**            | 2.0.1                                    |
| **Classification**     | `PUBLIC`                                 |
| **Author(s)**          | D. Ramírez (Stakeholder / author)        |
| **Reviewer(s)**        | GCPDS lab lead (reviewer and approver)   |
| **Approver(s)**        | GCPDS lab lead (reviewer and approver)   |

### Companion Documents

| Document ID             | Title                                    | Relationship                      |
|-------------------------|------------------------------------------|-----------------------------------|
| `STRS-FMSWD-001`       | Stakeholder Requirements Specification   | Upstream contract (G0 pair)       |
| `S1-FMSWD-001`         | S1 design document                       | Software design output (S1)       |

> **Note:** The SyRS is the detailed per-measurand technical specification derived
> from the G0-validated StRS. Every SYS- block carries a `Traces to` field pointing
> at the StRS block(s) it derives from, and a `Standard(s)` field citing its
> normative source. Compliance traceability is inline: §2.3 maps each normative
> source to the methods that realize it (this replaces a standalone compliance
> matrix).

### Change Log

| Version | Date       | Author       | Change Description               |
|---------|------------|--------------|----------------------------------|
| 0.1.0   | 2026-11-05 | D. Ramírez   | Initial creation from Build Package v2.0.0 |
| 0.2.0   | 2026-11-05 | D. Ramírez   | S0 rework: SYS-PSD-002 Standard updated from Build Package v2.0.1; version bump |

---

## 1. Introduction

### 1.1 Purpose

This document specifies the system requirements for the FM Spectrum, Waterfall and Channel Detection system (FMSWD), derived from STRS-FMSWD-001. Its audience is the design team and systems engineer.

### 1.2 Scope

Measurands: power spectrum (dBFS per bin), per-channel power (dBFS), noise floor (dBFS), per-channel occupied flag, per-channel occupancy (ratio 0–1), capture end → UI render latency (ms). Power is relative to ADC full scale.

This cycle is verified with the Mock HAL and the labelled synthetic scenes only, up to VL-1. No real hardware is connected this cycle.

### 1.3 Definitions, Acronyms, and Abbreviations

| Term       | Definition                                              |
|------------|---------------------------------------------------------|
| SyRS       | System Requirements Specification (this document)       |
| StRS       | Stakeholder Requirements Specification — upstream document |
| FMSWD      | FM Spectrum, Waterfall and Channel Detection             |
| dBFS       | Decibels relative to ADC full scale                     |
| I/Q        | In-phase / Quadrature                                   |
| FFT        | Fast Fourier Transform                                  |
| PSD        | Power Spectral Density                                  |
| RBW        | Resolution Bandwidth                                    |
| HAL        | Hardware Abstraction Layer                              |
| VL-0       | Verification Level 0 (golden vectors)                   |
| VL-1       | Verification Level 1 (labelled scenes)                  |
| fc         | Centre frequency of the captured slice                  |
| fs         | Complex sample rate                                     |
| N          | FFT size (1024 samples)                                 |
| K          | Number of non-overlapping frames per update (64)        |

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

§2 describes the measurement framework: measurand catalog, method selection and normative-to-method mapping. §3 contains the system requirements as SYS- blocks grouped by function. §4–§6 hold lab inputs (correction chains, uncertainty budgets, field protocols); this cycle has none. §7 provides the traceability matrix.

---

## 2. Measurement Framework

### 2.1 Measurand Catalog

| Measurand ID | Quantity                  | Unit   | Method Family              | StRS Traces                           |
|--------------|---------------------------|--------|----------------------------|---------------------------------------|
| `MEAS-001`   | Power spectrum             | dBFS/bin | Welch periodogram (Hann)  | `STK-DSP-001`, `NRM-ITU-001`, `NRM-ITU-002` |
| `MEAS-002`   | Per-channel power          | dBFS   | Band power integration     | `STK-DSP-003`, `NRM-FCC-001`          |
| `MEAS-003`   | Noise floor                | dBFS   | 10th percentile of used bins | `STK-DSP-003`                       |
| `MEAS-004`   | Per-channel occupied flag  | bool   | Fixed threshold (10 dB)    | `STK-DSP-003`                         |
| `MEAS-005`   | Per-channel occupancy      | ratio 0–1 | Running average over 60 s | `STK-DSP-003`                        |
| `MEAS-006`   | Capture end → UI render latency | ms | End-to-end timing         | `STK-UI-001`                          |

### 2.2 Method Selection and Rationale

| Method Family              | Selected Method                          | Rejected Alternatives                       | Rationale |
|----------------------------|------------------------------------------|---------------------------------------------|-----------|
| Spectrum estimation        | Welch periodogram, Hann N=1024 K=64     | Single periodogram                          | Too noisy for a fixed threshold |
| Band selection             | One fixed 2 MHz slice                   | Stepped sweep of the whole band             | More tuning logic and stitching for no gain in this cycle |
| DC spike mitigation        | fc on an even tenth, DC bin outside every channel window | DC interpolation              | Not needed when no window contains the DC bins |
| Noise floor estimation     | 10th percentile of the 853 used bins    | Median                                      | The median rises into the carriers when more than half the slice is on air, so SC-6 fails |
| Detection threshold        | Fixed 10 dB above noise floor           | Per-channel adaptive threshold              | Not needed for on-air detection |

### 2.3 Normative-to-Method Mapping

| Normative Source         | Clause                                      | Realized By (Method)                    | Blocks                      | Compliance |
|--------------------------|---------------------------------------------|-----------------------------------------|-----------------------------|------------|
| ITU Radio Regulations    | Art. 5, 88–108 MHz (Region 2)               | Capture with allowed fc range           | `SYS-CAP-001`              | `PENDING`  |
| 47 CFR Part 73           | §73.201 FM channel raster                   | Channel power with 200 kHz spacing      | `SYS-PSD-003`              | `PENDING`  |
| ITU-R BS.450-4           | Annex 1, max freq deviation ±75 kHz         | Welch periodogram RBW ≤ 25 kHz         | `SYS-PSD-001`              | `PENDING`  |
| ISO/IEC 25010:2023       | —                                           | DSP → UI contract, UI views, latency, software platform | `SYS-IFC-001`, `SYS-UI-001`, `SYS-QOS-001`, `SYS-SW-001` | `PENDING` |

---

## 3. System Requirements

### Block ID Convention

```
SYS-[SUB]-[NNN]
```

| Segment | Rule                                    | Example            |
|---------|-----------------------------------------|--------------------|
| `SUB`   | 2–4 uppercase letters — measurand group | `CAP`, `PSD`, `DET` |
| `NNN`   | 3-digit zero-padded sequence            | `001`, `042`       |

> **Regex:** `^SYS-[A-Z]{2,4}-\d{3}$`
> Block IDs share one namespace with the StRS — no ID may appear in both documents.

---

### 3.1 Capture

---

**`SYS-CAP-001` — Capture**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `MEASUREMENT`                                             |
| **Parameter**          | I/Q capture of a 2 MHz FM slice                           |
| **Method**             | Fixed-centre capture at fs 2.4 MS/s                       |
| **Traces to**          | `STK-DSP-001`, `NRM-ITU-001`, `HWC-SDR-001`, `HWC-SDR-002` |
| **Standard(s)**        | ITU RR Art. 5                                             |

**Acceptance Criteria:**

1. [ ] fs 2.4 MS/s; one fixed centre fc, default 98.0 MHz, allowed values 89.0–107.0 MHz on even tenths.
2. [ ] Only the central ±1.0 MHz is used.
3. [ ] One update every 0.5 s.
4. [ ] Slice fc ± 1.0 MHz inside 88.0–108.0 MHz.
5. [ ] An fc outside the allowed values is refused at start.

---

**`SYS-CAP-002` — Sample conversion**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `PROCESSING`                                              |
| **Parameter**          | uint8 I/Q to complex64                                    |
| **Method**             | Linear rescale: x = ((I − 127.5) + j(Q − 127.5))/127.5  |
| **Traces to**          | `HWC-SDR-003`                                             |
| **Standard(s)**        | —                                                         |

**Acceptance Criteria:**

1. [ ] Golden vector GV-1: uint8 bytes `[255, 0, 127, 128]` → complex64 `[1.0 − 1.0j, −0.0039216 + 0.0039216j]` (± 1e-6).

---

### 3.2 Power Spectrum

---

**`SYS-PSD-001` — Power spectrum**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `PROCESSING`                                              |
| **Parameter**          | Power spectrum (dBFS per bin)                             |
| **Method**             | Welch periodogram: K=64 non-overlapping frames of N=1024 samples, Hann window, P_k = 10·log10(mean over frames of \|X_k\|²/(Σw)²), FFT-shifted |
| **Traces to**          | `STK-DSP-001`, `STK-DSP-003`, `NRM-ITU-002`              |
| **Standard(s)**        | ITU-R BS.450-4                                            |

**Acceptance Criteria:**

1. [ ] Bin spacing 2.344 kHz.
2. [ ] Output the 853 bins with \|offset\| ≤ 1.0 MHz.
3. [ ] RBW = 1.5·fs/N = 3.52 kHz ≤ 25 kHz.
4. [ ] Golden vector GV-2: maximum of P at bin N/2 + 43, value 0.0 ± 0.1 dBFS.

---

**`SYS-PSD-002` — DC spike placement**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `PROCESSING`                                              |
| **Parameter**          | DC spike mitigation via centre frequency choice           |
| **Method**             | fc on an even tenth puts the DC bin midway between two channel centres, 100 kHz from each |
| **Traces to**          | `HWC-SDR-004`, `NRM-FCC-001`                              |
| **Standard(s)**        | 47 CFR §73.201 (channel raster only)                      |

**Acceptance Criteria:**

1. [ ] No channel window (±90 kHz) contains the DC bins N/2 ± 2 for any allowed fc.

---

**`SYS-PSD-003` — Channel power**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `PROCESSING`                                              |
| **Parameter**          | Per-channel power (dBFS)                                  |
| **Method**             | Mean in linear power of P_k over the bins within ±90 kHz of the channel centre (77 bins), in dBFS |
| **Traces to**          | `STK-DSP-003`, `NRM-FCC-001`                              |
| **Standard(s)**        | 47 CFR §73.201                                            |

**Acceptance Criteria:**

1. [ ] For channel n (n = 0…9, centre fc − 0.9 + 0.2·n MHz), 10 channel powers per update.
2. [ ] Golden vector GV-3: the highest channel power is channel n = 5.

---

### 3.3 Detection

---

**`SYS-DET-001` — Detection**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `PROCESSING`                                              |
| **Parameter**          | Per-channel occupied flag and occupancy                   |
| **Method**             | Noise floor = 10th percentile of the 853 used bins; channel occupied when power − floor ≥ 10 dB; occupancy = occupied updates / updates in the last 60 s (120 updates, fewer during the first minute) |
| **Traces to**          | `STK-DSP-003`                                             |
| **Standard(s)**        | —                                                         |

**Acceptance Criteria:**

1. [ ] Golden vector GV-4: occupied flags exactly `[false, true, false, false, true, false, false, false, true, false]`.
2. [ ] SC-1: every channel occupancy ≤ 0.05.
3. [ ] SC-2: ON (n1, n4, n8) occupancy ≥ 0.95; OFF occupancy ≤ 0.05.
4. [ ] SC-3: ON (n4, n5) occupancy ≥ 0.95; OFF (n3 and n6 included) occupancy ≤ 0.05.
5. [ ] SC-4: n2 occupancy ≥ 0.95; n7 and the rest occupancy ≤ 0.05.
6. [ ] SC-5: n6 occupied flag true in updates 1–60 and false in 61–120; n6 occupancy after update 120 = 0.50 ± 0.02; the rest occupancy ≤ 0.05.
7. [ ] SC-6: ON (n0–n7) occupancy ≥ 0.95; n8, n9 occupancy ≤ 0.05.

**Notes:**
Mock HAL signal model (B.2): noise complex white Gaussian, total power σ² = −31.7 dBFS (per-bin floor −60 dBFS). FM carrier: A·exp(j(2π·Δf·t + 75·sin(2π·1000·t + φ))); deviation ±75 kHz with a 1 kHz tone; φ from seed. DC spike: +0.02 real before quantisation. Quantisation: I = clip(round(127.5 + 127.5·Re x), 0, 255), same Q, interleaved. Labelled scenes SC-1 to SC-6 per Build Package B.3, each 60 s (120 updates) at default fc, seed-deterministic.

---

### 3.4 Waterfall

---

**`SYS-WFL-001` — Waterfall**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `PROCESSING`                                              |
| **Parameter**          | Ring buffer of spectra                                    |
| **Method**             | Ring buffer of the last 120 spectra (60 s), newest first  |
| **Traces to**          | `STK-DSP-002`                                             |
| **Standard(s)**        | —                                                         |

**Acceptance Criteria:**

1. [ ] After 130 updates the buffer holds exactly the last 120, in order.

---

### 3.5 DSP → UI Interface

---

**`SYS-IFC-001` — DSP → UI contract**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `QUALITY`                                                 |
| **Parameter**          | WebSocket message format                                  |
| **Method**             | One JSON message per update over WebSocket                |
| **Traces to**          | `STK-DSP-001`, `STK-DSP-002`, `STK-DSP-003`, `STK-UI-002` |
| **Standard(s)**        | ISO/IEC 25010:2023                                        |

**Acceptance Criteria:**

1. [ ] Message format: `{"v": 1, "t_capture_end": <ISO 8601 ms>, "fc_hz": <int>, "bin_hz": 2343.75, "spectrum_dbfs": [853 numbers, 0.1 dB], "floor_dbfs": <number>, "channels": [{"f_mhz": <number>, "power_dbfs": <number>, "occupied": <bool>, "occupancy": <0–1>} × 10]}`.
2. [ ] The UI keeps its own waterfall from the received spectra.
3. [ ] A message missing a field or with `v` ≠ 1 is rejected by the UI and logged.
4. [ ] Golden vector GV-5: the table shows 10 rows with n1 and n4 marked occupied; a copy with `v` = 2 is rejected and logged.

---

### 3.6 UI Views

---

**`SYS-UI-001` — UI views**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `QUALITY`                                                 |
| **Parameter**          | Browser UI presentation                                   |
| **Method**             | One page with three views                                 |
| **Traces to**          | `STK-UI-002`                                              |
| **Standard(s)**        | ISO/IEC 25010:2023                                        |

**Acceptance Criteria:**

1. [ ] Spectrum line plot (−80…−20 dBFS) with the 10 channel centres marked and occupied channels highlighted.
2. [ ] Waterfall canvas of 120 rows, colour scale −80…−20 dBFS.
3. [ ] Channel table with frequency, occupied flag and occupancy in %.
4. [ ] Reconnects automatically every 2 s when the WebSocket drops.
5. [ ] The three views update after every message, with no reload.

---

### 3.7 Quality of Service

---

**`SYS-QOS-001` — Latency budget**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `QUALITY`                                                 |
| **Parameter**          | Capture end → UI render latency                           |
| **Method**             | End-to-end timing budget                                  |
| **Traces to**          | `STK-UI-001`, `HWC-RPI-001`                               |
| **Standard(s)**        | ISO/IEC 25010:2023                                        |

**Acceptance Criteria:**

1. [ ] Capture end → message sent ≤ 200 ms.
2. [ ] LAN ≤ 100 ms.
3. [ ] Render ≤ 200 ms.
4. [ ] Total = 500 ms, margin 500 ms.
5. [ ] p95 ≤ 1.0 s over 60 s; each term reported.

---

### 3.8 Software Platform

---

**`SYS-SW-001` — Software platform**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `QUALITY`                                                 |
| **Parameter**          | Language and runtime constraints                          |
| **Method**             | Manifest inspection                                       |
| **Traces to**          | `STK-SW-001`, `HWC-RPI-001`                               |
| **Standard(s)**        | ISO/IEC 25010:2023                                        |

**Acceptance Criteria:**

1. [ ] DSP service: Python ≥ 3.12 + numpy, one SDR access path behind the HAL.
2. [ ] UI service: TypeScript in the browser.
3. [ ] Libraries chosen at S1.
4. [ ] Manifests list Python ≥ 3.12 and numpy for the DSP service, TypeScript for the UI.

---

## 4. Correction Chains

Not applicable: no lab inputs in the Build Package.

---

## 5. Uncertainty Budgets

Not applicable: no lab inputs in the Build Package.

---

## 6. Field Measurement Protocols

Not applicable: no lab inputs in the Build Package.

---

## 7. Traceability

| Block ID       | Parameter                        | Standard Ref              | StRS Traces                                              | Test Case |
|----------------|----------------------------------|---------------------------|----------------------------------------------------------|-----------|
| `SYS-CAP-001`  | I/Q capture of a 2 MHz FM slice  | ITU RR Art. 5             | `STK-DSP-001`, `NRM-ITU-001`, `HWC-SDR-001`, `HWC-SDR-002` | —         |
| `SYS-CAP-002`  | uint8 I/Q to complex64           | —                         | `HWC-SDR-003`                                            | —         |
| `SYS-PSD-001`  | Power spectrum (dBFS per bin)    | ITU-R BS.450-4            | `STK-DSP-001`, `STK-DSP-003`, `NRM-ITU-002`             | —         |
| `SYS-PSD-002`  | DC spike mitigation              | 47 CFR §73.201 (channel raster only) | `HWC-SDR-004`, `NRM-FCC-001`                    | —         |
| `SYS-PSD-003`  | Per-channel power (dBFS)         | 47 CFR §73.201            | `STK-DSP-003`, `NRM-FCC-001`                             | —         |
| `SYS-DET-001`  | Per-channel occupied flag and occupancy | —                  | `STK-DSP-003`                                            | —         |
| `SYS-WFL-001`  | Ring buffer of spectra           | —                         | `STK-DSP-002`                                            | —         |
| `SYS-IFC-001`  | WebSocket message format         | ISO/IEC 25010:2023        | `STK-DSP-001`, `STK-DSP-002`, `STK-DSP-003`, `STK-UI-002` | —         |
| `SYS-UI-001`   | Browser UI presentation          | ISO/IEC 25010:2023        | `STK-UI-002`                                             | —         |
| `SYS-QOS-001`  | Capture end → UI render latency  | ISO/IEC 25010:2023        | `STK-UI-001`, `HWC-RPI-001`                              | —         |
| `SYS-SW-001`   | Language and runtime constraints | ISO/IEC 25010:2023        | `STK-SW-001`, `HWC-RPI-001`                              | —         |

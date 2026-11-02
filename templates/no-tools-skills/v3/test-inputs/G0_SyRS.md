# [PROJECT: Real-Time FM Spectrogram (HackRF One)]

## System Requirements Specification (SyRS)

> **Standard:** IEEE/ISO/IEC 29148:2018 §9.5 — *System requirements specification.*
>
> **Template version:** 4.0.0  
> **Creation date:** 2026-11-01  
> **Last modified:** 2026-11-01  
> **Document status:** `APPROVED`

---

## Document Metadata

| Field                  | Value                                    |
|------------------------|------------------------------------------|
| **Document ID**        | `SYRS-FMSPEC-001`                        |
| **Project**            | Real-Time FM Spectrogram (HackRF One)    |
| **Organization**       | GCPDS — Universidad Nacional de Colombia |
| **Version**            | 1.0.0                                    |
| **Classification**     | `PUBLIC`                                 |
| **Author(s)**          | D. Ramírez (systems engineer)            |
| **Reviewer(s)**        | GCPDS lab lead (reviewer)                |
| **Approver(s)**        | GCPDS lab lead (approver)                |

### Companion Documents

| Document ID        | Title                                     | Relationship                    |
|--------------------|-------------------------------------------|---------------------------------|
| `STRS-FMSPEC-001`  | Stakeholder Requirements Specification    | Upstream contract (G0 pair)     |
| `S1-FMSPEC-001`    | Layered Architecture Design (V-SIL v3 S1) | Design output (S1, reviewed at G1) |

### Change Log

| Version | Date       | Author     | Change Description                       |
|---------|------------|------------|------------------------------------------|
| 1.0.0   | 2026-11-01 | D. Ramírez | Derived from STRS-FMSPEC-001 v1.0.0 (S0)  |

---

## 1. Introduction

### 1.1 Purpose

This document derives the per-measurand technical specification of the FM spectrogram
from `STRS-FMSPEC-001`: acquisition configuration, spectral estimation method, frequency
axis, display, timing, control and platform. Audience: S1 designers, G1 reviewers, S2
implementers, G2 verifiers.

### 1.2 Scope

Measurands: per-bin relative power (dBFS), bin centre frequency (MHz), waterfall line rate,
end-to-end latency, and overflow count. Power is relative to ADC full scale — no antenna
factor or absolute (dBm / dBµV/m) calibration is in scope.

### 1.3 Definitions, Acronyms, and Abbreviations

| Term       | Definition                                                       |
|------------|------------------------------------------------------------------|
| SyRS       | System Requirements Specification (this document)                |
| StRS       | Stakeholder Requirements Specification — upstream document       |
| N          | FFT length (2048)                                                |
| fs         | Complex sample rate (20 MS/s)                                    |
| f_c        | Tuned centre frequency (98.0 MHz)                                |
| K          | Number of FFT frames averaged per waterfall line (16)            |
| ENBW       | Equivalent noise bandwidth of the window (Hann: 1.5 bins)        |
| Line       | One row of the waterfall = one averaged power spectrum           |

### 1.4 References

| Ref ID     | Document                                                          | Version / Date |
|------------|-------------------------------------------------------------------|----------------|
| `REF-001`  | Great Scott Gadgets, *HackRF One* hardware documentation          | 2024.02.1      |
| `REF-002`  | Great Scott Gadgets, *libhackrf* API (`hackrf.h`)                 | 2024.02.1      |
| `REF-004`  | ITU Radio Regulations, Volume 1 (Articles)                        | Edition 2024   |
| `REF-005`  | ITU-R BS.450-4, *Transmission standards for FM sound broadcasting at VHF* | 2019   |
| `REF-007`  | IEEE Std 1241-2010, *Terminology and Test Methods for Analog-to-Digital Converters* | 2011 |
| `REF-008`  | ISO/IEC 25010:2023, *Product quality model*                       | 2023           |
| `REF-009`  | F. J. Harris, "On the use of windows for harmonic analysis with the DFT", *Proc. IEEE* 66(1) | 1978 |
| `REF-010`  | P. D. Welch, "The use of FFT for the estimation of power spectra", *IEEE Trans. Audio Electroacoust.* 15(2) | 1967 |

### 1.5 Document Overview

§2 catalogs measurands, method choices and the normative mapping; §3 holds the SYS- blocks;
§4 correction chains; §5 uncertainty budgets; §6 measurement protocols; §7 traceability.

---

## 2. Measurement Framework

### 2.1 Measurand Catalog

| Measurand ID | Quantity                   | Unit     | Method Family                 | StRS Traces |
|--------------|----------------------------|----------|-------------------------------|-------------|
| `MEAS-001`   | Per-bin relative power      | dBFS     | Averaged windowed periodogram  | `STK-SPEC-003`, `STK-SPEC-004`, `NRM-ITU-003` |
| `MEAS-002`   | Bin centre frequency        | MHz      | FFT bin mapping (fftshift)     | `STK-SPEC-001`, `NRM-ITU-001` |
| `MEAS-003`   | Waterfall line rate         | lines/s  | Software timestamps            | `STK-SPEC-002` |
| `MEAS-004`   | End-to-end latency          | ms       | Software timestamps            | `STK-SPEC-002` |
| `MEAS-005`   | Overflow events             | count    | Driver overflow report / sample-counter gaps | `STK-OPS-001` |

### 2.2 Method Selection and Rationale

| Method Family | Selected Method | Rejected Alternatives | Rationale |
|---------------|-----------------|-----------------------|-----------|
| Spectral estimation | Hann-windowed FFT, N = 2048, K = 16 consecutive frames averaged (Welch, no overlap) | Single periodogram; Blackman-Harris N = 1024; Swept tuning | ENBW = 1.5 × 9.766 kHz = 14.6 kHz ≤ 25 kHz; averaging reduces display variance to ≈ 1.1 dB; one 20 MHz capture covers the band without retuning |
| Band coverage | Single capture, f_c = 98.0 MHz, fs = 20 MS/s | Two 10 MHz captures with retuning (sweep) | Simplest live path; sweep halves the line rate per half-band and adds retune settling |
| DC artefact | Replace bins N/2 ± 2 by linear interpolation between bins N/2 − 3 and N/2 + 3 | Offset tuning (needs fs > 20 MS/s); hardware DC calibration | Offset tuning impossible at max fs; interpolation masks only ±19.5 kHz around 98.0 MHz |
| Timing | Monotonic timestamps attached to sample blocks and rendered lines | External oscilloscope measurement | Software-only, reproducible in SIL and HIL |

### 2.3 Normative-to-Method Mapping

| Normative Source | Clause | Realized By (Method) | Blocks | Compliance |
|------------------|--------|----------------------|--------|------------|
| ITU Radio Regulations | Art. 5 (88–108 MHz, Region 2) | Single 20 MHz capture centred at 98.0 MHz | `SYS-ACQ-001`, `SYS-PSD-003` | `COMPLIANT` |
| ITU Radio Regulations | No. 15.1 | Receive-only HAL (no TX path) | `SYS-SAF-001` | `COMPLIANT` |
| ITU-R BS.450-4 | Annex 1, max. deviation ±75 kHz | RBW 14.6 kHz (N = 2048, Hann) | `SYS-PSD-001` | `COMPLIANT` |
| IEEE Std 1241-2010 | Full-scale definitions | dBFS normalisation | `SYS-DSP-001`, `SYS-PSD-001` | `COMPLIANT` |
| ISO/IEC 25010:2023 | Performance efficiency — time behaviour; portability | Timing budget; platform constraint | `SYS-TIM-001`, `SYS-TIM-002`, `SYS-DISP-001`, `SYS-CTL-001`, `SYS-PLT-001` | `COMPLIANT` |

---

## 3. System Requirements

### 3.1 Acquisition

---

**`SYS-ACQ-001` — Acquisition configuration**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `MEASUREMENT`                                             |
| **Parameter**          | f_c, fs, baseband filter, RX gains                        |
| **Method**             | Single capture: f_c = 98.0 MHz, fs = 20.0 MS/s, baseband filter 20 MHz, RX amp off, LNA 16 dB, VGA 20 dB (defaults) |
| **Traces to**          | `STK-SPEC-001`, `NRM-ITU-001`, `HWC-SDR-001`, `HWC-SDR-002`, `HWC-ANT-001` |
| **Standard(s)**        | ITU Radio Regulations Art. 5                               |

**Acceptance Criteria:**

1. [ ] The SDR reports f_c = 98.0 MHz and fs = 20.0 MS/s after start-up.
2. [ ] The baseband filter is explicitly set to 20 MHz (not the driver default of ≈ 0.75 · fs).

**Notes:**  
Band edges (88–89 and 107–108 MHz) sit on the filter roll-off; lower displayed level there
is expected and must be characterised at HIL.

---

**`SYS-DSP-001` — Sample format conversion**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `PROCESSING`                                              |
| **Parameter**          | Complex baseband sample x[n]                              |
| **Method**             | Interleaved int8 (I, Q) → complex64: x = (I + jQ) / 128   |
| **Traces to**          | `HWC-SDR-003`, `STK-SPEC-004`                             |
| **Standard(s)**        | IEEE Std 1241-2010                                         |

**Acceptance Criteria:**

1. [ ] Input bytes `[127, 0, -128, 0]` convert to `[0.9921875+0j, -1.0+0j]`.
2. [ ] Conversion preserves sample order and count (2 bytes in → 1 complex sample out).

---

### 3.2 Spectral Estimation

---

**`SYS-PSD-001` — Averaged power spectrum per line**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `PROCESSING`                                              |
| **Parameter**          | P_k (dBFS), k = 0 … N − 1                                 |
| **Method**             | Hann window w[n], N = 2048; X_k = Σ w[n]·x[n]·e^(−j2πkn/N); P_k = 10·log10( mean over K = 16 consecutive frames of \|X_k\|² / (Σ w[n])² ) |
| **Traces to**          | `STK-SPEC-003`, `STK-SPEC-004`, `NRM-ITU-003`             |
| **Standard(s)**        | ITU-R BS.450-4; IEEE Std 1241-2010                         |

**Acceptance Criteria:**

1. [ ] A complex tone of amplitude 1.0 exactly on a bin centre reads 0.0 ± 0.1 dBFS.
2. [ ] A complex tone of amplitude 0.1 on a bin centre reads −20.0 ± 0.5 dBFS.
3. [ ] Two equal tones 200 kHz apart produce two peaks with a dip ≥ 20 dB between them.
4. [ ] RBW = ENBW · fs / N = 1.5 · 20e6 / 2048 = 14.65 kHz ≤ 25 kHz (analysis).

---

**`SYS-PSD-002` — DC spike mitigation**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `PROCESSING`                                              |
| **Parameter**          | P_k for k = N/2 − 2 … N/2 + 2                             |
| **Method**             | Replace the 5 centre bins (after fftshift) by linear interpolation between P_(N/2−3) and P_(N/2+3) |
| **Traces to**          | `HWC-SDR-005`, `STK-SPEC-001`                             |
| **Standard(s)**        | IEEE Std 1241-2010                                         |

**Acceptance Criteria:**

1. [ ] Input = AWGN + DC offset 0.1 FS: centre bins read within 3 dB of the mean of bins N/2 ± 3…10.
2. [ ] Bins outside N/2 ± 2 are unchanged (bit-exact).

**Notes:**  
A real station at 98.0 MHz would be masked (±19.5 kHz). Accepted limitation; S1 risk.

---

**`SYS-PSD-003` — Frequency axis**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `PROCESSING`                                              |
| **Parameter**          | f_k (MHz)                                                 |
| **Method**             | After fftshift: f_k = f_c + (k − N/2) · fs / N; axis extent f_c ± fs/2 = 88.0 … 108.0 MHz |
| **Traces to**          | `STK-SPEC-001`, `STK-SPEC-004`                            |
| **Standard(s)**        | ITU Radio Regulations Art. 5                               |

**Acceptance Criteria:**

1. [ ] f_0 = 88.000 MHz, f_1024 = 98.000 MHz, f_2047 = 107.990 MHz (± 1 Hz).
2. [ ] A synthetic tone at baseband −1.0 MHz peaks at bin 1024 − 102 or 1024 − 103 (97.0 MHz ± 1 bin).

---

### 3.3 Display and Timing

---

**`SYS-DISP-001` — Waterfall rendering**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `QUALITY`                                                 |
| **Parameter**          | Line rate, history depth, colour mapping                  |
| **Method**             | Scrolling image, newest line on top, ≥ 20 lines/s target, 200-line history (10 s), colour map over [P_min, P_max] with default [−80, 0] dBFS, MHz ticks every 2 MHz |
| **Traces to**          | `STK-SPEC-001`, `STK-SPEC-002`, `STK-SPEC-004`            |
| **Standard(s)**        | ISO/IEC 25010:2023                                         |

**Acceptance Criteria:**

1. [ ] Measured line rate ≥ 10 lines/s over 60 s (target 20).
2. [ ] Changing [P_min, P_max] takes effect on the next line without restart.
3. [ ] The axis shows 88, 90, …, 108 MHz ticks.

---

**`SYS-TIM-001` — End-to-end latency budget**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `QUALITY`                                                 |
| **Parameter**          | Latency from sample-block timestamp to line rendered (ms) |
| **Method**             | Budget: driver/USB buffering ≤ 100 ms + line accumulation ≤ 50 ms + spectral processing ≤ 50 ms + rendering ≤ 50 ms = 250 ms, margin 250 ms to the 500 ms limit |
| **Traces to**          | `STK-SPEC-002`, `HWC-HOST-001`                            |
| **Standard(s)**        | ISO/IEC 25010:2023                                         |

**Acceptance Criteria:**

1. [ ] 95th percentile latency ≤ 500 ms over 60 s.
2. [ ] Each budget term is measured separately and reported.

---

**`SYS-TIM-002` — Sustained throughput without overflow**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `QUALITY`                                                 |
| **Parameter**          | Overflow events per 10 min at 20 MS/s                     |
| **Method**             | Acquisition thread consumes USB buffers continuously; lines use K = 16 frames out of each 50 ms period and discard the rest (time decimation) so processing load is independent of fs |
| **Traces to**          | `STK-OPS-001`, `HWC-BUS-001`                              |
| **Standard(s)**        | ISO/IEC 25010:2023                                         |

**Acceptance Criteria:**

1. [ ] 30-minute run: ≤ 3 overflow events, no crash.
2. [ ] Overflow events are counted and logged with a timestamp.

---

### 3.4 Control, Safety and Platform

---

**`SYS-CTL-001` — Runtime gain control**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `PROTOCOL`                                                |
| **Parameter**          | LNA gain, VGA gain (dB)                                   |
| **Method**             | Operator request → validate (LNA ∈ {0,8,…,40}, VGA ∈ {0,2,…,62}; other values rounded down to the nearest step) → apply via the SDR API without stopping the stream |
| **Traces to**          | `STK-SPEC-005`, `HWC-SDR-004`                             |
| **Standard(s)**        | ISO/IEC 25010:2023                                         |

**Acceptance Criteria:**

1. [ ] Request LNA = 13 dB applies 8 dB; request VGA = 63 dB applies 62 dB.
2. [ ] The new gain is applied within 200 ms and the stream keeps running.

---

**`SYS-SAF-001` — Receive-only operation**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `PROTOCOL`                                                |
| **Parameter**          | SDR transceiver mode                                      |
| **Method**             | The hardware abstraction exposes RX operations only; no TX function or TX sink is reachable |
| **Traces to**          | `STK-OPS-002`, `NRM-ITU-002`                              |
| **Standard(s)**        | ITU Radio Regulations No. 15.1                             |

**Acceptance Criteria:**

1. [ ] Inspection: no call to `hackrf_start_tx`, `hackrf_set_txvga_gain`, or a GNU Radio sink bound to the HackRF.

---

**`SYS-PLT-001` — Software platform**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `QUALITY`                                                 |
| **Parameter**          | Runtime and libraries                                     |
| **Method**             | Python ≥ 3.10 + numpy; SDR access via GNU Radio 3.10 (gr-osmosdr) or libhackrf; GUI library chosen at S1 |
| **Traces to**          | `STK-OPS-003`, `HWC-HOST-001`                             |
| **Standard(s)**        | ISO/IEC 25010:2023                                         |

**Acceptance Criteria:**

1. [ ] The dependency manifest lists Python ≥ 3.10, numpy, and exactly one of GNU Radio 3.10 / libhackrf for SDR access.

---

## 4. Correction Chains

| Block          | Correction                    | Model / Source                         | Applied Where              |
|----------------|-------------------------------|----------------------------------------|----------------------------|
| `SYS-DSP-001`  | int8 → full-scale scaling      | x = (I + jQ)/128 (`REF-007`)            | Sample conversion          |
| `SYS-PSD-001`  | Window coherent-gain correction | divide \|X_k\|² by (Σ w)² (`REF-009`)  | Power spectrum             |
| `SYS-PSD-002`  | DC artefact removal            | Linear interpolation over 5 centre bins | After fftshift, before dB  |

No antenna factor or cable loss correction: power is relative (dBFS), not field strength.

---

## 5. Uncertainty Budgets

| Measurand   | Component                        | Source u(x)            | Distribution | Sensitivity c | Standard u |
|-------------|----------------------------------|------------------------|--------------|---------------|------------|
| P_k (dBFS)  | Scalloping loss (tone between bins, Hann) | 0 … 1.42 dB (`REF-009`) | Rectangular | 1 | 0.41 dB |
| P_k (dBFS)  | Averaging variance, K = 16 (noise-like signals) | ≈ 4.34/√K dB (`REF-010`) | Normal | 1 | 1.09 dB |
| P_k (dBFS)  | 8-bit quantisation (full-scale tone) | SQNR ≈ 49.9 dB      | Rectangular  | 1             | < 0.01 dB  |
| f_k (MHz)   | Bin spacing                       | fs/N = 9.766 kHz       | Rectangular  | 1             | 2.82 kHz   |
| f_k (MHz)   | HackRF reference oscillator (±20 ppm at 98 MHz) | ±1.96 kHz (`REF-001`) | Rectangular | 1 | 1.13 kHz |

---

## 6. Field Measurement Protocols

| Protocol ID | Applies To (Blocks) | Setup | Calibration | Execution |
|-------------|---------------------|-------|-------------|-----------|
| `PROTO-001` | `SYS-ACQ-001`, `SYS-PSD-003`, `SYS-DISP-001` | ANT500 extended near a window, HackRF on host USB 2.0 port, defaults of `SYS-ACQ-001` | None (relative dBFS); list of local licensed FM stations from the regulator | Run 60 s; note frequency of each visible station; compare with the list (± 1 bin) |
| `PROTO-002` | `SYS-TIM-001`, `SYS-TIM-002` | Same as PROTO-001, no other USB load | — | 60 s latency/line-rate log; then 30-min soak with overflow log |
| `PROTO-003` | `SYS-CTL-001`, `SYS-SAF-001` | Same as PROTO-001 | — | Step LNA 0→40 dB and VGA 0→62 dB while running; inspect code for TX calls |

---

## 7. Traceability

| Block ID       | Parameter                 | Standard Ref            | StRS Traces                                   | Test Case |
|----------------|---------------------------|-------------------------|-----------------------------------------------|-----------|
| `SYS-ACQ-001`  | f_c, fs, filter, gains    | ITU RR Art. 5           | `STK-SPEC-001`, `NRM-ITU-001`, `HWC-SDR-001`, `HWC-SDR-002`, `HWC-ANT-001` | TC-001 |
| `SYS-DSP-001`  | x[n]                      | IEEE 1241-2010          | `HWC-SDR-003`, `STK-SPEC-004`                 | TC-004    |
| `SYS-PSD-001`  | P_k                       | ITU-R BS.450-4; IEEE 1241 | `STK-SPEC-003`, `STK-SPEC-004`, `NRM-ITU-003` | TC-003, TC-004 |
| `SYS-PSD-002`  | centre bins               | IEEE 1241-2010          | `HWC-SDR-005`, `STK-SPEC-001`                 | TC-007    |
| `SYS-PSD-003`  | f_k                       | ITU RR Art. 5           | `STK-SPEC-001`, `STK-SPEC-004`                | TC-001    |
| `SYS-DISP-001` | line rate, colour map     | ISO/IEC 25010           | `STK-SPEC-001`, `STK-SPEC-002`, `STK-SPEC-004` | TC-002, TC-004 |
| `SYS-TIM-001`  | latency                   | ISO/IEC 25010           | `STK-SPEC-002`, `HWC-HOST-001`                | TC-002    |
| `SYS-TIM-002`  | overflow count            | ISO/IEC 25010           | `STK-OPS-001`, `HWC-BUS-001`                  | TC-006    |
| `SYS-CTL-001`  | LNA, VGA                  | ISO/IEC 25010           | `STK-SPEC-005`, `HWC-SDR-004`                 | TC-005    |
| `SYS-SAF-001`  | TX disabled               | ITU RR No. 15.1         | `STK-OPS-002`, `NRM-ITU-002`                  | TC-008    |
| `SYS-PLT-001`  | runtime                   | ISO/IEC 25010           | `STK-OPS-003`, `HWC-HOST-001`                 | TC-009    |

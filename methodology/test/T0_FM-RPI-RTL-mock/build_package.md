# Build Package — FM Spectrum, Waterfall and Channel Detection (RTL-SDR → Raspberry Pi)

> Test input for the T8 end-to-end run (`mock-only`, S0 → G2). Two services: a DSP service on
> the Raspberry Pi and a browser UI. It has **no lab inputs**: no correction chains, no
> uncertainty budgets, no field measurement protocols, so S0 writes
> `Not applicable: no lab inputs in the Build Package.` under SyRS §4, §5 and §6. The test
> oracle is fixed here by the author: the Mock HAL signal model (B.2), the labelled scenes (B.3)
> and the VL-0 golden vectors (B.4). No ML model is used; spectral localisation with ML is
> future work only (A.1), so the S1 design has no §1.5.

## Identity

| Item | Value |
|------|-------|
| Project | FM Spectrum, Waterfall and Channel Detection (RTL-SDR → Raspberry Pi) · acronym FMSWD |
| Organisation | GCPDS — Universidad Nacional de Colombia |
| Classification | PUBLIC · version 2.0.1 · date 2026-11-05 |
| Stakeholder / author | D. Ramírez · reviewer and approver: GCPDS lab lead |
| Objectives | OBJ-001 see the live spectrum of a 2 MHz slice of the FM band · OBJ-002 see its last minute as a waterfall · OBJ-003 know which FM channels in the slice are on air · OBJ-004 simple enough to build and verify in one cycle |

## Part A — Stakeholder content

### A.1 Scope and users

An RTL-SDR on a Raspberry Pi captures a fixed 2 MHz slice of the commercial FM band
(default centre 98.0 MHz), computes its power spectrum, keeps a one-minute waterfall and
detects which of the 10 FM channels in the slice are on air. A browser UI on the same LAN
shows the three views live. Users: lab engineers (technical: start the services, read the
views, run the tests) and students (basic: read the views). New standalone system with two
services: a DSP service on the Raspberry Pi and a UI service in the browser.

This cycle is verified with the Mock HAL and the labelled synthetic scenes of B.3 only, up to
VL-1. No real hardware is connected this cycle.

Out of scope: sweeping the whole band, audio demodulation, I/Q recording, calibrated dBm or
field-strength measurement, any transmission, user accounts, access from outside the LAN.

Future work, not a requirement of this Build Package: an ML model that performs spectral
localisation of the emitters. It is recorded here so it is not lost; nothing in this cycle
depends on it.

Assumptions: the Raspberry Pi runs only this software; the UI browser is a recent Chromium or
Firefox on the same LAN.

### A.2 Normative obligations

| # | Obligation | Source | Clause | Priority | Acceptance |
|---|------------|--------|--------|----------|------------|
| N1 | Stay inside the Region 2 BROADCASTING allocation 88–108 MHz | ITU Radio Regulations | Article 5, Table of Frequency Allocations, 88–108 MHz (Region 2) | MUST | the observed slice lies within 88.0–108.0 MHz for every allowed centre |
| N2 | Use the FM channel raster: channels of 200 kHz with centres on odd tenths of a MHz | 47 CFR Part 73 | §73.201 Numerical designation of FM broadcast channels | MUST | the 10 channel centres of the slice are fc − 0.9 + 0.2·n MHz, n = 0…9 |
| N3 | Resolve FM emissions with max. deviation ±75 kHz | ITU-R BS.450-4 | Annex 1, maximum frequency deviation | SHOULD | RBW ≤ 25 kHz (one third of 75 kHz) |

### A.3 Stakeholder requirements

| # | Need | Type | Priority | Verification | Acceptance |
|---|------|------|----------|--------------|------------|
| R1 | Live power spectrum of the 2 MHz slice, updated every 0.5 s (depends on N1, N3, H1, H2) | FUNCTIONAL | MUST | TEST | one spectrum per 0.5 s; golden vector GV-2 peaks at 0.0 ± 0.1 dBFS |
| R2 | Waterfall of the last 60 s of spectra (depends on R1) | FUNCTIONAL | MUST | TEST | 120 rows, newest on top, one row per update |
| R3 | Per-channel detection: occupied or free at every update, and the occupancy (0–1) over the last 60 s (depends on R1, N2) | FUNCTIONAL | MUST | TEST | every labelled scene of B.3 gives its expected result |
| R4 | The UI shows each update within 1.0 s of the end of its capture (depends on R1, C1) | NON_FUNCTIONAL | MUST | TEST | capture end → UI render latency p95 ≤ 1.0 s over 60 s |
| R5 | One browser page with the three views: spectrum, waterfall, channel table (depends on R1, R2, R3) | FUNCTIONAL | SHOULD | DEMONSTRATION | page loads on a LAN browser; the three views update with no reload |
| R6 | DSP service in Python ≥ 3.12; UI service in TypeScript in the browser (depends on C1) | CONSTRAINT | MUST | INSPECTION | manifests: Python ≥ 3.12 for the DSP service, TypeScript for the UI |

### A.4 COTS hardware (not negotiable)

| ID | Item | Part | Role |
|----|------|------|------|
| HW-001 | RTL-SDR Blog V4 (RTL2832U + R828D) | RTLSDR-BLOG-V4 | RF front end, tuner, 8-bit I/Q ADC (receive only) |
| HW-002 | RTL-SDR Blog dipole antenna kit | DIPOLE-KIT | VHF receive antenna |
| HW-003 | Raspberry Pi 4 Model B, 4 GB | RPI4-4GB | edge node: runs the DSP service and serves the UI |
| HW-004 | User laptop or PC with a browser | generic | runs the UI over the LAN |

Connections: HW-002 → HW-001 SMA coaxial (RF analog); HW-001 → HW-003 USB 2.0 bulk,
4.8 MB/s at 2.4 MS/s × 2 B; HW-003 → HW-004 Ethernet or Wi-Fi LAN (HTTP and WebSocket).

| # | Constraint | Component | Limit | Source | Impact | Status |
|---|------------|-----------|-------|--------|--------|--------|
| H1 | Tuning range | HW-001 | RANGE 500 kHz – 1.766 GHz | DATASHEET, REF-001 §Specifications | HARD | CONFIRMED |
| H2 | Complex sample rate without dropped samples | HW-001 | MAX 2.4 MS/s | DATASHEET, REF-001 §Specifications | HARD | CONFIRMED |
| H3 | I/Q resolution | HW-001 | FIXED 8 bit unsigned per I and Q, interleaved | DATASHEET, REF-001 §Specifications | HARD | CONFIRMED |
| H4 | DC spike at the tuned centre | HW-001 | FIXED present at every centre frequency | DATASHEET, REF-001 §Known issues | SOFT | PRELIMINARY |
| H5 | Reference oscillator | HW-001 | FIXED 1 ppm TCXO | DATASHEET, REF-001 §Specifications | INFORMATIONAL | CONFIRMED |
| C1 | Edge compute | HW-003 | FIXED 4 cores ARM Cortex-A72 64-bit / 4 GB / Raspberry Pi OS 64-bit | DATASHEET, REF-002 §Specifications | INFORMATIONAL | CONFIRMED |

### A.5 References

REF-001 RTL-SDR Blog V4 user guide (2023) · REF-002 Raspberry Pi 4 Model B product brief
(2024) · REF-003 ITU Radio Regulations Vol. 1 (Edition 2024) · REF-004 ITU-R BS.450-4 (2019) ·
REF-005 47 CFR Part 73 §73.201 · REF-006 Welch 1967, IEEE Trans. Audio Electroacoust. 15(2) ·
REF-007 Harris 1978, Proc. IEEE 66(1) · REF-008 ISO/IEC 25010:2023.

## Part B — System-level technical annex (systems engineer)

Measurands: power spectrum (dBFS per bin) · per-channel power (dBFS) · noise floor (dBFS) ·
per-channel occupied flag · per-channel occupancy (ratio 0–1) · capture end → UI render
latency (ms). Power is relative to ADC full scale.

### B.1 Specifications

| # | Specification | Type | Method / values | Derives from | Standard | Acceptance |
|---|---------------|------|-----------------|--------------|----------|------------|
| Y1 | Capture | MEASUREMENT | fs 2.4 MS/s; one fixed centre fc, default 98.0 MHz, allowed values 89.0–107.0 MHz on even tenths; only the central ±1.0 MHz is used; one update every 0.5 s | R1, N1, H1, H2 | ITU RR Art. 5 | slice fc ± 1.0 MHz inside 88.0–108.0 MHz; an fc outside the allowed values is refused at start |
| Y2 | Sample conversion | PROCESSING | interleaved uint8 (I,Q) → complex64, x = ((I − 127.5) + j(Q − 127.5))/127.5 | H3 | — | golden vector GV-1 |
| Y3 | Power spectrum | PROCESSING | per update, the K = 64 most recent non-overlapping frames of N = 1024 samples; Hann window; P_k = 10·log10(mean over frames of \|X_k\|²/(Σw)²), FFT-shifted; bin spacing 2.344 kHz; output the 853 bins with \|offset\| ≤ 1.0 MHz | R1, R3, N3 | ITU-R BS.450-4 | golden vector GV-2; RBW = 1.5·fs/N = 3.52 kHz ≤ 25 kHz |
| Y4 | DC spike placement | PROCESSING | an fc on an even tenth puts the DC bin midway between two channel centres, 100 kHz from each, so no channel window (±90 kHz) contains the DC bins N/2 ± 2 | H4, N2 | 47 CFR §73.201 (channel raster only) | no channel window contains bins N/2 ± 2 for any allowed fc |
| Y5 | Channel power | PROCESSING | for channel n (n = 0…9, centre fc − 0.9 + 0.2·n MHz), mean in linear power of P_k over the bins within ±90 kHz of the centre (77 bins), in dBFS | R3, N2 | 47 CFR §73.201 | 10 channel powers per update; golden vector GV-3 |
| Y6 | Detection | PROCESSING | noise floor = 10th percentile of the 853 used bins of the update; channel occupied in an update when its power − floor ≥ 10 dB; occupancy = occupied updates / updates in the last 60 s (120 updates, fewer during the first minute) | R3 | — | golden vector GV-4; every labelled scene of B.3 |
| Y7 | Waterfall | PROCESSING | ring buffer of the last 120 spectra (60 s), newest first | R2 | — | after 130 updates the buffer holds exactly the last 120, in order |
| Y8 | DSP → UI contract | QUALITY | one JSON message per update over WebSocket: `{"v": 1, "t_capture_end": <ISO 8601 ms>, "fc_hz": <int>, "bin_hz": 2343.75, "spectrum_dbfs": [853 numbers, 0.1 dB], "floor_dbfs": <number>, "channels": [{"f_mhz": <number>, "power_dbfs": <number>, "occupied": <bool>, "occupancy": <0–1>} × 10]}`; the UI keeps its own waterfall from the received spectra | R1, R2, R3, R5 | ISO/IEC 25010:2023 | a message missing a field or with `v` ≠ 1 is rejected by the UI and logged; golden vector GV-5 |
| Y9 | UI views | QUALITY | one page: spectrum line plot (−80…−20 dBFS) with the 10 channel centres marked and occupied channels highlighted; waterfall canvas of 120 rows, colour scale −80…−20 dBFS; channel table with frequency, occupied flag and occupancy in %; reconnects automatically every 2 s when the WebSocket drops | R5 | ISO/IEC 25010:2023 | the three views update after every message, with no reload |
| Y10 | Latency budget | QUALITY | capture end → message sent ≤ 200 ms + LAN ≤ 100 ms + render ≤ 200 ms = 500 ms, margin 500 ms | R4, C1 | ISO/IEC 25010:2023 | p95 ≤ 1.0 s over 60 s; each term reported |
| Y11 | Software platform | QUALITY | DSP service: Python ≥ 3.12 + numpy, one SDR access path behind the HAL; UI service: TypeScript in the browser; libraries chosen at S1 | R6, C1 | ISO/IEC 25010:2023 | manifests list Python ≥ 3.12 and numpy for the DSP service, TypeScript for the UI |

An em dash in `Standard` means no external normative source prescribes that method; its
values and acceptance criteria are specified by this Build Package. Y4 cites §73.201 only
for the 200 kHz FM channel raster. Keeping the DC bins outside the channel windows is a
project method, not a requirement of §73.201.

### B.2 Mock HAL signal model

The Mock HAL emits exactly what HW-001 emits: interleaved uint8 I/Q at 2.4 MS/s centred at fc.
Each scene is generated from its parameters and a seed; the same parameters and seed give the
same bytes.

| Element | Model |
|---------|-------|
| Noise | complex white Gaussian, total power σ² = −31.7 dBFS, which puts the per-bin floor of Y3 at −60 dBFS |
| FM carrier | A·exp(j(2π·Δf·t + 75·sin(2π·1000·t + φ))): Δf = carrier frequency − fc; A from the level in dBFS (total carrier power, 20·log10 A); deviation ±75 kHz with a 1 kHz tone; φ drawn from the seed |
| DC spike (H4) | constant +0.02 added to the real part before quantisation |
| Quantisation | I = clip(round(127.5 + 127.5·Re x), 0, 255), same for Q, interleaved I, Q |

For information, not a test value: a carrier at level L dBFS gives a channel power of about
L − 17.1 dBFS (10·log10(1.5/77)), so about L + 42.9 dB above the −60 dBFS floor; −20 dBFS is
about +23 dB. The labels of B.3 keep at least 4 dB of clearance from the 10 dB threshold.

### B.3 Labelled scenes (acceptance oracle for R3)

Channel index n = 0…9, centre fc − 0.9 + 0.2·n MHz (97.1, 97.3, …, 98.9 MHz at the default fc).
Every scene lasts 60 s (120 updates) at the default fc. A channel is **ON** when it is listed
as ON; every other channel is **OFF**.

| Scene | Purpose | Carriers (channel: level) | ON | Expected result |
|-------|---------|---------------------------|----|-----------------|
| SC-1 | Noise only | none | none | every channel: occupancy ≤ 0.05 |
| SC-2 | Three stations | n1, n4, n8: −20 dBFS | n1, n4, n8 | ON: occupancy ≥ 0.95 · OFF: occupancy ≤ 0.05 |
| SC-3 | Adjacent stations, DC spike between them | n4, n5: −20 dBFS | n4, n5 | ON: occupancy ≥ 0.95 · OFF, n3 and n6 included: occupancy ≤ 0.05 |
| SC-4 | Near the threshold | n2: −29 dBFS (about +15 dB) · n7: −39 dBFS (about +6 dB) | n2 | n2: occupancy ≥ 0.95 · n7 and the rest: occupancy ≤ 0.05 |
| SC-5 | Intermittent station | n6: −20 dBFS during the first 30 s, absent the last 30 s | n6 in updates 1–60 only | n6 occupied flag true in updates 1–60 and false in 61–120; n6 occupancy after update 120 = 0.50 ± 0.02 · the rest: occupancy ≤ 0.05 |
| SC-6 | Busy slice (8 of 10 channels on air) | n0–n7: −20 dBFS | n0–n7 | ON: occupancy ≥ 0.95 · n8, n9: occupancy ≤ 0.05 |

Labelling procedure:

1. The labels are the ON column above, written by the author before any data exists.
2. The Mock HAL generator takes only the carriers, levels, durations and seed; it never reads
   the labels.
3. The golden manifest copies each scene's labels and expected result as its expected output.
4. Nobody derives a label from the detector's output. Changing a scene or a label is a change
   to this Build Package and starts again at S0.

### B.4 VL-0 golden vectors

Short, deterministic inputs; each is versioned in the golden manifest with its SHA-256.

| Vector | Input | Expected output |
|--------|-------|-----------------|
| GV-1 | uint8 bytes `[255, 0, 127, 128]` | complex64 `[1.0 − 1.0j, −0.0039216 + 0.0039216j]` (± 1e-6) |
| GV-2 | 64 × 1024 complex64 samples of a tone of amplitude 1.0 at +43 bins (+100.78125 kHz), no noise, fed straight to Y3 | maximum of P at bin N/2 + 43, value 0.0 ± 0.1 dBFS |
| GV-3 | the GV-2 generator with a tone at fc + 0.1 MHz (98.1 MHz at the default fc) | the highest channel power is channel n = 5 |
| GV-4 | one update (64 × 1024 samples) of SC-2 through the Mock HAL with seed 1 | occupied flags exactly `[false, true, false, false, true, false, false, false, true, false]` |
| GV-5 | one fixed Y8 message with channels n1 and n4 occupied, fed to the UI | the table shows 10 rows with n1 and n4 marked occupied; a copy with `v` = 2 is rejected and logged |

Method rationale: one fixed 2 MHz slice (rejected: stepped sweep of the whole band — more
tuning logic and stitching for no gain in this cycle); Hann N = 1024 K = 64 (rejected: single
periodogram — too noisy for a fixed threshold); DC spike kept out of every channel by choosing
fc on an even tenth (rejected: DC interpolation — not needed when no window contains the DC
bins); noise floor at the 10th percentile of the used bins (rejected: the median — it rises
into the carriers when more than half the slice is on air, so SC-6 fails); fixed 10 dB
threshold (rejected: per-channel adaptive threshold — not needed for on-air detection).

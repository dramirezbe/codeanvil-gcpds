# Build Package — FM Channel Occupancy Edge (RTL-SDR → Raspberry Pi)

> Test input for the T8 end-to-end run (`mock-only`, S0 → G2). It has **no lab inputs**: no
> correction chains, no uncertainty budgets, no field measurement protocols, so S0 writes
> `Not applicable: no lab inputs in the Build Package.` under SyRS §4, §5 and §6. The ML model
> for spectral localisation is future work only (A.1), so the S1 design has no §1.5.

## Identity

| Item | Value |
|------|-------|
| Project | FM Channel Occupancy Edge (RTL-SDR → Raspberry Pi) · acronym FMOCC |
| Organisation | GCPDS — Universidad Nacional de Colombia |
| Classification | PUBLIC · version 1.0.0 · date 2026-11-05 |
| Stakeholder / author | D. Ramírez · reviewer and approver: GCPDS lab lead |
| Objectives | OBJ-001 know which FM channels are on air · OBJ-002 see it live on a small dashboard · OBJ-003 run unattended on a cheap edge node · OBJ-004 maintainable |

## Part A — Stakeholder content

### A.1 Scope and users

An RTL-SDR on a Raspberry Pi sweeps the commercial FM band (88–108 MHz), computes the
occupancy of every FM channel, and serves a small one-page dashboard to a browser on the
same LAN. Users: lab engineers (technical: start the edge node, read the dashboard, run soak
tests) and students (basic: read the dashboard). New standalone system.

This cycle is verified with the Mock HAL and labelled synthetic scenes only, up to VL-1. No
real hardware is connected this cycle.

Out of scope: audio demodulation, I/Q recording, calibrated dBm or field-strength
measurement, any transmission, user accounts, access from outside the LAN.

Future work, not a requirement of this Build Package: an ML model that performs spectral
localisation of the emitters. It is recorded here so it is not lost; nothing in this cycle
depends on it.

Assumptions: line of sight to local FM transmitters; the Raspberry Pi runs only this
software; the dashboard browser is a recent Chromium or Firefox on the same LAN.

### A.2 Normative obligations

| # | Obligation | Source | Clause | Priority | Acceptance |
|---|------------|--------|--------|----------|------------|
| N1 | Observe the Region 2 BROADCASTING allocation 88–108 MHz | ITU Radio Regulations | Article 5, Table of Frequency Allocations, 88–108 MHz (Region 2) | MUST | sweep covers 88.0–108.0 MHz |
| N2 | Use the FM channel raster: 100 channels of 200 kHz, centres 88.1–107.9 MHz | 47 CFR Part 73 | §73.201 Numerical designation of FM broadcast channels | MUST | 100 channels, centre of channel n = 88.1 + 0.2·n MHz, n = 0…99 |
| N3 | Resolve FM emissions with max. deviation ±75 kHz | ITU-R BS.450-4 | Annex 1, maximum frequency deviation | SHOULD | RBW ≤ 25 kHz (one third of 75 kHz) |

### A.3 Stakeholder requirements

| # | Need | Type | Priority | Verification | Acceptance |
|---|------|------|----------|--------------|------------|
| R1 | Occupancy (0–1) of each of the 100 FM channels over a sliding 60 s window (depends on N1, N2, H1, H2) | FUNCTIONAL | MUST | TEST | labelled synthetic scene: every on-air channel ≥ 0.95, every empty channel ≤ 0.05 |
| R2 | Dashboard updated after every sweep; a sweep shown within 1.5 s of its end (depends on R1, C1) | NON_FUNCTIONAL | MUST | TEST | sweep period ≤ 1.5 s; end-of-sweep → dashboard latency p95 ≤ 1.5 s over 60 s |
| R3 | RBW 25 kHz or finer so adjacent channels 200 kHz apart are told apart (depends on N3) | NON_FUNCTIONAL | MUST | ANALYSIS | analysis RBW ≤ 25 kHz; two carriers 200 kHz apart → two occupied channels |
| R4 | Small one-page dashboard: one bar per channel, the last sweep time and the edge node status (depends on R1) | FUNCTIONAL | SHOULD | DEMONSTRATION | page loads on a LAN browser; 100 bars labelled in MHz; time and status visible |
| R5 | 30 min unattended, ≤ 1 dropped sample buffer per 10 min (depends on B1, C1) | NON_FUNCTIONAL | MUST | TEST | 30-min soak: ≤ 3 dropped buffers, no crash |
| R6 | Edge software in Python ≥ 3.12 on Raspberry Pi OS (64-bit); dashboard in TypeScript in the browser (depends on C1) | CONSTRAINT | MUST | INSPECTION | dependency list: Python ≥ 3.12 on the edge, TypeScript for the dashboard |

### A.4 COTS hardware (not negotiable)

| ID | Item | Part | Role |
|----|------|------|------|
| HW-001 | RTL-SDR Blog V4 (RTL2832U + R828D) | RTLSDR-BLOG-V4 | RF front end, tuner, 8-bit I/Q ADC (receive only) |
| HW-002 | RTL-SDR Blog dipole antenna kit | DIPOLE-KIT | VHF receive antenna |
| HW-003 | Raspberry Pi 4 Model B, 4 GB | RPI4-4GB | edge node: runs the sweep, the occupancy and the dashboard server |
| HW-004 | User laptop or PC with a browser | generic | shows the dashboard over the LAN |

Connections: HW-002 → HW-001 SMA coaxial (RF analog); HW-001 → HW-003 USB 2.0 bulk,
4.8 MB/s at 2.4 MS/s × 2 B; HW-003 → HW-004 Ethernet or Wi-Fi LAN (HTTP).

| # | Constraint | Component | Limit | Source | Impact | Status |
|---|------------|-----------|-------|--------|--------|--------|
| H1 | Tuning range | HW-001 | RANGE 500 kHz – 1.766 GHz | DATASHEET, REF-001 §Specifications | HARD | CONFIRMED |
| H2 | Complex sample rate without dropped samples (= usable span per tuning step) | HW-001 | MAX 2.4 MS/s | DATASHEET, REF-001 §Specifications | HARD | CONFIRMED |
| H3 | I/Q resolution | HW-001 | FIXED 8 bit unsigned per I and Q | DATASHEET, REF-001 §Specifications | HARD | CONFIRMED |
| H4 | DC spike at the tuned centre | HW-001 | FIXED present at every centre frequency | DATASHEET, REF-001 §Known issues | SOFT | PRELIMINARY |
| H5 | Reference oscillator | HW-001 | FIXED 1 ppm TCXO | DATASHEET, REF-001 §Specifications | INFORMATIONAL | CONFIRMED |
| B1 | Sustained USB throughput HW-001 → HW-003 | HW-003 | MIN 4.8 MB/s | DERIVED, REF-001 §Specifications; REF-002 §Interfaces | SOFT | PRELIMINARY |
| C1 | Edge compute | HW-003 | FIXED 4 cores ARM Cortex-A72 64-bit / 4 GB / Raspberry Pi OS 64-bit | DATASHEET, REF-002 §Specifications | INFORMATIONAL | CONFIRMED |

### A.5 References

REF-001 RTL-SDR Blog V4 user guide (2023) · REF-002 Raspberry Pi 4 Model B product brief
(2024) · REF-003 ITU Radio Regulations Vol. 1 (Edition 2024) · REF-004 ITU-R BS.450-4 (2019) ·
REF-005 47 CFR Part 73 §73.201 · REF-006 Welch 1967, IEEE Trans. Audio Electroacoust. 15(2) ·
REF-007 Harris 1978, Proc. IEEE 66(1) · REF-008 ISO/IEC 25010:2023.

## Part B — System-level technical annex (systems engineer)

Measurands: per-channel occupancy (ratio 0–1) · per-channel mean power (dBFS) · noise floor
(dBFS) · sweep period (s) · end-of-sweep → dashboard latency (ms) · dropped buffers (count).
Power is relative to ADC full scale.

| # | Specification | Type | Method / values | Derives from | Standard | Acceptance |
|---|---------------|------|-----------------|--------------|----------|------------|
| Y1 | Sweep configuration | MEASUREMENT | fs 2.4 MS/s; 10 steps, centres 89.0, 91.0, …, 107.0 MHz; only the central ±1.0 MHz of each step is used; settle 20 ms, dwell 100 ms per step | R1, N1, H1, H2 | ITU RR Art. 5 | steps cover 88.0–108.0 MHz with no gap; sweep period 1.2 s |
| Y2 | Sample conversion | PROCESSING | interleaved uint8 (I,Q) → complex64, x = ((I − 127.5) + j(Q − 127.5))/127.5 | H3 | — | `[255, 0]` → `1.0 − 1.0j`; order and count kept |
| Y3 | Power spectrum per step | PROCESSING | Hann, N = 1024; P_k = 10·log10(mean over K = 64 frames of \|X_k\|²/(Σw)²); bin spacing 2.344 kHz | R3, N3 | ITU-R BS.450-4 | amp-1.0 tone 0.0 ± 0.1 dBFS; RBW = 1.5·fs/N = 3.52 kHz ≤ 25 kHz |
| Y4 | DC spike placement | PROCESSING | step centres at whole odd MHz fall midway between channel centres (odd tenths), so the DC bins N/2 ± 2 are excluded from every channel | H4, N2 | — | no channel window contains bins N/2 ± 2 |
| Y5 | Channel power | PROCESSING | for channel n, mean of P_k over the bins within ±90 kHz of 88.1 + 0.2·n MHz (covers the ±75 kHz deviation, stays 10 kHz clear of the step centres and edges) | R1, N2 | 47 CFR §73.201 | 100 channel powers per sweep; a 98.1 MHz tone lands in channel n = 50 |
| Y6 | Occupancy | PROCESSING | noise floor = median of all used bins of the sweep; channel occupied in a sweep when its power − floor ≥ 10 dB; occupancy = occupied sweeps / sweeps in the last 60 s | R1 | — | labelled scene (on-air channels at −30 dBFS, floor −70 dBFS): on-air ≥ 0.95, empty ≤ 0.05 |
| Y7 | Dashboard | QUALITY | one page served by the edge node over HTTP on the LAN; one bar per channel, ticks every 2 MHz, last sweep time, edge status; new data pushed after every sweep | R2, R4 | ISO/IEC 25010:2023 | page shows 100 bars and updates after every sweep; no page reload needed |
| Y8 | Latency budget | QUALITY | end of sweep → occupancy ≤ 300 ms + edge → browser ≤ 200 ms + render ≤ 300 ms = 800 ms, margin 700 ms | R2, C1 | ISO/IEC 25010:2023 | p95 ≤ 1.5 s over 60 s; each term reported |
| Y9 | Throughput without drops | QUALITY | continuous USB consumption at 4.8 MB/s; dropped buffers counted per sweep and logged with timestamp | R5, B1 | ISO/IEC 25010:2023 | 30 min: ≤ 3 dropped buffers, no crash |
| Y10 | Software platform | QUALITY | edge: Python ≥ 3.12 + numpy, one SDR access path; dashboard: TypeScript in the browser; libraries chosen at S1 | R6, C1 | ISO/IEC 25010:2023 | manifests list Python ≥ 3.12 and numpy on the edge, TypeScript for the dashboard |

Method rationale: stepped sweep at 2.4 MS/s (rejected: wider single capture — above the
no-drop rate of HW-001); Hann N = 1024 K = 64 (rejected: single periodogram); DC spike placed
between channels by choosing the step centres (rejected: DC interpolation — not needed when no
channel window contains the DC bins); fixed 10 dB threshold over the median floor (rejected:
per-channel adaptive threshold — not needed for occupancy).

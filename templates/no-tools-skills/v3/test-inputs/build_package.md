# Build Package — Real-Time FM Spectrogram (HackRF One)

> Test input for skill **S0-1**. S0 normalises only (V-SIL v3 §3), so this Build Package
> carries everything the GT needs: stakeholder content (Part A) and the system-level
> technical annex from the systems engineer (Part B). Pure normalisation of this file should
> reproduce `G0_StRS.md` + `G0_SyRS.md`. Deleting Part B must leave SyRS placeholders and
> make G0 FAIL.

## Identity

| Item | Value |
|------|-------|
| Project | Real-Time FM Spectrogram (HackRF One) · acronym FMSPEC |
| Organisation | GCPDS — Universidad Nacional de Colombia |
| Classification | PUBLIC · version 1.0.0 · date 2026-11-01 |
| Stakeholder / author | D. Ramírez · reviewer and approver: GCPDS lab lead |
| Objectives | OBJ-001 observe the FM band · OBJ-002 live feel · OBJ-003 safe lab use · OBJ-004 maintainable |

## Part A — Stakeholder content

### A.1 Scope and users

Live waterfall of the commercial FM band (88–108 MHz) from a HackRF One, shown on the lab PC.
Out of scope: audio demodulation, I/Q recording, calibrated dBm/field-strength measurement,
any transmission. Users: students (basic, observe the band) and lab engineers (technical,
start the system, tune gain, run soak tests). New standalone system. Assumptions: line of
sight to local FM transmitters; no other heavy USB/CPU load on the host; HackRF firmware and
libhackrf per REF-002.

### A.2 Normative obligations

| # | Obligation | Source | Clause | Priority | Acceptance |
|---|------------|--------|--------|----------|------------|
| N1 | Observe the Region 2 BROADCASTING allocation 88–108 MHz | ITU Radio Regulations | Article 5, Table of Frequency Allocations, 88–108 MHz (Region 2) | MUST | span covers 88.0–108.0 MHz |
| N2 | No unnecessary transmissions — receive only | ITU Radio Regulations | No. 15.1 | MUST | no code path enables HackRF TX |
| N3 | Resolve FM emissions with max. deviation ±75 kHz | ITU-R BS.450-4 | Annex 1, maximum frequency deviation | SHOULD | RBW ≤ 25 kHz (one third of 75 kHz) |

### A.3 Stakeholder requirements

| # | Need | Type | Priority | Verification | Acceptance |
|---|------|------|----------|--------------|------------|
| R1 | Live scrolling waterfall spanning 88.0–108.0 MHz on the host screen (depends on N1, H1, H2) | FUNCTIONAL | MUST | DEMONSTRATION | axis spans 88.0–108.0 MHz; known local stations at licensed frequency ± 1 FFT bin |
| R2 | ≥ 10 waterfall lines/s; on-air event on screen within 500 ms (depends on R1) | NON_FUNCTIONAL | MUST | TEST | line rate ≥ 10/s over 60 s; latency p95 ≤ 500 ms |
| R3 | RBW 25 kHz or finer so stations 200 kHz apart show as separate traces (depends on N3) | NON_FUNCTIONAL | MUST | ANALYSIS | analysis RBW ≤ 25 kHz; two tones 200 kHz apart → two peaks |
| R4 | Frequency axis in MHz, power colour in dBFS, adjustable range default −80…0 dBFS (depends on R1) | FUNCTIONAL | SHOULD | TEST | −20 dBFS tone reads −20 ± 0.5 dBFS; range changeable at runtime |
| R5 | Change LNA/VGA gain while running (depends on H4) | FUNCTIONAL | COULD | DEMONSTRATION | gain change visible within 1 s without restart |
| R6 | 30 min unattended, ≤ 1 sample-overflow event per 10 min (depends on B1) | NON_FUNCTIONAL | MUST | TEST | 30-min soak: ≤ 3 overflows, no crash |
| R7 | Receive-only operation of the HackRF (depends on N2) | CONSTRAINT | MUST | INSPECTION | no `hackrf_start_tx` or GNU Radio sink to the HackRF |
| R8 | Python ≥ 3.10 with GNU Radio 3.10 or libhackrf (designers choose) (depends on C1) | CONSTRAINT | MUST | INSPECTION | dependency list: Python ≥ 3.10 + GNU Radio 3.10 or libhackrf (+ pure-Python/numpy) |

### A.4 COTS hardware (not negotiable)

| ID | Item | Part | Role |
|----|------|------|------|
| HW-001 | Great Scott Gadgets HackRF One | HACKRF-ONE | RF front end, tuner, 8-bit I/Q ADC (RX only) |
| HW-002 | Great Scott Gadgets ANT500 telescopic antenna | ANT500 | VHF receive antenna |
| HW-003 | Lab host PC, generic x86-64 | 4-core / 8 GB / USB 2.0 | runs all software, drives the display |

Connections: HW-002 → HW-001 SMA coaxial (RF analog); HW-001 → HW-003 USB 2.0 High-Speed
bulk, 480 Mbit/s theoretical, ≈ 40 MB/s sustained (= 20 MS/s × 2 B).

| # | Constraint | Component | Limit | Source | Impact | Status |
|---|------------|-----------|-------|--------|--------|--------|
| H1 | Centre frequency | HW-001 | RANGE 1 MHz – 6 GHz | DATASHEET, REF-001 §Specifications | HARD | CONFIRMED |
| H2 | Complex sample rate (= span); 20 MHz for the band is the maximum, edges on filter roll-off | HW-001 | RANGE 2 – 20 MS/s | DATASHEET, REF-001 §Specifications | HARD | CONFIRMED |
| H3 | I/Q resolution; ideal SQNR ≈ 49.9 dB | HW-001 | FIXED 8 bit signed per I and Q | DATASHEET, REF-001 §Specifications | HARD | CONFIRMED |
| H4 | Gain steps | HW-001 | ENUM LNA 0, 8, …, 40 dB; VGA 0–62 dB in 2 dB steps | DRIVER_API, REF-002 `hackrf_set_lna_gain`, `hackrf_set_vga_gain` | HARD | CONFIRMED |
| H5 | DC spike at tuned centre (falls inside the band at 98 MHz) | HW-001 | FIXED present at every centre frequency | DATASHEET, REF-001 §FAQ "DC spike" | SOFT | CONFIRMED |
| A1 | Antenna usable range | HW-002 | RANGE 75 MHz – 1 GHz | DATASHEET, REF-003 §Specifications | INFORMATIONAL | CONFIRMED |
| B1 | Sustained USB 2.0 throughput HackRF → host; 20 MS/s at the ceiling, confirm by measurement | HW-003 | MAX ≈ 40 MB/s | DERIVED, REF-006 §5.8 bulk transfers; REF-001 §Specifications | SOFT | PRELIMINARY |
| C1 | Host compute and display | HW-003 | FIXED 4 cores x86-64 / 8 GB / 1920×1080 at 60 Hz | MEASURED, REF-001 §Host requirements; lab inventory sheet | INFORMATIONAL | CONFIRMED |

### A.5 References

REF-001 HackRF One hardware documentation (2024.02.1) · REF-002 libhackrf API `hackrf.h`
(2024.02.1) · REF-003 ANT500 product documentation (2023) · REF-004 ITU Radio Regulations
Vol. 1 (Edition 2024) · REF-005 ITU-R BS.450-4 (2019) · REF-006 USB 2.0 Specification (2000) ·
REF-007 IEEE Std 1241-2010 · REF-008 ISO/IEC 25010:2023 · REF-009 Harris 1978, Proc. IEEE 66(1) ·
REF-010 Welch 1967, IEEE Trans. Audio Electroacoust. 15(2).

## Part B — System-level technical annex (systems engineer)

Measurands: per-bin relative power (dBFS) · bin centre frequency (MHz) · line rate (lines/s)
· end-to-end latency (ms) · overflow events (count). Power is relative to ADC full scale.

| # | Specification | Type | Method / values | Derives from | Standard | Acceptance |
|---|---------------|------|-----------------|--------------|----------|------------|
| Y1 | Acquisition configuration | MEASUREMENT | f_c 98.0 MHz, fs 20.0 MS/s, baseband filter 20 MHz explicitly set, RX amp off, LNA 16 dB, VGA 20 dB | R1, N1, H1, H2, A1 | ITU RR Art. 5 | SDR reports f_c/fs; filter set to 20 MHz (not ≈ 0.75·fs default) |
| Y2 | Sample conversion | PROCESSING | interleaved int8 (I,Q) → complex64, x = (I + jQ)/128 | H3, R4 | IEEE Std 1241-2010 | `[127,0,-128,0]` → `[0.9921875+0j, -1.0+0j]`; order and count kept |
| Y3 | Power spectrum per line | PROCESSING | Hann, N = 2048; P_k = 10·log10(mean over K = 16 frames of \|X_k\|²/(Σw)²) | R3, R4, N3 | ITU-R BS.450-4; IEEE Std 1241-2010 | amp-1.0 tone 0.0 ± 0.1 dBFS; amp-0.1 tone −20.0 ± 0.5 dBFS; tones 200 kHz apart dip ≥ 20 dB; RBW = 1.5·fs/N = 14.65 kHz |
| Y4 | DC spike mitigation | PROCESSING | bins N/2 ± 2 replaced by linear interpolation between N/2 − 3 and N/2 + 3 | H5, R1 | IEEE Std 1241-2010 | DC 0.1 FS + AWGN: centre within 3 dB of neighbours; other bins bit-exact; masks ±19.5 kHz at 98.0 MHz |
| Y5 | Frequency axis | PROCESSING | f_k = f_c + (k − N/2)·fs/N after fftshift; extent 88.0–108.0 MHz | R1, R4 | ITU RR Art. 5 | f_0 = 88.000, f_1024 = 98.000, f_2047 = 107.990 MHz (± 1 Hz); −1.0 MHz tone at bin 921/922 |
| Y6 | Waterfall rendering | QUALITY | newest line on top, target 20 lines/s, 200-line history, colour range default [−80, 0] dBFS, ticks every 2 MHz | R1, R2, R4 | ISO/IEC 25010:2023 | ≥ 10 lines/s over 60 s; range change next line; ticks 88…108 |
| Y7 | Latency budget | QUALITY | USB/driver ≤ 100 ms + accumulation ≤ 50 + processing ≤ 50 + rendering ≤ 50 = 250 ms, margin 250 ms | R2, C1 | ISO/IEC 25010:2023 | p95 ≤ 500 ms over 60 s; each term reported |
| Y8 | Throughput without overflow | QUALITY | continuous USB consumption; each line uses K = 16 frames per 50 ms, rest discarded | R6, B1 | ISO/IEC 25010:2023 | 30 min: ≤ 3 overflows, no crash; overflows logged with timestamp |
| Y9 | Runtime gain control | PROTOCOL | validate LNA ∈ {0,8,…,40}, VGA ∈ {0,2,…,62}, round down; apply without stopping stream | R5, H4 | ISO/IEC 25010:2023 | LNA 13 → 8, VGA 63 → 62; applied ≤ 200 ms |
| Y10 | Receive-only | PROTOCOL | hardware abstraction exposes RX only | R7, N2 | ITU RR No. 15.1 | no `hackrf_start_tx`, `hackrf_set_txvga_gain`, TX sink |
| Y11 | Software platform | QUALITY | Python ≥ 3.10 + numpy; GNU Radio 3.10 (gr-osmosdr) or libhackrf; GUI library chosen at S1 | R8, C1 | ISO/IEC 25010:2023 | manifest: Python ≥ 3.10, numpy, exactly one SDR access path |

Method rationale: single 20 MHz capture (rejected: two-half sweep — halves line rate per
half-band, retune settling); Hann N = 2048 K = 16 (rejected: single periodogram,
Blackman-Harris N = 1024); centre-bin interpolation (rejected: offset tuning — needs > 20 MS/s;
hardware DC calibration); software timestamps (rejected: oscilloscope).

Corrections: int8 full-scale scaling (Y2) · window coherent gain (Σw)² (Y3, REF-009) · DC
interpolation (Y4). No antenna factor / cable loss (relative dBFS).

Uncertainty: scalloping 0–1.42 dB rect. (u 0.41 dB) · averaging K = 16 ≈ 4.34/√K (u 1.09 dB) ·
8-bit quantisation (u < 0.01 dB) · bin spacing 9.766 kHz rect. (u 2.82 kHz) · reference
oscillator ±20 ppm at 98 MHz = ±1.96 kHz rect. (u 1.13 kHz).

Protocols: PROTO-001 off-air station check (Y1, Y5, Y6) · PROTO-002 60 s timing log + 30-min
soak (Y7, Y8) · PROTO-003 gain steps while running + TX code inspection (Y9, Y10).

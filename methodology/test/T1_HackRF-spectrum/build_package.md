# Build Package — HackRF One Real-Time Spectrum Viewer with Live Parameter Control (HackRF One → x86_64 PC)

> Test input for the T4 end-to-end run. Two services: an `sdr_edge` DSP/streaming service and a
> browser UI, both on the same PC. The HackRF One is a real device connected to the PC over USB;
> the Real HW HAL is built and declared, and this cycle's run exercises the Mock HAL up to VL-1
> while VL-2 waits for a connected board. It has **no lab inputs**: no correction chains, no
> uncertainty budgets, no field measurement protocols (this is a relative-power spectrum viewer,
> not a calibrated measurement), so S0 writes `Not applicable: no lab inputs in the Build Package.`
> under SyRS §4, §5 and §6. The test oracle is fixed here by the author: the Mock HAL signal model
> (B.2), the labelled parameter scenarios (B.3) and the VL-0 golden vectors (B.4). No ML model is
> used.

## Identity

| Item | Value |
|------|-------|
| Project | HackRF One Real-Time Spectrum Viewer with Live Parameter Control · acronym HRTS |
| Organisation | GCPDS — Universidad Nacional de Colombia |
| Classification | PUBLIC · version 1.0.0 · date 2026-11-09 |
| Stakeholder / author | D. Ramírez · reviewer and approver: GCPDS lab lead |
| Objectives | OBJ-001 see the live power spectrum of the tuned slice at the highest sustainable update rate · OBJ-002 change every HackRF RX parameter live from the UI and see the spectrum react · OBJ-003 keep capture-to-display latency low enough for interactive tuning · OBJ-004 run on this PC with a HackRF One over USB, in one cycle |

## Part A — Stakeholder content

### A.1 Scope and users

A HackRF One connected to an x86_64 PC over USB 2.0 receives a tunable slice of spectrum. The
`sdr_edge` service streams the 8-bit I/Q at the configured sample rate, computes a continuous
power spectrum and serves it over a local WebSocket. A browser UI on the same PC (localhost)
shows the live spectrum and exposes controls for every HackRF receive parameter: centre
frequency, sample rate, baseband filter bandwidth, LNA gain, VGA gain, RF amplifier and antenna
port power (bias-tee). Users: RF engineers (set parameters, read the spectrum, run the tests) and
students (read the spectrum). New standalone system with two services on one host.

This cycle is verified with the Mock HAL and the labelled scenarios of B.3 up to VL-1. The Real
HW HAL for the HackRF One is built and its interface declared; running it at VL-2 needs a board
connected and is out of this cycle's recorded claims.

Out of scope: any transmission (the device is used receive-only), audio demodulation, I/Q
recording, calibrated dBm or field-strength measurement, persistence across restarts, more than
one device, and access from outside the host.

Assumptions: the PC runs a recent Linux with libhackrf installed; the UI browser is a recent
Chromium or Firefox on the same host; exactly one HackRF One is attached.

### A.2 Normative obligations

| # | Obligation | Source | Clause | Priority | Acceptance |
|---|------------|--------|--------|----------|------------|
| N1 | Operate the device receive-only; never enable transmission | Project safety policy; transmission requires a licence | GCPDS RF lab policy §2 (receive-only bench use) | MUST | the HAL exposes no transmit path; no `hackrf_start_tx` call exists in the delivered code |
| N2 | Keep the RF input below the level that saturates the 8-bit ADC or risks the front end | HackRF One documentation | HackRF FAQ, "What is the maximum input power?" | MUST | when any spectrum bin clips the ADC full scale, the UI shows a clip warning and the current gain values |
| N3 | Keep the tuned slice within the device tuning range | HackRF One datasheet | | MUST | fc ± span/2 stays within 1 MHz – 6 GHz; a centre frequency outside the range is refused at the edge before any device call |

### A.3 Stakeholder requirements

| # | Need | Type | Priority | Verification | Acceptance |
|---|------|------|----------|--------------|------------|
| R1 | Live power spectrum of the tuned slice, updated at the highest rate the host sustains (depends on N2, N3, H1, H2, H3) | FUNCTIONAL | MUST | TEST | at fs = 8 MS/s on the COTS PC, ≥ 15 spectra per second sustained over 60 s with no dropped-sample growth; golden vector GV-2 peaks at the expected bin |
| R2 | Change any HackRF receive parameter live from the UI — centre frequency, sample rate, baseband filter bandwidth, LNA gain, VGA gain, RF amplifier, antenna port power — and see the spectrum react (depends on R1, H1, H2, H4, H5, H6, H7, H8, H9) | FUNCTIONAL | MUST | TEST | each parameter command is applied within 300 ms, the next spectrum message reports the applied value, and B.3 scenarios give their expected result |
| R3 | Capture-to-display latency low enough for interactive tuning (depends on R1, C1) | NON_FUNCTIONAL | MUST | TEST | capture end → UI render p95 ≤ 150 ms at fs = 8 MS/s over 60 s |
| R4 | One browser page: the spectrum plot and a parameter control panel showing the active values (depends on R1, R2) | FUNCTIONAL | SHOULD | DEMONSTRATION | the page loads on localhost; the controls change the live spectrum with no reload |
| R5 | A throughput and dropped-sample indicator so the user knows when the chosen sample rate is unsustainable on this host (depends on R1, H2, C1) | NON_FUNCTIONAL | SHOULD | TEST | |
| R6 | DSP/edge service in Python ≥ 3.12; UI service in TypeScript in the browser (depends on C1) | CONSTRAINT | MUST | INSPECTION | manifests: Python ≥ 3.12 and numpy for the edge service, TypeScript for the UI |

### A.4 COTS hardware (not negotiable)

| ID | Item | Part | Role |
|----|------|------|------|
| HW-001 | HackRF One (Great Scott Gadgets) | HACKRF-ONE | RF front end, tuner, 8-bit I/Q ADC, used receive-only |
| HW-002 | SMA receive antenna (ANT500 telescopic) | ANT500 | receive antenna |
| HW-003 | Host PC with a browser | generic-x86_64 | runs the edge service, hosts the USB link and serves the UI on localhost |

Connections: HW-002 → HW-001 SMA coaxial (RF analog); HW-001 → HW-003 USB 2.0 High-Speed bulk,
up to 40 MB/s at 20 MS/s × 2 B; HW-003 serves the UI to its own browser over localhost
(HTTP and WebSocket).

| # | Constraint | Component | Limit | Source | Impact | Status |
|---|------------|-----------|-------|--------|--------|--------|
| H1 | Tuning range | HW-001 | RANGE 1 MHz – 6 GHz | DATASHEET, REF-001 §Specifications | HARD | CONFIRMED |
| H2 | Complex sample rate without dropped samples | HW-001 | RANGE 2 – 20 MS/s, USB 2.0 High-Speed bound | DATASHEET, REF-001 §Specifications | HARD | CONFIRMED |
| H3 | I/Q resolution | HW-001 | FIXED 8 bit signed per I and Q, interleaved | DATASHEET, REF-001 §Specifications | HARD | CONFIRMED |
| H4 | LNA (IF) gain | HW-001 | RANGE 0 – 40 dB in 8 dB steps | DATASHEET, REF-001 §Specifications | HARD | CONFIRMED |
| H5 | VGA (baseband) gain | HW-001 | RANGE 0 – 62 dB in 2 dB steps | DATASHEET, REF-001 §Specifications | HARD | CONFIRMED |
| H6 | RF amplifier | HW-001 | FIXED 0 or ~11 dB, on/off | DATASHEET, REF-001 §Specifications | HARD | CONFIRMED |
| H7 | Baseband filter bandwidth | HW-001 | SET {1.75, 2.5, 3.5, 5, 5.5, 6, 7, 8, 9, 10, 12, 14, 15, 20, 24, 28} MHz | DATASHEET, REF-001 §libhackrf | HARD | CONFIRMED |
| H8 | USB interface | HW-001 | FIXED USB 2.0 High-Speed 480 Mbps, half-duplex | DATASHEET, REF-001 §Specifications | HARD | CONFIRMED |
| C1 | Host compute | HW-003 | FIXED AMD Ryzen 7 7730U, 8 cores / 16 threads capped at 2.0 GHz (governor powersave), 15 GiB RAM, AMD USB 3.1 host, x86_64 Linux (Omarchy) | DATASHEET, REF-002 | INFORMATIONAL | CONFIRMED |

The CPU's 2.0 GHz cap and powersave governor (C1) are the real headroom limit for the FFT rate;
the USB 2.0 High-Speed link (H8) is the real limit on sustainable sample rate.

### A.5 References

REF-001 HackRF One documentation, hackrf.readthedocs.io (stable) and the libhackrf source ·
REF-002 this host: `lscpu`, `lsusb -t`, `/sys/devices/system/cpu` readings (2026-11-09) ·
REF-003 Great Scott Gadgets HackRF One product page · REF-004 PySDR, "HackRF One in Python"
(pysdr.org) · REF-005 Welch 1967, IEEE Trans. Audio Electroacoust. 15(2) · REF-006 Harris 1978,
Proc. IEEE 66(1) · REF-007 ISO/IEC 25010:2023.

## Part B — System-level technical annex (systems engineer)

Measurands: power spectrum (dBFS per bin) · noise floor (dBFS) · spectrum update rate (Hz) ·
capture end → UI render latency (ms) · dropped-sample count · the active parameter set. Power is
relative to ADC full scale.

### B.1 Specifications

| # | Specification | Type | Method / values | Derives from | Standard | Acceptance |
|---|---------------|------|-----------------|--------------|----------|------------|
| Y1 | Capture | MEASUREMENT | fs configurable 2–20 MS/s (default 8); one centre fc, default 98.0 MHz, any value with fc ± fs/2 inside 1 MHz – 6 GHz; continuous RX; the spectrum update rate follows the FFT throughput, not a fixed period | R1, N3, H1, H2 | — | fc and fs validated at the edge; an fc or fs outside the ranges is refused before any device call |
| Y2 | Sample conversion | PROCESSING | interleaved int8 (I,Q) → complex64, x = (I + jQ)/128.0 | H3 | — | golden vector GV-1 |
| Y3 | Power spectrum | PROCESSING | per update, the K most recent non-overlapping frames of N = 4096 samples; Hann window; P = 10·log10(mean over frames of \|X\|²/(Σw)²), FFT-shifted; bin spacing fs/N (1953.125 Hz at 8 MS/s); output all N bins | R1 | REF-005, REF-006 | golden vector GV-2; RBW = 1.5·fs/N |
| Y4 | Noise floor | PROCESSING | 10th percentile of the update's N bins, in dBFS | R1 | — | golden vector GV-4 |
| Y5 | Parameter command handling | PROCESSING | each UI parameter maps to one libhackrf call: fc→`set_freq`, fs→`set_sample_rate`, bb→`set_baseband_filter_bandwidth` (rounded down to the nearest H7 value), LNA→`set_lna_gain` (clamped to the H4 grid), VGA→`set_vga_gain` (clamped to the H5 grid), amp→`set_amp_enable`, bias→`set_antenna_enable`; an out-of-range value is refused and the current value kept | R2, H1, H2, H4, H5, H6, H7 | — | golden vector GV-3; every scenario of B.3 |
| Y6 | Spectrum → UI contract | QUALITY | one JSON message per update over WebSocket: `{"v": 1, "t_capture_end": <ISO 8601 ms>, "fc_hz": <int>, "fs_hz": <int>, "bin_hz": <number>, "spectrum_dbfs": [N numbers, 0.1 dB], "floor_dbfs": <number>, "params": {"lna_db": <int>, "vga_db": <int>, "amp": <bool>, "bb_bw_hz": <int>, "bias": <bool>}, "update_rate_hz": <number>, "dropped_samples": <int>}` | R1, R2, R4, R5 | REF-007 | a message missing a field or with `v` ≠ 1 is rejected by the UI and logged; golden vector GV-5 |
| Y7 | UI → edge control contract | QUALITY | one JSON command over WebSocket: `{"v": 1, "cmd": "set_params", "fc_hz"?, "fs_hz"?, "bb_bw_hz"?, "lna_db"?, "vga_db"?, "amp"?, "bias"?}`; the edge validates per Y5, applies, and acknowledges with the applied values in the next Y6 message | R2 | REF-007 | golden vector GV-3; an out-of-range field is refused, acknowledged unchanged and logged |
| Y8 | Latency budget | QUALITY | capture end → message sent ≤ 100 ms + localhost ≤ 10 ms + render ≤ 40 ms = 150 ms | R3, C1 | REF-007 | p95 ≤ 150 ms over 60 s at fs = 8 MS/s; each term reported |
| Y9 | Throughput indicator | QUALITY | the edge reports `update_rate_hz` and cumulative `dropped_samples` in every Y6 message; the UI shows both and warns when `dropped_samples` grows between updates | R5, H2 | REF-007 | dropped-sample growth is visible in the UI within one update of its occurrence |
| Y10 | Software platform | QUALITY | edge service: Python ≥ 3.12 + numpy, one SDR access path behind the HAL (Mock HAL and Real HW HAL share it); UI service: TypeScript in the browser; libraries chosen at S1 | R6, C1 | REF-007 | manifests list Python ≥ 3.12 and numpy for the edge, TypeScript for the UI |

An em dash in `Standard` means no external normative source prescribes that method; its values and
acceptance criteria are specified by this Build Package.

### B.2 Mock HAL signal model

The Mock HAL emits exactly what HW-001 emits: interleaved int8 I/Q at the configured fs centred at
fc. It also honours the parameter commands of Y5 so the parameter round-trip can be tested without
a board. Each scenario is generated from its parameters and a seed; the same parameters and seed
give the same bytes.

| Element | Model |
|---------|-------|
| Noise | complex white Gaussian, total power σ² = −30 dBFS, putting the per-bin floor of Y3 near −66 dBFS at N = 4096 |
| Tone | A·exp(j·2π·Δf·t): Δf = tone frequency − fc; A from the level in dBFS (20·log10 A) |
| Gain response | the applied LNA + VGA + RF-amp gain (H4, H5, H6) scales the tone and noise amplitude in dB before quantisation, so raising a gain raises every level by the same dB |
| Sample-rate response | changing fs changes the span and bin spacing of Y3; the tone stays at the same absolute frequency |
| Quantisation | I = clip(round(128·Re x), −128, 127), same for Q, interleaved int8 I, Q |

### B.3 Labelled scenarios (acceptance oracle for R2)

Each scenario starts from the default state (fc = 98.0 MHz, fs = 8 MS/s, LNA = 16 dB, VGA = 20 dB,
amp off, bb = 10 MHz) and applies one parameter command, then checks the next spectrum.

| Scenario | Command | Expected result |
|----------|---------|-----------------|
| SC-1 | none (baseline) | a tone seeded at 98.1 MHz appears at bin N/2 + round(0.1 MHz / bin_hz); floor near −66 dBFS |
| SC-2 | set fc_hz = 98 100 000 | the same tone now appears at the centre bin N/2 (DC) |
| SC-3 | set lna_db = 24 (from 16, +8 dB) | the tone level rises by 8.0 ± 0.5 dB; the floor rises by 8.0 ± 0.5 dB |
| SC-4 | set fs_hz = 16 000 000 | the span doubles and bin_hz doubles; the tone stays at 98.1 MHz, now at bin N/2 + round(0.1 MHz / bin_hz) |
| SC-5 | set lna_db = 33 (not on the 8 dB grid) | refused: the command is clamped to 32, acknowledged as 32, and logged |
| SC-6 | set bb_bw_hz = 4 000 000 (not a supported value) | rounded down to 3 500 000, acknowledged as 3 500 000 |
| SC-7 | set fc_hz = 7 000 000 000 (above range) | refused: fc stays at the previous value, acknowledged unchanged, logged |

Labelling procedure:

1. The expected result is written by the author before any data exists.
2. The Mock HAL generator takes only the parameters and seed; it never reads the expected result.
3. The golden manifest copies each scenario's command and expected result as its expected output.
4. Nobody derives an expected result from the implementation's output. Changing a scenario is a
   change to this Build Package and starts again at S0.

### B.4 VL-0 golden vectors

Short, deterministic inputs; each is versioned in the golden manifest with its SHA-256.

| Vector | Input | Expected output |
|--------|-------|-----------------|
| GV-1 | int8 bytes `[127, -128, 0, 64]` | complex64 `[0.9921875 − 1.0j, 0.0 + 0.5j]` (± 1e-6) |
| GV-2 | K × 4096 complex64 samples of a tone of amplitude 1.0 at +64 bins, no noise, fed to Y3 | maximum of P at bin N/2 + 64, value 0.0 ± 0.1 dBFS |
| GV-3 | the default parameter state, then control commands `lna_db = 24`, `bb_bw_hz = 4_000_000`, `lna_db = 33` | applied params `lna_db = 24` then `32`, `bb_bw_hz = 3_500_000`; the 33 is clamped to 32 |
| GV-4 | one update (K × 4096 samples) of SC-1 through the Mock HAL with seed 1 | noise floor −66 ± 1 dBFS; tone peak ≥ 20 dB above floor |
| GV-5 | one fixed Y6 message with the default params | the UI shows the spectrum and the panel reflects lna 16, vga 20, amp off, bb 10 MHz; a copy with `v` = 2 is rejected and logged |

Method rationale: continuous RX with a running FFT (rejected: one-shot capture per request — adds
round-trip latency and misses the interactive feel); Welch with Hann N = 4096 (rejected: single
periodogram — too noisy to read a floor); noise floor at the 10th percentile (rejected: the median
— rises into strong tones); parameter values clamped and rounded to the hardware grid at the edge
(rejected: rejecting any off-grid value — a worse user experience than snapping to the nearest
legal value).

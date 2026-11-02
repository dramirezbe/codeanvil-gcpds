# Test inputs — Real-Time FM Spectrogram (HackRF One)

Test case for the v3 chat-only skills: a live waterfall of the 88–108 MHz FM band from a
HackRF One, in Python with GNU Radio 3.10 or libhackrf.

| File | Use with | Expected result |
|------|----------|-----------------|
| `build_package.md` | `S0-1` | A StRS/SyRS pair equivalent to the two files below (Part A → StRS, Part B technical annex → SyRS; without Part B → SyRS placeholders → G0 FAIL) |
| `G0_StRS.md` + `G0_SyRS.md` | `S0-2` | `G0 GATE VERDICT: PASS` (the deterministic `g0_validate.py` gives 0 errors, 0 warnings on both + G0-X) |
| `G0_StRS.md` + `G0_SyRS.md` + G0 Record | `S1-1` | Layered design: HAL for the HackRF, DSP modules (conversion, PSD, DC fix, axis), waterfall buffer/view, gain control |

## Built-in pressure points (things the flow should discover)

| Where | What | Expected handling |
|-------|------|-------------------|
| S1 / G1 | DC spike at 98.0 MHz masks ±19.5 kHz (`SYS-PSD-002`) | Risk RSK in S1 §6, accepted limitation |
| S1 / G2.2 | Driver default baseband filter (≈ 0.75·fs) cuts the band edges (`SYS-ACQ-001`) | Contract on the HAL; HIL check of edge level |
| G2.2 | 20 MS/s is the USB 2.0 sustained ceiling (`HWC-BUS-001` PRELIMINARY) | If overflows exceed `STK-OPS-001` at 20 MS/s while 16 MS/s meets it but loses 88–90 / 106–108 MHz (`STK-SPEC-001`), `STK-SPEC-001` and `STK-OPS-001` are not met simultaneously → `SX-1` RFD (paper §9.2–9.3), options e.g. A) relax coverage, B) relax overflow limit, C) two-half sweep (new module + contract, S1 rework — like RFD-001 option C), D) host with another USB controller |
| G2.1 | dBFS normalisation (`SYS-PSD-001`: 0.1-amplitude tone → −20 ± 0.5 dBFS) | Golden-vector SIL test |

## Caveats

Values come from public HackRF One / ANT500 documentation and ITU texts as commonly cited.
Clause numbers (e.g. ITU-R BS.450-4 "Annex 1") are illustrative for testing the methodology;
check them against the official texts before using this GT for real compliance work.

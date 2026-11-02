# Build Package — Real-Time FM Spectrogram (HackRF One)

> Test input for skill **S0-1** (Build Package normalisation). Deliberately informal, the
> way a Build Package usually arrives. Expected S0-1 output ≈ `G0_StRS.md` + `G0_SyRS.md`
> in this folder.

**Owner:** GCPDS — Universidad Nacional de Colombia · **Acronym:** FMSPEC ·
**Classification:** PUBLIC · **Author:** D. Ramírez (stakeholder)

## What we want

1. A live waterfall spectrogram of the whole commercial FM band, 88–108 MHz, on the lab PC
   screen.
2. It has to feel live: at least 10 new spectrogram lines per second, and what happens on
   air must show up on screen in under half a second.
3. We must be able to tell adjacent FM stations apart (200 kHz channel spacing here in
   Colombia), so the frequency resolution must be 25 kHz or finer.
4. Frequency axis in MHz, power colour scale in dBFS, with adjustable dynamic range
   (default −80 to 0 dBFS). Nice to have, not blocking.
5. Nice to have: change the RF gain (LNA / VGA) while it is running.
6. It must run 30 minutes unattended; at most 1 sample-overflow event per 10 minutes.
7. Receive only. The HackRF must never transmit (ITU Radio Regulations No. 15.1 — no
   unnecessary transmissions).
8. Software: Python 3.10+, either GNU Radio 3.10 (gr-osmosdr) or libhackrf directly — the
   designers choose.

## Hardware we already have (COTS, not negotiable)

| Item | Part | Datasheet facts we rely on |
|------|------|----------------------------|
| SDR | Great Scott Gadgets HackRF One | 1 MHz–6 GHz tuning; 2–20 MS/s; 8-bit I/Q ADC; half-duplex; USB 2.0 High-Speed; strong DC spike at the tuned centre; LNA gain 0–40 dB in 8 dB steps, VGA gain 0–62 dB in 2 dB steps |
| Antenna | Great Scott Gadgets ANT500 telescopic | 75 MHz–1 GHz, SMA male |
| Host | Lab PC, x86-64, 4 cores, 8 GB RAM, USB 2.0 port, 1920×1080 display at 60 Hz | USB 2.0 HS 480 Mbit/s theoretical; ~40 MB/s sustained is the practical ceiling |

## Normative context

- ITU Radio Regulations, Article 5 — Region 2 allocates 88–108 MHz to BROADCASTING.
- ITU Radio Regulations, No. 15.1 — no unnecessary transmissions.
- ITU-R BS.450-4 — FM sound broadcasting at VHF; maximum frequency deviation ±75 kHz.

## Acceptance (how we will judge it)

- Known local FM stations visible at the right frequencies (± 1 bin).
- A −20 dBFS synthetic tone reads −20 ± 0.5 dBFS on the colour scale.
- Line rate and latency measured with timestamps in the software.
- 30-minute soak test with overflow counter.

# T2 — Minimal RPi5/HackRF web spectrum Build Package

Status: authored; no methodology run or real hardware verdict recorded.

Request: one complete, simple Build Package with real VL-2, RPi5 + HackRF,
Vite dashboard served by its backend on all interfaces, and web-sourced standards.

T1 was reviewed as the closest precedent. It targets x86_64, defers VL-2 and has
deliberate faults; T2 supplies a separate clean input rather than changing that oracle.
The case has six stakeholder requirements, two normative obligations, nine COTS
constraints and five system specifications. It fixes seven RX controls, a small
NumPy FFT and HTTP polling, without audio/ML/waterfall or a second web server.
Official IETF and manufacturer sources are linked with retrieval date and sections.
The tolerances are project choices, not invented requirements of those standards.

## Verification

- `.venv/bin/python /tmp/t2-preflight.py`: passed. Extracted IDs and traces resolve;
  a temporary projection of the supplied tables into StRS/SyRS passes the existing
  G0 validator with exit 0, no errors or warnings. This is an authoring preflight,
  not an S0 run, Gate H decision or complete quality assessment.
- Independent direct DFT of the supplied vectors: exact tone peaks at bin 576,
  −6.020599913 dBFS; quantized mock peaks at bin 640, −6.045089914 dBFS; zero vector
  is −120 dBFS throughout. All lie within the published tolerances.
- Native runtime harness: N/A; this work creates an input specification, not the
  delivered application. PROTO-001 defines the future hardware experiment. No RPi,
  HackRF, project state, credentials or existing run artifacts were modified.
- Evidence files: `/tmp/codeanvil-t2-preflight/{summary.json,g0.txt,StRS.md,SyRS.md}`.

One local work unit on `feat/t2-rpi5-hackrf-web-spectrum`, below 400 authored
changed lines. Rollback: remove the new T2 directory and its catalog/AGENTS entries
and this task note; T0/T1, implementation and methodology contracts are unaffected.

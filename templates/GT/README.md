# Ground Truth (GT) Templates

Templates for the three Ground Truth documents that define the contract a project must satisfy. Based on **IEEE/ISO/IEC 29148:2018**.

## Documents

| File         | Document type                          | IEEE 29148 section |
|--------------|----------------------------------------|--------------------|
| `G0_SRS.md`  | System Requirements Specification      | Full standard      |
| `G0_HCS.md`  | Hardware Constraints Specification     | §2.4 (Design Constraints) |

The prefix `G0` indicates these are the templates validated at **Gate 0** — the deterministic structural check that must pass before any downstream gate runs.

A third GT document — **Normativity** (applicable standards: ITU, ICNIRP, IEEE, etc.) — is planned but not yet templated.

## How to use

1. Copy `G0_SRS.md` and `G0_HCS.md` into your project directory.
2. Replace placeholders (`_project_name_`, `_YYYY-MM-DD_`, etc.) with real content.
3. Write requirements (SRS) and hardware constraints (HCS) following the block format documented in each template.
4. Run the G0 validation skill once it is implemented (`templates/skills/G0_valid_req_and_GT/` — currently scaffolded but empty).

The templates assume that hardware constraints have already been incorporated into the SRS — every requirement is feasible within the hardware envelope. The documents do not contain reconciliation machinery; they are final, reviewed IEEE 29148 artifacts.

## Naming convention

```
G<n>_<NAME>.md
```

- `G<n>` — the gate number that validates this template (currently only G0).
- `<NAME>` — the document type (`SRS`, `HCS`, or future `NORM`).

## Working examples

Filled-in examples for a real project (ANE Edge Sensor — spectrum monitoring) live in `methodology/test/T0_ANE-Lap2/just-edge/`:

| File      | Description                                           |
|-----------|-------------------------------------------------------|
| `SRS.md`  | Edge sensor SRS (HackRF One + Raspberry Pi 4B)        |
| `HCS.md`  | Edge sensor hardware constraints specification        |

## Legacy

The `legacy/` folder contains previous template versions (v1, v2) that used a COTS-reconciliation methodology with cross-reference fields between SRS and HCS. These are kept for reference only and should not be used for new projects.

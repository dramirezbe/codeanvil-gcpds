# Ground Truth (GT) Templates

Templates for the Ground Truth document pair that defines the contract a project must
satisfy, plus the G1 software requirements template. Based on **IEEE/ISO/IEC 29148:2018**.

## Documents

| File         | Document type                          | IEEE 29148 section | Gate |
|--------------|----------------------------------------|--------------------|------|
| `G0_StRS.md` | Stakeholder Requirements Specification | §9.4               | G0 input |
| `G0_SyRS.md` | System Requirements Specification      | §9.5               | G0 input |
| `G1_SRS.md`  | Software Requirements Specification    | §9.6               | G1 output |

The `G0`/`G1` prefix indicates the gate that validates the document: **G0** is the
deterministic structural check of the StRS + SyRS pair (including the G0-X
cross-document rules); **G1** is the agent-driven design gate that produces and
structurally validates the SRS.

The StRS merges what were previously separate SRS and HCS templates: stakeholder
requirements (`STK-` blocks), COTS hardware constraints (`HWC-` blocks), and normative
obligations (`NRM-` blocks) live in one document, each with inline compliance
traceability (Standard(s), Clause, Compliance). The SyRS is the per-measurand system
view (`SYS-` blocks) that replaces the former Mathematical Formulation: methods,
parameters, correction chains, and uncertainty budgets, each tracing back to StRS
block IDs.

## How to use

1. Copy `G0_StRS.md` and `G0_SyRS.md` into your project's `GT/` directory.
2. Replace placeholders (`_project_name_`, `_YYYY-MM-DD_`, etc.) with real content.
3. Write stakeholder requirements, hardware constraints, and normative obligations
   (StRS) and the per-measurand system specifications (SyRS) following the block
   format documented in each template.
4. Validate the pair (deterministic, no AI):

   ```bash
   python templates/skills/G0_valid_req_and_GT/scripts/g0_validate.py GT/G0_StRS.md GT/G0_SyRS.md
   ```

5. After G0 passes and the design gate (G1) runs, the SRS is authored at
   `GT/G1_SRS.md` following the G1 template — it is not a G0 input.

The templates assume that hardware constraints have already been incorporated into the
StRS — every requirement is feasible within the hardware envelope. The documents do
not contain reconciliation machinery; they are final, reviewed IEEE 29148 artifacts.

## Naming convention

```
G<n>_<NAME>.md
```

- `G<n>` — the gate that validates this document (G0 inputs, G1 output).
- `<NAME>` — the document type (`StRS`, `SyRS`, `SRS`).

## Working examples

Filled-in examples for a real project (ANE Edge Sensor — spectrum monitoring) live in `methodology/test/T0_ANE-Lap2/just-edge/`:

| File       | Description                                                        |
|------------|--------------------------------------------------------------------|
| `StRS.md`  | Merged stakeholder requirements + hardware constraints + normativity |
| `SyRS.md`  | Per-measurand system specifications (27 SYS blocks)                |

## Legacy

The `legacy/` folder contains previous template versions: v1/v2 (COTS-reconciliation
methodology with cross-reference fields between separate SRS and HCS files) and v3
(the pre-29148-family `G0_SRS.md`/`G0_HCS.md` pair). These are kept for reference
only and should not be used for new projects.

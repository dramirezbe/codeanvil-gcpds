# Ground Truth (GT) Templates

Templates for the Ground Truth document pair that defines the contract a project must
satisfy. S0 casts the author's Build Package into them. Based on **IEEE/ISO/IEC 29148:2018**.

## Documents

| File         | Document type                          | IEEE 29148 section | Stage |
|--------------|----------------------------------------|--------------------|-------|
| `StRS.md`    | Stakeholder Requirements Specification | §9.4               | S0 output, G0 input |
| `SyRS.md`    | System Requirements Specification      | §9.5               | S0 output, G0 input |

**G0** is the deterministic structural check of the StRS + SyRS pair (including the G0-X
cross-document rules), followed by a human Gate H. The design (S1) is not an IEEE 29148
GT document; the retired `G1_SRS.md` template lives in `templates/backups/`.

The StRS merges what were previously separate SRS and HCS templates: stakeholder
requirements (`STK-` blocks), COTS hardware constraints (`HWC-` blocks), and normative
obligations (`NRM-` blocks) live in one document, each with inline compliance
traceability (Standard(s), Clause, Compliance). The SyRS is the per-measurand system
view (`SYS-` blocks) that replaces the former Mathematical Formulation: methods,
parameters, correction chains, and uncertainty budgets, each tracing back to StRS
block IDs.

## How to use

1. Either write `.codeanvil/GT/build_package.md` and run the S0 skill, or copy `StRS.md`
   and `SyRS.md` into your project's `.codeanvil/GT/` directory by hand.
2. Replace placeholders (`_project_name_`, `_YYYY-MM-DD_`, etc.) with real content.
3. Write stakeholder requirements, hardware constraints, and normative obligations
   (StRS) and the per-measurand system specifications (SyRS) following the block
   format documented in each template.
4. Validate the pair (deterministic, no AI):

   ```bash
   python templates/skills/G0_valid_req_and_GT/scripts/g0_validate.py .codeanvil/GT/StRS.md .codeanvil/GT/SyRS.md
   ```

5. After G0 passes (script and Gate H), the S1 skill writes the design document to
   `.codeanvil/design/`.

The templates assume that hardware constraints have already been incorporated into the
StRS — every requirement is feasible within the hardware envelope. The documents do
not contain reconciliation machinery; they are final, reviewed IEEE 29148 artifacts.

## Naming convention

```
<NAME>.md
```

- `<NAME>` — the document type (`StRS`, `SyRS`).

The former `G<n>_<NAME>.md` prefix was retired when the GT pair moved under
`.codeanvil/GT/`; the gate that validates a document is recorded in the flow, not in
its filename.

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

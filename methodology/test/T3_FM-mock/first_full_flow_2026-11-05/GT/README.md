# Ground Truth (GT)

Write your project's Build Package here:

- `build_package.md` — your requirements, hardware constraints and normative obligations.
  The S0 skill reads it and writes the two files below.

S0 produces (a hand-written pair is also accepted as normalised input):

- `G0_StRS.md` — Stakeholder Requirements Specification (IEEE 29148 §9.4)
- `G0_SyRS.md` — System Requirements Specification (IEEE 29148 §9.5)

The expected structure is defined by the locked reference templates in
`.agents/skills/G0_valid_req_and_GT/templates/` — do not edit those.

G0 is a **pair gate**: both documents must pass, and the G0-X cross-document rules
must hold, before S1 runs. The S1 design document is produced later by S1 in
`.codeanvil/report/<cycle>/S1_artifacts/` — it is not a GT file.

Validate your GT pair (deterministic, no AI):

```bash
python .agents/skills/G0_valid_req_and_GT/scripts/g0_validate.py GT/G0_StRS.md GT/G0_SyRS.md
```

Exit code `0` means the structure passes; `1` means structural errors (or an incomplete pair)
block the gate.

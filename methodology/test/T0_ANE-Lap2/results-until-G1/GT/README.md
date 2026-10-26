# Ground Truth (GT)

Write your project's GT files here:

- `G0_StRS.md` — Stakeholder Requirements Specification (IEEE 29148 §9.4)
- `G0_SyRS.md` — System Requirements Specification (IEEE 29148 §9.5)

These are **your** files: edit them freely. The expected structure is defined by the
locked reference templates in `.agents/skills/G0_valid_req_and_GT/templates/` — do not edit those.

G0 is a **pair gate**: both documents must pass, and the G0-X cross-document rules
must hold, before any downstream gate runs. The SRS (Software Requirements
Specification, §9.6) is **produced later at G1** — do not create `G1_SRS.md` yet.

Validate your GT pair (deterministic, no AI):

```bash
python .agents/skills/G0_valid_req_and_GT/scripts/g0_validate.py GT/G0_StRS.md GT/G0_SyRS.md
```

Exit code `0` means G0 passes; `1` means structural errors (or an incomplete pair)
block the gate.

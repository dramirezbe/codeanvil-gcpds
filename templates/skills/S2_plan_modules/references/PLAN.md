# Slice {{slice_id}} Plan

| Field | Value |
|-------|-------|
| Slice ID | {{slice_id}} (e.g., slice-01-hal, slice-02-dsp) |
| Modules | {{module_1}}, {{module_2}}, ... |
| VL floor | {{VL-0 / VL-1 / VL-2}} |
| HAL mode | {{mock-only / mock+real}} |
| Build order | {{topological sort of module_id}} |
| Test entry | {{verification/run.sh vl0 \| vl1 \| vl2}} |
| Expected outputs | {{contracts produced by this slice}} |
| Infrastructure ready | {{Mock HAL / golden vectors / stubs / (list)}} |
| Telemetry scope | {{codeanvil telemetry + verification/logger}} |

## Module Details

For each module in this slice:

| Module | Responsibility | Tests | Deliverables |
|--------|-----------------|-------|--------------|
| {{module_id}} | {{one-sentence from SDD}} | {{test file(s)}} | {{code path / library / artifact}} |

## Contracts

Which contracts this slice **produces** (available to later slices):

- {{contract_name}}: {{brief description}}
- ...

Which contracts this slice **consumes** (must be available, mocked or real):

- {{contract_name}}: {{from which prior slice, or mocked}}
- ...

## Blockers and Assumptions

- {{blocking assumption or external dependency}}
- {{infrastructure readiness}}
- ...

---

**Instructions:**

1. Fill this plan during S2, once per slice.
2. Archive prior plans as PLAN-slice-NN.md before writing the next slice plan.
3. VL floor: typically VL-0 for logic, VL-1 when real data or deterministic vectors are needed, VL-2 when real hardware is required.
4. Build order: topological sort of module dependencies; use slice_backlog.py output.
5. Test entry: S3 runs this command to prove VL-0 floor before moving to later levels.

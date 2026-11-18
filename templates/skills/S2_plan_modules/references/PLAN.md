# Module PLAN — {{SUB-xxx/module_id}}

| Field | Value |
|-------|-------|
| Module | {{qualified module identity}} |
| Slice | {{k}} |
| GT version | {{SyRS Version at S2 entry}} |
| Traced requirements | {{SYS IDs and verbatim text}} |
| HAL mode | {{mock-only / mock+real}} |
| Required VL | {{VL-0 / VL-1 / VL-2}} |
| Allowed write paths | {{module source directory, module tests, own stub}} |

## Scope and acceptance criteria

{{Responsibility, exclusions, measurable criteria for each traced SYS requirement and VL.}}

## Contracts

{{Copy relevant provided/consumed SDD §3 contracts verbatim, including headings, versions,
types, units, error semantics, producer identities and dependency slice.}}

## Context set

{{Exact paths and relevant API sections: base API, verification kit for required VL,
dependency stubs, vectors. Every required type/value must resolve here or in this plan.
Do not load the full SDD, full GT or other module source into the implementor.}}

## Ordered tasks

{{Unit, bottom-up, sandwich and required VL-1 tests in this module slice; prepare VL-2
scripts against the fake device API when required. Replace own stub only after checks pass.
Each task names input, action, expected outcome and file scope.}}

## Test strategy

{{Commands, expected output, synthetic vectors/generation parameters, declared HAL,
HW target/prerequisites for VL-2, telemetry envelope. No real HW during S3.}}

## Delta Traceability

{{Applicable D-xxx rows and authority; empty if none.}}

## Risks

{{Unresolved risks, no invented prerequisites or requirement values.}}

## Approval boundary

This entire PLAN.md is immutable after G2 approval, including comments and formatting.
S3 records implementation notes in its report, never here. Any needed plan change goes to
S2 rework and a new G2 review; preserve the prior plan in the S2 backup.

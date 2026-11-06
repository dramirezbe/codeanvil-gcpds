# Verified Prototype — 01_fm_occupancy_mock

## 1. Cycle

| Field | Value |
|-------|-------|
| Cycle | 01_fm_occupancy_mock |
| Based on | S2 iteration 2, G2 iteration 2 |
| Date | 2026-11-05 22:59:12.955 |
| Decided by | D. Ramírez |

## 2. HAL mode

`mock-only`. Every claim is capped at VL-1 and no claim rests on real hardware.

## 3. Toolchain

| Service | Package | Language | Package manager | Test runner |
|---------|---------|----------|-----------------|-------------|
| SVC-001 | fm_edge | Python 3.12 | uv | pytest |
| SVC-002 | dashboard | TypeScript | pnpm | vitest |

## 4. Module evidence

| Module | `required_vl` | Declared level | Environment | Command | Result | Telemetry |
|--------|---------------|----------------|-------------|---------|--------|-----------|
| SVC-001/capture | VL-0 | VL-0 | Mock HAL | `verification/run.sh vl0` | pass | in envelope |
| SVC-001/spectrum | VL-0 | VL-0 | Mock HAL | `verification/run.sh vl0` | pass | in envelope |
| SVC-001/channels | VL-1 | VL-1 | Mock HAL | `verification/run.sh vl1` | pass | in envelope |
| SVC-001/server | VL-0 | VL-0 | Mock HAL | `verification/run.sh vl0` | pass | in envelope |
| SVC-002/client | VL-0 | VL-0 | Mock HAL | `verification/run.sh vl0` | pass | in envelope |
| SVC-002/waterfall | VL-0 | VL-0 | Mock HAL | `verification/run.sh vl0` | pass | in envelope |
| SVC-002/views | VL-1 | VL-1 | Mock HAL | `verification/run.sh vl1` | pass | in envelope |

## 5. Path evidence

| Path | `required_vl` | Declared level | Environment | Command | Result | Telemetry |
|------|---------------|----------------|-------------|---------|--------|-----------|
| PATH-001 | VL-0 | VL-0 | Mock HAL | `verification/run.sh vl0` | pass | in envelope |
| PATH-002 | VL-1 | VL-1 | Mock HAL | `verification/run.sh vl1` | pass | in envelope |
| PATH-003 | VL-0 | VL-0 | Mock HAL | `verification/run.sh vl0` | pass | in envelope |
| PATH-004 | VL-1 | VL-1 | Mock HAL | `verification/run.sh vl1` | pass | in envelope |

## 6. Telemetry report

Envelope from design §1.7:

| Signal | Nominal threshold | Action if exceeded |
|--------|-------------------|--------------------|
| Temperature | ≤ 80 °C | Flag evidence as potentially invalid |
| CPU | ≤ 90 % sustained (5 s window) | Flag evidence as potentially invalid |
| Dropped buffers | 0 | Flag evidence as potentially invalid |
| Scheduling latency | ≤ 50 ms | Flag evidence as potentially invalid |

Readings from the vsil-verifier run:

| Run | Samples | CPU mean | CPU max | Mem mean | Mem max | Dropped |
|-----|---------|----------|---------|----------|---------|---------|
| VL-0 | 4 | 11.9 % | 31.8 % | 29.2 % | 32.8 % | 0 |
| VL-1 | 10 | 11.6 % | 32.1 % | 28.2 % | 29.3 % | 0 |

Temperature and scheduling latency are not exposed by this WSL2 host. All measurable signals are
inside the declared envelope. No readings flagged.

## 7. Honesty declaration

- VERIFIED (VL-0, VL-1): SVC-001/capture, SVC-001/spectrum, SVC-001/channels, SVC-001/server, SVC-002/client, SVC-002/waterfall, SVC-002/views, PATH-001, PATH-002, PATH-003, PATH-004.
- VALIDATED (VL-2, `mock+real` only, `PROTO-*` on the Real HW HAL): none.
- Not claimed: No VL-2 evidence exists. The RTL-SDR Real HW HAL (HW-001) was not used this cycle. A future `mock+real` cycle would add VL-2 claims with `PROTO-*` procedures on real hardware.
- No ML evidence: no model is measured this round.

## 8. Delivered tree and verification kit

| Part | Location | Shipped |
|------|----------|---------|
| Services | `src/fm_edge/`, `src/dashboard/` | Yes |
| Verification kit (Mock HAL, golden vectors, telemetry companion, stubs, fakes, drivers, tests) | `verification/` | Never |

## 9. Verifier

`vsil-verifier` subagent, fresh context. Commands executed in order:

1. `verification/run.sh vl0` → exit code 0 (17 passed, 0 failed, 0 skipped)
2. `verification/run.sh vl1` → exit code 0 (10 passed, 0 failed, 0 skipped)

## 10. RFDs issued

None.

## 11. Future work

- A `mock+real` cycle with the RTL-SDR V4 on a Raspberry Pi 4 would add VL-2 claims and validate
  the detection threshold against real FM band noise (RSK-001).
- The HAL circular buffer drain (§1.3.2 Buffering strategy) must be implemented in the Real HW HAL
  for the `mock+real` cycle.
- Browser rendering profiling on the target device (RSK-002) to confirm the 200 ms render budget.

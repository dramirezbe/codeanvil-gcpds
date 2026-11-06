# Verified Prototype — <cycle-name>

<!-- Locked template. G2 fills it on PASS and writes it to
.codeanvil/report/<cycle-name>/G2_artifacts/verified_prototype.md. Replace every <placeholder>;
delete no section. -->

## 1. Cycle

| Field | Value |
|-------|-------|
| Cycle | <cycle-name> |
| Based on | S2 iteration <N>, G2 iteration <M> |
| Date | <codeanvil now> |
| Decided by | <name> |

## 2. HAL mode

`<mock-only | mock+real>`, from the S1 design Meta. In `mock-only`, every claim is capped at VL-1
and no claim rests on real hardware.

## 3. Toolchain

One row per service, copied from the design Meta.

| Service | Package | Language | Package manager | Test runner |
|---------|---------|----------|-----------------|-------------|
| SVC-xxx | <package> | <language> | <uv / pnpm> | <pytest / vitest> |

## 4. Module evidence

| Module | `required_vl` | Declared level | Environment | Command | Result | Telemetry |
|--------|---------------|----------------|-------------|---------|--------|-----------|
| MOD-xxx | <VL-n> | <VL-n> | <Mock HAL / Real HW HAL> | <verification/run.sh vl0 / vl1 / PROTO-*> | <pass> | <in envelope> |

## 5. Path evidence

| Path | `required_vl` | Declared level | Environment | Command | Result | Telemetry |
|------|---------------|----------------|-------------|---------|--------|-----------|
| PATH-xxx | <VL-n> | <VL-n> | <Mock HAL / Real HW HAL> | <command> | <pass> | <in envelope> |

## 6. Telemetry report

Envelope from design §1.7, readings from the telemetry companion, and every result flagged outside
the envelope with the human's decision on it.

## 7. Honesty declaration

- VERIFIED (VL-0, VL-1): <modules and paths>.
- VALIDATED (VL-2, `mock+real` only, `PROTO-*` on the Real HW HAL): <modules and paths, or "none">.
- Not claimed: <what was not verified this cycle and why, including a Real HW HAL declared at VL-0>.
- No ML evidence: no model is measured this round.

## 8. Delivered tree and verification kit

| Part | Location | Shipped |
|------|----------|---------|
| Services | `src/<service>/` | Yes |
| Verification kit (Mock HAL, golden vectors, telemetry companion, stubs, fakes, drivers, tests) | `verification/` | Never |

## 9. Verifier

`<vsil-verifier subagent | fresh session>`, and the exact commands run, in order, with exit codes.

## 10. RFDs issued

<RFD iterations raised in this cycle and their outcome, or "none">.

## 11. Future work (optional)

<Loose ends the human wants to record for the next cycle, or delete this line>.

## 12. Run the verified prototype

| Field | Value |
|-------|-------|
| System entry point | `<project-root command from design §0.5, exercised by the VL-0 smoke test>` |
| HAL mode | `<Mock HAL preview or Real HW HAL; state the evidence ceiling>` |
| Local URL / endpoint | `<address and port to open>` |
| Expected result | `<what the user should see updating>` |
| Stop | `<how to stop all processes>` |
| Smoke evidence | `<exact test ID, command, exit code and result>` |

Give the exact prerequisite install/build commands and then the system entry point. If the
preview uses the Mock HAL, say so plainly; do not imply real-hardware validation.

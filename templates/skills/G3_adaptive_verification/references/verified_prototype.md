# Verified Prototype — <cycle-name>

<!-- Locked template. G3 fills it only on system-scope PASS and writes it to
.codeanvil/report/<cycle-name>/G3_artifacts/verified_prototype.md. Replace every <placeholder>;
delete no section. -->

## 1. Cycle

| Field | Value |
|-------|-------|
| Cycle | <cycle-name> |
| Based on | S3 iteration <N>, G3 iteration <M> |
| Date | <codeanvil now> |
| Decided by | <name> |
| GT version at S2 entry | <version> |
| GT version at G3 exit | <version> |

## 2. HAL mode

`<mock-only | mock+real>`, from the S1 design Meta. In `mock-only`, every claim is capped at VL-1
and uses Mock HAL inputs. PIL may run these inputs on the actual compute unit; it is not real-RF
or VL-2 validation.

## 3. Toolchain

One row per subsystem, copied from the design Meta.

| Subsystem | Package | Language | Package manager | Test runner |
|---------|---------|----------|-----------------|-------------|
| SUB-xxx | <package> | <language> | <uv / pnpm> | <pytest / vitest> |

**Execution equipment and preparation:**

| Subsystem / PATH-* | Local / PIL / real HW | Equipment MAC or local host | Endpoint / user / port / workspace | Observed OS / architecture / device | Tool versions |
|------------------|-----------------------|-----------------------------|----------------------------------|-------------------------------------|---------------|
| <IDs> | <actual run type> | <declared identity> | <actual location> | <observations> | <versions used> |

- Deployment: <published at <remote> @ <commit> | local-only commit @ <commit> (not pushed; reproducible on this machine only)>

Record the clean code/kit branch+commit (state which case above applied), completed pre-HW checkpoint, actual tool/app
refs updated, dependencies and clock preparation. Name run IDs, files, commands and results;
no deployment manifest, per-file digest, version equality or formal capture request is required.

## 4. Module evidence

| Module | Slice | Plan | Evidence from (G3 iteration) | `required_vl` | Declared level | Environment | Command | Result | Telemetry |
|--------|-------|------|------------------------------|---------------|----------------|-------------|---------|--------|-----------|
| MOD-xxx | <k> | <plan path> | <iteration> | <VL-n> | <VL-n> | <Mock HAL / Real HW HAL> | <verification/run.sh vl0 / vl1 / PROTO-*> | <pass> | <in envelope> |

## 5. Path evidence

| Path | `required_vl` | Declared level | Environment | Command | Result | Telemetry |
|------|---------------|----------------|-------------|---------|--------|-----------|
| PATH-xxx | <VL-n> | <VL-n> | <Mock HAL / Real HW HAL> | <command> | <pass> | <in envelope> |

## 6. Telemetry report

Envelope from design §1.7, readings from the telemetry companion, and every result flagged outside
the envelope with the human's decision on it. Name the execution target per evidence file. Report
unavailable readings, investigated causes, affected claims and the decision to repeat or continue
with supported evidence. Name any skipped torn trailing line; collector exit 0 alone does not
establish complete coverage. Missing telemetry does not invalidate unrelated tests by itself.

## 7. Honesty declaration

- VERIFIED (VL-0, VL-1): <modules and paths; execution target and whether PIL>.
- VALIDATED (VL-2, `mock+real`, actual Real HW HAL tests): <supported modules/paths or "none">.
- Not claimed: <what was not verified this cycle and why, including a Real HW HAL declared at VL-0>.
- No ML evidence: no model is measured this round.

For each real HW claim, cite actual G3 measurement v2/script outputs, the GT criterion and
method/resolution justification. Add calibration, corrections and uncertainty only when the
requirement or conclusion needs them; absent required inputs make that claim inconclusive.
A valid JSON record alone is not a metrological verdict. Record human judgment, gaps and causal
feedback; never invent readings or expand tolerances to obtain PASS.

## 8. Delivered tree and verification kit

| Part | Location | Shipped |
|------|----------|---------|
| Subsystems | `src/<subsystem>/` | Yes |
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

## Plans

`.codeanvil/plans/BACKLOG.md`, INFRA-PLAN.md, INTEGRATION-PLAN.md and each module PLAN.md.
Plans and verification kit are development evidence, not shipped product artifacts.

## Delta traceability log

Link `.codeanvil/plans/DELTAS.md`; counts per ADDED/MODIFIED/REMOVED/RENAMED/design-sync,
with authority, applied iteration and remaining work. No pending accepted GT or design-sync deltas at system PASS; all required G0/G1 reviews completed.

## Verifier context

Name vsil-verifier subagent or fresh session, scope, origin evidence iterations and carried-forward
unchanged module digests. Disclose actual HAL, processor and execution equipment.

## Future work register

FW-001 CI/CD evidence; FW-002 PIL sub-gate; FW-003 VL-2 fault injection;
FW-004 SIL/HIL correlation; FW-005 MLOps; FW-006 automated planning.

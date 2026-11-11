# Verified Prototype — 01_ui_demo

> SYNTHETIC UI FIXTURE — simulated workflow and human verdicts, not a real V-SIL approval.

## 1. Cycle

| Field | Value |
|-------|-------|
| Cycle | 01_ui_demo |
| Based on | S2 iteration 1, G2 iteration 1 |
| Date | 2026-11-11 10:08:37.492 |
| Decided by | Synthetic UI actor — SIMULATED |

## 2. HAL mode

mock-only. Synthetic workflow, no physical-device evidence. VL-1 ceiling.

## 3. Toolchain

| Service | Package | Language | Package manager | Test runner |
|---------|---------|----------|-----------------|-------------|
| SVC-001 | demo_counter | Python 3.12+ | uv | pytest |

## 4. Module evidence

| Module | required_vl | Declared level | Environment | Command | Result | Telemetry |
|--------|-------------|----------------|-------------|---------|--------|-----------|
| SVC-001/identity | VL-0 | VL-0 | Mock HAL | verification/run.sh vl0 | pass (automated check) | Actual JSONL; independent judgment simulated |

## 5. Path evidence

| Path | required_vl | Declared level | Environment | Command | Result | Telemetry |
|------|-------------|----------------|-------------|---------|--------|-----------|
| PATH-001 | VL-0 | VL-0 | Local HTTP + Mock HAL | verification/run.sh vl0 | pass (automated smoke) | Actual JSONL; no hardware claim |

## 6. Telemetry report

Read actual readings in verification/telemetry/ and the summary in
S2_artifacts/test_run.md. The design's envelope is illustrative; an independent
human acceptance/envelope review was not performed for this UI fixture.

## 7. Honesty declaration

- VERIFIED (VL-0, VL-1): synthetic UI state only; not a genuine G2 approval.
- Actual automated checks: 3 VL-0 and 1 synthetic-sequence VL-1 tests passed.
- VALIDATED (VL-2): none. No physical measurements or ML evidence.
- Not claimed: a fresh independent verifier, human review or RF implementation.

## 8. Delivered tree and verification kit

| Part | Location | Shipped |
|------|----------|---------|
| Services | src/demo_counter/ | Yes |
| Verification kit | verification/ | Never |

## 9. Verifier

SIMULATED fresh-session role for UI display, not an actual vsil-verifier run.
The fixture builder executed verification/run.sh vl0 and verification/run.sh vl1
again in subprocesses; both exited 0. Raw logs: verification/test-output/g2-*.

## 10. RFDs issued

None.

## 11. Future work (optional)

Replace synthetic reports with a real agent-led cycle if assurance is needed.

## 12. Run the verified prototype

| Field | Value |
|-------|-------|
| System entry point | uv run --no-dev demo_counter |
| HAL mode | RuntimeMockHAL; synthetic values; no hardware-validation claim |
| Local URL / endpoint | http://127.0.0.1:8854/ |
| Expected result | Synthetic UI fixture page with repeating 0,1,2 |
| Stop | Ctrl-C |
| Smoke evidence | test_entrypoint; verification/run.sh vl0; exit 0; HTTP and clean shutdown |

```bash
uv sync --frozen --no-dev
uv run --no-dev demo_counter
```

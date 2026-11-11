# S2 test run

> SYNTHETIC UI FIXTURE — simulated workflow and human verdicts, not a real V-SIL approval.

## Commands for G2

```bash
verification/run.sh vl0
verification/run.sh vl1
```

## Last VL-0 floor run (actual automated execution)

| Service | Command | Exit | Passed | Failed | Skipped |
|---------|---------|------|--------|--------|---------|
| SVC-001 | verification/run.sh vl0 | 0 | 3 | 0 | 0 |

## Runnable entry point

Install: `uv sync --frozen --no-dev`. Run: `uv run --no-dev demo_counter`.
URL: http://127.0.0.1:8854/. Expected: the page displays repeating 0, 1, 2.
Stop: Ctrl-C. Smoke: test_entrypoint starts the installed package as a process,
receives HTML and [0,1,2] over HTTP and verifies exit 0 after SIGINT.
Smoke command: `verification/run.sh vl0` (3 passed, exit 0).

## Environment and telemetry

Linux 6.18.33.2-microsoft-standard-WSL2 x86_64; uv 0.12.1 (x86_64-unknown-linux-gnu); mock-only.
Toolchain: Python 3.12+, uv, pytest. Raw test logs: verification/test-output/.
Actual JSONL collector readings: 7 samples across 4 files
under verification/telemetry/. Missing sensors remain unavailable. No independent
G2 envelope judgment is asserted. No physical device or calibrated quantity.

## Possible infeasibility

None in this synthetic counter fixture.

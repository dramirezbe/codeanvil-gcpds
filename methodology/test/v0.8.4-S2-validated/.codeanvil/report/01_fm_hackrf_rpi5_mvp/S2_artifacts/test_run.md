# S2 Test Run — VL-0 Floor Evidence

| Field | Value |
|-------|-------|
| Cycle | 01_fm_hackrf_rpi5_mvp |
| Run ID | 01_fm_hackrf_rpi5_mvp_1_2026-11-13_21-42-38 |
| Level | VL-0 |
| Command | `bash verification/run.sh vl0` |
| Exit code | 0 |
| Timestamp | 2026-11-13 16:42:47.146 |

## Summary

| Suite | Collected | Passed | Failed | Skipped |
|-------|-----------|--------|--------|---------|
| fm_measure VL-0 | 9 | 9 | 0 | 0 |
| fm_supervisor VL-0 | 9 | 9 | 0 | 0 |
| fm_store_alert VL-0 | 3 | 3 | 0 | 0 |
| fm_report VL-0 | 1 | 1 | 0 | 0 |
| fm_time VL-0 | 6 | 6 | 0 | 0 |
| fm_web (vitest) VL-0 | 5 | 5 | 0 | 0 |
| **Total** | **39 pytest + 5 vitest** | **44** | **0** | **0** |

All 39 pytest VL-0 tests pass; all 5 vitest VL-0 tests pass. `verification/run.sh vl0` exits 0.

## Full VL-1 test count (run with `uv run pytest -q`)

| Suite | Tests |
|-------|-------|
| fm_measure | 43 |
| fm_store_alert | 20 |
| fm_report | 10 |
| fm_time | 15 |
| fm_supervisor | 29 |
| **Total Python** | **117** |

## Possible infeasibilities

None. All VL-2 modules (`acq`, `calibrate`, `verify`, `watchdog`) have correct stubs and are excluded from VL-0/VL-1; the Mock HAL synthesises all needed IQ in code.

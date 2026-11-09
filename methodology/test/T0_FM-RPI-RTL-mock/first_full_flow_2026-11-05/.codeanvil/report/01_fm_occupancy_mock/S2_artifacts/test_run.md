# S2 test run

## Commands G2 runs

```bash
verification/run.sh vl0
verification/run.sh vl1
```

## Last VL-0 run

| Field | Value |
|-------|-------|
| Command | `verification/run.sh vl0` |
| Exit code | 0 |
| Python (fm_edge) | passed 11, failed 0, skipped 0 |
| TypeScript (dashboard) | passed 6, failed 0, skipped 0 |
| Total | passed 17, failed 0, skipped 0 |

Breakdown by module / path:

| Area | Tests | Marker |
|------|-------|--------|
| GV-1 sample conversion | 1 | vl0 |
| GV-2 spectrum peak | 1 | vl0 |
| GV-3 channel identification | 1 | vl0 |
| GV-4 detection flags | 1 | vl0 |
| GV-5 producer message format | 1 | vl0 |
| DC spike / fc validation | 2 | vl0 |
| PATH-001 end-to-end over WebSocket | 1 | vl0 |
| PATH-003 waterfall depth | 1 | vl0 |
| PATH-004 latency budget and processing time | 2 | vl0 |
| GV-5 consumer validation (dashboard) | 4 | vl0 |
| Waterfall ring buffer (dashboard) | 2 | vl0 |

## Last VL-1 run (written, executes; the VL-1 claim belongs to G2)

| Field | Value |
|-------|-------|
| Command | `verification/run.sh vl1` |
| Exit code | 0 |
| Python (fm_edge) | passed 6, failed 0, skipped 0 |
| TypeScript (dashboard) | passed 4, failed 0, skipped 0 |

## Environment

| Item | Value |
|------|-------|
| OS | Linux 6.18.33.2-microsoft-standard-WSL2 x86_64 |
| CPU | 12th Gen Intel(R) Core(TM) i5-12450H, 12 logical cores |
| Python | 3.14.4 system, 3.12.13 in the uv environment |
| uv | 0.12.1 |
| Node | v24.18.0 |
| pnpm | 11.24.0 |
| TypeScript | 5.7 (project dev dependency) |
| vitest | 2.1.9 |
| pytest | 9.2.0 |
| HAL mode | mock-only |

## Telemetry companion summary (last VL-0 run)

```
samples: 4
cpu_pct: mean=10.7 max=27.4
mem_pct: mean=27.4 max=30.9
dropped: 0
file: .codeanvil/report/01_fm_occupancy_mock/S2_artifacts/telemetry_vl0.jsonl
```

All readings are inside the declared operating envelope (temperature not exposed in this WSL2
host; CPU ≤ 90 %, memory below the budget, 0 dropped buffers).

## Possible infeasibility

None.

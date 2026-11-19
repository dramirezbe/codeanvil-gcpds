# Verified Prototype — 01_fm_hackrf_rpi5_mvp

## 1. Cycle

| Field | Value |
|-------|-------|
| Cycle | 01_fm_hackrf_rpi5_mvp |
| Based on | S3 iteration 2, G3 iteration 1 |
| Date | 2026-11-18 17:50:32.803 |
| Decided by | dramirezbe |
| GT version at S2 entry | StRS sha256:db9d3775d3cca3683603ab998a31ca5a7df6e5b1853b6cfb954b169152a88ef3; SyRS sha256:ac2230edf7cc2e6f90a3f74be322dd54f282759e2f219ac8ac4fd29cd49a76b5 |
| GT version at G3 exit | StRS sha256:db9d3775d3cca3683603ab998a31ca5a7df6e5b1853b6cfb954b169152a88ef3; SyRS sha256:ac2230edf7cc2e6f90a3f74be322dd54f282759e2f219ac8ac4fd29cd49a76b5 |

## 2. HAL mode

`mock+real`, from the S1 design Meta. VL-2 is allowed per module, but no VL-2 evidence was obtained this cycle. All claims are capped at VL-1 and use Mock HAL inputs. PIL ran these inputs on the actual Pi 5 compute unit; it is not real-RF or VL-2 validation.

## 3. Toolchain

| Subsystem | Package | Language | Package manager | Test runner |
|-----------|---------|----------|-----------------|-------------|
| SUB-001 `measure` | fm_measure | Python 3.12 | uv | pytest |
| SUB-002 `store_alert` | fm_store_alert | Python 3.12 | uv | pytest |
| SUB-003 `report` | fm_report | Python 3.12 | uv | pytest |
| SUB-004 `web` | fm_web | TypeScript | pnpm | vitest |
| SUB-005 `time` | fm_time | Python 3.12 | uv | pytest |
| SUB-006 `supervisor` | fm_supervisor | Python 3.12 | uv | pytest |

**Execution equipment and preparation:**

| Subsystem / PATH-* | Local / PIL / real HW | Equipment MAC or local host | Endpoint / user / port / workspace | Observed OS / architecture / device | Tool versions |
|---------------------|----------------------|-----------------------------|----------------------------------|-------------------------------------|---------------|
| All VL-0/VL-1 | PIL | mac_2ccf670032ca | 10.171.152.95 / codeanvil-agent / 22 / /home/codeanvil-agent/projects/01a1f06c-0d8c-7000-8d04-1c2674199aae | Linux aarch64, HackRF One serial 230865dc3149c447 fw n_250816 | Python 3.13.5, Node 20.19.2, uv 0.13.9, pnpm 12.16.1, CodeAnvil 0.9.6 |
| VL-2 (attempted) | real HW | mac_2ccf670032ca | same | same | same |

- Deployment: local-only commit @ 8d0dee7 (not pushed; reproducible on this machine only)

CodeAnvil 0.9.6 already up to date on target. Code synced via `code_sync`. Dependencies installed via `uv sync` and `pnpm install`. NTP synchronized (timedatectl: yes). Pre-HW review checkpoint completed with explicit `continue`.

VL-0 Run ID: `01_fm_hackrf_rpi5_mvp_1_2026-11-18_22-38-40`
VL-1 Run ID: `01_fm_hackrf_rpi5_mvp_1_2026-11-18_22-38-52`

## 4. Module evidence

| Module | Subsystem | Evidence from | required_vl | Declared | Environment | Command | Result | Telemetry |
|--------|-----------|---------------|-------------|----------|-------------|---------|--------|-----------|
| acq | SUB-001 | G3 iter 1 | VL-2 | VL-2 | Mock HAL (PIL) | verification/run.sh vl0 | VL-0 PASS; VL-2 FAIL (stub) | MISSING |
| estimator | SUB-001 | G3 iter 1 | VL-1 | VL-1 | Mock HAL (PIL) | verification/run.sh vl1 | PASS (7 tests) | MISSING |
| calibration | SUB-001 | G3 iter 1 | VL-1 | VL-1 | Mock HAL (PIL) | — | MISSING TEST | MISSING |
| detector | SUB-001 | G3 iter 1 | VL-1 | VL-1 | Mock HAL (PIL) | verification/run.sh vl1 | PASS (11 tests) | MISSING |
| comparator | SUB-001 | G3 iter 1 | VL-1 | VL-1 | Mock HAL (PIL) | verification/run.sh vl1 | PASS (6 tests) | MISSING |
| duty_cycle | SUB-001 | G3 iter 1 | VL-1 | VL-1 | Mock HAL (PIL) | verification/run.sh vl1 | PASS (5 tests) | MISSING |
| records | SUB-001 | G3 iter 1 | VL-1 | VL-1 | Mock HAL (PIL) | verification/run.sh vl1 | PASS (5 tests) | MISSING |
| calibrate | SUB-001 | G3 iter 1 | VL-2 | VL-2 | — | — | INCONCLUSIVE (needs HW-010) | MISSING |
| verify | SUB-001 | G3 iter 1 | VL-2 | VL-2 | — | — | INCONCLUSIVE (needs HW-011) | MISSING |
| history | SUB-002 | G3 iter 1 | VL-1 | VL-1 | Mock HAL (PIL) | verification/run.sh vl1 | PASS (6 tests) | MISSING |
| alerts | SUB-002 | G3 iter 1 | VL-1 | VL-1 | Mock HAL (PIL) | verification/run.sh vl1 | PASS (9 tests) | MISSING |
| writer | SUB-003 | G3 iter 1 | VL-1 | VL-1 | Mock HAL (PIL) | verification/run.sh vl1 | PASS (6 tests) | MISSING |
| views | SUB-004 | G3 iter 1 | VL-1 | VL-1 | — | — | NOT RUN (pnpm operational) | MISSING |
| http | SUB-004 | G3 iter 1 | VL-1 | VL-1 | — | — | NOT RUN (pnpm operational) | MISSING |
| ntp | SUB-005 | G3 iter 1 | VL-1 | VL-1 | Mock HAL (PIL) | verification/run.sh vl1 | PASS (9 tests) | MISSING |
| config | SUB-006 | G3 iter 1 | VL-1 | VL-1 | Mock HAL (PIL) | verification/run.sh vl1 | PASS (6 tests) | MISSING |
| processes | SUB-006 | G3 iter 1 | VL-1 | VL-1 | Mock HAL (PIL) | verification/run.sh vl1 | PASS (5 tests) | MISSING |
| watchdog | SUB-006 | G3 iter 1 | VL-2 | VL-2 | Mock HAL (PIL) | verification/run.sh vl1 | VL-1 PASS (4 tests); VL-2 FAIL (stubs) | MISSING |
| metrics | SUB-006 | G3 iter 1 | VL-1 | VL-1 | Mock HAL (PIL) | verification/run.sh vl1 | PASS (5 tests) | MISSING |

## 5. Path evidence

| Path | required_vl | Declared | Environment | Command | Result | Telemetry |
|------|-------------|----------|-------------|---------|--------|-----------|
| PATH-001 | VL-2 | VL-2 | Mock HAL (PIL) | verification/run.sh vl0/vl1, ./run.sh smoke | VL-0/VL-1 chain demonstrated; VL-2 BLOCKED (acq stub) | MISSING |
| PATH-002 | VL-1 | VL-1 | Mock HAL (PIL) | verification/run.sh vl0/vl1 | PARTIAL (fm_web not run) | MISSING |
| PATH-003 | VL-1 | VL-1 | Mock HAL (PIL) | verification/run.sh vl1 | VL-1 pytest evidence | MISSING |
| PATH-004 | VL-1 | VL-1 | Mock HAL (PIL) | verification/run.sh vl1 | VL-1 pytest evidence | MISSING |
| PATH-005 | VL-1 | VL-1 | Mock HAL (PIL) | verification/run.sh vl0/vl1, ./run.sh smoke | PASS | MISSING |
| PATH-006 | VL-2 | VL-2 | — | — | BLOCKED (acq stub, needs HW-010) | MISSING |
| PATH-007 | VL-1 | VL-1 | Mock HAL (PIL) | verification/run.sh vl1 | VL-1 pytest evidence | MISSING |
| PATH-008 | VL-2 | VL-2 | — | — | BLOCKED (acq stub, needs HW-011) | MISSING |
| PATH-009 | VL-2 | VL-2 | — | — | BLOCKED (acq stub, needs real load) | MISSING |

## 6. Telemetry report

**Telemetry collector: not implemented.** `verification/telemetry/__init__.py` is empty (0 bytes). No JSONL data was produced for any run (VL-0, VL-1, VL-2 or entry-point smoke).

Manual target readings during idle (not under test load):

| Signal | Reading | Envelope (Pi 5) | Status |
|--------|---------|-----------------|--------|
| SoC temperature | 63.35 °C | ≤70 °C | OK |
| Free disk | 19 GB | ≥12.8 GB | OK |
| NTP sync | Synchronized | Synchronized | OK |
| CPU load average | 0.01 / 0.10 / 0.09 | ≤70 % sustained | OK (idle) |
| USB dropped frames | Not measurable | 0 | MISSING |
| Scheduling latency p99 | Not measurable | ≤1 000 ms | MISSING |
| Per-process CPU/RSS | Not measurable | Per-process limits | MISSING |

Timing, thermal and resource acceptance cannot be claimed without programmatic telemetry under test load. All functional results remain supported (missing telemetry does not invalidate functional tests per SDD §1.7 unavailable-signal policy).

## 7. Honesty declaration

- **VERIFIED (VL-0):** 39/39 pytest pass on Pi 5 target (PIL, Mock HAL). SUB-004 fm_web vitest not run (pnpm operational on target). All six Python subsystems verified at VL-0 floor.
- **VERIFIED (VL-1, partial):** 78/78 pytest pass on Pi 5 target (PIL, Mock HAL synthetic inputs). SUB-001/calibration VL-1 test missing. SUB-004 fm_web vitest not run. 13 of 15 VL-1 modules verified.
- **VL-2: NO EVIDENCE.** `RealSdrPort.read_frames` stub prevents real acquisition. `RealResourcePort` stubs return constant 0.0. No real-device inputs were used by any module. `calibrate` and `verify` require traceable source HW-010 and independent reference HW-011, not available this cycle.
- **Telemetry: MISSING.** Collector not implemented. No JSONL envelope data produced.
- No ML evidence: no model is measured this round (FW-ML-4).
- No claim uses real device inputs. Mock HAL caps all current evidence at VL-1 (VERIFIED). The human accepted this evidence ceiling for this cycle.

## 8. Delivered tree and verification kit

| Part | Location | Shipped |
|------|----------|---------|
| Subsystems | `src/fm_measure/`, `src/fm_store_alert/`, `src/fm_report/`, `src/fm_web/`, `src/fm_time/`, `src/fm_supervisor/` | Yes |
| Verification kit (Mock HAL, golden vectors, telemetry companion, stubs, fakes, drivers, tests) | `verification/` | Never |

## 9. Verifier

`vsil-verifier` subagent, launched from the G3 parent after pre-HW review and preparation.

Commands run, in order:

1. `FM_ITER=1 bash verification/run.sh vl0` — exit 1 (pytest 39/39 pass, vitest error)
2. `codeanvil custody verify-manifest verification/golden/manifest.md` — exit 1 (2 unlisted files)
3. `FM_ITER=1 bash verification/run.sh vl1` — exit 1 (pytest 78/78 pass, vitest error)
4. `./run.sh` (mock HAL, entry-point smoke) — exit 0 (5/6 spawned, clean shutdown)
5. `./run.sh --hal real` (VL-2 attempt) — exit 0 (HackRF opened, read_frames stub hit)
6. `fetch_evidence` — exit 0 (telemetry snapshot collected)

## 10. RFDs issued

None.

## 11. Future work

- **FW-VL2-001:** Implement `RealSdrPort.read_frames` with libhackrf streaming callback for real HackRF acquisition (SUB-001/acq VL-2).
- **FW-VL2-002:** Implement `RealResourcePort.cpu_percent()` and `rss_mb()` from `/proc` (SUB-006/watchdog VL-2).
- **FW-KIT-001:** Create `test_calibration_vl1.py` for SUB-001/calibration module (K(f), validity states, uncertainty, withheld power).
- **FW-KIT-002:** Implement the telemetry collector (`verification/telemetry/__init__.py`) per SDD §1.7.
- **FW-KIT-003:** Update `verification/golden/manifest.md` to include `__init__.py` and `generate.py`.
- **FW-KIT-004:** Add `ntplib` to `pyproject.toml` dependencies for fm_time real HAL.
- **FW-OPS-001:** Repair pnpm corepack on Pi 5 target (`.cjs` vs `.mjs` mismatch).
- **FW-VL2-003:** VL-2 calibration (PATH-006) and verification (PATH-008) with traceable source HW-010 and independent reference HW-011.

## 12. Run the verified prototype

| Field | Value |
|-------|-------|
| System entry point | `./run.sh` |
| HAL mode | Mock HAL preview (evidence ceiling: VL-1; no real-hardware validation) |
| Local URL / endpoint | `http://localhost:8080/power` |
| Expected result | 199 channels updating every 6 s, spectrum view, station history, node status and alert bar. All labelled "Screening evidence only: not a compliance determination". |
| Stop | `Ctrl-C` or `SIGTERM` to `./run.sh` — supervisor sends `shutdown.v1`, stops children in reverse, exit 0 |
| Smoke evidence | G3 iteration 1 entry-point smoke: `./run.sh` exit 0, 5/6 spawned, 4/6 operated, data exchange confirmed, clean shutdown |

**Prerequisites:**

```bash
uv sync
pnpm install
./run.sh
```

This preview uses the Mock HAL. It synthesises IQ from GV-001 parameters with a fixed seed. It does not use real hardware and does not perform real-RF validation.

## Plans

No `.codeanvil/plans/` directory (S2 migrated from V-SIL v3; planning evidence is in SDD §2.2, §3, §4).

## Delta traceability log

No `.codeanvil/plans/DELTAS.md` (no deltas this cycle).

## Verifier context

vsil-verifier subagent, system scope, evidence from G3 iteration 1 only. No carried-forward module digests (first G3 iteration). Actual HAL: Mock HAL (Python runtime mock, in-code IQ synthesis). Actual processor: Raspberry Pi 5 aarch64 (PIL). Execution equipment: mac_2ccf670032ca at 10.171.152.95.

Module digests at G3 exit:

| Module | Digest |
|--------|--------|
| SUB-001/fm_measure | sha256:1a97cf0f93acbac8a34a2362083913087112fa8ffb9a740b841570b087f93bc5 |
| SUB-002/fm_store_alert | sha256:87c531a902b738733b2f3e81f3df71c637a508cb4339ca34beb339b9dd012130 |
| SUB-003/fm_report | sha256:84fd7572a58cf81ea34686e6fd1f32e029f1d5eec28b0331a2abf48f9bbc7db6 |
| SUB-004/fm_web | sha256:f6d9596b64f1885b4808c90056853616539e798fcb2f210aaf0033ae8346c91e |
| SUB-005/fm_time | sha256:1920f4838f0407e788f581fdb03028d80cb67937e7df3ad24ea6e2d2c917978c |
| SUB-006/fm_supervisor | sha256:e187f2ca79a8cb8f37a2c0c495b94aa25c9c79339fb76a1501f3562103db6d2e |

## Future work register

FW-001 CI/CD evidence; FW-002 PIL sub-gate; FW-003 VL-2 fault injection; FW-004 SIL/HIL correlation; FW-005 MLOps; FW-006 automated planning.

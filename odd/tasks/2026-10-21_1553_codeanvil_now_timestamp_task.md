# Feature: `codeanvil now` — Unified System Timestamp

**Plan:** `odd/tasks/codeanvil_now_timestamp.md` (PLANNED)
**Branch:** `feat/codeanvil-now`
**Route:** delegated direct (writer trigger: 4 files — `templates/config.yaml`, `src/codeanvil/config/time.py`, `src/codeanvil/config/logger.py`, `src/codeanvil/CLI/cli.py`)
**TDD:** regex + offset validation in `tests/test_time.py`
**Delivery strategy:** `ask-on-risk`; forecast ≈ 120 authored changed lines (< 400) → single slice.

## Objective

Single timestamp function used everywhere — CLI (`codeanvil now`), logger, and future gate artifacts. Millisecond precision, timezone from `config.yaml`, overridable via `--tz`.

## Scope

- New: `src/codeanvil/config/time.py`, `tests/test_time.py`
- Modified: `templates/config.yaml`, `src/codeanvil/config/logger.py`, `src/codeanvil/CLI/cli.py`
- Out of scope: custody-chain timestamps (those use strict ISO-8601 UTC by design), DB `datetime('now')`, GT files.

## Constraints / decisions

1. **Module placement**: `src/codeanvil/config/time.py` — lives alongside `logger.py` and `paths.py`. No new `utils/` package.
2. **Config key**: `defaults.country: "America/Bogota"` in `config.yaml`. Loaded via existing `CONFIG` in `paths.py`.
3. **Resolution order**: explicit `--tz` arg > `CONFIG["defaults"]["country"]` > `"UTC"` fallback.
4. **Logger import**: lazy import inside `formatTime()` to preserve `logger.py`'s zero-dependency bootstrap property (logger is imported before `paths.py` in some modules).
5. **Stdlib only**: `datetime`, `zoneinfo` (native Python 3.10+). No new dependencies.
6. **Machine vs. human**: this format (`YYYY-MM-DD HH:MM:SS.mmm`) is for human-facing output only. Audit/DB/ledger timestamps stay ISO-8601 UTC unchanged.

## Tasks

- [ ] T1 — Add `defaults.country: "America/Bogota"` to `templates/config.yaml`
- [ ] T2 — Create `src/codeanvil/config/time.py`: `get_system_timezone(tz_name?) -> ZoneInfo` + `format_timestamp(dt?, tz_name?) -> str`
- [ ] T3 — Wire `logger.py`: override `ColoredFormatter.formatTime()` to call `format_timestamp`, remove static `datefmt`
- [ ] T4 — Wire `cli.py`: add `now` subparser with `--tz`, handler `cmd_now()`, match in `choose_option`
- [ ] T5 — Create `tests/test_time.py`: default tz, UTC override, regex `^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3}$`, invalid tz error
- [ ] T6 — Smoke test: `codeanvil now`, `codeanvil now --tz UTC`, logger output format
- [ ] T7 — Commit and push

## Subagent plan

| Phase | Subagent | Tasks | Depends on |
|-------|----------|-------|------------|
| 1 | `gentle-ai-worker` "Create time utility" | T1, T2 | — |
| 2a | `gentle-ai-worker` "Wire logger + CLI" | T3, T4 | Phase 1 |
| 2b | `gentle-ai-worker` "Add tests" | T5 | Phase 1 (parallel with 2a) |
| 3 | Parent | T6, T7 | Phase 2a + 2b |

## Progress

- [x] T1 — `defaults.country: "America/Bogota"` added to `templates/config.yaml`
- [x] T2 — `src/codeanvil/config/time.py` created: `get_system_timezone()` + `format_timestamp()`
- [x] T3 — `logger.py`: `ColoredFormatter.formatTime()` overridden with lazy import, static `datefmt` removed
- [x] T4 — `cli.py`: `now` subparser with `--tz`, `cmd_now()` handler, `choose_option` match
- [x] T5 — `tests/test_time.py`: 6 tests — regex, UTC override, Bogota offset, explicit tz, invalid tz, default config
- [x] T6 — Smoke tested: `codeanvil now` → `2026-10-21 15:50:16.913`, `--tz UTC` → `2026-10-21 20:50:17.079`, logger → ms precision
- [ ] T7 — Commit and push (pending user request)

## Evidence

- Tests: 6/6 passed (`tests/test_time.py`)
- CLI: `codeanvil now` → Bogota time, `codeanvil now --tz UTC` → UTC time
- Logger: `[2026-10-21 15:50:20.912]` — ms precision, Bogota timezone

# Plan — T6: S2 implements the services (one skill)

Feature: `odd/tasks/2026-11-05_1421_vsil_v3_full_flow.md` · Task T6 · Specs S2, S3, S4, S7, S10, S12 · Contracts C0–C11, D1–D10
Targets: `templates/skills/S2_implement_services/` with `SKILL.md` (about 120 lines), `references/project_layout.md` (the D2 trees), `references/logger.py` and `references/logger.ts` (the D10 loggers). No script. Paper §7, §9.2.
Replaces the three 2026-11-01 plans (`S2-1`, `S2-2`, and the S2 half of `S2-3`), which targeted chat-only skills.

## Goal

Turn the G1-approved design into running code plus the verification kit, prove the VL-0 floor, and leave the VL-1 tests ready for G2 to run. S2 is a **stage** (C4): its `PASS` means "delivered with VL-0 evidence"; the human verdict belongs to G2. The agent runs every test itself: the Mock HAL and the kit exist so it can, without hardware or a human in the loop (C9).

## Prerequisite (C2)

Resolve the cycle from `.codeanvil/project.yaml`. Check, in this order, writing **no iteration** when you stop (same wording as G1):

1. Latest `RFD.md` iteration holds `Superseded by cycle: <name>`: return exactly `Cycle closed by RFD. Continue in cycle <name>.`
2. `G1.md` missing or its latest iteration is not `HITL: PASS`, or `codeanvil status` marks G1 or an earlier report `stale`: return exactly `G1 must pass first. Run the G1 skill.`
3. S2's own latest iteration is `FEEDBACK` with `Verdict: design defect` and its `Based on` line names the current latest G1 iteration: return exactly `S1 must rework first. Run the S1 skill.`
4. The latest G2 iteration is `FEEDBACK` with `Verdict: RFD`: return exactly `Cycle suspended by RFD. Run the RFD skill.`, unless the latest `RFD.md` iteration states `Outcome: Withdrawn`.

The Description starts with `Based on: G1 iteration <N>` (C11).

## Inputs and outputs

| | Path |
|---|------|
| Input | `S1_artifacts/S1_design.md` (read-only): Meta `HAL mode` and `Toolchain`, §1.3.4, §1.6, §1.7, §2.2, §3, §4 |
| Input | `GT/G0_SyRS.md` for thresholds |
| Input (rework) | Latest `G2.md` iteration with `Verdict: module defect` |
| Reference | `references/project_layout.md`: the D2 trees (Python, TypeScript, mixed), with the root manifests |
| Reference | `references/logger.py`, `references/logger.ts`: the D10 loggers, copied unchanged |
| Output | `src/<package>/` per service, root manifests (`pyproject.toml` + `uv.lock`, and/or `package.json` + `pnpm-workspace.yaml` + `pnpm-lock.yaml`), and `verification/` (the kit) |
| Output | `.codeanvil/report/<cycle-name>/S2_artifacts/test_run.md`: the commands `verification/run.sh vl0` and `verification/run.sh vl1` (D8), last VL-0 run counts, environment, telemetry summary, and any `Possible infeasibility` |
| Output | `.codeanvil/report/<cycle-name>/S2.md` |

## `references/project_layout.md`

The D2 trees from the feature document, written out once each:

- **Python service** `src/<package>/`: `__init__.py`, `__main__.py` (`from <package>.main import main; main()`), `main.py`, `config/{logger,paths,runtime}.py`, `hal/`, one subpackage per functional layer, `lib/`.
- **TypeScript service** `src/<package>/` (no nested `src/`): `package.json`, `tsconfig.json`, `main.ts` (or `main.tsx` + `index.html` + `vite.config.ts` for a UI), `config/{logger,runtime}.ts`, `hal/`, one folder per functional layer, `lib/`.
- **Root manifests**, only for the toolchains in use: `pyproject.toml` (hatch, explicit `packages`, one `[project.scripts]` entry per Python service, `[dependency-groups] dev` with the kit dependencies and pytest, `[tool.pytest.ini_options]` with `testpaths` and `pythonpath` over `verification/`) and `uv.lock`; `package.json` (private, `packageManager: pnpm`), `pnpm-workspace.yaml` (`src/*`, `verification/*`) and `pnpm-lock.yaml`. Plus `cmd/` and `daemon/` when the design deploys to a host.
- **Kit** `verification/`: `run.sh`, `golden/` + `manifest.md`, `telemetry/`, and `verification/<package>/` per service with `mock_hal/`, `stubs/`, `fakes/`, `drivers/`, `test/` (a private pnpm package with vitest for a TS service).
- **Mixed example:** `fm_edge` (Python) + `dashboard` (TS), the T8 scenario.

Conventions carried over from nexus-API inside each service: type hints everywhere, Google-style docstrings (TSDoc in TS), `.env.example` committed and `.env` ignored, paths resolved in `config/paths.py`.

`verification/run.sh <vl0|vl1>` starts the telemetry companion, runs `uv run pytest -m <level>` when a Python service exists and `pnpm -r --filter "./verification/*" test:<level>` when a TS service exists, stops the companion, attaches its readings, and exits non-zero if any run failed.

## `references/logger.py`

A self-contained copy of `src/codeanvil/config/logger.py` (D10), with **no `codeanvil` import**:

- Same `_COLORS` (DEBUG `\033[90m`, INFO `\033[35m`, WARNING `\033[33m`, ERROR `\033[31m`), `_DIM` logger name, `_supports_color()` with `NO_COLOR`, `FORCE_COLOR`, Windows VT enable and the TTY check.
- Same format `[%(asctime)s] %(levelname)s %(name)s.%(funcName)s %(message)s`, stderr handler, `propagate = False`, no duplicate handlers.
- `formatTime` inlines `format_timestamp`: `%Y-%m-%d %H:%M:%S` plus `.mmm` milliseconds, in `ZoneInfo(TIMEZONE)`; `TIMEZONE` is read from `config/runtime.py`, defaults to `America/Bogota`, and falls back to `UTC` when unknown.

## `references/logger.ts`

The TypeScript twin (D10), no dependency: `getLogger(name)` returning `debug`, `info`, `warn`, `error`. Same format and timestamp (`Intl.DateTimeFormat` with `TIMEZONE` from `config/runtime.ts`, same default and fallback). Node: same ANSI codes, `NO_COLOR` / `FORCE_COLOR`, TTY check, stderr, `funcName` from the stack trace (best effort). Browser: same hues through `%c` CSS, no `funcName`.

## Steps

1. **Initial layer (S3).** Create the D2 tree and root manifests from `references/project_layout.md` for the design's `Toolchain` (D7), lock dependencies (`uv lock`, `pnpm install`), and copy `references/logger.py` or `references/logger.ts` to every service's `config/`. Build `verification/run.sh` and every tool of design §1.3.4 before any module, with the design's `Toolchain` (D7): Mock HAL with its VL-0 vectors and VL-1 synthetic generator, golden vectors with `verification/golden/manifest.md` (D4), telemetry companion (D3), one stub or fake peer per contract, drivers, and the Real HW HAL with a fake device API only in `mock+real`. Then the base layer of each service. Run base unit tests and the **top-down** test (base + all stubs) with the telemetry companion recording.
2. **ML (loose end, S10).** If design §1.5 exists, stop before any code with exactly `ML integration is future work. Remove design §1.5 for this round.` and write no iteration (FW-ML-3).
3. **Modules in DAG order (§2.2).** Per module: implement against its contract, unit test, **bottom-up** test with a driver through the base, replace its stub.
4. **Services and paths.** Producer and consumer contract tests with fake peers, then each `PATH-*` with the real service processes and Mock HAL input.
5. **VL-1 tests (written, not claimed).** For every module and `PATH-*` with `required_vl` VL-1 or higher: a test fed by the Mock HAL synthetic generator that measures the metric against its `SYS-*` threshold from `G0_SyRS.md`, with the telemetry companion attached. S2 may run them to check they execute, but never reports their result as evidence: the claim belongs to G2.1 (D8).
6. **Floor run.** `verification/run.sh vl0` runs the whole VL-0 suite with the telemetry companion attached. Write `test_run.md` with both `run.sh` commands.
7. Write the iteration and return `S2 complete. Run the G2 skill.`

## Hard rules

- Implement only what the design declares, with the design's `Toolchain`. A missing interface, an undeclared dependency, an incomplete contract or an empty `Toolchain` is a **design defect** (D6): write `| HITL | FEEDBACK |` with `Verdict: design defect` and the sections, then stop.
- **Infeasibility is reported through G2 (paper §9.2).** S2 never runs the RFD skill. When a requirement looks unreachable on the declared COTS platform, record it in `test_run.md` under `Possible infeasibility` with the requirement IDs and the run that shows it, and finish the pass. G2 presents it and offers the RFD option.
- Expected values come from §3 vectors and the golden manifest, never computed by the agent.
- No service imports or depends on anything under `verification/`: kit Python dependencies only in the dev group, no service `package.json` lists a kit package. The telemetry companion is never under `src/` (S2).
- Only the toolchains of D7. No `requirements.txt`, no npm or yarn lockfile.
- **Delivered code never depends on CodeAnvil** (S12). Every module logs through its service's `config/logger.py` (`log = get_logger(__name__)`) or `config/logger.ts` (`getLogger(...)`); no `print` or bare `console.log`, and the logger file is never edited.
- In `mock+real`, the Real HW HAL's VL-0 tests use the fake device API; S2 never needs the hardware (S7).
- Report only results of runs that actually happened, with their command.
- **Resume, do not restart.** On a re-run, continue from what already exists in `src/` and `verification/`: re-run its tests, keep what passes, build what is missing. Never rewrite working code to start over.
- Rework: a G2 iteration with `Verdict: module defect` names the modules to fix (including a missing VL-1 test); redo step 3 or 5 for them, then step 6.

## RED tests first

Through `_skill_text("S2_implement_services")`: `Cycle closed by RFD. Continue in cycle`, `Cycle suspended by RFD. Run the RFD skill.`, `G1 must pass first. Run the G1 skill.`, `S1 must rework first. Run the S1 skill.`, `Based on: G1 iteration`, `Toolchain`, `project_layout.md`, `logger.py`, `logger.ts`, `get_logger(__name__)`, `src/<package>/`, `verification/run.sh vl0`, `--no-dev`, `Verdict: design defect`, `verification/golden/manifest.md`, `VL-1`, `Possible infeasibility`, `ML integration is future work. Remove design §1.5 for this round.`, `Verdict: module defect` (accepted as rework), `Resume` and `S2 complete. Run the G2 skill.`. Negative: the text never tells S2 to run the RFD skill.

For `references/logger.py` (scaffolded copy):

- It contains no `codeanvil` string.
- Imported in isolation (`python -I`, from a temporary folder holding it as `config/logger.py` with a minimal `config/runtime.py`), a record renders as `[YYYY-MM-DD HH:MM:SS.mmm] INFO name.func message`, matching CodeAnvil's own logger output for the same record with colours off.
- With `FORCE_COLOR=1` the level and the logger name carry the same ANSI codes as CodeAnvil's logger.

For `references/logger.ts`: contains no `codeanvil` string; run under Node (`node --experimental-strip-types`, or skipped with a reason when Node is absent) it renders the same line shape and ANSI codes as the Python logger for the same level, name and message.

For `references/project_layout.md`: names `pyproject.toml`, `uv.lock`, `__main__.py`, `pnpm-workspace.yaml` and `verification/run.sh`.

## Acceptance

1. Kit and base exist before the first module commit-sized step (T8).
2. `test_run.md` shows the full VL-0 suite with telemetry readings attached, plus `verification/run.sh vl1` covering every VL-1 module and path.
3. A forced contract gap produces a design-defect iteration and S1 accepts it (T8).
4. Interrupting S2 mid-module and re-running it keeps the finished modules (T8).
5. `grep -r codeanvil src/` finds nothing, and every service logs in the D10 format (T8).
6. `uv sync --frozen --no-dev` followed by `uv run <package>` starts the Python service without any kit dependency; the built wheel contains no `verification/` file (T8).

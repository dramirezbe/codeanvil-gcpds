# Interactive TUI for `codeanvil create`

**Objective**: Refactor CLI into modular structure, then add a Vite-style interactive prompt flow when `codeanvil create` is called without arguments or flags. Separates project name (human label) from folder name (filesystem directory). Provides `--name`/`--folder` flags so agents and scripts can skip the TUI.

**Branch**: `feat/interactive-create`
**Delivery**: `single-pr`
**Test runner**: `uv run --extra dev pytest tests/ -v`

## Specs

S0. **CLI modular refactor**: split the monolithic `CLI/cli.py` (353 lines) into focused modules. No behavior change — pure structural refactor. All existing tests must pass with updated imports.

Current:
```
src/codeanvil/CLI/
├── __init__.py
└── cli.py              ← argparser + 6 cmd_* + choose_option + main (353 lines)
```

After:
```
src/codeanvil/CLI/
├── __init__.py          ← re-exports main (keeps pyproject.toml entry point working)
├── main.py              ← main() + choose_option()
├── parser.py            ← argparser() — pure argument definition
├── commands/
│   ├── __init__.py      ← re-exports all cmd_* functions
│   ├── init.py          ← cmd_init()
│   ├── create.py        ← cmd_create() + input resolution logic
│   ├── list.py          ← cmd_list()
│   ├── sync.py          ← cmd_sync()
│   ├── status.py        ← cmd_status() + _latest_reports()
│   └── now.py           ← cmd_now()
└── prompts.py           ← interactive_create() + to_folder_name() (added in T2)
```

Import updates required:
- `pyproject.toml`: `codeanvil.CLI.cli:main` → `codeanvil.CLI.main:main`
- `src/codeanvil/__main__.py`: `from codeanvil.CLI.cli import main` → `from codeanvil.CLI.main import main`
- `tests/test_create.py`: `from codeanvil.CLI.cli import cmd_create` → `from codeanvil.CLI.commands.create import cmd_create`
- `tests/test_create.py`: monkeypatch paths `codeanvil.CLI.cli.*` → `codeanvil.CLI.commands.create.*`

S1. `codeanvil create` (no positional arg, no `--name` flag) launches an interactive TUI prompt sequence using **beaupy** (Rich-powered interactive prompts):
  - **Project Name**: free-text input via `beaupy.prompt()`, required, non-empty. Allows spaces and mixed case (e.g. "My SDR Lab").
  - **Folder Name**: auto-derived as `to_folder_name(project_name)` (lowercase, spaces/hyphens → underscores, strip non-alnum/underscore). Shown as default in a second `beaupy.prompt()` — user presses Enter to accept or types a custom folder name.
  - **Continue / Cancel**: `beaupy.confirm()`. Cancel exits with code 0 and no side effects. Ctrl+C at any prompt also cancels cleanly.

S2. `codeanvil create <name>` (positional arg present) keeps working exactly as today — non-interactive, `name` is both the project name and folder name. No behavior change for existing CLI usage. **Deprecated in favor of `--name`, but still supported.**

S3. **Flag-based non-interactive mode** (for agents, scripts, CI):
  - `codeanvil create --name "My SDR Lab"` — skips TUI entirely. Folder name auto-derived as `to_folder_name("My SDR Lab")` → `my_sdr_lab`.
  - `codeanvil create --name "My SDR Lab" --folder my_custom_folder` — skips TUI, uses explicit folder name.
  - `--folder` without `--name` is an error.
  - `--name` + positional arg is an error (ambiguous).
  - Combined with `-p` and `--mcp` as usual.

S4. The TUI renders like this (inspired by Vite/create-react-app), styled via beaupy + Rich:
```
  CodeAnvil — create project

  ? Project name: My SDR Lab
  ? Folder name: (my_sdr_lab) █

  Create project? [y/N]
```
  - Project name prompt appears first. After the user types and presses Enter, the folder name prompt appears with the derived default shown.
  - The user presses Enter to accept the default, or types a custom folder name.
  - After both inputs, a confirmation summary is shown.

S5. `project.yaml` manifest stores the human-readable project name in the `name` field (already exists — not a schema change). The DB `projects.name` column stores the project name (human label), and `projects.path` ends with the folder name. These can now differ: name="My SDR Lab", folder="my_sdr_lab".

S6. `scaffold_project()` accepts both `name` (human label for manifest/DB) and `folder_name` (directory name). When called from the legacy positional-arg path (S2), `folder_name` equals `name` (backward compat). When called from S1 or S3, they can differ.

S7. `codeanvil list` displays the project name (human label), not the folder name. Example:
```
  [0192a3b4] My SDR Lab  —  /home/user/my_sdr_lab  (2026-10-22 15:30:00)
```

S8. `codeanvil status` lookup by name uses the human label (project name), not the folder name.

S9. The `--path` / `-p` flag works with all three modes (TUI, flags, positional). Sets the parent directory.

S10. The `--mcp` flag works with all three modes. MCP servers are validated after input is collected, before scaffolding.

S11. **Terminal compatibility**: beaupy uses Rich for output and yakh for keyboard input. Supported: Linux terminals (xterm, kitty, alacritty, foot, GNOME Terminal), macOS Terminal/iTerm2, Windows cmd/PowerShell/Windows Terminal. If `sys.stdin` is not a TTY (piped input), fall back to `--name`/`--folder` flags or error with a helpful message.

S12. **New dependency**: `beaupy` added to `pyproject.toml` `dependencies`. Pulls in `rich` and `yakh` transitively.

## Tasks

| ID | Spec | Route | Status | Commit |
|----|------|-------|--------|--------|
| T0 | S0 | inline | done | 68b4649 |
| T1 | S12 | inline | done | 68b4649 |
| T2 | S1, S4, S11 | inline | done | 1dd036b |
| T3 | S3, S6, S9, S10 | inline | done | 1dd036b |
| T4 | S2 | inline | done | 1dd036b |
| T5 | S5, S7, S8 | inline | done | 1dd036b |
| T6 | all | inline | done | 1dd036b |

**T0 — CLI modular refactor (pure structural, no behavior change)**
Split `CLI/cli.py` into `CLI/main.py`, `CLI/parser.py`, and `CLI/commands/*.py`. Each `cmd_*` function moves to its own module under `commands/`. Shared imports (DB_PATH, connect_db, etc.) are imported locally in each command module. Update all import references:
- `pyproject.toml` entry point → `codeanvil.CLI.main:main`
- `__main__.py` → `from codeanvil.CLI.main import main`
- `tests/test_create.py` → import from `codeanvil.CLI.commands.create`, update monkeypatch paths
- Delete `cli.py` after migration.
Verify: all existing tests pass. `uv run codeanvil --version` works. `uv run codeanvil --help` shows all subcommands.

**T1 — Add beaupy dependency**
Add `beaupy` to `pyproject.toml` `dependencies`. Verify install with `uv pip install -e .`.

**T2 — TUI prompt module** `src/codeanvil/CLI/prompts.py`
New module with:
- `to_folder_name(name: str) -> str` — snake_case derivation (lowercase, spaces/hyphens → underscores, strip non-alnum/underscore, collapse consecutive underscores).
- `interactive_create(default_path: Path) -> tuple[str, str] | None` — returns `(project_name, folder_name)` or `None` on cancel. Uses `beaupy.prompt()` for text inputs, `beaupy.confirm()` for continue/cancel. Handles Ctrl+C and KeyboardInterrupt gracefully. Checks `sys.stdin.isatty()` and raises if not a TTY.

**T3 — Wire flags and interactive mode into `cmd_create` and parser**
- Add `--name` and `--folder` flags to the `create` subparser in `parser.py`.
- Make positional `name` optional (`nargs="?"`).
- Resolution logic in `commands/create.py`:
  1. `--name` present → non-interactive, `folder_name = --folder or to_folder_name(--name)`.
  2. Positional `name` present (no `--name`) → legacy path, `folder_name = name`.
  3. Neither → interactive TUI via `interactive_create()`.
  4. Both `--name` and positional → error.
  5. `--folder` without `--name` → error.
- Pass both `name` and `folder_name` through to `scaffold_project()`.

**T4 — Backward compat: legacy positional arg**
When positional `name` is provided (no `--name`), `folder_name = name` (current behavior). No TUI. Existing tests must pass unmodified.

**T5 — Update `scaffold_project` signature**
`scaffold_project(name, folder_name, target, ...)` — uses `folder_name` for the directory (`target / folder_name`), `name` for the manifest and DB. `write_project_manifest` already writes `name`. `register_project` already stores `name`. Just route the correct values.

**T6 — Tests**
- Unit test `to_folder_name()`: "My SDR Lab" → "my_sdr_lab", "hello-world" → "hello_world", "  spaces  " → "spaces", "UPPER" → "upper", "foo__bar" → "foo_bar", "" → raises ValueError.
- Flag-based: `codeanvil create --name "Test Proj"` scaffolds `test_proj/` with manifest name "Test Proj".
- Flag-based: `codeanvil create --name "Test" --folder custom` scaffolds `custom/` with name "Test".
- Error cases: `--folder` without `--name`, `--name` + positional arg.
- Legacy: `codeanvil create foo` still works (existing tests).
- Interactive: monkeypatch `beaupy.prompt` and `beaupy.confirm` to test `interactive_create()`.
- Non-TTY: verify error message when stdin is not a TTY and no flags provided.

## Log

L1. User request: "A little TUI when user executes codeanvil create. Like small TUI of vite react. When user executes codeanvil create, the project asks in TUI: Project Name (type project name), Folder Name (type folder name, default just snake_case the project name and erase spaces, if user want to edit it is ok), Continue button, Cancel button."

L2. User addition (2026-10-22): "Add external TUI library for stylish prompts. Compatible with TTY of Linux (kitty, alacritty, xterm), and PowerShell/cmd on Windows. Add flags `--name` and `--folder` to skip TUI for agent/script use."

L3. Library decision (2026-10-22): Chose **beaupy** over questionary/InquirerPy/stdlib. Reasons: (1) Rich-powered styling matches the Vite aesthetic, (2) lightweight deps (rich + yakh only), (3) cross-platform (Linux/macOS/Windows), (4) actively maintained (v3.11.0, Jan 2026), (5) simple API — `prompt()` + `confirm()` cover all needs.

L4. User addition (2026-10-22): Refactor CLI into modular structure as T0 before TUI work. Split monolithic `cli.py` (353 lines) into `main.py`, `parser.py`, and `commands/*.py`. Four import references to update: pyproject.toml, __main__.py, tests/test_create.py (import + 2 monkeypatch paths).

L5. Implementation (2026-10-22): T0+T1 landed in 68b4649 as a pure structural move — `CLI/cli.py` deleted, `CLI/{main,parser}.py` + `CLI/commands/{init,create,list,sync,status,now}.py` added, `CLI/__init__.py` re-exports `main`, entry point moved to `codeanvil.CLI.main:main`, test imports and monkeypatch paths updated. Suite at that commit: 54 passed (baseline unchanged).

L6. Dependency resolution (2026-10-22): `uv add beaupy` resolved **beaupy 4.0.1** (not 3.11.0), pulling `rich`, `python-yakh`, `questo`. API used is the 4.x one: `beaupy.prompt(text, initial_value=..., validator=..., raise_validation_fail=False)` and `beaupy.confirm(question)` (default No: Enter cancels). Ctrl+C raises `KeyboardInterrupt`, Esc raises `beaupy.Abort` — both handled as a clean cancel.

L7. T2/T3/T4/T5 landed in 1dd036b. `CLI/prompts.py` holds `to_folder_name()` + `interactive_create()`; `CLI/commands/create.py` holds `resolve_create_inputs()` with the 5-case precedence from T3. `scaffold_project(name, folder_name, target, ...)` keeps the label for manifest/DB and the folder for the directory. `--folder` without `--name`, `--name` + positional, and empty names raise `CreateInputError` -> `log.error` + exit 1.

L8. Evidence (2026-10-22): `uv run --extra dev pytest tests/ -q` -> **94 passed** (54 baseline + 40 new). End-to-end in a sandbox `HOME=/tmp/opencode/ca-e2e/home`: `create --name "My SDR Lab"` -> `my_sdr_lab/`, manifest `name: My SDR Lab`, DB row `name='My SDR Lab' path=.../my_sdr_lab`; `list` and `status "My SDR Lab"` show the label; `sync` inside the project reports `already registered`; `create LegacyProj` still uses the verbatim folder name; `--folder` without `--name`, `--name` + positional, and `--mcp bogus` exit 1 before any directory is created. The TUI was driven through a real PTY (see L9): typed name, Enter on the derived folder default, `y` on confirm -> scaffolds; Ctrl+C at the project prompt -> exit 0 and no directory.

L9. Test/verification note (2026-10-22): PTY drivers live outside the repo (`/tmp/opencode/drive_tui.py`, `/tmp/opencode/cancel_tui.py`) and were not committed — committed coverage is the monkeypatched `interactive_create()` unit tests plus the non-TTY subprocess test (`python -I -m codeanvil create` with `stdin=DEVNULL`).

L10. Docs (2026-10-22): README (quick start, command table, how-it-works diagram, project structure), CLAUDE.md (CLI module map, command examples), AGENTS.md (console-script entry point + runtime deps).

L11. Independent verification (2026-10-22): verifier re-ran the suite at HEAD (94 passed) and at baseline 8645ce5 (54 passed), checked the entry point, wheel contents (`uv build`), `uv lock --check`, and drove the TUI through a real PTY (happy path + Ctrl+C at each prompt, Esc, `n`, Enter-on-default: all exit 0, no directory, DB hash unchanged). Verdict: no blockers; S0-S12 all PASS. Advisories: (A1) logger prefixes now name `codeanvil.CLI.commands.*` (unavoidable under S0); (A2) the folder default is a pre-filled buffer, not a placeholder (beaupy has no placeholder API), so typing appends until cleared; (A3) `preflight()` now runs after input collection by design (S10 orders input before MCP validation); (A4) stale local artifacts predate the change (`dist/` wheel, `CLI/__pycache__/cli.*.pyc`, the globally installed `~/.local/bin/codeanvil`); (A5) `questo` is an extra transitive dep beyond rich/yakh. Probes pinning previously untested spec items (S2 never-prompt, S4 order/summary, S9 TUI target, S10 ordering, S11 no-widget, S12 declaration) were added to the committed suite: **104 passed**.

L12. Status (2026-10-22): all tasks T0-T6 done on `feat/interactive-create`; 3 work-unit commits plus this record. Native assessment over the branch range (`--base-ref 8645ce5 --committed-only`): risk `medium` (`executable_change`), `review_due: false`, reason `under_budget` — no native review started. Push and PR remain the user's decision.

# CodeAnvil — CLAUDE.md

## What this repo is

CodeAnvil is a **harness** that implements the V-SIL methodology (V-model at the SIL tier, made continuous) through Claude Code skills, agents, subagents, and MCP servers.

**Scope**: develops, tests, and validates **software on COTS hardware** (not necessarily OOTB) — it does not design hardware. All hardware is assumed commercial off-the-shelf; the GT informs what constraints that hardware imposes.

The repo has two sides with very different roles:

### `templates/` — The methodology (the real product)

The V-SIL pipeline encoded as executable artifacts:

- **`templates/GT/`** — Ground Truth document templates. GT is the methodology's input: 3 pre-processed `.md` files (not raw PDFs), human-authored, that define the contract a project must satisfy:
  1. **Requirements** (`placeholder_requirements.md`) — functional and non-functional requirements
  2. **HW Restrictions** (`placeholder_hw_restrictions.md`) — COTS hardware constraints (embedded specs, server deploy, DAQ/SDR datasheets)
  3. **Normativity** (`placeholder_normativity.md`) — applicable standards (ITU, ICNIRP, IEEE, etc.)
- **`templates/skills/`** — Skills executed at each gate:
  - `G0_valid_req_and_GT/` — **Deterministic structural validation** of the 3 GT files. No AI — pure script (`scripts/valid_structure.py`). `SKILL.md` documents the expected structure. Hard pass/fail.
  - `G1_start_design/` — Agent-driven: initiate design once G0 passes.
  - Future gates (G2, G3, ...) follow the same pattern.

### `src/codeanvil/` — The delivery tool (serves the methodology)

CLI + PySide6 UI that bootstraps projects, wires up the harness, and tracks state:

- **`__main__.py`** — entry point (`python -m codeanvil`)
- **`CLI/cli.py`** — argparse CLI with subcommands: `init`, `create`, `list`, `status`
- **`UI/ui.py`** — PySide6 graphical interface (planned)
- **`config/logger.py`** — cross-platform colored logger (`get_logger(__name__)`)
- **`config/paths.py`** — canonical paths (`WORKDIR`, `DB_PATH`, `PROJECTS_DIR`) + `ensure_dirs()`
- **`db/schema.py`** — SQLite schema: `projects`, `sessions`, `gate_results` tables + `db_exists()`, `create_schema()`
- **`db/sessions.py`** — session CRUD: `create_session`, `get_session`, `list_sessions`, `update_gate`, `record_gate_result`
- **`db/utils.py`** — `connect_db()` (WAL mode, row factory, foreign keys) + `health_db()`
- **`init/check.py`** — `preflight()` (workdir + DB checks) + `check_project_path()`
- **`init/create.py`** — `scaffold_project()` (copies GT templates + skills) + `register_project()` in DB

## Key concepts

- **GT (Ground Truth)**: 3 pre-processed `.md` files (requirements, HW restrictions, normativity) that define what "correct" means. Human-authored, not raw PDFs.
- **Gate (Gn)**: verification checkpoint. Sequential — G0 must pass before G1 runs. G0 is deterministic (script-only). G1+ use Claude Code agents.
- **Skill**: `SKILL.md` + optional scripts that define what happens at a gate. Live in `templates/skills/`.
- **Session**: persistent record of a project's progress through gates, stored in SQLite.

## Development rules

- Do not conflate the two sides: `src/` changes are tooling changes, `templates/` changes are methodology changes.
- Skills must be self-contained — an agent reading only `SKILL.md` and the GT should execute the gate.
- GT templates are placeholders; real content is filled per-project at scaffold time.
- The DB schema must support resuming a session at any gate.
- Use `get_logger(__name__)` for all logging.

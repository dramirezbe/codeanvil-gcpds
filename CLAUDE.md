# CodeAnvil — CLAUDE.md

## What this repo is

CodeAnvil is an **agent-agnostic harness** that implements the V-SIL methodology (V-model at the SIL tier, made continuous) through skills, agents, subagents, and MCP servers. It is designed to work with any AI coding agent (Claude, Codex, OpenCode, Pi, etc.) — the methodology is the product, not the runtime.

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
- **`config/paths.py`** — canonical paths (`WORKDIR`, `DB_PATH`) + `ensure_dirs()`. Projects live wherever the user creates them, not under `~/.codeanvil/`.
- **`db/schema.py`** — SQLite schema: `projects`, `sessions`, `gate_results` tables + `db_exists()`, `create_schema()`
- **`db/sessions.py`** — session CRUD: `create_session`, `get_session`, `list_sessions`, `update_gate`, `record_gate_result`
- **`db/utils.py`** — `connect_db()` (WAL mode, row factory, foreign keys) + `health_db()`
- **`init/check.py`** — `preflight()` (workdir + DB checks) + `check_project_path()`
- **`init/create.py`** — `scaffold_project()` (copies GT templates + skills) + `register_project()` in DB

## Key concepts

- **GT (Ground Truth)**: 3 pre-processed `.md` files (requirements, HW restrictions, normativity) that define what "correct" means. Human-authored, not raw PDFs.
- **T# (Test GT)**: numbered test cases (`methodology/test/T<n>_<name>/`) that serve as V-SIL system inputs — real-world GT instances used to validate and stress-test the methodology pipeline end-to-end. Each T# folder contains raw project materials (proposals, papers, design docs) from which the 3 GT files would be derived. They are the methodology's integration tests.
  - **T1_FM-monitoring** — SDR-based FM broadcast compliance monitoring system. LaTeX specification (no executable code). RAG-informed from regulatory docs (FCC Part 73, ANE Res. 105, ITU-R BS.412/450/SM.2152, ISO/IEC 17025). Covers DSP pipeline, compliance measurands, uncertainty budgets, and decision frameworks.
  - **T2_IoT-Indoor** — Indoor IoT radio environment mapping at 2.4 GHz ISM (Proyecto Hermes / GCPDS). Contains the Hermes proposal, radio environment mapping literature, and a variable adaptation design doc.
- **Gate (Gn)**: verification checkpoint. Sequential — G0 must pass before G1 runs. G0 is deterministic (script-only). G1+ use AI coding agents (any runtime).
- **Skill**: `SKILL.md` + optional scripts that define what happens at a gate. Agent-agnostic — any coding agent that reads markdown can execute them. Live in `templates/skills/`.
- **Session**: persistent record of a project's progress through gates, stored in SQLite.

## Development rules

- Do not conflate the two sides: `src/` changes are tooling changes, `templates/` changes are methodology changes.
- Skills must be self-contained — an agent reading only `SKILL.md` and the GT should execute the gate.
- GT templates are placeholders; real content is filled per-project at scaffold time.
- The DB schema must support resuming a session at any gate.
- Use `get_logger(__name__)` for all logging.

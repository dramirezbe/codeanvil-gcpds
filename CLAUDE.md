# CodeAnvil — CLAUDE.md

## What this repo is

CodeAnvil is an **agent-agnostic harness** that implements the V-SIL methodology (V-model at the SIL tier, made continuous) through skills, agents, subagents, and MCP servers. It is designed to work with any AI coding agent (Claude, Codex, OpenCode, Pi, etc.) — the methodology is the product, not the runtime.

**Scope**: develops, tests, and validates **software on COTS hardware** (not necessarily OOTB) — it does not design hardware. All hardware is assumed commercial off-the-shelf; the GT informs what constraints that hardware imposes.

The repo has two sides with very different roles:

### `templates/` — The methodology (the real product)

The V-SIL pipeline encoded as executable artifacts:

- **`templates/GT/`** — Ground Truth document templates. GT is the methodology's input: 3 pre-processed `.md` files (not raw PDFs), human-authored, that define the contract a project must satisfy:
  1. **Requirements** (`G0_SRS.md`) — System Requirements Specification (IEEE 29148)
  2. **HW Restrictions** (`G0_HCS.md`) — Hardware Constraints Specification (§2.4 Design Constraints)
  3. **Normativity** — applicable standards (ITU, ICNIRP, IEEE, etc.) — template not yet implemented
- **`templates/skills/`** — Skills executed at each gate:
  - `G0_valid_req_and_GT/` — **Deterministic structural validation** of the GT files (SRS + HCS). No AI — pure script (`scripts/g0_validate.py`). `SKILL.md` is the agent contract, `references/RULES.md` the full rule tables. Hard pass/fail.
  - `custody-chain/` — **Cross-cutting provenance skill** (gate `*`). Seals GT files after G0 pass (`source_snapshot.py`), tracks chain of custody for audit documents (`custody_ledger.py`, HMAC-signed hash-chain), validates audit controls (`control_registry.py`), and verifies port bindings (`port_check.py`). All stdlib-only.
  - `G1_start_design/` — Agent-driven: initiate design once G0 passes.
  - Future gates (G2, G3, ...) follow the same pattern.

### `src/codeanvil/` — The delivery tool (serves the methodology)

CLI + PySide6 UI that bootstraps projects, wires up the harness, and tracks state:

- **`__main__.py`** — entry point (`python -m codeanvil`)
- **`CLI/cli.py`** — argparse CLI with subcommands: `init`, `create`, `list`, `status`
- **`UI/ui.py`** — PySide6 graphical interface (planned; see `UI/README.md` for scope)
- **`config/logger.py`** — cross-platform colored logger (`get_logger(__name__)`)
- **`config/paths.py`** — canonical paths (`WORKDIR`, `DB_PATH`) + `ensure_dirs()`. Projects live wherever the user creates them, not under `~/.codeanvil/`.
- **`db/schema.py`** — SQLite schema: `projects`, `sessions`, `gate_results` tables + `db_exists()`, `create_schema()`
- **`db/sessions.py`** — `list_sessions` (read a project's session rows). Gate orchestration is harness-driven (in the scaffolded `AGENTS.md`), not tool code — there is no orchestrator writing sessions or gate results.
- **`db/utils.py`** — `connect_db()` (WAL mode, row factory, foreign keys) + `health_db()`
- **`init/check.py`** — `preflight()` (workdir + DB checks) + `check_project_path()`
- **`init/create.py`** — `scaffold_project()` (copies skills to `.agents/skills/`, embeds GT reference templates inside skills, rewrites repo-root paths, creates agent symlinks, writes user `GT/` dir) + `register_project()` in DB (idempotent). Templates located via `_find_templates_dir()` (editable install: source tree; wheel install: `importlib.resources`)
- **`init/mcp.py`** — MCP server lifecycle: `install_mcp_server()` (clone + prewarm), `copy_mcp_skills()` (prefix + gate frontmatter), `generate_agent_mcp_configs()` (per-agent JSON: `.mcp.json`, `.vscode/`, `.opencode/`, `.codex/`), `_detect_system_site_packages()` (bridges system packages like gnuradio into uv venvs via `PYTHONPATH`)

## Key concepts

- **GT (Ground Truth)**: 3 pre-processed `.md` files (requirements, HW restrictions, normativity) that define what "correct" means. Human-authored, not raw PDFs.
- **T# (Test GT)**: numbered test cases (`methodology/test/T<n>_<name>/`) that serve as V-SIL system inputs — real-world GT instances used to validate and stress-test the methodology pipeline end-to-end. See [`methodology/test/README.md`](methodology/test/README.md) for the full test catalog and end-to-end manual test procedure.
  - **T0_ANE-Lap2** — SDR spectrum monitoring edge sensor (ANE). **GT-ready**: `just-edge/SRS.md` + `just-edge/HCS.md` are valid GT files that can be copied directly into a project as `G0_SRS.md` / `G0_HCS.md`.
  - **T1_FM-monitoring** — SDR-based FM broadcast compliance monitoring system. Raw LaTeX spec (GT must be derived). RAG-informed from regulatory docs (FCC Part 73, ANE Res. 105, ITU-R BS.412/450/SM.2152, ISO/IEC 17025).
  - **T2_IoT-Indoor** — Indoor IoT radio environment mapping at 2.4 GHz ISM (Proyecto Hermes / GCPDS). Raw proposal + literature (GT must be derived).
- **Gate (Gn)**: verification checkpoint. Sequential — G0 must pass before G1 runs. G0 is deterministic (script-only). G1+ use AI coding agents (any runtime).
- **Skill**: `SKILL.md` + optional scripts that define what happens at a gate. Agent-agnostic — any coding agent that reads markdown can execute them. Live in `templates/skills/` (repo) and `.agents/skills/` (scaffolded projects).
- **Gate progress**: tracked by the harness via the GT files and `.provenance/` artifacts, not by the tool. There is no orchestrator advancing a stored session — the agent reads the scaffolded `AGENTS.md` to find the next gate.
- **MCP server**: external tool provider (Model Context Protocol) that gives agents callable tools beyond text. Installed globally to `~/.codeanvil/mcp/<name>/`, wired into projects via per-agent config files. First server: Marconi (GNU Radio — 19 tools, 6 skills for RF/SDR). Configured in `templates/config.yaml` under `mcp_servers`, logic in `src/codeanvil/init/mcp.py`.

## Active plans

| Plan                 | Path                       | Status    | Description                                                        |
|----------------------|----------------------------|-----------|--------------------------------------------------------------------|
| G0 validation script | `plans/g0_skill.md`        | DONE      | Deterministic Python script to structurally validate SRS/HCS against IEEE 29148 templates |
| Scaffold CLI         | `plans/scaffold_cli.md`    | DONE      | pyproject.toml, skill dir convention (.agents/skills/ + symlinks), path rewriting, GT inside skills |
| AGENTS.md template   | `plans/agents_md_template.md` | PLANNED | Config-driven scaffold: YAML config, AGENTS.md template with dynamic skills, multi-agent symlinks |
| MCP integration      | `plans/dazzling-percolating-cook.md` | DONE | Agent-agnostic MCP server integration: Marconi/gr-mcp as first server, system package bridging, per-agent configs |

## Installation

Two install paths:

- **End users**: `curl -fsSL https://raw.githubusercontent.com/dramirezbe/codeanvil-gcpds/main/install.sh | bash` — installs `uv` if needed, then `uv tool install` from GitHub. Shell detection (bash/zsh/fish) + PATH injection with sentinel comments.
- **Developers**: `uv pip install -e .` from a local clone. Templates resolved from the source tree via `_find_templates_dir()`.

Templates are bundled into the wheel via hatch `force-include` (`pyproject.toml`), so non-editable installs work.

## Two contexts — never confuse them

There are two completely different environments where an agent reads these files:

### 1. This repo (CodeAnvil source — you are here)

The agent is a **developer** of the tool. The working directory is the CodeAnvil repo.

```
codeanvil-gcpds/                  ← repo root
├── src/codeanvil/                ← CLI + scaffold logic (Python package)
├── templates/
│   ├── skills/                   ← skill SOURCE templates (repo-root paths)
│   │   ├── G0_valid_req_and_GT/
│   │   └── custody-chain/
│   ├── GT/                       ← GT reference templates (IEEE 29148)
│   ├── AGENTS/TEMPLATE_AGENT.md  ← AGENTS.md Jinja template
│   └── config.yaml               ← single source of truth for scaffold
├── install.sh                    ← curl installer
├── CLAUDE.md                     ← THIS FILE (dev instructions)
└── AGENTS.md                     ← repo-level agent instructions
```

- Skill paths use **repo-root** form: `templates/skills/custody-chain/scripts/...`
- `path_replacements` in `config.yaml` rewrites them during scaffold.
- Changes here affect the **tool and methodology**, not any user project.

### 2. A scaffolded user project (what `codeanvil create` produces)

The agent is a **user** running the V-SIL methodology. The working directory is the
project folder — it has no `src/`, no `templates/`, no `pyproject.toml`.

```
/path/to/project/                 ← project root (anywhere on disk)
├── AGENTS.md                     ← generated from TEMPLATE_AGENT.md (canonical)
├── CLAUDE.md -> AGENTS.md        ← symlink
├── GT/                           ← user-authored ground truth (SRS, HCS)
│   ├── G0_SRS.md
│   └── G0_HCS.md
├── .provenance/                  ← custody-chain artifacts (snapshot, ledger)
├── .agents/
│   ├── skills/                   ← copied skills (project-root paths)
│   │   ├── G0_valid_req_and_GT/
│   │   │   ├── SKILL.md
│   │   │   ├── scripts/
│   │   │   └── templates/        ← locked GT reference copies
│   │   ├── custody-chain/
│   │   │   ├── SKILL.md
│   │   │   └── scripts/
│   │   └── marconi-*/SKILL.md    ← (if --mcp marconi) 6 RF/SDR skills
│   └── mcp.yaml                  ← (if --mcp) agent-agnostic MCP manifest
├── .mcp.json                     ← (if --mcp) Claude Code MCP server definition
├── .claude/
│   ├── skills -> ../.agents/skills
│   ├── settings.json             ← (if --mcp) enabledMcpjsonServers
│   └── settings.local.json       ← (if --mcp) enabledMcpjsonServers
├── .github/skills -> ../.agents/skills
└── .github/copilot-instructions.md  ← pointer to AGENTS.md
```

- Skill paths use **project-root** form: `.agents/skills/custody-chain/scripts/...`
- GT files are **user-authored inputs**, not tool templates.
- The agent reads `AGENTS.md` (or `CLAUDE.md` symlink) and follows the methodology.

### How they connect

```
codeanvil init                              → ~/.codeanvil/ + DB
codeanvil init --mcp marconi               → + clone to ~/.codeanvil/mcp/marconi/
codeanvil create myproj -p /path/to/        → /path/to/myproj/ (scaffolded)
codeanvil create myproj --mcp marconi       → + marconi-* skills, MCP configs, PYTHONPATH
```

The scaffold copies `templates/skills/` → `.agents/skills/`, runs `path_replacements`
on `.md` files, generates `AGENTS.md` from the template, creates symlinks, and registers
the project in the DB. With `--mcp`, it also copies MCP skills (prefixed), generates
per-agent MCP configs, and bridges system packages (like gnuradio) via `PYTHONPATH`.
After that the project is self-contained — it does not depend on the repo at runtime.

### Installation paths

- **End users**: `curl -fsSL https://raw.githubusercontent.com/dramirezbe/codeanvil-gcpds/main/install.sh | bash`
  - Installs `uv` if needed, then `uv tool install` from GitHub (Python 3.12)
  - Injects `~/.local/bin` into PATH (bash/zsh/fish), idempotent
  - Templates bundled in the wheel via hatch `force-include`
- **Developers**: `uv pip install -e .` from a local clone
  - Templates resolved from source tree via `_find_templates_dir()`
- **Uninstall**: `bash install.sh uninstall` (removes tool + PATH entry)

## Development rules

- Do not conflate the two sides: `src/` changes are tooling changes, `templates/` changes are methodology changes.
- Skills must be self-contained — an agent reading only `SKILL.md` and the GT should execute the gate.
- GT templates are locked reference artifacts inside skills, not user-editable project files.
- Gate state is harness-owned (GT files + `.provenance/`); the tool's DB holds project registration only, and does not drive or resume gates.
- Use `get_logger(__name__)` for all logging.

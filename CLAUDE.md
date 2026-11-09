# CodeAnvil — CLAUDE.md

## What this repo is

CodeAnvil is an **agent-agnostic harness** that implements the V-SIL methodology (V-model at the SIL tier, made continuous) through skills, agents, subagents, and MCP servers. It is designed to work with any AI coding agent (Claude, Codex, OpenCode, Pi, etc.) — the methodology is the product, not the runtime.

**Scope**: develops, tests, and validates **software on COTS hardware** (not necessarily OOTB) — it does not design hardware. All hardware is assumed commercial off-the-shelf; the GT informs what constraints that hardware imposes.

## First read for current work

This is the **CodeAnvil source repo**, so edit `src/codeanvil/` for delivery
code and `templates/` for methodology. Read [`AGENTS.md`](AGENTS.md) for the
active stage contracts and source-versus-scaffold distinction. The current
release is [v0.6.0](https://github.com/dramirezbe/codeanvil-gcpds/releases/tag/v0.6.0).

For the first complete S0 → G2 run, start with the
[`T3_FM-mock` snapshot guide](methodology/test/T3_FM-mock/FIRST_FULL_FLOW_SNAPSHOT.md),
then the [archived project's `RUN.md`](methodology/test/T3_FM-mock/first_full_flow_2026-11-05/RUN.md)
and [review holdout](methodology/test/T3_FM-mock/S1_G1_review_holdout_2026-11-05.md).
The snapshot includes a G2 design-defect FEEDBACK → S1/G1/S2 rework → G2 PASS.
The later entry-point fix has separate smoke evidence; the original G2 verdict
does not cover that correction. The holdout's document renames, report moves,
telemetry collector and pause policy are implemented by the
[T3 holdout refactor](odd/tasks/t3-holdout-refactor/2026-11-06_1410_t3_holdout_refactor.md);
the VL-2 machine interface remains a proposal.

The repo has two sides with very different roles:

### `templates/` — The methodology (the real product)

The V-SIL pipeline encoded as executable artifacts:

- **`templates/GT/`** — Ground Truth document templates. GT is the methodology's input: human-authored `.md` files (not raw PDFs) that define the contract a project must satisfy, following the IEEE/ISO/IEC 29148:2018 document family:
  1. **StRS** (`StRS.md`) — Stakeholder Requirements Specification (§9.4): stakeholder requirements (`STK-`), COTS hardware constraints (`HWC-`), and normative obligations (`NRM-` with inline compliance traceability)
  2. **SyRS** (`SyRS.md`) — System Requirements Specification (§9.5): per-measurand system requirements (`SYS-`) — methods, correction chains, uncertainty budgets — tracing to StRS blocks
  The author writes a Build Package (`.codeanvil/GT/build_package.md`); the S0 skill casts it into the two blueprints. The scaffold has no `SRS.md`; S1 writes `.codeanvil/design/SDD.md` and `.codeanvil/design/dependency_graph.html`.
- **`templates/skills/`** — Skills for each stage and gate of the V-SIL v3 flow `S0 → G0 → S1 → G1 → S2 → G2`; RFD can be raised from any stage. Each skill is self-contained: its templates, scripts and assets live in its own folder.
  - `S0_normalise_build_package/` — **Stage**: casts `.codeanvil/GT/build_package.md` into `.codeanvil/GT/StRS.md` and `SyRS.md` in one pass, with no judgement. Writes `S0.md`.
  - `G0_valid_req_and_GT/` — **Deterministic structural validation** of the GT pair (StRS + SyRS) plus the G0-X cross-document rules. No AI — pure script (`scripts/g0_validate.py`) — followed by the human Gate H. `SKILL.md` is the agent contract, `references/RULES.md` the full rule tables.
  - `S1_design_services/` — **Stage**: designs a system of layered services (`.codeanvil/design/SDD.md`) and its dependency graph (`.codeanvil/design/dependency_graph.html`, vis-network vendored in `assets/`). Design §0.5 defines one runnable entry point for the complete system.
  - `G1_design_review/` — **Human gate**: no script. The agent fills a checklist, including G1.15 for the runnable entry point, and recommends; the human answers PASS, FEEDBACK or RFD.
  - `RFD_request_for_deviation/` — Outside the chain: decision document when requirements are infeasible on the declared COTS platform. Suspends the cycle until the author decides.
  - `S2_implement_services/` — **Stage**: builds the services under `src/<service>/`, the verification kit under `verification/` (Mock HAL, golden vectors, telemetry collector), the runnable §0.5 entry point and its VL-0 smoke test. Uses `references/project_layout.md` and the locked `references/logger.py` and `references/logger.ts`, and runs the locked `scripts/telemetry_collector.py` in place on the methodology runtime (psutil). Writes `S2.md` and `S2_artifacts/test_run.md`.
  - `G2_adaptive_verification/` — **Human gate**: delegates the `test_run.md` commands to the `vsil-verifier` subagent, checks the entry-point smoke evidence, presents the results and records PASS, FEEDBACK (`Verdict: module defect` → S2, `Verdict: design defect` → S1) or RFD. PASS writes `G2_artifacts/verified_prototype.md` with run instructions.
- **`templates/agents/`** — Subagent bodies. `vsil-verifier.md` is the one shared body of the G2 verifier; `codeanvil create` writes it per runtime (`.claude/agents/`, `.opencode/agents/`, `.codex/agents/`) as listed under `subagents` in `config.yaml`.
- **`templates/backups/`** — Retired in v3 and kept for later: `custody-chain/`, `G1_start_design/` and `G1_SRS.md`. Not scaffolded and not shipped in the wheel.

### `src/codeanvil/` — The delivery tool (serves the methodology)

CLI + PySide6 UI that bootstraps projects, wires up the harness, and tracks state:

- **`__main__.py`** — entry point (`python -m codeanvil`)
- **`CLI/`** — argparse CLI: `main.py` (entry point + dispatch), `parser.py` (argument definitions), `prompts.py` (interactive `create` TUI via beaupy/Rich), `commands/` (one module per subcommand: `init`, `create`, `list`, `sync`, `status`, `now`, `backup`, `runtime`, `python`, `mcp`, `sandbox`, `upgrade`)
- **`reports.py`** — shared report parser (`ReportState`, `_report_state()`, `_cycle_reports()`, `_gate_order()`, `backup_entries()`): the gate reports `status` reads and the backups `backup` resolves; command modules never import from each other
- **`UI/ui.py`** — PySide6 graphical interface (planned; see `UI/README.md` for scope)
- **`config/logger.py`** — cross-platform colored logger (`get_logger(__name__)`)
- **`config/paths.py`** — canonical paths (`WORKDIR`, `DB_PATH`) + `ensure_dirs()` (with one-time `~/.codeanvil/` → `~/.codeanvil-config/` migration) + `find_manifest()` + project-local `PROJECT_*` constants. Projects live wherever the user creates them, not under `~/.codeanvil-config/`.
- **`config/identity.py`** — `generate_uuidv7()` (stdlib-only RFC 9562 UUIDv7; Python 3.10+ compatible)
- **`config/time.py`** — `format_timestamp()` (human-readable) + `format_timestamp_machine()` (filename-safe, for `codeanvil now --machine`)
- **`db/schema.py`** — SQLite schema: `projects` table only (TEXT UUIDv7 id, name, path, created_at) + `db_exists()`, `create_schema()`, `has_legacy_schema()`/`recreate_if_legacy()` (pre-release migration)
- **`db/projects.py`** — registry CRUD: `register_project()` (idempotent by UUID), `sync_project()` (register/no-op/moved upsert), `get_project_by_id()`, `get_project_by_name()`, `list_projects()`. The gate chain is report-driven (each skill checks its predecessor's report), not tool code — no orchestrator rows.
- **`db/utils.py`** — `connect_db()` (WAL mode, row factory, foreign keys) + `health_db()`
- **`init/check.py`** — `preflight()` (workdir + DB checks) + `check_project_path()`
- **`init/create.py`** — `scaffold_project()` (copies skills to `.agents/skills/`, embeds GT reference templates inside skills, rewrites repo-root paths, creates agent symlinks, writes `.codeanvil/GT/`, `.codeanvil/design/`, `.codeanvil/backups/`) + `write_project_manifest()`. Templates located via `_find_templates_dir()` (editable install: source tree; wheel install: `importlib.resources`)
- **`init/sync.py`** — `run_sync()` (clone/move flow: read manifest → migrate `.provenance/` → upsert DB) + `_migrate_provenance()`
- **`init/mcp.py`** — MCP manager: `install_mcp_server()` / `update_mcp_server()` (clone, check out the pinned `ref`, venv on the system interpreter the server's system packages need, probe), `doctor()`, `run_server()` (the `codeanvil mcp run` launcher: resolves install path, project root and env at start-up; `execvpe` on POSIX, parent process on Windows), `generate_agent_mcp_configs()` (per-agent JSON calling the launcher, no absolute path: `.mcp.json`, `.vscode/`, `opencode.json`, `.codex/`), `enable_server()` / `disable_server()`
- **`init/system_packages.py`** — OS-installed Python packages (gnuradio): `probe()` imports in the target interpreter and reports ok / missing (with the OS-family install command from `config.yaml`) / ABI mismatch / broken; `cached_probe()`; `system_interpreter_for()`
- **`init/runtime.py`** — global methodology runtime (`~/.codeanvil-config/runtime/`): `sync()`, `add()`, `remove()`, `listing()`, `.pth` bridge for `runtime.system_packages`; the shipped `templates/runtime/` spec is rendered from `config.yaml` `runtime.base`
- **`skills.py`** — shared SKILL.md frontmatter parser (`name`, `description`, `gate`, `runtime`)

## Key concepts

- **GT (Ground Truth)**: the pair of human-authored `.md` files (StRS + SyRS) that define what "correct" means. Human-authored, not raw PDFs. Normativity lives inline in the StRS as `NRM-` blocks. S0 produces the pair from the author's Build Package.
- **T# (Test GT)**: numbered test cases (`methodology/test/T<n>_<name>/`) that serve as V-SIL system inputs — real-world GT instances used to validate and stress-test the methodology pipeline end-to-end. See [`methodology/test/README.md`](methodology/test/README.md) for the full test catalog and end-to-end manual test procedure.
  - **T0_ANE-Lap2** — SDR spectrum monitoring edge sensor (ANE). **GT-ready**: `just-edge/StRS.md` + `just-edge/SyRS.md` are valid GT files that can be copied directly into a project as `.codeanvil/GT/StRS.md` / `SyRS.md`.
  - **T1_FM-monitoring** — SDR-based FM broadcast compliance monitoring system. Raw LaTeX spec (GT must be derived). RAG-informed from regulatory docs (FCC Part 73, ANE Res. 105, ITU-R BS.412/450/SM.2152, ISO/IEC 17025).
  - **T2_IoT-Indoor** — Indoor IoT radio environment mapping at 2.4 GHz ISM (Proyecto Hermes / GCPDS). Raw proposal + literature (GT must be derived).
  - **T3_FM-mock** — ready Build Package and an archived mock-only full-flow run. The snapshot contains GT, code, verification kit and cycle reports; `RUN.md` starts the corrected preview.
- **Stage (Sn) and gate (Gn)**: stages produce, gates judge. Sequential — each needs its predecessor's report at `HITL: PASS`. G0 is the only deterministic gate (script); Gate H, G1 and G2 are human. A stage's PASS means "delivered".
- **Skill**: `SKILL.md` + optional scripts that define what happens at a gate. Agent-agnostic — any coding agent that reads markdown can execute them. Live in `templates/skills/` (repo) and `.agents/skills/` (scaffolded projects).
- **Gate progress**: tracked by the harness via the GT files and cycle-scoped reports (`.codeanvil/report/<cycle>/<gate>.md`), not by the tool. There is no orchestrator advancing a stored session — each skill checks its predecessor's report, and the agent asks for the cycle on project open.
- **MCP server**: external tool provider (Model Context Protocol) that gives agents callable tools beyond text. Installed globally to `~/.codeanvil-config/mcp/<name>/`, wired into projects via per-agent config files. First server: Marconi (GNU Radio — 19 tools, 6 skills for RF/SDR). Configured in `templates/config.yaml` under `mcp_servers`, logic in `src/codeanvil/init/mcp.py`.

## V-SIL paper

The formal methodology paper lives at `methodology/V-SIL-v2/V-SIL.tex` (+ compiled PDF). It defines the V-SIL continuous verification framework that CodeAnvil implements.

## Archived plans

Completed plans live in `odd/tasks/` grouped by milestone. The 2026-11-05
full-flow plan is [complete](odd/tasks/vsil-v3-full-flow/2026-11-05_1421_vsil_v3_full_flow.md);
its remaining failure probes are future regression work, not recorded as PASS.

| Plan                 | Path                                              | Description                                                        |
|----------------------|---------------------------------------------------|--------------------------------------------------------------------|
| G0 validation script | `odd/tasks/scaffold-cli/2026-10-13_1227_g0_skill_plan.md` | Deterministic Python script to structurally validate the GT documents against IEEE 29148 templates |
| Scaffold CLI         | `odd/tasks/scaffold-cli/2026-10-21_1423_scaffold_cli_plan.md` | pyproject.toml, skill dir convention (.agents/skills/ + symlinks), path rewriting, GT inside skills |
| AGENTS.md template   | `odd/tasks/scaffold-cli/2026-10-14_1514_agents_md_template_plan.md` | Config-driven scaffold: YAML config, AGENTS.md template with dynamic skills, multi-agent symlinks |
| V-SIL v3 full flow | `odd/tasks/vsil-v3-full-flow/2026-11-05_1421_vsil_v3_full_flow.md` | S0 → G2 implementation, T3 full-flow run, v0.4.1 release; deferred probes documented |
| Windows support    | v0.4.2                                              | PowerShell installer, symlink fallback, tzdata/pathsep fixes, validated on Windows |

## Installation

Cross-platform (Linux, macOS, Windows). Two install paths:

- **End users (Linux/macOS)**: `curl -fsSL https://raw.githubusercontent.com/dramirezbe/codeanvil-gcpds/main/install.sh | bash` — installs `uv` if needed, then `uv tool install` from GitHub. Shell detection (bash/zsh/fish) + PATH injection with sentinel comments.
- **End users (Windows)**: `irm https://raw.githubusercontent.com/dramirezbe/codeanvil-gcpds/main/install.ps1 | iex` — installs `uv` if needed, adds `%USERPROFILE%\.local\bin` to user PATH. On Windows, symlinks fall back to directory junctions or file copies when Developer Mode is not enabled.
- **Developers** (all platforms): `uv pip install -e .` from a local clone. Templates resolved from the source tree via `_find_templates_dir()`.

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
│   │   ├── S0_normalise_build_package/
│   │   ├── G0_valid_req_and_GT/
│   │   ├── S1_design_services/
│   │   ├── G1_design_review/
│   │   ├── S2_implement_services/
│   │   ├── G2_adaptive_verification/
│   │   └── RFD_request_for_deviation/
│   ├── agents/vsil-verifier.md   ← shared body of the G2 verifier subagent
│   ├── backups/                  ← retired skills (custody-chain, G1_start_design)
│   ├── GT/                       ← GT reference templates (IEEE 29148)
│   ├── AGENTS/TEMPLATE_AGENT.md  ← AGENTS.md Jinja template
│   └── config.yaml               ← single source of truth for scaffold
├── install.sh                    ← Linux/macOS installer
├── install.ps1                   ← Windows installer
├── CLAUDE.md                     ← THIS FILE (dev instructions)
└── AGENTS.md                     ← repo-level agent instructions
```

- Skill paths use **repo-root** form: `templates/skills/G0_valid_req_and_GT/scripts/...`
- `path_replacements` in `config.yaml` rewrites them during scaffold.
- Changes here affect the **tool and methodology**, not any user project.

### 2. A scaffolded user project (what `codeanvil create` produces)

The agent is a **user** running the V-SIL methodology. The working directory is the
project folder — it has no `templates/`, and no `src/`, `verification/` or `pyproject.toml` until S2 builds the code.

```
/path/to/project/                 ← project root (anywhere on disk)
├── AGENTS.md                     ← generated from TEMPLATE_AGENT.md (canonical)
├── CLAUDE.md -> AGENTS.md        ← symlink
├── .codeanvil/                   ← every methodology-owned artifact
│   ├── GT/                       ← user-authored ground truth
│   │   ├── build_package.md      ← the author's input; S0 reads it
│   │   ├── StRS.md               ← written by S0
│   │   └── SyRS.md               ← written by S0
│   ├── design/                   ← S1 working copy
│   │   ├── SDD.md
│   │   └── dependency_graph.html
│   ├── backups/                  ← `codeanvil backup <stage>`; never overwritten
│   ├── project.yaml              ← project identity (UUIDv7, name, GT pointers)
│   └── report/                   ← per-cycle iterative reports (<cycle>/<gate>.md)
├── .agents/
│   ├── skills/                   ← copied skills (project-root paths)
│   │   ├── G0_valid_req_and_GT/
│   │   │   ├── SKILL.md
│   │   │   ├── scripts/
│   │   │   └── templates/        ← locked GT reference copies
│   │   ├── S0_normalise_build_package/   ← own blueprints in templates/
│   │   ├── S1_design_services/           ← references/ + assets/ (vis-network)
│   │   ├── G1_design_review/
│   │   ├── S2_implement_services/        ← references/ (layout, loggers, collector)
│   │   ├── G2_adaptive_verification/     ← references/verified_prototype.md
│   │   ├── RFD_request_for_deviation/
│   │   └── marconi-*/SKILL.md    ← (if --mcp marconi) 6 RF/SDR skills
│   └── mcp.yaml                  ← (if --mcp) agent-agnostic MCP manifest
├── .mcp.json                     ← (if --mcp) Claude Code MCP server definition
├── .claude/
│   ├── skills -> ../.agents/skills
│   ├── agents/vsil-verifier.md   ← generated (also .opencode/agents/, .codex/agents/*.toml)
│   ├── settings.json             ← (if --mcp) enabledMcpjsonServers
│   └── settings.local.json       ← (if --mcp) enabledMcpjsonServers
├── .github/skills -> ../.agents/skills
└── .github/copilot-instructions.md  ← pointer to AGENTS.md
```

- Skill paths use **project-root** form: `.agents/skills/G0_valid_req_and_GT/scripts/...`
- GT files are **user-authored inputs**, not tool templates.
- The agent reads `AGENTS.md` (or `CLAUDE.md` symlink) and follows the methodology.

### How they connect

```
codeanvil init                              → ~/.codeanvil-config/ + DB + methodology runtime
codeanvil runtime sync|add|remove|list|path → the global methodology venv (~/.codeanvil-config/runtime/)
codeanvil python <script> [args]           → run a skill script on the runtime (-I, from the project root)
codeanvil mcp add marconi                  → clone, pin, venv on gnuradio's interpreter, probe (= init --mcp)
codeanvil mcp update|remove|list|doctor    → MCP lifecycle; doctor names the fix for each problem
codeanvil mcp run marconi                  → the launcher every project config calls (stdio)
codeanvil mcp enable|disable marconi       → wire/unwire a server in the current project
codeanvil create                            → interactive prompts: project + folder name
codeanvil create --name "My SDR Lab"        → ./my_sdr_lab/ (folder derived from the label)
codeanvil create myproj -p /path/to/        → /path/to/myproj/ (legacy: name == folder)
codeanvil create myproj --mcp marconi       → + marconi-* skills, portable MCP configs (launcher)
codeanvil sync (inside a clone)            → register the project in the local DB
codeanvil list                             → registered projects (short UUID + local path)
codeanvil status [myproj]                  → cycles and latest HITL per gate (.codeanvil/report/)
codeanvil backup S0|S1|S2|G2               → copy the stage's files to .codeanvil/backups/<cycle>/
codeanvil now [--machine]                  → timestamp: human-readable / filename-safe
codeanvil upgrade                          → reinstall from latest main (uv), then the new binary's runtime sync
codeanvil sandbox <agent>                  → launch agent (claude|pi|opencode|codex) with only project-local settings
```

The scaffold copies `templates/skills/` → `.agents/skills/`, runs `path_replacements`
on `.md` files, generates `AGENTS.md` from the template, creates links, and registers
the project in the DB. On Windows, symlinks fall back to directory junctions or file
copies when Developer Mode is not enabled. With `--mcp`, it also copies MCP skills
(prefixed) and writes per-agent MCP configs that call `codeanvil mcp run <name>`. After
that the project does not depend on the repo at runtime. It does depend on the installed
`codeanvil` by design: skill scripts (G0, the S2 telemetry collector) run on the global
methodology runtime through `codeanvil python`, and MCP servers start through the
launcher. Delivered code (`src/`) never depends on the tool.

### Installation paths

- **Linux/macOS**: `curl -fsSL https://raw.githubusercontent.com/dramirezbe/codeanvil-gcpds/main/install.sh | bash`
  - Installs `uv` if needed, then `uv tool install` from GitHub (Python 3.12)
  - Injects `~/.local/bin` into PATH (bash/zsh/fish), idempotent
  - Templates bundled in the wheel via hatch `force-include`
- **Windows**: `irm https://raw.githubusercontent.com/dramirezbe/codeanvil-gcpds/main/install.ps1 | iex`
  - Same `uv tool install` flow; adds `%USERPROFILE%\.local\bin` to user PATH
  - Uninstall: `.\install.ps1 -Uninstall`
- **Developers** (all platforms): `uv pip install -e .` from a local clone
  - Templates resolved from source tree via `_find_templates_dir()`
- **Uninstall** (Linux/macOS): `bash install.sh uninstall` (removes tool + PATH entry)

## Development rules

- Do not conflate the two sides: `src/` changes are tooling changes, `templates/` changes are methodology changes.
- Skills must be self-contained — an agent reading only `SKILL.md` and the GT should execute the gate.
- GT templates are locked reference artifacts inside skills, not user-editable project files.
- Gate state is harness-owned (GT files + `.codeanvil/`); the tool's DB holds project registration only, and does not drive or resume gates.
- Use `get_logger(__name__)` for all logging.
- Use `codeanvil now` when a task needs human-readable timestamps. The function `codeanvil.config.time.format_timestamp()` is the single source for timestamps in CLI output, logger, and future gate artifacts. Do not use `datetime.now().strftime()` directly.

# CodeAnvil

[![CI](https://github.com/dramirezbe/codeanvil-gcpds/actions/workflows/ci.yml/badge.svg)](https://github.com/dramirezbe/codeanvil-gcpds/actions/workflows/ci.yml)

Agent-agnostic project scaffolding, templates, and agent definitions for the **V-SIL methodology** (V-model at the SIL tier, made continuous). Develops, tests, and validates software on COTS hardware — informed by Ground Truth documents — through the V-SIL v3 flow `S0 → G0 → S1 → G1 → S2 → G2`: agent-driven stages, one deterministic gate (G0) and human review gates, ending in a Verified Prototype.

Works with any AI coding agent: Claude, Codex, OpenCode, Pi, or others. Runs on **Linux, macOS and Windows**.

**Current release:** [v0.7.5](https://github.com/dramirezbe/codeanvil-gcpds/releases/tag/v0.7.5). Simple red-button deletion confirmation: Replaces typed-name UI confirmation with a direct question, Cancel and a red Delete button. Keeps explicit file-removal selection and existing identity/path safeguards.

**v0.7.0 background:** HIL harness groundwork: the telemetry collector becomes the `codeanvil telemetry` subcommand, and a remote-only MCP server (`vsil_hil_mcp`) runs the verification kit on a real compute unit over SSH — credential custody, a two-door command model and a per-target policy dial (trusted-policy MVP, not yet validated on hardware). The first realistic complete run, including a G2 → S1 rework loop, is archived under [`methodology/test/T0_FM-RPI-RTL-mock/`](methodology/test/T0_FM-RPI-RTL-mock/). Its [snapshot guide](methodology/test/T0_FM-RPI-RTL-mock/FIRST_FULL_FLOW_SNAPSHOT.md), [prototype run instructions](methodology/test/T0_FM-RPI-RTL-mock/first_full_flow_2026-11-05/RUN.md), and [review holdout](methodology/test/T0_FM-RPI-RTL-mock/S1_G1_review_holdout_2026-11-05.md) show the result and its limits.

> This methodology does not design hardware. It targets software running on Commercial Off-The-Shelf devices (not necessarily out-of-the-box), where the GT defines what constraints that hardware imposes.

## Install

### Linux / macOS

**One-liner** (installs `uv` if needed, then `codeanvil` from GitHub):

```bash
curl -fsSL https://raw.githubusercontent.com/dramirezbe/codeanvil-gcpds/main/install.sh | bash
```

**Uninstall**:

```bash
curl -fsSL https://raw.githubusercontent.com/dramirezbe/codeanvil-gcpds/main/install.sh | bash -s uninstall
```

### Windows

**PowerShell one-liner** (installs `uv` if needed, then `codeanvil` from GitHub):

```powershell
irm https://raw.githubusercontent.com/dramirezbe/codeanvil-gcpds/main/install.ps1 | iex
```

**Manual install / reinstall** (if the one-liner fails or you need to update):

```powershell
uv tool install --force-reinstall --python 3.11 "git+https://github.com/dramirezbe/codeanvil-gcpds.git"
```

**Uninstall**:

```powershell
.\install.ps1 -Uninstall
```

> On Windows, project symlinks fall back to directory junctions (no special
> privileges required) or file copies when Developer Mode is not enabled.

### Developer install (all platforms)

```bash
git clone https://github.com/dramirezbe/codeanvil-gcpds.git
cd codeanvil-gcpds
uv pip install -e .
```

## Quick start

```bash
# Prepare the global DB, methodology runtime and bundled UI
codeanvil init

# Open the graphical workspace (no Node, pnpm or extra Python install needed)
codeanvil ui

# Scaffold a new project interactively (project name, folder name, confirm)
codeanvil create

# ...or non-interactively, for agents/scripts/CI
codeanvil create --name "My SDR Lab"              # → ./my_sdr_lab/
codeanvil create --name "My SDR Lab" --folder sdr_lab

# Legacy form: the project name is also the folder name
codeanvil create myproject

# ...or in a specific path
codeanvil create myproject -p ~/projects

# Write your Build Package in myproject/.codeanvil/GT/build_package.md, then ask your agent to run
# the S0 skill. It writes the GT pair (IEEE 29148):
#   .codeanvil/GT/StRS.md  — Stakeholder Requirements Specification (§9.4)
#   .codeanvil/GT/SyRS.md  — System Requirements Specification (§9.5)
# Reference templates: .agents/skills/S0_normalise_build_package/templates/

# Validate the GT pair yourself (deterministic, no AI; the G0 skill runs the same script)
cd myproject
python3 .agents/skills/G0_valid_req_and_GT/scripts/g0_validate.py .codeanvil/GT/StRS.md .codeanvil/GT/SyRS.md

# Check project status (reads .codeanvil/report/ from the current directory)
codeanvil status

# Cloned the project elsewhere? Register/move it in your local DB
codeanvil sync

# Filename-safe timestamp (report filenames, machine identifiers)
codeanvil now --machine
```

The **agent** runs the stages and gates from `.agents/skills/`; there is no
`codeanvil run` command. G0 runs its deterministic script, while Gate H, G1
and G2 need a human verdict. After a G2 design-defect FEEDBACK, the same cycle
repeats S1 → G1 → S2 → G2; `codeanvil status` shows stale downstream reports.

### Try the completed FM mock example

From this repository, with Python 3.12+, `uv`, Node and `pnpm` installed:

```bash
cd methodology/test/T0_FM-RPI-RTL-mock/first_full_flow_2026-11-05
uv sync --frozen --no-dev
./run-demo SC-2
```

Open the local Vite URL printed by the launcher (normally
<http://127.0.0.1:5173/>). The spectrum and waterfall update, and scene SC-2
shows three occupied channels. Ctrl-C stops both services. This is a **Mock HAL
preview with a VL-1 ceiling**; it does not validate the RTL-SDR or Raspberry Pi.
See [RUN.md](methodology/test/T0_FM-RPI-RTL-mock/first_full_flow_2026-11-05/RUN.md)
for separate-terminal commands and smoke evidence. The archived G2 PASS was
recorded before the entry-point correction; that correction has separate smoke
evidence, not a new G2 verdict.

### Commands

| Command | Purpose |
|---------|---------|
| `codeanvil init [--mcp <name>]` | Prepare global DB/runtime, validate bundled UI and seed launcher settings; optional MCP installs |
| `codeanvil ui [--port 8765] [--no-browser]` | Serve the bundled graphical workspace locally |
| `codeanvil create` | Scaffold interactively: project name, folder name (default derived), confirm |
| `codeanvil create --name <label> [--folder <dir>] [-p <path>] [--mcp <name>]` | Scaffold non-interactively (agents, scripts, CI); folder defaults to the derived snake_case name |
| `codeanvil create <name> [-p <path>] [--mcp <name>]` | Legacy form: name is both project label and folder name (deprecated) |
| `codeanvil sync` | Register or move a cloned project (reads `.codeanvil/project.yaml`) |
| `codeanvil delete [PROJECT] [--remove-files] [-y]` | Remove a registration by exact name/full UUID, or the current registered project; keep files unless `--remove-files` is explicit |
| `codeanvil status [name]` | Latest report per stage/gate in flow order, with `delivered`, `stale`, `closed` markers and the latest backup per stage (from cwd, or by project name) |
| `codeanvil backup <S0\|S1\|S2\|G2>` | Copy the stage's current outputs to `.codeanvil/backups/<cycle>/<stage>_iter<N>/` with `MANIFEST.yaml` before a skill overwrites them; a no-op when nothing exists |
| `codeanvil list` | Registered projects (short UUID + local path) |
| `codeanvil now [--machine]` | System timestamp: human-readable or filename-safe |
| `codeanvil upgrade` | Reinstall codeanvil from the latest main branch (detects OS, uses uv) |

In a project workspace, **Terminal** runs installed local CLIs (Claude Code,
Codex and other configured terminal launchers) inside Linux/WSL. Leave
**Sandbox mode** unchecked for your normal configuration, or check it to reuse
the project-only settings of `codeanvil sandbox`. Click **Start terminal** to
launch; stop the process before changing its mode. Returning to the panel
reconnects to a running session. Native Windows/PowerShell-to-WSL launching is
not implemented in this first terminal version.

### Delete a project

`codeanvil delete "My Lab"` shows the selected name, full UUID, path and effect,
then asks for confirmation (default No). Without a name/UUID it selects the
registered project containing the current directory. Duplicate names require
the full UUID from the registry. Deletion never auto-registers a project.

The default removes only its local registration; its files remain and can be
registered again with `codeanvil sync`. Add `--remove-files` to permanently
remove the project folder and everything inside it. Noninteractive use requires
`--yes` (or `-y`):

```bash
codeanvil delete "My Lab" --yes
codeanvil delete FULL_UUID --remove-files --yes
```

Physical removal validates the root manifest and directory identity, and refuses
protected paths or folders containing other registered projects. If removal
fails, the registration stays and the error identifies the restored or recovery
folder. Some files may already have been removed; filesystem deletion and the
SQLite transaction cannot be rolled back together.

## MCP server integration (optional)

CodeAnvil can scaffold projects with MCP (Model Context Protocol) servers that give AI agents tool-calling capabilities beyond text. MCP servers are installed globally once, then wired into each project with per-agent configs.

### Marconi — LLM-driven GNU Radio

[Marconi](https://github.com/yoelbassin/gr-mcp) provides 19 MCP tools and 6 skills for RF/SDR work: spectrum survey, receiver building, simulation, transmit experiments, and GRC flowgraph export. Tested with Claude Code.

```bash
# Install Marconi (pinned clone, venv on gnuradio's Python, import probe)
codeanvil mcp add marconi
codeanvil mcp doctor marconi

# Scaffold a project with Marconi enabled
codeanvil create sdr-lab --mcp marconi -p ~/projects

# Verify MCP server connects
cd ~/projects/sdr-lab && claude mcp list
# marconi: ✔ Connected
```

**Requires**: GNU Radio 3.10+ installed via your system package manager (`pacman -S gnuradio`, `apt install gnuradio`, `dnf install gnuradio`, `brew install gnuradio`). `codeanvil mcp add` builds Marconi's venv on the Python gnuradio was built for and checks the import; if it fails, it prints the install command for your OS or `Run codeanvil mcp update marconi.`

**What you get in the scaffolded project**:

| What | Where |
|------|-------|
| 6 Marconi skills | `.agents/skills/marconi-*` (survey-spectrum, build-receiver, simulate-scene, debug-no-signal, tx-experiment, escape-hatch) |
| MCP server definition | `.mcp.json` (Claude Code), `.vscode/mcp.json`, `opencode.json`, `.codex/mcp.json` — all call `codeanvil mcp run marconi` |
| Agent-agnostic manifest | `.agents/mcp.yaml` |
| Server pre-approved | `.claude/settings.json` + `.claude/settings.local.json` (`enabledMcpjsonServers`) |

**Tested workflows** (Claude Code):

- Simulate a VHF scene → capture → survey spectrum (PSD, find_signals, spectrogram)
- Capture FM broadcast band from HackRF → convert int8→cf32 → analyze with Marconi
- Build NBFM receiver → validate → run → export `.grc` for GNU Radio Companion
- Real-time spectrum analyzer via escape-hatch (soapy_hackrf_source → qtgui sinks)
- DC spike correction for direct-conversion receivers (dc_blocker_cc via escape-hatch)

**Marconi v1.0 limitations**: simulation and file-based analysis only. No live hardware source blocks or real-time GUI sinks in the vocabulary — use the escape-hatch skill to write raw GRC flowgraphs or Python scripts for those. Hardware support (RTL-SDR, HackRF, USRP via gr-soapy/gr-uhd) is planned for Marconi v1.2.

## How it works

```
codeanvil create [<name> | --name <label> [--folder <dir>]] [-p <path>] [--mcp marconi]
       │
       ▼
  <path>/<folder>/                  (default: ./<name>/, folder derived from label)
       ├── AGENTS.md                 ← generated (canonical agent instructions)
       ├── CLAUDE.md → AGENTS.md     ← symlink
       ├── .codeanvil/               ← every methodology-owned artifact
       │    ├── GT/
       │    │    ├── README.md            ← instructions: write build_package.md here
       │    │    ├── build_package.md     ← you author; S0 reads it
       │    │    ├── StRS.md              ← written by S0 (IEEE 29148 §9.4)
       │    │    └── SyRS.md              ← written by S0 (IEEE 29148 §9.5)
       │    ├── design/                    ← S1 working design: SDD.md, dependency_graph.html (dark), dependency_graph_light.html
       │    ├── backups/                   ← written only by `codeanvil backup <stage>`
       │    ├── project.yaml              ← project identity (UUIDv7, no machine paths)
       │    └── report/                    ← per-cycle iterative reports (<cycle>/<id>.md)
       ├── .agents/
       │    ├── skills/             ← canonical skill store
       │    │    ├── G0_valid_req_and_GT/
       │    │    │    ├── SKILL.md           ← agent contract (paths rewritten)
       │    │    │    ├── templates/         ← locked IEEE 29148 reference templates
       │    │    │    │    ├── StRS.md
       │    │    │    │    └── SyRS.md
       │    │    │    ├── references/RULES.md
       │    │    │    └── scripts/g0_validate.py
       │    │    ├── S0_normalise_build_package/   ← own blueprints in templates/
       │    │    ├── S1_design_services/           ← references/ + assets/ (vis-network)
       │    │    ├── G1_design_review/
       │    │    ├── S2_implement_services/        ← references/ (project layout, loggers)
       │    │    ├── G2_adaptive_verification/     ← references/verified_prototype.md
       │    │    ├── RFD_request_for_deviation/
       │    │    └── marconi-*/SKILL.md     ← (if --mcp marconi) 6 RF/SDR skills
       │    └── mcp.yaml            ← (if --mcp) agent-agnostic MCP manifest
       ├── .mcp.json                ← (if --mcp) Claude Code MCP server config
       ├── .claude/skills  → ../.agents/skills
       ├── .opencode/skills → ../.agents/skills
       ├── .codex/skills   → ../.agents/skills
       └── .claude/agents/, .opencode/agents/, .codex/agents/   ← generated vsil-verifier subagent
```

`src/`, `verification/` and the root manifests are not scaffolded: S2 creates them when it builds the code.
The `vsil-verifier` subagent (one shared body, one file per runtime) is used only by G2 to run the verification commands in a fresh, read-only context; Copilot and Pi have no subagent file, so G2 asks for a fresh session there.

Skills live in `.agents/skills/` — the single source of truth. Agent runtime directories (`.claude/skills/`, `.opencode/skills/`, `.codex/skills/`) are symlinks, so every runtime discovers the same skills automatically.

GT reference templates are **locked** inside the skills that use them (`.agents/skills/S0_.../templates/` and `.agents/skills/G0_.../templates/`). Users write their Build Package in `.codeanvil/GT/`.

1. **Write your Build Package** — `.codeanvil/GT/build_package.md`. A hand-written StRS + SyRS pair is also accepted.
2. **S0 normalises** — an agent casts the Build Package into the locked StRS and SyRS blueprints, in one pass, inventing nothing.
3. **G0 validates structure** — a deterministic script checks that both GT documents follow the expected format and that the pair is cross-consistent (G0-X). Hard pass/fail, no LLM. Then a human answers Gate H: *Requirements complete, bounded, and verifiable?*
4. **S1 designs** — an agent writes the design and dependency graph. Design §0.5 defines one runnable project-root entry point, selected HAL, URL, visible result and shutdown.
5. **G1 reviews** — a human decides whether all implementation-critical design choices, including the entry point, are resolved (PASS, FEEDBACK or RFD).
6. **S2 implements** — an agent builds services under `src/`, the kit under `verification/`, the entry point and a VL-0 smoke test of the complete system. It records the `verification/run.sh vl0` and `vl1` commands.
7. **G2 verifies** — the `vsil-verifier` subagent re-runs those commands in a fresh, read-only context, including entry-point smoke evidence; a human answers PASS, FEEDBACK (module or design defect) or RFD. PASS writes the Verified Prototype with run instructions.
8. **RFD** — when a requirement is infeasible on the declared COTS platform, a decision document suspends the cycle until the Build Package author decides.

The S1 design lives in `.codeanvil/design/`: `SDD.md`, dark `dependency_graph.html`
and light `dependency_graph_light.html`. Both graphs share the same topology,
use the UI palette, and are working copies overwritten together on rework.
G2's Verified Prototype stays under `.codeanvil/report/<cycle>/G2_artifacts/`. Before S0, S1, S2 or G2 overwrites
its outputs, it runs `codeanvil backup <stage>`. Code under `src/` and `verification/` is not backed up; use git for it.
Projects scaffolded before v0.5.0 keep their old paths for the cycle they are in; there is no migration.
Reader-facing `reports/`, `validation_levels.md` and an optional `SRS.md` are not implemented.

## Definitions

| Acronym | Meaning |
|---------|---------|
| **GT**  | Ground Truth — the StRS + SyRS `.md` pair that defines the project contract (produced by S0 from the Build Package) |
| **T#**  | Test GT — real-world V-SIL input sets (`methodology/test/T<n>_<name>/`) used to validate the methodology end-to-end |
| **S#**  | Stage # — a step that produces an artifact (S0 normalise, S1 design) |
| **G#**  | Gate # — a verification checkpoint in the V-SIL pipeline |
| **RFD** | Request for Deviation — requirements infeasible on the declared COTS platform |
| **COTS** | Commercial Off-The-Shelf |
| **OOTB** | Out-Of-The-Box |
| **DAQ** | Data Acquisition (device/system; e.g. SDR) |
| **SDR** | Software Defined Radio |
| **SIL** | Safety Integrity Level |

## Project structure

```
codeanvil-gcpds/
├── src/codeanvil/           # Delivery tool (CLI + UI)
│   ├── __main__.py          # Entry point: python -m codeanvil
│   ├── CLI/
│   │   ├── __init__.py      # re-exports main (console-script entry point)
│   │   ├── main.py          # main() + subcommand dispatch
│   │   ├── parser.py        # argparse definitions
│   │   ├── prompts.py       # interactive create TUI (beaupy + Rich)
│   │   └── commands/        # one module per subcommand (create, init, list, ...)
│   ├── reports.py           # Report parser shared by `status` and `backup`
│   ├── project_delete.py    # Shared project removal for CLI and UI
│   ├── UI/ui.py             # Local FastAPI server and bundled React interface
│   ├── config/
│   │   ├── paths.py         # Canonical paths (~/.codeanvil-config/)
│   │   ├── identity.py      # UUIDv7 project IDs (stdlib-only)
│   │   ├── time.py          # Human + filename-safe timestamps
│   │   └── logger.py        # Colored cross-platform logger
│   ├── db/
│   │   ├── projects.py      # Project registry (register, sync, lookup)
│   │   ├── schema.py        # SQLite schema (projects only)
│   │   └── utils.py         # Connection management and health checks
│   └── init/
│       ├── check.py         # Pre-flight validation
│       ├── create.py        # Scaffold projects from templates
│       ├── sync.py          # Clone/move registration (codeanvil sync)
│       └── mcp.py           # MCP server install, skill copy, per-agent config gen
│
├── methodology/test/        # Test GT cases (V-SIL system inputs)
│   ├── T0_FM-RPI-RTL-mock/  # FM occupancy, RPi + RTL-SDR — Build Package + archived full-flow run
│   └── T1_HackRF-spectrum/  # HackRF One real-time spectrum — Build Package + seeded-fault oracle
│
├── templates/               # The methodology (the real product)
│   ├── GT/                  # Ground Truth document templates (IEEE 29148)
│   │   ├── StRS.md         # StRS template (§9.4 — merged stakeholder + HW + normativity)
│   │   ├── SyRS.md         # SyRS template (§9.5 — per-measurand system requirements)
│   │   ├── README.md
│   │   └── legacy/         # Old template versions (v1, v2, v3)
│   ├── backups/             # Retired skills (custody-chain, G1_start_design, G1_SRS.md)
│   ├── agents/vsil-verifier.md  # Shared G2 verifier body, rendered per runtime
│   ├── config.yaml           # Scaffold skill chain and subagent configuration
│   └── skills/              # Stage and gate skills (self-contained)
│       ├── S0_normalise_build_package/
│       ├── G0_valid_req_and_GT/      # + deterministic g0_validate.py and RULES.md
│       ├── S1_design_services/     # + references/ and assets/ (vis-network)
│       ├── G1_design_review/       # + references/G1_CHECKLIST.md
│       ├── S2_implement_services/  # + project layout and logger references
│       ├── G2_adaptive_verification/  # + Verified Prototype reference
│       └── RFD_request_for_deviation/
│
├── odd/tasks/               # Archived plans and task logs (grouped by milestone)
│
├── install.sh               # Linux/macOS installer (curl one-liner)
├── install.ps1              # Windows installer (PowerShell one-liner)
├── pyproject.toml            # PEP 621 packaging (hatch, templates bundled in wheel)
├── CLAUDE.md                # Development context for AI coding agents
└── AGENTS.md                # Agent architecture documentation
```

## Tech stack

- **Python packaging** — `uv` + hatch (templates bundled via `force-include`)
- **Installer** — `install.sh` (Linux/macOS) and `install.ps1` (Windows); both install `uv` if needed and inject PATH
- **UI** — PySide6 (planned)
- **Database** — SQLite (local, `~/.codeanvil-config/db/codeanvil.db`)
- **Agent runtime** — agent-agnostic (Claude, Codex, OpenCode, Pi, etc.)

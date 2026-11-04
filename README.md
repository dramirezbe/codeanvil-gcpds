# CodeAnvil

[![CI](https://github.com/dramirezbe/codeanvil-gcpds/actions/workflows/ci.yml/badge.svg)](https://github.com/dramirezbe/codeanvil-gcpds/actions/workflows/ci.yml)

Agent-agnostic project scaffolding, templates, and agent definitions for the **V-SIL methodology** (V-model at the SIL tier, made continuous). Develops, tests, and validates software on COTS hardware — informed by Ground Truth documents — through the V-SIL v3 flow `S0 → G0 → S1 → G1 → (S2 → G2)`: agent-driven stages, one deterministic gate (G0) and human review gates.

Works with any AI coding agent: Claude, Codex, OpenCode, Pi, or others.

> This methodology does not design hardware. It targets software running on Commercial Off-The-Shelf devices (not necessarily out-of-the-box), where the GT defines what constraints that hardware imposes.

## Install

**One-liner** (installs `uv` if needed, then `codeanvil` from GitHub):

```bash
curl -fsSL https://raw.githubusercontent.com/dramirezbe/codeanvil-gcpds/main/install.sh | bash
```

**Developer install** (editable, from a local clone):

```bash
git clone https://github.com/dramirezbe/codeanvil-gcpds.git
cd codeanvil-gcpds
uv pip install -e .
```

**Uninstall**:

```bash
curl -fsSL https://raw.githubusercontent.com/dramirezbe/codeanvil-gcpds/main/install.sh | bash -s uninstall
```

## Quick start

```bash
# Initialize workdir and database
codeanvil init

# Scaffold a new project interactively (project name, folder name, confirm)
codeanvil create

# ...or non-interactively, for agents/scripts/CI
codeanvil create --name "My SDR Lab"              # → ./my_sdr_lab/
codeanvil create --name "My SDR Lab" --folder sdr_lab

# Legacy form: the project name is also the folder name
codeanvil create myproject

# ...or in a specific path
codeanvil create myproject -p ~/projects

# Write your GT files in myproject/GT/
#   G0_StRS.md  — Stakeholder Requirements Specification (IEEE 29148 §9.4)
#   G0_SyRS.md  — System Requirements Specification (IEEE 29148 §9.5)
# Reference templates: .agents/skills/G0_valid_req_and_GT/templates/

# Validate the GT pair (deterministic, no AI)
cd myproject
python .agents/skills/G0_valid_req_and_GT/scripts/g0_validate.py GT/G0_StRS.md GT/G0_SyRS.md

# Check project status (reads .codeanvil/report/ from the current directory)
codeanvil status

# Cloned the project elsewhere? Register/move it in your local DB
codeanvil sync

# Filename-safe timestamp (report filenames, machine identifiers)
codeanvil now --machine
```

### Commands

| Command | Purpose |
|---------|---------|
| `codeanvil init [--mcp <name>]` | Create `~/.codeanvil-config/` (DB + optional MCP installs) |
| `codeanvil create` | Scaffold interactively: project name, folder name (default derived), confirm |
| `codeanvil create --name <label> [--folder <dir>] [-p <path>] [--mcp <name>]` | Scaffold non-interactively (agents, scripts, CI); folder defaults to the derived snake_case name |
| `codeanvil create <name> [-p <path>] [--mcp <name>]` | Legacy form: name is both project label and folder name (deprecated) |
| `codeanvil sync` | Register or move a cloned project (reads `.codeanvil/project.yaml`) |
| `codeanvil status [name]` | Latest report per stage/gate in flow order, with `delivered`, `stale` and `closed` markers (from cwd, or by project name) |
| `codeanvil list` | Registered projects (short UUID + local path) |
| `codeanvil now [--machine]` | System timestamp: human-readable or filename-safe |

## MCP server integration (optional)

CodeAnvil can scaffold projects with MCP (Model Context Protocol) servers that give AI agents tool-calling capabilities beyond text. MCP servers are installed globally once, then wired into each project with per-agent configs.

### Marconi — LLM-driven GNU Radio

[Marconi](https://github.com/yoelbassin/gr-mcp) provides 19 MCP tools and 6 skills for RF/SDR work: spectrum survey, receiver building, simulation, transmit experiments, and GRC flowgraph export. Tested with Claude Code.

```bash
# Install Marconi (clones repo, prewarms uv dependencies)
codeanvil init --mcp marconi

# Scaffold a project with Marconi enabled
codeanvil create sdr-lab --mcp marconi -p ~/projects

# Verify MCP server connects
cd ~/projects/sdr-lab && claude mcp list
# marconi: ✔ Connected
```

**Requires**: GNU Radio 3.10+ installed via your system package manager (`pacman -S gnuradio`, `apt install gnuradio-dev`, `dnf install gnuradio-devel`). The scaffold auto-detects the system gnuradio path and injects `PYTHONPATH` so Marconi's isolated uv venv can access it.

**What you get in the scaffolded project**:

| What | Where |
|------|-------|
| 6 Marconi skills | `.agents/skills/marconi-*` (survey-spectrum, build-receiver, simulate-scene, debug-no-signal, tx-experiment, escape-hatch) |
| MCP server definition | `.mcp.json` (Claude Code), `.vscode/mcp.json`, `.opencode/mcp.json`, `.codex/mcp.json` |
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
       ├── GT/
       │    ├── README.md            ← instructions: write build_package.md here
       │    ├── build_package.md     ← you author; S0 reads it
       │    ├── G0_StRS.md           ← written by S0 (IEEE 29148 §9.4)
       │    └── G0_SyRS.md           ← written by S0 (IEEE 29148 §9.5)
       ├── .codeanvil/               ← machine-generated methodology artifacts
       │    ├── project.yaml         ← project identity (UUIDv7, no machine paths)
       │    └── report/              ← per-cycle iterative reports (<cycle>/<id>.md)
       ├── .agents/
       │    ├── skills/             ← canonical skill store
       │    │    ├── G0_valid_req_and_GT/
       │    │    │    ├── SKILL.md           ← agent contract (paths rewritten)
       │    │    │    ├── templates/         ← locked IEEE 29148 reference templates
       │    │    │    │    ├── G0_StRS.md
       │    │    │    │    └── G0_SyRS.md
       │    │    │    ├── references/RULES.md
       │    │    │    └── scripts/g0_validate.py
       │    │    ├── S0_normalise_build_package/   ← own blueprints in templates/
       │    │    ├── S1_design_services/           ← references/ + assets/ (vis-network)
       │    │    ├── G1_design_review/
       │    │    ├── RFD_request_for_deviation/
       │    │    └── marconi-*/SKILL.md     ← (if --mcp marconi) 6 RF/SDR skills
       │    └── mcp.yaml            ← (if --mcp) agent-agnostic MCP manifest
       ├── .mcp.json                ← (if --mcp) Claude Code MCP server config
       ├── .claude/skills  → ../.agents/skills
       ├── .opencode/skills → ../.agents/skills
       └── .codex/skills   → ../.agents/skills
```

Skills live in `.agents/skills/` — the single source of truth. Agent runtime directories (`.claude/skills/`, `.opencode/skills/`, `.codex/skills/`) are symlinks, so every runtime discovers the same skills automatically.

GT reference templates are **locked** inside the skills that use them (`.agents/skills/S0_.../templates/` and `.agents/skills/G0_.../templates/`). Users write their Build Package in `GT/`.

1. **Write your Build Package** — `GT/build_package.md`. A hand-written StRS + SyRS pair is also accepted.
2. **S0 normalises** — an agent casts the Build Package into the locked StRS and SyRS blueprints, in one pass, inventing nothing.
3. **G0 validates structure** — a deterministic script checks that both GT documents follow the expected format and that the pair is cross-consistent (G0-X). Hard pass/fail, no LLM. Then a human answers Gate H: *Requirements complete, bounded, and verifiable?*
4. **S1 designs** — an agent writes the design of a system of layered services and its dependency graph.
5. **G1 reviews** — a human decides whether all implementation-critical design choices are resolved (PASS, FEEDBACK or RFD).
6. **RFD** — when a requirement is infeasible on the declared COTS platform, a decision document suspends the cycle until the Build Package author decides. S2 and G2 (implementation and verification) are planned.

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
│   ├── UI/ui.py             # PySide6 graphical interface (planned)
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
│   ├── T0_ANE-Lap2/        # ANE edge sensor (StRS + SyRS examples, Phase 2)
│   ├── T1_FM-monitoring/    # SDR-based FM compliance monitoring (LaTeX spec)
│   └── T2_IoT-Indoor/      # Indoor IoT radio environment (Hermes/GCPDS)
│
├── templates/               # The methodology (the real product)
│   ├── GT/                  # Ground Truth document templates (IEEE 29148)
│   │   ├── G0_StRS.md      # StRS template (§9.4 — merged stakeholder + HW + normativity)
│   │   ├── G0_SyRS.md      # SyRS template (§9.5 — per-measurand system requirements)
│   │   ├── README.md
│   │   └── legacy/         # Old template versions (v1, v2, v3)
│   ├── backups/             # Retired skills (custody-chain, G1_start_design, G1_SRS.md)
│   └── skills/              # Stage and gate skills (self-contained)
│       ├── S0_normalise_build_package/
│       ├── S1_design_services/     # + references/ and assets/ (vis-network)
│       ├── G1_design_review/       # + references/G1_CHECKLIST.md
│       ├── RFD_request_for_deviation/
│       ├── G0_valid_req_and_GT/
│       │   ├── SKILL.md            # Agent contract (agentskills.io format)
│       │   ├── references/RULES.md # Full Phase 1-4 rule tables
│       │   └── scripts/g0_validate.py  # Deterministic validator (stdlib only)
│
├── odd/tasks/               # Archived plans and task logs (date-prefixed)
│
├── install.sh               # curl one-liner installer (uv tool install from GitHub)
├── pyproject.toml            # PEP 621 packaging (hatch, templates bundled in wheel)
├── CLAUDE.md                # Development context for AI coding agents
└── AGENTS.md                # Agent architecture documentation
```

## Tech stack

- **Python packaging** — `uv` + hatch (templates bundled via `force-include`)
- **Installer** — `install.sh` (curl one-liner, installs `uv` if needed, shell detection for PATH injection)
- **UI** — PySide6 (planned)
- **Database** — SQLite (local, `~/.codeanvil-config/db/codeanvil.db`)
- **Agent runtime** — agent-agnostic (Claude, Codex, OpenCode, Pi, etc.)

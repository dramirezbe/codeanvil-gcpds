# CodeAnvil

Agent-agnostic project scaffolding, templates, and agent definitions for the **V-SIL methodology** (V-model at the SIL tier, made continuous). Develops, tests, and validates software on COTS hardware — informed by Ground Truth documents — through a pipeline of deterministic and agent-driven gates.

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

# Scaffold a new project (in the current directory)
codeanvil create myproject

# ...or in a specific path
codeanvil create myproject -p ~/projects

# Write your GT files in myproject/GT/
#   SRS.md  — System Requirements Specification
#   HCS.md  — Hardware Constraints Specification
# Reference templates: .agents/skills/G0_valid_req_and_GT/templates/

# Validate GT structure (deterministic, no AI)
cd myproject
python .agents/skills/G0_valid_req_and_GT/scripts/g0_validate.py GT/SRS.md GT/HCS.md

# Check project status
codeanvil status myproject
```

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
codeanvil create <name> [-p <path>] [--mcp marconi]
       │
       ▼
  <path>/<name>/                    (default: ./<name>/)
       ├── GT/
       │    └── README.md           ← instructions: write SRS.md, HCS.md here
       ├── .agents/
       │    ├── skills/             ← canonical skill store
       │    │    ├── G0_valid_req_and_GT/
       │    │    │    ├── SKILL.md           ← agent contract (paths rewritten)
       │    │    │    ├── templates/         ← locked IEEE 29148 reference templates
       │    │    │    │    ├── G0_SRS.md
       │    │    │    │    └── G0_HCS.md
       │    │    │    ├── references/RULES.md
       │    │    │    └── scripts/g0_validate.py
       │    │    ├── G1_start_design/
       │    │    │    └── SKILL.md
       │    │    └── marconi-*/SKILL.md     ← (if --mcp marconi) 6 RF/SDR skills
       │    └── mcp.yaml            ← (if --mcp) agent-agnostic MCP manifest
       ├── .mcp.json                ← (if --mcp) Claude Code MCP server config
       ├── .claude/skills  → ../.agents/skills
       ├── .opencode/skills → ../.agents/skills
       └── .codex/skills   → ../.agents/skills
```

Skills live in `.agents/skills/` — the single source of truth. Agent runtime directories (`.claude/skills/`, `.opencode/skills/`, `.codex/skills/`) are symlinks, so every runtime discovers the same skills automatically.

GT reference templates are **locked** inside each skill (e.g. `.agents/skills/G0_.../templates/`). Users write their own GT files in `GT/`.

1. **Write your GT** — author `SRS.md` and `HCS.md` in `GT/`, following the locked reference templates
2. **G0 validates structure** — a deterministic script checks that each GT file follows the expected format. Hard pass/fail, no LLM.
3. **G1+ gates run agents** — AI coding agents (any runtime) execute skills that drive design, implementation, and verification stages. Each gate reads the GT and prior gate outputs.

## Definitions

| Acronym | Meaning |
|---------|---------|
| **GT**  | Ground Truth — the 3 `.md` files that define the project contract |
| **T#**  | Test GT — real-world V-SIL input sets (`methodology/test/T<n>_<name>/`) used to validate the methodology end-to-end |
| **G#**  | Gate # — a verification checkpoint in the V-SIL pipeline |
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
│   ├── CLI/cli.py           # argparse CLI with subcommands
│   ├── UI/ui.py             # PySide6 graphical interface (planned)
│   ├── config/
│   │   ├── paths.py         # Canonical paths (~/.codeanvil/)
│   │   └── logger.py        # Colored cross-platform logger
│   ├── db/
│   │   ├── schema.py        # SQLite schema (projects, sessions, gate_results)
│   │   ├── sessions.py      # Session CRUD
│   │   └── utils.py         # Connection management and health checks
│   └── init/
│       ├── check.py         # Pre-flight validation
│       ├── create.py        # Scaffold projects from templates
│       └── mcp.py           # MCP server install, skill copy, per-agent config gen
│
├── methodology/test/        # Test GT cases (V-SIL system inputs)
│   ├── T0_ANE-Lap2/        # ANE edge sensor (SRS + HCS examples, Phase 2)
│   ├── T1_FM-monitoring/    # SDR-based FM compliance monitoring (LaTeX spec)
│   └── T2_IoT-Indoor/      # Indoor IoT radio environment (Hermes/GCPDS)
│
├── templates/               # The methodology (the real product)
│   ├── GT/                  # Ground Truth document templates (IEEE 29148)
│   │   ├── G0_SRS.md       # SRS template
│   │   ├── G0_HCS.md       # HCS template (§2.4 Design Constraints)
│   │   ├── README.md
│   │   └── legacy/         # Old template versions (v1, v2)
│   └── skills/              # Gate skills (deterministic + agent-driven)
│       ├── G0_valid_req_and_GT/
│       │   ├── SKILL.md            # Agent contract (agentskills.io format)
│       │   ├── references/RULES.md # Full Phase 1-4 rule tables
│       │   └── scripts/g0_validate.py  # Deterministic validator (stdlib only)
│       └── G1_start_design/
│           └── SKILL.md
│
├── plans/                   # Implementation plans
│   ├── g0_skill.md          # G0 deterministic validation script plan
│   └── scaffold_cli.md      # Scaffold CLI plan
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
- **Database** — SQLite (local, `~/.codeanvil/db/codeanvil.db`)
- **Agent runtime** — agent-agnostic (Claude, Codex, OpenCode, Pi, etc.)

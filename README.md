# CodeAnvil

Agent-agnostic project scaffolding, templates, and agent definitions for the **V-SIL methodology** (V-model at the SIL tier, made continuous). Develops, tests, and validates software on COTS hardware — informed by Ground Truth documents — through a pipeline of deterministic and agent-driven gates.

Works with any AI coding agent: Claude, Codex, OpenCode, Pi, or others.

> This methodology does not design hardware. It targets software running on Commercial Off-The-Shelf devices (not necessarily out-of-the-box), where the GT defines what constraints that hardware imposes.

## Quick start

```bash
# Install
uv pip install -e .

# Initialize workdir and database
codeanvil init

# Scaffold a new project (in the current directory)
codeanvil create myproject

# ...or in a specific path
codeanvil create myproject -p ~/projects

# Fill in the 3 GT files under myproject/GT/
#   requirements.md      — functional and non-functional requirements
#   hw_restrictions.md   — COTS hardware constraints (embedded, server, DAQ/SDR)
#   normativity.md       — applicable standards (ITU, ICNIRP, IEEE, ...)

# Check project status
codeanvil status myproject
```

## How it works

```
codeanvil create <name> [-p <path>]
       │
       ▼
  <path>/<name>/          (default: ./<name>/)
       ├── GT/
       │    ├── requirements.md
       │    ├── hw_restrictions.md
       │    └── normativity.md
       └── skills/
            ├── G0_valid_req_and_GT/   ← deterministic (script, no AI)
            ├── G1_start_design/       ← agent-driven
            └── ...
```

1. **Fill the GT** — write the 3 Ground Truth `.md` files (pre-processed, human-authored)
2. **G0 validates structure** — a deterministic script checks that each GT file follows the expected format. Hard pass/fail, no LLM.
3. **G1+ gates run agents** — AI coding agents (any runtime) execute skills that drive design, implementation, and verification stages. Each gate reads the GT and prior gate outputs.

## Definitions

| Acronym | Meaning |
|---------|---------|
| **GT**  | Ground Truth — the 3 `.md` files that define the project contract |
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
│       └── create.py        # Scaffold projects from templates
│
├── templates/               # The methodology (the real product)
│   ├── GT/                  # Ground Truth document templates
│   │   ├── placeholder_requirements.md
│   │   ├── placeholder_hw_restrictions.md
│   │   └── placeholder_normativity.md
│   └── skills/              # Gate skills (deterministic + agent-driven)
│       ├── G0_valid_req_and_GT/
│       │   ├── SKILL.md
│       │   └── scripts/valid_structure.py
│       └── G1_start_design/
│           └── SKILL.md
│
├── CLAUDE.md                # Development context for AI coding agents
└── AGENTS.md                # Agent architecture documentation
```

## Tech stack

- **Python packaging** — `uv`
- **UI** — PySide6
- **Database** — SQLite (local, `~/.codeanvil/db/codeanvil.db`)
- **Agent runtime** — agent-agnostic (Claude, Codex, OpenCode, Pi, etc.)

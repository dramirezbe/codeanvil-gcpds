# CodeAnvil — Agent Architecture

## Context — This is the CodeAnvil source repo, not a user project

You are working on the **tool itself** — the CLI, scaffold logic, methodology templates,
and skill definitions. You are a **developer** of CodeAnvil, not a user running the
V-SIL methodology.

- `src/codeanvil/` = the delivery tool (Python package, CLI, DB, scaffold)
- `templates/` = the methodology (skills, GT templates, config)
- Skill paths here use **repo-root** form: `templates/skills/<name>/scripts/...`
- Changes here affect the tool and methodology — they do NOT run against any user's GT.

A **scaffolded user project** (produced by `codeanvil create`) is a different thing:
it has `.agents/skills/`, `GT/`, `.codeanvil/`, and no `src/` or `templates/`.
The user's AGENTS.md (generated from `templates/AGENTS/TEMPLATE_AGENT.md`) tells
agents they are in a user project. Do not confuse the two environments.

## Overview

CodeAnvil implements the V-SIL pipeline as a chain of gates — G0 is deterministic, G1+ are AI coding agents. The harness is **agent-agnostic**: it works with any coding agent runtime (Claude, Codex, OpenCode, Pi, etc.). `src/` scaffolds and tracks state.

**Scope**: software development, testing, and validation on COTS hardware (not necessarily OOTB). Does not design hardware — assumes commercial off-the-shelf devices, validates software against GT constraints.

```
curl | bash ───────► install.sh (uv + codeanvil from GitHub, shell PATH injection)
codeanvil init ────► ~/.codeanvil-config/ (config + SQLite DB only)
codeanvil create ──► scaffold project anywhere
                       ├─ AGENTS.md            (generated, canonical instructions)
                       ├─ CLAUDE.md → AGENTS.md (symlink)
                       ├─ .agents/skills/      (canonical skill store)
                       ├─ .claude/skills → ../.agents/skills  (symlink)
                       ├─ .opencode/skills → ../.agents/skills
                       ├─ .codex/skills → ../.agents/skills
                       ├─ GT/README.md         (user writes G0_SRS.md, G0_HCS.md here)
                       ├─ .codeanvil/          (project.yaml + custody/ + report/)
                       └─ DB registration (idempotent)
codeanvil sync ─────► register/move a cloned project in the local DB
                       (reads the project's .codeanvil/project.yaml — no re-scaffold)

the harness (agent runtime) reads the scaffolded AGENTS.md and drives the gates:
                       │
                       ├─ G0 (deterministic — no agent)
                       │    ├─ reads: 3 GT .md files
                       │    ├─ script: g0_validate.py
                       │    ├─ checks: required sections, format, fields
                       │    └─ output: pass/fail (hard gate)
                       │
                       ├─ custody-chain (cross-cutting — after G0 pass)
                       │    ├─ seals GT: source_snapshot.py (SHA-256 + manifest)
                       │    ├─ records: custody_ledger.py (HMAC-signed, hash-chained)
                       │    └─ output: PASS/FAIL (tamper detection from here on)
                       │
                       ├─ G1 Agent (start design)
                       │    ├─ reads: validated GT + G0 report
                       │    ├─ skill: SKILL.md
                       │    └─ output: design artifacts
                       │
                       ├─ G2 Agent (...)
                       └─ ...
```

## The system — two sides

"The system" has two sides, and they must never be confused:

1. **Harness engineering (this repo — the wrapper).** CodeAnvil itself: `src/`
   (CLI + scaffold) and `templates/` (the methodology). This is where you *build
   the wrapper* — the gates, skills, GT templates, MCP wiring, and the generator
   that produces a user project. Work here changes the tool and the methodology.

2. **The user side (a ready harness).** What `codeanvil create` produces: a
   scaffolded project that is itself a complete, runnable harness — MCP servers
   wired in, skills under `.agents/skills/`, and **gate orchestration expressed
   in the generated `AGENTS.md`**. The agent runtime reads that `AGENTS.md` and
   drives the gates. Orchestration is harness engineering, not tool code — there
   is no `codeanvil run`.

## Test GT cases (V-SIL system inputs)

`methodology/test/T<n>_<name>/` — numbered test cases containing real-world project materials from which the 3 GT files are derived. They are the methodology's integration tests. See [`methodology/test/README.md`](methodology/test/README.md) for the full catalog and the **end-to-end manual test procedure** (clean install → scaffold → GT → G0 → custody-chain, with sandboxed Claude prompts).

| Test | Domain | GT-ready | Contents |
|------|--------|----------|----------|
| **T0_ANE-Lap2** | SDR spectrum monitoring (ANE edge sensor) | **Yes** | `just-edge/SRS.md` + `just-edge/HCS.md` — copy as `G0_SRS.md`/`G0_HCS.md` |
| **T1_FM-monitoring** | SDR-based FM broadcast compliance monitoring | No (raw) | LaTeX specification (RAG-informed from FCC Part 73, ANE Res. 105, ITU-R BS.412/450/SM.2152, ISO/IEC 17025) |
| **T2_IoT-Indoor** | Indoor IoT radio environment mapping, 2.4 GHz ISM (GCPDS) | No (raw) | Hermes proposal, radio environment mapping literature, variable adaptation design doc |

## Gate details

### G0 — Validate GT Structure (deterministic, no agent)

Pure Python script. No LLM, no AI agent — just `g0_validate.py`.

- **Purpose**: hard gate ensuring each GT `.md` file has the required structure before any agent gate runs.
- **Script**: `templates/skills/G0_valid_req_and_GT/scripts/g0_validate.py` (repo), `.agents/skills/G0_valid_req_and_GT/scripts/g0_validate.py` (scaffolded project)
- **Spec**: `SKILL.md` documents the expected structure; `references/RULES.md` holds the full rule tables.
- **GT reference templates**: locked inside the skill at `.agents/skills/G0_valid_req_and_GT/templates/` (G0_SRS.md, G0_HCS.md)
- **Inputs** (3 pre-processed `.md` files, human-authored):
  1. **Requirements** — functional and non-functional requirements
  2. **HW Restrictions** — COTS hardware constraints (embedded, server, DAQ/SDR)
  3. **Normativity** — applicable standards (ITU, ICNIRP, IEEE, etc.)
- **Output**: pass/fail with exact listing of missing/malformed sections.
- **Property**: deterministic — same input, same result. No interpretation.

### Custody Chain — Data Provenance & Integrity (cross-cutting, after G0)

Not a numbered gate — runs alongside any gate to prove GT immutability and track audit document custody.

- **Purpose**: seal GT files after G0 passes so any later modification is detected; record chain of custody for every generated audit document.
- **Skill**: `templates/skills/custody-chain/SKILL.md`
- **Scripts** (all stdlib-only, no network):
  - `source_snapshot.py` — seal and verify file integrity (SHA-256 + manifest digest)
  - `custody_ledger.py` — hash-chained, HMAC-signed append-only custody log
  - `control_registry.py` — validate audit controls are declarative and typed
  - `port_check.py` — verify runtime ports have bound implementations
- **Typical flow**: G0 PASS → seal GT (`snapshot --include 'GT/**'`) → record custody → before each later gate, verify GT unchanged
- **Output**: PASS/FAIL/INCOMPLETE provenance report with findings and evidence
- **Requires**: `PROVENANCE_HMAC_KEY` env var for signing ledger entries

### G1 — Start Design (agent-driven)

- **Purpose**: initiate design phase once GT is validated.
- **Skill**: `templates/skills/G1_start_design/SKILL.md`
- **Inputs**: validated GT + G0 pass report
- **Output**: initial design artifacts (architecture, interfaces, GT-derived constraints)

## Gate orchestration (harness-driven)

There is no `codeanvil run` command and no orchestrator in the tool. Gate
sequencing is **harness engineering**: the agent runtime (Claude, Codex,
OpenCode, Pi, ...) reads the scaffolded project's `AGENTS.md`, finds the lowest
incomplete gate, loads that gate's `SKILL.md`, and executes it.

- G0: the agent runs `g0_validate.py` directly (deterministic, no AI).
- custody-chain: after G0 passes, the agent seals GT and records custody.
- G1+: the agent follows the gate's `SKILL.md` against the validated GT.

State lives in the GT files and `.codeanvil/`, not in the tool. The `codeanvil`
CLI only scaffolds and registers projects; it never drives gates.

## Agent contract

Each gate agent (G1+), regardless of runtime:

1. Receives `SKILL.md` as instructions
2. Receives the project's GT documents as context
3. Executes validation, generation, or review per the skill
4. Returns structured output (pass/fail, findings, artifacts)

Agents are **stateless** and **runtime-agnostic** — all persistence is in the GT files and `.codeanvil/`. Any coding agent that reads markdown and executes scripts can run a gate. Re-runnable without side effects.

## MCP servers

MCP (Model Context Protocol) servers give AI agents tool-calling capabilities. They are installed globally at `~/.codeanvil-config/mcp/<name>/` and wired into projects during scaffold. Config is generated per agent runtime.

### Implemented: Marconi (GNU Radio)

[Marconi/gr-mcp](https://github.com/yoelbassin/gr-mcp) — 19 MCP tools + 6 skills for LLM-driven RF/SDR work.

**Install & scaffold flow**:
```
codeanvil init --mcp marconi       → clones to ~/.codeanvil-config/mcp/marconi/, prewarms uv deps
codeanvil create proj --mcp marconi → copies 6 marconi-* skills, generates MCP configs
```

**Agent-agnostic config generation** (`src/codeanvil/init/mcp.py`):
- `.mcp.json` — Claude Code (standard project MCP manifest)
- `.claude/settings.json` + `.claude/settings.local.json` — `enabledMcpjsonServers` (pre-approves the server)
- `.vscode/mcp.json` — VS Code / Copilot
- `.opencode/mcp.json` — OpenCode
- `.codex/mcp.json` — Codex
- `.agents/mcp.yaml` — agent-agnostic canonical manifest

**System package bridging**: GNU Radio is installed by the system package manager (not pip). `_detect_system_site_packages()` finds the system gnuradio and injects `PYTHONPATH` into all generated MCP configs so Marconi's uv venv can access it. Configured via `system_packages` in `templates/config.yaml`.

**Marconi v1.0 vocabulary** (17 blocks): tone_source, audio_tone_source, noise_source, file_source, head, add, multiply_const, freq_shift, freq_xlating_lowpass, quadrature_demod, rational_resampler_c/f, fm_deemphasis, nbfm_rx, nbfm_tx, file_sink, wav_sink. No hardware sources or GUI sinks — those use escape-hatch.

**Tested with Claude Code** (2026-10-20):
- Simulated VHF scene → capture → spectrum survey (PSD, find_signals, spectrogram)
- HackRF FM band capture → int8→cf32 conversion → Marconi analysis
- NBFM receiver build → validate → run → export `.grc`
- Real-time spectrum analyzer (soapy_hackrf_source → qtgui sinks) via escape-hatch
- DC blocker insertion for direct-conversion receiver artifact removal

### Planned

- **Project DB** — query project metadata (UUID registry)
- **GT access** — read/write GT documents with schema validation
- **CI bridge** — trigger and read SIL regression results

## Adding a new gate

1. Create `templates/skills/G<n>_<name>/SKILL.md`
2. Add validation scripts under `scripts/` if needed
3. Add GT reference templates under `templates/` if the gate validates document structure
4. Register the gate in the generated `AGENTS.md` gate sequence (the harness reads it)
5. Define the gate's artifact outputs in its `SKILL.md` (artifacts are project files, not DB rows)
6. Run `codeanvil create` — new skills are automatically copied and path-rewritten

## Scaffolded project structure

After `codeanvil create myproj`, the project has this layout:

```
myproj/
├── AGENTS.md                        ← generated (canonical agent instructions)
├── CLAUDE.md → AGENTS.md            ← symlink
├── GT/
│   ├── README.md                    ← write G0_SRS.md, G0_HCS.md here
│   ├── G0_SRS.md                    ← user-authored SRS (IEEE 29148)
│   └── G0_HCS.md                    ← user-authored HCS (design constraints)
├── .codeanvil/                      ← machine-generated methodology artifacts
│   ├── project.yaml                 ← project identity (UUIDv7, name, GT pointers)
│   ├── custody/                     ← custody-chain artifacts
│   │   ├── snapshot.json            ← sealed GT digests (after G0 pass)
│   │   └── custody.jsonl            ← append-only chain-of-custody ledger
│   └── report/                      ← timestamped gate reports (<gate>_<ts>.md)
├── .agents/
│   ├── skills/                      ← canonical skill store
│   │   ├── G0_valid_req_and_GT/
│   │   │   ├── SKILL.md             ← paths rewritten to project-relative
│   │   │   ├── templates/           ← locked IEEE 29148 reference templates
│   │   │   │   ├── G0_SRS.md
│   │   │   │   └── G0_HCS.md
│   │   │   ├── references/RULES.md  ← paths rewritten
│   │   │   └── scripts/g0_validate.py
│   │   ├── custody-chain/
│   │   │   ├── SKILL.md             ← cross-cutting provenance skill
│   │   │   ├── references/schemas.md
│   │   │   ├── assets/controls.example.json
│   │   │   └── scripts/             ← source_snapshot, custody_ledger, etc.
│   │   ├── G1_start_design/
│   │   │   └── SKILL.md
│   │   └── marconi-*/               ← (if --mcp marconi) 6 RF/SDR skills
│   │       └── SKILL.md
│   └── mcp.yaml                     ← (if --mcp) agent-agnostic MCP manifest
├── .mcp.json                        ← (if --mcp) Claude Code MCP server config
├── .claude/
│   ├── skills  → ../.agents/skills
│   ├── settings.json                ← (if --mcp) enabledMcpjsonServers
│   └── settings.local.json          ← (if --mcp) enabledMcpjsonServers
├── .vscode/mcp.json                 ← (if --mcp) VS Code / Copilot MCP config
├── .opencode/
│   ├── skills → ../.agents/skills
│   └── mcp.json                     ← (if --mcp) OpenCode MCP config
├── .codex/
│   ├── skills → ../.agents/skills
│   └── mcp.json                     ← (if --mcp) Codex MCP config
├── .github/skills  → ../.agents/skills
└── .github/copilot-instructions.md  ← pointer to AGENTS.md
```

Agent runtimes discover skills via their own symlinked directory. All point to the same `.agents/skills/`.

## Packaging and distribution

- **`pyproject.toml`** — PEP 621, hatch backend. Console script: `codeanvil = codeanvil.CLI.cli:main`. Templates bundled in wheel via `force-include`.
- **`install.sh`** — curl one-liner installer. Checks Python 3.10+, installs `uv` if missing, runs `uv tool install` from GitHub. Detects shell (bash/zsh/fish via `$SHELL`), injects `~/.local/bin` PATH with sentinel comments (`# >>> codeanvil >>>` / `# <<< codeanvil <<<`). Supports `bash install.sh uninstall`.
- **Template resolution** — `_find_templates_dir()` in `init/create.py`: editable installs use the source tree (`templates/`), wheel installs use `importlib.resources` (`codeanvil/templates/`).

## Versioning

Version follows SemVer (`X.Y.Z`). The single source of truth is `pyproject.toml`;
`codeanvil --version` reads it from package metadata at runtime.

| Bump | When | Examples |
|------|------|----------|
| **Z** (patch) | Single feature, refactor, important fix | new flag, bug fix, doc restructure |
| **Y** (minor) | Large feature or 25+ accumulated Z bumps | new gate, new MCP server, sync command |
| **X** (major) | Full code refactor or 50+ accumulated features | schema break, CLI redesign |

After merging to `main`, if the change warrants a bump per this table:

```bash
git tag -a v0.Y.Z -m "vX.Y.Z: short description"
git push origin v0.Y.Z
```

The tag push triggers the release workflow (`.github/workflows/release.yml`)
which creates a GitHub Release with a changelog. CI runs on every push and PR
(`.github/workflows/ci.yml`).

## Principles

- **GT is pre-processed input**: 3 human-authored `.md` files, not raw PDFs.
- **G0 is deterministic**: no AI, no interpretation. Valid or not.
- **Gates are sequential**: G(n+1) requires G(n) pass.
- **Skills are the methodology**: not in `SKILL.md` (or G0 script) → not in V-SIL.
- **GT is the contract**: agents validate against GT, never assumptions.
- **Agents are stateless**: re-runnable, same GT → same result.
- **`src/` serves `templates/`**: the tool delivers the methodology, not the other way around.

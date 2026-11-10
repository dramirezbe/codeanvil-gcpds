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
it has `.agents/skills/`, `.codeanvil/` (GT, design, backups and reports), and no `templates/`;
it has no `src/` until S2 writes the delivered code there. The user's AGENTS.md (generated from
`templates/AGENTS/TEMPLATE_AGENT.md`) never mentions this repository: it names only the
`codeanvil` CLI, the skills and `.codeanvil/`. Do not confuse the two environments.

## Where to start (v0.6.0)

| Need | Source of truth |
|------|-----------------|
| Change a stage, gate or artifact contract | The matching `templates/skills/<stage>/SKILL.md` and its `references/`; register scaffold changes in `templates/config.yaml` |
| Understand the first complete V-SIL v3 run | [`methodology/test/T0_FM-RPI-RTL-mock/FIRST_FULL_FLOW_SNAPSHOT.md`](methodology/test/T0_FM-RPI-RTL-mock/FIRST_FULL_FLOW_SNAPSHOT.md) and [`first_full_flow_2026-11-05/`](methodology/test/T0_FM-RPI-RTL-mock/first_full_flow_2026-11-05/) |
| Run the archived Mock HAL prototype | [`first_full_flow_2026-11-05/RUN.md`](methodology/test/T0_FM-RPI-RTL-mock/first_full_flow_2026-11-05/RUN.md) (`uv sync --frozen --no-dev`, then `./run-demo SC-2`) |
| Review findings and pending proposals | [`S1_G1_review_holdout_2026-11-05.md`](methodology/test/T0_FM-RPI-RTL-mock/S1_G1_review_holdout_2026-11-05.md) |
| See release and completed work | [`v0.7.0`](https://github.com/dramirezbe/codeanvil-gcpds/releases/tag/v0.7.0) and [`2026-11-06_1521_global_runtime_and_mcp_manager.md`](odd/tasks/global-runtime-mcp/2026-11-06_1521_global_runtime_and_mcp_manager.md) |

The T0_FM-RPI-RTL-mock snapshot completed S0 → G2 with a G2 design-defect feedback loop through
S1, G1 and S2. Its original G2 PASS predates the later runnable-entry-point
correction; `RUN.md` records that correction's separate smoke evidence. Do not
present it as a new G2 verdict. The holdout is an observation log; the refactor plan
[`2026-11-06_1410_t3_holdout_refactor.md`](odd/tasks/t3-holdout-refactor/2026-11-06_1410_t3_holdout_refactor.md)
implements its document renames, telemetry collector and pause policy, while the
VL-2 machine interface remains a proposal.

## Overview

CodeAnvil implements the V-SIL v3 flow `S0 → G0 → S1 → G1 → S2 → G2` as a chain of stages and gates, with RFD raisable from any stage. G0 is the only deterministic gate; Gate H, G1 and G2 are human verdicts, and the stages are run by AI coding agents. The harness is **agent-agnostic**: it works with any coding agent runtime (Claude, Codex, OpenCode, Pi, etc.) on **Linux, macOS and Windows**. `src/` scaffolds and tracks state.

**Scope**: software development, testing, and validation on COTS hardware (not necessarily OOTB). Does not design hardware — assumes commercial off-the-shelf devices, validates software against GT constraints.

```
curl | bash ───────► install.sh (Linux/macOS) or irm | iex ► install.ps1 (Windows)
codeanvil init ────► ~/.codeanvil-config/ (config + SQLite DB only)
codeanvil create ──► scaffold project anywhere
                       ├─ AGENTS.md            (generated, canonical instructions)
                       ├─ CLAUDE.md → AGENTS.md (symlink)
                       ├─ .agents/skills/      (canonical skill store)
                       ├─ .claude/skills → ../.agents/skills  (symlink)
                       ├─ .opencode/skills → ../.agents/skills
                       ├─ .codex/skills → ../.agents/skills
                       ├─ .claude/agents/, .opencode/agents/, .codex/agents/  (vsil-verifier)
                       ├─ .codeanvil/          (GT/ + build_package, design/, backups/, project.yaml, report/)
                       └─ DB registration (idempotent)
codeanvil sync ─────► register/move a cloned project in the local DB
                       (reads the project's .codeanvil/project.yaml — no re-scaffold)

the harness (agent runtime) asks for a cycle, then loads skills; each skill
checks its predecessor's report before it runs:
                       │
                       ├─ S0 normalise (agent) ── Build Package → StRS + SyRS
                       ├─ G0 (deterministic script) + Gate H (human)
                       ├─ S1 design services (agent) ── design + dependency graph
                       ├─ G1 design review (human verdict, agent prepares)
                       ├─ S2 implement services (agent) ── code + verification kit + VL-1 tests
                       ├─ G2 adaptive verification (human verdict, vsil-verifier runs) ── Verified Prototype
                       └─ RFD (outside the chain — raised from S1, G1 or G2)
```

## The system — two sides

"The system" has two sides, and they must never be confused:

1. **Harness engineering (this repo — the wrapper).** CodeAnvil itself: `src/`
   (CLI + scaffold) and `templates/` (the methodology). This is where you *build
   the wrapper* — the gates, skills, GT templates, MCP wiring, and the generator
   that produces a user project. Work here changes the tool and the methodology.

2. **The user side (a ready harness).** What `codeanvil create` produces: a
   scaffolded project that is itself a complete, runnable harness — MCP servers
   wired in, skills under `.agents/skills/`, and the **gate chain encoded in the
   skills themselves**: each skill checks its predecessor's report before it
   runs. The generated `AGENTS.md` is a passive reference (cycle protocol, skill
   table, report format, folders, MCP), not an orchestrator. Orchestration is
   harness engineering, not tool code — there is no `codeanvil run`.

## Test GT cases (V-SIL system inputs)

`methodology/test/T<n>_<name>/` — numbered test cases containing real-world project materials from which the GT pair is derived. They are the methodology's integration tests. See [`methodology/test/README.md`](methodology/test/README.md) for the catalog and manual test procedure; T0_FM-RPI-RTL-mock contains the first archived full-flow run.

| Test | Domain | GT-ready | Contents |
|------|--------|----------|----------|
| **T0_FM-RPI-RTL-mock** | FM occupancy, Raspberry Pi + RTL-SDR, mock-only | Build Package | Archived S0 → G2 run, copied project, runnable preview and review holdout |
| **T1_HackRF-spectrum** | Real-time spectrum + live HackRF One parameter control, x86_64 PC | Build Package | Build Package plus `SEEDED_FAULTS.md`, the oracle for the triage/draft acid test |

## Gate details

### G0 — Validate GT Structure (deterministic, no agent)

Pure Python script. No LLM, no AI agent — just `g0_validate.py`.

- **Purpose**: hard gate ensuring the GT pair (StRS + SyRS) has the required structure before any agent gate runs.
- **Script**: `templates/skills/G0_valid_req_and_GT/scripts/g0_validate.py` (repo), `.agents/skills/G0_valid_req_and_GT/scripts/g0_validate.py` (scaffolded project)
- **Spec**: `SKILL.md` documents the expected structure; `references/RULES.md` holds the full rule tables.
- **GT reference templates**: locked inside the skill at `.agents/skills/G0_valid_req_and_GT/templates/` (StRS.md, SyRS.md)
- **Inputs** (the Ground Truth **pair**, human-authored, IEEE 29148:2018 family):
  1. **StRS** (`.codeanvil/GT/StRS.md`, §9.4) — stakeholder requirements (`STK-`), COTS hardware constraints (`HWC-`), normative obligations (`NRM-` with inline compliance traceability)
  2. **SyRS** (`.codeanvil/GT/SyRS.md`, §9.5) — per-measurand system requirements (`SYS-`) tracing to StRS block IDs
- **G0-X**: cross-document consistency — STK coverage, trace resolvability, shared-ID namespace, normative citations.
- **Output**: per-document reports + G0-X report + gate report; pass/fail with exact listing of missing/malformed sections.
- **Property**: deterministic — same input, same result. No interpretation.

### S0 — Normalise the Build Package (agent, one pass)

- **Skill**: `templates/skills/S0_normalise_build_package/SKILL.md`; its locked blueprints are copied into `templates/` inside the skill on scaffold.
- **Input**: `.codeanvil/GT/build_package.md`. **Output**: `.codeanvil/GT/StRS.md`, `.codeanvil/GT/SyRS.md` and `S0.md` (inventory, missing list, trace).
- **Property**: normalises only; invents nothing. A hand-written pair is accepted as a no-op iteration.

### S1 — Design of layered services (agent)

- **Skill**: `templates/skills/S1_design_services/SKILL.md`, with the design template and graph template in `references/` and vis-network in `assets/`.
- **Output**: `.codeanvil/design/SDD.md` and `.codeanvil/design/dependency_graph.html` (one spider per service). `S1.md` is the only state.
- **Runnable contract**: design §0.5 names one project-root command, the services and runtime HAL it starts, URL, visible result and clean shutdown. G1 checks this in G1.15.

### G1 — Human design review

- **Skill**: `templates/skills/G1_design_review/SKILL.md` and `references/G1_CHECKLIST.md`. No script: the agent fills the checklist and recommends; the human answers PASS, FEEDBACK or RFD.

### S2 — Implement services (agent)

- **Skill**: `templates/skills/S2_implement_services/SKILL.md`, with `references/project_layout.md`, the locked `references/logger.py` and `references/logger.ts`, and the locked `scripts/telemetry_collector.py` that `run.sh` runs in place through `codeanvil python` (psutil from the methodology runtime).
- **Output**: the delivered code in `src/<service>/`, the verification kit in `verification/`, the root manifests, `S2.md` and `S2_artifacts/test_run.md` (the two `verification/run.sh vl0|vl1` commands and `Possible infeasibility`). S2 implements §0.5 and a VL-0 smoke test of the actual entry point, including the URL and observed result. Only S2 writes code; a design defect is a `Verdict: design defect` iteration routed to S1.

### G2 — Adaptive verification (human verdict)

- **Skill**: `templates/skills/G2_adaptive_verification/SKILL.md` and `references/verified_prototype.md`. G2 declares the levels, delegates the `test_run.md` commands to the `vsil-verifier` subagent, checks the entry-point smoke evidence, presents the results and records the human's PASS, FEEDBACK (`Verdict: module defect` → S2, `Verdict: design defect` → S1) or RFD. On PASS it writes `G2_artifacts/verified_prototype.md` with run instructions.

### `vsil-verifier` subagent

- **Body**: `templates/agents/vsil-verifier.md`, one shared body; `subagents` in `templates/config.yaml` lists one file per runtime. `codeanvil create` writes `.claude/agents/vsil-verifier.md`, `.opencode/agents/vsil-verifier.md` and `.codex/agents/vsil-verifier.toml`.
- **Contract**: fresh context, read-only, runs only the `test_run.md` commands, never writes a report and never asks the human; it returns a results table to G2. Runtimes without subagents (Copilot, Pi) run G2 in a fresh session.

### RFD — Request for Deviation (outside the chain)

- **Skill**: `templates/skills/RFD_request_for_deviation/SKILL.md`. A decision document for the Build Package author when requirements are infeasible on the declared COTS platform. A decided RFD re-enters at S0 in a new cycle.

The retired custody-chain and multi-hypothesis G1 skills are in `templates/backups/`.

## Gate chain (report-driven)

There is no `codeanvil run` command and no orchestrator in the tool — and none in
`AGENTS.md` either. The chain lives in the skills: on load, each skill checks its
predecessor's report (`S0`, `G0`, `S1`, `G1`, `S2` in `config.yaml`) and stops with the
predecessor's name when it is missing or its latest iteration is not
`HITL: PASS`.

- **Cycle:** the agent asks the user for a cycle name on every project open,
  normalizes it to a slug (`01_test_sdr_usrp_iot_signals`), records it in
  `.codeanvil/project.yaml`, and scopes reports to
  `.codeanvil/report/<cycle>/<id>.md`.
- **Iteration:** each stage or gate appends one `## Iteration <N>` section per run with a
  `HITL` verdict (`PASS` or `FEEDBACK`; there is no DENIED state).
- S0: no prerequisite; writes `S0.md` (`PASS` means "delivered").
- G0: requires `S0.md` latest `PASS`; the agent runs `g0_validate.py` directly
  (deterministic, no AI), then asks the human Gate H. Script errors force `FEEDBACK`.
- S1: requires `G0.md` latest `PASS`. G1: requires `S1.md` latest `PASS`; the human answers.
- S2: requires `G1.md` latest `PASS`; writes `S2.md` (`PASS` means "delivered").
- G2: requires `S2.md` latest `PASS`; the `vsil-verifier` subagent runs, the human answers.
- Every iteration of G0, S1, G1, S2 and G2 starts with `Based on: <predecessor> iteration <N>`, so
  `codeanvil status` can mark a report `stale` after its predecessor was reworked.
- After G2 `FEEDBACK` for a design defect, rework S1 in the same cycle, obtain a new G1 verdict, re-deliver S2 against that design and rerun G2. `codeanvil status` shows downstream reports as stale until re-delivered.

State lives in the GT files, the cycle reports, and `.codeanvil/`, not in the
tool. The `codeanvil` CLI only scaffolds and registers projects; it never drives
gates.

### Deferred proposals, not active paths

The T0_FM-RPI-RTL-mock holdout's `.codeanvil/` layout, `codeanvil backup`, bounded S1/G1/S2
rework, S2 pause schedule, module subagents and telemetry collector are
implemented on `main` (unreleased until v0.5.0). The plan and its Log are in
`odd/tasks/t3-holdout-refactor/2026-11-06_1410_t3_holdout_refactor.md`.

Still deferred, and **not** implemented: the VL-2 machine interface, reader-facing
`reports/` (`verified_prototype.md` stays in `report/<cycle>/G2_artifacts/`),
`validation_levels.md`, optional `GT/SRS.md` and an MCP telemetry facade. Change
the skills, scaffold, documentation and tests together before treating a
deferred proposal as implemented.

## Agent contract

Each stage agent (S0, S1), regardless of runtime:

1. Receives `SKILL.md` as instructions
2. Receives the project's GT documents as context
3. Executes validation, generation, or review per the skill
4. Returns structured output (pass/fail, findings, artifacts)

Agents are **stateless** and **runtime-agnostic** — all persistence is in the GT files and `.codeanvil/`. Any coding agent that reads markdown and executes scripts can run a gate. Re-runnable without side effects.

## MCP servers

MCP (Model Context Protocol) servers give AI agents tool-calling capabilities. Each is installed globally at `~/.codeanvil-config/mcp/<name>/` with its own venv, pinned to the `ref` in `templates/config.yaml`, and never shares the methodology runtime. Projects call every server through the launcher `codeanvil mcp run <name>`, so their configs hold no absolute path and survive a move or a clone.

### Implemented: Marconi (GNU Radio)

[Marconi/gr-mcp](https://github.com/yoelbassin/gr-mcp) — 19 MCP tools + 6 skills for LLM-driven RF/SDR work.

**Install & scaffold flow**:
```
codeanvil mcp add marconi          → clone, check out the pinned ref, venv, probe gnuradio (fails fast)
codeanvil mcp doctor marconi       → PATH tools, pin, venv, gnuradio import — each with its fix
codeanvil create proj --mcp marconi → copies 6 marconi-* skills, writes launcher configs
codeanvil mcp enable marconi       → (inside a project) wire it later, or rewrite an old absolute config
```

**Agent-agnostic config generation** (`src/codeanvil/init/mcp.py`):
- `.mcp.json` — Claude Code (standard project MCP manifest)
- `.claude/settings.json` + `.claude/settings.local.json` — `enabledMcpjsonServers` (pre-approves the server)
- `.vscode/mcp.json` — VS Code / Copilot
- `opencode.json` — OpenCode
- `.codex/mcp.json` — Codex
- `.agents/mcp.yaml` — agent-agnostic canonical manifest

**System packages**: GNU Radio is installed by the system package manager (not pip) and compiled for one system Python. `mcp add` / `mcp update` build Marconi's venv on that exact interpreter (`/usr/bin/python3.X`, never a version shim) with `--system-site-packages`. The probe is a real `from gnuradio import gr` in the venv, reported as ok, missing (with the OS-family install command from `system_packages` in `templates/config.yaml`), ABI mismatch (`Run codeanvil mcp update marconi.`) or broken; `mcp run` refuses to start on a failed probe with one stderr line.

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
4. Register the gate under `skills:` in `templates/config.yaml` with its
   `prerequisite` report id; the AGENTS.md generator renders the chain table
5. Define the gate's artifact outputs in its `SKILL.md` (artifacts are project files, not DB rows)
6. Run `codeanvil create` — new skills are automatically copied and path-rewritten

## Scaffolded project structure

After `codeanvil create myproj`, the project has this layout:

```
myproj/
├── AGENTS.md                        ← generated (canonical agent instructions)
├── CLAUDE.md → AGENTS.md            ← symlink
├── .codeanvil/                      ← every methodology-owned artifact
│   ├── GT/                          ← ground truth (human-authored, plus S0 output)
│   │   ├── README.md                ← write build_package.md here
│   │   ├── build_package.md         ← user-authored; S0 reads it
│   │   ├── StRS.md                  ← written by S0 (IEEE 29148 §9.4)
│   │   └── SyRS.md                  ← written by S0 (IEEE 29148 §9.5)
│   ├── design/                      ← S1 working copy: SDD.md, dependency_graph.html
│   ├── backups/                     ← written only by `codeanvil backup <stage>`
│   ├── custody/                     ← empty; left from the retired custody chain, unused
│   ├── project.yaml                 ← project identity (UUIDv7, name, GT pointers, cycle)
│   └── report/                      ← per-cycle iterative reports (<cycle>/<id>.md)
│       └── <cycle>/S2_artifacts/test_run.md, G2_artifacts/verified_prototype.md
├── .agents/
│   ├── skills/                      ← canonical skill store
│   │   ├── G0_valid_req_and_GT/
│   │   │   ├── SKILL.md             ← paths rewritten to project-relative
│   │   │   ├── templates/           ← locked IEEE 29148 blueprints
│   │   │   │   ├── StRS.md
│   │   │   │   └── SyRS.md
│   │   │   ├── references/RULES.md  ← paths rewritten
│   │   │   └── scripts/g0_validate.py
│   │   ├── S0_normalise_build_package/   ← templates/ (StRS.md, SyRS.md blueprints)
│   │   ├── S1_design_services/           ← references/ (SDD.md, dependency_graph_template.html) + assets/ (vis-network)
│   │   ├── G1_design_review/             ← references/G1_CHECKLIST.md
│   │   ├── S2_implement_services/        ← references/ (project_layout.md, logger.py/.ts, telemetry_collector.py)
│   │   ├── G2_adaptive_verification/     ← references/verified_prototype.md
│   │   ├── RFD_request_for_deviation/
│   │   └── marconi-*/               ← (if --mcp marconi) 6 RF/SDR skills
│   │       └── SKILL.md
│   └── mcp.yaml                     ← (if --mcp) agent-agnostic MCP manifest
├── .mcp.json                        ← (if --mcp) Claude Code MCP server config
├── .claude/
│   ├── skills  → ../.agents/skills
│   ├── agents/vsil-verifier.md      ← generated subagent
│   ├── settings.json                ← (if --mcp) enabledMcpjsonServers
│   └── settings.local.json          ← (if --mcp) enabledMcpjsonServers
├── .vscode/mcp.json                 ← (if --mcp) VS Code / Copilot MCP config
├── .opencode/
│   ├── skills → ../.agents/skills
│   ├── agents/vsil-verifier.md      ← generated subagent
│   └── mcp.json                     ← (if --mcp) OpenCode MCP config
├── .codex/
│   ├── skills → ../.agents/skills
│   ├── agents/vsil-verifier.toml    ← generated subagent
│   └── mcp.json                     ← (if --mcp) Codex MCP config
├── .github/skills  → ../.agents/skills
└── .github/copilot-instructions.md  ← pointer to AGENTS.md
```

Agent runtimes discover skills via their own symlinked directory. All point to the same `.agents/skills/`.
`src/`, `verification/` and the root manifests (`pyproject.toml`, `uv.lock`, `package.json`, `pnpm-workspace.yaml`, `pnpm-lock.yaml`) are not scaffolded: S2 creates them.

## Packaging and distribution

- **`pyproject.toml`** — PEP 621, hatch backend. Console script: `codeanvil = codeanvil.CLI.main:main`. Runtime deps: `pyyaml`, `beaupy` (interactive prompts). Templates bundled in wheel via `force-include`.
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

- **GT is pre-processed input**: the human-authored StRS + SyRS pair (`.md` files), not raw PDFs.
- **G0 is deterministic**: no AI, no interpretation. Valid or not.
- **Gates are sequential**: G(n+1) requires G(n) pass.
- **Skills are the methodology**: not in `SKILL.md` (or G0 script) → not in V-SIL.
- **GT is the contract**: agents validate against GT, never assumptions.
- **Agents are stateless**: re-runnable, same GT → same result.
- **`src/` serves `templates/`**: the tool delivers the methodology, not the other way around.

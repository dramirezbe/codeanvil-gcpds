# V-SIL v3 — Implemented Baseline

> **Purpose**: scope exactly what is built and working as of v0.8.7 (2026-11-17),
> so the V-SIL v4 refactor knows what it inherits and what it can change.
> Every item here has code, tests or archived evidence on `main`.

---

## 1. The pipeline: S0 → G0 → S1 → G1 → S2 → G2 + RFD

Seven skills, fully implemented in `templates/skills/`, scaffolded by
`codeanvil create` and copied to `.agents/skills/` in every project.

### S0 — Normalise Build Package

- **Input**: `.codeanvil/GT/build_package.md` (human-authored).
- **Output**: `.codeanvil/GT/StRS.md`, `.codeanvil/GT/SyRS.md`, `S0.md`.
- Casts the Build Package into the IEEE 29148:2018 pair in one pass.
  Invents nothing. A hand-written pair passes through as a no-op.
- Locked blueprints (StRS.md, SyRS.md) are embedded in the skill's
  `templates/` directory.

### G0 — Validate GT Structure (deterministic)

- Pure Python script: `scripts/g0_validate.py`. No AI.
- Validates StRS and SyRS structural compliance + G0-X cross-document
  consistency (STK coverage, trace resolvability, shared-ID namespace,
  normative citations).
- Full rule tables in `references/RULES.md`.
- Followed by **Gate H** (human question: "Requirements complete, bounded
  and verifiable?").
- **Failure triage** (v0.6.1): on Build Package faults, G0 reports which
  section is missing/malformed so S0 can rework.

### S1 — Design System

- Writes `.codeanvil/design/SDD.md` (layered subsystems, contracts with
  stubs, traceability, decisions, risks) and two dependency graphs:
  - `dependency_graph.html` (dark theme, vis-network vendored in `assets/`)
  - `dependency_graph_light.html` (light theme, same topology)
- Design §0.5: one runnable entry-point command.
- §1.6 `Target(s)` maps subsystems to local or named `project.yaml` targets.
- §1.7 supplies COTS-based telemetry envelope.
- **v0.8.3**: service → subsystem rename throughout the pipeline.
- **v0.8.4**: `phys` field in dependency graph + layout tuning.
- vis-network vendored in `assets/` — no network needed to view graphs.

### G1 — Design Review (human)

- Agent fills `references/G1_CHECKLIST.md` (G1.1–G1.15), including G1.15
  for the runnable entry point.
- Shows the graph path, the GT digest match, and recommends.
- Human answers PASS, FEEDBACK or RFD. No script.

### S2 — Implement Subsystems

- Builds `src/<subsystem>/`, `verification/` (Mock HAL, golden vectors,
  telemetry collector), root manifests, the §0.5 entry point and VL-0
  smoke test.
- Writes `S2.md` and `S2_artifacts/test_run.md` (the two
  `verification/run.sh vl0|vl1` commands + "Possible infeasibility").
- Locked references: `project_layout.md`, `logger.py`, `logger.ts`.
- Runs `codeanvil telemetry` on the execution target via the locked
  `run.sh` starter.
- **Pause Schedule** (v0.5.0): S2 preserves its configurable pause points
  and waits for explicit `continue` before remote deployment or local HW
  tests.
- **Continuation** (v0.8.6): accepts continuation aliases and offers
  concrete unblock options when stuck.
- **Draft mode** (v0.6.1): on Build Package errors, S0/G0/G1 can produce
  draft-mode output with explicit caveats.

### G2 — Adaptive Verification (human)

- Declares verification levels, delegates `test_run.md` commands to the
  `vsil-verifier` subagent.
- Checks entry-point smoke evidence.
- On PASS: writes `G2_artifacts/verified_prototype.md` with run
  instructions.
- On FEEDBACK: `Verdict: module defect` → S2 rework, `Verdict: design
  defect` → S1 rework.
- Measurement schema: `measurement.schema.json` + `validate_measurement.py`
  + `machine_evidence.md` reference — shared from G2 into S2 via
  `shared_skill_assets` in config.yaml.

### RFD — Request for Deviation

- Decision document when requirements are infeasible on COTS hardware.
- Suspends the cycle. A decided RFD re-enters at S0 in a new cycle.
- Raisable from any stage (S1, G1 or G2).

### `vsil-verifier` subagent

- Shared body: `templates/agents/vsil-verifier.md`.
- Generated per runtime: `.claude/agents/`, `.opencode/agents/`,
  `.codex/agents/` (TOML format for Codex).
- Fresh context, runs recorded tests, never edits product/test code.
- Tool-restricted: Read, Grep, Glob, Bash + HIL MCP probe/exec/fetch.
- Runtimes without subagents (Copilot, Pi) run G2 in a fresh session.

---

## 2. Gate chain mechanics

- **Report-driven**: each skill checks its predecessor's
  `.codeanvil/report/<cycle>/<id>.md`. No orchestrator.
- **Cycle-scoped**: reports live under `<cycle>/`, active cycle stored in
  `project.yaml`.
- **Iterative**: each run appends `## Iteration <N>` with
  `| HITL | PASS|FEEDBACK |`.
- **Based on**: every iteration of G0, S1, G1, S2, G2 starts with
  `Based on: <predecessor> iteration <N>`.
- **Stale detection**: `codeanvil status` marks downstream reports stale
  when a predecessor is reworked.
- **Stage vs Gate**: stages deliver (`PASS` = done), gates judge (human
  answers).
- **Superseded cycle**: RFD closes the old cycle, opens a new one.
- **Backup**: `codeanvil backup <stage>` saves files before overwrite
  (config-driven `backup_targets`).
- Chain order: `S0 → G0 → S1 → G1 → S2 → G2`, declared in
  `config.yaml:skills` with `prerequisite` keys.

---

## 3. CLI commands (27 subcommands)

| Command | What it does |
|---------|-------------|
| `codeanvil init` | Create `~/.codeanvil-config/`, DB, methodology runtime |
| `codeanvil create` | Interactive or `--name`/`-p` scaffold of a new project |
| `codeanvil list` | Registered projects (short UUID + path) |
| `codeanvil sync` | Register/update a cloned project in the local DB |
| `codeanvil delete` | Unregister project; `--remove-files` for physical removal |
| `codeanvil status` | Cycles, gates, stale marks, delivered stages |
| `codeanvil backup S0\|S1\|S2\|G2` | Copy stage files to `.codeanvil/backups/<cycle>/` |
| `codeanvil now` | Human-readable timestamp (`--machine` for filename-safe) |
| `codeanvil upgrade` | Reinstall from latest main + `runtime sync` |
| `codeanvil sandbox <agent>` | Launch agent with project-only settings |
| `codeanvil runtime sync\|add\|remove\|list\|path` | Global methodology runtime management |
| `codeanvil python <script>` | Run script on the methodology runtime (`-I`) |
| `codeanvil mcp add\|update\|remove\|list\|doctor\|run\|enable\|disable` | Full MCP server lifecycle |
| `codeanvil telemetry` | Sample host+process telemetry to JSONL |
| `codeanvil credential-setup` | Discover MACs, deploy keys for HIL targets |
| `codeanvil hil-enrollment` | Enroll hardware targets by MAC |
| `codeanvil ui` | Local web workspace (FastAPI + Vite frontend) |

### Sandbox agents implemented

| Agent | Strategy | Isolation |
|-------|----------|-----------|
| Claude Code | `native` | `--setting-sources project --strict-mcp-config` |
| Pi | `native` | `--no-extensions --no-mcp --no-skills ...` + re-enable bridge |
| OpenCode | `xdg_redirect` | Empty `XDG_CONFIG_HOME`, `--standalone` |
| Codex | `env_redirect` | `CODEX_HOME` override, `--no-daemon`, auth files only |

---

## 4. Project scaffold output

`codeanvil create` produces:

- `AGENTS.md` — generated from Jinja template (`templates/AGENTS/TEMPLATE_AGENT.md`)
- `CLAUDE.md` → symlink to `AGENTS.md`
- `.agents/skills/` — canonical skill store (7 skills, path-rewritten)
- `.claude/skills/`, `.github/skills/`, `.opencode/skills/` → symlinks
  to `.agents/skills/`
- `.claude/agents/`, `.opencode/agents/`, `.codex/agents/` — vsil-verifier
- `.github/copilot-instructions.md` — pointer file
- `.codeanvil/GT/` (build_package.md, README), `.codeanvil/design/`,
  `.codeanvil/backups/`, `.codeanvil/report/`, `.codeanvil/project.yaml`
- With `--mcp`: `.mcp.json`, `.claude/settings.json`,
  `.vscode/mcp.json`, `opencode.json`, `.codex/config.toml`,
  `.agents/mcp.yaml`, plus prefixed MCP skills
- Windows: symlinks fall back to directory junctions or file copies

Path rewriting: `config.yaml:path_replacements` rewrites repo-root to
project-root paths in `.md` files at scaffold time.

---

## 5. MCP servers

### Marconi (GNU Radio) — external, pinned

- 19 MCP tools + 6 skills for LLM-driven RF/SDR.
- Installed globally at `~/.codeanvil-config/mcp/marconi/`.
- Venv built on the system interpreter with `--system-site-packages`
  (gnuradio).
- Probe: real `from gnuradio import gr` import in the venv.
- `codeanvil mcp doctor marconi`: PATH tools, pin, venv, gnuradio.
- Projects call via `codeanvil mcp run marconi` (no absolute paths).
- Agent-agnostic config generation: `.mcp.json`, `.claude/settings.json`,
  `.vscode/mcp.json`, `opencode.json`, `.codex/config.toml`,
  `.agents/mcp.yaml`.

### vsil_hil_mcp — bundled, first-party

- Hardware-in-the-loop proxy: deploy, run, fetch evidence over SSH/rsync.
- Bundled in the wheel at `templates/mcp/vsil_hil_mcp/`.
- `credential-setup -u <admin> -i <host>`: discover physical MACs, reuse
  client keys across projects.
- Published Git deployment: clean, pushed candidate through the server.
- Database preservation during deployment.
- Tools: `probe_target`, `ssh_exec_cmd`, `ssh_exec_cmd_trusted`,
  `fetch_evidence`, `code_sync`, `init_codeanvil`.
- Workspaces scoped to the project UUID.
- Linux target execution implemented; Windows provisioning deferred.

---

## 6. Telemetry

- `codeanvil telemetry`: creates evidence files exclusively, flushes
  samples, optional `--fsync`.
- Sources: `src/codeanvil/telemetry/collector.py` (psutil) +
  `evidence.py`.
- Runs on the methodology runtime via `codeanvil python`.
- Output: JSONL in `verification/telemetry/`.
- Disk errors degrade the companion with a diagnostic.
- Missing/incomplete evidence prompts notice, diagnosis and a reasoned
  repeat/continue decision.

---

## 7. UI — Web workspace

- **Backend**: FastAPI + Uvicorn + Watchdog (file-system events).
- **Frontend**: Vite + React + TypeScript (bundled in the wheel; end users
  need no Node/pnpm).
- `codeanvil ui --port 8765` launches the workspace.

### Implemented views

- Project creation and addition.
- Cycle and report-iteration browsing.
- Shared stale/delivered state rendering.
- Safe Markdown rendering for reports.
- Design view (SDD.md) and verification view (test artifacts).
- Nested artifact browsing.
- **Workspace terminal**: runs installed local CLIs in a Linux/WSL PTY,
  with normal/sandbox checkbox.
- Project deletion dialog with safety confirmation.
- Backups view.

### UI infrastructure

- `codeanvil init` validates prebuilt assets/dependencies and seeds
  `~/.codeanvil-config/launchers.yaml`.
- Hatch build hook (`build_hook.py`) includes `frontend/dist` in the wheel.
- CI: pnpm install, test, build, then `uv build` (`.github/workflows/ci.yml`).

---

## 8. Installation and distribution

- **Linux/macOS**: `curl | bash` one-liner (`install.sh`). Installs `uv`,
  `uv tool install` from GitHub, injects PATH (bash/zsh/fish with sentinel
  comments).
- **Windows**: `irm | iex` one-liner (`install.ps1`). Same `uv tool install`
  flow, adds `%USERPROFILE%\.local\bin` to user PATH.
- **Developers**: `uv pip install -e .` from clone.
- **Uninstall**: `bash install.sh uninstall`.
- **Upgrade**: `codeanvil upgrade` (reinstall from main + runtime sync).
- Templates bundled via hatch `force-include` in `pyproject.toml`.
- Template resolution: `_find_templates_dir()` — editable install uses
  source tree, wheel uses `importlib.resources`.
- Python 3.10+ (CI matrix: 3.10, 3.12).
- SemVer versioning; single source of truth: `pyproject.toml`.
- Tag push triggers GitHub Release with changelog
  (`.github/workflows/release.yml`).

---

## 9. Database and project identity

- SQLite at `~/.codeanvil-config/codeanvil.db` (WAL mode).
- Schema: `projects` table (TEXT UUIDv7 id, name, path, created_at).
- `generate_uuidv7()`: stdlib-only RFC 9562, Python 3.10+ compatible.
- CRUD: `register_project()` (idempotent), `sync_project()`,
  `get_project_by_id()`, `get_project_by_name()`, `list_projects()`.
- Project deletion: `project_delete.py` — keeps files by default, physical
  removal requires matching manifest + registered identity.
- Legacy migration: `~/.codeanvil/` → `~/.codeanvil-config/` automatic.
- Pre-release schema migration: `has_legacy_schema()`/`recreate_if_legacy()`.

---

## 10. Ground Truth (GT) documents

- IEEE 29148:2018 family:
  - **StRS** (§9.4): `STK-` stakeholder requirements, `HWC-` hardware
    constraints, `NRM-` normative obligations.
  - **SyRS** (§9.5): `SYS-` system requirements per measurand, tracing to
    StRS blocks.
- Reference templates locked in `templates/GT/` (StRS.md, SyRS.md) and
  copied into G0 skill's `templates/` on scaffold.
- Build Package: human input at `.codeanvil/GT/build_package.md`, consumed
  by S0.
- GT README template scaffolded to `.codeanvil/GT/README.md`.
- **Not implemented**: optional `SRS.md` (third document).

---

## 11. Test suite

- **Tool tests** (`tests/`): 7901 LOC, 37 test files. Coverage:
  - CLI: create, list, sync, delete, status, backup, sandbox, prompts
  - DB: schema, identity, paths, time
  - MCP: manager, e2e
  - Reports: state parsing, stale detection
  - UI: app, workspace, terminal, workflows, delete, installation, user context
  - V-SIL v3: S0, S1, S2, G1, G2, subagent, AGENTS.md generation
  - HIL: credential setup, enrollment, measurements
  - Telemetry: collector
  - Codex compatibility
- **Skill tests** (`templates/tests/`): 1401 LOC. G0 script validation,
  S1 graph theme tests, reference template checks.
- CI: Python 3.10 + 3.12 matrix, UI build (pnpm test + build + uv build).

---

## 12. Test GT cases (methodology integration tests)

| Case | Domain | Status |
|------|--------|--------|
| **T0_FM-RPI-RTL-mock** | FM occupancy, RPi + RTL-SDR, mock-only | Archived S0 → G2 run, corrected entry point, review holdout |
| **T1_HackRF-spectrum** | Real-time spectrum + live HackRF control, x86_64 | Build Package + seeded faults; no archived run |
| **T2_RPi5-HackRF-web-spectrum** | Web spectrum + 7 RX controls, RPi5 + HackRF | Build Package + VL-2 protocol; hardware run not executed |

Synthetic UI fixtures: 5 portable snapshots (empty → G2) for UI testing at
`methodology/test/v0.7.0-example-artifacts/`.

---

## 13. Cross-platform support

- **Linux**: primary development platform. Full feature set.
- **macOS**: supported. Same install flow, shell detection (bash/zsh/fish).
- **Windows**: supported since v0.4.2. PowerShell installer, symlink
  fallback (directory junctions or file copies when Developer Mode off),
  `tzdata`/`pathsep` fixes.
- **WSL**: UI terminal runs in Linux PTY; sandbox checkbox available.

---

## 14. What is explicitly NOT implemented (deferred)

These are documented as deferred in AGENTS.md. V-SIL v4 can decide to
implement, redesign, or drop them.

| Item | Where documented |
|------|-----------------|
| Reader-facing `reports/` surface | AGENTS.md "Deferred proposals" |
| `validation_levels.md` | AGENTS.md "Deferred proposals" |
| Optional `GT/SRS.md` (third IEEE 29148 doc) | AGENTS.md "Deferred proposals" |
| MCP telemetry facade | AGENTS.md "Deferred proposals" |
| G0 v2 metrology-content rules | AGENTS.md "Deferred proposals" |
| Windows target provisioning for HIL | AGENTS.md HIL section |
| `guarded`/`locked` HIL policies | AGENTS.md HIL section |
| HIL release acceptance tests | AGENTS.md HIL section |
| Project DB MCP server | AGENTS.md "Planned" MCP |
| GT access MCP server | AGENTS.md "Planned" MCP |
| CI bridge MCP server | AGENTS.md "Planned" MCP |
| UI: auto-refresh, HW/telemetry surfaces, native packaging | UI README |

---

## 15. Version history (releases on `main`)

| Tag | Milestone |
|-----|-----------|
| v0.1.0 | Initial release: scaffold, G0, custody-chain, sync, CI/CD |
| v0.1.2 | IEEE 29148 GT family (StRS/SyRS/SRS) |
| v0.2.0 | G2 gate SOTA research and conceptual harness docs |
| v0.3.0 | V-SIL v3 skill flow S0–G0–S1–G1, RFD and status chain |
| v0.4.0 | V-SIL v3 full flow S0 → G2 |
| v0.4.1 | Python 3.10 CI compatibility |
| v0.4.2 | Windows support |
| v0.5.0 | T3 holdout refactor: backups, pause schedule, telemetry collector |
| v0.6.0 | Service rename, test cases T1/T2 |
| v0.6.1 | Failure triage + draft mode for S0/G0/G1 |
| v0.7.0 | HIL harness groundwork: telemetry + vsil_hil_mcp trusted MVP |
| v0.7.1–v0.7.5 | UI workspace: creation, browsing, terminal, deletion |
| v0.8.0 | Agent-operated HIL/PIL and reusable MAC access |
| v0.8.3 | service→subsystem rename + HIL operational fixes |
| v0.8.4 | S1 dependency graph: phys field + layout tuning |
| v0.8.5 | Native Codex project MCP, skills and custom agent compatibility |
| v0.8.6 | S2/G2 continuation, unblock options, outer harness guide |
| v0.8.7 | V-SIL v4 English and Spanish drafts |

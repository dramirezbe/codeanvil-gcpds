# V-SIL Test Cases (T#) and End-to-End Manual Test

## Catalog

| Case | Input | Execution scope |
|------|-------|-----------------|
| T0_FM-RPI-RTL-mock | [Build Package](T0_FM-RPI-RTL-mock/build_package.md) | Archived mock-only S0 → G2 flow. |
| T1_HackRF-spectrum | [Build Package](T1_HackRF-spectrum/build_package.md) | x86_64 spectrum/control; deliberate triage faults, hardware validation deferred. |
| T2_RPi5-HackRF-web-spectrum | [Guide and Build Package](T2_RPi5-HackRF-web-spectrum/README.md) | Small RPi5-hosted Vite dashboard and seven HackRF RX controls; explicit functional VL-2 protocol, not yet executed. |

## Synthetic UI fixtures — CodeAnvil 0.7.0

[`v0.7.0-example-artifacts/`](v0.7.0-example-artifacts/README.md) contains five
portable project snapshots: empty, through G0, through G1, through S2 and
through G2 with a minimal Python Mock HAL preview. Their progress and gate
decisions are explicitly synthetic; recorded G0 checks, test output and
telemetry are actual executions. Use the collection's README to verify hashes,
copy the examples and register them for future UI tests without running the
agent pipeline. This collection is separate from the T# methodology runs below.

---

## End-to-End Manual Test Procedure

This earlier procedure covers the clean install and Build Package → S0 → G0 →
S1 → G1 portion of the flow, using the FM Build Package under
`templates/no-tools-skills/v3/test-inputs/` as the test input. The test suite's own
StRS + SyRS pair under `templates/tests/fixtures/` can be copied straight in as a
hand-written GT pair (S0 passes it through as normalised input).
For the S2 → G2 continuation and a runnable result, use the T0_FM-RPI-RTL-mock archive below.

### Prerequisites

- Python 3.10+
- `curl` (Linux/macOS) or PowerShell (Windows)
- Agent CLI: `claude`, `pi`, or `opencode` (for sandboxed agent test)
- Internet access (for install from GitHub)

### 1. Install or upgrade

#### Remote (GitHub `main` — no clone needed)

**Linux / macOS:**

```bash
curl -fsSL https://raw.githubusercontent.com/dramirezbe/codeanvil-gcpds/main/install.sh | bash
source ~/.zshrc  # or ~/.bashrc
```

**Windows (PowerShell):**

```powershell
irm https://raw.githubusercontent.com/dramirezbe/codeanvil-gcpds/main/install.ps1 | iex
```

If codeanvil is already installed, both installers auto-detect it and run
`--force-reinstall` to pull the latest commit from `main`.

#### Upgrade (if codeanvil is already installed)

```bash
codeanvil upgrade
```

Cross-platform — detects the OS and reinstalls from the latest `main` via `uv`.

#### Local repository (development or testing unreleased changes)

From the root of this repository:

```bash
uv tool install --force-reinstall .
# or run the local installer:
bash install.sh          # Linux/macOS
# .\install.ps1          # Windows
```

Verify:
```bash
codeanvil --help                      # should show: init, create, list, sync, status, now, sandbox, upgrade
codeanvil sandbox --help              # shows supported agents: claude, codex, opencode, pi
codeanvil now                         # timestamp works
```

### 1b. Clean slate (optional — only for full reset testing)

**Linux / macOS:**

```bash
bash install.sh uninstall 2>/dev/null || true
rm -rf ~/.codeanvil-config
rm -rf ~/.codeanvil  # legacy state — would be auto-migrated back on init
hash -r  # refresh shell command cache
```

**Windows (PowerShell):**

```powershell
.\install.ps1 -Uninstall
Remove-Item -Recurse -Force "$env:USERPROFILE\.codeanvil-config" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "$env:USERPROFILE\.codeanvil" -ErrorAction SilentlyContinue
```

Verify (any OS):
```bash
command -v codeanvil && echo "FAIL: still installed" || echo "OK: clean"
```

Then install fresh with the appropriate command from step 1.

### 2. Initialize and create project

```bash
codeanvil init
codeanvil create smoke-test -p /tmp
```

Verify:
```bash
# Project structure
ls /tmp/smoke-test/AGENTS.md          # generated
ls /tmp/smoke-test/CLAUDE.md          # symlink → AGENTS.md
ls /tmp/smoke-test/.agents/skills/    # S0, G0, S1, G1, S2, G2, RFD

# .codeanvil/ machine-generated dir
ls /tmp/smoke-test/.codeanvil/project.yaml   # UUIDv7 identity manifest
ls /tmp/smoke-test/.codeanvil/report/        # empty — populated by gate reports

# GT dir — user-authored, inside .codeanvil/ with the other methodology artifacts
ls /tmp/smoke-test/.codeanvil/GT/README.md   # GT dir with instructions
ls /tmp/smoke-test/.codeanvil/design/        # empty — S1 writes SDD.md and dependency_graph.html here
ls /tmp/smoke-test/.codeanvil/backups/       # empty — written only by `codeanvil backup <stage>`

# Methodology runtime — `init` built it; skill scripts run on it via `codeanvil python`
codeanvil runtime list    # psutil  base  <version> / pyyaml  base  <version>
codeanvil runtime path    # ~/.codeanvil-config/runtime/.venv/bin/python
```

The runtime, the telemetry collector and the GNU Radio MCP server have their own probe:
[`runtime_mcp_probe.md`](runtime_mcp_probe.md). With Marconi, install it once with
`codeanvil mcp add marconi`, check it with `codeanvil mcp doctor marconi`, then
`codeanvil create smoke-test -p /tmp --mcp marconi`.

### 2b. Verify project identity and status

```bash
codeanvil list                        # shows [<short-uuid>] smoke-test — /tmp/smoke-test
cd /tmp/smoke-test
codeanvil status                      # project identity from manifest, no reports yet
codeanvil now                         # human-readable timestamp (configured timezone)
codeanvil now --machine               # filename-safe format (no colons or spaces)
```

Verify:
- `codeanvil list` shows the project with a UUIDv7 short prefix.
- `codeanvil status` prints project name, UUID, path, and "none yet" for reports.
- `codeanvil now` prints a timestamp with millisecond precision.
- `codeanvil now --machine` prints a filename-safe timestamp (e.g. `2026-10-22_09-15-30-123`).

### 2c. Verify sync flow (simulates cloning on another machine)

```bash
# Simulate a clone: copy project to new location
cp -r /tmp/smoke-test /tmp/smoke-test-clone

# Sync the "clone" — registers it with the local DB at its new path
cd /tmp/smoke-test-clone
codeanvil sync

# Verify
codeanvil list                        # shows BOTH entries — same UUID, different paths
codeanvil status                      # resolves from .codeanvil/project.yaml in cwd
```

Verify:
- `codeanvil sync` prints `Synced: smoke-test (<short-uuid>) → /tmp/smoke-test-clone [registered]` (or `[moved]` if the UUID already existed with a different path).
- `codeanvil list` shows the project registered at the new location.
- Cleanup: `rm -rf /tmp/smoke-test-clone`

### 3. Copy the Build Package into the project

```bash
# From the codeanvil repo:
cp templates/no-tools-skills/v3/test-inputs/build_package.md /tmp/smoke-test/.codeanvil/GT/build_package.md
```

Alternative (hand-written pair, S0 runs as a no-op): copy the test suite's fixture pair instead.

```bash
cp templates/tests/fixtures/StRS.md /tmp/smoke-test/.codeanvil/GT/StRS.md
cp templates/tests/fixtures/SyRS.md /tmp/smoke-test/.codeanvil/GT/SyRS.md
```

### 4. Enter sandboxed Claude session in the project

```bash
cd /tmp/smoke-test
codeanvil sandbox claude
```

This launches Claude Code with only project-local settings visible (see
[Two modes: sandbox vs. normal](#two-modes-sandbox-vs-normal) below).

### 4b. Enter sandboxed Pi session in the project (alternative)

```bash
cd /tmp/smoke-test
codeanvil sandbox pi
```

This launches Pi with all user extensions, MCP servers, skills, prompt
templates, and themes disabled, re-enabling only the `pi-claude-bridge`
extension (model access). The result is a clean session that reads only
the project's `AGENTS.md` without interference from global config.

### 4c. Enter sandboxed OpenCode session in the project (alternative)

```bash
cd /tmp/smoke-test
codeanvil sandbox opencode
```

This launches OpenCode in standalone mode with `XDG_CONFIG_HOME` redirected
to an isolated temporary directory. Global plugins, custom agent definitions,
and user prompt overrides are stripped while preserving stored credentials.
OpenCode reads `AGENTS.md` and project skills symlinked at `.opencode/skills/`.

### Two modes: sandbox vs. normal

- **Sandbox** (`codeanvil sandbox <agent>`) — the agent sees only the
  project: `AGENTS.md`, `.agents/skills/`, and the GT. Global skills,
  MCP servers, extensions, and memory are disabled. Use this to test the
  methodology on a clean agent, with no interference from your own config.
  Nothing persists outside the project — no state to revert.
- **Normal** (run `claude`, `pi`, `opencode`, or `codex` directly) — your
  full setup loads as usual: global skills, MCP servers, extensions,
  memory. Use this for day-to-day work on the project.

Internally, `codeanvil sandbox` applies each agent's native isolation strategy:

```bash
# what `codeanvil sandbox claude` runs:
claude --setting-sources "project"

# what `codeanvil sandbox pi` runs:
pi --no-extensions --no-mcp --no-skills --no-prompt-templates --no-themes \
   -e ~/.pi/agent/npm/node_modules/pi-claude-bridge/src/index.ts

# what `codeanvil sandbox opencode` runs (XDG_CONFIG_HOME redirected to empty tempdir):
opencode --standalone
```

The `--setting-sources "project"` flag loads only project-level settings
(CLAUDE.md → AGENTS.md) and ignores user/local settings, ensuring a clean
test of the scaffolded instructions without interference from global config.

*(Note: `--setting-sources ""` disables ALL settings including CLAUDE.md
autodiscovery — don't use it for methodology testing.)*

### 5. Test prompts (inside sandboxed Claude, Pi, or OpenCode)

Run these prompts in sequence inside the sandboxed session. After each,
verify the expected outcome before proceeding.

#### Prompt 1 — Context check

```
What project is this? What skills are available? What should you do first?
```

**Expected:** the agent runs `codeanvil status`, reads `AGENTS.md`, identifies a V-SIL
scaffolded project, lists S0 → G0 → S1 → G1 with their prerequisite chain and RFD with
`-`, and asks for a **cycle name** before any work. Answer `Smoke Test` → it writes
`cycle: 01_smoke_test` into `.codeanvil/project.yaml`.

#### Prompt 2 — Order is enforced

```
Run G1
```

**Expected:** `S1 must pass first. Run the S1 skill.` No report is written.

#### Prompt 3 — Run S0

```
Run S0
```

**Expected:** one pass, no questions. Writes `.codeanvil/GT/StRS.md`, `.codeanvil/GT/SyRS.md` and
`.codeanvil/report/<cycle>/S0.md` with `| HITL | PASS |`, the inventory and the missing
list. Returns `S0 complete. Run the G0 skill.`

#### Prompt 4 — Run G0 and answer Gate H

```
Run G0
```

**Expected:** runs `g0_validate.py`, shows exit `0`, the output and S0's missing list, then
asks *Requirements complete, bounded, and verifiable?* Answer `PASS` and a name → `G0.md`
records the answer, the date and `Decided by:`.

#### Prompt 5 — Run S1

```
Run S1
```

**Expected:** writes `.codeanvil/design/SDD.md` (GT digests in Meta) and
`.codeanvil/design/dependency_graph.html`, then `S1.md` with `| HITL | PASS |` naming the graph path.
On a rework of an existing design, S1 first runs `codeanvil backup S1` and the iteration cites the
printed `.codeanvil/backups/<cycle>/S1_iter<N>/` path (or `nothing to back up` on the first run).
Open the graph: spiders, one per service, with the manifest text and no network needed.

#### Prompt 6 — Run G1 (human review)

```
Run G1
```

**Expected:** the agent shows the graph path, the filled checklist (`open` findings first), the
digest match and a recommendation, then **waits**. Answer `PASS` and a name → `G1.md`
records it with `Based on: S1 iteration 1`. The agent says S2 is not available yet.

Expected `codeanvil status` afterwards:

```
Cycles:
  01_smoke_test (active)
    S0: delivered (iteration 1)
    G0: PASS (iteration 1)
    S1: delivered (iteration 1)
    G1: PASS (iteration 1)
```

#### Failure paths to try

| Case | How | Expected |
|------|-----|----------|
| G0 FAIL → S0 | Remove Part B from `build_package.md` before S0 | Placeholders, exit 1, `G0: FEEDBACK`; S0 re-run reports "needs Build Package content" |
| Gate H refused | Answer FEEDBACK with `STK-SPEC-002: ...` | Reason stored verbatim; S0 re-entry reads it |
| GT edited after S1 | Change one byte, run G1 | Digest mismatch shown to the human; nothing blocks |
| G1 FEEDBACK → S1 | Remove a stub recipe in the design | Finding marked `open`; S1 re-run reads the FEEDBACK |
| Rework routed from reports | Answer FEEDBACK at G1, run G1 again without S1 | `S1 must rework first. Run the S1 skill.`; no iteration written |
| Stale PASS | After G1 PASS, re-run S1, then `codeanvil status` | `G1: PASS (iteration 1) [stale: based on S1 iteration 1, S1 is at 2]` |
| Reports drive the chain | Delete `.codeanvil/design/dependency_graph.html`, run G1 | Prerequisite still passes; finding marked `advisory` |
| Graph differs from design | Remove a module from the graph's `DATA`, run G1 | Finding marked `open` |
| RFD closes the cycle | Answer RFD at G1, decide it, name a new cycle | Old cycle shows `(closed: superseded by <name>)`; G1 before the decision returns `Cycle suspended by RFD. Run the RFD skill.` |

### 5b. Full flow S0 → G2, `mock-only` (T0_FM-RPI-RTL-mock)

Scenario: SDR → Raspberry Pi DSP service (spectrum, waterfall, detection of the 10 FM channels
of a 2 MHz slice) and a browser UI, validation up to VL-1 with the Mock HAL and the labelled
synthetic scenes the Build Package fixes (B.2 signal model, B.3 scenes SC-1–SC-6, B.4 golden
vectors GV-1–GV-5), no real hardware. The ML spectral-localisation model
is future work only, so the design has no §1.5. Plan:
`odd/tasks/vsil-v3-full-flow/2026-11-05_E2E_full_flow_mock_only.md`.

```bash
ROOT="$(mktemp -d)"
codeanvil create --name "FM Occupancy Mock" -p "$ROOT"
cd "$ROOT"/fm_occupancy_mock
cp <repo>/methodology/test/T0_FM-RPI-RTL-mock/build_package.md .codeanvil/GT/build_package.md
codeanvil sandbox claude    # or opencode, codex; pi only for the fresh-session probe
```

| Step | Prompt | Expect |
|------|--------|--------|
| 1 | Run S0, then G0 | SyRS §4–§6 hold the "not applicable" line; GT pair passes `g0_validate.py`; human Gate H |
| 2 | Run S1 | `HAL mode: mock-only`; `Toolchain` per service (DSP and UI); §0.5 names a runnable system entry point; §1.3.4 with D2 paths, §1.6 Mock HAL following B.2 with SC-1–SC-6 and GV-1–GV-5 as its vectors, §1.7 filled; no §1.5; no `hw_dependency: true`; no label invented beyond B.3 |
| 3 | Run G1, answer PASS | No script runs; checklist with G1.11–G1.15 and the kit row (incl. `Toolchain`); G1.14 runs the `--version` checks and asks before installing; G1.15 checks the entry point; returns `G1 passed. Run the S2 skill.` |
| 4 | Run S2 | D2 tree: `src/fm_edge/` (Python, `__main__.py`) and `src/dashboard/` (TS), `pyproject.toml` + `uv.lock`, `package.json` + `pnpm-workspace.yaml` + `pnpm-lock.yaml`, `verification/` with `run.sh`, `golden/` (manifest lists SC-1–SC-6 and GV-1–GV-5 with the B.3 labels copied as expected output), `telemetry/`, `fm_edge/`, `dashboard/`; kit and base first, then modules, paths and VL-1 tests; `verification/run.sh vl0` green with telemetry and a system-entry-point smoke test; `test_run.md` has the two `run.sh` commands and the entry-point evidence; `grep -r codeanvil src/` is empty; edge logs show `[YYYY-MM-DD HH:MM:SS.mmm] LEVEL name.funcName message` in colour; `uv sync --frozen --no-dev && uv run fm_edge` starts without kit dependencies |
| 5 | Run G2, declare VL-1 for DSP and the edge → UI path | Runs delegated to `vsil-verifier` (Claude Code, OpenCode); source tree unchanged after them; only the `test_run.md` commands run; a VL-2 request is refused; `verified_prototype.md` written on PASS |
| 6 | `codeanvil status` | S0–S2 `delivered`, G0–G2 `PASS` |

Failure probes:

| Probe | How | Expect |
|-------|-----|--------|
| ML section in the design | Add a §1.5 to the design before S2 | `ML integration is future work. Remove design §1.5 for this round.`; no iteration |
| Design defect | Remove a contract field before S2 | `Verdict: design defect` iteration; S1 reworks |
| Module defect | Force a module bug before G2 | `Verdict: module defect`, routed to S2 |
| Missing VL-1 test | Delete one VL-1 test before G2 | `Verdict: module defect`; G2 writes no test |
| Rework routed from reports | Re-run G2 after that FEEDBACK without re-running S2 | `S2 must rework first. Run the S2 skill.` |
| Interrupted S2 | Interrupt S2 mid-module and re-run it | Finished modules kept |
| Runtime without subagents | Run G2 in Pi or Copilot | Fresh-session request; no runs |

Recommended, not required: run step 5 on the Raspberry Pi so the telemetry collector records
the real compute unit. Record each row's observation, with the agent runtime used, in the
feature document's Log; a failing step reopens the task of the skill that failed.

The first OpenCode result of this procedure, including its hidden scaffold files,
GT, reports, services and verification kit, is archived at
`T0_FM-RPI-RTL-mock/first_full_flow_2026-11-05/`. Its original state is commit
`2b760da`; the corrected runnable entry point and replay instructions are in
that directory's `RUN.md`. See `T0_FM-RPI-RTL-mock/FIRST_FULL_FLOW_SNAPSHOT.md` for the
copy exclusions and `T0_FM-RPI-RTL-mock/S1_G1_review_holdout_2026-11-05.md` for the
review.

### 6. Cleanup

```bash
rm -rf /tmp/smoke-test
# Optionally: bash install.sh uninstall
```

---

## Expected findings / feedback areas

After running the full flow, note:

- [ ] Did `codeanvil create` scaffold S0, G0, S1, G1, S2, G2 and RFD (and no custody-chain)?
- [ ] Did it write `vsil-verifier` to `.claude/agents/`, `.opencode/agents/` and `.codex/agents/`?
- [ ] Did the AGENTS.md skill table list the chain S0 → G0 → S1 → G1 with RFD as `-`?
- [ ] Did the agent ask for a cycle name on project open and normalize it (`01_smoke_test`)?
- [ ] Did `.codeanvil/` contain `project.yaml` (with `cycle:`) and an empty `report/`?
- [ ] Did each step write one iterative `<cycle>/<id>.md` report, and did G0 and G1 wait for
      the human's answer?
- [ ] Did S1 write the design and graph to `.codeanvil/design/` (`SDD.md`, `dependency_graph.html`)?
- [ ] On any rework, did S0, S1, S2 and G2 run `codeanvil backup <stage>` before overwriting, and did
      each iteration cite the backup path (or `nothing to back up`)?
- [ ] Did `codeanvil status` show stages as `delivered` and mark a reworked chain `stale`?
- [ ] Did `codeanvil sync` register a cloned project without re-scaffolding?
- [ ] Did G0 run with the correct project-relative path (`.agents/skills/...`)?
- [ ] Any path errors, missing files, or confusing agent behavior?

Record findings and report back to improve the methodology and tooling.

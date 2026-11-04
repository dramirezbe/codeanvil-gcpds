# V-SIL Test Cases (T#) and End-to-End Manual Test

## Test cases

Each `T<n>_<name>/` folder is a real-world GT instance used to validate the
methodology pipeline. They are the methodology's integration tests.

| T# | Domain | GT-ready | Contents |
|----|--------|----------|----------|
| **T0_ANE-Lap2** | SDR spectrum monitoring (ANE edge sensor) | **Yes** — `just-edge/StRS.md` + `just-edge/SyRS.md` are valid GT files | Also has `full-system/StRS_APPROVED.md` (broader scope, historical snapshot) |
| **T1_FM-monitoring** | SDR-based FM broadcast compliance | No — raw LaTeX spec, GT must be derived | `00_sdr_spectrum_sensor_design/` (RAG-informed from FCC/ANE/ITU) |
| **T2_IoT-Indoor** | Indoor IoT radio environment mapping, 2.4 GHz | No — raw proposal + literature | Hermes proposal, radio env mapping papers, variable adaptation doc |

Only **T0** has ready-to-use GT files for the pipeline. T1 and T2 are raw project
materials from which GT files would be authored.

---

## End-to-End Manual Test Procedure

This procedure validates the full CodeAnvil flow from a clean install through
the Build Package → S0 → G0 → S1 → G1, using the FM Build Package under
`templates/no-tools-skills/v3/test-inputs/` as the test input. T0 stays usable as a
hand-written GT pair (S0 passes it through as normalised input).

### Prerequisites

- Python 3.10+
- `curl`
- Agent CLI: `claude`, `pi`, or `opencode` (for sandboxed agent test)
- Internet access (for curl install from GitHub)

### 1. Install or upgrade

#### Remote (GitHub `main` — no clone needed)

The same curl command installs fresh or upgrades an existing installation:

```bash
curl -fsSL https://raw.githubusercontent.com/dramirezbe/codeanvil-gcpds/main/install.sh | bash
source ~/.zshrc  # or ~/.bashrc
```

If codeanvil is already installed, this auto-detects it and runs
`--force-reinstall` to pull the latest commit from `main`.

#### Local repository (development or testing unreleased changes)

From the root of this repository:

```bash
uv tool install --force-reinstall .
# or run the local installer:
bash install.sh
```

Verify:
```bash
codeanvil --help                      # should show: init, create, list, sync, status, now, sandbox
codeanvil sandbox --help              # shows supported agents: claude, codex, opencode, pi
codeanvil now                         # timestamp works
```

### 1b. Clean slate (optional — only for full reset testing)

```bash
# Remove existing installation and state
bash install.sh uninstall 2>/dev/null || true
rm -rf ~/.codeanvil-config
rm -rf ~/.codeanvil  # legacy state — would be auto-migrated back on init
hash -r  # refresh shell command cache
```

Verify:
```bash
command -v codeanvil && echo "FAIL: still installed" || echo "OK: clean"
ls ~/.codeanvil-config 2>&1 | grep -q "No such" && echo "OK: no state" || echo "FAIL: state remains"
```

Then install fresh with the curl command from step 1.

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
ls /tmp/smoke-test/.agents/skills/    # S0, G0, S1, G1, RFD

# .codeanvil/ machine-generated dir
ls /tmp/smoke-test/.codeanvil/project.yaml   # UUIDv7 identity manifest
ls /tmp/smoke-test/.codeanvil/report/        # empty — populated by gate reports

# GT dir — user-authored, outside .codeanvil/
ls /tmp/smoke-test/GT/README.md       # empty GT dir with instructions
```

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
cp templates/no-tools-skills/v3/test-inputs/build_package.md /tmp/smoke-test/GT/build_package.md
```

Alternative (hand-written pair, S0 runs as a no-op): copy the T0 pair instead.

```bash
cp methodology/test/T0_ANE-Lap2/just-edge/StRS.md /tmp/smoke-test/GT/G0_StRS.md
cp methodology/test/T0_ANE-Lap2/just-edge/SyRS.md /tmp/smoke-test/GT/G0_SyRS.md
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

**Expected:** one pass, no questions. Writes `GT/G0_StRS.md`, `GT/G0_SyRS.md` and
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

**Expected:** writes `S1_artifacts/S1_design.md` (GT digests in Meta) and
`S1_artifacts/S1_graph.html`, then `S1.md` with `| HITL | PASS |` naming the graph path.
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
| Reports drive the chain | Delete `S1_graph.html`, run G1 | Prerequisite still passes; finding marked `advisory` |
| Graph differs from design | Remove a module from the graph's `DATA`, run G1 | Finding marked `open` |
| RFD closes the cycle | Answer RFD at G1, decide it, name a new cycle | Old cycle shows `(closed: superseded by <name>)`; G1 before the decision returns `Cycle suspended by RFD. Run the RFD skill.` |

The flow is **not** end to end until S2 and G2 exist; nothing after G1 is covered here.

### 6. Cleanup

```bash
rm -rf /tmp/smoke-test
# Optionally: bash install.sh uninstall
```

---

## Expected findings / feedback areas

After running the full flow, note:

- [ ] Did `codeanvil create` scaffold S0, G0, S1, G1 and RFD (and no custody-chain)?
- [ ] Did the AGENTS.md skill table list the chain S0 → G0 → S1 → G1 with RFD as `-`?
- [ ] Did the agent ask for a cycle name on project open and normalize it (`01_smoke_test`)?
- [ ] Did `.codeanvil/` contain `project.yaml` (with `cycle:`) and an empty `report/`?
- [ ] Did each step write one iterative `<cycle>/<id>.md` report, and did G0 and G1 wait for
      the human's answer?
- [ ] Did S1 write the design and graph to `.codeanvil/report/<cycle>/S1_artifacts/`?
- [ ] Did `codeanvil status` show stages as `delivered` and mark a reworked chain `stale`?
- [ ] Did `codeanvil sync` register a cloned project without re-scaffolding?
- [ ] Did G0 run with the correct project-relative path (`.agents/skills/...`)?
- [ ] Any path errors, missing files, or confusing agent behavior?

Record findings and report back to improve the methodology and tooling.

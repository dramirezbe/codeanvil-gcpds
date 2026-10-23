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
GT → G0 → custody-chain, using T0 as the test input.

### Prerequisites

- Python 3.10+
- `curl`
- `claude` CLI (for sandboxed agent test)
- Internet access (for curl install from GitHub)

### 1. Install or upgrade (no clone needed)

The same curl command installs fresh or upgrades an existing installation:

```bash
curl -fsSL https://raw.githubusercontent.com/dramirezbe/codeanvil-gcpds/main/install.sh | bash
source ~/.zshrc  # or ~/.bashrc
```

If codeanvil is already installed, this auto-detects it and runs
`--force-reinstall` to pull the latest commit from `main`.

Verify:
```bash
codeanvil --help                      # should show: init, create, list, sync, status, now
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
ls /tmp/smoke-test/.agents/skills/    # G0, G1, custody-chain

# .codeanvil/ machine-generated dir
ls /tmp/smoke-test/.codeanvil/project.yaml   # UUIDv7 identity manifest
ls /tmp/smoke-test/.codeanvil/custody/       # empty — populated after G0
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

### 3. Copy T0 Ground Truth files into the project

```bash
# From the codeanvil repo:
cp methodology/test/T0_ANE-Lap2/just-edge/StRS.md /tmp/smoke-test/GT/G0_StRS.md
cp methodology/test/T0_ANE-Lap2/just-edge/SyRS.md /tmp/smoke-test/GT/G0_SyRS.md
```

Verify:
```bash
head -1 /tmp/smoke-test/GT/G0_StRS.md  # "# PROJECT: Edge Sensor ..."
head -1 /tmp/smoke-test/GT/G0_SyRS.md  # "# PROJECT: Edge Sensor ..."
```

### 4. Enter sandboxed Claude session in the project

```bash
cd /tmp/smoke-test
claude --setting-sources "project"
```

The `--setting-sources "project"` flag loads only project-level settings
(CLAUDE.md → AGENTS.md) and ignores user/local settings, ensuring a clean test
of the scaffolded instructions without interference from global config.

*(Note: `--setting-sources ""` disables ALL settings including CLAUDE.md
autodiscovery — don't use it for methodology testing.)*

### 4b. Enter sandboxed Pi session in the project (alternative)

```bash
cd /tmp/smoke-test
pi --no-extensions -e ~/.pi/agent/npm/node_modules/pi-claude-bridge/src/index.ts -e ~/.pi/agent/npm/node_modules/opencode-pi/src/index.ts --no-mcp --no-skills --no-prompt-templates
```

This launches Pi with all user extensions, MCP servers, skills, and prompt
templates disabled, then re-enables only the Claude bridge and OpenCode
extensions. The result is a clean session that reads only the project's
`AGENTS.md` without interference from global config.

### 5. Test prompts (inside sandboxed Claude or Pi)

Run these prompts in sequence inside the sandboxed session. After each,
verify the expected outcome before proceeding.

#### Prompt 1 — Context check

```
What project is this? What skills are available? What should you do first?
```

**Expected:** Claude reads `AGENTS.md`, identifies this as a V-SIL scaffolded
project (not the CodeAnvil repo), lists G0 + custody-chain + G1 in the skill
table, and says the first step is G0 validation of the GT files.

#### Prompt 2 — Run G0

```
start
```

**Expected:** Claude loads `.agents/skills/G0_valid_req_and_GT/SKILL.md`, runs
`python .agents/skills/G0_valid_req_and_GT/scripts/g0_validate.py GT/G0_StRS.md GT/G0_SyRS.md`,
reports the exit code, verdict (G0: PASS or FAIL with specific errors), and the
full validation output (per-document reports + G0-X cross-document report).

#### Prompt 3 — Seal GT with custody-chain

```
G0 passed. Now seal the GT files using the custody-chain skill so any tampering is detected going forward.
```

**Expected:** Claude loads `.agents/skills/custody-chain/SKILL.md`, then:
1. Checks `PROVENANCE_HMAC_KEY` — will report it's unset and ask for it.
   Respond with: `export PROVENANCE_HMAC_KEY="smoke-test-key-2026"` (or tell
   Claude to set it).
2. Runs `source_snapshot.py snapshot --root . --include 'GT/**' --out .codeanvil/custody/snapshot.json`
   → SEALED, 2 files, manifest digest.
3. Records custody: `custody_ledger.py record --ledger .codeanvil/custody/custody.jsonl
   --doc GT/G0_StRS.md --action created --actor "tester" ...` (for both files).
4. Runs `custody_ledger.py verify` → PASS.
5. Reports the provenance report with all statuses.

#### Prompt 4 — Tamper detection

```
I secretly edited GT/G0_StRS.md. Verify the GT files are still intact.
```

**Expected:** Claude runs `source_snapshot.py verify --strict` → FAIL with
`DIGEST_CHANGED` and/or `LENGTH_CHANGED` findings showing expected vs. actual
hashes. Claude does NOT fix the file — reports the finding per the skill's
hard rules.

*(Note: you must actually edit the file before this prompt for it to fail.
If you don't edit it, it should PASS — that's also a valid test.)*

#### Prompt 5 — Custody history

```
Show the full custody history for GT/G0_StRS.md.
```

**Expected:** Claude runs `custody_ledger.py history --doc GT/G0_StRS.md` and
displays the timeline of actions (seq, timestamp, action, actor, hash prefix).

### 6. Cleanup

```bash
rm -rf /tmp/smoke-test
# Optionally: bash install.sh uninstall
```

---

## Expected findings / feedback areas

After running the full flow, note:

- [ ] Did `codeanvil create` scaffold all skills including custody-chain?
- [ ] Did the AGENTS.md skill table list all three skills (G0, custody-chain, G1)?
- [ ] Did `.codeanvil/` contain `project.yaml`, `custody/`, and `report/` (no GT)?
- [ ] Did `codeanvil status` correctly read identity from the manifest?
- [ ] Did `codeanvil sync` register a cloned project without re-scaffolding?
- [ ] Did Claude in the sandboxed session correctly identify it's in a user project?
- [ ] Did G0 run with the correct project-relative path (`.agents/skills/...`)?
- [ ] Did custody-chain scripts write to `.codeanvil/custody/` (not `.provenance/`)?
- [ ] Did the provenance report format match the output contract in SKILL.md?
- [ ] Did Claude refuse to fix a tampered GT file (hard rule: originals are read-only)?
- [ ] Any path errors, missing files, or confusing agent behavior?

Record findings and report back to improve the methodology and tooling.

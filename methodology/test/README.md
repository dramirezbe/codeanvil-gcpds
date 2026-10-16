# V-SIL Test Cases (T#) and End-to-End Manual Test

## Test cases

Each `T<n>_<name>/` folder is a real-world GT instance used to validate the
methodology pipeline. They are the methodology's integration tests.

| T# | Domain | GT-ready | Contents |
|----|--------|----------|----------|
| **T0_ANE-Lap2** | SDR spectrum monitoring (ANE edge sensor) | **Yes** — `just-edge/SRS.md` + `just-edge/HCS.md` are valid GT files | Also has `full-system/SRS_APPROVED.md` (broader scope) |
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

### 1. Clean slate

```bash
# Remove existing installation and state
bash install.sh uninstall 2>/dev/null || true
rm -rf ~/.codeanvil
hash -r  # refresh shell command cache
```

Verify:
```bash
command -v codeanvil && echo "FAIL: still installed" || echo "OK: clean"
ls ~/.codeanvil 2>&1 | grep -q "No such" && echo "OK: no state" || echo "FAIL: state remains"
```

### 2. Install from curl

```bash
curl -fsSL https://raw.githubusercontent.com/dramirezbe/codeanvil-gcpds/main/install.sh | bash
source ~/.zshrc  # or ~/.bashrc
```

Verify:
```bash
codeanvil --help  # should show usage
```

### 3. Initialize and create project

```bash
codeanvil init
codeanvil create smoke-test -p /tmp
```

Verify:
```bash
ls /tmp/smoke-test/AGENTS.md          # generated
ls /tmp/smoke-test/CLAUDE.md          # symlink → AGENTS.md
ls /tmp/smoke-test/.agents/skills/    # G0, G1, custody-chain
ls /tmp/smoke-test/GT/README.md       # empty GT dir with instructions
```

### 4. Copy T0 Ground Truth files into the project

```bash
# From the codeanvil repo:
cp methodology/test/T0_ANE-Lap2/just-edge/SRS.md /tmp/smoke-test/GT/G0_SRS.md
cp methodology/test/T0_ANE-Lap2/just-edge/HCS.md /tmp/smoke-test/GT/G0_HCS.md
```

Verify:
```bash
head -1 /tmp/smoke-test/GT/G0_SRS.md  # "# PROJECT: Edge Sensor ..."
head -1 /tmp/smoke-test/GT/G0_HCS.md  # "# PROJECT: Edge Sensor ..."
```

### 5. Enter sandboxed Claude session in the project

```bash
cd /tmp/smoke-test
claude --setting-sources ""
```

The `--setting-sources ""` flag disables all external settings — Claude reads
only the project's `CLAUDE.md` (→ `AGENTS.md`), ensuring a clean test of the
scaffolded instructions without interference from global config.

### 6. Test prompts (inside sandboxed Claude)

Run these prompts in sequence inside the sandboxed Claude session. After each,
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
`python .agents/skills/G0_valid_req_and_GT/scripts/g0_validate.py GT/G0_SRS.md GT/G0_HCS.md`,
reports the exit code, verdict (G0: PASS or FAIL with specific errors), and the
full validation report.

#### Prompt 3 — Seal GT with custody-chain

```
G0 passed. Now seal the GT files using the custody-chain skill so any tampering is detected going forward.
```

**Expected:** Claude loads `.agents/skills/custody-chain/SKILL.md`, then:
1. Checks `PROVENANCE_HMAC_KEY` — will report it's unset and ask for it.
   Respond with: `export PROVENANCE_HMAC_KEY="smoke-test-key-2026"` (or tell
   Claude to set it).
2. Runs `source_snapshot.py snapshot --root . --include 'GT/**' --out .provenance/snapshot.json`
   → SEALED, 2 files, manifest digest.
3. Records custody: `custody_ledger.py record --ledger .provenance/custody.jsonl
   --doc GT/G0_SRS.md --action created --actor "tester" ...` (for both files).
4. Runs `custody_ledger.py verify` → PASS.
5. Reports the provenance report with all statuses.

#### Prompt 4 — Tamper detection

```
I secretly edited GT/G0_SRS.md. Verify the GT files are still intact.
```

**Expected:** Claude runs `source_snapshot.py verify --strict` → FAIL with
`DIGEST_CHANGED` and/or `LENGTH_CHANGED` findings showing expected vs. actual
hashes. Claude does NOT fix the file — reports the finding per the skill's
hard rules.

*(Note: you must actually edit the file before this prompt for it to fail.
If you don't edit it, it should PASS — that's also a valid test.)*

#### Prompt 5 — Custody history

```
Show the full custody history for GT/G0_SRS.md.
```

**Expected:** Claude runs `custody_ledger.py history --doc GT/G0_SRS.md` and
displays the timeline of actions (seq, timestamp, action, actor, hash prefix).

### 7. Cleanup

```bash
rm -rf /tmp/smoke-test
# Optionally: bash install.sh uninstall
```

---

## Expected findings / feedback areas

After running the full flow, note:

- [ ] Did `codeanvil create` scaffold all skills including custody-chain?
- [ ] Did the AGENTS.md skill table list all three skills (G0, custody-chain, G1)?
- [ ] Did Claude in the sandboxed session correctly identify it's in a user project?
- [ ] Did G0 run with the correct project-relative path (`.agents/skills/...`)?
- [ ] Did custody-chain scripts run from the project root without import errors?
- [ ] Did the provenance report format match the output contract in SKILL.md?
- [ ] Did Claude refuse to fix a tampered GT file (hard rule: originals are read-only)?
- [ ] Any path errors, missing files, or confusing agent behavior?

Record findings and report back to improve the methodology and tooling.

# Runtime, telemetry and MCP probe

Manual probe for the global methodology runtime, the psutil telemetry collector
and the GNU Radio MCP server (plan:
[`global_runtime_and_mcp_manager.md`](../../odd/tasks/global-runtime-mcp/2026-11-06_1521_global_runtime_and_mcp_manager.md),
WU-RT7 and WU-M6). Run the parts in order, and record each run in
[Results](#results).

Commands are for Linux/macOS with bash or zsh. In fish, write `$fish_pid`
wherever this file writes `$$`.

## 0. Install the build under test

The released `codeanvil` (v0.5.0) has no `runtime`, `python` or `mcp`
commands. Install the branch instead:

```bash
cd ~/GIT/UNAL/codeanvil-gcpds
git switch feat/global-runtime-mcp && git pull --ff-only
uv tool install --force-reinstall --python 3.12 .
codeanvil runtime sync
codeanvil runtime list        # psutil  base  <ver> / pyyaml  base  <ver>
```

**PASS:** `runtime list` prints psutil and pyyaml with a version each.

## A. Telemetry at rest (about 2 minutes)

The collector runs in place on the runtime, exactly as `verification/run.sh`
starts it. Here the measured process tree is your shell, so the run shows what
this machine looks like at rest.

```bash
mkdir -p ~/sandbox-vsil && cd ~/sandbox-vsil
codeanvil create --name "Telemetry Idle"
cd telemetry_idle
echo "shell PID: $$"
codeanvil python .agents/skills/S2_implement_services/scripts/telemetry_collector.py \
  --pid $$ --interval 1 --duration 120 --output verification/telemetry/idle.jsonl
```

Leave the machine alone for the 2 minutes: no builds, no browser video. Then
summarise the run with the runtime's own Python:

```bash
"$(codeanvil runtime path)" - verification/telemetry/idle.jsonl <<'EOF'
import json, statistics as st, sys
rows = [json.loads(line) for line in open(sys.argv[1], encoding="utf-8")]
span = rows[-1]["monotonic_s"] - rows[0]["monotonic_s"]
def col(path):
    out = []
    for row in rows:
        value = row
        for key in path:
            value = value.get(key) if isinstance(value, dict) else None
        if isinstance(value, (int, float)):
            out.append(value)
    return out
def show(label, values, unit=""):
    if not values:
        print(f"{label:<22} UNAVAILABLE"); return
    print(f"{label:<22} min {min(values):7.2f}  mean {st.mean(values):7.2f}  "
          f"max {max(values):7.2f}  stdev {st.pstdev(values):6.2f} {unit}")
print(f"samples {len(rows)}  span {span:.1f} s  interval {span / max(len(rows) - 1, 1):.2f} s")
print("measurement_source", sorted({row['measurement_source'] for row in rows}))
host = rows[0]["host"]
print("host", host["system"], host["release"], host["machine"], "cpus", host["cpu_count"])
show("system cpu %", col(["system", "cpu_percent"]))
show("system memory %", col(["system", "memory_percent"]))
show("temperature C", col(["temperature_c", "value"]))
show("tree cpu %", col(["process", "cpu_percent"]))
show("tree rss MB", [v / 2**20 for v in col(["process", "rss_bytes"])])
print("tree pid", {row["process"].get("pid") for row in rows},
      "processes", {row["process"].get("processes") for row in rows})
print("sensors", sorted({row["temperature_c"].get("sensor", "?") for row in rows}))
bad = [k for row in rows for k, v in row.items() if isinstance(v, dict) and "unavailable" in v]
print("unavailable fields", sorted(set(bad)) or "none")
EOF
```

**PASS when all hold:**

| Check | Expected |
|-------|----------|
| samples / interval | about 120 samples, interval 1.00 s (± 0.05) |
| `measurement_source` | `['psutil']` only |
| system cpu % | low at rest: mean well under 10 % on a multi-core desktop; no constant value (stdev > 0) |
| system memory % | stable: stdev under 1 |
| temperature C | a value with a sensor name (e.g. `Tctl` on AMD); `UNAVAILABLE` is acceptable only on a host with no sensors (VM), and must say why in the JSONL |
| tree pid | the `shell PID` you echoed |
| processes | `{1}`: the shell alone — the collector never measures itself |
| unavailable fields | `none` except `counters` / `counters_source` (no `--counters` given) |

A constant CPU reading or a 0.0 first sample is a FAIL: G2 rejects constant or
placeholder telemetry as evidence.

Optional load check, in the same shell (so the load is part of its tree):
`(yes > /dev/null & sleep 25; kill $!) &`, then the collector command with
`--duration 20 --output verification/telemetry/load.jsonl`, then the summary on
`load.jsonl`. `tree cpu %` must be about 100 and `processes` 2–3.

## B. GNU Radio MCP, local to a user project

### B1. Fail fast before the fix

The dev machine's marconi venv was built on a Python that moved from 3.14 to
3.15. gnuradio is compiled for 3.14. The doctor must say so, and give the fix:

```bash
codeanvil mcp doctor marconi; echo "exit $?"
```

**PASS:** `[FAIL] system package gnuradio: gnuradio is built for Python 3.14;
the marconi venv runs 3.15. Run codeanvil mcp update marconi.` and `exit 1`.
On a machine without GNU Radio, the line instead names the install command for
your OS family (e.g. `sudo pacman -S gnuradio`).

### B2. Fix and re-check

```bash
codeanvil mcp update marconi
codeanvil mcp doctor marconi; echo "exit $?"
codeanvil mcp list
```

**PASS:** every doctor line is `[ok]`, including `system package gnuradio:
gnuradio 3.10.x`, and `exit 0`. `mcp list` shows `marconi installed ref
533bae4268e3 pinned`.

### B3. Baseline: nothing global yet

```bash
sha256sum ~/.claude.json | tee /tmp/claude_json.before
(cd ~ && claude mcp list) | tee /tmp/claude_mcp.before
```

Note the user-scope servers listed (on the dev machine: codegraph, context7,
engram, local-rag).

### B4. A user project with marconi

```bash
cd ~/sandbox-vsil
codeanvil create --name "MCP Sandbox Probe" --mcp marconi
cd mcp_sandbox_probe
cat .mcp.json
```

**PASS:** `.mcp.json` holds only
`"command": "codeanvil", "args": ["mcp", "run", "marconi"], "env": {}`, with no
path under your home folder.

### B5. Protocol probe (Level 1, no tokens)

From the repository:

```bash
cd ~/GIT/UNAL/codeanvil-gcpds
CODEANVIL_MCP_E2E=1 uv run pytest tests/test_mcp_e2e.py -v
```

**PASS:** 1 passed. The test starts the launcher from a nested folder, runs a
real GNU Radio flowgraph through `run_pipeline` (4096 samples written) and
checks that stdout carried JSON-RPC only.

### B6. Sandboxed Claude sees only the project's server (Level 2, costs tokens)

```bash
cd ~/sandbox-vsil/mcp_sandbox_probe
claude -p --setting-sources project --output-format stream-json --verbose \
  "List your MCP servers." \
  | jq -c 'select(.type == "system" and .subtype == "init") | .mcp_servers'
```

**PASS:** exactly `[{"name":"marconi","status":"connected"}]`, with no
codegraph, context7, engram or local-rag.

If `jq` prints `null`, the field has another name in your Claude Code version:
drop the trailing `.mcp_servers` and read the init event.

**If a user-scope server leaks**, the sandbox recipe needs the strict flags.
Rerun with them, and if they fix it, report it so `config.yaml`
`sandbox_agents.claude.args` gets them:

```bash
claude -p --setting-sources project --strict-mcp-config --mcp-config .mcp.json \
  --output-format stream-json --verbose "List your MCP servers." \
  | jq -c 'select(.type == "system" and .subtype == "init") | .mcp_servers'
```

### B7. A real tool call from the sandboxed session

```bash
claude -p --setting-sources project --allowedTools "mcp__marconi__run_pipeline" \
  --output-format stream-json --verbose \
  "Call the marconi run_pipeline tool once with this pipeline and report its status: name tone_dump, sample_rate 1e6, blocks: src tone_source (freq 1e5, amplitude 0.5), head head (num_samples 4096), sink file_sink (path $PWD/tone.bin); connections src->head, head->sink." \
  | jq -c 'select(.type == "user") | .message.content[]? | select(.type == "tool_result") | .content' 
ls -l tone.bin
```

**PASS:** the `tool_result` holds `"status": "ok"`, and `tone.bin` is 32768
bytes (4096 complex64 samples).

### B8. Nothing became global

```bash
sha256sum -c /tmp/claude_json.before
(cd ~ && claude mcp list) | diff /tmp/claude_mcp.before - && echo "same user-scope list"
(cd /tmp && claude mcp list) | grep -c marconi   # 0
```

**PASS:** the checksum is `OK`, the user-scope list is unchanged, and the
`grep -c` prints `0`.

### B9. Portability: move the project

```bash
mv ~/sandbox-vsil/mcp_sandbox_probe ~/sandbox-vsil/moved_probe
cd ~/sandbox-vsil/moved_probe && rm -f tone.bin
```

Repeat B7 here, without regenerating any config.

**PASS:** the same `"status": "ok"` and a 32768-byte `tone.bin` in the new folder.

## C. The rest

| Step | Command | PASS |
|------|---------|------|
| C1 user package | `codeanvil runtime add six && codeanvil runtime list` | `six  user  <ver>` listed |
| C2 runs on the runtime | `echo 'import six, sys; print(six.__version__, sys.flags.isolated)' > /tmp/rt.py && codeanvil python /tmp/rt.py` | version and `1` |
| C3 skill package check | In `telemetry_idle`: `codeanvil runtime remove six`, then the collector command of part A with `--duration 2` | still runs: psutil is base, not user |
| C4 base cannot go | `codeanvil runtime remove psutil` | exit 1, `base packages of the runtime cannot be removed: psutil` |
| C5 G0 on the runtime | In `telemetry_idle`: copy `methodology/test/T0_ANE-Lap2/just-edge/{StRS,SyRS}.md` to `.codeanvil/GT/`, then `codeanvil python .agents/skills/G0_valid_req_and_GT/scripts/g0_validate.py .codeanvil/GT/StRS.md .codeanvil/GT/SyRS.md; echo $?` | exit 0, same report as `python3 -I <same script> <same files>` |
| C6 disable / enable | In `moved_probe`: `codeanvil mcp disable marconi`, `cat .mcp.json`, `codeanvil mcp enable marconi` | marconi and its `marconi-*` skills disappear, then come back; the MCP table in `AGENTS.md` follows |
| C7 remove guard | `codeanvil mcp remove marconi` | exit 1, lists the registered projects that use it; nothing deleted |
| C8 full flow | `methodology/test/README.md` § 5b (T3 S0 → G2) in a fresh project | `run.sh vl0` writes JSONL under `verification/telemetry/` from the in-place collector; G2 accepts the readings |

Cleanup: `rm -rf ~/sandbox-vsil/telemetry_idle ~/sandbox-vsil/moved_probe`.
The registry keeps their rows (no prune command yet).

## Results

| Date | Part | Machine | Result | Notes |
|------|------|---------|--------|-------|
| | A | | | |
| | B1–B9 | | | |
| | C1–C8 | | | |

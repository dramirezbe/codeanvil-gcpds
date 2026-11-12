---
name: vsil-hil-usage
description: Deploy a published V-SIL project to enrolled Linux equipment, run PIL or real HW tests, and fetch telemetry through vsil_hil_mcp. Use for remote equipment declared in project.yaml; local devices use the normal runtime tools.
---

# Operate remote PIL/HIL equipment

Use `vsil_hil_mcp` to prepare and test enrolled equipment. Normal commands, scripts,
packages and `sudo` run directly. Clearly destructive operations use trusted.
Follow the current S2/G2 skill: it owns the pre-HW pause, tests and report contract.
The MCP is a command proxy, with credentials kept in local storage, not an orchestrator.
Never read private keys or start a separate direct SSH/rsync session.

## Access and equipment

A human enrolls equipment from a project with:

```sh
codeanvil credential-setup -u <admin-user> -i <host> --port 22
```

Physical MACs discovered over authenticated SSH identify the equipment. The admin
user authorizes enrollment; it does not select or regenerate keys. A known PC
reuses its keys across projects/IP changes. A new PC needs one admin authorization
to append its own public keys to the same `codeanvil-agent`. Never copy another
PC's private keys. Project metadata contains the equipment/endpoint and a workspace
under `/home/codeanvil-agent/projects/<project UUID>`, without local key paths.
Legacy identities remain readable and their existing access is preserved.

No `targets:` means local execution; do not use this server for a device attached
to the developer host. A sole declared target may be implicit in MCP calls; with
several, pass the intended declared identity. Do not ask for a user-invented alias.
If access is missing, explain the enrollment command to the human; tool updates
through `init_codeanvil` require existing access and do not enroll a machine.

## Tools

| Tool | Use |
|------|-----|
| `probe_target(target="")` | Observe actual OS/architecture/CodeAnvil and optional USB enumeration. Versions are diagnostic; `declared_device` is configuration, not detected hardware. |
| `init_codeanvil(target="", source_ref="<published tool ref>", source_repo="<tool repo>")` | Update CodeAnvil on enrolled equipment and check runtime, telemetry and clock commands. Distinguish the CodeAnvil tool repo/ref from the delivered project. |
| `code_sync(target="")` | Fetch upstream, require a clean published Git candidate and rsync its temporary Git export. Preserve databases, SQLite sidecars and declared `persistent_paths`. |
| `ssh_exec_cmd(cmd, target="")` | Execute normal commands verbatim, including scripts, packages and sudo; return raw stdout/stderr/exit code. Use the declared workspace for relative project commands. |
| `ssh_exec_cmd_trusted(cmd, target="")` | Execute a clearly destructive command once, verbatim and audited, under host runtime permissions. |
| `fetch_evidence(target="")` | Fetch only remote `verification/telemetry/` to a new host snapshot and return `local_path`. Select the current run inside it. |

## Prepare → run → fetch

1. Finish local code/kit/tests and inspect Git status. Require committed, clean
   staged/unstaged/untracked inputs and HEAD equal to the freshly fetched upstream.
   Publish the candidate using existing user authorization; a failed push blocks HW.
2. Show code/kit changes, published branch/commit, local results, equipment/device
   and intended preparation/test scope. **Stop and wait for explicit `continue`**
   before updates, deployment or local HW tests, even in full-access mode. Inventory
   probes may precede review. Silence/timeouts are not consent. A changed candidate,
   target, scope or iteration renews the pause. Follow S2's unchanged Pause Schedule;
   record the completed checkpoint in its normal narrative, never a partial report.
3. After review, update tool/app/dependencies from their respective published refs.
   Use an actual published CodeAnvil ref with `init_codeanvil`, not a tag guessed
   from SemVer or the DUT's commit. Diagnose capability failures rather than requiring
   identical tool versions. Synchronize clocks before acquisition, never during it;
   use monotonic durations for measurements. `systemctl` uses trusted.
4. Deploy with `code_sync`. It sends only the Git export, excluding ignored files,
   telemetry, secrets and databases. Persistent destination state survives overwrite
   and `--delete`. If a test must change protected state, do so explicitly via trusted.
5. Run the kit from the equipment's workspace, such as
   `cd <workspace> && verification/run.sh vl0`. S2 writes required tests and metric
   scripts; the fresh G2 verifier runs recorded commands plus auxiliary diagnostics
   within reviewed scope, without changing product/test code. The G2 parent owns
   preparation, expanded scope and trusted operations; the verifier never asks the human.
6. Name attempts `<cycle>_<iteration>_<codeanvil now --machine>` using the current
   S2/G2 iteration. Keep named JSONL telemetry, `measurement.json` v2 and script/capture
   outputs in `verification/telemetry/<run_id>/`; retry with a new timestamp.
   Fetch and read only this attempt's files inside returned `local_path`, which may
   also contain older remote logs. Local attempts use their local output directory.
7. Investigate missing/partial telemetry, notify the parent and decide which measures
   need repeating or which claims remain supported. Collector exit 0 is not complete
   coverage. Never use missing readings as zeros. Preserve failed attempts.

## Destructive commands and trusted

The ordinary door returns `{"status":"use_trusted","command":"...","reason":"..."}`
for visible destructive operations: `systemctl`, reboot/shutdown/poweroff/halt,
recursive `rm`, disk erasers and database writes/tools that can modify state.
Simple database file reads remain normal. Reissue the exact command through
`ssh_exec_cmd_trusted`; host runtime permissions govern native approval prompts.
Full-access mode may have no native prompt, but the skill's pre-HW review still
requires an actual `continue` response. No repeated permission is needed for each
ordinary command inside the reviewed scope.

The router recognizes tokens/options, not arbitrary program behavior. If a script
will erase data or perform another destructive action, use trusted explicitly;
do not hide it inside a permitted script. Unknown normal commands are allowed.

## Results and feedback

PIL runs Mock HAL tests on the real processor and remains VERIFIED. A real hardware
claim needs the actual device test against GT criteria. Choose suitable tools/scripts
and justify measurement resolution against the tolerance. Calibration/corrections
are required only when the GT or conclusion needs them; never widen GT or fabricate
readings. The G2 machine-evidence guide defines measurement v2's small structural
record. No per-file deployment manifest, capture request or universal oracle is needed.

G2 feedback explains observed/expected result, command/equipment, evidence, cause or
pending hypothesis, affected requirement/module/path and next action. Module/kit
rework goes to S2; design rework goes through S1 → G1 → S2 in the same cycle;
infeasibility goes to RFD. Operational faults remain operational. Preserve normal
`Based on`, append-only iterations, HITL and stale handling. A valid JSON record is
not a passing test or a human gate verdict.

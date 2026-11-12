# vsil_hil_mcp — operate the lab target from the agent

The server carries SSH execution, deployment and evidence retrieval to a declared
Linux compute unit. The agent prepares the machine and runs the complete kit.
Before a stage updates, deploys or tests hardware, it must show the candidate and
wait for the user's explicit `continue`. Existing S2 HITL schedules still apply.
Local devices use the normal host tools and the same pre-hardware checkpoint.

## Enroll access once per client and device

From a scaffolded project, with SSH reachable and an existing sudo-capable account:

```sh
codeanvil credential-setup -u <admin-user> -i <host> --port 22
```

The command discovers physical interface MAC addresses over authenticated SSH.
There is no target alias to choose. `-u` authorizes enrollment; MAC identifies the
machine. Changing admin login or a recognized endpoint does not regenerate keys.
The local registry is under `~/.codeanvil-config/hil/`; private keys never enter
project metadata or Git. SSH host authentication remains in effect.

- The same client uses its existing keys in another project and registers that
  project's metadata without repeating administrative enrollment when access works.
- A second client creates its own keys and adds their public counterparts to the
  existing `codeanvil-agent`; it does not replace another client's keys.
- The dedicated agent user has passwordless sudo. Ordinary operations use the main
  tool; visibly destructive operations use the distinct trusted tool below.
- Project workspaces use the existing project UUID under a stable projects root.
  Different projects do not overwrite one shared deployment folder. Clients of the
  same project coordinate use of that workspace; no session/locking service exists.
- Legacy client keys are adopted when authenticated, not silently replaced. Existing
  legacy deploy restrictions are preserved; adopted clients can use their existing
  exec key for project-specific sync rather than invalidate older projects.

Automatic enrollment currently supports Linux targets. The host needs SSH tooling
and `sshpass` for initial password authentication. Repeated access uses dedicated
keys; Windows provisioning and guarded/locked policies remain deferred.

## Connect the tools

```sh
codeanvil mcp add vsil_hil_mcp
codeanvil mcp enable vsil_hil_mcp
```

The launcher resolves the project and credentials. When several devices are declared,
the agent selects the generated equipment ID in tool arguments; users do not name
an arbitrary `--target` during enrollment.

## Tools

| Tool | Behavior |
|------|----------|
| `ssh_exec_cmd(cmd, target="")` | Ordinary shell, sudo, package installs and scripts. Returns stdout/stderr/exit code. Only visibly destructive operations redirect to trusted. |
| `ssh_exec_cmd_trusted(cmd, target="")` | Executes the exact consequential command under the host runtime's permission policy. |
| `init_codeanvil(target="", source_ref="...", source_repo="...")` | After review, installs/updates the tool as the enrolled agent user and checks runtime/telemetry commands. Source ref must be an actually published CodeAnvil ref, independent of the DUT repo. |
| `code_sync(target="")` | Requires a clean, published Git candidate; deploys its temporary Git export, preserving DBs and declared persistent paths. |
| `probe_target(target="")` | Observes OS, architecture, installed version and USB enumeration. Version differences are diagnostic, not an equality gate. |
| `fetch_evidence(target="")` | Fetches remote `verification/telemetry/` into a fresh local snapshot and returns `local_path`. |

A single device can be selected implicitly. Commands remain raw operations, not a
new stage orchestrator. Setup failures are diagnosed by the agent; no measurements
or gate verdicts are invented from a successful connection.

## Normal and destructive operations

Most commands run directly, including custom metrics scripts, `sudo apt install`,
`uv`, pipelines and the kit's `vl0`, `vl1` and approved real-HW tests. The small
router redirects recognizable `systemctl`, reboot/shutdown, recursive `rm`, disk
erasers, DB clients and visible database mutations to the trusted tool.

This is routing assistance, not an adversarial sandbox. Script internals are not
interpreted; an agent that knows a script destroys data must choose trusted. The
host runtime controls its prompts. Full access may suppress those prompts, while
the stage's explicit pre-hardware review checkpoint must still wait for the user.

Sync excludes DBs/SQLite sidecars and declared `persistent_paths` from both sender
overwrite and receiver `--delete`. A deliberate DB migration/reset is an explicit
trusted operation. Private credentials, local environments and telemetry are not
code deployment inputs.

## Stage workflow

1. S2 builds and tests according to its existing pause schedule.
2. The agent checks clean Git status and the published upstream candidate. It shows
   the code/kit, device and planned operations, then stops for review.
3. After `continue`, the parent prepares tool/project dependencies and clocks before
   measuring. It uses an explicit published tool ref for `init_codeanvil`; equal
   numeric versions alone do not identify an unreleased candidate.
4. The agent deploys and runs approved tests, captures real outputs and retrieves
   evidence. G2 uses a fresh verifier that can operate hardware but never edits the
   DUT, asks the human or decides the gate verdict; its parent handles trusted work.
5. Report outcomes and failures with their technical cause and existing rework route.

No HIL deployment manifest, per-file SHA ledger, `capture_request.json` or strict
host-time/version attestation is required. Git/cycle/iteration identify the work.
A changed candidate, target or scope renews review. A retry of the same approved
acquisition uses a new timestamp, not a new gate or cycle.

## Evidence

Run names are `<cycle>_<iteration>_<codeanvil now --machine>`, with stage and device
recorded in `measurement.json`. The v2 record supports numbers, text and booleans,
criteria and `pass|fail|inconclusive`; calibration/uncertainty are required only
when the GT/tolerance needs them. Real measurements are never replaced with fake
values. PIL with Mock HAL inputs remains VERIFIED on the real compute unit.

Incomplete telemetry is reported and investigated. The agent decides whether to
repeat or limit affected conclusions, recording the cause and decision. Collector
exit 0 does not prove full coverage; missing readings are not zeros. `--fsync`
remains optional, and evidence files are never silently overwritten.

Each fetch creates `verification/telemetry/<equipment>/fetch-<unique>/`. Read only
the current run inside the returned `local_path`; snapshots can include older
remote runs. A nonzero transfer exit is a partial fetch, not complete evidence.

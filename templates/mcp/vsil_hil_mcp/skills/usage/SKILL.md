---
name: vsil-hil-usage
description: Run a V-SIL verification kit on a real remote COTS target (Raspberry Pi, Jetson, x86 box) through the vsil_hil_mcp server — deploy the code, run the kit on the real processor, fetch the telemetry back. Use when a project declares a remote `targets:` block and you need PIL (VL-0/VL-1 on real hardware) or to drive a declared target over SSH.
---

# vsil-hil-usage

`vsil_hil_mcp` is the bridge that lets this project's verification kit run on a
**real remote compute unit** over SSH instead of only on the dev host. Running the
kit there turns VL-0/VL-1 into **processor-in-the-loop (PIL)** evidence: the same
tests, Mock HAL and `SYS-*` thresholds, but measured on the real UC's CPU, thermals
and throttling.

You drive the target **only through this server's MCP tools**. You never type a
`codeanvil`/`ssh`/`rsync` shell command for the remote target yourself, never hold a
credential, and never get an interactive shell. The server is the credential
custodian; each tool call is one capability.

## When this applies

- The project declares a remote target in `.codeanvil/project.yaml` under `targets:`.
  No target declared ⇒ the SDR is local (PC→SDR) ⇒ **do not use this server**; run
  `verification/run.sh` directly on the host.
- A human has already provisioned the target (keys installed, CodeAnvil present).
  See **If the target is not provisioned yet** below if the tools report missing keys.

## The tools

| Tool | What it does | You use it for |
|------|--------------|----------------|
| `code_sync(target="")` | rsync the project code → target workspace (deploy key, write-only). Excludes `.git`, `__pycache__`, telemetry, secrets. | Deploy before every run after a code change. |
| `ssh_exec_cmd(cmd, target="")` | Run a **non-privileged** command on the target; returns raw `{stdout, stderr, exit_code}`. Read-only shell + `codeanvil`/`uv`/`python`/`pytest` in the workspace. | Run the kit, probe the device, read logs. **The main interface.** |
| `ssh_exec_cmd_trusted(cmd, target="")` | The **only** privileged door: carries `sudo`/mutating commands, once, verbatim, audited. | OS packages, udev rules, service restarts — see the redirect flow. |
| `fetch_evidence(target="")` | rsync **only** `verification/telemetry/` target → host. | Pull evidence back so G2 reads it on the host. |
| `init_codeanvil(target, host, user, …)` | Generate the target's keys and emit a provisioning **script** for the human. No SSH happens. | First contact only — relay the script to the human. |

`target` may be **omitted** when exactly one target is declared; pass it by name when
several are.

## The core loop: deploy → run → fetch

For a PIL run of a verification level (`vl0`, `vl1`):

1. **Deploy.** `code_sync()` — push the current code to the target workspace.
2. **Run.** `ssh_exec_cmd("cd <workspace> && verification/run.sh vl0")`. `run.sh`
   starts `codeanvil telemetry` on the target itself, so the collector samples the
   **real UC** while the kit runs. Read the raw stdout/exit_code to judge pass/fail.
3. **Fetch.** `fetch_evidence()` — pull the per-run `telemetry-*.jsonl` back into the
   host's `verification/telemetry/`. G2 and the verifier read the evidence locally.

Diagnose before fixing (all read-only, auto-allowed through `ssh_exec_cmd`):
`uname -a`, `cat /proc/cpuinfo`, `lsusb` (is the SDR enumerated?), `dmesg | tail`,
`df -h`, `free -m`, `vcgencmd get_throttled` (RPi undervolt/throttle),
`SoapySDRUtil --find`, `rtl_test`. You are genuinely strong at reading these — this is
real value. Name physical faults (antenna, USB power, RF); you cannot fix them.

## Privileged commands — the `use_trusted` redirect

`ssh_exec_cmd` **refuses** any command containing `sudo` (or another privileged
marker). It runs nothing and returns:

```json
{"status": "use_trusted", "command": "<cmd>", "reason": "..."}
```

When you see this, **do not retry it on `ssh_exec_cmd`**. Instead:

1. Tell the human plainly: *"the target needs `<command>` because `<reason>`"*.
2. Re-issue the **exact same command** through `ssh_exec_cmd_trusted("<command>")`.
3. Because that is a distinct tool, the runtime shows its native permission prompt
   with that command. The human approving the prompt **is** the approval — you don't
   decide it. On approval the server runs it once, verbatim, and returns stdout. On
   decline, nothing runs — report that and stop.

Use the trusted door for OS packages, udev rules (non-root SDR access needs the agent
user in `plugdev`), service restarts — anything that mutates the target. Draft the
exact command (you can build an install command from the OS family), present it, let
the human approve. Never try to smuggle `sudo` inside a `python`/`pytest` script to
dodge the prompt — that defeats the audit and the whole point of the gate.

In non-interactive / sandbox runs there is no human to approve, so the trusted door is
denied by default. That is correct: no privilege escalation in automation.

## If the target is not provisioned yet

If a tool reports a missing key (`missing key … run init_codeanvil first`) or the
target isn't declared, the target needs one-time human bootstrap. **You cannot do this
yourself** — first contact is human-consented by design. Two human paths:

- **Recommended (automated):** the human runs, from inside the project,
  `codeanvil credential-setup -u <admin-user> -i <target-ip>` — it generates the
  confined keys, bootstraps the target over SSH, and registers it in `project.yaml`.
- **Printed-script:** call `init_codeanvil(target="<name>", host="<ip>", user="<user>")`,
  then relay the returned `provision.sh` to the human to run **once, as root, on the
  target**. It creates the confined user, installs the two restricted keys, and
  installs CodeAnvil there.

Either way, surface the instruction to the human and wait. Do not fabricate access.

## Honesty about what PIL buys

Running the kit on the real UC is **VERIFIED on real hardware (PIL)** — no real RF.
It is *not* VL-2/HIL validation: that needs the Real HW HAL against the SDR, an oracle
and the correction chains, which this server carries and runs but does not supply. When
you report results, name the UC (host, os, arch, CodeAnvil version, device) in the
evidence, and keep the VERIFIED-vs-VALIDATED line honest.

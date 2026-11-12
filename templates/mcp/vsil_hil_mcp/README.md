# vsil_hil_mcp — run V-SIL on real hardware over SSH

`vsil_hil_mcp` lets a V-SIL project run its verification kit on a **real remote
compute unit** — a Raspberry Pi, a Jetson, an x86 box — instead of only the
developer's machine. The agent reaches the target through this thin, audited MCP
server (an `ssh`/`rsync` proxy); it never holds a credential and never gets a shell.

Running the kit on the real UC turns VL-0/VL-1 into **processor-in-the-loop (PIL)**
evidence: the same tests and thresholds, measured on the real processor's CPU,
temperature and throttling. This is the first step toward hardware-in-the-loop (HIL).

> **This server is for REMOTE hardware only.** If the SDR is plugged into the machine
> you run the agent on (PC→SDR), you do **not** need this server — run
> `verification/run.sh` directly on the host. Use `vsil_hil_mcp` only when the hardware
> lives on a separate box reached over SSH (SDR→RPi).

---

## Before you start — hardware & network prerequisites

Read this section first. Most HIL problems are network problems, not code problems.

### The target must have

- **A Linux OS with SSH** (an `sshd` running and reachable). Windows targets are
  designed for but not yet validated; bare-metal / no-OS MCUs are **out of scope**.
- **An admin (sudoer) account** you know the password for — used **once**, by you, to
  bootstrap the confined agent user. The agent never sees it.
- **`rsync` available** (or installable). The bootstrap installs `rrsync` (the
  restricted rsync wrapper) to confine the deploy key.
- Enough space and a working package manager (`apt`, `dnf` or `pacman`) for CodeAnvil.

### The network — the part people get wrong

The host (your machine) and the target **must be on the same network** and the host
must be able to open a TCP connection to the target's SSH port (22 by default).

- **Prefer a wired link (Ethernet).** It is the most stable option for sustained test
  runs and the IP rarely changes.
- **No wired option? Use a dedicated access point (AP).** A phone hotspot works for a
  quick smoke test, but it is fragile: the link drops whenever the target upgrades
  network packages (`wpasupplicant`) or the DHCP lease churns the IP mid-run. Avoid it
  for real runs.
- **Reserve a static / fixed IP for the target** (DHCP reservation on the router, or a
  static address on the target). The target is keyed by its IP/host, so a changing IP
  breaks access and forces a re-bootstrap.
- **Let the target finish any `apt`/package upgrades before you drive it over SSH** — an
  in-flight network-stack upgrade will drop the connection.

Find the target's IP from the target itself: `ip addr` (Linux) or `hostname -I`. Confirm
reachability from the host before bootstrapping: `ping <target-ip>` and
`ssh <admin-user>@<target-ip>` once by hand.

---

## One-time setup: bootstrap the target

You do this **once per target**, from inside your project directory. It is the only
moment a human provides privileged access; after it the agent works within the chosen
policy and you never SSH in to type commands again.

### Recommended — automated bootstrap

```bash
# from inside the project (where .codeanvil/ lives):
codeanvil credential-setup -u <admin-user> -i <target-ip>
```

What it does, end to end:

1. Generates two **confined, passphraseless ed25519 keys** under
   `~/.codeanvil-config/hil/<target>/` — isolated from your personal `~/.ssh`.
2. Connects to the target with the admin password (prompted securely; never shown in
   `ps`, never logged), creates the locked agent user **`codeanvil-agent`**, its
   workspace, `rrsync` confinement, NOPASSWD sudo (policy `trusted`), and installs the
   two public keys with their restrictions.
3. Registers the target under `targets:` in `.codeanvil/project.yaml`.

Flags: `-p/--password` (skip the prompt — discouraged), `-s/--sudo-password` (only if
sudo differs from SSH), `-w/--workspace`, `--port`, `-t/--target` (name; defaults to the
IP with `.`/`:` → `_`), `--os linux|windows`. Run `codeanvil credential-setup -h` for
the full list.

The SSH port is saved with the target and used for execution, deployment and evidence
retrieval. An existing target name cannot be reused with different connection settings;
correct its declaration explicitly before reconfiguring it. MCP SSH calls ignore personal
SSH configuration and the SSH agent, and use only the target's dedicated key store.
Windows bootstrap and remote execution currently fail before changing credentials or
registering a target; the Windows provisioning design remains deferred.

> The agent user is **always `codeanvil-agent`** (fixed, for traceability) — not
> configurable.

### Alternative — printed provisioning script

If you'd rather apply the changes yourself, have the agent call `init_codeanvil(...)`.
It generates the keys and prints a `provision.sh` you copy to the target and run
**once, as root**. Same result, zero credential transfer. Read the script before
running it — it creates a user, installs restricted keys, and installs CodeAnvil.

### Install CodeAnvil on the target

`credential-setup` sets up **access**. To actually run the kit, the target also needs
CodeAnvil installed (it brings the telemetry collector). The provisioning script pins
the host's release version and checks it after installation. If you bootstrapped another
way, install the same release as `codeanvil-agent` (with `uv` already available):

```bash
# Replace X.Y.Z with the version reported by codeanvil --version on the host.
uv tool install --force 'git+https://github.com/dramirezbe/codeanvil-gcpds.git@vX.Y.Z'
codeanvil init && codeanvil runtime sync
```

---

## Wire the server into a project

`vsil_hil_mcp` is a bundled, first-party server (version-matched with CodeAnvil). Like
marconi, it is **opt-in** — not every project does HW validation.

```bash
codeanvil mcp add vsil_hil_mcp            # install globally, once
codeanvil mcp enable vsil_hil_mcp         # wire it into the current project
#   ... or at scaffold time:
codeanvil create --mcp vsil_hil_mcp
```

This writes the per-agent MCP configs (`.mcp.json`, `.vscode/`, `opencode.json`,
`.codex/`), all calling the launcher `codeanvil mcp run vsil_hil_mcp`. From then on the
agent discovers the tools over MCP. `codeanvil mcp list` shows install status;
`codeanvil mcp disable` / `remove` tear it down.

The launcher passes its installed version through `VSIL_HIL_CODEANVIL_VERSION`.
Provisioning fails before generating keys if this version is missing or is not a release
`X.Y.Z`; it never guesses a version or installs `main`. Equal release versions establish
collector version parity, not identity of unpublished source changes. DUT identity is
checked separately against the deployed input manifest.

---

## What the agent can and cannot do

The security model is deliberate: the server enforces, the skill only teaches.

| Door | Tool | What goes through it |
|------|------|----------------------|
| **Auto (allow)** | `ssh_exec_cmd` | Known read-only diagnostics and full `codeanvil` control. `python`/`python3`/`uv`/`pytest` and `verification/run.sh vl0\|vl1` require `cd <declared workspace> &&`. Unknown commands, mutations and shell expansion are **refused** and redirected. |
| **Privileged** | `ssh_exec_cmd_trusted` | `sudo` / mutating commands. Configure your runtime to require approval for this distinct tool. Runs once, verbatim, audited. |
| **Deploy** | `code_sync` | rsync host → target workspace (write-only, confined by `rrsync`). |
| **Fetch** | `fetch_evidence` | rsync **only** remote `verification/telemetry/` into a fresh host snapshot; returns `local_path`. |
| **Probe** | `probe_target` | Read OS, architecture, CodeAnvil version and optional `lsusb` output; compare observed and host release versions. No installs or RF transmission. |

Every call — including refusals — is logged to `.codeanvil/hil/audit.log` (target,
command, exit code): attributable and replayable.

**Honest about the limits.** The classifier is a conservative routing aid, not a sandbox:
an allowed Python script or the full CodeAnvil CLI can execute arbitrary user code,
including indirect sudo under the default passwordless `trusted` policy. Permission
prompts belong to the host runtime, not the MCP server; a full-access runtime may run
the trusted tool without asking. Target-side `rrsync` confines only the deploy key;
the exec user has ordinary OS access and is root-equivalent when NOPASSWD is enabled. Use
`trusted` on a **lab box you own and can reflash**. The stricter `guarded` (password
custody, closes the indirect hole) and `locked` (edited allowlist) policies are
designed but not yet implemented.

**Physical faults stay human-only.** The agent can diagnose (read `dmesg`, `lsusb`,
`vcgencmd get_throttled`, `rtl_test`) but cannot fix antenna, USB power or RF-environment
problems — it names the symptom; you act.

---

## Day-to-day: run the kit on the target

Once set up, the agent drives the loop through MCP tool calls:

1. `probe_target()` — record the observed OS, architecture and CodeAnvil version. Stop
   before claiming evidence if `metadata.version_match` is false. `declared_device` is
   configuration; `usb_devices` is observed enumeration and does not prove SDR capability.
2. `code_sync()` — deploy the current code (S2 only; the independent G2 verifier never deploys).
3. `ssh_exec_cmd("cd <workspace> && verification/run.sh vl0")` — run the level; `run.sh`
   starts `codeanvil telemetry` on the target so the collector samples the real UC.
4. `fetch_evidence()` — pull the telemetry into a fresh host directory
   `verification/telemetry/<target>/fetch-<unique>/`. Use the returned `local_path` to read and
   hash evidence. This preserves files fetched from other targets and earlier runs. Each
   snapshot may contain older remote logs too: select only the files produced by this run.
   A nonzero transfer exit means partial evidence; do not accept that snapshot as complete.

You only step in to approve a `ssh_exec_cmd_trusted` prompt when the target genuinely
needs a privileged command (OS packages, udev rules for non-root SDR access). The agent
drafts it and explains why; you approve or decline.

---

## Troubleshooting

| Symptom | Likely cause / fix |
|---------|--------------------|
| `missing key … run init_codeanvil first` | Target not bootstrapped. Run `codeanvil credential-setup` (above). |
| Connection drops mid-run | Unstable WiFi / AP. Switch to Ethernet or a reserved IP; let target `apt` upgrades finish first. |
| IP changed, access broken | DHCP churn. Reserve a static IP; re-run `credential-setup` if the host changed. |
| `no remote target declared` | Not registered in `project.yaml`. Bootstrap registers it; or add the `targets:` block by hand. |
| SDR not found (`lsusb` empty, `SoapySDRUtil --find` empty) | Physical: USB power, cable, or the device isn't plugged in. Human-only. |
| Non-root SDR access denied | Needs udev rules + the agent user in `plugdev` — a one-time `ssh_exec_cmd_trusted` step you approve. |

---

## Scope

- **In:** remote Linux targets over SSH; PIL (VL-0/VL-1 on the real UC); machine-captured
  telemetry.
- **Out (for now):** bare-metal / no-OS MCUs; UART transport; the oracle and metrological
  VL-2 validation (separate workstream); Windows targets are designed but unproven;
  `guarded`/`locked` policies are stubs.

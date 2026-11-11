# UI — graphical companion for CodeAnvil

The UI is an optional graphical companion to the existing CLI. It presents
CodeAnvil's current project, MCP, runtime and methodology capabilities through
purpose-built views while reusing their existing Python logic.

> **Status:** implementation in progress. This README is the UI design brief;
> `odd/tasks/ui/` tracks delivery. Keep the UI optional and additive: do not
> change CLI behavior, project formats or database schema just to support UI
> workflows.

---

## 1. What it is

A **modern management and access surface** for CodeAnvil: see a project's
V-SIL progress, reports and iterations; run every current CLI capability (and
more) from buttons; and launch your favourite coding agent or editor — all in
one app, themed like a **forge** (forge fire / anvil; WoW-style richness given
a professional, restrained turn).

It is a **control surface over the methodology**, not a new agent runtime and
not a new LLM integration. It **displays, relays and orchestrates the existing
tooling** — it never interprets or replaces the harness.

## 2. Hard constraints

1. **Project detection drives the whole app.** A project is detected by
   **`.codeanvil/project.yaml`** — `config/paths.py` already exposes
   `find_manifest()`, which walks up from the launch directory looking for
   exactly that file. This decides which of the two top-level modes the app
   opens in (§3).
2. **Reuse the CLI's code, never shell out to the CLI.** The backend imports
   and calls the existing Python logic **in-process**. The CLI and UI are two
   front-ends over the same logic layer; the UI does not launch the
   `codeanvil` binary for capabilities already available in Python (§6). Launching
   *external* agents/editors and running *verification commands* are genuinely
   external processes and are the only exceptions (§7, §8).
3. **Self-sustained backend that serves the UI.** One process, one launch
   command (§4 picks the shell).
4. **Native-desktop goal on all OS** (Linux, macOS, Windows), including a
   Windows app that drives **WSL** for the terminal/agent side (§5).
5. **No hard-fail without an agent.** Progress, reports, GT and design views
   work with no agent running. Only the **chat/terminal** needs a live agent —
   there the UI makes it visible that you must launch an agent first, instead
   of failing (§7).
6. **UI-only feature glue.** Add UI routes, forms and presentation under
   `src/codeanvil/UI/`; call existing CLI/domain functions in-process. Do not
   add parallel CLI, database, project-manifest or MCP lifecycle logic for a
   UI feature. Extend the shared core only if review proves the capability is
   genuinely missing from the CLI as well.

## 3. Two modes — launcher vs workspace (O1)

The app chooses its mode from `find_manifest()` at launch, and can switch at
runtime:

- **Launcher / dashboard** — when the launch folder has **no** `.codeanvil/`
  project. Shows the **projects list** (`db/projects.list_projects()`) and a
  **Create project** button (`init/create.scaffold_project()`), plus global
  tool config (runtime, MCP, `init`, `upgrade`). Picking a project opens it in
  workspace mode.
- **Workspace** — when the folder **is** a project. Opens the full working
  interface for that project: progress board, reports, GT/design viewers,
  per-project actions, and the agent/editor sidebar (§7).

So project-less actions (`create`, `list`, global config) live in the launcher;
project-scoped views live in the workspace. No warning-and-exit — the launcher
*is* the graceful fallback.

## 4. Packaging — the "vs" (O2)

The backend must run locally no matter what (it spawns PTYs and local
processes), so the only real choice is the **shell** that renders the web
frontend. Options, with CodeAnvil's constraints (Python backend, PTY/local
process access, 3 OS, forge-grade polish):

| Approach | Added stack | Native window & installers | Bundle size | PTY / local access | Build effort | Cross-OS |
|----------|-------------|----------------------------|-------------|--------------------|--------------|----------|
| **Browser-based** (serve to system browser) | none | ✗ (a browser tab) | ~0 | ✓ (local backend) | lowest | ✓ immediate |
| **PyWebView** (system webview from Python) | 1 pip dep | ~ (window yes; installers DIY) | small | ✓ | low | ✓ (webview quirks per OS) |
| **Tauri** (Rust shell + system webview, Python as sidecar) | Rust + Node + PyInstaller sidecar | ✓ real windows + per-OS installers | small (~10–20 MB) | ✓ (sidecar backend) | high | ✓ |
| **Electron** (bundled Chromium) | Node + PyInstaller sidecar | ✓ | large (~120 MB+) | ✓ | medium | ✓ |

**Recommendation (two-phase):**
- **MVP → Browser-based.** Zero packaging, all three OS on day one, fastest
  path to a working control surface. `codeanvil ui` starts FastAPI and opens
  the browser.
- **Ship → Tauri.** Real native windows and signed per-OS installers with a
  small footprint; the FastAPI app is bundled as a **PyInstaller sidecar** the
  Tauri shell launches. **PyWebView** is the pure-Python middle ground if we
  want a window without adding the Rust/Node toolchain; **Electron** only if a
  Tauri webview limitation forces it.

The WS/PTY core is identical across all four, so the MVP is not throwaway.

## 5. Architecture

- **Monolith deployment**: the backend opens the frontend — single process,
  one `codeanvil ui` command.
- **Backend**: FastAPI (Python). Serves the frontend and exposes WebSocket
  endpoints for terminal I/O, agent communication and live status. It calls the
  CodeAnvil logic layer directly (§6).
- **Frontend ↔ Backend**: a WebSocket carries real-time traffic (terminal
  streams, agent messages, status pushes). Plain request/response is fine for
  one-shot actions (list projects, read a report).
- **PTY mirroring**: the backend allocates a real PTY (`pty` stdlib) that
  mirrors the terminal into the frontend. A CLI agent runs **inside this PTY** —
  the frontend is a live window into the same session, not a separate chat.
- **Shell detection**: detects the shell (bash, zsh, fish) from `$SHELL` and
  spawns the PTY with the right interpreter, preserving env, prompt and rc
  files.

### WSL bridge (O4)

On Windows, if **WSL is detected**, the app:
1. starts the WSL distro **in the background** at launch,
2. scans for installed agents/editors **inside WSL** (§7 scan),
3. then runs normally — from the user's point of view it is a native app; WSL
   just loads first and the PTY/agent side runs in WSL, in the selected
   project's path.

## 6. Reuse boundary — the logic layer

The backend imports these directly (no CLI subprocess):

| Concern            | Module / functions |
|--------------------|--------------------|
| Project detection  | `config/paths.py` — `find_manifest()`, `PROJECT_*`, `WORKDIR`, `DB_PATH` |
| Report/gate state  | `reports.py` — `ReportState`, `_report_state()`, `_cycle_reports()`, `_gate_order()`, `backup_entries()` |
| Registry           | `db/projects.py` — `list_projects()`, `get_project_by_id/name()`, `register_project()`, `sync_project()`; `db/utils.connect_db()` |
| Scaffold           | `init/create.py` — `scaffold_project()`, `write_project_manifest()` |
| MCP lifecycle      | `init/mcp.py` — install/update/doctor/enable/disable/run |
| Runtime            | `init/runtime.py` — `sync/add/remove/listing/path` |
| System packages    | `init/system_packages.py` — `probe()`, `cached_probe()` |
| Skills metadata    | `skills.py` — SKILL.md frontmatter parser |
| Timestamps         | `config/time.py` — `format_timestamp[_machine]()` |
| Config             | `templates/config.yaml` via `config.paths.CONFIG` |

The recent refactor already split **pure logic** (above) from **CLI dispatch**
(`parser.py` = arg defs only, `main.py` = thin dispatch, `CLI/commands/*` =
per-command glue). Where a command module mixes logic with printing/`sys.exit`,
the UI work extracts the pure function into a small **service layer** both
front-ends call — the CLI keeps zero adherence to the UI and vice-versa.
**(design task)**

## 7. Agent & editor sidebar (O3)

A left sidebar lists launchers in two groups, by whether they drive the PTY:

- **No terminal (GUI apps)** — open the app on the project path, no PTY:
  **Claude desktop**, **Codex desktop**, **OpenCode desktop**, **VS Code**,
  **JetBrains**.
- **Needs terminal (CLI agents)** — the launch logic **opens a terminal + runs
  the agent**, both in the selected project path; the session is the PTY the
  chat panel mirrors: **codex**, **claude**, **opencode**, **pi**.

Behaviour:
- **Install scan**: at launch (and inside WSL on Windows), scan what is
  installed; **grey out / make opaque** anything not installed.
- **Click-to-install**: clicking a greyed item tells the user it will be
  installed, then installs it **only if the install needs no `sudo`** (the
  common case). Needs sudo → warn and show the manual command.
- **Shell refresh**: after an install, `source` the user's shell rc
  (`~/.bashrc` / `~/.zshrc` / fish equivalent) so a freshly-installed binary is
  found without restarting.
- **Chat gating** (constraint §2.5): if no agent session is live, the chat
  panel shows a clear "launch an agent first" state (with the launch buttons)
  rather than erroring. Progress/reports/GT/design never gate on this.

All launch and install recipes come from an editable YAML (§9), not hard-coded.

## 8. Verification commands

Running a project's `verification/run.sh vlN` and the telemetry collector are
real subprocesses by nature (they execute the delivered prototype, possibly on
a remote HIL target). These are the methodology's own external work, surfaced
through the terminal/PTY and the WS stream — not the CLI-reuse exception.

## 9. Launcher registry — editable YAML (O5)

One **easily-editable YAML** holds every agent/editor entry so install and
launch commands can be changed fast, per OS. Shape (sketch):

```yaml
launchers:
  claude-desktop:
    kind: gui            # gui | terminal
    label: "Claude Desktop"
    icon: claude
    detect: { cmd: "claude-desktop --version" }   # or a path/registry probe
    launch:
      linux:   "claude-desktop {project}"
      darwin:  "open -a Claude {project}"
      windows: "..."                                # inside WSL when applicable
    install:
      linux:   "..."          # run only if no sudo needed
      darwin:  "brew install --cask claude"
      windows: "winget install ..."                # §: winget first, else warn
  claude:
    kind: terminal
    label: "Claude Code"
    icon: claude
    detect: { cmd: "claude --version" }
    launch: { any: "claude" }    # opened in a PTY at {project}
    install:
      linux:  "curl -fsSL https://claude.ai/install.sh | bash"
      windows: "winget install ... || <warn: install manually>"
```

- **Windows installs prefer `winget`**; if winget can't provide it, the UI
  **warns the user to install it manually** rather than guessing.
- Icons: one per launcher (Claude, Codex, OpenCode, Pi, VS Code, VSCodium,
  JetBrains).
- This registry can live beside `config.yaml` (or a dedicated
  `launchers.yaml`) — decided when the ODD task starts.

## 10. Live refresh via watchdog (O6)

A **watchdog** watches every **non-code project document** (the `.codeanvil/`
tree: `report/`, `GT/`, `design/`, `backups/`, `project.yaml`, HIL audit log;
not `src/` or `verification/` code). On a change (file saved, or its **SHA**
differs):
- re-read **only that file**, and
- refresh **only the UI items bound to it** (e.g. a new `report/<cycle>/G1.md`
  bumps the progress board and that gate's report view) via a WS push.

No full rescans; targeted, SHA-gated updates keep the board live while an agent
works.

## 11. Look & feel

- **Theme**: a forge — anvil, forge fire, hot-metal accents, hammered-steel
  surfaces. Inspiration from rich game UIs (e.g. WoW) **re-tuned to a
  professional, restrained register**: legible, calm by default, dramatic only
  where it earns attention (active gate, running agent, PASS/FEEDBACK).
- **Modern**: responsive, light/dark, keyboard-friendly, accessible contrast.
- Data viz (progress, telemetry, dependency graph) uses a consistent,
  accessible palette — brand tokens defined once, not per chart.

## 12. Feature surface — everything the UI must expose

Grounded in the current CLI (`parser.py`) and methodology. This section is the
target UI contract; the current implementation note distinguishes existing
views from planned workflows.

### View & understand
- **Progress board**: `S0 → G0 → S1 → G1 → S2 → G2` (RFD from any stage), per
  cycle, with delivered / stale / closed-cycle markers — from `reports.py`.
- **Reports & iterations**: browse each cycle's gate reports and HITL verdicts;
  diff iterations across cycles. **(+ new)**
- **Themed Markdown viewer**: render reports, GT and design documents as
  formatted HTML (headings, tables, links, quotes and code blocks), rather than
  showing Markdown source. Use the forge palette, spacing and surfaces in both
  light and dark themes. **(+ new; pending)**
- **GT viewer**: `build_package.md`, `StRS.md`, `SyRS.md`.
- **Design viewer**: render `SDD.md` and the interactive
  `dependency_graph.html` inline. **(+ new)**
- **Backups**: `.codeanvil/backups/<cycle>/` with MANIFEST SHA-256.
- **Telemetry**: chart the JSON-lines telemetry (CPU/mem/temp). **(+ new)**
- **HIL targets**: `targets:` from `project.yaml` + `.codeanvil/hil/audit.log`.
  **(+ new)**
- **HW COTS gallery**: a card per hardware component, with its image. **(+ new,
  see §12.1)**
- **Logs**: application logs.

### Feature workflows (the primary UI)

CLI capabilities should appear where users need them, as guided controls with
the right project context, status and result. The generic **CLI actions** page
remains available as an advanced fallback; it is not the main way to use the
UI.

| CLI capability | UI workflow |
|----------------|-------------|
| `list` | The launcher already shows registered projects. |
| `create` | A project creation wizard asks for name and location, then lets the user activate selected MCP servers that are installed globally. |
| `sync` | An **Add existing project** action opens the operating system's folder picker, validates `.codeanvil/project.yaml`, registers or updates the project, then shows it in the launcher. |
| `status` | The workspace progress board is the status view; no separate status command is needed. |
| `backup` | Offer a backup action in the relevant stage/artifact view with its result and manifest. |
| `runtime` | Runtime settings expose package sync/add/remove/list/path with clear global scope. |
| `mcp` | The launcher has an MCP catalog (marketplace-style) showing available servers and install state. Users can install a server there; project creation then offers installed servers to activate for that project. Project settings show health and wiring actions. |
| `telemetry` | Verification and telemetry views display collected data and offer bounded capture controls. |
| `credential-setup` | A guided HIL target setup flow collects target details and credentials securely. |
| `init`, `upgrade` | Global setup/update controls show confirmation, progress and result. |
| `now` | Use internally for timestamps; it does not need a prominent user action. |
| `python`, `sandbox`, `mcp run`, `verification/run.sh` | Run through the live terminal/PTY workflow (§5/§8). |

The generic CLI action catalog is generated from the argument parser and
dispatches existing Python handlers in-process. Keep it for advanced use and
debugging. The feature workflows should use the same underlying logic while
providing purpose-built forms, folder selection, contextual navigation,
confirmation and result display.

**MCP lifecycle:** the launcher catalog is based on the MCP servers CodeAnvil
knows from its shipped configuration. Installing a server uses the existing
global `mcp add` lifecycle; creating a project only offers servers already
installed, and activating one writes that project's MCP manifest, agent
configuration and skills. This keeps global installation separate from
project-level activation. The catalog is marketplace-style UI, not a remote
third-party marketplace.

The current code already provides the needed operations: `server_rows()` lists
configured servers and installed state; `doctor()` reports readiness;
`install_mcp_server()` implements global installation; `cmd_create()` accepts
installed MCP names and delegates scaffold/config generation to
`scaffold_project()`; and `enable_server()` wires a server into an existing
project. The UI should call these through its in-process action adapter or a
small UI route. Do not add a second registry, installer, or project-wiring
implementation.

**Current implementation:** the launcher already implements `list`; the
generic action page can dispatch one-shot handlers. The project creation
wizard, native folder picker for `sync`, and the other feature-specific
workflows above are still pending.

### Launch (external — §7)
- Agents/editors sidebar, two groups.

## 12.1 HW COTS gallery — public API, no key **(+ new)**

Show a photo of every COTS hardware component the project targets, so the GT's
hardware reads as real objects, not just identifiers.

- **Source of the list**: the StRS `HWC-` blocks (and the SyRS). The UI already
  knows the component names; it only needs an image per name.
- **Image source — Wikimedia Commons / Wikidata, no API key.** Resolve each
  component to its Wikidata entity and read the image property **`P18`**, then
  pull the file from Commons. Both are public, keyless, rate-friendly APIs with
  explicit CC licensing and (often) transparent-background product shots. Stock
  APIs (Unsplash/Pexels/Pixabay) are rejected here: they have no specific
  hardware, only generic photography.
- **Cache + offline + reproducible**: the resolved image (and its license +
  attribution) is cached under `.codeanvil/` on first fetch, so later views work
  offline and the artifact is reproducible. Only the public component *name*
  ever leaves the machine — no project or user data.
- **Author override wins**: a `HWC-` block (or `project.yaml`) may pin an exact
  image URL or a local path; that is canonical and author-controlled, like the
  rest of the GT contract.
- **Forge placeholder fallback**: when nothing resolves, show a steel-framed
  line-art placeholder instead of a broken image.
- **Pluggable provider**: the launcher-registry YAML (§9) may define an optional
  alternate image provider (e.g. a keyed search API) for anyone who wants one —
  off by default; the keyless Commons path is the default.
- **Where the fetch runs**: in the **backend** (FastAPI), which has no sandbox
  CSP. (In a published artifact preview the browser sandbox blocks external
  images, so a mockup renders the cards as drawn SVG; the shipped UI shows the
  real Commons photos.)
- **Aesthetic fit**: frame each photo in a hard-edged steel "billet" card with
  its `HWC-` chip and a license/attribution line; prefer Commons'
  transparent-background files; an optional subtle duotone keeps glossy product
  shots inside the forge palette.

## 13. What it will NOT do

- No standalone agent runtime — it mirrors an external agent session.
- No custom LLM integration — orchestration stays with the harness; the UI
  displays and relays, never interprets.
- No shelling out to the `codeanvil` binary for logic the tool already does in
  Python (§2.2).

## 14. Still to pin down (at ODD-task time)

- Exact home of the launcher registry (`launchers.yaml` vs a block in
  `config.yaml`).
- Service-layer extraction list: which `CLI/commands/*` functions need a pure
  counterpart.
- WSL transport specifics (localhost WS into a WSL-side backend vs
  `wsl.exe`-spawned PTY from a Windows-side backend).
- Install-without-sudo detection per package manager (how we know an install
  won't prompt for sudo before running it).

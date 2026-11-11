# UI — graphical companion for CodeAnvil

The UI is a bundled graphical companion to the existing CLI. It presents
CodeAnvil's current project, MCP, runtime and methodology capabilities through
purpose-built views while reusing their existing Python logic.

> **Status:** implementation in progress. This README is the UI design brief;
> `odd/tasks/ui/` tracks delivery. Opening the UI is optional; its dependencies
> and built assets ship with the normal global installation. Keep it additive: do not
> change CLI behavior, project formats or database schema just to support UI
> workflows.

The [2026-11-11 project-contract audit](../../../odd/tasks/ui/2026-11-11_current_project_ui_audit.md)
maps paths and artifact producers for **new projects created with release
`v0.7.0` (`2f08944`)**. Use its expected completed-project tree and acceptance
criteria when adding views. Earlier-version projects and compatibility are
outside scope; acceptance uses only the new 0.7.0 example collection. The UI is developed on `feat/ui`;
the release tag itself has no UI command. Audit §6 identifies post-tag changes
that must not be presented as released 0.7.0 capabilities.

**Implemented on the UI branch (2026-11-11):** project creation/addition,
cycle and report-iteration browsing, shared stale/delivered states, safe
Markdown, Design/Verification views and nested artifacts. The five synthetic
[0.7.0 examples](../../../methodology/test/v0.7.0-example-artifacts/README.md)
exercise the empty through G2 states. Terminal sessions, automatic refresh,
hardware/telemetry surfaces and native packaging remain later work.

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
  **Create project** workflow (existing `CLI/commands/create.cmd_create()`
  includes input validation, scaffold, identity and DB registration), plus global
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
| Report/gate state  | `reports.py` — `ReportState`, `report_state()`, `parse_report_iterations()`, `stale_reason()`, `cycle_reports()`, `gate_order()`, `backup_entries()`; CLI and UI share staleness |
| Registry           | `db/projects.py` — `list_projects()`, `get_project_by_id/name()`, `register_project()`, `sync_project()`; `db/utils.connect_db()` |
| Scaffold           | `init/create.py` — `scaffold_project()`, `write_project_manifest()` |
| Full project sync  | `init/sync.py` — `run_sync()`; reads manifest and reconciles local registration |
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

The current read adapter is `UI/workspace.py`; `UI/project_context.py`
validates identity once for bootstrap, artifact views and workflows.
`UI/workflows.py` calls the full create handler and existing sync function
without changing cwd. Remaining handler extraction is incremental; the
advanced action adapter still dispatches CLI handlers in-process.

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

The active S2/G2 contract names `verification/run.sh vl0` and
`verification/run.sh vl1`, recorded in
`.codeanvil/report/<cycle>/S2_artifacts/test_run.md`. Run them through the
terminal/PTY with the collector companion. Manual reruns show their own
results; they do not write a G2 verdict. The G2 skill and human own that verdict.
Remote execution integration into the stage skills is still pending; the HIL
transport's existence does not establish an automatic remote G2 or `vl2` kit.

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
- The shipped registry is `src/codeanvil/UI/launchers.yaml`; `load_registry()`
  creates the editable global copy at `~/.codeanvil-config/launchers.yaml` on
  first use. The YAML above is a design sketch; the implementation accepts
  argv arrays and does not interpret recipes as shell pipelines.

## 10. Live refresh via watchdog (O6)

A **watchdog** watches methodology documents under `.codeanvil/` (`report/`,
`GT/`, `design/`, `backups/`, `project.yaml`, `hil/audit.log`) and evidence data
under **`verification/telemetry/`**. Include extensionless `report/<cycle>/DRAFT`
and file creation/deletion. Do not watch `src/` or verification source code.
On a change (file saved, or its **SHA** differs):
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
- **Progress board**: `S0 → G0 → S1 → G1 → S2 → G2`, per cycle, with delivered,
  human verdict, stale, draft and closed/suspended-cycle states. RFD is raised
  from S1/G1/G2; S2 records possible infeasibility for G2. Share status semantics;
  raw `reports.py` output alone does not compute all these states.
- **Reports & iterations**: browse each cycle's gate reports and select an
  individual iteration. Implemented; cross-cycle diffs remain planned.
- **Themed Markdown viewer**: render reports, GT and design documents as
  formatted HTML (headings, tables, links, quotes and code blocks), rather than
  showing Markdown source. Use the forge palette, spacing and surfaces in both
  light and dark themes. Implemented with safe GFM rendering; raw HTML and
  automatic external-image loading are disabled.
- **GT viewer**: `build_package.md`, `StRS.md`, `SyRS.md`.
- **Design viewer**: render `SDD.md` and the interactive
  `dependency_graph.html` inline. **(+ new)**
- **Verification / final result**: open `S2_artifacts/test_run.md` and
  `G2_artifacts/verified_prototype.md` inside the selected cycle; show evidence
  levels and the final template's §12 run/stop instructions. Existing files
  can be stale after rework; do not label a cycle complete from file existence.
- **Draft / deviations**: `DRAFT`, `RFD.md` and `RFD_artifacts/RFD-NNN.md`,
  including withdrawn and superseded-cycle outcomes. **(+ new)**
- **Backups**: `.codeanvil/backups/<cycle>/` with MANIFEST SHA-256.
- **Telemetry**: chart `verification/telemetry/*.jsonl` (process/system CPU,
  memory, temperature and available counters); retain unavailable readings and
  unknown cycle/target associations. **(+ new)**
- **HIL targets**: `targets:` from `project.yaml` + `.codeanvil/hil/audit.log`.
  **(+ new)**
- **HW COTS gallery**: a card per hardware component, with its image. **(+ new,
  see §12.1)**
- **Logs**: captured action/terminal streams and project-declared log files.
  The current project contract defines no universal application log directory.

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
| `credential-setup` (post-tag extension) | Guided HIL setup requires the later tool build; the command is absent from release 0.7.0 and is deferred for the strict release baseline. |
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

The current code already provides these operations: `server_rows()` lists
configured servers and installed state; `doctor()` reports readiness;
`install_mcp_server()` implements global installation; `cmd_create()` accepts
installed MCP names and delegates scaffold/config generation to
`scaffold_project()`; and `enable_server()` wires a server into an existing
project. The UI should call these through its in-process action adapter or a
small UI route. Do not add a second registry, installer, or project-wiring
implementation.

Release boundary: the 0.7.0 tag declares `vsil_hil_mcp`, but its wheel mapping
omits the bundled server source and its transport predates the rrsync fix.
The later branch corrects both. The release catalog entry alone is not proof
that HIL installation or execution works; keep that distinct from the core
0.7.0 project views and workflows.

**Current implementation:** the launcher lists projects, adds an existing
project through manifest validation and UUID-based sync, and creates projects
through the full scaffold/identity/registration operation. A native folder
picker runs in an isolated Python/Tk process; manual path entry remains
available when it is unavailable or headless. Creation lists the configured
MCP servers and permits activation of installed ones. Global MCP installation,
contextual backup/runtime/telemetry controls and other guided settings remain
available through the advanced action catalog until their own workflows land.

Without a selected project, the WORKSPACE sidebar contains only CLI actions.
Opening a project reveals its navigation; a labeled Project launcher button
returns to the project list, including from global CLI actions. Recent projects
show the local user/home context and abbreviate paths inside that home as
`~/…`, retaining full paths in tooltips and exact paths outside the home.

The workspace now exposes GT, Design, reports and Verification with cycle and
iteration selection, useful missing-artifact states and a synthetic-fixture
notice. A completed cycle requires current stage/gate reports plus a prototype
whose baseline matches the latest S2/G2 iterations; file existence is not
enough. DRAFT, RFD suspension/withdrawal, closed cycles and transitive staleness
are shown explicitly. Backups currently list the latest per stage/cycle;
history and manifest inspection are still pending. The graph runs in a
sandboxed iframe with its copied library inlined for offline display.

Validation: 537 Python tests passed (one optional test skipped), 11 frontend
tests passed, and the production frontend built. A real Chromium run covered
the five fixture states, add/create, iteration selection, the interactive graph,
light/dark themes and mobile navigation against an isolated temporary DB.
Native folder-dialog interaction is covered by mocked tests, not a cross-OS
desktop acceptance claim. The global tool now uses this branch's self-contained
wheel; the published release tag remains unchanged.

To run this branch's UI from the repository root:

```bash
uv run codeanvil ui
```

This runs the checkout's implementation. Development checks are
`uv run --extra dev pytest tests templates/tests -q` and, from `frontend/`, `pnpm test`
and `pnpm build`.

### Local user context and folder defaults

The bootstrap response includes the local user's name and home directory.
Folder dialogs start in an existing `~/Documents`, then `~/Documentos`, or
the home directory when neither exists, independently of the launch directory.
An explicit valid path takes precedence. Folder-name previews call the shared
CLI creation logic, so the default follows the TUI's naming rules.
The locally bundled Lucide Anvil favicon is served at both `/favicon.svg` and
`/favicon.ico`; its upstream license ships with the frontend assets.

### Global installation and dependency ownership

The standard CodeAnvil package includes FastAPI, Uvicorn, HTTPX and watchdog
in its own global tool environment. React, Markdown, icons and local fonts
are compiled by the frontend build and shipped under `UI/frontend/dist/`.
The browser fetches those assets from CodeAnvil's local server, with no font
CDN or frontend package installation at startup.

`codeanvil init` validates the complete HTML/JS/CSS/font bundle and Python
web imports, seeds the editable global launcher registry once, and prepares
the DB and methodology runtime. It preserves existing project registrations
and launcher edits. Afterwards `codeanvil ui` works from the global binary
without an `[ui]` extra, Node or pnpm. These are development tools only;
distribution builds require the prebuilt frontend and never install them.

The global wheel installation and `init` passed with Node and pnpm absent from
PATH. Chromium loaded the global UI, all three font families and the completed
prototype with external requests blocked (zero attempted). The six existing
project registrations and database bytes remained unchanged.

The native folder picker remains optional OS integration: when Python/Tk or
a desktop display is unavailable, the project form accepts a manual path.
MCP servers and external agents keep their separate explicit install flows.

### Launch (external — §7)
- Agents/editors sidebar, two groups.

## 12.1 HW COTS gallery — public API, no key **(+ new)**

Show a photo of every COTS hardware component the project targets, so the GT's
hardware reads as real objects, not just identifiers.

- **Source of the list**: StRS §1.6 hardware inventory (`HW-*` entries: name,
  purpose, manufacturer, part number). Join its HWC-* constraints through the
  `Component` field. A component can have many constraints: one card represents
  the component, not each constraint. No current UI inventory reader exists.
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
- **Author override wins (planned)**: define a UI-owned image override and cache
  format before implementation. Current GT/manifest schemas have no image field;
  do not require new GT content or silently extend `project.yaml` for the gallery.
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
  its `HW-*` identity, linked HWC-* constraints and a license/attribution line; prefer Commons'
  transparent-background files; an optional subtle duotone keeps glossy product
  shots inside the forge palette.

## 13. What it will NOT do

- No standalone agent runtime — it mirrors an external agent session.
- No custom LLM integration — orchestration stays with the harness; the UI
  displays and relays, never interprets.
- No shelling out to the `codeanvil` binary for logic the tool already does in
  Python (§2.2).

## 14. Still to pin down (at ODD-task time)

- Launcher recipe completeness and OS validation; registry location is resolved (§9).
- Service-layer extraction list: which `CLI/commands/*` functions need a pure
  counterpart.
- WSL transport specifics (localhost WS into a WSL-side backend vs
  `wsl.exe`-spawned PTY from a Windows-side backend).
- Install-without-sudo detection per package manager (how we know an install
  won't prompt for sudo before running it).

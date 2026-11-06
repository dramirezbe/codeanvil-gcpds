# Global Methodology Runtime and MCP Manager Plan

## Context

Skills need Python dependencies that a project does not own (for example a
script that needs `psutil` or `torch`), and the methodology has to run the
same way on Linux, macOS and Windows. Today:

- `uv tool install` puts codeanvil in its own isolated venv, which holds only
  `beaupy` and `pyyaml`. Skills cannot declare or rely on any other package.
- Skills describe OS-specific shell steps (`sha256sum` / `shasum` /
  `Get-FileHash` in G1, `cp` vs `Copy-Item`), so every OS needs its own
  wording.
- MCP servers (`src/codeanvil/init/mcp.py`) each get their own venv under
  `~/.codeanvil-config/mcp/<name>/`, but:
  - they install only through `codeanvil init --mcp`; there is no update,
    remove, list or health check;
  - the clone is not pinned: a reinstall runs `git pull --ff-only` on the
    branch head;
  - install errors are swallowed (`uv sync` runs with `check=False,
    capture_output=True`);
  - `codeanvil create` bakes the absolute install path, the absolute
    project path (`MARCONI_WORKSPACE`) and the system-package `PYTHONPATH`
    into four per-agent JSON files. A moved project, a cloned project or a
    changed system Python leaves them stale, and they differ per OS;
  - the env/bridge logic is duplicated in `write_mcp_manifest()` and
    `generate_agent_mcp_configs()`;
  - a missing system package only logs a warning, and a **present but
    unusable** one is reported as found (evidence below).

**Evidence: the gnuradio bridge is broken on the dev machine (2026-11-06).**
gnuradio 3.10.12 is installed for Python 3.14
(`/usr/lib/python3.14/site-packages/gnuradio`); the marconi venv runs
Python 3.15. `_detect_system_site_packages()` finds the folder, so no warning
is logged, but the import fails through the bridge:

```
$ PYTHONPATH=/usr/lib/python3.14/site-packages ~/.codeanvil-config/mcp/marconi/.venv/bin/python \
    -c "from gnuradio import gr"
ModuleNotFoundError: No module named 'gnuradio.gr.gr_python'
```

The compiled extension exists only for CPython 3.14. `python3` (3.14) imports
it fine. The check tests that a folder exists, not that the import works.
**Leave this machine broken until WU-M5 lands**: it is the regression case
for WU-M5 and WU-M6.

**Sandbox isolation is unproven.** `~/.claude.json` holds four user-scope MCP
servers (`codegraph`, `context7`, `engram`, `local-rag`). The Claude sandbox
recipe passes only `--setting-sources project`; whether that excludes
user-scope MCP servers has not been tested. Claude Code 2.1.318 offers
`--strict-mcp-config` with `--mcp-config <file>`, which loads only the given
servers.

More MCP servers are planned, so each of these costs grows per server.

## Decision (owner, 2026-11-06)

One manager under `~/.codeanvil-config/`, two kinds of environment:

```
~/.codeanvil-config/
├── db/
├── runtime/                 ← NEW: methodology venv, shared by every project
│   ├── pyproject.toml       ← generated: shipped base + user additions
│   ├── uv.lock              ← one universal lock (Linux, macOS, Windows)
│   ├── user.yaml            ← packages added with `codeanvil runtime add`
│   └── .venv/
└── mcp/<name>/              ← one venv per server, pinned ref, own lock
```

- The **methodology runtime** is global by design. This trades skill
  self-containment for comfort and one cross-platform lock; skills mitigate
  it by declaring what they need (`metadata.runtime`, WU-RT4).
- **MCP servers never share the runtime venv.** Each server is a third-party
  project with its own lock; a shared venv would let one server break another,
  and future servers may not be Python. What they share is the lifecycle
  commands and one launcher.

## Coordination with the T3 holdout refactor

The refactor in
[`odd/tasks/t3-holdout-refactor/2026-11-06_1410_t3_holdout_refactor.md`](../t3-holdout-refactor/2026-11-06_1410_t3_holdout_refactor.md)
is complete: `v0.5.0` is tagged on `main` (`027acd4`, PR #6), so the start rule
below is met and this plan runs on `feat/global-runtime-mcp`.

**Start rule.** Begin this plan only after `v0.5.0` is tagged on `main`.
Branch `feat/global-runtime-mcp` from that tag. If the refactor gets
follow-up commits, rebase before touching a shared file.

**Shared files.** Both plans edit these. The refactor has merged, so they are
free to edit; the table records what v0.5.0 already put there:

| File | Refactor touches | This plan touches |
|------|------------------|-------------------|
| `templates/config.yaml` | `backup_targets`, GT paths | `runtime`, `mcp_servers.*.ref` |
| `src/codeanvil/config/paths.py` | `PROJECT_GT`, `PROJECT_DESIGN`, `PROJECT_BACKUPS` | `RUNTIME_DIR` |
| `src/codeanvil/CLI/parser.py`, `main.py`, `commands/__init__.py` | `backup` (its `choices` come from `CONFIG["backup_targets"]`) | `runtime`, `python`, `mcp`, following the same config-derived pattern |
| `tests/test_cli.py` | `EXPECTED_SUBCOMMANDS` + `backup` | + `runtime`, `python`, `mcp` |
| `src/codeanvil/init/create.py` | GT/design/backups dirs | MCP config generation |
| `templates/AGENTS/TEMPLATE_AGENT.md` | command list, layout | command list |
| `CLAUDE.md`, `AGENTS.md` | Phase 5 docs | Phase 4 docs |

**Non-goals:**
- Do not change stage or gate logic. The only skill edits are the
  `metadata.runtime` declarations, the G0 script invocation (WU-RT5) and the
  telemetry collector's move to the runtime (WU-RT7).

**Owner decision (2026-11-06, after v0.5.0):** the telemetry collector moves to
the methodology runtime and uses psutil only (WU-RT7). This reverses the
earlier non-goal. Cost: a delivered project's `run.sh` needs `codeanvil` on
PATH to record telemetry, the same self-containment trade the runtime already
makes for skill scripts.

---

## Phase 1 — Methodology runtime

### WU-RT1: Shipped runtime spec

- New `templates/runtime/pyproject.toml`: project `codeanvil-runtime`,
  `requires-python = ">=3.12"`, base dependencies kept minimal (`pyyaml`,
  `psutil` for WU-RT7), `[tool.uv] package = false`.
- `pyproject.toml` force-includes paths one by one, so add
  `"templates/runtime" = "codeanvil/templates/runtime"`; without it a wheel
  install has no runtime spec.
- New `templates/runtime/uv.lock`: generated with `uv lock`, which resolves
  for every platform at once. This is the single lock maintained for Linux,
  macOS and Windows.
- New `config.yaml` key:

  ```yaml
  runtime:
    dir: "runtime"              # under ~/.codeanvil-config/
    python: "3.12"              # same interpreter pin as install.sh / upgrade
    system_packages: []         # e.g. ["gnuradio"], bridged via a .pth file
  ```

- `paths.py`: `RUNTIME_DIR = WORKDIR / CONFIG["runtime"]["dir"]`.

### WU-RT2: `codeanvil runtime <sync|add|remove|list|path>`

New `src/codeanvil/CLI/commands/runtime.py` plus `src/codeanvil/init/runtime.py`.

- **`sync`**: write `RUNTIME_DIR/pyproject.toml` = shipped base +
  packages from `user.yaml`; copy the shipped `uv.lock` when the runtime has
  none; run `uv lock` (keeps existing pins as preferences) and
  `uv sync --project RUNTIME_DIR`. Errors are never swallowed: a failing `uv`
  call exits nonzero with its stderr.
- **`add <pkg>...` / `remove <pkg>...`**: edit `user.yaml`, then `sync`.
  User additions survive `codeanvil upgrade` because they live outside the
  shipped spec.
- **`list`**: base and user packages with their locked versions.
- **`path`**: print the runtime's Python interpreter path.
- **System packages**: for each `runtime.system_packages` entry, reuse
  `_detect_system_site_packages()` and write `codeanvil-system.pth` into the
  venv's site-packages. A `.pth` file still works under `python -I`, while a
  `PYTHONPATH` bridge does not (`-I` ignores environment variables).
  Move `_detect_system_site_packages()` from `mcp.py` to a shared
  `src/codeanvil/init/system_packages.py` used by both.

### WU-RT3: `codeanvil python <script> [args...]`

- Resolve the project root with `find_manifest(cwd)`; fall back to cwd.
- Run `<RUNTIME_DIR>/.venv/bin/python -I <script> [args]`
  (`.venv\Scripts\python.exe` on Windows) with cwd = project root. Forward
  the exit code. On POSIX `os.execv` replaces the launcher, so the script's
  parent is the caller (`run.sh`), which the telemetry collector relies on.
  On Windows the launcher stays as the parent (`subprocess.run`).
- Missing runtime → exit nonzero with `Runtime not installed. Run codeanvil runtime sync.`
- Logging goes to stderr only; stdout belongs to the script.

### WU-RT4: Skill dependency declaration

- Skills declare runtime packages in frontmatter:

  ```yaml
  metadata:
    gate: "G0"
    runtime: ["pyyaml"]
  ```

- `codeanvil python` checks a script under `.agents/skills/<skill>/` against
  that skill's `metadata.runtime` with `importlib.metadata` in the runtime
  venv. A missing package stops before the run:
  `Skill G0_valid_req_and_GT needs psutil. Run codeanvil runtime add psutil.`
- Extend `_parse_skill_frontmatter()` in `create.py` to return `runtime`, or
  move frontmatter parsing to a shared module so `create` and `python` use
  one parser.

### WU-RT5: First adopter: G0

- G0 `SKILL.md`: invoke the validator as
  `codeanvil python .agents/skills/G0_valid_req_and_GT/scripts/g0_validate.py <StRS.md> <SyRS.md>`
  and replace its `compatibility:` line (no more "Requires Python 3.9+").
- The validator stays stdlib-only; this WU proves the path end to end.

### WU-RT6: Lifecycle hooks

- `codeanvil init` runs `runtime sync` after the DB setup.
- `codeanvil upgrade` runs the **new** binary's `codeanvil runtime sync` as a
  subprocess after a successful reinstall, so a changed shipped lock takes
  effect at once.

### WU-RT7: Telemetry collector on the runtime (psutil only)

- Move `S2_implement_services/references/telemetry_collector.py` to
  `S2_implement_services/scripts/telemetry_collector.py`. It stays locked, but
  S2 no longer copies it into the project: `run.sh` runs it in place with
  `codeanvil python .agents/skills/S2_implement_services/scripts/telemetry_collector.py --pid $$ --output verification/telemetry/<level>-<timestamp>.jsonl &`.
- S2 frontmatter declares `metadata.runtime: ["psutil"]`; `psutil` joins the
  runtime base. The collector imports psutil unconditionally: the "psutil
  missing → every metric unavailable" branch goes away, and a missing psutil
  is caught by `codeanvil python` before the run (WU-RT4).
- The collector excludes its own PID from the measured tree.
- `project_layout.md`: drop `psutil` from the kit's dev group;
  `verification/telemetry/` keeps only the JSONL runs. G1, G2, the SDD
  template and the verifier keep the §1.7 "telemetry companion" design
  contract; only the collector's location and launch change.

**Tests (Phase 1)**: new `tests/test_runtime.py` with `uv` calls mocked
(pyproject merge of base + user packages, `user.yaml` survives a re-sync,
`.pth` content, interpreter path per OS, missing-runtime error,
`metadata.runtime` check passes and fails); `tests/test_cli.py` guards for
`runtime` and `python`. One integration test, marked slow, runs a real
`uv sync` on a temp `RUNTIME_DIR`.

---

## Phase 2 — MCP manager

### WU-M1: Pin every server

- `config.yaml` `mcp_servers.<name>.ref`: a tag or commit. For `marconi`, pin
  the commit currently installed (`git -C ~/.codeanvil-config/mcp/marconi rev-parse HEAD`
  at implementation time).
- Install and update check out `ref`; never `pull` a branch head.

### WU-M2: `codeanvil mcp <add|update|remove|list|doctor>` (global)

New `src/codeanvil/CLI/commands/mcp.py`; logic stays in `init/mcp.py`.

- **`add <name>`**: clone, check out `ref`, `uv sync --extra mcp`, check
  `system_packages`. Errors exit nonzero with the failing command's stderr.
  `codeanvil init --mcp <name>` stays as an alias that calls the same code.
- **`update [name]`**: fetch, check out the configured `ref`, re-sync.
- **`remove <name>`**: delete `~/.codeanvil-config/mcp/<name>/` after
  listing the projects in the DB whose `.agents/mcp.yaml` names it.
- **`list`**: configured servers, installed or not, pinned `ref` vs checked-out
  commit.
- **`doctor [name]`**: `requires` on PATH, `system_packages` found, venv
  present, checked-out commit equals `ref`.

### WU-M3: `codeanvil mcp run <name>` launcher

The single command every agent config calls. At start it resolves:

- the install path (`get_mcp_install_path()`);
- `{project_dir}` from `find_manifest(cwd)`, so a moved or cloned project
  needs no regenerated config;
- the system-package bridge (`PYTHONPATH` for the server's own venv);
- `env` from `config.yaml`.

Then it starts `command` + `args`:

- **POSIX**: `os.execvpe`, so the launcher is replaced by the server.
- **Windows**: `os.execv` does not replace the process; it spawns a new one
  and the parent exits, which an MCP client reads as a dead server. The
  launcher stays as the parent: `subprocess.run` with inherited stdin,
  stdout and stderr, terminates the child on Ctrl+C or parent exit, and
  forwards the exit code.
- **stdout is the MCP protocol channel.** The launcher writes nothing to
  stdout; logs go to stderr (the codeanvil logger already uses stderr).
  Errors exit nonzero with one stderr line.

### WU-M4: Portable per-project configs

- `generate_agent_mcp_configs()` and `write_mcp_manifest()` emit, for every
  server: `command: "codeanvil"`, `args: ["mcp", "run", "<name>"]`, no env,
  no absolute path. The four writers (`.mcp.json`, `.vscode/`, `.opencode/`,
  `.codex/`) produce the same content on every OS.
- Remove the duplicated env/bridge code from both functions; it lives only
  in the launcher.
- **`codeanvil mcp enable <name>` / `disable <name>`** (inside a project):
  copy or remove the server's prefixed skills, regenerate the four configs
  and `.agents/mcp.yaml`. This also migrates a project created with the old
  absolute-path configs.
- Check `codeanvil sandbox` recipes: `codeanvil` must stay on PATH inside the
  sandbox (today no recipe rewrites PATH).

### WU-M5: System packages fail fast, with install instructions

**Probe = a real import in the target interpreter**, never a folder check.
New `src/codeanvil/init/system_packages.py` (shared with WU-RT2):

1. Run `<server venv python> -c "<probe>"` with the bridge applied. The probe
   comes from config, e.g. `from gnuradio import gr; print(gr.version())`.
2. Report exactly one of three outcomes:
   - **missing**: no installation found → OS-specific install instruction;
   - **ABI mismatch**: found for Python X.Y, venv runs A.B (the dev-machine
     case) → `gnuradio is built for Python 3.14; the marconi venv runs 3.15.
     Run codeanvil mcp update marconi.`;
   - **ok** → the version string.
3. **Prevent the mismatch at install time.** When a server declares
   `system_packages`, `mcp add` / `mcp update` create its venv with the
   interpreter the package was built for (read from the `python3.X` segment
   of the detected path, or `gnuradio-config-info`), using
   `uv venv --python <that interpreter> --system-site-packages` instead of
   a `PYTHONPATH` bridge. Same rule for `runtime.system_packages` in WU-RT2.
4. **Where it runs:**
   - `mcp add` and `mcp update`: blocking; exit nonzero.
   - `mcp doctor`: reports all three outcomes.
   - `mcp run`: before starting the server, one stderr line and exit
     nonzero, so the agent shows "server failed to start" with the reason.
     Cache an `ok` result in `~/.codeanvil-config/mcp/<name>/.probe.json`,
     keyed by the venv interpreter path and the package folder mtime, so
     startup does not pay the import every time.
   - `codeanvil python`: the same for `runtime.system_packages`.
5. **Install instructions are data**, not code. The OS family comes from
   `platform.freedesktop_os_release()` (`ID`, then `ID_LIKE`), `darwin` and
   `win32`:

   ```yaml
   system_packages:
     gnuradio:
       probe: "from gnuradio import gr; print(gr.version())"
       install:
         arch: "sudo pacman -S gnuradio"
         debian: "sudo apt install gnuradio"
         fedora: "sudo dnf install gnuradio"
         darwin: "brew install gnuradio"
         win32: "Use WSL, or install radioconda (Windows support unverified)"
   ```

   `mcp_servers.<name>.system_packages` lists names from this table.
   Replace the hardcoded hint in `install_mcp_server()`
   (`apt install gnuradio-dev`, `dnf install gnuradio-devel`: the `-dev`
   packages are for building out-of-tree modules, not for running GNU Radio).
6. **Windows** is unverified: radioconda ships gnuradio inside a conda
   Python, so the server venv would need that interpreter. Until tested on a
   Windows machine, the `win32` instruction recommends WSL.

**Tests**: probe outcomes with a fake interpreter (missing, mismatch, ok);
OS-family selection from a fake `os-release`; `mcp run` exits nonzero with
nothing on stdout when the probe fails; cache invalidation on mtime change.

### WU-M6: End-to-end proof — local, not global, through the Claude sandbox

Two levels: a deterministic protocol probe (no tokens, runs in CI) and a real
sandboxed Claude session (manual, costs tokens).

**Setup** (scratch dir, not the repo):
`codeanvil create --name "MCP Sandbox Probe" --mcp marconi`. Record the
SHA-256 of `~/.claude.json` and the output of `claude mcp list` run from
`$HOME` **before** the create.

**Level 1 — protocol probe** (new `tests/test_mcp_e2e.py`, marked `slow`,
skipped when marconi is not installed):
1. From a nested folder of the project, spawn `codeanvil mcp run marconi`
   and speak JSON-RPC over stdio: `initialize` → `tools/list` →
   `tools/call` on one tool that **imports gnuradio** (pick the tool at
   implementation time from `tools/list`).
2. Pass: the tool call returns a result, not an error. On the dev machine
   **before** WU-M5 this must fail with the ABI-mismatch message; after
   WU-M5 it must pass.
3. Every byte on stdout parses as JSON-RPC (no log line leaks into the
   protocol channel).

**Level 2 — sandboxed Claude session** (manual script
`methodology/test/mcp_sandbox_probe.md` with exact commands and expected
output; record each run's result there):
1. **Only project servers are visible.** Run the sandbox recipe
   non-interactively in the project:
   `claude -p --setting-sources project --output-format stream-json --verbose "List your MCP servers."`
   In the `system`/`init` event, the MCP server list must equal `{marconi}`
   with status `connected`, and must not contain `codegraph`, `context7`,
   `engram` or `local-rag`. (Confirm the event's field name for the server
   list at implementation time.)
2. **If a user-scope server leaks**, change the Claude recipe in
   `config.yaml` to
   `args: ["--setting-sources", "project", "--strict-mcp-config", "--mcp-config", ".mcp.json"]`
   and rerun step 1. Also check that `--mcp-config` servers load without the
   `enabledMcpjsonServers` approval; if they do, the
   `.claude/settings.json` approval write may become redundant for the
   sandbox (keep it for normal sessions).
3. **A real tool call works.** Prompt the session to call the gnuradio tool
   from Level 1; the `tool_result` event must hold a successful result.
4. **Nothing became global.** After the run: `~/.claude.json` has the same
   SHA-256 as before; `claude mcp list` from `$HOME` shows no `marconi`;
   a plain `claude` session in another folder does not list `marconi`.
5. **Portability.** Move the project folder and repeat step 3 with no
   config regeneration.

Level 2 repeats for OpenCode and Codex sandboxes later; this plan proves
Claude first.

**Tests (Phase 2)**: new `tests/test_mcp_manager.py` (pinned checkout, `doctor`
findings, `list` output, configs contain no absolute path, `enable` rewrites
an old-style config, launcher resolves `{project_dir}` from a nested cwd,
launcher writes nothing to stdout); update the existing MCP assertions in
`tests/test_create.py` and `tests/test_vsil_v3_subagent.py`. A launcher stdio
round-trip test with a tiny echo server runs on Linux in CI and **must be run
on Windows by hand** before release.

---

## Phase 3 — Docs

- `CLAUDE.md`: global layout, `runtime` / `python` / `mcp` commands in "How
  they connect", `init/mcp.py` description, the self-containment trade-off.
- Repo `AGENTS.md` and `templates/AGENTS/TEMPLATE_AGENT.md`: command list.
- `methodology/test/README.md`: install procedure (`codeanvil runtime sync`,
  `codeanvil mcp add marconi`).

## Phase 4 — Release tag

Only after every verification check passes on the final commit.

- **Version `v0.6.0`**: new commands and a changed MCP config format
  (existing projects keep working until `codeanvil mcp enable` rewrites them).
- Bump the same four files as earlier releases (`pyproject.toml`,
  `CLAUDE.md`, `AGENTS.md`, `README.md`), commit
  `docs: bump version to v0.6.0`, rerun both test suites, `git tag v0.6.0`.
- **Confirm with the owner**, then push the commits and the tag and create
  the GitHub release with an upgrade note: run `codeanvil runtime sync` once,
  then `codeanvil mcp enable <name>` in each project that uses an MCP.
- Smoke test the published install with
  `uv tool install --force-reinstall git+https://github.com/dramirezbe/codeanvil-gcpds.git@v0.6.0`
  (the tag, not `main`).

---

## Deferred

| Item | Reason |
|------|--------|
| Replace OS-specific shell steps in skills (hashes, copies) with runtime scripts | Needs its own per-skill review; this plan only builds and proves the runtime |
| Non-Python MCP servers (Node, Rust) | The launcher is generic, but `add` assumes `uv sync`; extend when the first one appears |
| GPU-specific wheels (CUDA, Jetson) in the runtime | Needs per-platform index configuration; decide with the first real user |
| Per-project runtime overlay | Not requested; the global runtime comes first |

## Verification

1. `uv run pytest tests/` and `python3 -m unittest discover -s templates/tests`.
2. Fresh machine flow: `codeanvil init` → `codeanvil runtime list` shows the
   base packages; `codeanvil runtime add psutil` → `codeanvil python` runs a
   script that imports `psutil`; `codeanvil upgrade` keeps `psutil`.
3. In a scaffolded project, G0 runs through `codeanvil python` and prints the
   same report as the direct `python` call.
4. `codeanvil mcp add marconi` → `doctor` clean → `codeanvil create --mcp marconi`
   writes configs with no absolute path → the agent connects through
   `codeanvil mcp run marconi`.
5. Move the project folder; the MCP still starts without regenerating configs.
6. WU-M5: on the dev machine, `codeanvil mcp doctor marconi` reports the
   ABI mismatch before the fix and `ok` after `codeanvil mcp update marconi`.
7. WU-M6 Level 1 passes; Level 2 steps 1–5 are recorded as PASS in
   `methodology/test/mcp_sandbox_probe.md`, including the "nothing became
   global" checks.
8. Steps 2–5 repeated on Windows, including the launcher stdio round trip.

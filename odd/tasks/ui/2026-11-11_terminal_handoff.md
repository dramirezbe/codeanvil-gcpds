# Continue the interactive terminal work on another PC

Work stopped at the user's request on 2026-11-11. The implementation is saved
on `feat/local-terminal-wsl`, based on `main` at release `v0.7.5` (`3082ae6`).
The package version is still 0.7.5. This is a development branch; creating a
new release or merging to main remains pending.

## Resume

```bash
git fetch origin
git switch feat/local-terminal-wsl
git pull --ff-only
uv sync --frozen --extra dev
uv run codeanvil ui
```

Select a CodeAnvil project, open **Terminal**, choose an installed CLI and click
**Start terminal**. **Sandbox mode** defaults to unchecked (normal local config).
Check it before Start to use the existing `codeanvil sandbox` settings recipe.
Stop the process before changing mode. Install/authenticate the chosen CLI on
the new PC independently; account credentials and the local project registry
are not part of the repository.

The committed production frontend already includes xterm. Node/pnpm is needed
only when editing/rebuilding frontend sources, not to run this checkout's UI.

## Saved implementation

| Commit | Behavior | Authored lines |
|--------|----------|----------------|
| `6d45e55` | Shared sandbox context and CLI regression tests | 309 |
| `2e958a3` | Linux/WSL PTY, controlling terminal and owned process group | 441 |
| `98c50a0` | Sessions, cancellation, cleanup and bounded output replay | 295 |
| `d745c1b` | HTTP/WebSocket routes, project/mode validation and shutdown | 439 |
| `1c4712b` | Terminal UI, sandbox checkbox, reattach, styles, tests and bundled assets | 667 |

Generated assets/lockfiles and vendored licenses are excluded from authored
counts. Cohesive units above 400 lines need an explicit size exception if used
as PR slices; no review or PR has been created. Revert consumers before their
dependencies. The [UI plan, L18](2026-11-10_2036_ui.md) records validation and
rollback boundaries.

## Completed validation

- Python regression: **660 passed, 1 skipped**; frontend: **42 passed**.
- TypeScript and production build passed. Vite warns about the 768 kB JS chunk.
- A visible WSLg Chromium window ran real local **Claude Code 2.1.322** in the
  empty live project **Laboratorio de espectro RF**. `Hi` was entered through
  xterm and Claude answered. It ran `codeanvil status` and asked for a cycle;
  no cycle name was supplied, and no report/gate work was performed.
- Normal mode, navigation/reconnection with the same PID, light/dark, explicit
  Stop and checked sandbox startup were verified. Sandbox used
  `--setting-sources project --strict-mcp-config`, with no second model prompt.
- The development wheel/sdist built without Node/pnpm. Global install/init
  preserved DB bytes and launcher edits. An installed-wheel harness verified
  actual PTY keyboard/output and sandbox cleanup in both modes.

The old PC's screenshots, wheel and detailed receipts are under
`/tmp/codeanvil-terminal-acceptance/`; those temporary files do **not** travel
with Git. All product code, tests, assets/licenses, usage docs and the results
above do travel. No credentials or raw Claude session transcript are copied.

## Remaining tasks

- [ ] Repeat the smoke on the new WSL PC: install/authenticate Claude, select a
  disposable project, verify normal/sandbox selection, typing, Ctrl-C, resize,
  switching views and Stop. No further prompt was sent after the successful Hi.
- [ ] Test installed Codex, OpenCode and Pi interactively; their configured
  launchers reuse this PTY but only Claude received a real model prompt here.
- [ ] Review the five implementation commits, then decide merge and version
  bump/release. The published v0.7.5 release does not include this feature yet.
- [ ] Optionally split/lazy-load xterm to reduce the initial frontend bundle.
- [ ] Continue remaining UI work in the main plan: artifact watching/diffs,
  backup history/manifests, contextual runtime/MCP/telemetry workflows, hardware
  gallery and later native packaging. T3/T6 still list their deferred parts.

Native Windows-to-WSL launching (including PowerShell calling WSL) was explicitly
excluded by the user. Native macOS PTY support is also deferred. Sessions exist
in server memory; stopping the server ends owned sessions. This sandbox checkbox
isolates CLI settings, not filesystem permissions.

Normal Claude inherited an existing nonblocking Engram startup-hook warning;
global agent settings were not edited. Under the execution sandbox, delayed
cross-thread asyncio wakeups can hang even a minimal example unrelated to
CodeAnvil. The successful final Python/installed tests ran directly on WSL.

To rerun checks on WSL:

```bash
uv run --extra dev pytest tests templates/tests -q
cd src/codeanvil/UI/frontend
pnpm install --frozen-lockfile
pnpm test
pnpm build
```

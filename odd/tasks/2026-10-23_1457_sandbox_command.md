# codeanvil sandbox — Agent-Isolated Methodology Execution

## Objective

New subcommand `codeanvil sandbox <agent>` that launches an AI coding agent
inside a scaffolded project with only project-local settings visible — no
global skills, MCPs, extensions, or memory. The agent sees only
`AGENTS.md`, `.agents/skills/`, and the project's GT. Ephemeral — no state
to revert. Branch: `feat/sandbox-command`.

Test runner: `uv run pytest tests/ -q`

## Specs

### S1 — CLI subcommand and dispatch

`codeanvil sandbox <agent>` where `<agent>` is one of: `claude`, `pi`,
`opencode`, `codex`. Must run from inside a scaffolded project (detect
`.codeanvil/project.yaml`). Exits with an error and a helpful message if:
- not inside a project
- agent binary not found on PATH
- unknown agent name

```
codeanvil sandbox claude
codeanvil sandbox pi
codeanvil sandbox opencode
codeanvil sandbox codex
```

### S2 — Claude Code isolation

Launch: `claude --setting-sources "project"`

Native flag — no HOME trick, no temp dirs, no cleanup. The flag loads only
project-level settings (CLAUDE.md → AGENTS.md) and ignores user/local
settings.

### S3 — Pi isolation

Launch:
```bash
pi --no-extensions --no-mcp --no-skills --no-prompt-templates --no-themes \
   -e ~/.pi/agent/npm/node_modules/pi-claude-bridge/src/index.ts
```

Native flags disable all global extensions, MCP servers, skills, prompt
templates, and themes. AGENTS.md discovery stays ON (no `--no-context-files`)
because the project's AGENTS.md IS the methodology contract.

`pi-claude-bridge` must be re-enabled — without it Pi cannot talk to Claude.
All other extensions (gentle-pi, gentle-engram, opencode-pi, pi-web-access,
pi-btw) are stripped for isolation.

Pi extensions on this machine (2026-10-23):
- `pi-claude-bridge` — model access (REQUIRED)
- `opencode-pi` — OpenCode integration (stripped)
- `gentle-pi` — Gentle AI (stripped)
- `gentle-engram` — Engram memory (stripped)
- `pi-web-access` — web browsing (stripped)
- `pi-btw` — BTW (stripped)

The config carries a `required_extensions` list so the command auto-discovers
the paths from `pi list` output or the config.

### S4 — OpenCode isolation

OpenCode follows XDG conventions. Config lives at `~/.config/opencode/`
(opencode.json with agents, providers, plugins, MCPs). Auth is server-side
(uses `opencode` provider with free models) — no local API keys to preserve.

Sandbox: override `XDG_CONFIG_HOME` to an empty temp dir + `--standalone`:

```bash
sandbox_dir=$(mktemp -d)
XDG_CONFIG_HOME="$sandbox_dir" opencode --standalone
rm -rf "$sandbox_dir"
```

This blocks `~/.config/opencode/opencode.json` (full config, plugins, MCPs)
without needing any auth file copies. The `--standalone` flag gives a private
server.

OpenCode directories (none needed in sandbox):
- `~/.opencode/bin/` — binary only
- `~/.config/opencode/` — config + plugins (BLOCKED by XDG override)
- `~/.local/state/opencode/` — session, model prefs, prompt history
- `~/.local/share/opencode/` — SQLite DB, logs, snapshots
- `~/.cache/opencode/` — binary cache, npm

### S5 — Codex isolation

Codex supports `CODEX_HOME` to override its config directory (`~/.codex/`):

```bash
sandbox_dir=$(mktemp -d)
mkdir -p "$sandbox_dir"
# Copy only auth/installation_id — no skills, hooks, memories, config
cp ~/.codex/installation_id "$sandbox_dir/" 2>/dev/null || true
CODEX_HOME="$sandbox_dir" codex --no-daemon
rm -rf "$sandbox_dir"
```

Codex global dir has: `config.toml`, `hooks.json`, `skills/`, `plugins/`,
`AGENTS.md`, memory DBs, logs. The sandbox copies only the installation
identity.

### S6 — Config-driven agent definitions

Agent sandbox recipes go in `templates/config.yaml` under a new
`sandbox_agents` key:

```yaml
sandbox_agents:
  claude:
    binary: claude
    strategy: native       # native flags, no temp dir
    args: ["--setting-sources", "project"]
  pi:
    binary: pi
    strategy: native
    args: ["--no-extensions", "--no-mcp", "--no-skills",
           "--no-prompt-templates", "--no-themes"]
    required_extensions: ["pi-claude-bridge"]  # re-enabled with -e
  opencode:
    binary: opencode
    strategy: xdg_redirect   # empty XDG_CONFIG_HOME, no auth needed
    env_var: XDG_CONFIG_HOME
    args: ["--standalone"]
  codex:
    binary: codex
    strategy: env_redirect   # CODEX_HOME override
    env_var: CODEX_HOME
    args: ["--no-daemon"]
    auth_files: ["installation_id"]
```

Three strategies: `native` (flags only — Claude, Pi), `xdg_redirect`
(empty XDG_CONFIG_HOME — OpenCode), `env_redirect` (CODEX_HOME override +
copy installation_id — Codex).

### S7 — Implementation: src/codeanvil/CLI/commands/sandbox.py

New module with `cmd_sandbox(agent: str)`:

1. Verify cwd is a scaffolded project (`find_manifest()` or
   `.codeanvil/project.yaml` exists).
2. Look up agent in `CONFIG["sandbox_agents"]`.
3. Verify binary exists on PATH (`shutil.which()`).
4. Based on strategy:
   - `native`: `subprocess.run([binary] + args)`. For Pi, resolve
     `required_extensions` paths and append `-e <path>` for each.
   - `xdg_redirect`: create temp dir, run with `<env_var>=<tmp>`,
     cleanup on exit (try/finally). No auth files to copy.
   - `env_redirect`: create temp dir, copy `auth_files` from the
     agent's config dir, run with `<env_var>=<tmp>`, cleanup on exit.
5. Exit with the agent's exit code.

### S8 — Parser registration

Add `sandbox` subcommand to `src/codeanvil/CLI/parser.py`:
- Positional `agent` argument (choices from config keys)
- Wire to `cmd_sandbox` in `main.py`

### S9 — Tests

- `test_sandbox_rejects_outside_project`: run from a non-project dir → error.
- `test_sandbox_rejects_unknown_agent`: `codeanvil sandbox foo` → error.
- `test_sandbox_requires_agent_binary`: mock `shutil.which` → None → error.
- `test_sandbox_subcommand_in_help`: `codeanvil --help` shows `sandbox`.
- `test_sandbox_claude_uses_native_flags`: verify constructed command for
  claude strategy.
- `test_sandbox_opencode_creates_temp_dir`: verify HOME redirect creates
  and cleans up.

### S10 — README update

Update `methodology/test/README.md`:
- Replace the manual `claude --setting-sources "project"` and
  `pi --no-extensions ...` commands with `codeanvil sandbox claude` and
  `codeanvil sandbox pi`.
- Keep the manual commands as documentation of what sandbox does internally.
- Add a section explaining the two modes (sandbox vs. normal).

### S11 — CLAUDE.md and AGENTS.md updates

- `CLAUDE.md`: add `sandbox` to the CLI subcommand list and description.
- `templates/AGENTS/TEMPLATE_AGENT.md`: no change — sandbox is a tool
  concern, not a methodology concern. The scaffolded project doesn't know
  or care how the agent was launched.

## NOT touched

- Gate skills, GT templates, custody-chain — methodology is unchanged.
- `codeanvil create` — sandbox is a separate concern from scaffolding.
- MCP server lifecycle — sandbox disables MCP loading at the agent level,
  not at the server level.

## Tasks

| ID | Spec | Route | Status | Commit |
|----|------|-------|--------|--------|
| T1 | S6 | inline | done | c4001ce |
| T2 | S7 | inline | done | c4001ce |
| T3 | S8 | inline | done | c4001ce |
| T4 | S2, S3, S4, S5 | inline | done | c4001ce |
| T5 | S9 | inline | done | c4001ce |
| T6 | S10 | inline | done | c4001ce |
| T7 | S11 | inline | done | c4001ce |
| T8 | S1 | inline | done | c4001ce |

## Log

**L1** (user, 2026-10-23): User proposed sandboxed agent execution from a
pasted OpenCode idea (HOME redirect + `--standalone`). Confirmed intent:
methodology testing in isolation, not gatekeeping normal use. "the idea is to
test sandboxed (raw, fresh) or methodology."

**L2** (exploration, 2026-10-23): Checked all four agents' CLI flags:
- Claude Code: `--setting-sources "project"` (native, documented)
- Pi: `--no-extensions --no-mcp --no-skills --no-prompt-templates --no-themes
  --no-context-files` — richest native isolation. `--no-context-files` must
  NOT be used (it hides AGENTS.md). Current README re-enables extensions;
  pure sandbox should not.
- OpenCode: `--standalone` only. `~/.opencode/` has only `bin/` — auth
  location unclear; HOME trick may not even need auth copy.
- Codex: `CODEX_HOME` env var overrides `~/.codex/`. Global dir has
  config.toml, hooks.json, skills/, plugins/, AGENTS.md, memory DBs.
  `--no-daemon` disables background daemon.

**L3** (decision, 2026-10-23): Three strategies: `native` (flags),
`home_redirect` (temp HOME), `env_redirect` (env var for config dir).
Config-driven via `templates/config.yaml` so adding agents later is just
a YAML entry.

**L4** (implementation, 2026-10-23): Implemented all tasks T1-T8 on branch
`feat/sandbox-command`. Notes:
- S6 config gained `config_dir: "~/.codex"` for the codex recipe — the
  `env_redirect` strategy needs a source dir to copy `auth_files` from;
  spec S6 YAML didn't include it but S5 implies it (`~/.codex/`).
- `_build_command()` handles `required_extensions` for any agent, not just
  Pi — config-driven, no agent-name special-casing in code.
- Spec S9 says "verify HOME redirect" for the opencode test; the actual
  strategy is `xdg_redirect` (XDG_CONFIG_HOME, per S4) — test follows S4.
- RED observed: `ImportError: cannot import name 'sandbox'` (13 tests).
  GREEN: 13/13 sandbox tests, full suite 141 passed.
- CLI error paths verified live (not just mocked): outside project → 1,
  unknown agent → 2 (argparse choices), missing binary → 1.
- TEMPLATE_AGENT.md untouched per S11.

# Bug: `codeanvil mcp add` does not wire the server into existing projects

**Filed:** 2026-11-18  
**Component:** `src/codeanvil/init/mcp.py`  
**Severity:** usability bug — silent failure, user has to know to run `mcp enable` manually

## Problem

When a project is scaffolded **without** `--mcp` and the user later runs
`codeanvil mcp add <server>` globally, the server installs to
`~/.codeanvil-config/mcp/<server>/` but **no per-project config files are
generated**. The project has no `.mcp.json`, no `.claude/settings.json`, no
`.vscode/mcp.json`, and no MCP skills — so `codeanvil sandbox claude` launches
without the server, and the agent has no tools.

The user must discover and run `codeanvil mcp enable <server>` inside the
project directory to fix it. Nothing in the `mcp add` output suggests this.

## Expected behaviour

After `codeanvil mcp add <server>`, if the user is inside a scaffolded project
(`.codeanvil/project.yaml` exists), the command should either:

1. **Auto-enable** the server in the current project (write `.mcp.json`,
   settings, skills, manifest), or
2. **Print a clear next-step message**: `Server installed. Run 'codeanvil mcp
   enable <server>' inside your project to wire it up.`

Option 1 is the better UX — `mcp add` already knows the project context from
`find_manifest()`. The global install + project wiring should be one operation
when a project is present.

## Reproduction

```bash
codeanvil create --name "Test"
cd test/
# no --mcp during create
codeanvil mcp add vsil_hil_mcp    # installs globally, no project files
codeanvil sandbox claude           # MCP tools missing
# fix:
codeanvil mcp enable vsil_hil_mcp  # NOW it works
```

## Fix scope

- `cmd_mcp()` in `CLI/commands/mcp.py`: after a successful `add`, check if cwd
  is inside a project. If so, call the same `enable` logic automatically.
- If not inside a project, print the `mcp enable` hint.
- No change to `mcp enable` itself — it already works correctly.

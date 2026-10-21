# UI — future feature

This package is a placeholder for a planned graphical interface for CodeAnvil.

It is **not implemented yet**. `ui.py` is intentionally empty.

Nothing in the CLI, scaffold, or database layer depends on this package. It
exists only to reserve the module path for future work.

## Planned scope

The GUI is a **management and access surface** for CodeAnvil projects — not an
agent runtime.

### What it will do

- Create projects
- Search projects
- View a project's reports, configs, and audits
- Open a project directly in an external editor or coding agent
  (VS Code, VSCodium, Codex, Claude, Pi, OpenCode)
- Show application logs

### What it will NOT do

- No built-in chat
- No agent runs

Agent orchestration and execution stay with the harness (the coding-agent
runtime), never inside CodeAnvil. The GUI only launches those external tools;
it does not embed or drive them.

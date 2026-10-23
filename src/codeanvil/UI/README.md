# UI — future feature

This package is a placeholder for a planned graphical interface for CodeAnvil.

It is **not implemented yet**. `ui.py` is intentionally empty.

Nothing in the CLI, scaffold, or database layer depends on this package. It
exists only to reserve the module path for future work.

## Planned scope

The GUI is a **management and access surface** for CodeAnvil projects, with a
terminal-mirroring agent chat and a FastAPI backend.

### Architecture

- **Monolith deployment**: backend opens the frontend — single process, one
  `codeanvil ui` command.
- **Backend**: FastAPI (Python). Serves the frontend, exposes WebSocket
  endpoints for terminal I/O and agent communication.
- **Frontend → Backend**: WebSocket connection for real-time bidirectional
  communication (terminal streams, agent messages, status updates).
- **PTY mirroring**: the backend allocates a real PTY (via `pty` stdlib) that
  mirrors the user's terminal into the frontend. The agent runtime
  (OpenCode, Pi, Claude, Codex) runs inside this PTY — the frontend is a
  live window into the same session the agent sees.
- **Shell detection**: detects the user's shell (bash, zsh, fish) from
  `$SHELL` and spawns the PTY with the correct interpreter, preserving
  environment, prompt, and rc files.

### What it will do

- Create projects
- Search projects
- View a project's reports, configs, and audits
- Open a project directly in an external editor or coding agent
  (VS Code, VSCodium, Codex, Claude, Pi, OpenCode)
- Show application logs
- **Agent chat**: a chat panel in the UI that mirrors the agent's terminal
  session. The user types in the frontend, the agent executes in the PTY,
  and output streams back over WebSocket in real time. This is not a
  separate chat — it is the real terminal, rendered in the browser.
- **Execute via WebSocket**: commands and agent interactions travel over the
  WebSocket to the PTY — no REST polling, no stdin pipe hacks.

### What it will NOT do

- No standalone agent runtime — the UI mirrors an external agent session,
  it does not replace it.
- No custom LLM integration — agent orchestration stays with the harness
  (the coding-agent runtime). The UI displays and relays, never interprets.

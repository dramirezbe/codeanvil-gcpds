# Codex sandbox authentication cache

Branch: `fix/codex-sandbox-auth`, based on released v0.9.0 / main.
Status: fixed, locally installed as 0.9.1; publication not performed.

User report: “El sandbox de codex me pide iniciar sesión. Revisa dónde se guardan las
credenciales para copiarlas o algo así cuando se ejecute codex en sandbox”.

## Cause and change

The recipe copied installation_id but omitted auth.json. Local inspection confirmed a
file-backed auth cache at ~/.codex/auth.json, without reading its contents into tool output.
Codex CLI 0.169.1 consequently lost its login when CODEX_HOME redirected to a temporary home.

Add auth.json to the explicit recipe allowlist and copy it before redirecting CODEX_HOME.
Honor an already configured CODEX_HOME; otherwise use ~/.codex. Create copied files privately
(0600 on POSIX), even if source permissions are loose. The temporary home remains private
and is removed on normal exit, preparation failure and child failure. Global settings,
instructions, skills, MCP and history remain excluded. No change to OS sandbox permissions.

The auth cache is a temporary snapshot, not a bidirectional credential sync. Changes in that
snapshot are discarded on exit; the normal credential file is not overwritten. Keyring-only
authentication is not exported. No API inference call or V-SIL stage was executed for this fix.

Official reference: https://learn.chatgpt.com/docs/auth#credential-storage

## Verification

- `.venv/bin/python -m pytest -q tests/test_sandbox.py tests/test_sandbox_context.py tests/test_ui_terminal.py`:
  **47 passed, 1 existing FastAPI/httpx deprecation warning** (1.00 s).
- Tests cover the allowlist, private permissions, inherited CODEX_HOME, cleanup on exception,
  unchanged original cache, unchanged parent environment and the shared UI terminal lifecycle.
- Real Codex boundary: normal login status exit 0; `codex --no-daemon login status` under the
  corrected prepare_sandbox context also exited 0, with no global config copied.
- Installed the local candidate with `uv tool install --force-reinstall --python 3.12 .`.
  `codeanvil --version` reports 0.9.1. Repeated the login-status probe using the installed tool's
  Python environment against the existing T0 project: exit 0, temporary credentials removed,
  original auth bytes unchanged. Only booleans/status codes were printed, no credential values.
- `git diff --check`: clean. User's T0 files, reports and cycle were not modified.

## Review and rollback

One work unit: sandbox.py, the Codex recipe, authentication regression tests, 0.9.1 metadata
and README/changelog. Revert this unit to restore the old recipe and copy behavior.
The local install can independently return to the published v0.9.0 tag through uv tool install;
that also restores the reported authentication bug. No PR, push, merge or release tag was made.

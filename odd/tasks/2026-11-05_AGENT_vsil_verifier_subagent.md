# Plan — T9: ship the `vsil-verifier` subagent with every project

Feature: `odd/tasks/2026-11-05_1421_vsil_v3_full_flow.md` · Task T9 · Spec S13 · Contract D11 · Paper P2 (the oracle is not the generator)
Targets: `templates/agents/vsil-verifier.md` (new, the shared body), `templates/config.yaml` (new `subagents:` key), `src/codeanvil/init/create.py` (one new step, about 30 lines), `tests/test_create.py`.
The only task of this feature that changes Python; accepted as an exception to S9 with S13.

## Goal

G2 must not verify in the context that wrote the code. A subagent gives a fresh context in the same session, without asking the user to open another one. `codeanvil create` writes it in each runtime's own format from **one shared body**, so the instructions never drift between runtimes.

## The subagent (body: `templates/agents/vsil-verifier.md`)

About 40 lines, English, plain Markdown with no frontmatter:

- **Role.** Run the evidence of one G2 iteration and report it. You did not write this code and you do not judge the cycle.
- **Input from G2.** Cycle name and declared level per module and `PATH-*`. Nothing else from the calling conversation.
- **Reads.** `.codeanvil/report/<cycle>/S2_artifacts/test_run.md` (the `VL-0` and `VL-1` commands), `S1_artifacts/S1_design.md` §1.6–§1.7 (HAL ladder and telemetry envelope), `GT/G0_SyRS.md` (thresholds, and §6 `PROTO-*` for VL-2).
- **Does.** G2.0: run `VL-0`. G2.1: run `VL-1` when any VL-1 is declared. G2.2: prepare the `PROTO-*` procedure when VL-2 is declared in `mock+real`. Then check every telemetry reading against the §1.7 envelope.
- **Returns.** One table: item, declared level, command, environment, result (pass, fail, `missing test`), telemetry flag; then counts and the exact commands run.
- **Never.** Edit or create source, test or design files; write `G2.md` or any report; ask the human; fix a failure; compute an expected value; report a run that did not happen. Run outputs land only where the `test_run.md` commands themselves write them.

## Per-runtime files (written by `codeanvil create`)

| Runtime | Path | Header around the shared body | Source |
|---------|------|-------------------------------|--------|
| Claude Code | `.claude/agents/vsil-verifier.md` | YAML frontmatter `name: vsil-verifier`, `description`, `tools: Read, Grep, Glob, Bash` (no Edit, no Write) | code.claude.com/docs/en/sub-agents |
| OpenCode | `.opencode/agents/vsil-verifier.md` | YAML frontmatter `description`, `mode: subagent`, `permission: {edit: deny, webfetch: deny, bash: allow}` | opencode.ai/docs/agents |
| Codex | `.codex/agents/vsil-verifier.toml` | `name`, `description`, `sandbox_mode = "workspace-write"` (tests write caches and telemetry files), body in `developer_instructions = """…"""` | Community guide; **verify against official Codex docs first** |

Copilot and Pi get no file: G2 falls back to asking for a fresh session (D11).

## `templates/config.yaml`

```yaml
# Subagents shipped with every project: one shared body, one header per
# runtime. Only runtimes with documented project-scoped subagents are listed.
subagents:
  vsil-verifier:
    body: "templates/agents/vsil-verifier.md"
    description: "V-SIL G2 verifier: runs the S2 test commands in a fresh, read-only context and returns a results table. Use only from the G2 skill."
    targets:
      claude:
        path: ".claude/agents/vsil-verifier.md"
        format: "markdown"
        frontmatter: {name: "vsil-verifier", tools: "Read, Grep, Glob, Bash"}
      opencode:
        path: ".opencode/agents/vsil-verifier.md"
        format: "markdown"
        frontmatter: {mode: "subagent", permission: {edit: "deny", webfetch: "deny", bash: "allow"}}
      codex:
        path: ".codex/agents/vsil-verifier.toml"
        format: "toml"
        fields: {name: "vsil-verifier", sandbox_mode: "workspace-write"}
```

## `create.py`

New `_write_subagents(project_dir)`, called in `scaffold_project` after `_link_agent_configs`. For each target: `markdown` writes `---\n<yaml frontmatter + description>\n---\n\n<body>`; `toml` writes the fields, `description` and `developer_instructions` as a TOML multi-line string. Always overwritten, like `AGENTS.md` (generated, not hand-edited). No new dependency: YAML through `pyyaml`, TOML written by hand (flat string fields only).

## RED tests first

In `tests/test_create.py`, on a scaffolded project:

1. The three files exist at the paths above.
2. The two Markdown files parse as frontmatter + body, and their bodies are byte-identical to `templates/agents/vsil-verifier.md`; the TOML file parses with `tomllib` and its `developer_instructions` equals the same body.
3. The Claude frontmatter `tools` contains neither `Edit` nor `Write`; the OpenCode `permission.edit` is `deny`.
4. Re-scaffolding the same project is idempotent (same bytes).
5. The body names `test_run.md` and contains the "Never" list's `Edit or create source`.

## Check

`codeanvil create` into a `mktemp -d` folder; open it with `codeanvil sandbox claude` and `codeanvil sandbox opencode` and confirm the runtime lists `vsil-verifier` (`/agents` in Claude Code, `opencode agent list` in OpenCode). Remove the scratch folder afterwards.

## Acceptance

1. Claude Code and OpenCode list the subagent in a fresh scaffold.
2. The Codex format is confirmed against official docs, or the Codex target is dropped from `config.yaml` and the fallback covers it.
3. The whole suite passes.

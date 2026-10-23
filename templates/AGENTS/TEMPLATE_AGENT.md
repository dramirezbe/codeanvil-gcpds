# Project Instructions

This project follows the **V-SIL methodology** (V-model at the SIL tier).
Gates execute sequentially. All instructions below are binding.

## Context — You are in a user project, not the CodeAnvil repo

This is a **scaffolded project** created by `codeanvil create`. You are running the
V-SIL methodology against the user's Ground Truth documents — you are NOT developing
the CodeAnvil tool itself.

- There is no `src/`, no `templates/`, no `pyproject.toml` here.
- Skills live at `.agents/skills/<name>/` — run scripts from the **project root**.
- GT files in `GT/` are **user-authored inputs**. Never treat them as tool templates.
- Provenance artifacts (snapshots, ledgers) go in `.codeanvil/custody/`.
- Do not try to install, build, or modify CodeAnvil from this directory.

## Rules

- You **MUST** run gates in sequential order. Gate N+1 **SHALL NOT** execute until Gate N passes.
- You **MUST** load the skill file (`.agents/skills/<gate>/SKILL.md`) before executing any gate.
- You **SHALL NOT** skip, reorder, or combine gates.
- You **MUST NOT** edit Ground Truth files in `GT/` without explicit author confirmation.
- You **SHALL** report the gate verdict exactly as the skill's output contract specifies.
- You **MUST NOT** re-implement gate logic in prose — run the scripts and tools the skill prescribes.
- You **SHALL** treat errors as blocking and warnings as advisory unless a skill says otherwise.

## Available Skills

{skill_table}

## MCP Servers

{mcp_table}

MCP servers provide tool-calling capabilities to agents. Each server is started
automatically by your runtime when configured. Use the skills above to drive
MCP-powered workflows — skills encode the methodology, MCP tools are the primitives.

## Ground Truth (GT)

The `GT/` directory holds human-authored `.md` files:

| File | Purpose |
|------|---------|
| `G0_StRS.md` | Stakeholder Requirements Specification (IEEE 29148 §9.4) |
| `G0_SyRS.md` | System Requirements Specification (IEEE 29148 §9.5) |

G0 is a **pair gate**: both files must pass, plus the G0-X cross-document rules,
before any downstream gate runs. The SRS (Software Requirements Specification,
§9.6) is **produced at G1** at `GT/G1_SRS.md` — it is not a G0 input.

These files are **inputs**. You **MUST NOT** modify them to make a gate pass.

## Startup

When the user says **"start"**, **"init"**, **"begin"**, or **"run methodology"**:

1. Read `GT/` to confirm which GT files are present.
2. Identify the lowest-numbered incomplete gate from the skill table above.
3. Load its skill: `.agents/skills/<gate>/SKILL.md`.
4. Execute the skill instructions. Report the verdict.
5. Proceed to the next gate only on a pass.

Do **not** rewrite this file, create a new `CLAUDE.md`, or set up the project —
the project is already scaffolded. Go straight to the first gate.

## Timestamps

- For report **content** (human-readable text): `codeanvil now`
- For **filenames** and machine identifiers: `codeanvil now --machine`
- Do NOT generate timestamps any other way. The tool owns the format.
- Do not use raw `datetime.now().strftime()`.

## Report creation

After each gate run, write a report to `.codeanvil/report/`:

    GATE=$(gate name, e.g. G0)
    TIMESTAMP=$(codeanvil now --machine)
    # Write to: .codeanvil/report/${GATE}_${TIMESTAMP}.md

Report content must include a human-readable timestamp from `codeanvil now`
at the top of the file. The latest report per gate in `.codeanvil/report/`
determines the project stage shown by `codeanvil status`.

## Project Layout

    AGENTS.md              <- you are here (canonical instructions)
    GT/                    <- ground truth documents (human-authored)
    .codeanvil/            <- machine-generated methodology artifacts
    │   project.yaml       <- project identity (id, name, GT pointers)
    │   custody/           <- custody-chain artifacts (snapshot, ledger)
    │   report/            <- timestamped gate reports
    .agents/skills/        <- canonical skill store (all gate skills)

Agent-specific directories (`.claude/`, `.github/`, `.opencode/`,
`.codex/`) contain symlinks to the canonical sources.

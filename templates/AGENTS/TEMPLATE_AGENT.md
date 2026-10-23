# Project Instructions

This project follows the **V-SIL methodology** (V-model at the SIL tier).
This file is a **reference** — it describes the project, its skills, and its
conventions. It does not orchestrate gates: each skill enforces its own
prerequisite report, so the gate chain lives in the skills. All instructions
below are binding.

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

## On Project Open

**First action on every project open** — before any gate work, before loading a
skill, and before asking the user anything — run:

```bash
codeanvil status
```

This prints the project identity, active cycle, and per-gate HITL verdicts.
Use its output as your orientation: it tells you where the methodology stands
so you do not need to read files or list directories to discover progress.

## Cycle

A **cycle** is one complete run of the V-SIL methodology pipeline against a GT
baseline. Every report belongs to exactly one cycle.

**After running `codeanvil status`**, before any gate work and before loading a
skill, ask the user for a cycle name using your runtime's native question
mechanism (`AskUserQuestion` in Claude Code, the equivalent in other runtimes).
This is mandatory — do not defer it to a "start" command. If `codeanvil status`
already shows an active cycle, offer it as the default choice.

- Offer the cycles that already exist under `.codeanvil/report/` as choices,
  plus the option of a new name.
- If the user selects an existing cycle, resume it: the next gate is the first
  one whose latest iteration is not `HITL: PASS`.
- If the user gives a new name, normalize it to a directory-safe slug:
  1. lowercase;
  2. spaces become `_`;
  3. remove every character except letters, digits, `_`, and `-`;
  4. collapse repeated `_`;
  5. trim leading/trailing `_` and `-`;
  6. prefix the zero-padded sequence number of the new cycle.
- Examples: `"Test SDR USRP IoT Signals"` → `01_test_sdr_usrp_iot_signals`;
  the next cycle `"Websocket Refactor"` → `02_websocket_refactor`.
- Record the selected cycle in `.codeanvil/project.yaml` as `cycle: <name>`.
  Update only that key — never rewrite the rest of the manifest.
- Scope every gate report to `.codeanvil/report/<cycle-name>/<gate>.md`.

Previous cycles are preserved and read-only. To run the methodology again (for
example after a major refactor), start a new cycle: it writes a fresh set of
reports while the old cycles stay untouched.

## Available Skills

{skill_table}

Load a skill when the user asks for its gate or when its trigger applies. The
skill checks its prerequisite report itself:

- prerequisite report missing, or its latest iteration is `HITL: FEEDBACK` →
  the skill stops and tells you which skill to run first;
- prerequisite report's latest iteration is `HITL: PASS` → the skill runs and
  appends its own iteration.

This is a **chain, not orchestration**: nothing in this file sequences gates,
and you must not sequence them from it either.

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

## Report Format

Every gate writes **one** report file: `.codeanvil/report/<cycle-name>/<gate>.md`
(for example `G0.md`, `CC.md`, `G1.md`). Iterations are appended sections in
that file — never separate files. G1 additionally writes its design artifacts
to `.codeanvil/report/<cycle-name>/G1_artifacts/` — working files that are
overwritten on rework, not report iterations.

```markdown
# <Gate Name>

| Field     | Value |
|-----------|-------|
| Gate      | <id> |
| Cycle     | <cycle-name> |
| Document  | <input files> |
| Created   | <codeanvil now> |

---

## Iteration <N>

| Field       | Value |
|-------------|-------|
| Date        | <codeanvil now> |
| Timestamp   | <codeanvil now --machine> |
| Iteration   | <N> |
| Cycle       | <cycle-name> |
| HITL        | PASS | FEEDBACK |

### Description

<content — user feedback, script output, or N/A>
```

Rules:

- Iterations start at `1` and increment on each run.
- `HITL: PASS` means the gate is done. `HITL: FEEDBACK` means iterate.
- There is **no DENIED** state — a rejected result is `FEEDBACK` with the
  user's comments, and the gate re-runs.
- For G0 (deterministic), the Description carries the full script report, and
  script errors force `HITL: FEEDBACK`.
- A gate is complete only when its latest iteration is `HITL: PASS`.

## Timestamps

- For report **content** (human-readable text): `codeanvil now`
- For **filenames** and machine identifiers: `codeanvil now --machine`
- Do NOT generate timestamps any other way. The tool owns the format.
- Do not use raw `datetime.now().strftime()`.

## Folder Reference

| Path | What it holds |
|------|---------------|
| `GT/` | Human-authored Ground Truth. Read-only during gates unless the author approves an edit. |
| `.codeanvil/project.yaml` | Project identity (`id`, `name`, GT pointers) plus the active `cycle`. |
| `.codeanvil/custody/` | Custody-chain artifacts (source snapshot, custody ledger). |
| `.codeanvil/report/<cycle-name>/` | One iterative report per gate, scoped to the cycle. |
| `.codeanvil/report/<cycle-name>/G1_artifacts/` | G1 intermediate design files (ASR, candidates, trade study, etc.). Overwritten on rework. |
| `.agents/skills/` | Canonical skill store — every agent runtime links here. |

## Project Layout

    AGENTS.md              <- you are here (canonical instructions)
    GT/                    <- ground truth documents (human-authored)
    .codeanvil/            <- machine-generated methodology artifacts
    │   project.yaml       <- project identity (id, name, GT pointers, cycle)
    │   custody/           <- custody-chain artifacts (snapshot, ledger)
    │   report/            <- per-cycle gate reports (<cycle-name>/<gate>.md)
    │                          <cycle-name>/G1_artifacts/  <- G1 intermediate design files
    .agents/skills/        <- canonical skill store (all gate skills)

Agent-specific directories (`.claude/`, `.github/`, `.opencode/`,
`.codex/`) contain symlinks to the canonical sources.

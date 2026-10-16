# Project Instructions

This project follows the **V-SIL methodology** (V-model at the SIL tier).
Gates execute sequentially. All instructions below are binding.

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

## Ground Truth (GT)

The `GT/` directory holds human-authored `.md` files:

| File | Purpose |
|------|---------|
| `G0_SRS.md` | System Requirements Specification (IEEE 29148) |
| `G0_HCS.md` | Hardware Constraints Specification (design constraints) |

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

## Project Layout

    AGENTS.md              <- you are here (canonical instructions)
    GT/                    <- ground truth documents (human-authored)
    .agents/skills/        <- canonical skill store (all gate skills)

Agent-specific directories (`.claude/`, `.github/`, `.opencode/`,
`.codex/`) contain symlinks to the canonical sources.

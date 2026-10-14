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
| `requirements.md` | System Requirements Specification (IEEE 29148) |
| `hw_restrictions.md` | Hardware Constraints Specification (design constraints) |
| `normativity.md` | Applicable standards (ITU, ICNIRP, IEEE, etc.) |

These files are **inputs**. You **MUST NOT** modify them to make a gate pass.

## Workflow

1. Read the GT in `GT/` to understand the project contract.
2. Execute the lowest-numbered incomplete gate.
3. Load its skill: `.agents/skills/<gate>/SKILL.md`.
4. Follow the skill instructions. Report the verdict.
5. Proceed to the next gate only on a pass.

## Project Layout

    AGENTS.md              <- you are here (canonical instructions)
    GT/                    <- ground truth documents (human-authored)
    .agents/skills/        <- canonical skill store (all gate skills)

Agent-specific directories (`.claude/`, `.github/`, `.opencode/`,
`.codex/`) contain symlinks to the canonical sources.

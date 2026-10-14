# Plan: AGENTS.md Template + Config-Driven Scaffold

**Status:** PLANNED

## Context

Scaffolded projects have skills symlinked for Claude/OpenCode/Codex, but no root instruction file telling agents what the project is, what skills exist, or the hard rules for working in it. Currently, skills and symlink paths are hardcoded in `create.py`.

**Goal:** A YAML config as the single source of truth, a template that generates `AGENTS.md` with dynamic skill listing and hard agent instructions, and symlinks/pointers so every agent finds it.

## Agent ecosystem conventions (as of 2026-10)

| Agent / Tool | Instruction files read | Skills directory | Notes |
|--------------|----------------------|------------------|-------|
| **AGENTS.md** (AAIF/Linux Foundation) | `AGENTS.md` at root | `.agents/skills/` | Cross-tool standard. |
| **Claude Code** | `CLAUDE.md`, `AGENTS.md` (v2.1.277+) | `.claude/skills/` | Symlink `CLAUDE.md -> AGENTS.md` safest for all versions. |
| **GitHub Copilot** (Chat/Workspace/Review) | `AGENTS.md` + `CLAUDE.md` + `GEMINI.md` + `.github/copilot-instructions.md` — **all additive** | `.github/skills/*/SKILL.md` | Copilot CLI does **not** read any. `COPILOT.md` is fictional. Reads all files additively — symlinks cause **duplicate context**. |
| **Antigravity CLI** (ex-Gemini CLI) | `AGENTS.md`, `.agents/AGENTS.md`, `GEMINI.md` (fallback) | `.agents/skills/` (official) | Gemini CLI dead June 2026. `.gemini/AGENTS.md` was never a convention. |
| **OpenCode** | `AGENTS.md` | — | Reads root AGENTS.md. |
| **Codex** | `AGENTS.md`, `AGENTS.override.md`, configurable fallbacks | — | No documented `.codex/skills/` auto-discovery. |

### Key insight: Copilot triple-read risk

Copilot reads `AGENTS.md` + `CLAUDE.md` + `.github/copilot-instructions.md` **additively**. If all three resolve to the same content, the same instructions load 3 times, wasting context budget. Fix: `.github/copilot-instructions.md` must be a **one-line pointer file**, not a symlink.

## What exists and works

| Component | File | Status |
|-----------|------|--------|
| `scaffold_project()` | `src/codeanvil/init/create.py` | Works — copies skills, GT, rewrites paths, creates symlinks |
| `_link_agent_skill_dirs()` | `src/codeanvil/init/create.py` | Works — hardcoded `[".claude/skills", ".opencode/skills", ".codex/skills"]` |
| Skill frontmatter | `templates/skills/*/SKILL.md` | G0 has full YAML frontmatter, G1 is empty |
| `pyproject.toml` | repo root | No dependencies, hatch force-include for templates |

## New files

### 1. `templates/config.yaml`

Single source of truth for skills, agent symlinks, and template path:

```yaml
skills:
  G0_valid_req_and_GT:
    project_dir: ".agents/skills/G0_valid_req_and_GT"
    template_dir: "templates/skills/G0_valid_req_and_GT"
  G1_start_design:
    project_dir: ".agents/skills/G1_start_design"
    template_dir: "templates/skills/G1_start_design"

# Skill directory symlinks — agent runtimes that discover skills
# via a directory convention.
agent_skill_links:
  # Claude Code — native skill discovery
  ".claude/skills": "../.agents/skills"
  # GitHub Copilot — native skill discovery at .github/skills/
  ".github/skills": "../.agents/skills"
  # Antigravity — reads .agents/skills/ directly (no symlink needed,
  # it's the canonical path), but kept for completeness
  # OpenCode / Codex — no documented skill discovery, harmless symlinks
  ".opencode/skills": "../.agents/skills"
  ".codex/skills": "../.agents/skills"

# Instruction file symlinks — point agent-specific config files
# to the canonical AGENTS.md.
# Only include conventions that real tools actually read.
agent_config_links:
  # Claude Code — symlink, safest for all versions (pre/post v2.1.277)
  "CLAUDE.md": "AGENTS.md"

# Instruction pointer files — written as one-line references to AGENTS.md
# instead of symlinks, to avoid duplicate context loading in agents
# that read multiple instruction files additively.
agent_pointer_files:
  # Copilot reads AGENTS.md + CLAUDE.md + copilot-instructions.md
  # additively. A symlink would triple-load the same content.
  ".github/copilot-instructions.md": "See [AGENTS.md](../AGENTS.md) for project instructions."

  # REMOVED — no tool reads these:
  #   "COPILOT.md"          — fictional convention, nothing reads it
  #   ".gemini/AGENTS.md"   — Gemini CLI is dead; Antigravity reads
  #                           root AGENTS.md natively; Gemini read
  #                           GEMINI.md at root, not .gemini/AGENTS.md

  # OPTIONAL legacy fallback (uncomment if needed):
  #   "GEMINI.md": "See AGENTS.md for project instructions."

agents_template: "templates/AGENTS/TEMPLATE_AGENT.md"

gt_reference_templates:
  - "G0_SRS.md"
  - "G0_HCS.md"
```

### 2. `templates/AGENTS/TEMPLATE_AGENT.md`

Hard instructions (MUST, SHALL, DO NOT) + `{skill_table}` placeholder:

```markdown
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
```

## Changes to existing files

### `pyproject.toml`

- Add dependency: `dependencies = ["pyyaml"]`
- Add force-include entries for `templates/config.yaml` and `templates/AGENTS/`

### `src/codeanvil/init/create.py`

**Remove hardcoded constants:** `AGENT_SKILL_DIRS`, `G0_SKILL_NAME`, `GT_REFERENCE_TEMPLATES`. Replace with config-driven loading.

**New: `_load_config() -> dict`** — reads `templates/config.yaml` via `yaml.safe_load`.

**New: `_parse_skill_frontmatter(skill_md) -> dict | None`** — regex extracts `---` block, `yaml.safe_load` parses it. Returns `{name, description, gate}` or `None` for empty SKILL.md.

**New: `_collect_skill_summaries(skills_root) -> list[dict]`** — globs `*/SKILL.md`, parses frontmatter, returns sorted `[{gate, name, description}]`.

**New: `_generate_agents_md(project_dir) -> None`** — reads `TEMPLATE_AGENT.md`, builds skill table from summaries, writes `AGENTS.md` with `{skill_table}` replaced.

**New: `_link_agent_configs(project_dir) -> None`** — iterates `CONFIG["agent_config_links"]` for symlinks + `CONFIG["agent_pointer_files"]` for one-line pointer files.

**Modified: `_link_agent_skill_dirs`** — reads from `CONFIG["agent_skill_links"]` instead of `AGENT_SKILL_DIRS`.

**Modified: `_copy_gt_reference_templates`** — reads template list from `CONFIG["gt_reference_templates"]`.

**Modified: `scaffold_project()`** — adds `_generate_agents_md()` and `_link_agent_configs()`:

```python
def scaffold_project(name, target):
    ...
    _copy_skills(project_dir)
    _copy_gt_reference_templates(project_dir)
    _rewrite_skill_paths(project_dir / SKILLS_DIRNAME)
    _create_gt_dir(project_dir)
    _generate_agents_md(project_dir)     # NEW
    _link_agent_skill_dirs(project_dir)
    _link_agent_configs(project_dir)     # NEW
    ...
```

## Resulting scaffolded layout

```
myproj/
├── AGENTS.md                                    <- canonical (generated)
├── CLAUDE.md -> AGENTS.md                       <- symlink (Claude Code)
├── .github/
│   ├── copilot-instructions.md                  <- pointer file (not symlink)
│   └── skills/ -> ../.agents/skills             <- Copilot skill discovery
├── GT/
│   └── README.md
├── .agents/skills/                              <- canonical (Antigravity native)
│   ├── G0_valid_req_and_GT/
│   └── G1_start_design/
├── .claude/skills -> ../.agents/skills
├── .opencode/skills -> ../.agents/skills
└── .codex/skills -> ../.agents/skills
```

**What each agent sees:**
- **Claude Code** — reads `CLAUDE.md` (symlink → AGENTS.md), discovers skills via `.claude/skills/`
- **Copilot** — reads `AGENTS.md` + `CLAUDE.md` + `.github/copilot-instructions.md` (pointer, no duplication), discovers skills via `.github/skills/`
- **Antigravity** — reads `AGENTS.md`, discovers skills via `.agents/skills/` (canonical path)
- **Codex** — reads `AGENTS.md`, skill discovery via AGENTS.md content
- **OpenCode** — reads `AGENTS.md`, skill discovery via AGENTS.md content

## Verification

1. `codeanvil create test_cfg -p /tmp` — scaffold
2. Check `AGENTS.md` has G0 in the skill table (G1 absent — empty SKILL.md)
3. Verify `CLAUDE.md` is a symlink: `readlink CLAUDE.md` → `AGENTS.md`
4. Verify `.github/copilot-instructions.md` is a **file** (not symlink) with pointer content
5. Verify `.github/skills/` is a symlink: `readlink .github/skills` → `../.agents/skills`
6. Confirm no `COPILOT.md` or `.gemini/` directory exists
7. Edit `templates/config.yaml` to add a test skill → re-scaffold → verify it appears
8. Copy T0 GT files, run `claude -p` → verify agent picks up instructions and runs G0
9. `uv pip install -e .` and repeat to test wheel path resolution

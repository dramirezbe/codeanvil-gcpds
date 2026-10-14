# Feature: AGENTS.md Template + Config-Driven Scaffold

**Plan:** `plans/agents_md_template.md` (PLANNED → IN PROGRESS)
**Branch:** `feat/agents-md-template`
**Route:** delegated direct (writer trigger: 4 files — `templates/config.yaml`, `templates/AGENTS/TEMPLATE_AGENT.md`, `src/codeanvil/init/create.py`, `pyproject.toml`)
**TDD:** off — no test runner exists for `src/` (only `templates/tests/` for the G0 script shipped to projects). Verification = functional scaffold checks from the plan.
**Delivery strategy:** `ask-on-risk`; forecast ≈ 250 authored changed lines (< 400) → single slice, no split expected.

## Objective

Single source of truth (`templates/config.yaml`) for skills, symlinks, and pointers; generate a root `AGENTS.md` from `TEMPLATE_AGENT.md` with a dynamic skill table; wire every agent runtime to it without duplicate-context loading (Copilot pointer file, not symlink).

## Scope

- New: `templates/config.yaml`, `templates/AGENTS/TEMPLATE_AGENT.md`
- Modified: `src/codeanvil/init/create.py`, `pyproject.toml`
- Out of scope: changes to GT docs, G0 validator logic, installer, DB schema.

## Constraints / decisions

1. Plan says remove `AGENT_SKILL_DIRS`, `G0_SKILL_NAME`, `GT_REFERENCE_TEMPLATES`. **Gap:** `G0_SKILL_NAME` is also used by `_create_gt_dir()` for `GT_README.format(skill=...)`. Resolution: add explicit config key `g0_skill: "G0_valid_req_and_GT"` (deterministic, no frontmatter coupling).
2. Config paths like `templates/AGENTS/TEMPLATE_AGENT.md` are repo-root-relative: resolve as `TEMPLATES_DIR.parent / <config path>` (works for editable and wheel layouts).
3. Skill table rows come only from skills with YAML frontmatter (G0 yes, G1 empty → absent), sorted by gate; use the skill **directory name** for the load path.
4. `templates/config.yaml` and `templates/AGENTS/` must be force-included in wheel + sdist, plus `dependencies = ["pyyaml"]`.

## Tasks

- [x] T1 — Created `templates/config.yaml` (plan §1 + `g0_skill` key) + `templates/AGENTS/TEMPLATE_AGENT.md`
- [x] T2 — `pyproject.toml`: `dependencies = ["pyyaml"]`; force-include config + AGENTS template (wheel + sdist)
- [x] T3 — `create.py`: `_load_config`/`CONFIG`, `_parse_skill_frontmatter`, `_collect_skill_summaries`, `_skill_table`, `_generate_agents_md`, `_link_agent_configs`; config-driven `_link_agent_skill_dirs`, `_copy_gt_reference_templates`, `_create_gt_dir`; constants removed; scaffold order per plan
- [x] T4 — Verification PASSED (writer run + independent parent re-run):
  - scaffold via `PYTHONPATH=src ... scaffold_project` → exit 0
  - AGENTS.md skill table: G0 present, G1 absent (empty frontmatter); untracked `custody-chain` skill also listed (gate `-`) — correct dynamic behavior
  - `CLAUDE.md -> AGENTS.md` symlink ✓; `.github/skills -> ../.agents/skills` ✓
  - `.github/copilot-instructions.md` is a regular file with pointer content ✓
  - no `COPILOT.md`, no `.gemini/` ✓
  - config-edit propagation: temp `agent_skill_links` entry scaffolded, then reverted ✓
  - `uv build --wheel`: wheel contains `codeanvil/templates/config.yaml` + `codeanvil/templates/AGENTS/TEMPLATE_AGENT.md` ✓
  - CLI path: blocked by pre-existing `codeanvil init` DB preflight (environmental, out of scope)

## Progress

- [x] Exploration + route decision
- [x] T1–T3 delegated to writer (general) — status partial only due to pre-existing/environmental items below
- [x] T4 verification: writer self-verification + parent spot-check re-run; risk assess = medium, under budget (328 changed lines, review_due false)
- [x] Work-unit commit (see Evidence)

## Evidence

- Writer task `ses_ec415ce8affeH7HGr4pb8SraIf`: checks 1–7 PASS; 8b PASS (`uv build --wheel`); 8a FAIL = **pre-existing** sdist→wheel hatch flaw (proven at HEAD via stash); 9 = DB preflight (needs `codeanvil init`, environmental)
- Parent re-run: full scaffold + all link/pointer/table checks PASS (2026-10-14)
- Known follow-ups (not this feature): (a) sdist force-include breaks wheel-from-sdist at HEAD — fix by dropping the sdist force-include table; (b) template GT table lists `requirements.md`/`hw_restrictions.md`/`normativity.md` while `GT/README.md` says `SRS.md`/`HCS.md` — pre-existing doc inconsistency
- Unexpected untracked `templates/skills/custody-chain/` appeared mid-session (14:53, not created by this feature's writer) — left uncommitted, owner's call

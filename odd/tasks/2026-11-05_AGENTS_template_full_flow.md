# Plan — T10: the generated `AGENTS.md` follows the full flow

Feature: `odd/tasks/2026-11-05_1421_vsil_v3_full_flow.md` · Task T10 · Specs S5, S9, S11, S12, S13, S14, S15, S16 · Contracts C1, C2, C10, D2, D7–D11
Targets: `templates/AGENTS/TEMPLATE_AGENT.md` (the user-project instructions), `tests/test_create.py`. Second part: this repo's `AGENTS.md` and `README.md` (developer documentation).
Runs after T7 (the S2 and G2 texts are final) and before T8 (the end-to-end run reads the generated file).

## Goal

The template stays a **passive reference** (C10): it describes, it never orchestrates. It must stop contradicting the refactor (today line 15 says "There is no `src/`, no `templates/`, no `pyproject.toml` here", which S2 makes false). The fix is to delete the Context section, not to rewrite it (S15): the agent needs only `codeanvil status` at session start, the skills and `GT/`. Detail stays in the skills; the template points to them.

## Changes to `TEMPLATE_AGENT.md`, section by section

| Section | Change |
|---------|--------|
| Header | "V-SIL v3"; the chain named once: S0 → G0 → S1 → G1 → S2 → G2, RFD outside it. |
| Context | **Removed entirely** (S15). The agent is never told that a CodeAnvil repository, its `src/` or its `templates/` exist, and no sentence contrasts "this project" with "the tool". The word CodeAnvil appears nowhere; only the `codeanvil` CLI is named. |
| On Project Open | Keeps `codeanvil status` as the first action of every session. Adds two lines: the `codeanvil` CLI is available and is the only tool for project state and timestamps (`codeanvil status`, `codeanvil now`, `codeanvil now --machine`); how each step works is in the skills under `.agents/skills/`, and what the project must do is in `GT/` (S15). |
| Rules | Chain list becomes `(S0, G0, S1, G1, S2, G2)`. Three new rules: only S2 writes code under `src/` and `verification/` (reworks included); G2 and the `vsil-verifier` subagent never edit code; delivered code under `src/` never imports or calls `codeanvil` and never depends on `verification/` (D2, D10). |
| Available Skills | `{skill_table}` already lists S2 and G2 after T5. RFD paragraph: raised from S1, G1 or G2; S2 only records `Possible infeasibility` for G2 (paper §9.2). One new paragraph on routing: `Verdict: design defect` (from S2 or G2) returns to S1, `Verdict: module defect` (from G2) returns to S2 (D6). |
| **Subagents (new)** | `vsil-verifier` is generated in `.claude/agents/`, `.opencode/agents/` and `.codex/agents/`. Only the G2 skill uses it, to run the verification commands in a fresh, read-only context. In a runtime without subagents, run G2 in a fresh session. Never use it for anything else, and never edit its files (they are regenerated). |
| Ground Truth | `G0_SyRS.md` §4–§6 hold the lab inputs (procedures as `PROTO-*`, correction chains, tolerances), optional: `Not applicable: no lab inputs in the Build Package.` when the Build Package has none (D9). |
| Software | **No section** (S16). The code layout, toolchain, `run.sh` commands, deploy and logger rules live only in the S2 skill and its `references/`. |
| Report Format | The id list adds `S2.md`, `G2.md`. Working folders add `S2_artifacts/` (`test_run.md`) and `G2_artifacts/` (`verified_prototype.md`, the cycle's terminal output). Rule on `Based on`: "Every iteration of G0, S1, G1, S2 and G2" (moved here from T4). |
| Timestamps | Scoped to reports and filenames. Delivered code formats its own log timestamps through its `config/logger`; it never calls `codeanvil`. |
| Folder Reference | New rows only for what the scaffold or the reports create: `S2_artifacts/`, `G2_artifacts/`, `.claude/agents/` · `.opencode/agents/` · `.codex/agents/`. No rows for `src/`, `verification/`, the manifests, `cmd/` or `daemon/` (S16). |
| Project Layout | The tree adds `S2_artifacts/`, `G2_artifacts/` and the agent folders; no `src/`, `verification/` or manifests (S16). Last sentence: runtime directories hold symlinks to `.agents/skills/` **and** the generated `vsil-verifier` files. |

Length budget: the template stays about the size of today's (202 lines), give or take 15. Nothing from the skills is copied in: each new item is one or two lines plus a pointer.

## Second part: developer docs of this repo

Not user-facing, same task so they cannot drift:

- `AGENTS.md`: the Context paragraph (a scaffolded project has no `src/` **until S2**); the overview diagram drops "S2, G2 (planned — not implemented yet)"; `## Gate details` gains short S2 and G2 entries and the `vsil-verifier` subagent; `## Gate chain` lists S2 and G2; `## Scaffolded project structure` adds `.claude/agents/`, `.opencode/agents/`, `.codex/agents/` and the S2/G2 skill folders, and notes `src/`, `verification/` and the manifests as created by S2.
- `README.md`: "What you get in the scaffolded project" lists the same.

## RED tests first

In `tests/test_create.py`, on a scaffolded project's `AGENTS.md`:

1. New `test_agents_md_describes_the_full_flow`: contains `S2_artifacts/`, `G2_artifacts/`, `verified_prototype.md`, `vsil-verifier`, `fresh session`, `Verdict: design defect`, `Verdict: module defect` and `Not applicable: no lab inputs in the Build Package.`
2. Same test, negatives: no `There is no \`src/\``, no `(and later S2, G2)`, no `not available in this release`, no `## Context`, no `## Software`, no `CodeAnvil` (case-sensitive: the lowercase CLI name `codeanvil` stays), no `templates/`, no `pyproject.toml`, no `run.sh`.
3. Positives for S15: `codeanvil status`, `codeanvil now`, `.agents/skills/` and `GT/` appear in `## On Project Open`.
4. `test_agents_md_is_a_passive_reference` stays unchanged and green (no orchestration added).
5. `test_agents_md_skill_table_shows_the_prerequisite_chain` gains the S2 and G2 rows (T5 already adds them; checked again here).

## Check

`codeanvil create` into a `mktemp -d` folder, read the generated `AGENTS.md` top to bottom once, and confirm every path it names exists after scaffold or is marked "created by S2". Remove the scratch folder afterwards.

## Acceptance

1. No sentence in the generated `AGENTS.md` contradicts D2, D9, D10 or D11, and none mentions a CodeAnvil repository (S15).
2. The template still orchestrates nothing (C10).
3. The repo's `AGENTS.md` and `README.md` describe S2, G2 and the subagent as implemented.
4. The whole suite passes.

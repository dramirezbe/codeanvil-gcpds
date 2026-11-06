# Plan — CHAIN: switch the scaffold to the v3 chain

Feature: `odd/tasks/2026-11-04_1042_vsil_v3_skill_flow.md` · Task T6 · Specs S4, S6 · Contracts C0, C1, C3
Commit together with T5, because `tests/test_create.py` pins the old chain. Runs after T1–T4 so the new skill directories exist.

## Goal

Make `codeanvil create` scaffold the v3 chain. This is config and text except for one Python line. The only other tool change is `codeanvil status` (T10).

## Changes

| File | Change |
|------|--------|
| `templates/skills/custody-chain/` | `git mv` to `templates/backups/custody-chain/` (S6) |
| `templates/skills/G1_start_design/` | `git mv` to `templates/backups/G1_start_design/` (A2) |
| `templates/GT/G1_SRS.md` | `git mv` to `templates/backups/G1_SRS.md` (A2) |
| `templates/config.yaml` `skills` | Chain below; delete `custody-chain` and `G1_start_design` |
| `templates/config.yaml` | Add `s0_skill: "S0_normalise_build_package"`. Delete `g1_skill`, `g1_reference_templates` and the `templates/GT/G1_SRS.md` path replacement. Keep the `.provenance/` entry (unused, ready for when custody returns) |
| `src/codeanvil/init/create.py:72` | Replace `("g1_skill", "g1_reference_templates")` with `("s0_skill", "gt_reference_templates")`, so S0 and G0 each get their own blueprints (C10). Left as is, `CONFIG["g1_skill"]` raises `KeyError` |
| `pyproject.toml:29` | Drop the `G1_SRS.md` `force-include`. `templates/backups/` is not force-included, so wheels do not ship it |
| `src/codeanvil/CLI/parser.py:38-44` | Epilog: drop the SRS line; describe the flow as S0 → G0 → S1 → G1 → S2 → G2 |
| `templates/GT/README.md.template`, `templates/GT/README.md` | Add `build_package.md` as the input; drop the `G1_SRS.md` paragraph |
| `templates/AGENTS/TEMPLATE_AGENT.md` | See below |

```yaml
skills:
  S0_normalise_build_package:
    project_dir: ".agents/skills/S0_normalise_build_package"
    template_dir: "templates/skills/S0_normalise_build_package"
    prerequisite: null
  G0_valid_req_and_GT:
    project_dir: ".agents/skills/G0_valid_req_and_GT"
    template_dir: "templates/skills/G0_valid_req_and_GT"
    prerequisite: "S0"
  S1_design_services:
    project_dir: ".agents/skills/S1_design_services"
    template_dir: "templates/skills/S1_design_services"
    prerequisite: "G0"
  G1_design_review:
    project_dir: ".agents/skills/G1_design_review"
    template_dir: "templates/skills/G1_design_review"
    prerequisite: "S1"
```

S2 and G2 are added here when T8 and T9 exist. RFD stays out on purpose.

## `TEMPLATE_AGENT.md` edits

| Line | Today | Becomes |
|------|-------|---------|
| 18 | Provenance artifacts go in `.codeanvil/custody/` | Delete |
| "MUST NOT edit GT" rule | Absolute | Exception: "the S0 skill writes `G0_StRS.md` and `G0_SyRS.md` from `build_package.md`" |
| Rules | "gates" | "stages and gates", still sequential |
| New section | — | One line on `RFD_request_for_deviation`: can be raised from any stage |
| 110 | SRS produced at G1 | Delete; S1 produces the design in `S1_artifacts/` |
| GT table | StRS, SyRS | Add `build_package.md`, which S0 reads |
| 117-119 | `G0.md`, `CC.md`, `G1.md`, `G1_artifacts/` | `S0.md`, `G0.md`, `S1.md`, `G1.md`, `RFD.md`, and `<ID>_artifacts/` |
| 172, 174, 183, 185 | Custody and G1 artifacts rows | Delete the custody rows; point artifacts at `S1_artifacts/` and `RFD_artifacts/` |
| 57 | Resume at the first gate not at PASS | Same rule, in chain order, plus: "Load that skill; its prerequisite check sends you to the right step. A cycle `codeanvil status` shows as closed is not resumed." |
| 152 | `HITL: PASS` means the gate is done | Add: "On a stage (S0, S1, S2), PASS means the output was delivered; the human verdict belongs to the next gate." |
| Report Format schema | No `Based on` | Description starts with `Based on: <predecessor id> iteration <N>`, except in S0 and RFD (C11) |

## `tests/test_create.py`

| Lines | Change |
|-------|--------|
| 329-333 | `test_config_declares_skill_prerequisite_chain`: S0 → G0 → S1 → G1 |
| 384-397 | `test_agents_md_skill_table_shows_the_prerequisite_chain`: same chain and order, RFD `-` |
| 404-409 | `test_g0_skill_writes_an_iterative_report`: per T5 |
| 412-417 | Delete `test_custody_skill_requires_a_passing_g0_report` |
| 420-425 | Replace by the G1 test in T1 |
| 428-436 | Rewrite for `S1_artifacts/S1_design.md` |

**New regression test:** `codeanvil create` does not produce `.agents/skills/custody-chain` or `.agents/skills/G1_start_design`, and `AGENTS.md` does not mention `custody-chain`, `CC.md` or `G1_SRS`.

**New regression test (C10):** in a scaffold, no `.md` or `.html` file under `.agents/skills/<skill>/` contains a path into `.agents/skills/<another skill>/`, or `methodology/`. The S1 graph output's script path points into S1's own folder, so it passes.

`tests/test_sync.py` and `tests/test_paths.py` keep their custody assertions: the folder and migration stay.

## Differential check before finishing

Run `codeanvil status`, `sync`, `list`, `now` and `create` from a base-commit copy in a `mktemp -d` folder and from the change, and compare stdout, stderr and exit code. Only `create`'s output and the `--help` epilog should differ; `status` is compared separately in T10. `sync` and `now` must be identical (S11).

## Docs (same delivery, last slice)

`CLAUDE.md` (skills list, flow, tree), `AGENTS.md`, `README.md:55-59,140-151,219-227`, `methodology/test/README.md` (T7). Add `templates/backups/` to the tree with a one-line reason.

## Risk

Item 3: changes the generated `AGENTS.md`, the shipped config, and removes skills from scaffolds. **Already-scaffolded projects keep working**, because they hold their own copy of the skills.

## Acceptance

Full suite green, no change to `sync.py`, `now`, `sandbox`, `mcp.py` or `db/`; a wheel build scaffolds the same tree as an editable install.

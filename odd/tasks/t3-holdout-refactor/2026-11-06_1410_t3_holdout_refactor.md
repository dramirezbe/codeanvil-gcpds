# T3 Holdout Refactor Plan

## Context

The T3 full-flow run (2026-11-05) produced the holdout
`methodology/test/T3_FM-mock/S1_G1_review_holdout_2026-11-05.md`. The
placeholder layer, sandwich verification and the entry-point contract
(S1 §0.5, G1.15, S2 smoke test, G2 check) are already applied. This plan
implements the remaining proposals.

**Execution order (owner decision, 2026-11-06):**

```
Phase 1 Renames → Phase 2 Backups (codeanvil backup + skill step) → Phase 3 Layout CLI code → Phase 4 Skill logic → Phase 5 Docs → Phase 6 Release tag (v0.5.0)
```

Renames come first so that every later edit is written once, against the
final paths. Backups come before any change to a skill's internal logic, so
the bounded-rework protocol (Phase 4) can rely on them. Backups are a CLI
command (`codeanvil backup`), so its code and the skill step that calls it
land together in Phase 2: a skill never names a command that does not exist.
The remaining CLI code for the new layout follows in Phase 3.

The owner wants **all methodology-owned artifacts under `.codeanvil/`**: GT,
design, backups, reports and project metadata.

### Deliberate deviations from the holdout

| Holdout proposal | This plan | Reason |
|------------------|-----------|--------|
| `GT/` and `design/` at the project root | `.codeanvil/GT/` and `.codeanvil/design/` | Owner decision: one methodology tree |
| Optional `GT/SRS.md` | Deferred | No T3 evidence that a distinct SRS adds detail beyond SyRS |
| Reader-facing `reports/<cycle>/verified_prototype.md` + `validation_levels.md` | `verified_prototype.md` stays in `report/<cycle>/G2_artifacts/`; `validation_levels.md` deferred | Keeps this refactor bounded |

## Target project layout

```
project/
├── AGENTS.md
├── .codeanvil/
│   ├── GT/                         ← was project-root GT/
│   │   ├── README.md
│   │   ├── build_package.md
│   │   ├── StRS.md                 ← was G0_StRS.md
│   │   └── SyRS.md                 ← was G0_SyRS.md
│   ├── design/                     ← was report/<cycle>/S1_artifacts/
│   │   ├── SDD.md                  ← was S1_design.md
│   │   └── dependency_graph.html   ← was S1_graph.html
│   ├── backups/                    ← written only by `codeanvil backup`
│   │   └── <producing-cycle>/      ← or unknown/
│   │       ├── S0_iter<N>/{StRS.md, SyRS.md, MANIFEST.yaml}
│   │       ├── S1_iter<N>/{SDD.md, dependency_graph.html, MANIFEST.yaml}
│   │       ├── S2_iter<N>/{test_run.md, MANIFEST.yaml}
│   │       └── G2_iter<N>/{verified_prototype.md, MANIFEST.yaml}
│   ├── report/<cycle>/             ← gate reports; never backed up (append-only)
│   │   ├── S0.md … G2.md
│   │   ├── S2_artifacts/test_run.md
│   │   └── G2_artifacts/verified_prototype.md
│   └── project.yaml
├── .agents/skills/…
├── src/          (S2 creates)
└── verification/ (S2 creates)
```

- `.codeanvil/design/` is a single working copy. Each cycle's S1.md/G1.md
  records the SHA-256 of the SDD it produced or reviewed, so S2/G2 can detect
  a design changed after G1 approved it.
- Locked blueprints keep their own paths:
  `.agents/skills/{S0,G0}_…/templates/StRS.md` and `SyRS.md`. The skills must
  name both paths in full so an agent never writes into a blueprint.
- **Existing projects are not migrated.** A project scaffolded before this
  change finishes its current cycle on the old paths; this plan adds no
  `codeanvil migrate`. The archived T3 snapshot under `methodology/test/T3_FM-mock/`
  stays untouched as historical evidence.

## Step 0 — Baseline

Commit the pending S2 placeholder/sandwich change and its holdout entry as a
separate commit before Phase 1, so the refactor starts from a clean tree.

---

## Phase 1 — Renames (paths, folders, file names)

Only path and name changes. No behaviour change in any skill.

### WU-R1: GT relocation + rename

`GT/G0_StRS.md` → `.codeanvil/GT/StRS.md`, `GT/G0_SyRS.md` → `.codeanvil/GT/SyRS.md`,
`GT/build_package.md` → `.codeanvil/GT/build_package.md`.

| File | What changes |
|------|-------------|
| `templates/skills/S0_normalise_build_package/SKILL.md` | Description, compatibility, inputs, outputs, blueprint names |
| `templates/skills/G0_valid_req_and_GT/SKILL.md` | Inputs, template refs (`templates/GT/StRS.md`) |
| `templates/skills/G0_valid_req_and_GT/references/RULES.md` | Template paths |
| `templates/skills/S1_design_services/SKILL.md` | Inputs, compatibility |
| `templates/skills/S1_design_services/references/S1_design.md` | Header, source doc refs |
| `templates/skills/G1_design_review/SKILL.md` | Inputs, `sha256sum` targets |
| `templates/skills/G1_design_review/references/G1_CHECKLIST.md` | Source doc refs |
| `templates/skills/S2_implement_services/SKILL.md` | Inputs |
| `templates/skills/G2_adaptive_verification/SKILL.md` | Inputs |
| `templates/agents/vsil-verifier.md` | Input path |
| `templates/AGENTS/TEMPLATE_AGENT.md` | GT rule (line 15–16), §GT table, layout tree |
| `templates/GT/README.md`, `templates/GT/README.md.template` | All refs |
| `templates/config.yaml` | `gt_reference_templates: [StRS.md, SyRS.md]`; `path_replacements` keys and values |
| `templates/tests/test_g0_validate.py` | `TEMPLATE_STRS` / `TEMPLATE_SYRS` and messages |
| `templates/tests/requirements.txt` | Comment ref |

Then rename the files: `templates/GT/G0_StRS.md` → `templates/GT/StRS.md`,
`templates/GT/G0_SyRS.md` → `templates/GT/SyRS.md`.

`g0_validate.py` needs no change: it takes the paths as arguments and detects
the document type from the first `##` heading.

### WU-R2: Design relocation + rename

`report/<cycle>/S1_artifacts/S1_design.md` → `.codeanvil/design/SDD.md`,
`S1_graph.html` → `.codeanvil/design/dependency_graph.html`.

| File | What changes |
|------|-------------|
| `templates/skills/S1_design_services/SKILL.md` | Outputs, "Working files live in…" rule, template copy steps, graph edit step |
| `templates/skills/G1_design_review/SKILL.md` | Inputs |
| `templates/skills/G1_design_review/references/G1_CHECKLIST.md` | Refs |
| `templates/skills/S2_implement_services/SKILL.md` | Inputs |
| `templates/skills/G2_adaptive_verification/SKILL.md` | Inputs |
| `templates/agents/vsil-verifier.md` | Input path |
| `templates/AGENTS/TEMPLATE_AGENT.md` | Tree, artifact refs |
| `templates/GT/README.md.template` | `S1_artifacts` ref |

Then rename the files:
`references/S1_design.md` → `references/SDD.md`,
`references/S1_graph_template.html` → `references/dependency_graph_template.html`
(and its internal `S1_` ref).

### Phase 1 tests

Update the assertions that pin skill text or template names:
`tests/test_create.py` (S1_artifacts lines 513, 524 and the GT refs),
`tests/test_vsil_v3_s0.py`, `tests/test_vsil_v3_s1.py`,
`tests/test_vsil_v3_agents_md.py`.

**Known intermediate state:** after Phase 1 the scaffold still creates
project-root `GT/` and writes the old manifest pointers (fixed in Phase 3).
Do not release between Phase 1 and Phase 3.

---

## Phase 2 — Backup protocol (`codeanvil backup`)

Backups are deterministic tool code, not agent judgement: copying files,
hashing them and computing `<N>` by hand would depend on the agent and the OS
(`cp`/`Copy-Item`, `sha256sum`/`Get-FileHash`). Like `codeanvil status`, the
command only **reads** reports; it copies files but never decides or advances
a gate, so the rule "the tool does not drive gates" still holds. Skills
already depend on the CLI (`codeanvil status`, `codeanvil now`).

### WU-B1: Shared report parser

Move `ReportState`, `_report_state()`, `_cycle_reports()`, `_gate_order()` and
the report regexes from `src/codeanvil/CLI/commands/status.py` to a new
`src/codeanvil/reports.py`. `status` imports them from there; no behaviour
change. `backup` must not import from another command module.

**Tests**: existing `status` tests pass unchanged.

### WU-B2: `codeanvil backup <stage>`

`<stage>` is one of `S0`, `S1`, `S2`, `G2`.

1. **Targets.** Read from a new `config.yaml` key, the single source of truth:

   ```yaml
   backup_targets:
     S0: [".codeanvil/GT/StRS.md", ".codeanvil/GT/SyRS.md"]
     S1: [".codeanvil/design/SDD.md", ".codeanvil/design/dependency_graph.html"]
     S2: [".codeanvil/report/{cycle}/S2_artifacts/test_run.md"]
     G2: [".codeanvil/report/{cycle}/G2_artifacts/verified_prototype.md"]
   ```

   `{cycle}` is the active cycle from `.codeanvil/project.yaml`.
2. **Producer.** Resolve the cycle and iteration that produced the files:
   - the latest iteration of `<stage>.md` in the active cycle; otherwise
   - (new cycle) the cycle whose latest `RFD.md` iteration says
     `Superseded by cycle: <active>`, and its latest `<stage>.md` iteration;
     otherwise
   - `unknown`, written to `backups/unknown/<stage>_<machine-timestamp>/`.

   Do not guess "the previous cycle" from ordering: `_cycle_reports` sorts
   cycles by name, not by date.
3. **Write.** Copy the existing targets to
   `.codeanvil/backups/<producing-cycle>/<stage>_iter<N>/` and write
   `MANIFEST.yaml`: per file its source path and SHA-256, plus the producer
   (cycle, stage, iteration or `unknown`), the active cycle and `Created`
   from `format_timestamp()`.
4. **Idempotent.**
   - No target exists → print `nothing to back up`, exit 0.
   - The latest backup of that stage has the same digests → print
     `already backed up: <path>`, exit 0.
   - Never overwrite an existing backup folder. If the folder exists with
     different digests, exit nonzero: it signals a file edited outside the
     flow, and the skill stops for the human.
5. **Errors.** Any failure (no manifest, no active cycle for S2/G2, I/O error)
   → short diagnostic, exit nonzero.
6. **Output.** One line with the backup path, so the agent can cite it in
   the stage report.

**Files**:
- `src/codeanvil/CLI/commands/backup.py` (new), `commands/__init__.py`
- `src/codeanvil/CLI/parser.py` (subcommand + help), `src/codeanvil/CLI/main.py` (dispatch)
- `src/codeanvil/config/paths.py` (`PROJECT_BACKUPS`)
- `templates/config.yaml` (`backup_targets`)

**Tests** (new `tests/test_backup.py`): producer from the active cycle;
producer across an RFD supersede; `unknown` fallback; idempotent repeat;
nothing to back up; existing folder with different digests → nonzero;
`MANIFEST.yaml` content. `tests/test_cli.py`: add `backup` to
`EXPECTED_SUBCOMMANDS` and a `--help` guard.

### WU-B3: `codeanvil status` shows backups

After each cycle's gates, one line per stage with its latest backup path, e.g.
`  Backups: S1 iteration 1 → .codeanvil/backups/<cycle>/S1_iter1/`.
**Tests**: extend the `status` tests.

### WU-B4: Backup step in every overwriting skill

One instruction in S0, S1, S2 and G2 `SKILL.md`, immediately before the step
that writes the target:

> Before overwriting, run `codeanvil backup <stage>` from the project root.
> If it exits nonzero, stop and show its message; write no iteration.
> Cite the printed backup path in the iteration's Description.

| Stage | When the skill runs it |
|-------|------------------------|
| S0 | Before writing the GT pair (any iteration, any cycle) |
| S1 | Before writing the design (any iteration, **including iteration 1 of a new cycle**) |
| S2 | Before overwriting `test_run.md` on rework |
| G2 | Before overwriting `verified_prototype.md` |

The command is a no-op when nothing exists, so the skills call it
unconditionally. **Scope limit:** backups do not cover `src/` or
`verification/`; code recovery relies on git. Each skill states this in one
line. `TEMPLATE_AGENT.md` adds `codeanvil backup <stage>` to its command list
(line 37).

**Tests**: one assertion per skill that `codeanvil backup <stage>` and the
stop-on-failure rule appear; `tests/test_vsil_v3_agents_md.py` for the
command list.

---

## Phase 3 — CLI code that accompanies the new layout

### WU-C1: Paths and scaffold

| File | What changes |
|------|-------------|
| `src/codeanvil/config/paths.py` | Add `PROJECT_GT`, `PROJECT_DESIGN` (`PROJECT_BACKUPS` lands in WU-B2); fix comment line 16 ("GT stays at the project root") |
| `src/codeanvil/init/create.py` | `_create_gt_dir` writes `.codeanvil/GT/` — call it **after** `_create_codeanvil_dirs` or use `parents=True` (today it runs first, line 73–74); `_create_codeanvil_dirs` adds `design/` and `backups/` and drops the "never under .codeanvil/" docstring; `write_project_manifest` points to `.codeanvil/GT/StRS.md`, `.codeanvil/GT/SyRS.md` |
| `src/codeanvil/CLI/parser.py` | Help text lines 31, 40–41 |
| `src/codeanvil/CLI/commands/sandbox.py` | Docstring GT ref only |

`codeanvil status` needs no layout change: it reads only `report/<cycle>/*.md`
(its backup line comes from WU-B3).

**Tests**: `tests/test_paths.py` (new constants), `tests/test_create.py`
(layout), `tests/test_sync.py:133` (manifest `gt`).

---

## Phase 4 — Skill logic

### WU-L1: G2 prerequisite split by verdict

G2 `SKILL.md` prerequisite 3 (line 33) returns `S2 must rework first` for any
unchanged FEEDBACK. Split it:
- `Verdict: module defect` → `S2 must rework first. Run the S2 skill.`
- `Verdict: design defect` → `S1 must rework first. Run the S1 skill.`

No extra S1 check is needed: once S1/G1 advance, prerequisite 2 already
blocks a stale S2.
**Tests**: `tests/test_vsil_v3_g2.py` asserts both strings.

### WU-L2: Bounded rework — S1 and G1

**S1 on rework** (the old baseline is the folder printed by
`codeanvil backup S1`, cited in the iteration):
1. Emit a **design change set** in S1.md: per changed `SYS-*`, contract,
   service, module or `PATH-*` ID: old decision, new decision, reason,
   interface-changed flag. A graph-only change is marked "no code impact".
2. Keep stable IDs for unchanged elements.
3. Record the SDD digest.

**G1 on rework**:
1. Review the change set; trace each changed contract to producers,
   consumers, stubs and tests along the §2.2 DAG.
2. Produce an **impact map**: files to edit vs paths to retest only.
3. An unexplained impact is an open finding (new checklist row).

**Files**: S1 `SKILL.md`, G1 `SKILL.md`, `G1_CHECKLIST.md`.
**Tests**: `tests/test_vsil_v3_s1.py`, `tests/test_vsil_v3_g1.py`.

### WU-L3: S2 design-defect rework

Depends on WU-L2.
- Inputs table (line 43): add the latest G1 PASS iteration's impact map as a
  rework input, next to `G2.md` `module defect`.
- New rework paragraph: revise the affected contract and stub first, then
  the owning module (unit, bottom-up, sandwich), then replace the stub.
  Preserve unaffected modules. Rerun affected `PATH-*` and changed VL-1
  tests, then the full VL-0 floor. S2.md records changed IDs, files,
  commands, results and the G2 iteration it answers.

**Tests**: `tests/test_vsil_v3_s2.py`.

### WU-L4: S2 pause schedule

Ask at the start of every S2 iteration, with the native question tool (English
text, like every other skill):

| Option | Pauses |
|--------|--------|
| Per layer and module | Per service: after kit+base, after each module and its tests, after integration |
| Per layer (recommended) | Per service: after kit+base, once after all modules, after integration |
| Per service | Once after each completed service |

For all options, add one pause after cross-service integration, before the
`PATH-*` tests. At each pause the user picks `continue`, `rework` or `stop`.
Answers are recorded as checkpoint lines in the iteration's Description, not
as gate verdicts. `stop` writes no iteration; the "Resume, do not restart"
rule picks up from `src/` on the next run.

**Decide before implementing** (proposed defaults above): recommended option,
ask on every iteration vs once per cycle.
**Tests**: `tests/test_vsil_v3_s2.py`, `tests/test_gate_questions.py`.

### WU-L5: Module-level subagents (optional)

Depends on WU-L4.
- Parent owns kit, bases, contracts, integration and the pause schedule.
- A module subagent gets one module and its contract, implements it, runs
  unit + bottom-up + sandwich tests, and returns: changed files, commands run,
  and pass/fail per test.
- Parallel only for modules whose DAG dependencies are ready and whose files
  do not overlap. Default concurrency 1. S2 must work without subagents.

**Files**: S2 `SKILL.md`.

### WU-L6: Ready-to-use telemetry collector

- New `templates/skills/S2_implement_services/references/telemetry_collector.py`,
  locked like the loggers. **Proposed: stdlib only** (`/proc`, `/sys/class/thermal`,
  `/proc/device-tree/model` for RPi/Jetson; other OSes report `unavailable`).
- Records timestamp, host profile, process/system CPU and memory, temperature
  when available, measurement source, collector version.
- Application counters (dropped buffers, queue depth, scheduling latency) are
  read from HAL/service instrumentation; never invented.
- Missing data → `unavailable` with a reason, never zero. JSON lines, one file
  per VL run. Quiet; nonzero exit on error.
- S2 copies it unchanged; `project_layout.md` (lines 109, 124, 154) replaces
  the self-written "telemetry companion" with the collector.
- G2 rejects a constant or placeholder reading as measured evidence.

**Files**: collector (new), S2 `SKILL.md`, `project_layout.md`, G2 `SKILL.md`.
**Tests**: new `tests/test_telemetry_collector.py` (no codeanvil import,
`unavailable` instead of zero, JSON-lines schema), like the logger tests.
**Decide before implementing**: stdlib only vs `psutil`.

---

## Phase 5 — Docs

- `CLAUDE.md`: trees, GT and design paths, S1/G2 descriptions, the
  `codeanvil backup` line in "How they connect", `CLI/commands/` list and
  the new `src/codeanvil/reports.py` module.
- Repo `AGENTS.md`: 14 old-path refs.
- `methodology/test/README.md`: test procedure paths.
- Do not edit the archived T3 snapshot, `templates/backups/`,
  `templates/no-tools-skills/` or `templates/GT/legacy/`.

---

## Phase 6 — Release tag

Only after every check in **Verification** passes on the final commit.

**Version: `v0.5.0`.** The scaffold layout changes in a breaking way (GT and
design move under `.codeanvil/`, the GT files are renamed, and there is a new
`codeanvil backup` command), and old projects are not migrated. Before 1.0,
a breaking change bumps the minor version.

1. Bump the version in the same four files as the v0.4.4 bump (`48eb834`):
   `pyproject.toml` (`version = "0.5.0"`), `CLAUDE.md` (current-release
   link), `AGENTS.md`, `README.md`. Commit:
   `docs: bump version to v0.5.0`.
2. Re-run `uv run pytest tests/` and
   `python3 -m unittest discover -s templates/tests` on that commit.
3. Tag it the same way as the earlier releases (lightweight, like
   `v0.4.4`): `git tag v0.5.0`.
4. **Confirm with the owner first**, then push the commits and the tag
   (`git push origin main v0.5.0`) and create the GitHub release. The release
   notes include a breaking-changes section: the new layout, the renamed
   files, `codeanvil backup`, and "existing projects finish their current
   cycle on the old paths".
5. Smoke test the published install: run `codeanvil upgrade`, then
   `codeanvil create --name "Release Smoke"` produces the new layout.

---

## Deferred

| Item | Reason |
|------|--------|
| VL-2 M2M interface | Future `mock+real` cycle |
| MCP telemetry facade | Needs its own design; the CLI collector comes first |
| `validation_levels.md` and reader-facing `reports/` | Later G2 enhancement |
| Optional `SRS.md` | No evidence it is needed yet |
| `codeanvil migrate` for old projects | Old projects finish their cycle on old paths |
| Retire `.codeanvil/custody/` | `sync.py` `_migrate_provenance` still targets it and `test_create.py` asserts it, so retire them together |
| `codeanvil list --missing` / prune for registry rows whose path is gone | 8 of 10 rows on the dev machine point at missing paths (checked 2026-11-06); there is no removal command, so a stale row can only be cleared by hand |

---

## Verification

After each phase:

1. `uv run pytest tests/`
2. `python3 -m unittest discover -s templates/tests`

After Phase 2, in a scratch project with a fake S1 report and design:

- `codeanvil backup S1` creates `.codeanvil/backups/<cycle>/S1_iter1/` with
  `MANIFEST.yaml`; a second run prints `already backed up`; `codeanvil status`
  shows the backup line.

After Phase 3:

3. `codeanvil create --name "Test Refactor"` produces `.codeanvil/GT/`,
   `.codeanvil/design/`, `.codeanvil/backups/`, the new manifest pointers and
   no project-root `GT/`.
4. In that project, `python -I .agents/skills/G0_valid_req_and_GT/scripts/g0_validate.py .codeanvil/GT/StRS.md .codeanvil/GT/SyRS.md`
   runs on files written from the blueprints.

After Phase 5:

5. Old-path grep returns zero hits (138 today):

   ```bash
   grep -rnE "G0_(StRS|SyRS)|S1_design\.md|S1_graph|S1_artifacts|(^|[^./A-Za-z_])GT/" \
     templates/ src/ tests/ AGENTS.md CLAUDE.md methodology/test/README.md \
     --exclude-dir=backups --exclude-dir=no-tools-skills --exclude-dir=legacy \
     --exclude-dir=__pycache__
   ```

   The regex excludes `.codeanvil/GT/`, `templates/GT/` and the
   `S1_design_services` / `G0_valid_req_and_GT` folder names.
6. Every `SKILL.md` input/output path matches the target layout.

---

## Log

- **2026-11-06 — Phase 1 complete** (`954c3f9`): GT pair moved to `.codeanvil/GT/StRS.md` and
  `SyRS.md`; design moved to `.codeanvil/design/SDD.md` and `dependency_graph.html`; repo
  templates renamed to `templates/GT/StRS.md`, `templates/GT/SyRS.md`,
  `references/SDD.md`, `references/dependency_graph_template.html`; every skill, agent template,
  test and `pyproject.toml` force-include updated. Evidence: 228 pytest + 97 unittest green.
- **2026-11-06 — Phase 2 complete.** WU-B1 moved the report parser to
  `src/codeanvil/reports.py`. WU-B2 added `codeanvil backup S0|S1|S2|G2`
  (`CLI/commands/backup.py`, `backup_targets` in `templates/config.yaml`, `PROJECT_BACKUPS`),
  producer resolution (active cycle → RFD supersede → `unknown`), idempotency and
  `MANIFEST.yaml`. WU-B3 prints the latest backup per stage in `codeanvil status`. WU-B4 adds the
  backup step to S0, S1, S2 and G2 and the command to `TEMPLATE_AGENT.md`. Evidence: 244 pytest +
  97 unittest green; scratch project: first run created `.codeanvil/backups/01_run/S1_iter1/`
  with `MANIFEST.yaml`, second printed `already backed up`, and `status` printed
  `Backups: S1 iteration 1 → .codeanvil/backups/01_run/S1_iter1/`.
- **Next:** Phase 3 (WU-C1 paths and scaffold), then Phase 4 (WU-L4 and WU-L6 decisions are open).
- **2026-11-06 — Phase 3 complete.** `PROJECT_GT` and `PROJECT_DESIGN` added; `create` now writes
  `.codeanvil/GT/` (README only), `.codeanvil/design/`, `.codeanvil/backups/` and no project-root
  `GT/`; the manifest points to `.codeanvil/GT/StRS.md` and `.codeanvil/GT/SyRS.md`; parser help
  text updated. Evidence: 246 pytest + 97 unittest green; scratch `create --name "Test Refactor"`
  produced the new tree with no root `GT/`, and `g0_validate.py` passed (exit 0) on a real GT pair
  placed at `.codeanvil/GT/`.
- **Next:** Phase 4 — ask the owner the two open decisions (WU-L4 pause schedule, WU-L6 telemetry
  collector dependency) before implementing those units.
- **2026-11-06 — Phase 4, WU-L1–L3 complete.** G2 prerequisite 3 splits the unchanged-code stop by
  verdict (`module defect` → S2, `design defect` → S1). S1 writes a bounded design change set and
  the final `SDD.md` digest; G1 reviews the change set, records the reviewed digest and produces an
  impact map, with new checklist row G1.16. S2 takes the latest G1 PASS impact map as a rework
  input and works contract+stub → module → stub, preserving unlisted modules. Evidence: 251 pytest
  + 97 unittest green.
- **Next:** WU-L4 and WU-L6 wait on the owner's decisions recorded below.
- **2026-11-06 — WU-L4–L6 complete.** Owner decisions: pause schedule default **Per layer**, asked
  at the start of **every** iteration; the telemetry collector may use dependencies, so it uses
  **psutil** (CPU, memory and Linux temperature) and reports every psutil metric as `unavailable`
  with a reason when psutil is missing. S2 gained a `## Pause Schedule` section (three options, one
  extra pause after cross-service integration and before the `PATH-*` tests, `continue|rework|stop`
  recorded as checkpoint lines, `stop` writes no iteration) and a `## Module Subagents` section
  (parent keeps kit, bases, contracts, integration and pauses; one module per subagent; default
  concurrency 1; S2 works without subagents). The locked `references/telemetry_collector.py` writes
  JSON lines per VL run (timestamp, host profile, process and system CPU/memory, temperature,
  measurement source, collector version, and counters copied from `--counters`), stays quiet and
  exits nonzero on I/O errors; `project_layout.md` and the S2/G2 skills now use it, and G2 rejects a
  constant or placeholder reading. `psutil` joined the repo dev extra and the project kit dev group.
  Evidence: 267 pytest + 97 unittest green; manual runs showed `measurement_source: unavailable`
  under system python3 and `psutil` with a Tctl temperature under the venv.
- **Next:** Phase 5 docs (`CLAUDE.md`, repo `AGENTS.md`, `methodology/test/README.md`) and the
  old-path grep.
- **2026-11-06 — Phase 5 complete (docs).** `CLAUDE.md` was updated in the previous session; this run
  checked it only by the old-path grep below (its remaining hits are legitimate), not line by line.
  Repo `AGENTS.md`: the "Proposed follow-ups" section now lists
  only the four still-deferred items (VL-2 interface, reader-facing `reports/`, `validation_levels.md`,
  optional `GT/SRS.md`, MCP telemetry facade) and points here for what landed; the scaffold tree
  matches a fresh `codeanvil create` output (checked in a scratch project, not from memory).
  `methodology/test/README.md`: GT paths moved to `.codeanvil/GT/`, S1 outputs to `.codeanvil/design/`,
  `S1_graph.html` → `dependency_graph.html`, `telemetry companion` → `telemetry collector`, and two
  checks for `codeanvil backup <stage>` on rework (no new step: the skills run it themselves).
  - **Old-path grep** (Verification 5): 5 hits left, all legitimate: `AGENTS.md:55` and
    `CLAUDE.md:154` (`GT/` nested under `.codeanvil/`); `AGENTS.md:263` (same, scaffold tree);
    `CLAUDE.md:131` (`templates/GT/`, repo-side blueprints folder); `AGENTS.md:190` (`GT/SRS.md`,
    named as a deferred, unimplemented proposal).
  - **Finding:** `create` also makes an empty `.codeanvil/custody/` (`PROJECT_CUSTODY`), which the
    target layout above does not list. No skill uses it. Documented in the repo `AGENTS.md` tree as
    "empty; left from the retired custody chain". Removing it is a code change, deferred to the owner.
  - **Gap:** the repo root `README.md` still shows the old layout (`GT/G0_StRS.md`, `S1_artifacts/`)
    in about 15 places. It is outside Phase 5's file list and the grep, so it was not changed.
  - Evidence: 267 pytest + 97 unittest green.
- **2026-11-06 — Unit 1: root README.** Branch `feat/t3-holdout-refactor` (from `main`, 8 commits
  ahead of origin). README Quick Start, command table (`codeanvil backup <S0|S1|S2|G2>`, status
  backups line), "How it works" tree (`.codeanvil/{GT,design,backups,report}`, `StRS.md`/`SyRS.md`),
  artifacts paragraph (`design/`, backup rule, no migration) and the repo tree (`StRS.md`/`SyRS.md`
  templates, `reports.py`). Old-path grep with `README.md` added: 7 hits left, all legitimate
  (`GT/` nested under `.codeanvil/` in two trees, `templates/GT/` blueprints folder, and the
  deferred `GT/SRS.md` and nested GT references). Evidence: 267 pytest + 97 unittest green.
- **2026-11-06 — Unit 2: deferred rows.** Added the custody retirement row (checked:
  `sync.py:33` `_migrate_provenance` targets `.codeanvil/custody/`; `tests/test_create.py:357` asserts
  it) and the registry-prune row (checked: `codeanvil list` shows 10 rows, 8 with missing paths). No
  code changed; `~/.codeanvil-config/db` untouched. Evidence: 267 pytest + 97 unittest green.
- **2026-11-06 — Unit 3: version bump to v0.5.0.** `pyproject.toml`, `CLAUDE.md` and `README.md`
  (current-release links), and `AGENTS.md` ("Where to start" heading and table row). `uv.lock` also
  records the project version and the v0.4.4 bump did not update it, so it was regenerated with
  `uv lock` (one line changed). Release notes drafted at
  `odd/tasks/t3-holdout-refactor/v0.5.0_release_notes.md` (breaking changes, features). Evidence:
  267 pytest + 97 unittest green.
- **Next:** Unit 4 (final verification on the last commit, Release Smoke scratch run, cleanup).

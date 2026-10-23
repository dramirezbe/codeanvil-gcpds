# Report-Driven Gate Chain + Cycle Identity

## Objective

Refactor gate orchestration from AGENTS.md step-by-step logic to a **report-driven chain**: each skill checks for its predecessor's report, runs if it's missing or has `HITL: FEEDBACK`, and writes its own iterative report. AGENTS.md becomes a passive reference (skills, folders, MCP, cycle identity) — not an orchestrator. Branch: `feat/report-driven-gates`.

## Specs

### S1 — Standardized iterative report format

Every gate writes **one file** per gate in `.codeanvil/report/<gate>.md` (e.g. `G0.md`, `CC.md`, `G1.md`). Iterations are appended sections, never separate files. Format:

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
- Iteration starts at 1, increments on each run.
- `HITL: PASS` means the gate is done. `HITL: FEEDBACK` means iterate.
- No DENIED — that's incongruent. If user rejects, they provide feedback and the gate re-runs.
- For G0 (deterministic): Description carries the full script report. HITL forced `FEEDBACK` if script reports errors.
- Gate is complete when its latest iteration has `HITL: PASS`.

### S2 — Cycle identity in AGENTS.md

**Definition**: a **cycle** is one complete run of the V-SIL methodology pipeline against a GT baseline. Starting a new cycle means re-running the full gate chain from G0, producing a fresh set of reports. Previous cycles are preserved and read-only.

**On every project open**, before any gate work, the agent **MUST ask the user** for a cycle name. This is not optional and not deferred to "start" — it happens on first interaction with the project. The agent uses the harness's native question mechanism (e.g. `AskUserQuestion` in Claude Code, equivalent in other runtimes).

**Cycle name normalization**: the user provides a human-readable name; the agent normalizes it to a directory-safe slug:
- Lowercase
- Spaces → underscores
- Strip non-alphanumeric (except underscores and hyphens)
- Prefix with zero-padded sequence number based on existing cycles
- Example: user says `"Test SDR USRP IoT Signals"` → `01_test_sdr_usrp_iot_signals`
- Example: next cycle `"Websocket Refactor"` → `02_websocket_refactor`

The cycle name:

- Scopes all reports: `.codeanvil/report/<cycle-name>/<gate>.md`
- Written to `.codeanvil/project.yaml` under `cycle: <name>`
- Allows re-running the methodology (e.g. after a major refactor) by starting a new cycle
- If an existing cycle is selected, the agent resumes where it left off (latest gate without PASS)

If user wants to redo the methodology, they give a new cycle name. Old reports stay untouched.

```
.codeanvil/
├── project.yaml
└── report/
    ├── initial-design/
    │   ├── G0.md
    │   ├── CC.md
    │   └── G1.md
    └── websocket-refactor/
        ├── G0.md
        └── ...
```

### S3 — AGENTS.md becomes passive reference

Refactor `templates/AGENTS/TEMPLATE_AGENT.md`:

**Remove:**
- The "Startup" section that tells the agent to find the lowest incomplete gate and step through them
- Sequential gate execution logic
- The `## Report creation` section with timestamped filenames

**Keep:**
- Context section (you are in a user project)
- Rules (MUST NOT edit GT, etc.)
- GT section
- Timestamp section
- Project layout

**Add:**
- `## Cycle` — ask user for cycle name on start; scope reports to it
- `## Available Skills` — table with gate, skill path, prerequisite report (the chain)
- `## MCP Servers` — unchanged
- `## Report Format` — the iterative schema from S1
- `## Folder Reference` — brief guide to GT/, .codeanvil/, .agents/skills/

The skill table gains a `Prerequisite` column:

| Gate | Skill | Prerequisite |
|------|-------|-------------|
| G0 | `.agents/skills/G0_valid_req_and_GT/` | None (entry point) |
| CC | `.agents/skills/custody-chain/` | `G0.md` latest iteration `HITL: PASS` |
| G1 | `.agents/skills/G1_start_design/` | `CC.md` latest iteration `HITL: PASS` |

The agent loads a skill. The skill checks its prerequisite. If missing or FEEDBACK, it exits and tells the agent to run the prerequisite skill first. **Chain, not orchestration.**

### S4 — Skill prerequisite check (G0)

Refactor `templates/skills/G0_valid_req_and_GT/SKILL.md`:

- G0 has no prerequisite — it's the entry point.
- After running `g0_validate.py`, the skill writes/appends to `.codeanvil/report/<cycle-name>/G0.md`.
- If script exits 0: agent presents report to user, asks PASS or FEEDBACK.
- If script exits 1: HITL forced `FEEDBACK`, description carries the script output.
- `g0_validate.py` itself stays side-effect free (prints to stdout). The skill (agent) captures output and writes the report.

### S5 — Skill prerequisite check (Custody Chain)

Refactor `templates/skills/custody-chain/SKILL.md`:

- On load, check `.codeanvil/report/<cycle-name>/G0.md` exists and latest iteration is `HITL: PASS`.
- If not: exit with message "G0 must pass first. Run the G0 skill."
- After running custody scripts, write/append to `.codeanvil/report/<cycle-name>/CC.md`.

### S6 — Skill prerequisite check (G1)

Refactor `templates/skills/G1_start_design/SKILL.md`:

- On load, check `.codeanvil/report/<cycle-name>/CC.md` exists and latest iteration is `HITL: PASS`.
- If not: exit with message "Custody chain must pass first. Run the custody-chain skill."
- After each of the 8 jobs, user gives PASS or FEEDBACK. FEEDBACK appends a new iteration with the user's comments.
- Final PASS writes the last iteration with `HITL: PASS`.

### S7 — No-tools skills excluded

`templates/no-tools-skills/G0_SKILL.md` and `G1_SKILL.md` are **not touched** in this refactor. They are web-chat variants without file access — they can't read or write reports. They stay as-is.

### S8 — Scaffold creates report directory

`src/codeanvil/init/create.py` — `_create_codeanvil_dirs` creates `.codeanvil/report/` but does NOT create a cycle subdirectory. The agent creates the cycle directory on first gate run, after asking for the cycle name.

### S9 — config.yaml prerequisite chain

Add a `prerequisites` key to `templates/config.yaml` under each skill entry:

```yaml
skills:
  G0_valid_req_and_GT:
    project_dir: ".agents/skills/G0_valid_req_and_GT"
    template_dir: "templates/skills/G0_valid_req_and_GT"
    prerequisite: null
  custody-chain:
    project_dir: ".agents/skills/custody-chain"
    template_dir: "templates/skills/custody-chain"
    prerequisite: "G0"
  G1_start_design:
    project_dir: ".agents/skills/G1_start_design"
    template_dir: "templates/skills/G1_start_design"
    prerequisite: "CC"
```

This is consumed by the AGENTS.md template generator to build the prerequisite column.

## Tasks

| ID | Spec | Route | Status | Commit |
|----|------|-------|--------|--------|
| T1 | S9 | inline | done — RED/GREEN (`test_config_declares_skill_prerequisite_chain`) | aa1ab12 |
| T2 | S1, S2, S3 | inline | done — RED/GREEN (`test_agents_md_*`, 6 tests) | aa1ab12 |
| T3 | S4 | inline | done — RED/GREEN (`test_g0_skill_writes_an_iterative_report`) | aa1ab12 |
| T4 | S5 | inline | done — RED/GREEN (`test_custody_skill_requires_a_passing_g0_report`) | aa1ab12 |
| T5 | S6 | inline | done — RED/GREEN (`test_g1_skill_requires_a_passing_custody_report`) | aa1ab12 |
| T6 | S8 | inline | done — already conformant, pinned by `test_create_makes_report_dir_without_cycle_subdir` | aa1ab12 |
| T7 | S2 (report discovery) | inline | done — RED/GREEN (`test_status_reads_cycle_scoped_reports`, `test_status_lists_every_cycle`) | aa1ab12 |

## Log

**L1** (user, 2026-10-23): "Create plan. Refactor AGENTS template as just an informed tools markdown. Just informs skills, folder use, mcp, plugins, etc. Also add the refactor to existent skills, except no-tools-skills, to see if there's a report file, if not exit current skill and run before skill or last skill. In this way, we achieve a chain of iterative returns and not an orchestration in AGENTS.md. Add another thing in AGENTS.md, ask user experiment name. In this way the contract is attached to experiment id. If user wants to do the methodology again, for example a huge refactor, the user just does another experiment-name."

**L2** (analysis, 2026-10-23): Current state — G0 prints to stdout, agent saves report. AGENTS.md has explicit step-by-step startup logic. Skills check for "reports exist" loosely. Report format is ad hoc (G0 plain text, custody JSON). No cycle scoping. The refactor removes orchestration from AGENTS.md and pushes it into the skill chain via prerequisite reports.

**L3** (user, 2026-10-23): Renamed "experiment" → "cycle" — better V-model terminology. Cycle name added to both header and iteration metadata tables in the report format. Reports live under `.codeanvil/report/<cycle-name>/`.

**L4** (user, 2026-10-23): Cycle prompt is mandatory on every project open, not just on "start". Agent must always ask via native question mechanism. Cycle name normalized: lowercase, spaces→underscores, zero-padded sequence prefix. Example: "Test SDR USRP IoT Signals" → `01_test_sdr_usrp_iot_signals`. Existing cycle can be resumed.

**L5** (agent, 2026-10-23): Added **T7** — adapt `codeanvil status` to the cycle-scoped layout. The existing command globbed `<gate>_<timestamp>.md` at the report root, so after S2 it would print "none yet" while reports exist. Legacy files stay readable under a labelled section.

**L6** (agent, 2026-10-23): Implementation decisions within spec: (a) the G0 report is written by the skill, not `g0_validate.py`, per S4's side-effect-free validator; (b) custody-chain frontmatter gate is now `CC` (was `*`) so the S3 chain table renders CC and config order G0→CC→G1 drives table order; (c) the generated `project.yaml` header now allows the agent to maintain the `cycle` key, since S2 requires it and re-scaffold skips same-id manifests; (d) AGENTS.md table keeps the S3 three-column shape (Gate | Skill | Prerequisite) and drops the free-text description.

**L7** (agent, 2026-10-23): Evidence — `uv run pytest -q`: 216 passed (baseline 205 + 11 new). Differential check vs `main`: an identical `create --name "D Proj"` produces the same tree and stdout; content differs only in the intended AGENTS.md, skill docs, and manifest header (plus the project UUID). Scaffold inspection confirmed the chain table, empty `report/`, rewritten script paths, and cycle-aware `status` including legacy files.

**L8** (agent, 2026-10-23): Independent verification (read-only, fresh scratch copy) returned no blockers: S1–S9 and T7 MET; 216/216 suite in the candidate vs 205 at baseline; invariant commands (`now`, `sync`, `list`) and the scaffold tree match baseline; validator exit codes 0/1/2 with input digests unchanged. Advisories fixed in the correction batch: `status` no longer reads the literal schema row `| HITL | PASS | FEEDBACK |` as PASS (the HITL regex now requires exactly two cells), the root AGENTS.md config-id typo is corrected, and four durable probe tests were added (ambiguous schema row, legacy-only status, latest-verdict-wins, validator side effects/exit codes). Suite after fixes: 220 passed.

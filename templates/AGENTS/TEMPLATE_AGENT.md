# Project Instructions

This project follows the **V-SIL v3 methodology** (V-model at the SIL tier), whose chain
is S0 → G0 → S1 → G1 → S2 → G2, with RFD outside it. This file is a **reference** — it
describes the project, its skills, and its conventions. It does not orchestrate stages or
gates: each skill enforces its own prerequisite report, so the chain lives in the skills.
All instructions below are binding.

## Rules

- You **MUST** run stages and gates in sequential order (S0, G0, S1, G1, S2, G2). A step
  **SHALL NOT** execute until its predecessor passes.
- You **MUST** load the skill file (`.agents/skills/<skill>/SKILL.md`) before executing any step.
- You **SHALL NOT** skip, reorder, or combine stages and gates.
- You **MUST NOT** edit Ground Truth files in `.codeanvil/GT/` without explicit author confirmation.
  The one exception: the S0 skill writes `StRS.md` and `SyRS.md` from `build_package.md`.
- You **SHALL** report the gate verdict exactly as the skill's output contract specifies.
- You **MUST NOT** re-implement gate logic in prose — run the scripts and tools the skill prescribes.
- You **SHALL** treat errors as blocking and warnings as advisory unless a skill says otherwise.
- Only S2 writes code under `src/` and `verification/`, reworks included; G2 and the
  `vsil-verifier` subagent **MUST NOT** edit code.
- Delivered code under `src/` **MUST NOT** import or call `codeanvil` or depend on `verification/`.

## On Project Open

**First action on every project open** — before any gate work, before loading a
skill, and before asking the user anything — run:

```bash
codeanvil status
```

This prints the project identity, active cycle, and per-gate HITL verdicts. Use it as your
orientation: you do not need to read files or list directories to discover progress.

- The `codeanvil` CLI is the only tool for project state and timestamps:
  `codeanvil status`, `codeanvil now`, `codeanvil now --machine`.
- How each step works is in its skill under `.agents/skills/`; what the project must do
  is in `.codeanvil/GT/`. Read those to know what to do; run skill scripts from the project root.

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
- If the user selects an existing cycle, resume it: the next step is the first one, in
  chain order, whose report is missing, not at `HITL: PASS`, or marked `stale` by
  `codeanvil status`. Load that skill; its prerequisite check sends you to the right step.
  A cycle `codeanvil status` shows as closed is not resumed.
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

Load a skill when the user asks for its stage or gate or when its trigger applies. The
skill checks its prerequisite report itself:

- prerequisite report missing, or its latest iteration is `HITL: FEEDBACK` →
  the skill stops and tells you which skill to run first;
- prerequisite report's latest iteration is `HITL: PASS` → the skill runs and
  appends its own iteration.

This is a **chain, not orchestration**: nothing in this file sequences stages or
gates, and you must not sequence them from it either.

A rework is routed by a verdict line in the report: `Verdict: design defect` (from S2 or G2)
returns to S1; `Verdict: module defect` (from G2) returns to S2.

The `RFD_request_for_deviation` skill is outside the chain: it can be raised from S1, G1 or any
sub-gate of G2 when requirements are infeasible on the declared COTS platform (S2 only records
`Possible infeasibility` for G2), and it suspends the cycle until the Build Package author
decides. An accepted deviation closes the cycle: the flow is redone in a **new cycle with a new
name**, starting at S0 with an updated Build Package. The chain skills refuse to run in a closed cycle.

## Subagents

`vsil-verifier` is generated in `.claude/agents/`, `.opencode/agents/` and `.codex/agents/`. Only the
G2 skill uses it, to run the verification commands in a fresh, read-only context; in a runtime without
subagents, run G2 in a fresh session. Never use it for anything else or edit its files (regenerated).

## MCP Servers

{mcp_table}

MCP servers provide tool-calling capabilities to agents. Each server is started
automatically by your runtime when configured. Use the skills above to drive
MCP-powered workflows — skills encode the methodology, MCP tools are the primitives.

## Ground Truth (GT)

The `.codeanvil/GT/` directory holds human-authored `.md` files:

| File | Purpose |
|------|---------|
| `build_package.md` | The author's Build Package. S0 reads it |
| `StRS.md` | Stakeholder Requirements Specification (IEEE 29148 §9.4), written by S0 |
| `SyRS.md` | System Requirements Specification (IEEE 29148 §9.5), written by S0 |

`SyRS.md` §4–§6 hold the optional lab inputs (correction chains, tolerances, `PROTO-*`
procedures); with none in the Build Package, each holds `Not applicable: no lab inputs in the Build Package.`

G0 is a **pair gate**: both files must pass, plus the G0-X cross-document rules, before S1
runs. The S1 design document is produced by S1 in `.codeanvil/design/`.

These files are **inputs**. You **MUST NOT** modify them to make a gate pass.

## Report Format

Every stage and gate writes **one** report file: `.codeanvil/report/<cycle-name>/<id>.md`
(for example `S0.md`, `G0.md`, `S1.md`, `G1.md`, `S2.md`, `G2.md`, `RFD.md`). Iterations are
appended sections in that file — never separate files. S1 writes its working design to
`.codeanvil/design/` (`SDD.md` and `dependency_graph.html`). S2, G2 and RFD also write
working files to `.codeanvil/report/<cycle-name>/<ID>_artifacts/` (`S2_artifacts/` with
`test_run.md`, `G2_artifacts/` with `verified_prototype.md`, the cycle's terminal output,
and `RFD_artifacts/`), overwritten on rework and not report iterations.

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

<`Based on: <predecessor id> iteration <N>` first line, then content — user feedback, script output, or N/A>
```

Rules:

- Iterations start at `1` and increment on each run.
- `HITL: PASS` means the step is done. `HITL: FEEDBACK` means iterate. On a stage
  (S0, S1, S2), PASS means the output was delivered; the human verdict belongs to
  the next gate.
- Every iteration of G0, S1, G1, S2 and G2 starts its Description with the exact
  line `Based on: <predecessor id> iteration <N>`, where `N` is the predecessor's latest
  iteration when the work starts. S0 and RFD have no such line. `codeanvil status` uses
  it to mark a report `stale` when its predecessor was reworked.
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
- These rules cover reports and filenames. Delivered code formats its own log timestamps
  through its `config/logger` and never calls `codeanvil`.

## Folder Reference

| Path | What it holds |
|------|---------------|
| `.codeanvil/GT/` | Human-authored Ground Truth. Read-only during gates unless the author approves an edit. |
| `.codeanvil/design/` | S1's working design: `SDD.md` and `dependency_graph.html`. Overwritten on rework. |
| `.codeanvil/backups/` | Stage artifacts saved by `codeanvil backup <stage>`. |
| `.codeanvil/project.yaml` | Project identity (`id`, `name`, GT pointers) plus the active `cycle`. |
| `.codeanvil/report/<cycle-name>/` | One iterative report per gate, scoped to the cycle. |
| `.codeanvil/report/<cycle-name>/RFD_artifacts/` | RFD decision documents. Overwritten on rework. |
| `.codeanvil/report/<cycle-name>/S2_artifacts/` | S2's `test_run.md`: the verification commands and `Possible infeasibility` entries. |
| `.codeanvil/report/<cycle-name>/G2_artifacts/` | `verified_prototype.md`, written on G2 PASS. |
| `.agents/skills/` | Canonical skill store — every agent runtime links here. |
| `.claude/agents/`, `.opencode/agents/`, `.codex/agents/` | The generated `vsil-verifier` subagent, one file per runtime. |

## Project Layout

    AGENTS.md              <- you are here (canonical instructions)
    .codeanvil/            <- methodology tree (GT, design, reports, backups, identity)
    │   GT                 <- ground truth documents (human-authored): .codeanvil/GT/
    │   design/            <- S1 working design: SDD.md + dependency_graph.html
    │   project.yaml       <- project identity (id, name, GT pointers, cycle)
    │   report/            <- per-cycle gate reports (<cycle-name>/<gate>.md)
    │                          <cycle-name>/S2_artifacts/  <- test_run.md
    │                          <cycle-name>/G2_artifacts/  <- verified_prototype.md
    │   backups/           <- stage artifacts saved by `codeanvil backup <stage>`
    .agents/skills/        <- canonical skill store (all gate skills)
    .claude/agents/        <- vsil-verifier (also .opencode/agents/, .codex/agents/)

Agent-specific directories (`.claude/`, `.github/`, `.opencode/`, `.codex/`) contain
symlinks to `.agents/skills/` and the generated `vsil-verifier` files.

---
name: g1-design-review
description: "Trigger: G1, design review, review the S1 design, are design choices resolved. Prepare a design review of the S1 document for a human, with a filled checklist and a recommendation, and record the human's PASS, FEEDBACK or RFD answer."
license: Apache-2.0
compatibility: "No scripts. Network only to install a missing toolchain tool after the user agrees. Writes only .codeanvil/report/<cycle-name>/G1.md."
metadata:
  author: "gcpds"
  version: "1.0"
  gate: "G1"
  pipeline: "V-SIL"
---

# G1 — Human Design Review

G1 answers one question: **are all implementation-critical design choices resolved?**
**The human answers it.** G1 has no script and no exit code: the agent prepares the evidence and
recommends; only the human's answer sets the verdict.

**G1 runs no script.** The agent is the reviewer's analyst: it validates by reading, reasoning
and running the tools on this machine itself, and spends the tokens a thorough review needs.
Its findings inform the human; they are never an automatic verdict.

## Prerequisite and Cycle

Resolve the active cycle from `.codeanvil/project.yaml` (`cycle:`); if missing, ask the user.
If the latest iteration of `.codeanvil/report/<cycle-name>/RFD.md` holds a line
`Superseded by cycle: <name>`, this cycle is **closed** by an RFD and read-only: return exactly
`Cycle closed by RFD. Continue in cycle <name>.` and write nothing.

**Draft mode.** If `.codeanvil/report/<cycle-name>/DRAFT` exists, G1 runs in draft mode: re-derive the
findings on the **current** design, run Triage ([references/TRIAGE.md](references/TRIAGE.md)) on every
`open` finding, loop with the human, and write **no** iteration — the recorded-order checks below do
not block. The recorded review happens when the human commits the draft.

Otherwise check, in this order, writing **no iteration** when you stop:

1. `.codeanvil/report/<cycle-name>/S1.md` is missing or its latest iteration is not
   `HITL: PASS`: return exactly `S1 must pass first. Run the S1 skill.`
2. `codeanvil status` marks `S1` or any earlier report of the cycle `stale`: return the same
   line, naming the earliest stale report.
3. G1's own latest iteration is `FEEDBACK`. With `Verdict: RFD`, return exactly
   `Cycle suspended by RFD. Run the RFD skill.`, unless the latest `RFD.md` iteration states
   `Outcome: Withdrawn`. Otherwise, if its `Based on` line names the current latest S1
   iteration, the design was not reworked: return exactly
   `S1 must rework first. Run the S1 skill.` An unchanged design is never reviewed twice.

## Inputs

| Path | Role |
|------|------|
| `.codeanvil/design/SDD.md` | The design under review |
| `.codeanvil/design/dependency_graph.html` | Reading aid, named in `S1.md` |
| `.codeanvil/GT/StRS.md`, `.codeanvil/GT/SyRS.md` | Read-only: requirements the design must cover |
| `templates/skills/G1_design_review/references/G1_CHECKLIST.md` | This skill's checklist and filled form |
| `templates/skills/G1_design_review/references/TRIAGE.md` | Failure triage + draft mode, shared with S0 and G0 |

## Hard Rules

- The agent recommends; **only the human's answer sets `HITL`**. Never write `PASS` without it.
- `open` findings are shown first and never hidden, softened or fixed here. Rework belongs to S1.
- G1 is **not answered `PASS` while any `open` finding is undecided.** The human decides each one
  explicitly — accept/ignore (recorded with the decider's name), fix (→ S1 as FEEDBACK), or RFD. A
  blanket PASS over open findings is not a decision. Record every answer verbatim. See
  [references/TRIAGE.md](references/TRIAGE.md) §2.
- The graph is a reading aid. The prerequisite and the verdict rest on `S1.md`, the design and the
  human's answer. G1 never edits the graph; a wrong graph goes back to S1.
- Never edit the design or GT here.
- Read the whole design and both GT documents before filling any row, and
  re-derive every row yourself: the topological order from the §1.4 cards, coverage from the full `SYS-*` list, each
  contract field by field. Never trust the design's own summaries (§2.2 order, §4 tables)
  without checking them against the source sections.
- Tools are checked on this machine (G1.14). Install a missing one only after the user agrees.

## Steps

1. Give the human the graph's path from `S1.md`: its spiders support the topology and
   runtime-loop review (G1.9); the build order is reviewed in the design's §2 (G1.1).
2. Fill the checklist, including G1.11–G1.16 and the kit row.
3. **Validate the toolchain (G1.14).** For every `Toolchain` entry, run the `--version` of its
   language runtime and package manager yourself (for example `python3`, `uv`, `node`, `pnpm`,
   and `tsc` for TypeScript); the test runner comes with S2's lock. Record each version. When a
   tool is missing or older than the design needs, ask the user briefly, one question for all
   of them: `Install <tools> now?` with `yes` and `no`, with the native question tool or in
   chat. Install it only after a yes, at user level with the tool's documented installer, and
   never with `sudo` unless the user says so; then run `--version` again. A refused or failed
   install is an `open` G1.14 finding.
4. Recompute the GT digests with the system's hash command (`sha256sum .codeanvil/GT/StRS.md
   .codeanvil/GT/SyRS.md`; `shasum -a 256` on macOS, `Get-FileHash` in PowerShell) and show the human
   whether they match the design's Meta row. Information only: it never blocks. Compute the
   `SDD.md` digest the same way and record it in the iteration: S2 and G2 use it to detect a design
   changed after this review.
5. Present the findings, `open` first, and a recommendation. **If any finding is `open`, enter
   draft** — write the `DRAFT` marker ([references/TRIAGE.md](references/TRIAGE.md) §2) — and run
   Triage on each: a plain-language problem with reconciliation options. **The human decides every
   `open` finding** (accept/ignore, fix → S1, or RFD) before G1 is answered; the marker is removed
   when the answer is recorded. When the G1.8 test points to RFD, the recommendation names it.
6. Ask the human: **PASS**, **FEEDBACK** or **RFD**, as **Asking the human** says below.
7. Write the iteration with the filled form and the answer verbatim, including `Decided by: <name>`.

| Human answer | Row written | Route |
|--------------|-------------|-------|
| PASS | `HITL: PASS` | S2: return "G1 passed. Run the S2 skill." |
| FEEDBACK | `HITL: FEEDBACK` plus sections to rework | S1 |
| RFD | `HITL: FEEDBACK` plus the line `Verdict: RFD` | RFD skill |

**Asking the human.** Ask with your runtime's native question tool (`AskUserQuestion` in Claude Code): one single-select question with the options `PASS`, `FEEDBACK` and `RFD`, and a free-text answer allowed (the tool's type-your-own-answer choice). If the runtime has no question tool, ask the same question in chat and wait for the reply; never assume or default an answer. Any answer is recorded verbatim; a typed answer that does not choose `PASS` or `RFD` counts as `FEEDBACK`, never as `PASS`, and its text is the feedback. Then ask who is deciding, unless the human already said.

## Rework review (bounded)

When `S1.md`'s latest iteration carries a design change set, review the change instead of the whole
design again:

1. Trace each changed contract to its producers, consumers, stubs and tests along the §2.2 DAG. An
   interface change reaches every caller; a changed field reaches every stub, fake peer and vector.
2. Produce an **impact map** in the iteration's Description: the files S2 must edit, and the
   `PATH-*` and VL-1 tests it must retest only.
3. An impact the change set does not explain is an `open` finding (row G1.16). An empty impact map
   on a changed interface is always `open`.

## Report Contract

Write exactly one file: `.codeanvil/report/<cycle-name>/G1.md`, append-only.

- First run: header plus `## Iteration 1`; later runs append `## Iteration <N>`.
- Header: a `| Field | Value |` table with `Gate` = `G1`, `Cycle`, `Document` (the design path) and
  `Created` = `codeanvil now`.
- Iteration: a `| Field | Value |` table with `Date` = `codeanvil now`, `Timestamp` =
  `codeanvil now --machine`, `Iteration`, `Cycle`, and exactly one row written as
  `| HITL | PASS |` or `| HITL | FEEDBACK |` (never both in one row, which `codeanvil status`
  reads as `UNKNOWN`). Then `### Description`.
- The Description starts with the exact line `Based on: S1 iteration <N>`, where `N` is the latest
  S1 iteration when the review starts, followed by the filled checklist form and the SHA-256 of the
  `SDD.md` it reviewed. On rework it also carries the impact map.
- G1 is a **gate**: its `PASS` is the human's verdict.

## Output Contract

Return the findings (`open` first), the recommendation, the human's answer, the report path with
the iteration number, and the route.

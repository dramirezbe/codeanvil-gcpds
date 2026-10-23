---
name: g0-valid-req-and-gt
description: "Trigger: G0, validate StRS, validate SyRS, GT structural check, IEEE 29148. Deterministically validate the Ground Truth document pair, write the iterative G0 report, and return a line-numbered result."
license: Apache-2.0
compatibility: "Requires Python 3.9+ (stdlib only). No network access. The validator is side-effect free; the skill writes only .codeanvil/report/<cycle-name>/G0.md."
metadata:
  author: "gcpds"
  version: "3.0"
  gate: "G0"
  pipeline: "V-SIL"
---

# G0 — Structural Validation of Ground Truth Documents

## Prerequisite and Cycle

G0 has **no prerequisite** — it is the entry point of the V-SIL chain.

Before running anything:

1. Resolve the active cycle from `.codeanvil/project.yaml` (the `cycle:` key).
   If the key is missing, stop and ask the user for a cycle name (see
   `AGENTS.md`, `## Cycle`). Never guess a cycle or reuse another one.
2. Create `.codeanvil/report/<cycle-name>/` when it does not exist.

## Activation Contract

Load this skill when the V-SIL **Ground Truth pair** — a StRS (Stakeholder Requirements
Specification) and a SyRS (System Requirements Specification) `.md` file — needs structural
validation **before** any AI-driven gate runs, or when a G0 result must be deterministic and
reproducible.

Do **not** load it to judge requirement quality, measurement-method correctness, or
metrological rigor — those are later gates.

## Hard Rules

- **Run the script.** Never re-implement or hand-wave these checks in prose:
  `python templates/skills/G0_valid_req_and_GT/scripts/g0_validate.py <StRS.md> <SyRS.md>`
- **G0 is a pair gate.** Both a StRS and a SyRS must be provided; a missing half is an
  ERROR (exit `1`) via the G0 gate report.
- **The exit code is the gate verdict.** `0` pass, `1` errors block, `2` script error. Never
  record G0 as passed on exit `1` or `2`.
- **Errors block; warnings do not.** Report every ERROR. Never downgrade or suppress one.
- **Never edit a GT document to make G0 pass** without the author's explicit confirmation.
- **Validate against the templates**, never assumptions: `templates/GT/G0_StRS.md`,
  `templates/GT/G0_SyRS.md`.
- The validator is **stdlib-only and side-effect free** — it reads GT files and prints to
  stdout; never patch it to write to the documents it checks. The skill (the agent)
  captures the output and writes the report.
- **One report file, append-only.** Never write a second `G0` file and never edit an
  earlier iteration.

## Report Contract

Write exactly one file: `.codeanvil/report/<cycle-name>/G0.md`.

- First run: write the header and `## Iteration 1`.
- Later runs: append `## Iteration <N>`, where `N` is the number of existing
  iterations plus one.
- Header fields: `Gate` = `G0`, `Cycle` = the active cycle, `Document` = the two
  input paths, `Created` = `codeanvil now` (header written once).
- Iteration fields: `Date` = `codeanvil now`, `Timestamp` = `codeanvil now --machine`,
  `Iteration` = `N`, `Cycle` = the active cycle, `HITL` = `PASS` or `FEEDBACK`.
- `Description` carries the **full script output** verbatim — the two document
  reports, the G0-X cross-document report, and the G0 gate report when the pair is
  incomplete — plus the user's feedback when there is any.

## Decision Gates

| Situation | Action |
|-----------|--------|
| Exit `0` | Present the output to the user and ask **PASS** or **FEEDBACK**. Write the iteration with that `HITL` value. `PASS` completes G0. On `FEEDBACK`, write the user's comments in the Description. |
| Exit `1` | `HITL` is forced to **FEEDBACK**. Write the iteration with the full report so each ERROR is fixable by line + block ID. |
| Exit `2` | Script error (bad args, unreadable file, undetectable doc type). Fix the invocation or the type heading and re-run. Write **no** iteration. |
| Pair incomplete | The G0 GATE REPORT names the missing document; supply both files in one invocation. Write the iteration with `HITL: FEEDBACK`. |
| Finding needs context | Read the reported file and line; `Line` + block ID (+ `[StRS]`/`[SyRS]` tag on G0-X findings) locate it. |

## Execution Steps

1. Resolve the active cycle and ensure the report directory exists.
2. Confirm both target files exist: the StRS (`## Stakeholder Requirements Specification (StRS)`
   heading) and the SyRS (`## System Requirements Specification (SyRS)` heading).
3. From the project root, run the validator with **both** files in one invocation.
4. Capture **stdout** (per-document reports plus the G0-X cross-document report) and the
   **exit code**.
5. Map the exit code through the Decision Gates table above and write the report
   iteration.
6. Return the reports plus the verdict. For each ERROR, quote file, line number, block ID,
   document tag (G0-X), message, and `Expected:` value so the fix needs no re-read.

## Output Contract

Return all five:

1. **Verdict** — `G0: PASS` or `G0: FEEDBACK (N errors, M warnings)`.
2. **The full validation output** exactly as printed by the script (two G0 VALIDATION
   REPORTs, the G0-X CROSS-DOCUMENT REPORT, and — when the pair is incomplete — the
   G0 GATE REPORT).
3. **Fix list** — when there are ERRORs, one entry per error: file · line · block ID ·
   message · expected value.
4. **The observed exit code.**
5. **The report path** — `.codeanvil/report/<cycle-name>/G0.md` and the iteration number.

## References

- [references/RULES.md](references/RULES.md) — full Phase 1–4 + G0-X rule tables, required
  sections, enum values, block/field formats, the report format, and the script's internal
  architecture.
- `scripts/g0_validate.py` — the deterministic validator (Python 3.9+, stdlib only).
- `templates/GT/G0_StRS.md`, `templates/GT/G0_SyRS.md` — the authoritative structure
  definitions (repository-root relative).

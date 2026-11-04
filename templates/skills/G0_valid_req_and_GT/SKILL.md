---
name: g0-valid-req-and-gt
description: "Trigger: G0, Gate H, validate StRS, validate SyRS, GT structural check, IEEE 29148. Deterministically validate the Ground Truth document pair S0 produced, then ask the human the Gate H question, write the iterative G0 report, and return a line-numbered result."
license: Apache-2.0
compatibility: "Requires Python 3.9+ (stdlib only). No network access. The validator is side-effect free; the skill writes only .codeanvil/report/<cycle-name>/G0.md."
metadata:
  author: "gcpds"
  version: "3.1"
  gate: "G0"
  pipeline: "V-SIL"
---

# G0 — Structural Validation of Ground Truth Documents

## Prerequisite and Cycle

G0 validates what S0 produced. Before running anything:

1. Resolve the active cycle from `.codeanvil/project.yaml` (the `cycle:` key).
   If the key is missing, stop and ask the user for a cycle name (see
   `AGENTS.md`, `## Cycle`). Never guess a cycle or reuse another one.
2. If the latest iteration of `.codeanvil/report/<cycle-name>/RFD.md` holds a line
   `Superseded by cycle: <name>`, this cycle is **closed** by an RFD and read-only: return exactly
   `Cycle closed by RFD. Continue in cycle <name>.` and write nothing.
3. Check, in this order, writing **no iteration** when you stop:
   1. `.codeanvil/report/<cycle-name>/S0.md` is missing or its latest iteration is not
      `HITL: PASS`: return exactly `S0 must pass first. Run the S0 skill.`
   2. `codeanvil status` marks `S0` stale: return the same line.
   3. G0's own latest iteration is `FEEDBACK`. With `Verdict: RFD`, return exactly
      `Cycle suspended by RFD. Run the RFD skill.`, unless the latest `RFD.md` iteration
      states `Outcome: Withdrawn`. Otherwise, if its `Based on` line names the current latest
      S0 iteration, nothing was reworked: return exactly
      `S0 must rework first. Run the S0 skill.`
4. Create `.codeanvil/report/<cycle-name>/` when it does not exist.

## Activation Contract

Load this skill when the V-SIL **Ground Truth pair** — a StRS (Stakeholder Requirements
Specification) and a SyRS (System Requirements Specification) `.md` file — needs structural
validation, or when a G0 result must be deterministic and reproducible. G0 is the **only
deterministic gate** of the flow; the human answers Gate H right after it.

Do **not** load it to judge requirement quality, measurement-method correctness, or
metrological rigor, and do not use it for the design: that is S1 and G1.

## Hard Rules

- **Run the script.** Never re-implement or hand-wave these checks in prose:
  `python templates/skills/G0_valid_req_and_GT/scripts/g0_validate.py <StRS.md> <SyRS.md>`
- **G0 is a pair gate.** Both a StRS and a SyRS must be provided; a missing half is an
  ERROR (exit `1`) via the G0 gate report.
- **The exit code is the gate verdict.** `0` pass, `1` errors block, `2` script error. Never
  record G0 as passed on exit `1` or `2`.
- **Errors block; warnings do not.** Report every ERROR. Never downgrade or suppress one.
- **Never edit a GT document inside G0.** A fix goes back to S0 (or to the author, for a
  hand-written pair).
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
- `HITL` is written as one row, `| HITL | PASS |` or `| HITL | FEEDBACK |`, never both in
  one row, which `codeanvil status` reads as `UNKNOWN`.
- `Description` starts with the exact line `Based on: S0 iteration <N>`, where `N` is the
  latest S0 iteration when the check starts. It then carries the **full script output**
  verbatim — the two document reports, the G0-X cross-document report, and the G0 gate report
  when the pair is incomplete — plus, on exit `0`, the Gate H record: the answer verbatim,
  the date from `codeanvil now`, and `Decided by: <name>`.

## Decision Gates

| Situation | Action |
|-----------|--------|
| Exit `0` | Show the user the script output and the **missing list** from the latest `S0.md` iteration (placeholders the validator does not reject). Then ask **Gate H**: *Requirements complete, bounded, and verifiable?* Answer **PASS** or **FEEDBACK**, and who is deciding. Write the iteration with that `HITL` value; `PASS` completes G0. |
| Gate H `FEEDBACK` | Collect the reasons one per line, each starting with the block ID it concerns, and write them verbatim. The route back is S0. Never suggest or complete a reason. |
| Exit `1` | `HITL` is forced to **FEEDBACK**, with no question to the human. Write the iteration with the full report so each ERROR is fixable by line + block ID. The route back is S0. |
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
   iteration. On a Gate H `PASS`, record the date and `Decided by: <name>` in the Description.
6. Return the reports plus the verdict. For each ERROR, quote file, line number, block ID,
   document tag (G0-X), message, and `Expected:` value so the fix needs no re-read.

## Output Contract

Return all five:

1. **Verdict** — `G0: PASS` (script and Gate H) or `G0: FEEDBACK (N errors, M warnings)`.
   After a `PASS`, return `G0 complete. Run the S1 skill.`
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

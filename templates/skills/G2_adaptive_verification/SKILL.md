---
name: g2-adaptive-verification
description: "Trigger: G2, adaptive verification, verify the S2 build, Verified Prototype. Run the S2 evidence at the declared levels in a fresh context, present it to a human and record the PASS, FEEDBACK or RFD answer."
license: Apache-2.0
compatibility: "Runs only the test_run.md level and read-only preflight commands, locally or through the declared vsil_hil_mcp target. Fetches telemetry; never deploys or repairs code. Writes only .codeanvil/report/<cycle-name>/G2.md and G2_artifacts/."
metadata:
  author: "gcpds"
  version: "1.0"
  gate: "G2"
  pipeline: "V-SIL"
---

# G2 — Adaptive Verification

G2 answers one question: **does the delivered software meet its requirements at the declared
levels?** **The human answers it.** The agent runs the evidence, never writes or edits a test, and
drafts the honesty declaration; only the human's answer sets the verdict. On PASS, G2 writes the
cycle's terminal output: the Verified Prototype.

## Prerequisite and Cycle

Resolve the active cycle from `.codeanvil/project.yaml` (`cycle:`); if missing, ask the user.
Check, in this order, writing **no iteration** when you stop:

1. The latest iteration of `.codeanvil/report/<cycle-name>/RFD.md` holds a line
   `Superseded by cycle: <name>`: return exactly `Cycle closed by RFD. Continue in cycle <name>.`
2. `.codeanvil/report/<cycle-name>/S2.md` is missing or its latest iteration is not `HITL: PASS`,
   or `codeanvil status` marks `S2` or any earlier report `stale`: return exactly
   `S2 must pass first. Run the S2 skill.`
3. G2's own latest iteration is `FEEDBACK`. With `Verdict: RFD`, return exactly
   `Cycle suspended by RFD. Run the RFD skill.`, unless the latest `RFD.md` iteration states
   `Outcome: Withdrawn`. Otherwise, when its `Based on` line names the current latest S2 iteration,
   the code was not reworked: return exactly `S2 must rework first. Run the S2 skill.` for
   `Verdict: module defect`, or `S1 must rework first. Run the S1 skill.` for
   `Verdict: design defect`. Unchanged code is never verified twice.

## Inputs

| Path | Role |
|------|------|
| `.codeanvil/report/<cycle-name>/S2_artifacts/test_run.md` | The only commands G2 runs: `verification/run.sh vl0`, `verification/run.sh vl1` and recorded read-only target/deployment preflights; target block and `Possible infeasibility` entries |
| `.codeanvil/project.yaml` | Target declarations, compared with SDD and the S2 target block before any remote execution |
| `.codeanvil/design/SDD.md` | Meta `Target(s)`, `HAL mode` and `Toolchain`, `required_vl` per module and `PATH-*`, §1.6 HAL ladder, §1.7 telemetry envelope per target |
| `.codeanvil/GT/SyRS.md` | Read-only: `SYS-*` thresholds; §6 `PROTO-*`, §4 correction chains, §5 tolerances for VL-2 |
| `templates/skills/G2_adaptive_verification/references/verified_prototype.md` | The Verified Prototype template |

## Hard Rules

- The agent recommends; **only the human's answer sets `HITL`**. Never write `PASS` without it.
- Run only the commands of `test_run.md`. Never write, edit or fix a test, the code or the design.
  A declared VL-1 module or path with no VL-1 test is a **module defect** routed to S2.
- The VL-0 run must include a smoke test of the runnable system entry point from design §0.5:
  the real processes start, exchange one valid update and shut down cleanly. A missing or failing
  entry-point smoke test is a module defect routed to S2, even when other tests pass.
- Never reuse S2's results: always re-run.
- Levels by HAL mode: `mock-only` caps every claim at VL-1, so refuse a VL-2 declaration and state
  that no claim uses real device inputs. PIL may use the actual processor with Mock HAL inputs
  and stays VERIFIED. `mock+real` allows VL-2 per module or path; a Real HW HAL
  declared at VL-0 for this cycle means G2.2 does not fire, and the honesty declaration says so.
- A result outside the §1.7 telemetry envelope is shown flagged, never silently accepted.
- A constant or placeholder telemetry reading is not measured evidence: report it as a module
  defect, never as an envelope result.
- A target/configuration mismatch, failed provenance or version preflight, missing command,
  missing/empty/corrupt telemetry or unavailable required readings is an **evidence gap**. Show
  it explicitly; it cannot be reported as a passing or in-envelope result. A collector exit 0
  alone is insufficient. Skip only a torn final JSONL line, disclose it and assess the remaining
  coverage; do not silently discard earlier corruption.
- No model is measured this round (FW-ML-4): the Verified Prototype has no ML evidence.

## Who runs what

Steps 2–5 run in the **`vsil-verifier` subagent**: a fresh context that did not write the code,
cannot edit files and returns one results table. Pass it only the cycle name and the declared
levels, nothing from S2's conversation. G2 itself declares levels, presents, asks the human and
writes the report. When the runtime has no `vsil-verifier` subagent (for example Copilot or Pi),
say so and ask the user to run G2 in a fresh session; run nothing in the session that ran S2.
In a fresh session that did not run S2, G2 runs steps 2–5 itself and records
`Verifier` = `fresh session`.

## Local or remote execution

No declared `targets:` means local execution. Otherwise use the SDD's named execution targets,
matching every service/path with `test_run.md`; several declared targets require explicit names.
The target block names host, user, port, workspace, observed OS/architecture, device and host and
target CodeAnvil versions. Missing or conflicting values stop that target's run as an evidence gap;
never silently substitute the developer host.

S2 has already deployed the delivered code and kit. The fresh verifier uses only
`ssh_exec_cmd(cmd="<exact recorded payload>", target="<name>")` and `fetch_evidence` remotely:

1. Execute the recorded read-only version/OS/architecture probes and compare the observed
   CodeAnvil version to the host and S2 record. Then run the recorded
   `python3 verification/check_deployment.py --expected <manifest-SHA256>` preflight from the
   target workspace. The expected digest and clean delivered git revision come from the host's
   S2 record; `.git` is not deployed. A missing preflight or nonzero exit stops the run.
2. Relay `verification/run.sh vl0` and, when declared, `verification/run.sh vl1` exactly as
   recorded, with the workspace `cd` prefix and explicit target. The kit collects telemetry on
   that compute unit. Recheck deployment identity after the runs; a changed baseline invalidates
   the affected evidence even if the tests exited 0.
3. `fetch_evidence(target="<name>")` retrieves telemetry. Match the exact new files to this run,
   record their SHA-256 hashes and apply that target's §1.7 envelope. Old telemetry is not a fresh
   result. The report and Verified Prototype name the real compute unit and identify PIL.

Never call `code_sync`, `init_codeanvil` or `ssh_exec_cmd_trusted` from the verifier. A setup
problem returns to S2 or the human; the verifier cannot change its command or repair access.
Tool availability and runtime permissions are separate: a tool name alone does not guarantee a
human prompt. Claude/OpenCode constrain the shipped MCP tool set; Codex's shared body is an
instruction boundary, not an OS sandbox. If the runtime cannot supply the permitted MCP tools,
use a fresh session with them or report the gap instead of invoking direct SSH.

## Steps

1. **Declare levels.** Show each module and `PATH-*` with its `required_vl`. The human declares
   the level for this cycle (default VL-0).
2. **G2.0, always.** Resolve local/remote execution and complete the recorded preflights above.
   Fresh run of `verification/run.sh vl0` with the telemetry companion on that execution target.
   Check its §0.5 entry-point smoke result and the exact command recorded in `test_run.md`.
3. **G2.1, when VL-1 is declared.** Run `verification/run.sh vl1`: Mock HAL synthetic inputs per
   §1.6, metrics against the `SYS-*` thresholds.
4. **G2.2, when VL-2 is declared in `mock+real`.** The SyRS §6 `PROTO-*` procedures cited by design
   §1.6, on the Real HW HAL, with the §4 correction chains and §5 tolerances. The subagent prepares
   the procedure; if no hardware is reachable from the session, the human runs it and pastes the
   measurements.
5. **Telemetry check.** Fetch remote evidence and complete the post-run identity check above.
   Flag every result produced outside that target's §1.7 envelope. Reject a constant or
   placeholder reading as measured evidence: it is a module defect. Report unavailable evidence
   and incomplete coverage rather than assigning an in-envelope result.
6. **Infeasibility.** Show every `Possible infeasibility` entry from `test_run.md` next to the G2
   result that confirms or refutes it. When the defect-or-RFD test points to RFD, the
   recommendation names it.
7. **Present** one table per module and path (declared level, environment, result, telemetry
   flag), the entry-point smoke result, the draft honesty declaration and a recommendation. Ask
   the human: **PASS**,
   **FEEDBACK** or **RFD**, as **Asking the human** says below.
8. **Back up the previous Verified Prototype before overwriting it.** Run `codeanvil backup G2`
   from the project root. If it exits nonzero, stop and show its message; write no iteration.
   Cite the printed backup path in the iteration's Description. Backups never cover `src/` or
   `verification/`: code recovery relies on git.
9. Write the iteration with the results table and the answer verbatim, including
   `Decided by: <name>`.

| Human answer | Row written | Route |
|--------------|-------------|-------|
| PASS | `HITL: PASS` plus `G2_artifacts/verified_prototype.md` | Done: return "G2 passed. Verified Prototype written." |
| FEEDBACK, module defect | `HITL: FEEDBACK` plus `Verdict: module defect` and the modules, including missing VL-1 tests | S2 |
| FEEDBACK, design defect | `HITL: FEEDBACK` plus `Verdict: design defect` and the S1 sections to rework | S1 |
| RFD | `HITL: FEEDBACK` plus the line `Verdict: RFD` | RFD skill, with the G2 report as evidence |

**Asking the human.** Ask with your runtime's native question tool (`AskUserQuestion` in Claude Code): one single-select question with the options `PASS`, `FEEDBACK` and `RFD`, and a free-text answer allowed (the tool's type-your-own-answer choice). If the runtime has no question tool, ask the same question in chat and wait for the reply; never assume or default an answer. Any answer is recorded verbatim; a typed answer that does not choose `PASS` or `RFD` counts as `FEEDBACK`, never as `PASS`, and its text is the feedback. Then ask who is deciding, unless the human already said. A FEEDBACK answer names module defect or design defect; ask if it does not.

## Report Contract

Write only `.codeanvil/report/<cycle-name>/G2.md`, append-only, and on PASS
`.codeanvil/report/<cycle-name>/G2_artifacts/verified_prototype.md` filled from the template.

- First run: header plus `## Iteration 1`; later runs append `## Iteration <N>`.
- Header: a `| Field | Value |` table with `Gate` = `G2`, `Cycle`, `Document` (the `test_run.md`
  path) and `Created` = `codeanvil now`.
- Iteration: a `| Field | Value |` table with `Date` = `codeanvil now`, `Timestamp` =
  `codeanvil now --machine`, `Iteration`, `Cycle`, `Verifier` (`vsil-verifier` or
  `fresh session`), and exactly one row written as `| HITL | PASS |` or `| HITL | FEEDBACK |`.
  Then `### Description`.
- The Description starts with the exact line `Based on: S2 iteration <N>`, where `N` is the latest
  S2 iteration when verification starts, followed by the declared levels and the results table.
- Honesty declaration: VERIFIED for VL-0 and VL-1 claims; VALIDATED only for VL-2 claims.
- G2 is a **gate**: its `PASS` is the human's verdict.

## Output Contract

Return the results table (flagged rows first), the honesty declaration, the human's answer, the
report path with the iteration number, and the route.

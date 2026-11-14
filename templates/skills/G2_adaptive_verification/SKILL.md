---
name: g2-adaptive-verification
description: "Trigger: G2, adaptive verification, verify the S2 build, Verified Prototype. Run the S2 evidence at the declared levels in a fresh context, present it to a human and record the PASS, FEEDBACK or RFD answer."
license: Apache-2.0
compatibility: "Parent reviews/prepares HW; fresh verifier runs the recorded tests and approved diagnostic commands locally or through vsil_hil_mcp. Parent handles trusted; verifier never edits DUT or asks the human. Writes only .codeanvil/report/<cycle-name>/G2.md and G2_artifacts/."
metadata:
  author: "gcpds"
  version: "1.2"
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
| `.codeanvil/report/<cycle-name>/S2_artifacts/test_run.md` | Recorded VL-0/VL-1 and real HW tests, measurement scripts, target/preparation context, structural-record checker and `Possible infeasibility` |
| `.codeanvil/project.yaml` | Target declarations, compared with SDD and the S2 target block before any remote execution |
| `.codeanvil/design/SDD.md` | Meta `Target(s)`, `HAL mode` and `Toolchain`, `required_vl` per module and `PATH-*`, §1.6 HAL ladder, §1.7 telemetry envelope per target |
| `.codeanvil/GT/SyRS.md` | Read-only: `SYS-*` thresholds; §6 `PROTO-*`, §4 correction chains, §5 tolerances for VL-2 |
| `templates/skills/G2_adaptive_verification/references/verified_prototype.md` | The Verified Prototype template |
| `templates/skills/G2_adaptive_verification/references/machine_evidence.md` | Small measurement v2 record, pre-HW checkpoint, acquisition and telemetry diagnosis |

## Hard Rules

- The agent recommends; **only the human's answer sets `HITL`**. Never write `PASS` without it.
- Run the required commands of `test_run.md`; approved auxiliary diagnostics can explain failures,
  never replace a missing required test. Never write, edit or fix the DUT, required tests or design.
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
- Missing commands, configuration or telemetry must be shown with cause and affected scope,
  never silently accepted or replaced by invented values. Diagnose collector/process/disk/sensors
  and decide whether to repeat the affected measure or continue with supported evidence. A
  collector exit 0 does not prove coverage; a missing metric does not invalidate unrelated tests.
  A torn final JSONL line may be skipped with notice; earlier corruption needs investigation.
- No model is measured this round (FW-ML-4): the Verified Prototype has no ML evidence.

## Execution Continuity

After the human declares levels or gives the required pre-HW `continue`, execute the authorized
next steps **in the same turn** through preparation, fresh verification and evidence review to
the next required human decision or a concrete blocker. A progress update is not a stopping
point; never end only with "I will run the tests", "verification is in progress" or unfinished
analysis when an authorized next action remains. A status question during active work gets a
brief update, then work continues unless the human explicitly pauses or redirects it.

- Resume from the existing candidate, scope and answered checkpoints; do not request the same
  approval again. A changed candidate/scope/target/delivery/iteration still renews pre-HW review.
  `continue` is permission for that checkpoint's scope, never a level declaration or HITL PASS.
- Launch the fresh verifier and await its actual results using the runtime's task/wait tools.
  A promise or progress-only return is not verification evidence: request the missing execution
  and results within the reviewed scope. A concrete scope/setup blocker returns to the parent;
  the verifier never asks the human or repairs product/test code.
- Read the actual attempt's outputs, exit codes and evidence files against the criteria and
  referenced normative schemas. Available schemas do not need redesign because legacy code
  differs from them; classify the demonstrated failure through Operational vs defect.

| Boundary | Required action |
|----------|-----------------|
| Required levels, enrollment, pre-HW review or final human decision | Ask the specific outstanding question and wait; state what remains pending. Pending enrollment blocks HW, not authorized local G2.0/G2.1. |
| Operational blocker or missing evidence | Diagnose within scope and retry when possible; otherwise show command/error or missing artifact, affected claims and the concrete input/action needed. Continue unaffected checks where permitted; do not manufacture a defect or verdict. |
| Missing/failed required test or contradictory design | Present observed versus expected, files/sections, cause or hypothesis and proposed route; obtain the human verdict under Steps before publishing FEEDBACK. Never fix the candidate in G2. |
| Human verdict and decision author obtained | Perform the backup and publish the completed report and any PASS artifact in this turn; no extra `continue` is needed. A backup failure still stops without an iteration. |
| Explicit human stop or runtime interruption/limit | Preserve evidence and identify completed/pending scope and the concrete resume action; no partial iteration or invented HITL. |

### Continuation responses and unblocking options

At a continuation checkpoint, trim surrounding whitespace and compare the whole reply without
case sensitivity: `continue`, `y`, `yes`, `ok` and `run` all mean `continue` (including `Y` and
`RUN`). This is explicit consent to the presented scope, including the pre-HW review; do not ask
for the literal word again. Record the canonical `continue` checkpoint with the original reply
verbatim in its note. Do not match substrings or ignore negation/conditions. These replies never
select a level, authorize changed scope or choose the final `PASS`/`FEEDBACK`/`RFD` verdict.

For a blocker, offer one recommended concrete way forward and up to two useful alternatives,
with each option's action, scope and check for success: for example, repair a diagnosed target
permission, retry the reviewed command or complete unaffected checks while disclosing the gap.
The parent applies authorized operational fixes; the verifier returns setup/scope needs to it.
Ask only for missing input, permission or a real choice. A bare affirmative accepts a single
clearly presented proposal; if incompatible alternatives remain, ask which one. Code/test
changes still route through S2 and design changes through S1 with the human's verdict. Never
offer fabricated evidence, weaker criteria or bypassing required pre-HW review as an unblock.

## Who runs what

Steps 2–5 run in the **`vsil-verifier` subagent**: a fresh context that did not write the code,
cannot edit product/test files and returns one results table. Pass only the cycle, the next G2
iteration number, declared levels and reviewed execution scope (equipment and permitted commands),
nothing from S2's conversation. Derive that iteration number as 1 when no G2 iteration exists,
otherwise the last appended G2 iteration number plus 1; pass it as ordinary execution context,
without writing a partial report or introducing a counter/state. G2 itself declares levels, presents, asks the human and
writes the report. When the runtime has no `vsil-verifier` subagent (for example Copilot or Pi),
say so and ask the user to run G2 in a fresh session; run nothing in the session that ran S2.
In a fresh session that did not run S2, G2 runs steps 2–5 itself and records
`Verifier` = `fresh session`.

## Hardware enrollment (pre-G2, parent only)

Hardware credentials, IP and MAC appear only here, never earlier in the flow. The step applies when
the SDD declares `HAL mode` `mock+real` **and** a VL-2 claim **and** `.codeanvil/project.yaml` has
no enrolled `targets:` entry. Then **stop** and ask the human to run, from the project root:

`codeanvil credential-setup -u <admin-user> -i <host> --port 22`

This **blocks the real-HW stage** (G2.2 and the pre-HW review below) until enrollment is done and
`targets:` holds the target; re-check `project.yaml` after the human reports it. Silence/timeouts
are not consent. G2.0 and G2.1 need no hardware and may proceed locally while it is pending.
`mock-only` designs and designs limited to VL-0/VL-1 never trigger this step: do not mention it.
This version supports exactly one target; `credential-setup` rejects a different second device.
The pre-HW review checkpoint below then follows enrollment; it is not a second checkpoint.

## Pre-HW review and preparation (parent only)

Before remote update/deployment or any local device test, the G2 parent shows the code/kit,
published branch/commit, equipment/device and intended preparation/test commands. Require a
clean Git tree and the candidate committed — pushed to its upstream when the branch tracks a remote, or a local-only commit flagged unpublished otherwise; staged or untracked source and
failed pushes (when a remote is tracked) cannot reach hardware. Keep the delivered-project repo/ref separate from the
CodeAnvil tool repo/ref. Do not invent tags, change code to make tests pass or force push.

**Stop and wait for explicit `continue`** (or an affirmative alias defined above), including in full-access mode. Silence/timeouts are
not consent. On `rework`, return code/test changes to S2; on `stop`, preserve the work and write
no iteration. A new code candidate, scope, target, delivery or iteration renews the review. The
same reviewed acquisition may be retried with a fresh timestamp within that scope. Record
`Checkpoint: pre-HW review — continue — <equipment, candidate and scope>` in the completed G2
Description, not as a gate, new HITL state, capture request or partial `## Iteration` section.

After `continue`, the parent automatically updates enrolled equipment's CodeAnvil from its
actual published tool ref (`init_codeanvil`), deploys the clean published application candidate
with `code_sync`, installs needed dependencies, checks capabilities and synchronizes clocks.
Preserve target databases/state. Ordinary commands, packages and `sudo` use `ssh_exec_cmd`;
clearly destructive work (including `systemctl`) uses trusted under the parent's runtime policy.
Do not change the clock during acquisition; use monotonic durations and record clock incidents.
Version observations inform diagnosis, not an exact-SemVer gate. If preparation still prevents
measurement, explain the operational cause and pause rather than inventing a product defect.

The verifier remains fresh and never asks the human. The parent completes preparation before
launching it, and handles any trusted operation or needed expansion of reviewed scope that the
verifier returns. An extra human operator is not required to run actual HW tests.

## Local or remote execution

No declared `targets:` means local execution. Otherwise use the design's declared equipment,
identified by discovered MAC (legacy IDs remain readable), and its project UUID workspace.
Select the intended equipment explicitly when several exist; do not request a user-invented
alias or put local key paths in shared metadata. Match the observed OS/architecture/device and
commands against the design; never silently substitute the developer host.

After parent preparation, the fresh verifier uses `probe_target`, `ssh_exec_cmd` and
`fetch_evidence` on remote equipment, and normal runtime tools locally. Execute the exact test
payloads from their workspace. Run required VL-0/VL-1 tests and authorized real HW tests; choose
auxiliary diagnostic commands appropriate to the GT metric and tolerance when needed. A required
missing test is a module/kit defect for S2, not an invitation to invent a replacement in G2.

Each attempt uses `<cycle>_<iteration>_<codeanvil now --machine>`, based on the current G2
iteration, with telemetry and measurement/script outputs in `verification/telemetry/<run_id>/`.
The ordinary stage/cycle/run records identify the attempt. `fetch_evidence`
returns a new host snapshot `local_path`; select this run's files inside it rather than reusing
old logs. S2's development runs never stand in for G2's fresh evidence. Missing telemetry is
investigated and the repeat/continue decision names exactly which claims remain supported.

## Operational vs defect (verdict branch)

Before recommending any verdict, classify the failure. The G2 verdict logic has four
first-class outcomes: **operational-fix** (fix the DUT and re-run G2), **module defect**
(→ S2), **design defect** (→ S1) and **RFD**. Only a genuine behavioral failure of the
delivered code is a module or design defect.

A permission, driver, group, udev, device-visibility or USB-access problem on the target
DUT — for example, the `codeanvil-agent` user cannot open the HackRF — is **operational**,
never a module or design defect, and must not route to S2 or S1 feedback. The correct
response is to recommend the fix on the DUT (add `codeanvil-agent` to the device group,
add a udev rule or a `plugdev` entry), verify with `probe_target` / `lsusb`, then **re-run
G2**. A transient SSH/clock/setup fault is operational in the same way: diagnose and repair
during preparation, pause if it prevents measurement, never a product-defect label.

**Last resort.** If the runtime or tool blocks the remediation command (the permission
classifier refuses `ssh_exec_cmd_trusted`, or the sandbox blocks the fix), hand the user
the exact commands to run by hand on the target — the concrete group/udev/plugdev
commands — then re-run G2, rather than giving up or mislabeling it an S2 defect.

## Steps

1. **Declare levels.** Show each module and `PATH-*` with its `required_vl`. The human declares
   the level for this cycle (default VL-0).
2. **G2.0, always.** Resolve local/remote execution; parent completes any required pre-HW review
   and preparation above. Fresh run of `verification/run.sh vl0` with telemetry on that target.
   Check its §0.5 entry-point smoke result and the exact command recorded in `test_run.md`.
3. **G2.1, when VL-1 is declared.** Run `verification/run.sh vl1`: Mock HAL synthetic inputs per
   §1.6, metrics against the `SYS-*` thresholds.
4. **G2.2, when VL-2 is declared in `mock+real`.** After the parent's checkpoint and preparation,
   the fresh verifier runs the recorded real HW command and measurement scripts itself. Follow
   `references/machine_evidence.md`, read `measurement.json` v2 and run the copied basic checker.
   Choose methods with resolution justified against GT tolerances; use `PROTO-*`, calibration,
   corrections and uncertainty only when the requirement/conclusion needs them. Missing required
   metrological inputs make the affected result inconclusive; functional tests need no universal
   oracle. A valid record may contain failed or inconclusive measurements and never decides HITL.
5. **Telemetry check.** Fetch remote evidence and assess this attempt's readings against that
   target's §1.7 envelope. Flag out-of-envelope results. Reject a constant or placeholder reading
   as measured evidence: it is a module defect. If evidence is missing/incomplete, investigate,
   notify the parent and decide whether to repeat affected measures or proceed with the supported
   scope; record the cause and decision instead of invalidating all unrelated tests.
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
| FEEDBACK, module defect | `HITL: FEEDBACK` plus `Verdict: module defect`, the modules (including missing VL-1 tests) and the Description's enumerated change list | S2 |
| FEEDBACK, design defect | `HITL: FEEDBACK` plus `Verdict: design defect` and the S1 sections to rework | S1 |
| RFD | `HITL: FEEDBACK` plus the line `Verdict: RFD` | RFD skill, with the G2 report as evidence |

**Asking the human.** Ask with your runtime's native question tool (`AskUserQuestion` in Claude Code): one single-select question with the options `PASS`, `FEEDBACK` and `RFD`, and a free-text answer allowed (the tool's type-your-own-answer choice). If the runtime has no question tool, ask the same question in chat and wait for the reply; never assume or default an answer. A standalone continuation alias is not a verdict: ask the human to choose `PASS`, `FEEDBACK` or `RFD` and write no HITL until that decision exists. Any answer is recorded verbatim; any other typed answer that does not choose `PASS` or `RFD` counts as `FEEDBACK`, never as `PASS`, and its text is the feedback. Then ask who is deciding, unless the human already said. A FEEDBACK answer names module defect or design defect; ask if it does not.

## Report Contract

Write only `.codeanvil/report/<cycle-name>/G2.md`, append-only, and on PASS
`.codeanvil/report/<cycle-name>/G2_artifacts/verified_prototype.md` filled from the template.
Diagnostic artifacts may be kept under `G2_artifacts/`; they do not become report states.

- First run: header plus `## Iteration 1`; later runs append `## Iteration <N>`.
- Header: a `| Field | Value |` table with `Gate` = `G2`, `Cycle`, `Document` (the `test_run.md`
  path) and `Created` = `codeanvil now`.
- Iteration: a `| Field | Value |` table with `Date` = `codeanvil now`, `Timestamp` =
  `codeanvil now --machine`, `Iteration`, `Cycle`, `Verifier` (`vsil-verifier` or
  `fresh session`), and exactly one row written as `| HITL | PASS |` or `| HITL | FEEDBACK |`.
  Then `### Description`.
- The Description starts with the exact line `Based on: S2 iteration <N>`, where `N` is the latest
  S2 iteration when verification starts, followed by the declared levels and the results table.
- On a module-defect FEEDBACK, write in the `### Description` (right after the `Based on:` line) an
  explicit, enumerated list of the concrete changes S2 must make — which `SUB-nnn`/module and file,
  and what to change — so S2 applies exactly that list without re-asking the human. The gate report
  is already the only gate-to-stage channel, so this adds no new channel, data structure or
  communication software: S2 edits only what the list names, with no AskUser prompt and no redesign.
- Honesty declaration: VERIFIED for VL-0 and VL-1 claims; VALIDATED only for VL-2 claims.
- For FEEDBACK, explain command/target, actual result, expected criterion, relevant logs/measures,
  technical cause (or unconfirmed hypothesis), affected requirement/module/kit/PATH, concrete next
  action and route. Module/kit defect goes to S2; design defect goes through S1 → G1 → S2;
  infeasibility goes to RFD, all in the existing cycle/rework rules. An operational HW/environment
  problem is not a defect: classify it by the operational-vs-defect branch above and re-run G2,
  never with a product-defect label. New S2 delivery is required before
  rerunning G2 after module feedback on the same Based-on iteration.
- G2 is a **gate**: its `PASS` is the human's verdict.

## Output Contract

Return the results table (flagged rows first), the honesty declaration, the human's answer, the
report path with the iteration number, and the route.

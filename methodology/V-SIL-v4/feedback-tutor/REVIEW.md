# Tutor Feedback — V-SIL v4 Skills Review

**Branch:** `fix/tutor-feedback` (from `main`, v3-compatible)
**Date:** 2026-11-17
**Reviewer:** Tutor

---

## How to use this file

For each skill reviewed, add a section below with:
1. **Raw issues** — what the tutor found (verbatim or paraphrased)
2. **Correction plan** — what needs to change and where
3. **Correction log** — commit hash and what was done

---

## Skills to review

| Skill | Folder | Status |
|---|---|---|
| S0_normalise_build_package | [S0/](S0/) | ✅ done |
| G0_valid_req_and_GT | [G0/](G0/) | ⬜ pending |
| S1_design_system | [S1/](S1/) | ⬜ pending |
| G1_design_review | [G1/](G1/) | ⬜ pending |
| S2_implement_subsystems (v3) | [S2/](S2/) | ⬜ pending |
| G2_adaptive_verification (v3) | [G2/](G2/) | ⬜ pending |
| RFD_request_for_deviation | [RFD/](RFD/) | ⬜ pending |

---

## S0_normalise_build_package

### Raw issues

**Note:** The tutor's tool reads only `SKILL.md` in isolation, without access to the rest of the system (`codeanvil` CLI, scaffold structure, `TRIAGE.md`, GT blueprints, `AGENTS.md`, `reports.py`, or the scaffolded project layout). Issues that stem from this missing context are marked INVIABLE.

**T1 · Draft mode state transition** (execution error)
> The skill states "The recorded S0 run… happens only when the human commits the draft", but provides no mechanism for the LLM to detect this commit.

Verdict: **VALID.** The skill says "when the human commits the draft" but never defines the trigger. The DRAFT sentinel file is mentioned as an entry condition (`DRAFT` exists → draft mode) but there is no step saying "when the human deletes `DRAFT` or tells you to commit, then write the iteration". The LLM has no actionable transition.

**T2 · Re-entry cycle discovery** (execution error)
> The instruction says "if another cycle's latest RFD.md iteration holds Superseded by cycle: <this cycle>" but does not instruct the LLM on how to find this other cycle.

Verdict: **VALID.** Step 4 describes the condition but not the file-system traversal: `ls .codeanvil/report/*/RFD.md`, read each, check the `Superseded by` line. Without explicit globbing instructions, the LLM must guess the discovery mechanism.

**T3 · Contradictory inventory output** (execution error)
> Steps say "Inventory every statement… as STK | HWC | NRM | SYS | not mapped." Output Contract says "Return… the inventory counts". Report Description says "the inventory, the missing list… and the trace". Unclear whether "inventory" means the full mapping or just counts.

Verdict: **VALID.** Three references to "inventory" with different implied granularity. The report Description (step 5) says "the inventory" (full), the Output Contract says "inventory counts" (summary). The LLM will produce one or the other inconsistently.

**T4 · Dynamic template alteration vs. "Fill the blueprint"** (concept error)
> The skill commands "Fill the StRS blueprint" but also "Drop the author-guidance sections… and every empty blueprint placeholder row". This requires structural judgement, violating "no judgement".

Verdict: **PARTIALLY VALID.** The tutor is right that "fill" + "drop sections" is a tension. However, the Hard Rules enumerate the exact section names and placeholder patterns to drop (`### Block ID Convention`, `### Fields per Block`, `### Enumeration Values`, `### Block Format`, `_What this document specifies…_`, `_TERM_ | _Precise definition_`, `_Brief description…_`, `[TYPE]-[SUB]-[NNN]`). This is a finite, enumerated list — not open-ended judgement. The concept is sound but the execution could be clearer: frame it as "copy the blueprint, then delete these exact patterns" rather than "fill and drop".

**T5 · Unverifiable CLI dependencies** (unverifiable)
> The skill relies on `codeanvil backup S0`, `codeanvil now`, `codeanvil status`. If these are not installed, the skill fails.

Verdict: **INVIABLE.** The tutor's tool cannot see the system. `codeanvil` is the tool that scaffolds the project and runs the skills — it is always present by construction. The CLI commands exist and are tested (`codeanvil backup`, `codeanvil now`, `codeanvil status` all confirmed). Skills run inside scaffolded projects where the tool is a hard prerequisite.

### Correction plan

| ID | Issue | Fix | Where |
|---|---|---|---|
| T1 | Draft mode has no exit trigger | Add explicit step: "When the human says 'commit the draft' or deletes `.codeanvil/report/<cycle>/DRAFT`, exit draft mode and write the recorded iteration per the Report Contract." | SKILL.md §Draft mode |
| T2 | Re-entry cycle discovery has no file traversal | Add explicit glob: "List `.codeanvil/report/*/RFD.md`, read the latest iteration of each, and check for `Superseded by cycle: <this cycle>`." | SKILL.md §Prerequisite step 4 |
| T3 | "Inventory" has three conflicting definitions | Unify: the step produces the full categorized mapping; the report Description includes the full mapping; the Output Contract returns the full mapping + counts. | SKILL.md §Steps, §Report Description, §Output Contract |
| T4 | "Fill + drop" tension | Reframe: "Copy the blueprint skeleton. Delete the following enumerated guidance patterns: [list]. Then fill each remaining section from the Build Package." Makes the order explicit: copy → delete → fill. | SKILL.md §Hard Rules + §Steps |
| T5 | CLI not verified | INVIABLE — no fix needed |

### Correction log

- **T1 fix:** Added explicit "Exiting draft mode" paragraph with two triggers (human says "commit the draft" OR deletes the DRAFT file) and the action (reconcile, write iteration, delete DRAFT).
- **T2 fix:** Step 4 now starts with "list every directory in `.codeanvil/report/` and read the latest iteration of each `RFD.md` found" before checking the `Superseded by` condition.
- **T3 fix:** Unified "inventory" across three locations: step 1 defines it as a full categorized mapping with counts as a summary line; step 5 says "full inventory + counts + missing list + trace"; Output Contract says "full inventory mapping, counts summary, missing list".
- **T4 fix:** Reframed "Emit spec, not blueprint scaffolding" as three ordered steps: (1) copy skeleton, (2) delete enumerated guidance patterns, (3) fill from Build Package. No open-ended judgement.
- **T5:** INVIABLE. `codeanvil` CLI is the tool that scaffolds and runs the project — always present by construction.

---

## G0_valid_req_and_GT

### Raw issues

_— pending tutor feedback —_

### Correction plan

### Correction log

---

## S1_design_system

### Raw issues

_— pending tutor feedback —_

### Correction plan

### Correction log

---

## G1_design_review

### Raw issues

_— pending tutor feedback —_

### Correction plan

### Correction log

---

## S2_implement_subsystems

### Raw issues

_— pending tutor feedback —_

### Correction plan

### Correction log

---

## G2_adaptive_verification

### Raw issues

_— pending tutor feedback —_

### Correction plan

### Correction log

---

## RFD_request_for_deviation

### Raw issues

_— pending tutor feedback —_

### Correction plan

### Correction log

# Tutor feedback v2 — V-SIL v4 skills

**Branch:** `fix/tutor-feedback-v2`
**Baseline:** `93420664ca0b2d4c51d305e35dd592ec006d4718`
**Status:** AGENTS initial triage and own corrections complete; skill reviews pending.

## Skills to review

| ID | Current source skill | Folder | Status |
|----|----------------------|--------|--------|
| S0 | [S0_normalise_build_package](../../../templates/skills/S0_normalise_build_package/SKILL.md) | [S0/](S0/) | Pending |
| G0 | [G0_valid_req_and_GT](../../../templates/skills/G0_valid_req_and_GT/SKILL.md) | [G0/](G0/) | Pending |
| S1 | [S1_design_system](../../../templates/skills/S1_design_system/SKILL.md) | [S1/](S1/) | Pending |
| G1 | [G1_design_review](../../../templates/skills/G1_design_review/SKILL.md) | [G1/](G1/) | Pending |
| S2 | [S2_plan_modules](../../../templates/skills/S2_plan_modules/SKILL.md) | [S2/](S2/) | Pending |
| G2 | [G2_plan_review](../../../templates/skills/G2_plan_review/SKILL.md) | [G2/](G2/) | Pending |
| S3 | [S3_implement_modules](../../../templates/skills/S3_implement_modules/SKILL.md) | [S3/](S3/) | Pending |
| G3 | [G3_adaptive_verification](../../../templates/skills/G3_adaptive_verification/SKILL.md) | [G3/](G3/) | Pending |
| RFD | [RFD_request_for_deviation](../../../templates/skills/RFD_request_for_deviation/SKILL.md) | [RFD/](RFD/) | Pending |

Cross-cutting instructions review (not an additional stage):

| Item | Current source | Folder | Status |
|------|----------------|--------|--------|
| AGENTS.md | [Template](../../../templates/AGENTS/TEMPLATE_AGENT.md) | [AGENTS/](AGENTS/README.md) | Initial triage/fixes complete; tutor patches not supplied |

Use the [same per-skill workflow](README.md#workflow) as the first round.
For each review, record the actual source revision and supplied context before
adding findings. Mark a review done only after its corrections and verification
are recorded; proposals and rejected patches remain distinguishable from fixes.

## AGENTS.md

### Raw issues
Original audit and four SVGs moved unchanged from `raw-AGENTSmd/` to [AGENTS/raw/](AGENTS/raw/).
The target `SKILL_pre_david.md` and instrument `Navaja_(6).md` were not supplied.
Baseline for local contrast: `2af198d532986ffef70da40c20e140e228a3584d`.
See [EXPLAIN.md](AGENTS/EXPLAIN.md) for all eleven findings and contextual evidence.

### Correction plan
Five valid contract defects: N-01 admission exceptions, N-02 cycle/status binding,
N-03 closed selection, N-05 hardware wording and N-07 S2 delivery semantics.
N-08 is a partial recovery limitation; N-04/N-06/N-09/N-10/N-11 do not establish
methodology defects with the tutor's limited context. Clarify existing scope,
recovery and author-authority contracts without adding gates or an orchestrator.

### Correction log
Applied to the source template in `e44d7c000b69ebe807b0f42653ebff53d5437fc5`.
Focused verification: 135 tests passed; synthetic two-cycle probe confirms N-02.
No human gate or hardware validation occurred. Await actual tutor patches before
creating `corrected/PATCHES.md` and its patch-by-patch `ANALYSIS.md`.

## S0_normalise_build_package

### Raw issues
Pending tutor feedback.

### Correction plan
Pending triage.

### Correction log
No corrections applied.

## G0_valid_req_and_GT

### Raw issues
Pending tutor feedback.

### Correction plan
Pending triage.

### Correction log
No corrections applied.

## S1_design_system

### Raw issues
Pending tutor feedback.

### Correction plan
Pending triage.

### Correction log
No corrections applied.

## G1_design_review

### Raw issues
Pending tutor feedback.

### Correction plan
Pending triage.

### Correction log
No corrections applied.

## S2_plan_modules

### Raw issues
Pending tutor feedback.

### Correction plan
Pending triage.

### Correction log
No corrections applied.

## G2_plan_review

### Raw issues
Pending tutor feedback.

### Correction plan
Pending triage.

### Correction log
No corrections applied.

## S3_implement_modules

### Raw issues
Pending tutor feedback.

### Correction plan
Pending triage.

### Correction log
No corrections applied.

## G3_adaptive_verification

### Raw issues
Pending tutor feedback.

### Correction plan
Pending triage.

### Correction log
No corrections applied.

## RFD_request_for_deviation

### Raw issues
Pending tutor feedback.

### Correction plan
Pending triage.

### Correction log
No corrections applied.

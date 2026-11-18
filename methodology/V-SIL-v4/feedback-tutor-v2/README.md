# feedback-tutor-v2/ — Second tutor review

Audit workspace for the current V-SIL v4 skills on `fix/tutor-feedback-v2`.
Baseline: `93420664ca0b2d4c51d305e35dd592ec006d4718`.
The [first round](../feedback-tutor/README.md) remains historical and unchanged.
See [REVIEW.md](REVIEW.md) for the skill index and progress.

## Structure and conventions

This round keeps the first round's names: `EXPLAIN.md`, `corrected/PATCHES.md`,
and `corrected/ANALYSIS.md`. Each stage/gate has its own directory:
`S0/`, `G0/`, `S1/`, `G1/`, `S2/`, `G2/`, `S3/`, `G3/`, and `RFD/`.
Every directory already contains `corrected/`; `.gitkeep` preserves empty folders.

| File | Contents | Created when |
|------|----------|--------------|
| `REVIEW.md` | Per-skill status, raw issues, correction plan and correction log. | Now; all reviews are pending. |
| `<ID>/EXPLAIN.md` | Findings, explanation in Spanish, viability and proposed/applied correction. | Tutor findings arrive. |
| `<ID>/corrected/PATCHES.md` | Original tutor correction output, saved verbatim. | Tutor patches arrive. |
| `<ID>/corrected/ANALYSIS.md` | Patch-by-patch accept/reject reasoning and summary. | Patches are analysed. |

No findings, patches, scores or acceptance results have been carried over from
the first round. Empty review files are created only when their inputs exist.

## Workflow

1. Identify the reviewed skill and its revision in `REVIEW.md`; record which
   references or project instructions the tutor actually received.
2. Receive findings and write `EXPLAIN.md`. Keep the familiar classifications
   **VÁLIDO**, **PARCIALMENTE VÁLIDO**, and **INVIABLE**, with evidence from the
   current methodology and scaffold. Missing tutor context alone does not prove
   or disprove a defect.
3. Save original tutor patches in `corrected/PATCHES.md` without editing them;
   analyse each one in `corrected/ANALYSIS.md`.
4. Apply accepted corrections to the linked source skill, record the commit and
   relevant verification, then update the review status. Preparing these folders
   does not apply any correction or run a methodology cycle.

S2/G2 now mean module planning and plan review; implementation and verification
belong to S3/G3. RFD remains outside the chain. This is a harness audit workspace,
not a scaffolded project's gate report or a new gate verdict.

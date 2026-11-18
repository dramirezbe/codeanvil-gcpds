# feedback-tutor/ — Tutor Review of V-SIL Skills

External tutor review of each V-SIL skill's `SKILL.md`, with triage, corrections, and
traceability. The tutor's tool reads **only** `SKILL.md` in isolation — it has no access
to the `codeanvil` CLI, scaffold structure, referenced files, or the project layout.

## Structure

```
feedback-tutor/
├── README.md              ← this file
├── REVIEW.md              ← index: one row per skill with status and folder link
├── S0/
│   ├── EXPLAIN.md         ← our triage of the tutor's raw findings (Spanish)
│   └── corrected/
│       ├── PATCHES.md     ← raw tutor output: diff patches + resolution ledger
│       └── ANALYSIS.md    ← patch-by-patch verdict: accept or reject, with reasoning
├── G0/corrected/
├── S1/corrected/
├── G1/corrected/
├── S2/corrected/
├── G2/corrected/
└── RFD/corrected/
```

## Per-skill folder contents

Each `<SKILL>/` folder holds:

| File | What it contains | When it is written |
|------|------------------|--------------------|
| `EXPLAIN.md` | For each tutor finding: raw quote, explanation in Spanish, viability verdict (VÁLIDO / PARCIALMENTE VÁLIDO / INVIABLE), and correction applied (or why not). | After receiving the tutor's initial findings |
| `corrected/PATCHES.md` | Raw output from the tutor's correction tool: numbered patches (P-01, P-02, …), old/new snippets, rationale, and a resolution ledger. Saved verbatim — no edits. | After receiving the tutor's corrected version |
| `corrected/ANALYSIS.md` | Our patch-by-patch analysis: accept or reject each patch with technical reasoning. Includes a summary table. | After analyzing the corrected version |

## Workflow for each skill

1. **Receive tutor findings** → create `<SKILL>/EXPLAIN.md` with triage.
2. **Apply our own fixes** to the actual `templates/skills/<SKILL>/SKILL.md` based on valid findings.
3. **Receive tutor corrected version** → save verbatim in `<SKILL>/corrected/PATCHES.md`.
4. **Analyze patches** → write `<SKILL>/corrected/ANALYSIS.md` with accept/reject verdicts.
5. **Apply accepted patches** to the actual skill. Run tests.
6. **Update `REVIEW.md`** status to ✅ done.

## Viability classification

The tutor's tool sees only `SKILL.md`. Findings that require system context are classified:

- **VÁLIDO** — real issue, actionable from the skill text alone.
- **PARCIALMENTE VÁLIDO** — the concern is real but the skill already addresses it in a way the tool cannot see (e.g., enumerated lists that look like open-ended judgement).
- **INVIABLE** — requires context the tool does not have (e.g., `codeanvil` CLI existence, scaffold path rewriting, referenced files).

Inviable findings may still get a documentation fix (e.g., adding `runtime:` to frontmatter) to make the skill self-documenting for isolated readers.

## Branch

All work lives on `fix/tutor-feedback` from `main` (v3-compatible). Corrections target the
v3 skills in `templates/skills/`, not the v4 renames on `feat/vsil-v4`.

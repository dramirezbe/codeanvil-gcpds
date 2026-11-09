# T1 HackRF-spectrum — seeded faults (test-harness oracle)

**Do not copy this file into the scaffolded project.** It stays in the repo test case. It is the
comparison oracle for the triage + draft-mode acid test: it records the small faults planted in
`build_package.md` on purpose, where each should be caught, and what good triage looks like. The
running agent (opencode) must never see it.

The faults are small and look like genuine author mistakes — none is announced in the Build
Package. The run is a success when the new **failure triage** translates each into a plain-language
problem with reconciliation options, and **draft mode** lets them be fixed without a report
iteration per edit.

Anything the flow surfaces that is **not** listed here is either a real latent defect in the Build
Package (worth recording) or agent noise (worth noting) — both are useful signal.

## Planted faults

| ID | Where in build_package.md | The fault | Expected catch | What good triage should say |
|----|---------------------------|-----------|----------------|-----------------------------|
| F1 | A.3 · R2 `depends on … H8, H9` | R2 declares a dependency on constraint **H9**, which does not exist — constraints are H1–H8 and C1. Looks like an author miscount of the gain/parameter constraints. | **G0** deterministic cross-reference ERROR (dependency to an unknown block id), forcing exit 1 → draft loop. If S0 does not lift the prose dependency into the block field, it falls to **G1** DAG review instead. | "R2 says it depends on H9, but there is no H9 — the constraints stop at H8. Nobody can trace R2's parameter control to a real limit." Options: connect to the intended constraint (likely H1, the tuning range, or drop H9), create H9 if a real constraint is missing, or remove the dangling dependency. |
| F2 | A.2 · N3 empty `Clause` cell | N3 obliges staying within the tuning range but cites no clause/section — the `Clause` cell is blank. Looks like the author could not find the exact datasheet section. | **S0 missing list** → **Gate H** triage (placeholder, not a G0 exit-1 error). | "N3 requires staying in the tuning range but points at no source section, so the obligation cannot be checked against anything." Options: cite REF-001 §Specifications (the datasheet range), mark it a project constraint derived from H1, or ask the author for the exact clause. |
| F3 | A.3 · R5 empty `Acceptance` cell | R5 (throughput / dropped-sample indicator) has no acceptance criterion — the cell is blank. The author knew the feature but did not pin the pass condition. | **S0 missing list** → **Gate H** triage. | "R5 asks for a dropped-sample indicator but says nothing about when it passes, so it is not verifiable." Options: connect it to Y9's existing criterion (dropped-sample growth visible within one update) — the natural fix, since Y9 already defines the behavior — or state a fresh criterion, or downgrade R5's priority. |

## Notes for the review after the run

- F1 is the one meant to force **draft mode**: a G0 exit-1 error is the clearest trigger for the
  "edit directly, lint, loop without recording" loop. Watch whether opencode offers the `DRAFT`
  marker and loops, or whether it writes a FEEDBACK iteration per edit (old behaviour).
- F2 and F3 are missing-list items: they test triage at **Gate H**, where there is no exit code —
  the agent must still translate them and offer options before asking the human the Gate H
  question.
- Check that in every case the **verdict stays human / exit-code**, never the agent's: triage must
  not pre-approve or auto-fix. The agent interprets; the human chooses.
- Compare the `.codeanvil/report/<cycle>/` iterations against this table after the run and record
  the result in a `SECOND_FULL_FLOW_<date>` note, as the first run was archived.

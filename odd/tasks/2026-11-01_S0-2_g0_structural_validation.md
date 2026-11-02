# Plan — Skill S0-2: G0 Structural Validation + Gate H

Feature: `odd/tasks/2026-11-01_2235_no_tools_skills_v3.md` · Specs S1, S2, S3, S6 · Task T3
Target file: `templates/no-tools-skills/v3/S0-2_SKILL.md`

## Objetivo

Chat-only (non-deterministic) emulation of the deterministic G0 gate
(`g0_validate.py`): validate the StRS + SyRS pair for headings, metadata, block fields,
intra-StRS cross-checks and the G0-X cross-document rules; emit a binary verdict;
on PASS run the human **Gate H** ("Requirements complete, bounded, and verifiable?")
before S1 may start.

## Mapeo V-SIL-v3

| Paper | Element |
|-------|---------|
| §4 G0 | P1 Headings · P2 Metadata · P3 Block fields · P4 Cross-doc G0-X; exit 0 → PASS → Gate H; exit 1 → FAIL → edit GT |
| §4 FAIL edge | "validate vs original Build Package" → S0 (S0-1) |
| P1 | Gate H is an authorisation barrier (human only) |
| P3 | mechanical rejection beats LLM approval: any rule failure = FAIL, no "looks fine" override |

## Inputs

| Input | Source | Required |
|-------|--------|----------|
| `G0_StRS.md` | S0-1 or user | yes |
| `G0_SyRS.md` | S0-1 or user | yes (G0 is the pair — refuse partial run) |
| Original Build Package | S0-1 / user | optional — not used by the checks (G0 is structural only) |

## Outputs

1. Per-document G0 VALIDATION REPORT (StRS, SyRS) — v2 format, unchanged.
2. G0-X CROSS-DOCUMENT REPORT.
3. `G0 GATE VERDICT: PASS | FAIL`.
4. FAIL → Fix List (Block ID → what is wrong → valid values) + routing line
   `→ S0 (S0-1): correct the GT against the original Build Package`.
5. PASS → **Gate H prompt** (exact text) and its recorded outcome:
   `GATE H: AUTHORISED` (paper §2 "G0 PASS + Gate H → S1" → S1-1) /
   `GATE H: NOT AUTHORISED` (no S1 entry; the only back-edge from G0 is to S0, paper §4).
   NOT AUTHORISED asks the human for numbered reasons, each tagged with block ID(s); the
   block is pasted into S0-1 together with the Build Package.
6. On authorisation: the **`G0 RECORD`** block (C3): doc IDs + versions, G0 verdict,
   Gate H outcome/date/authoriser, and the **block inventory** (every NRM/HWC/STK/SYS ID
   with its Status). S1-1 compares the GT pasted later against this inventory (m6),
   since chat cannot hash files.

## Activation Contract (C1)

**Load when:** the user pastes a StRS + SyRS pair and asks for G0, structural validation,
or GT review.
**Do NOT load when:** the user asks to write/fix the GT (→ S0-1), asks about requirement
quality or metrology (later gates), or pastes only one document (ask for the other; refuse a
partial G0 — v2 rule).
**Context pack (C7):** StRS + SyRS only, new chat (the author of the GT must not be its
checker — P2). Disclaimer C6 included.

## Prompt template (resumido)

```
Step 1  Detect type (StRS | SyRS | UNDETECTABLE → stop)
Step 2  Phase 1 headings      (StRS 18 headings, SyRS 15 headings)
Step 3  Phase 2 metadata      (Document ID, Project, Organization, SemVer, Classification; placeholder rule)
Step 4  Phase 3 blocks        (NRM/HWC/STK/SYS field + enum rules)
Step 5  Phase 4 cross-checks  (StRS intra + G0-X)
Step 6  Reports + verdict
Step 7  Gate H (only on PASS):
        GATE H — HUMAN AUTHORISATION
        Are the requirements complete, bounded, and verifiable?
          y — Authorise. GT is frozen as the S1 design basis.
          N — Not authorised; return to S0 with reasons. (default)
        [y/N]:
```

Gate H answer handling mirrors v2's GT approval prompt: questions are answered and the
prompt re-presented; "go ahead"/"continue" is not `y`; ambiguous input → re-ask.

## Criterios de aceptación

1. All v2 G0 rules (headings, metadata, NRM/HWC/STK/SYS, intra, G0-X) are present
   verbatim in meaning; no rule weakened, none added that the deterministic script lacks.
2. Non-determinism disclaimer present (v2 convention).
3. Verdict rules: zero errors → PASS; any error → FAIL; UNDETECTABLE → FAIL and stop.
4. The skill never edits the GT and never suggests rewording (v2 rule kept).
5. Gate H is shown only after PASS and needs an explicit `y` (closed domain, C2).
6. The G0 RECORD inventory lists exactly the block IDs found in Phase 3, with Status.
7. Test: `test-inputs/G0_StRS.md` + `G0_SyRS.md` → `G0 GATE VERDICT: PASS`
   (expected 0 errors; warnings allowed).
8. Test: fixture `F1_G0_fail_StRS.md` (T2b) + the valid SyRS → `G0 GATE VERDICT: FAIL`
   with a Fix List naming each of the 5 seeded errors, and no Gate H prompt.

## Dependencias

- Upstream: S0-1 (or hand-authored GT).
- Downstream: S1-1 (needs PASS + Gate H AUTHORISED + G0 RECORD); S0-1 on FAIL or Gate H
  NOT AUTHORISED.

## Design notes

- Source: `templates/no-tools-skills/v2/G0_SKILL.md` — rules copied; definitions updated
  (G1 is now DAG + contract validation, not SRS synthesis; SRS no longer produced).
- Gate H is new in v3 (paper §4 last paragraph).

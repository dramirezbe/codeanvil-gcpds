---
name: g0-valid-req-and-gt
description: "Trigger: G0, validate SRS, validate HCS, GT structural check, IEEE 29148. Deterministically validate Ground Truth structure; returns a line-numbered report."
license: Apache-2.0
compatibility: "Requires Python 3.9+ (stdlib only). No network access, no filesystem writes."
metadata:
  author: "gcpds"
  version: "1.0"
  gate: "G0"
  pipeline: "V-SIL"
---

# G0 — Structural Validation of Ground Truth Documents

## Activation Contract

Load this skill when a V-SIL **Ground Truth document** (SRS or HCS `.md` file) needs
structural validation **before** any AI-driven gate runs, or when a G0 result must be
deterministic and reproducible.

Do **not** load it to judge requirement quality, constraint accuracy, or SRS↔HCS consistency —
those are later gates.

## Hard Rules

- **Run the script.** Never re-implement or hand-wave these checks in prose:
  `python templates/skills/G0_valid_req_and_GT/scripts/g0_validate.py <file> [<file> ...]`
- **The exit code is the gate verdict.** `0` pass, `1` errors block, `2` script error. Never
  record G0 as passed on exit `1` or `2`.
- **Errors block; warnings do not.** Report every ERROR. Never downgrade or suppress one.
- **Never edit a GT document to make G0 pass** without the author's explicit confirmation.
- **Validate against the templates**, never assumptions: `templates/GT/G0_SRS.md`,
  `templates/GT/G0_HCS.md`.
- The validator is **stdlib-only and side-effect free** — it reads GT files and prints to
  stdout; never patch it to write to the documents it checks.

## Decision Gates

| Situation | Action |
|-----------|--------|
| Exit `0` | Record `G0: PASS`. Surface warnings as advisory; proceed to the next gate. |
| Exit `1` | Record `G0: FAIL`. Return the report verbatim so each ERROR is fixable by line + block ID. |
| Exit `2` | Script error (bad args, unreadable file, undetectable doc type). Fix the invocation or the type heading, re-run. Record **no** verdict. |
| Multiple GT files | Pass all in one invocation; exit code is the worst result, each file gets its own report. |
| Finding needs context | Read the reported file and line; `Line` + block ID locate it. |

## Execution Steps

1. Confirm each target file exists and is a GT `.md` document (SRS or HCS).
2. From the repository root, run the validator with every file to check.
3. Capture **stdout** (the report) and the **exit code**.
4. Map the exit code through the Decision Gates table above.
5. Return the report plus the verdict. For each ERROR, quote file, line number, block ID,
   message, and `Expected:` value so the fix needs no re-read.

## Output Contract

Return all four:

1. **Verdict** — `G0: PASS` or `G0: FAIL (N errors, M warnings)`.
2. **The full validation report** exactly as printed by the script.
3. **Fix list** — when there are ERRORs, one entry per error: file · line · block ID ·
   message · expected value.
4. **The observed exit code.**

## References

- [references/RULES.md](references/RULES.md) — full Phase 1–4 rule tables, required sections,
  enum values, block/field formats, the report format, and the script's internal architecture.
- `scripts/g0_validate.py` — the deterministic validator (Python 3.9+, stdlib only).
- `templates/GT/G0_SRS.md`, `templates/GT/G0_HCS.md` — the authoritative structure definitions
  (paths relative to the repository root).

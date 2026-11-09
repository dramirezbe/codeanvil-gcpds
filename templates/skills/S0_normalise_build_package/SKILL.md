---
name: s0-normalise-build-package
description: "Trigger: S0, Build Package, normalise, StRS, SyRS. Cast .codeanvil/GT/build_package.md into the two IEEE 29148 blueprints (StRS.md, SyRS.md) in one pass, with no judgement, and write the S0 report."
license: Apache-2.0
compatibility: "No network access, no scripts. Writes .codeanvil/GT/StRS.md, .codeanvil/GT/SyRS.md and .codeanvil/report/<cycle-name>/S0.md."
metadata:
  author: "gcpds"
  version: "1.0"
  gate: "S0"
  pipeline: "V-SIL"
---

# S0 — Build Package Normalisation

S0 **normalises only**. It copies what the Build Package says into the two blueprints. It
never judges, completes or improves the content. Iteration happens at G0.

## Prerequisite and Cycle

S0 has **no prerequisite**: it is the entry point of the V-SIL chain.

1. Resolve the active cycle from `.codeanvil/project.yaml` (the `cycle:` key). If it is
   missing, stop and ask the user for a cycle name (see `AGENTS.md`, `## Cycle`).
2. If the latest iteration of `.codeanvil/report/<cycle-name>/RFD.md` holds a line
   `Superseded by cycle: <name>`, this cycle is **closed** by an RFD and read-only: return exactly
   `Cycle closed by RFD. Continue in cycle <name>.` and write nothing.
3. Create `.codeanvil/report/<cycle-name>/` when it does not exist.
4. **After an RFD:** if another cycle's latest `RFD.md` iteration holds
   `Superseded by cycle: <this cycle>`, this is the re-entry cycle and the whole flow is redone from
   here. Compute the SHA-256 of `.codeanvil/GT/build_package.md`
   (`python -c "import hashlib,sys;print(hashlib.sha256(open(sys.argv[1],'rb').read()).hexdigest())" .codeanvil/GT/build_package.md`).
   If it equals that RFD's `Build Package digest:` line, return exactly
   `Build Package unchanged since the RFD. Update .codeanvil/GT/build_package.md first.` and write nothing.
   A digest of `none` (the RFD was decided on a hand-written pair) skips this check.

**Draft mode.** If `.codeanvil/report/<cycle-name>/DRAFT` exists, S0 runs in draft mode: apply the
human's requested GT changes — re-normalise from the Build Package, or help edit the GT pair
directly — run Triage ([references/TRIAGE.md](references/TRIAGE.md)) on anything the Build Package
does not supply, and write **no** iteration. The recorded S0 run (Report Contract below) happens
only when the human commits the draft, which also reconciles any direct GT edits against the Build
Package (TRIAGE.md §2). While drafting, the digest and overwrite checks above do not block.

## Inputs

| Path | Role |
|------|------|
| `.codeanvil/GT/build_package.md` | User-authored. The only content source |
| `templates/skills/S0_normalise_build_package/templates/StRS.md`, `.../SyRS.md` | This skill's locked blueprints. Never edit them |
| `.codeanvil/report/<cycle-name>/G0.md` | Re-entry only: the latest FEEDBACK |
| `references/TRIAGE.md` | Failure triage + draft mode, shared with G0 and G1 |

## Decision Table

| Situation | Action |
|-----------|--------|
| `.codeanvil/GT/build_package.md` present, no GT pair | Normalise |
| Build Package present, GT pair present, an `S0.md` exists in **any** cycle | Re-normalise, applying the latest G0 feedback (an RFD re-entry lands here) |
| Build Package present, GT pair present, no `S0.md` in any cycle | Hand-written pair: ask once before overwriting it |
| No Build Package, GT pair present | No-op iteration: "pair supplied as normalised input". Write nothing to `.codeanvil/GT/` |
| Neither | Stop and ask the user for `.codeanvil/GT/build_package.md` |

## Hard Rules

- Run in **one pass**, with no confirmation prompts, apart from the hand-written pair row.
- Copy numbers, units, standards and clauses **verbatim**.
- **Invent nothing.** A field the Build Package does not supply keeps its blueprint
  placeholder and goes on the missing list. G0 does not reject a placeholder inside a
  block body, so the missing list is what shows it: the author supplies the content.
- Copy `Status`, `Compliance` and STK `Standard(s)` from the Build Package; never infer
  them. Where the blueprint has an enum marker, use `PENDING` or `PROPOSED`. Never fill a
  field by vocabulary heuristic.
- Laboratory procedures, calibration and tolerances go into `.codeanvil/GT/SyRS.md`: procedures to
  §6 as `PROTO-NNN` rows, calibration to §4, tolerances to §5. Never invent one. When the
  Build Package has none for a section, write exactly
  `Not applicable: no lab inputs in the Build Package.` under its heading and keep the heading.
- Give no verdict and no comment on sufficiency, realism or scope.
- Write only the two GT files and `S0.md`. Never touch `.codeanvil/GT/build_package.md`.

## Steps

1. Inventory every statement of the Build Package as `STK | HWC | NRM | SYS | not mapped`.
2. **Back up before overwriting.** Run `codeanvil backup S0` from the project root. If it exits
   nonzero, stop and show its message; write no iteration. Cite the printed backup path in the
   iteration's Description. Backups never cover `src/` or `verification/`: code recovery relies
   on git.
3. Fill the StRS blueprint.
4. Fill the SyRS blueprint, including `Traces to` from the Build Package's own links.
5. Build the report Description: the inventory, the **missing list** (every placeholder
   left, as `<file> · <block ID> · <field>`) and the trace from each block to its
   Build Package line.
6. Write the iteration with the row `| HITL | PASS |` (see `## Report Contract`) and return:
   `S0 complete. Run the G0 skill.`

## Re-entry

When the latest `G0.md` iteration is `FEEDBACK`, run Triage
([references/TRIAGE.md](references/TRIAGE.md)) on each reason first: present the real problem and
reconciliation options, and let the human choose. Then match each reason to its Build Package
line. If the content exists there, correct the GT block. If not, list it as
"needs Build Package content" and leave the block unchanged. A re-run after G0 passed makes
`codeanvil status` mark G0 stale, so G0 runs again.

## Report Contract

Write exactly one file: `.codeanvil/report/<cycle-name>/S0.md`, append-only.

- First run: write the header and `## Iteration 1`. Later runs append `## Iteration <N>`.
- Header: a `| Field | Value |` table with `Gate` = `S0`, `Cycle`, `Document`
  (`.codeanvil/GT/build_package.md`) and `Created` = `codeanvil now`.
- Iteration: a `| Field | Value |` table with `Date` = `codeanvil now`, `Timestamp` =
  `codeanvil now --machine`, `Iteration`, `Cycle`, and exactly one verdict row,
  written as `| HITL | PASS |` (never `PASS | FEEDBACK` in one row, which
  `codeanvil status` reads as `UNKNOWN`). Then `### Description`.
- S0 is a **stage**: `PASS` means "output delivered". The human verdict belongs to G0's
  Gate H. S0 has no `Based on` line.

## Output Contract

Return the two GT paths, the inventory counts, the missing list, and the report path with
the iteration number.

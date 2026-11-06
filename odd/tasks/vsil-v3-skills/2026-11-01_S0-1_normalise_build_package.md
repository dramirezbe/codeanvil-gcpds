# Plan — Skill S0-1: Build Package Normalisation

Feature: `odd/tasks/2026-11-01_2235_no_tools_skills_v3.md` · Specs S1, S2, S3, S6 · Task T3
Target file: `templates/no-tools-skills/v3/S0-1_SKILL.md`
Shared contracts used: C0, C1, C3, C7 (feature doc).

## Objetivo

Cast the content of a Build Package (PRD with measurable constraints, COTS hardware
envelope, acceptance criteria, normative obligations) into the two IEEE 29148 Ground
Truth blueprints — `G0_StRS.md` (§9.4) and `G0_SyRS.md` (§9.5). Paper §3: "S0 **normalises
only** — it casts the Build Package content into the IEEE 29148 document blueprints and
makes no conceptual judgement about sufficiency or scope." "Any iteration happens
afterwards at G0, which validates the Build Package content against the deterministic gate
(the blueprint) — not by a review judgement here."

## Mapeo V-SIL-v3

| Paper | Element |
|-------|---------|
| §2 Stage-Gate Overview | `BP → S0` edge; re-entry `RFD → updated BP → S0` |
| §3 S0 — Normalisation and Ground Truth | the whole stage (fill blueprints; no judgement; iteration at G0) |
| §4 G0 | consumer of this skill's output; G0 FAIL routes back here ("validate vs original Build Package") |
| P2 (oracle ≠ generator) | S0-1 never validates its own output — it hands off to S0-2 |

## Activation Contract (C1)

**Load when:** the user pastes a Build Package (first entry, or updated after an RFD) or a
G0 FAIL / Gate H return together with the Build Package, and asks for normalisation, GT
authoring, StRS/SyRS drafting, or "S0".
**Do NOT load when:** the user already has a StRS + SyRS and wants them checked (→ S0-2);
asks for design (→ S1-1); asks whether a requirement is achievable or sufficient (S0 makes
no such judgement — Gate H is the human question, RFD the infeasibility route).
**Context pack (C7):** Build Package (+ G0 FAIL report or Gate H return on re-entry). S0-2
runs in a new chat (P2).

## Inputs

| Input | Source | Required |
|-------|--------|----------|
| Build Package (PRD, COTS envelope, acceptance criteria, obligations; may include a system-level technical annex) | user, pasted | yes — the **only** source of content |
| Previous G0 FAIL report (re-entry, paper §4 "FAIL → edit GT … validate vs original Build Package") | S0-2 | optional |
| Gate H not-authorised reasons (re-entry through the same S0 edge) | S0-2 | optional |
| Updated Build Package after an RFD (paper §9.2 "re-enters at S0") | Build Package author | optional |

## Outputs

1. **Build Package inventory** — a table classifying every BP statement as
   `STK` / `HWC` / `NRM` / `SYS` / `not mapped` with its source line.
2. **Missing-information list** — every blueprint field the BP does not supply. The field
   keeps its blueprint placeholder (e.g. `_X.Y.Z_`, `_TERM_`) or an explicit enum marker
   where the blueprint has one (`PENDING`, `PRELIMINARY`). S0-1 does not ask for, decide or
   invent the value: G0 will reject the placeholder and the BP author supplies the content
   (paper §3: iteration happens at G0).
3. **`G0_StRS.md`** — full document following the StRS blueprint (headings §1.1–§6,
   metadata table, NRM-/HWC-/STK- blocks with all G0 fields).
4. **`G0_SyRS.md`** — full document following the SyRS blueprint (§1–§7, measurand
   catalog, method rationale, normative mapping, SYS- blocks with `Traces to`), filled only
   from BP content.
5. **Normalisation trace** — BP statement → block ID / field mapping (so a G0 FAIL can be
   checked "vs original Build Package").
6. Handoff line: `S0 COMPLETE — submit both documents to S0-2 (G0) in a new chat.`

## Prompt template (resumido)

```
Step 0  Intake        "Paste the Build Package (and, on re-entry, the G0 FAIL report or
                       Gate H reasons)."
Step 1  Inventory     Table: # | BP statement (verbatim) | Class | Target block/field → pause.
Step 2  Missing list  Every blueprint field with no BP source → kept as placeholder/marker,
                       listed. No questions, no proposals. → pause.
Step 3  StRS          Emit G0_StRS.md → pause.
Step 4  SyRS          Emit G0_SyRS.md → pause.
Step 5  Trace + handoff  BP→block table; "S0 COMPLETE — run S0-2 in a new chat".
```

Behaviour rules:
- Verbatim preservation: BP numbers, units, standards and clauses are copied, never "improved".
- No invention: every value comes from the BP; anything else stays a placeholder and is
  listed (G0 decides, the BP author fixes).
- No judgement: S0 never comments on sufficiency, realism or scope.
- Re-entry: on a G0 FAIL report, each error is matched to its BP line; if the BP has the
  content, the GT is corrected; if not, the error is listed as "needs Build Package
  content" for the BP author.
- Output in chunks (one document per message) to avoid truncation (v2 convention).

## Criterios de aceptación

1. Every BP statement appears in the inventory with exactly one class.
2. Every StRS heading required by G0 (Step 2 of S0-2) is present; every SyRS heading too.
3. Every block carries every field G0 checks (STK: Type/Priority/Status/Verification/
   Standard(s)/Clause/Compliance/Description SHALL/Acceptance Criteria; NRM: concrete
   Standard + Clause; HWC: Component/Parameter/Limit type/Value(s)/Source/Source ref/
   Impact/Status; SYS: Type/Parameter/Method/Traces to/concrete Standard/Acceptance) —
   filled from the BP or left as a listed placeholder.
4. `Traces to` tokens reproduce the BP's own derivation links.
5. Every non-placeholder value traces to a BP line in the normalisation trace.
6. The skill never emits a PASS/FAIL verdict, never asks for or proposes values.

## Dependencias

- Upstream: none (entry point) — or S0-2 (G0 FAIL / Gate H not authorised) / updated BP after SX-1.
- Downstream: S0-2.
- Reference artefacts embedded in the skill: block field tables and enums from
  `templates/GT/G0_StRS.md` and `templates/GT/G0_SyRS.md` (template v4.0.0).

## Design notes

- v2 had no S0 skill (G0 assumed hand-authored GT). v3 adds S0 explicitly (paper §3).
- Companion Documents rows point to the S1 design document instead of the v2 SRS.
- Test vector: `test-inputs/build_package.md` carries the stakeholder content and a
  system-level technical annex (methods, parameters, corrections, uncertainty, protocols),
  so pure normalisation reproduces `test-inputs/G0_StRS.md` + `G0_SyRS.md`: same blocks,
  fields and values (BP items N#/R#/H#/A#/B#/C#/Y# map 1:1 to NRM/STK/HWC/SYS blocks;
  the `SUB` segment of each ID is assigned by S0 per the blueprint convention and may differ). Removing the annex must yield SyRS placeholders → G0 FAIL → S0.

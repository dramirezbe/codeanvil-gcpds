# Plan — Skill S0-1: Build Package Normalisation

Feature: `odd/tasks/2026-11-01_2235_no_tools_skills_v3.md` · Specs S1, S2, S3, S6 · Task T3
Target file: `templates/no-tools-skills/v3/S0-1_SKILL.md`

## Objetivo

Cast the content of a Build Package (PRD with measurable constraints, COTS hardware
envelope, acceptance criteria, normative obligations) into the two IEEE 29148 Ground
Truth blueprints — `G0_StRS.md` (§9.4) and `G0_SyRS.md` (§9.5) — **without judging
sufficiency or scope**. S0 normalises only (paper §3, SDAD Phase 1 "spec
crystallisation"). Any judgement happens later at G0 (structural) and Gate H (human).

## Mapeo V-SIL-v3

| Paper | Element |
|-------|---------|
| §2 Stage-Gate Overview | `BP → S0` edge; re-entry `RFD → BP → S0` |
| §3 S0 — Normalisation and Ground Truth | the whole stage |
| §4 G0 | consumer of this skill's output; G0 FAIL routes back here ("validate vs original Build Package") |
| P2 (oracle ≠ generator) | S0-1 never validates its own output — it hands off to S0-2 |

## Inputs

| Input | Source | Required |
|-------|--------|----------|
| Build Package (free text, bullet list, PRD, email, spec excerpt) | user, pasted | yes |
| Project identity: acronym, organisation, classification, author | user (asked if missing) | yes |
| COTS hardware list with datasheet values | Build Package or user | yes (an HWC- block needs a source) |
| Normative sources (standards + clauses) | Build Package or user | yes for NRM-/SYS- |
| Previous G0 FAIL report (re-entry) | S0-2 output | optional |
| Approved RFD outcome (re-entry after deviation) | SX-1 output + updated BP | optional |

## Outputs

1. **Build Package inventory** — a table classifying every BP statement as
   `STK` / `HWC` / `NRM` / `SYS-candidate` / `OUT-OF-SCOPE-NOTE` with its source line.
2. **Missing-information list** — every blueprint field the BP does not supply (asked,
   never invented). Values the user declines to give stay as explicit `PENDING`/`PRELIMINARY` markers.
3. **`G0_StRS.md`** — full document following the StRS blueprint (headings §1.1–§6,
   metadata table, NRM-/HWC-/STK- blocks with all G0 fields).
4. **`G0_SyRS.md`** — full document following the SyRS blueprint (§1–§7, measurand
   catalog, method rationale, normative mapping, SYS- blocks with `Traces to`).
5. **Normalisation trace** — BP statement → block ID mapping (so G0 FAIL can be checked
   "vs original Build Package").
6. Handoff line: `S0 COMPLETE — submit both documents to S0-2 (G0).`

## Prompt template (resumido)

```
Step 0  Intake        "Paste the Build Package. Also give: project acronym (2–8 caps),
                       organisation, classification (PUBLIC/INTERNAL/CONFIDENTIAL)."
Step 1  Inventory     Table: # | BP statement (verbatim) | Class | Target block
                       → pause: "Correct any classification, or say continue."
Step 2  Gaps          Numbered questions, one per missing mandatory field
                       (datasheet value? clause? acceptance criterion?) → wait.
Step 3  StRS draft    Emit G0_StRS.md (metadata, §1.6 inventory, §2.6/2.7, NRM, STK, HWC, §6)
                       → pause.
Step 4  SyRS draft    Emit G0_SyRS.md (measurands, methods, §2.3 mapping, SYS blocks,
                       §4 correction chains, §5 budgets, §6 protocols, §7 trace) → pause.
Step 5  Trace + handoff  BP→block table; "S0 COMPLETE — run S0-2".
```

Behaviour rules for the prompt:
- Verbatim preservation: BP numbers/units/standards are copied, never "improved".
- No invention: a missing value is asked; if the user cannot supply it, emit the
  explicit marker (`PRELIMINARY`, `PENDING`) and list it — never a plausible guess.
- No scope judgement: S0 never says "this requirement is unrealistic" — that is Gate H / RFD.
- Output in chunks (one document per message) to avoid truncation (v2 convention).

## Criterios de aceptación

1. Every BP statement appears in the inventory with exactly one class.
2. Every StRS heading required by G0 (Step 2 of S0-2) is present; every SyRS heading too.
3. Every block carries every field G0 checks (STK: Type/Priority/Status/Verification/
   Standard(s)/Clause/Compliance/Description SHALL/Acceptance Criteria; NRM: concrete
   Standard + Clause; HWC: Component/Parameter/Limit type/Value(s)/Source/Source ref/
   Impact/Status; SYS: Type/Parameter/Method/Traces to/concrete Standard/Acceptance).
4. Every STK- is named by ≥ 1 SYS- `Traces to`; every `Traces to` token resolves.
5. No field value is invented: each value is traceable to a BP line or to a user answer
   in the conversation (normalisation trace proves it).
6. The skill never emits a PASS/FAIL verdict on its own documents.

## Dependencias

- Upstream: none (entry point) — or SX-1 (RFD accepted → updated BP) / S0-2 (G0 FAIL).
- Downstream: S0-2.
- Reference artefacts embedded in the skill: block field tables and enums from
  `templates/GT/G0_StRS.md` and `templates/GT/G0_SyRS.md` (template v4.0.0).

## Design notes

- v2 had no S0 skill (G0 assumed hand-authored GT). v3 adds S0 explicitly (paper §3).
- Companion Documents rows point to the S1 design document instead of the v2 SRS.
- Test vector: `test-inputs/build_package.md` → expected output equivalent to
  `test-inputs/G0_StRS.md` + `test-inputs/G0_SyRS.md`.

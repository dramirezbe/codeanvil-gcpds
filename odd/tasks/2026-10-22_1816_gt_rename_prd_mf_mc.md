# GT Rename: SRS+HCS → PRD, add MF (optional) + MC (required)

**Objective**: Refactor the Ground Truth input model across the entire repo. Replace the current two-document pair (SRS + HCS) with a new trio: PRD (always required), MC (always required), MF (optional). PRD merges what was SRS and HCS into a single Product Requirements Document. MC (Compliance Matrix) is a new always-required document covering normativity (ITU, ICNIRP, IEEE, ISO, etc.). MF (Mathematical Formulation) is optional.

**Branch**: `feat/gt-rename-prd`
**Delivery**: `ask-on-risk`
**Test runner**: `uv run --extra dev pytest tests/ -v`

## Specs

S1. **GT composition changes**. The Ground Truth is now:
  - **PRD** (Product Requirements Document) — ALWAYS required. Merges SRS (functional/non-functional requirements, IEEE 29148) and HCS (hardware constraints, §2.4) into one document. Contains both requirement blocks (`[A-Z]{3,5}-[A-Z]{2,4}-NNN`) and constraint blocks (`HWC-[A-Z]{2,4}-NNN`).
  - **MC** (Compliance Matrix) — ALWAYS required. Maps applicable standards (ITU, ICNIRP, IEEE, ISO, IEC, etc.) to requirements/constraints. New document type, new template, new G0 validation rules.
  - **MF** (Mathematical Formulation) — OPTIONAL. Formal mathematical models, signal processing chains, transfer functions, etc. New document type, new template, new G0 validation rules (when present).

S2. **PRD template** (`templates/GT/G0_PRD.md`). Merges current SRS and HCS templates into one document. Required headings = union of SRS headings + HCS headings (§1.5 Hardware Inventory, §2.1 Block Diagram, §2.2 Bus and Interface Topology, §3 Hardware Constraints, §4 Derived Constraints folded in alongside §3 Specific Requirements, §4 External Interface Requirements, §5 Non-Functional Requirements, §6 Traceability). Single metadata table. Both block types coexist.

S3. **MC template** (`templates/GT/G0_MC.md`). New template. Structure TBD — at minimum: Document Metadata, applicable standards list, compliance matrix table (Standard × Requirement/Constraint ID × Compliance Status × Evidence).

S4. **MF template** (`templates/GT/G0_MF.md`). New template. Structure TBD — at minimum: Document Metadata, model descriptions, variable definitions, equations/formulations, assumptions, validation criteria.

S5. **G0 validation — tool-backed script** (`g0_validate.py`). Update to:
  - Detect document type as PRD, MC, or MF (not SRS/HCS).
  - PRD validation = current SRS rules + current HCS rules applied to one document. Both block types validated. Cross-checks unified (traceability, orphan components, dependencies all within one document now).
  - MC validation = new rules (TBD with template).
  - MF validation = new rules (TBD with template), only when MF is present.
  - Gate logic: PRD + MC must both pass. MF must pass if present. Missing PRD or MC → FAIL.

S6. **G0 validation — no-tools skill** (`templates/no-tools-skills/G0_SKILL.md`). Same logic as S5 but in prose. Replace all SRS/HCS references with PRD/MC/MF. Precondition: "both PRD and MC required; MF optional." Detection, rules, report format all updated.

S7. **G1 skill** (`templates/no-tools-skills/G1_SKILL.md`). Update all GT references: receives PRD + MC (+ optional MF), not SRS + HCS. ASR extraction reads from PRD (both requirement and constraint blocks). HCS Impact→Priority mapping stays (constraint blocks in PRD still have Impact). MC informs compliance-driven ASRs.

S8. **Definitions table** in all skills. Update:
  - **GT** → "the set of documents (PRD + MC, optionally MF) that define the project contract"
  - **PRD** → "Product Requirements Document — functional requirements, non-functional requirements, and hardware constraints in one document"
  - **MC** → "Compliance Matrix — maps applicable standards to requirements and constraints"
  - **MF** → "Mathematical Formulation — formal mathematical models (optional)"
  - Remove **SRS** and **HCS** as standalone definitions.

S9. **config.yaml**. Update `gt_reference_templates`, `path_replacements`, and any SRS/HCS filename references to PRD/MC/MF.

S10. **Scaffold logic** (`src/codeanvil/init/create.py`). Update `_copy_gt_reference_templates()` to copy PRD, MC, MF templates. Update `_create_gt_dir()` README to reference new document names.

S11. **AGENTS.md template** (`templates/AGENTS/TEMPLATE_AGENT.md`). Replace SRS/HCS references with PRD/MC/MF.

S12. **Custody-chain skill** (`templates/skills/custody-chain/SKILL.md`). Update GT file references from SRS/HCS to PRD/MC/MF.

S13. **Test cases** (`methodology/test/`). Update T0_ANE-Lap2 GT files: merge SRS + HCS into a single PRD. Create MC for that test case. Update test README.

S14. **Tool-backed G0 tests** (`templates/tests/test_g0_validate.py`). Update all test fixtures from SRS/HCS to PRD/MC/MF. New tests for MC validation and optional MF handling.

S15. **Documentation**. Update CLAUDE.md, README.md, and any odd/tasks references to reflect the new GT model.

S16. **Legacy templates**. Move current `G0_SRS.md` and `G0_HCS.md` to `templates/GT/legacy/` (they already have legacy copies there). Keep for reference but not used by scaffold.

## Tasks

| ID | Spec | Route | Status | Commit |
|----|------|-------|--------|--------|
| T1 | S2 | inline | todo | |
| T2 | S3, S4 | inline | todo | |
| T3 | S5, S14 | inline | todo | |
| T4 | S6, S8 | inline | todo | |
| T5 | S7, S8 | inline | todo | |
| T6 | S9, S10, S11, S12, S16 | inline | todo | |
| T7 | S13 | inline | todo | |
| T8 | S15 | inline | todo | |
| T9 | S1 (all) | inline | todo | |

**T1 — PRD template**: Merge SRS + HCS templates into `templates/GT/G0_PRD.md`. Union of required headings. Single metadata table. Both requirement and constraint block types documented.

**T2 — MC + MF templates**: Create `templates/GT/G0_MC.md` (Compliance Matrix) and `templates/GT/G0_MF.md` (Mathematical Formulation). Define required headings, metadata, block structures.

**T3 — G0 script + tests**: Refactor `g0_validate.py` to detect PRD/MC/MF, validate PRD with merged SRS+HCS rules, add MC/MF validation. Update all test fixtures.

**T4 — No-tools G0 skill**: Rewrite `G0_SKILL.md` for PRD/MC/MF. Update definitions, preconditions, detection, validation rules, report format.

**T5 — No-tools G1 skill**: Update `G1_SKILL.md` GT references, definitions, ASR extraction from PRD, MC-informed compliance ASRs.

**T6 — Scaffold + config**: Update config.yaml, create.py, AGENTS.md template, custody-chain skill. Move old templates to legacy.

**T7 — Test cases**: Merge T0_ANE-Lap2 SRS+HCS into PRD, create MC, update test README.

**T8 — Docs**: Update CLAUDE.md, README.md.

**T9 — Integration verification**: End-to-end: scaffold a project, copy T0 PRD+MC, run G0 (script + no-tools), verify pass. Run full test suite.

## Log

L1. User request (2026-10-22): "Refactor input of methodology names in all repo and structure: Now the files must be PRD (Product Requirements Document [SRS + HCS in one document]) and optional MF (Mathematical Formulation), also needed always MC (Compliance Matrix [normativity, compliance, ITU, ICNIRP, IEEE, ISO, etc])."

L2. Blast radius (2026-10-22): 36 files reference SRS/HCS across the repo. Key surfaces: g0_validate.py (constants, detection, block validation), config.yaml (template list, path rewrites), create.py (scaffold), both no-tools skills, AGENTS.md template, custody-chain skill, test fixtures, GT templates, documentation.

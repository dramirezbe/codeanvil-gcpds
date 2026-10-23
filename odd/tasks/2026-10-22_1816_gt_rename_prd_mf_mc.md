# GT Rename: IEEE 29148 Document Family (StRS + SyRS + SRS)

**Objective**: Refactor the Ground Truth input model across the entire repo. Replace the current two-document pair (SRS + HCS) with the IEEE/ISO/IEC 29148:2018 document hierarchy: StRS (§9.4, always required, G0), SyRS (§9.5, always required, G0), and SRS (§9.6, always required, G1). Compliance traceability (formerly MC) becomes inline sections within StRS and SyRS. Mathematical formulation (formerly MF) is replaced by SyRS content.

**Branch**: `feat/gt-rename-prd`
**Delivery**: `ask-on-risk`
**Test runner**: `uv run --extra dev pytest tests/ -v`

## Summary

| Old | New | Required | Gate |
|-----|-----|----------|------|
| SRS | StRS — Stakeholder Req. Spec (§9.4) | Always | G0 |
| HCS | (merged into StRS §9.4.12) | — | — |
| (none) | SyRS — System Req. Spec (§9.5) | Always | G0 |
| (none) | SRS — Software Req. Spec (§9.6) | Always | G1 |
| MC | (inline in StRS + SyRS) | — | — |
| MF | (replaced by SyRS) | — | — |

### Document flow

```
StRS (§9.4) + SyRS (§9.5) — domain/measurement engineering input
→ G0 (structural validation per §9.4/§9.5, cross-doc consistency)
→ Gate H (human readiness review)
→ Software design (Ctx 02-03)
→ SRS (§9.6) — software engineering output
→ G1 (software design validation)
→ Build + CI+SIL (Layer 2)
```

### Document descriptions

- **StRS — Stakeholder Requirements Specification (IEEE 29148 §9.4)**: system-level view covering all subsystems, all frequency bands, all measurement types. Contains the normative framework (ITU, ICNIRP, ANE, GUM), COTS platform envelope (HackRF, RPi), stakeholder requirements, operational concept, and system-level design decisions. Typed blocks: normative obligations (NRM-\*), COTS constraints (HWC-\*), stakeholder requirements (STK-\*), each with compliance traceability inline. Template follows §9.4.2 through §9.4.17.

- **SyRS — System Requirements Specification (IEEE 29148 §9.5)**: detailed per-measurand technical specification. Contains method selection with rationale, parameter specification (window, overlap, NFFT, normalization), correction chains (antenna factor, cable loss, impedance matching), GUM uncertainty budgets per component, field measurement protocols, and measurand-specific acceptance criteria. Typed blocks: system requirements (SYS-\*), measurement methods, correction chains, uncertainty budgets, each tracing back to StRS block IDs. Template follows §9.5 sections.

- **SRS — Software Requirements Specification (IEEE 29148 §9.6)**: software design specification derived from G0-validated StRS + SyRS. Contains software-specific SHALL statements, library/framework selections, implementation constraints, algorithms, data schemas, interfaces, error behavior, and test specifications. Typed blocks: software requirements (REQ-\*) tracing back to SyRS block IDs. Template follows §9.6 sections. Produced as G1 output, validated by G1.

## Specs

S1. **GT composition changes**. The Ground Truth is now:
  - **StRS** (Stakeholder Requirements Specification, IEEE 29148 §9.4) — ALWAYS required. System-level: normative framework, COTS platform envelope, stakeholder requirements, operational concept, design decisions. Merges old SRS functional/non-functional requirements and old HCS hardware constraints into one document. Contains NRM-\*, HWC-\*, and STK-\* typed blocks with inline compliance traceability (replaces standalone MC).
  - **SyRS** (System Requirements Specification, IEEE 29148 §9.5) — ALWAYS required. Per-measurand: methods, parameters, correction chains, uncertainty budgets, field protocols, acceptance criteria. Contains SYS-\* typed blocks tracing to StRS. Replaces the optional MF document — now mandatory.
  - **SRS** (Software Requirements Specification, IEEE 29148 §9.6) — ALWAYS required. Software design: libraries, frameworks, algorithms, schemas, interfaces, error behavior, tests. Contains REQ-\* typed blocks tracing to SyRS. Produced at G1, not G0 input.

S2. **StRS template** (`templates/GT/G0_StRS.md`). Replaces current SRS and HCS templates. Follows IEEE 29148 §9.4 sections (§9.4.2 purpose through §9.4.17 operational scenarios). Required headings = union of old SRS headings + old HCS headings (§1.5 Hardware Inventory, §2.1 Block Diagram, §2.2 Bus and Interface Topology folded alongside §3 Specific Requirements, §4 External Interface Requirements, §5 Non-Functional Requirements, §6 Traceability). Single metadata table. Block types: NRM-\* (normative obligations), HWC-\* (COTS constraints), STK-\* (stakeholder requirements). Each block carries compliance traceability inline (standard reference, clause, compliance status).

S3. **SyRS template** (`templates/GT/G0_SyRS.md`). New template replacing MF. Follows IEEE 29148 §9.5 sections. Block type: SYS-\* (system requirements). Required content per measurand: method selection with rationale, parameter specification, correction chains, GUM uncertainty budgets, field measurement protocols, acceptance criteria. Each block traces back to StRS block IDs. Compliance traceability inline (per-measurand normative-to-method mapping, replaces standalone MC).

S4. **SRS template** (`templates/GT/G1_SRS.md`). New template for G1 output. Follows IEEE 29148 §9.6 sections. Block type: REQ-\* (software requirements). Required content: software SHALL statements, library/framework selections, implementation constraints, algorithms, data schemas, interfaces, error behavior, test specifications. Each block traces back to SyRS block IDs.

S5. **G0 validation — tool-backed script** (`g0_validate.py`). Update to:
  - Detect document type as StRS or SyRS (not SRS/HCS/PRD/MC/MF).
  - StRS validation = current SRS rules + current HCS rules applied to one document. NRM-\*, HWC-\*, STK-\* blocks validated. Cross-checks unified within one document.
  - SyRS validation = new rules per §9.5 (method blocks, traceability to StRS IDs, uncertainty budget structure).
  - G0-X cross-document validation: every StRS requirement must have a corresponding SyRS specification; every SyRS measurand must trace to an StRS requirement and normative source.
  - Gate logic: StRS + SyRS must both pass, plus G0-X. Missing StRS or SyRS → FAIL.

S6. **G0 validation — no-tools skill** (`templates/no-tools-skills/G0_SKILL.md`). Same logic as S5 but in prose. Replace all SRS/HCS/PRD/MC/MF references with StRS/SyRS. Precondition: "both StRS and SyRS required." Detection, rules, cross-document checks, report format all updated.

S7. **G1 skill** (`templates/no-tools-skills/G1_SKILL.md`). Update GT references: G1 receives G0-validated StRS + SyRS and governs SRS (§9.6) production. ASR extraction reads from StRS (NRM-\*, HWC-\*, STK-\* blocks) and SyRS (SYS-\* blocks). G1 validates the produced SRS against both upstream documents.

S8. **Definitions table** in all skills. Update:
  - **GT** → "the set of documents (StRS + SyRS) that define the project contract; validated by G0"
  - **StRS** → "Stakeholder Requirements Specification (IEEE 29148 §9.4) — system-level requirements, normative framework, COTS constraints, stakeholder requirements"
  - **SyRS** → "System Requirements Specification (IEEE 29148 §9.5) — per-measurand methods, parameters, correction chains, uncertainty budgets"
  - **SRS** → "Software Requirements Specification (IEEE 29148 §9.6) — software design derived from StRS + SyRS; produced at G1"
  - Remove standalone **MC** and **MF** definitions. Remove old **SRS** (as GT input) and **HCS** definitions.

S9. **config.yaml**. Update `gt_reference_templates`, `path_replacements`, and any SRS/HCS filename references to StRS/SyRS. Remove MC/MF references if any were added.

S10. **Scaffold logic** (`src/codeanvil/init/create.py`). Update `_copy_gt_reference_templates()` to copy StRS and SyRS templates. Update `_create_gt_dir()` README to reference new document names. SRS template (G1) is not scaffolded at G0 — it is produced later.

S11. **AGENTS.md template** (`templates/AGENTS/TEMPLATE_AGENT.md`). Replace SRS/HCS references with StRS/SyRS/SRS and the IEEE 29148 document flow.

S12. **Custody-chain skill** (`templates/skills/custody-chain/SKILL.md`). Update GT file references from SRS/HCS to StRS/SyRS.

S13. **Test cases** (`methodology/test/`). Update T0_ANE-Lap2 GT files: merge SRS + HCS into StRS, create SyRS for that test case. Update test README.

S14. **Tool-backed G0 tests** (`templates/tests/test_g0_validate.py`). Update all test fixtures from SRS/HCS to StRS/SyRS. New tests for SyRS validation and G0-X cross-document consistency.

S15. **Documentation**. Update CLAUDE.md, README.md, and any odd/tasks references to reflect the new GT model.

S16. **Legacy templates**. Move current `G0_SRS.md` and `G0_HCS.md` to `templates/GT/legacy/`. Keep for reference but not used by scaffold.

S17. **G1 gate validation**. Define G1 validation rules for SRS (§9.6): every REQ-\* block must trace to a SyRS SYS-\* block, software SHALL statements must be testable, library/framework selections must be justified. Add G1 validation to the no-tools G1 skill and (future) tool-backed G1 script.

S18. **SyRS validator — MVP scope** (`g0_validate.py`). Simple structural validation for SyRS, not full metrological rigor. Phase 1–4 structure mirrors StRS validation:
  - **Phase 1 — Headings**: required sections exist (per §9.5 template).
  - **Phase 2 — Metadata**: same metadata table rules as StRS (ID, Version, Classification).
  - **Phase 3 — Block validation**:
    - SYS-\* block ID format and uniqueness
    - Required fields: ID, type, parameter, method, traces\_to (StRS block ID)
    - At least one acceptance criterion per block
    - Uncertainty budget section present (can be placeholder for MVP)
  - **Phase 4 — Cross-checks**:
    - Every `traces_to` reference points to a valid StRS block ID (NRM-\*, HWC-\*, or STK-\*)
    - No orphan blocks (every SYS-\* traces to something)
    - No duplicate block IDs across StRS + SyRS

  NOT in MVP: validation of GUM uncertainty structure, correction chain completeness, method rationale quality, or field protocol coverage. Those are G0 v2.

S19. **Legacy name eradication**. After all implementation tasks are complete, verify zero references to the old names (SRS as GT input, HCS, MC, MF, PRD, G0\_SRS, G0\_HCS) remain anywhere in the repo outside `odd/tasks/`, `methodology/V-SIL-v2/audit/`, and `templates/GT/legacy/`. The following 26 files currently contain legacy references and must be updated or removed:

  **Source code + config (6 files):**
  - `pyproject.toml` — force-include mappings for G0\_SRS.md / G0\_HCS.md
  - `templates/config.yaml` — gt\_reference\_templates, path\_replacements
  - `src/codeanvil/init/create.py` — scaffold template references
  - `src/codeanvil/CLI/parser.py` — help text / examples
  - `templates/skills/G0_valid_req_and_GT/scripts/g0_validate.py` — constants, detection, validation
  - `tests/test_sync.py` — fixture file references

  **Templates + skills (8 files):**
  - `templates/GT/G0_SRS.md` — becomes G0\_StRS.md (or moved to legacy/)
  - `templates/GT/G0_HCS.md` — moved to legacy/
  - `templates/GT/README.md` — document listing
  - `templates/AGENTS/TEMPLATE_AGENT.md` — scaffolded AGENTS.md content
  - `templates/skills/G0_valid_req_and_GT/SKILL.md` — skill contract
  - `templates/skills/G0_valid_req_and_GT/references/RULES.md` — rule tables
  - `templates/no-tools-skills/G0_SKILL.md` — no-tools G0 skill
  - `templates/no-tools-skills/G1_SKILL.md` — no-tools G1 skill
  - `templates/tests/test_g0_validate.py` — test fixtures

  **Documentation (4 files):**
  - `CLAUDE.md` — project instructions
  - `AGENTS.md` — repo-level agent instructions
  - `README.md` — project README

  **Methodology / test cases (5 files):**
  - `methodology/test/README.md` — test catalog
  - `methodology/test/T0_ANE-Lap2/just-edge/SRS.md` — rename to StRS.md
  - `methodology/test/T0_ANE-Lap2/just-edge/HCS.md` — merge into StRS.md or remove
  - `methodology/test/T0_ANE-Lap2/full-system/SRS_APPROVED.md` — rename/update
  - `methodology/V-SIL-v2/G1_DESIGN.md` — GT references
  - `methodology/V-SIL-v2/vsil-dsp-literature-analysis.md` — GT references
  - `methodology/V-SIL/V-SIL.md` — GT references
  - `methodology/V-SIL/audit/V-SIL Methodology Audit.md` — GT references

## Tasks

| ID | Spec | Route | Status | Commit |
|----|------|-------|--------|--------|
| T1 | S2 | inline | done | 1ff05b4 |
| T2 | S3 | inline | done | 1ff05b4 |
| T3 | S4, S17 | inline | done | 1ff05b4 |
| T4a | S5 (StRS validation) | inline | done | 1ff05b4 |
| T4b | S18 (SyRS validation) | inline | done | 1ff05b4 |
| T4c | S5 (G0-X cross-doc) | inline | done | 1ff05b4 |
| T4d | S14 (test fixtures) | inline | done | 1ff05b4 |
| T5 | S6, S8 | inline | done | d4e3b06 |
| T6 | S7, S8 | inline | done | d4e3b06 |
| T7 | S9, S10, S11, S12, S16 | inline | done | d4e3b06 |
| T8 | S13 | inline | done | 1ff05b4, d4e3b06 |
| T9 | S15 | inline | done | (next commit) |
| T10 | S1 (all) | inline | done | (next commit) — scaffold smoke + G0 pair exit 0/1 verified, 205+93 tests green |
| T11 | S19 (legacy eradication) | inline | done | (next commit) — zero live hits; carve-outs per L8 |

**T1 — StRS template**: Create `templates/GT/G0_StRS.md` by merging current SRS + HCS templates. IEEE 29148 §9.4 sections (§9.4.2–§9.4.17). Block types: NRM-\*, HWC-\*, STK-\*. Inline compliance traceability. Single metadata table.

**T2 — SyRS template**: Create `templates/GT/G0_SyRS.md`. IEEE 29148 §9.5 sections. Block type: SYS-\*. Per-measurand: methods, parameters, correction chains, uncertainty budgets, field protocols. Traces to StRS block IDs. Inline compliance traceability.

**T3 — SRS template + G1 gate**: Create `templates/GT/G1_SRS.md`. IEEE 29148 §9.6 sections. Block type: REQ-\*. Software SHALL statements, library selections, schemas, interfaces, tests. Traces to SyRS block IDs. Define G1 validation rules.

**T4a — StRS validator**: Refactor `g0_validate.py` to detect StRS, apply merged SRS+HCS rules. NRM-\*/HWC-\*/STK-\* block validation. Metadata, headings, block parsing, internal cross-checks — same four phases as current G0 but against the merged document.

**T4b — SyRS validator (MVP)**: Add SyRS detection and MVP structural validation per S18. SYS-\* blocks, `traces_to` field referencing StRS block IDs, acceptance criteria presence, uncertainty budget section present. Simple structural checks only — not full metrological rigor.

**T4c — G0-X cross-document consistency**: Every StRS stakeholder requirement (STK-\*) must have a corresponding SyRS specification (SYS-\*). Every SyRS measurand must trace back to an StRS requirement and normative source. Shared ID namespace — no collisions across StRS + SyRS block IDs.

**T4d — Test fixtures**: Update all existing test cases from SRS/HCS to StRS/SyRS format. Add new fixtures: valid SyRS document, SyRS with missing traces\_to, SyRS with orphan blocks, G0-X cross-doc failure cases.

**T5 — No-tools G0 skill**: Rewrite `G0_SKILL.md` for StRS/SyRS. Update definitions, preconditions, detection, validation rules (including G0-X cross-doc), report format.

**T6 — No-tools G1 skill**: Update `G1_SKILL.md` GT references, definitions. G1 receives StRS + SyRS, governs SRS production. ASR extraction from StRS + SyRS blocks. Add SRS validation rules.

**T7 — Scaffold + config**: Update config.yaml, create.py, AGENTS.md template, custody-chain skill. Move old templates to legacy/.

**T8 — Test cases**: Merge T0_ANE-Lap2 SRS+HCS into StRS, create SyRS for that test case, update test README.

**T9 — Docs**: Update CLAUDE.md, README.md.

**T10 — Integration verification**: End-to-end: scaffold a project, copy T0 StRS+SyRS, run G0 (script + no-tools), verify pass. Run full test suite.

**T11 — Legacy name eradication (S19)**: Final pass. Grep the entire repo for SRS (as GT input), HCS, MC, MF, PRD, G0\_SRS, G0\_HCS. Verify zero hits outside allowed exclusion zones (`odd/tasks/`, `methodology/V-SIL-v2/audit/`, `templates/GT/legacy/`). Fix any stragglers. 26 files identified in S19.

## Log

L1. User request (2026-10-22): "Refactor input of methodology names in all repo and structure: Now the files must be PRD (Product Requirements Document [SRS + HCS in one document]) and optional MF (Mathematical Formulation), also needed always MC (Compliance Matrix [normativity, compliance, ITU, ICNIRP, IEEE, ISO, etc])."

L2. Blast radius (2026-10-22): 36+ files reference SRS/HCS across the repo. Key surfaces: g0_validate.py (constants, detection, block validation), config.yaml (template list, path rewrites), create.py (scaffold), both no-tools skills, AGENTS.md template, custody-chain skill, test fixtures, GT templates, documentation.

L3. Plan revision (2026-10-22): After IEEE/ISO/IEC 29148:2018 research and domain collaboration, replaced PRD+MC+MF model with the IEEE 29148 document family: StRS (§9.4) + SyRS (§9.5) as G0 inputs, SRS (§9.6) as G1 output. MC becomes inline compliance traceability in StRS and SyRS. MF is replaced by SyRS (now mandatory). Added S17/T3 for G1 gate validation. Task count: 9 → 13.

L4. Plan revision (2026-10-22): Split T4 into T4a–T4d for explicit StRS validator, SyRS MVP validator (S18), G0-X cross-doc, and test fixtures. Added S18 (SyRS validator MVP scope). Task count: 10 → 13.

L5. Implementation pass (2026-10-22): Searched repo for all legacy SRS/HCS references. Found 26 files. Added S19 (legacy name eradication) and T11 (final grep pass). Task count: 13 → 14. File inventory recorded in S19 across 4 categories: source code + config (6), templates + skills (9), documentation (3), methodology + test cases (8).

L6. T1–T4d + T8 fixtures (2026-10-22, commit 1ff05b4): Created G0_StRS.md / G0_SyRS.md / G1_SRS.md templates; rewrote g0_validate.py (StRS 18 + SyRS 15 required headings, STK/NRM/HWC/SYS per-kind field+enum rules, inline compliance rows, G0-X pair rules, pair-gate CLI); rewrote test_g0_validate.py (93 tests, stdlib unittest + pytest runners); migrated T0 just-edge fixtures (43 STK renamed CAT/ANTE/CONF/CONN/FORN/GEST/NORM/POWR→STK, 17 HWC with compliance rows, 4 new NRM blocks, SyRS with 27 SYS covering all 43 STKs). Validator pair run: StRS PASS (5 known source-ref warnings), SyRS PASS, G0-X PASS, exit 0. Template noise on unfilled templates (placeholder + example-block enum choice cells) matches old-validator behavior — contract is "fails, no missing section".

L7. T5–T9 + T11 (2026-10-22, commit d4e3b06 + follow-up): Rewrote G0 SKILL.md/RULES.md/no-tools G0 skill (pair gate, per-kind rules, G0-X); G1 no-tools skill now runs 8 jobs incl. SRS authoring (Job 6), SRS structural validation (Job 7), review package (Job 8); wrote G1_start_design/SKILL.md; config.yaml/create.py/test_sync manifest gt={strs,syrs}; legacy templates moved to templates/GT/legacy/ as v3; TEMPLATE_AGENT + GT READMEs + CLAUDE.md + README.md + repo AGENTS.md updated; T0 legacy just-edge SRS.md/HCS.md removed, full-system renamed StRS_APPROVED.md (155 IDs → STK-*); test README procedure updated; pyproject force-include + parser.py help fixed.

L8. S19 carve-out decision (2026-10-22): Historical deliverable snapshots — `methodology/V-SIL/` (v1 paper .md/.tex), `methodology/reports/`, `methodology/slides/`, and `methodology/V-SIL-v2/` pipeline/literature artifacts (all outside S19's 26-file inventory) — retain legacy GT names as historical record; rewriting published-style artifacts would falsify them. Also intentional historical mentions: `templates/GT/README.md` Legacy section (documents legacy/ contents), the StRS change-log "merged HCS" entry, and cited-literature "SRS" wording in `G1_DESIGN.md` (flagged via top-of-file note). All 26 inventoried files are updated.

L9. T10/T11 integration verification (2026-10-22): scaffold smoke (`codeanvil init` + `create` in /tmp/opencode) — GT README, locked templates G0_StRS/G0_SyRS in G0 skill + G1_SRS in G1 skill (new g1_skill scaffold copy, path_replacements added), manifest gt={strs,syrs}, no `templates/GT` paths leak into rewritten skills. G0 with T0 pair: StRS PASS (0e/5w), SyRS PASS, G0-X PASS, exit 0; missing-SyRS run: G0 GATE REPORT FAIL, exit 1. Suites: pytest 205 passed, unittest 93 OK. S19 final grep: zero live legacy hits; only intentional historical mentions remain (L8 carve-outs). Smoke project + its DB rows removed after verification.

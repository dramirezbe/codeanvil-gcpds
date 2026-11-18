# V-SIL v4 refactor: S0→G3 chain implementation

**Objective:** Implement the full V-SIL v4 lifecycle from the v3 chain shipped in v0.8.7, transforming S0→G2 to S0→G3 with 8-node chain, module-slice cadence, fresh-context implementor, and living GT with custody integrity.

**Branch:** `feat/vsil-v4` from `main`

**Delivery:** 8 chained PRs, each main-mergeable with full test suite green (§6 of detailed plan)

**Test runner:** `uv run --extra dev pytest` (skill-text assertions through `_skill_text()`)

---

## Specs

**S1** — "Coge esta nueva versión de V-SIL-v4.md y planea un refactor para implementar por completo V-SIL-v4, partiendo de V-SIL-v3 actual de este repo. Guardala en odd/tasks/vsilv4-refactor/ SOlo haz el planing específico"

**S2** — "Agrega que el alcance no es la UI, Ui queda incompatible con V-SIL-v4, lo delegamos para después de tener un full flow con v4."

---

## Decisions (confirmed 2026-11-17)

| ID | Decision | Chosen | Notes |
|---|---|---|---|---|
| D2 | Mini-V cadence | Per slice | Each slice k: S2(k)→G2(k)→S3(k)→G3(k), then slice k+1 |
| D3 | Plans location | `.codeanvil/plans/` | Methodology-owned, like `.codeanvil/design/` |
| D8 | Living GT | Full | Accepted deltas applied by S0/S1 in `delta-sync`; staleness accepts authorized advances |
| D10 | v3 projects | Fail (no migrate) | No `codeanvil migrate` command; just fail if not v4; no LEGACY_V3 or deprecated logic |
| D11 | Release | 0.9.0 | Pre-1.0 minor bump, breaking chain |
| — | Branch | `feat/vsil-v4` | From `main` |

---

## Tasks

### Phase A — Tooling foundations · ~650 LOC

| ID | Spec | Route | Status | Commits |
|---|---|---|---|---|---|
| **A1** | Configure `config.yaml` for 8-node chain (S0→G2→S3→G3), `loop_after`, `subagents` | Inline | ✅ DONE | ef4866c |
| **A2** | `reports.py`: scope, inputs (digest staleness, authorized advances), `next_step()` | Inline | ✅ DONE | 70e7003 |
| **A3** | `codeanvil custody`: digest/verify/verify-manifest CLI, stateless integrity | Inline | ✅ DONE | 70e7003 |
| **A4** | `backup.py`: directory targets with per-file paths, manifest hashes via custody | Inline | ✅ DONE | 6cdd02b |
| **A5** | `status`: show Scope, Next:, findings from `custody.verify()` | Inline | ✅ DONE | 6cdd02b |
| **A6** | Retire `.codeanvil/custody/` folder creation (config/paths, init/create, sync) | Inline | ✅ DONE | ef4866c |

Acceptance: v3 projects' `status` output identical; `custody` works; no DB changes.

### Phase B — Rename S2/G2 to S3/G3 · ~300 LOC

| ID | Spec | Route | Status | Commits |
|---|---|---|---|---|
| **B1** | `git mv S2_implement_subsystems→S3_implement_modules`, `G2_adaptive_verification→G3_adaptive_verification` | Inline | ✅ DONE | 3460764 |
| **B2** | Rename in `vsil-verifier.md`, S1/G1/RFD/skills | Inline | ✅ IMPLEMENTED |
| **B3** | Add skip marker to `test_ui_workspace.py` (§0: UI deferred) | Inline | ✅ IMPLEMENTED |
| **B4** | Update help text, HIL MCP docs | Inline | ✅ IMPLEMENTED |
| **B5** | Rename tests, sweep for S2/G2 references | Inline | ✅ IMPLEMENTED |

Intermediate: 6-node chain `S0→G0→S1→G1→S3→G3` (S3 prereq temporarily G1).

### Phase C — S1/G1 module identity, slicing readiness · ~300 LOC

| ID | Spec | Route | Status | Commits |
|---|---|---|---|---|
| **C1** | SDD §1.4 card: 8 fields (`module_id`, `subsystem_id`, layer, `depends_on`, provides, hw_dep, `required_vl`, `traced_reqs`); remove Meta `G0 approved` row | Inline | ✅ DONE | f86572a |
| **C2** | S1 skill: 8-field guide, `traced_reqs` validation, `Input:` lines in report | Inline | ✅ DONE | f86572a |
| **C3** | G1 checklist: add G1.17 (decomposition), G1.18 (topological sort) | Inline | ✅ DONE | f86572a |
| **C4** | Update fixture SDD with new card (8-field examples: acq, estimator) | Inline | ✅ DONE | f86572a |
| **C5** | Replace all hand-computed hashes (`hashlib`, `sha256sum`, `shasum`, `Get-FileHash`) in skills with `codeanvil custody digest`; guard test in `test_custody_rule.py` | Inline | ✅ DONE | 2c0740e, 2eeee1d |

C-fix commit `64b9168`: test fixes (backup flattening, v3→v4 renames in tests, UI skip markers). Suite: 711 passed, 40 skipped.

### Phase D — New S2 module planning skill · ~500 LOC

| ID | Spec | Route | Status | Commits |
|---|---|---|---|---|
| **D1** | Create `S2_plan_modules/SKILL.md`: cadence (C1/C2+), slice boundaries (HAL-first, DSP-then-Decision), plans/contracts/deltas | Inline | ✅ DONE | f59287f |
| **D2** | References: `BACKLOG.md`, `PLAN.md`, `DELTAS.md` templates | Inline | ✅ DONE | f59287f |
| **D3** | `slice_backlog.py`: deterministic topological sort, cycle detection | Inline | ✅ DONE | f59287f |

**D-fix implemented (2026-11-17; 4b47fe2):** the following items were reviewed and found incomplete:

| ID | Required fix | Status |
|---|---|---|
| **D-fix.1** | PLAN.md must be **per module** at `.codeanvil/plans/<SUB-xxx>/<module_id>/PLAN.md` (D2, §3.2, P7). Currently per-slice (line 104 of SKILL.md: "One PLAN.md per slice"). Restructure SKILL.md and references/PLAN.md. | ✅ DONE |
| **D-fix.2** | Add `references/INFRA-PLAN.md` (Slice 0, paper §8.3.1 (a)–(d): bases, verification kit, stubs, top-down integration) | ✅ DONE |
| **D-fix.3** | Add `references/INTEGRATION-PLAN.md` (D12: system-scope cross-subsystem contract tests, PATH-*, entry point) | ✅ DONE |
| **D-fix.4** | `DELTAS.md` must be empty-on-first-run; G3/RFD delta logic belongs to Phase H | ✅ DONE |
| **D-fix.5** | Tests for `slice_backlog.py`: Kahn levels, cycle→exit 1, unknown dependency→exit 1, deterministic order | ✅ DONE |

### Phase E — New G2 plan micro-gate · ~350 LOC

| ID | Spec | Route | Status | Commits |
|---|---|---|---|---|
| **E1** | Create `G2_plan_review/SKILL.md` + `G2_CHECKLIST.md` | Inline | ✅ DONE | 9e61ef5 |
| **E2** | S0: add re-entry row for G2 `Verdict: GT defect` → Triage | Inline | ✅ DONE | 36a1311 |

**E-fix implemented (2026-11-17; 4b47fe2):** G2 checks must be rewritten per paper §9.1:

| ID | Required fix | Status |
|---|---|---|
| **E-fix.1** | G2 checks are still the 6 invented ones (Module present, Dependency order, VL-2 readiness, Test entry, Contract clarity, Slice boundary). Must rewrite to §9.1: (1) completeness, (2) traceability, (3) contract consistency, (4) task ordering, (5) verification feasibility, (6) fresh-context sufficiency. Rewrite both `SKILL.md` and `G2_CHECKLIST.md`. | ✅ DONE |
| **E-fix.2** | Verdicts must follow plan §3.4: PASS→S3; plan defect→S2; design defect→S1; GT defect→S0 | ✅ DONE |

Acceptance: 8-node chain with correct G2 checks per §9.1 and per-module PLAN.md granularity (P7).

### Phase F — S3 per-module fresh context · ~500 LOC

| ID | Spec | Route | Status | Commits |
|---|---|---|---|---|
| **F1** | Create `vsil-implementor.md` subagent: one PLAN.md, write-scoped to module only | Inline | ✅ IMPLEMENTED |
| **F2** | S3 skill: slice cadence, MCP analysis, Pause Schedule, proposed deltas | Inline | ✅ IMPLEMENTED |

### Phase G — G3 adaptive verification by slice · ~400 LOC

| ID | Spec | Route | Status | Commits |
|---|---|---|---|---|
| **G1** | G3 skill: slice scope, VL-0 floor regression, self-diagnosis, enrollment/pre-HW review | Inline | ✅ IMPLEMENTED |
| **G2** | Verified Prototype v4: GT version, module table with Slice/Plan/Evidence, DELTAS summary | Inline | ✅ IMPLEMENTED |
| **G3** | `vsil-verifier.md`: receives scope, runs G3.0, all digests from custody | Inline | ✅ IMPLEMENTED |

### Phase H — Living GT and design sync · ~350 LOC

| ID | Spec | Route | Status | Commits |
|---|---|---|---|---|
| **H1** | `DELTAS.md` schema: ID, Type, Target, Document, Before/After, Reason, Authority, Status, Applied in, Before/After sha256, Interface impact | Inline | ✅ IMPLEMENTED |
| **H2** | `authorized_advance()`: chains of applied deltas with no interface impact | Inline | ✅ IMPLEMENTED |
| **H3** | S0 `delta-sync`: apply GT deltas, bump Version, write to DELTAS.md | Inline | ✅ IMPLEMENTED |
| **H4** | S1 `delta-sync`: apply design-sync deltas, G1 rework confirms empty impact | Inline | ✅ IMPLEMENTED |

### Phase I — Generated and repo documentation · ~300 LOC

| ID | Spec | Route | Status | Commits |
|---|---|---|---|---|
| **I1** | `TEMPLATE_AGENT.md`: 8-node chain, cadence, routing §3.4, RFD sources (S1/G1/G3), custody rule | Inline | ✅ IMPLEMENTED |
| **I2** | Repo docs: `AGENTS.md`, `CLAUDE.md`, `README.md`, `methodology/test/README.md` | Inline | ✅ IMPLEMENTED |
| **I3** | UI disclosure (§0): v3-only until follow-up; non-chain features kept working | Inline | ✅ IMPLEMENTED |
| **I4** | Archive note: v3 items stay untouched | Inline | ✅ IMPLEMENTED |

### Phase K — End-to-end validation · no product LOC

| ID | Spec | Route | Status | Commits |
|---|---|---|---|---|
| **K1** | Run T0_FM-RPI-RTL-mock under v4 to Verified Prototype; 8 probes (plan defect, GT defect, design defect, self-diagnosis, deltas, stale cascade, fresh sessions, UI smoke) | Inline | ⏳ HUMAN ACCEPTANCE |

### Phase L — Release

| ID | Spec | Route | Status | Commits |
|---|---|---|---|---|
| **L1** | `pyproject.toml` → 0.9.0, changelog, tag, `CLAUDE.md` | Inline | ✅ PREPARED; publication pending review |

---

## Log

**L1** (2026-11-17 user request, verbatim):
- S1: "Coge esta nueva versión de V-SIL-v4.md y planea un refactor para implementar por completo V-SIL-v4, partiendo de V-SIL-v3 actual de este repo. Guardala en odd/tasks/vsilv4-refactor/ SOlo haz el planing específico"
- S2: "Agrega que el alcance no es la UI, Ui queda incompatible con V-SIL-v4, lo delegamos para después de tener un full flow con v4."

**L2** (2026-11-17 decisions confirmed):
- D2 per slice ✓
- D3 `.codeanvil/plans/` ✓
- D8 full living GT ✓
- D10 no migrate; just fail if not v4 ✓ (removed Phase J)
- D11 release 0.9.0 ✓
- Branch `feat/vsil-v4` ✓
- Modified plan: removed Phase J (migration), removed migrate from Phase I, reordered delivery chain (now 7 PRs: A–I, K–L)

**L3** (2026-11-17 review):
- Phase C fix committed (64b9168): tests green (711/40 skip), custody guard test added, hand-computed hashes eliminated.
- Phase E2 committed (36a1311): S0 GT-defect re-entry row.
- Review found D and E NOT properly fixed: per-module PLAN.md missing (still per-slice), no INFRA/INTEGRATION templates, no slice_backlog tests, G2 checks still invented (not §9.1). D-fix and E-fix items added above as PENDING.
- Branch pushed to `origin/feat/vsil-v4`.

**Next:** Owner review of the implementation candidate; then execute Phase K with actual human gate verdicts. No final PR or release tag before review.


## Implementation candidate — 2026-11-17

User authorization: “Lee el plan de hoy de odd/tasks, y termina de implementar todas las fases.
No hagas el PR final sin que yo te revise. Por ahora implementa todo”.

The historical task tables above record the starting review; this ledger supersedes their pending
implementation statuses. Code/skills are implemented; acceptance and publication are separate.

| Phase | Candidate status | Evidence |
|-------|------------------|----------|
| A follow-up | Implemented missing custody checks, real digest staleness, scope continuation, CLI failure exits | test_v4_integrity.py, test_v4_scaffold_flow.py |
| B/C follow-up | Active S3/G3 names, measurement schema, HIL docs, all-subsystem module DAG and G1 integrity checks | Ported skill tests, measurement tests, custody rule |
| D-fix.1–5 | Implemented per-module plans, INFRA/INTEGRATION templates, empty delta table, deterministic Kahn CLI and rejection tests | test_vsil_s2.py, templates/tests/test_slice_backlog.py |
| E-fix.1–2 | Six paper checks and four routes; S0 GT-defect re-entry retained alongside tutor corrections | test_vsil_g2.py |
| F | Mandatory module context isolation, allowed-write review, fresh-session handoff; slice parent owns shared files | test_vsil_s3.py, test_vsil_subagents.py |
| G | Slice floor regression, unchanged-module self-diagnosis, plan-defect route, system-only prototype, evidence origin | test_vsil_g3.py |
| H | Applied authoritative neutral delta chains; S0/S1 delta-sync instructions and bounded G0/G1 review | test_v4_integrity.py; S0/S1/G1 contracts |
| I | Generated v4 instructions, source docs/profile, archive distinction and UI incompatibility disclosure | test_vsil_agents_md.py; paper implementation profiles |
| K | Automated probes implemented/executed; full T0 and human gate acceptance pending | methodology/test/T0_FM-RPI-RTL-mock/vsil_v4_flow_2026-11-17/RUN.md |
| L | 0.9.0 metadata, lockfile and unreleased changelog prepared; tag/release withheld for review | pyproject.toml, uv.lock, CHANGELOG.md |

Implementation corrections to the original plan:

- `custody verify --gate <ID>` checks a prerequisite without blocking on a previous slice's
  legitimately superseded G3 source-tree baseline. Full verify still exposes every stale latest input.
- Cite a prior G3 report by iteration/scope, rather than digesting its mutable append-only file;
  later G3 iterations must not invalidate S2 simply by appending to that report.
- Stage outputs describe delivered artifacts; an overwritten previous SDD is not a current Input.
- CLI propagates custody failure exits, so verify-manifest can actually stop verification/run.sh.

Review units (local commits, no PR): integrity tooling; D/E planning contracts and slicer;
F/G/H execution and delta-sync contracts with ported tests; I/K/L docs and release preparation.
Some units exceed 400 authored lines; they follow the plan's cohesive boundaries and no PR is
opened automatically. Split review slices before any requested PR creation.
Rollback boundaries: each unit's files/behavior listed in its commit; no UI or DB code changed.
Runtime boundary: generated scaffold and real custody console calls are exercised by the probes.
Real hardware: N/A for the mock/tooling candidate; no hardware run or verdict is claimed.


Final automated validation: `.venv/bin/python -m pytest -q` → **730 passed, 40 skipped,
1 warning, 12.81 s**. `git diff --check` clean. The warning is FastAPI/Starlette's httpx
TestClient deprecation. No UI source or DB source modifications.

Implementation commit identities:
- `8ca0224`: integrity tooling, scoped prerequisite verification and report progression.
- `4b47fe2`: D/E module plans, Kahn slicer, six-check G2 and scaffold probes.
- `243669e`: F/G/H, v4 agent instructions, HIL vocabulary, measurement stage schema and ported tests.
- Documentation/version preparation follows these commits on the same branch.

Each unit was covered by the final suite and generated scaffold/console probe. Rollback boundaries:
`8ca0224` owns custody/reports/status/parser/CLI and test_v4_integrity; `4b47fe2` owns S2/G2 planning
skills and their slicer/scaffold tests; `243669e` owns the remaining methodology templates,
generated-agent contract, HIL docs and renamed stage tests. These are review boundaries; revert
dependent units in reverse order. No actual prototype validation or publication is implied.

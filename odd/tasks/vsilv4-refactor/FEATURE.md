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
|---|---|---|---|
| D2 | Mini-V cadence | Per slice | Each slice k: S2(k)→G2(k)→S3(k)→G3(k), then slice k+1 |
| D3 | Plans location | `.codeanvil/plans/` | Methodology-owned, like `.codeanvil/design/` |
| D8 | Living GT | Full | Accepted deltas applied by S0/S1 in `delta-sync`; staleness accepts authorized advances |
| D10 | v3 projects | Fail (no migrate) | No `codeanvil migrate` command; just fail if not v4; no LEGACY_V3 or deprecated logic |
| D11 | Release | 0.9.0 | Pre-1.0 minor bump, breaking chain |
| — | Branch | `feat/vsil-v4` | From `main` |

---

## Tasks

### Phase A — Tooling foundations · ~650 LOC

| ID | Spec | Route | Status |
|---|---|---|---|
| **A1** | Configure `config.yaml` for 8-node chain (S0→G2→S3→G3), `loop_after`, `subagents` | Inline | — |
| **A2** | `reports.py`: scope, inputs (digest staleness, authorized advances), `next_step()` | Inline | — |
| **A3** | `codeanvil custody`: digest/verify/verify-manifest CLI, stateless integrity | Inline | — |
| **A4** | `backup.py`: directory targets with per-file paths, manifest hashes via custody | Inline | — |
| **A5** | `status`: show Scope, Next:, findings from `custody.verify()` | Inline | — |
| **A6** | Retire `.codeanvil/custody/` folder creation (config/paths, init/create, sync) | Inline | — |

Acceptance: v3 projects' `status` output identical; `custody` works; no DB changes.

### Phase B — Rename S2/G2 to S3/G3 · ~300 LOC

| ID | Spec | Route | Status |
|---|---|---|---|
| **B1** | `git mv S2_implement_subsystems→S3_implement_modules`, `G2_adaptive_verification→G3_adaptive_verification` | Inline | — |
| **B2** | Rename in `vsil-verifier.md`, S1/G1/RFD/skills | Inline | — |
| **B3** | Add skip marker to `test_ui_workspace.py` (§0: UI deferred) | Inline | — |
| **B4** | Update help text, HIL MCP docs | Inline | — |
| **B5** | Rename tests, sweep for S2/G2 references | Inline | — |

Intermediate: 6-node chain `S0→G0→S1→G1→S3→G3` (S3 prereq temporarily G1).

### Phase C — S1/G1 module identity, slicing readiness · ~300 LOC

| ID | Spec | Route | Status |
|---|---|---|---|
| **C1** | SDD §1.4 card: 8 fields (`module_id`, `subsystem_id`, layer, `depends_on`, provides, hw_dep, `required_vl`, `traced_reqs`); remove Meta `G0 approved` row | Inline | — |
| **C2** | S1 skill: 8-field guide, `traced_reqs` validation, `Input:` lines in report | Inline | — |
| **C3** | G1 checklist: add G1.17 (decomposition), G1.18 (topological sort) | Inline | — |
| **C4** | Update fixture SDD with new card | Inline | — |
| **C5** | Custody call sites: S0, S1, G1, RFD (C5 table: S0/RFD `--raw`, S1 Output lines, G1 verify) | Inline | — |

Acceptance: `test_custody_rule.py` passes; no hand-hashing in any skill.

### Phase D — New S2 module planning skill · ~650 LOC

| ID | Spec | Route | Status |
|---|---|---|---|
| **D1** | Create `S2_plan_modules/SKILL.md`: cadence, slice scope, plans, contracts, deltas | Inline | — |
| **D2** | References: `BACKLOG.md`, `PLAN.md`, `INFRA-PLAN.md`, `INTEGRATION-PLAN.md`, `DELTAS.md` | Inline | — |
| **D3** | `slice_backlog.py`: deterministic topological sort, cycle detection | Inline | — |

### Phase E — New G2 plan micro-gate · ~350 LOC

| ID | Spec | Route | Status |
|---|---|---|---|
| **E1** | Create `G2_plan_review/SKILL.md` + `G2_CHECKLIST.md`: 6 checks per module, verdicts (PASS/FEEDBACK) | Inline | — |
| **E2** | S0: add re-entry row for G2 `Verdict: GT defect` → Triage | Inline | — |

Acceptance: 8-node chain active; S3 prerequisite becomes G2.

### Phase F — S3 per-module fresh context · ~500 LOC

| ID | Spec | Route | Status |
|---|---|---|---|
| **F1** | Create `vsil-implementor.md` subagent: one PLAN.md, write-scoped to module only | Inline | — |
| **F2** | S3 skill: slice cadence, MCP analysis, Pause Schedule, proposed deltas | Inline | — |

### Phase G — G3 adaptive verification by slice · ~400 LOC

| ID | Spec | Route | Status |
|---|---|---|---|
| **G1** | G3 skill: slice scope, VL-0 floor regression, self-diagnosis, enrollment/pre-HW review | Inline | — |
| **G2** | Verified Prototype v4: GT version, module table with Slice/Plan/Evidence, DELTAS summary | Inline | — |
| **G3** | `vsil-verifier.md`: receives scope, runs G3.0, all digests from custody | Inline | — |

### Phase H — Living GT and design sync · ~350 LOC

| ID | Spec | Route | Status |
|---|---|---|---|
| **H1** | `DELTAS.md` schema: ID, Type, Target, Document, Before/After, Reason, Authority, Status, Applied in, Before/After sha256, Interface impact | Inline | — |
| **H2** | `authorized_advance()`: chains of applied deltas with no interface impact | Inline | — |
| **H3** | S0 `delta-sync`: apply GT deltas, bump Version, write to DELTAS.md | Inline | — |
| **H4** | S1 `delta-sync`: apply design-sync deltas, G1 rework confirms empty impact | Inline | — |

### Phase I — Generated and repo documentation · ~300 LOC

| ID | Spec | Route | Status |
|---|---|---|---|
| **I1** | `TEMPLATE_AGENT.md`: 8-node chain, cadence, routing §3.4, RFD sources (S1/G1/G3), custody rule | Inline | — |
| **I2** | Repo docs: `AGENTS.md`, `CLAUDE.md`, `README.md`, `methodology/test/README.md` | Inline | — |
| **I3** | UI disclosure (§0): v3-only until follow-up; non-chain features kept working | Inline | — |
| **I4** | Archive note: v3 items stay untouched | Inline | — |

### Phase K — End-to-end validation · no product LOC

| ID | Spec | Route | Status |
|---|---|---|---|
| **K1** | Run T0_FM-RPI-RTL-mock under v4 to Verified Prototype; 8 probes (plan defect, GT defect, design defect, self-diagnosis, deltas, stale cascade, fresh sessions, UI smoke) | Inline | — |

### Phase L — Release

| ID | Spec | Route | Status |
|---|---|---|---|
| **L1** | `pyproject.toml` → 0.9.0, changelog, tag, `CLAUDE.md` | Inline | — |

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

**Next:** Start Phase A (tooling foundations).

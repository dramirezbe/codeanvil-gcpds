# Plan — Skill S2-2: Module-by-Module Implementation (DAG Order)

Feature: `odd/tasks/2026-11-01_2235_no_tools_skills_v3.md` · Specs S1, S2, S3, S6 · Task T5
Target file: `templates/no-tools-skills/v3/S2-2_SKILL.md`
Shared contracts used: C1–C5, C7–C12 (feature doc).

## Objetivo

Implement **Step 2 of S2** for **one module per invocation**, in the topological order of
the S1 DAG: implement the module against its contracts, write its **unit test in
isolation** (reference vectors from §3), and its **bottom-up integration test** (module +
driver against the real base layer). Swap the module's stub for the real module, re-run
the base top-down test and all previously completed modules' tests (regression), and
apply the v3 self-diagnosis rule on unexpected failures. Three modes:

| Mode | When | What |
|------|------|------|
| `NEXT` | normal flow | implement the next module in topological order |
| `REWORK <module>` | S2-3 or the user routes a MODULE DEFECT to an already finished module, or C9 voided its row | reopen module k, void its row and downstream regression (C9b), fix, re-evidence, then re-run regression for every row after k |
| `INTEGRATION` | all modules VALID | final all-real wiring run (C11, paper §5.1 "Integration") |

## Mapeo V-SIL-v3

| Paper | Element |
|-------|---------|
| §7 S2, Step 2 "Each module (DAG order)" | Implement module against contract → Unit test in isolation → Bottom-up integration (module + driver vs base) |
| §7 Mandatory floor | Each module: unit test + bottom-up integration with driver |
| §5.1 Integration | `INTEGRATION` mode — modules wired through the base layer, no module stubs |
| §5.1 / §5.2 HAL | First module = device adapter (layer HAL, VL-2) behind the base-layer HAL port (C8) |
| §1 Terminology | Drivers (call the unit under test); sandwich = top-down + bottom-up |
| §9.1 Self-diagnosis | Unchanged module fails on re-test ⇒ undeclared dependency ⇒ design defect ⇒ S1 |
| §9.1 Defect classes | Module defect → S2 (here); design defect → S1 |

## Activation Contract (C1)

**Load when:** S2-1 base rows are VALID in the pasted MODULE LEDGER and the user asks to
implement a module, "next module", rework a module, or the integration run.
**Do NOT load when:** no base evidence (→ S2-1); no G1 PASS (→ S1-2); the user asks for G2 or
VL-1/VL-2 testing (→ S2-3); the requested change needs a new contract (→ DESIGN DEFECT NOTE → S1-1).
**Context pack (C7):** module's §1.3 card + its §3 contracts + base-layer contract types +
MODULE LEDGER (+ the DESIGN/MODULE defect evidence when in REWORK). Integration mode also
needs the list of all module files.

## Inputs

| Input | Source | Required |
|-------|--------|----------|
| S1_design.md (approved) sections for the module | S1-1 | yes |
| G1 RECORD (contract versions) | S1-2 | yes — rows built on another g1_version are VOID (C9a) |
| MODULE LEDGER (C3) | S2-1 / previous S2-2 runs | yes |
| Mode + module ID (`NEXT`, `REWORK <id>`, `INTEGRATION`) | user / S2-3 routing | yes |
| Defect evidence (REWORK) | S2-3 report or user paste | yes in REWORK |

## Outputs

1. **Module card** — id, layer, contracts consumed/provided (`id@schema_version`),
   `required_vl`, SYS- traced, position k/n, upstream modules already real vs stubbed.
2. **Module code** — implements only the declared `provides` contracts. The device-adapter
   module implements the base-layer HAL port against the real driver (GNU Radio / libhackrf);
   at VL-0 its tests run against the HAL stub and a mocked driver call layer.
3. **Unit tests** — expected values copied verbatim from §3 vectors (C5) + edge cases named
   in the stub recipe (nominal / degraded / edge).
4. **Driver + bottom-up integration test** — driver feeds the module through the real base
   router; asserts output contract (type, shape, units, rate; latency bound when measurable
   at VL-0).
5. **Test manifest** (C4) — names of all tests to run, incl. regression set.
6. **Regression set** — base top-down test with this module real + all earlier VALID rows.
7. **Updated MODULE LEDGER** rows (C3), state `VALID` only from matching pasted evidence.
8. On failure: `MODULE DEFECT` fix batch, or `DESIGN DEFECT NOTE` (C3) → S1-1, or
   `RFD SEED` → SX-1.

## Prompt template (resumido)

```
Step 0  Ledger check (C2 closed domain):
        - G1 RECORD version ≠ ledger rows' g1_version → mark those rows VOID (C9a), list them.
        - NEXT: requested module = next in §2.2 order? If not:
          "Module <m> is not next (next is <n>). [k] keep order and do <n> / [o] override and
           do <m> with predecessors stubbed / [x] stop" — default k.
        - REWORK <m>: void m's row and the regression column of every later row (C9b); list them.
        - INTEGRATION: every row VALID? else list missing rows and stop.
Step 1  Module card. pause.
Step 2  Implementation (fix batch in REWORK). pause.
Step 3  Unit tests (isolation). pause.
Step 4  Driver + bottom-up integration test + regression + manifest + exact commands. pause.
Step 5  EVIDENCE (C4) → paste:
          matches manifest, all green → ledger rows VALID → "Next: <module k+1>" |
            "REWORK done — re-run regression for rows after k" | "All VALID → INTEGRATION" |
            after INTEGRATION → "→ S2-3 (new chat)".
          mismatch → NOT EVIDENCED → re-run.
          this module red → MODULE DEFECT → one fix batch per message → re-run.
          an UNCHANGED module red → first re-run once in a quiet environment (m9: rule out a
            flaky/env failure); still red AND the failing test is that module's OWN unit or
            bottom-up test → self-diagnosis: undeclared dependency → DESIGN DEFECT NOTE → S1-1.
            (A top-down-only failure is not enough to trigger the rule; diagnose first.)
          contract unmeetable by any implementation → apply C12 → RFD SEED → SX-1.
```

Rules: no edits to other modules or to base-layer contracts (a needed change = design
defect); no extra features beyond `provides`; evidence-only status (C4); expected values only
from §3 vectors or SyRS acceptance criteria (C5).

## Criterios de aceptación

1. Exactly one module per run (or the integration run); order follows §2.2 unless the user
   picks `o`.
2. Unit + bottom-up tests exist for the module (VL-0 floor) and reuse §3 vectors verbatim.
3. Regression includes base top-down + all VALID rows; REWORK re-runs every later row.
4. Self-diagnosis is applied only after one clean re-run and only on an unchanged module's
   own tests; it routes to S1-1 via DESIGN DEFECT NOTE, never patched locally.
5. Ledger row is VALID only from pasted output matching the manifest (C4).
6. INTEGRATION run uses no module stubs; at VL-0 only the HAL port stub remains.
7. Test: fixture `F3_pastes.md` (T2b) — the skipped-test paste → NOT EVIDENCED; the
   unchanged-module failure → DESIGN DEFECT NOTE.

## Dependencias

- Upstream: S2-1 (first run) / previous S2-2 runs / S2-3 (REWORK routing).
- Downstream: next S2-2 run, INTEGRATION, then S2-3.
- Exits: S1-1 (design defect), SX-1 (infeasible).

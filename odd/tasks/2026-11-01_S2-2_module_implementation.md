# Plan — Skill S2-2: Module-by-Module Implementation (DAG Order)

Feature: `odd/tasks/2026-11-01_2235_no_tools_skills_v3.md` · Specs S1, S2, S3, S6 · Task T5
Target file: `templates/no-tools-skills/v3/S2-2_SKILL.md`

## Objetivo

Implement **Step 2 of S2** for **one module per invocation**, in the topological order of
the S1 DAG: implement the module against its contracts, write its **unit test in
isolation** (reference vectors from §3), and its **bottom-up integration test** (module +
driver against the real base layer). Swap the module's stub for the real module, re-run
the base top-down test and all previously completed modules' tests (regression), and
apply the v3 self-diagnosis rule on unexpected failures.

## Mapeo V-SIL-v3

| Paper | Element |
|-------|---------|
| §7 S2, Step 2 "Each module (DAG order)" | Implement module against contract → Unit test in isolation → Bottom-up integration (module + driver vs base) |
| §7 Mandatory floor | Each module: unit test + bottom-up integration with driver |
| §1 Terminology | Drivers (call the unit under test); sandwich = top-down + bottom-up |
| §9.1 Self-diagnosis | Unchanged module fails on re-test ⇒ undeclared dependency ⇒ design defect ⇒ S1 |
| §9.1 Defect classes | Module defect → S2 (here); design defect → S1 |

## Inputs

| Input | Source | Required |
|-------|--------|----------|
| S1_design.md (approved) | S1-1 | yes — the module's §1.3 black box, its §3 contracts, §2.2 order |
| S2-1 evidence record + base-layer code | S2-1 | yes |
| Module progress ledger (completed modules + their evidence) | previous S2-2 runs | yes after module #1 |
| Module ID to implement (or "next") | user | yes |

## Outputs

1. **Module card** — id, layer, contracts consumed/provided, `required_vl`, SYS- traced,
   position k/n in topological order, upstream modules already real vs stubbed.
2. **Module code** — implements only the declared `provides` contracts.
3. **Unit tests** — reference vectors of every consumed/provided contract + edge cases
   named in the stub recipe (nominal / degraded / edge).
4. **Driver + bottom-up integration test** — driver feeds the module through the real
   base router; asserts output contract (type, shape, units, rate, latency bound when
   measurable at VL-0).
5. **Regression set** — base top-down test with this module real + all earlier modules' tests.
6. **Updated module progress ledger** (pasted back by the user next time):
   `| step | module | unit | bottom-up | regression | VL-0 evidence | date |`.
7. Defect routing statement when red.

## Prompt template (resumido)

```
Step 0  Ledger check: paste ledger; confirm requested module is next in topological
        order (or its predecessors are real/stubbed consistently). Out-of-order → warn, ask.
Step 1  Module card. pause.
Step 2  Implementation. pause.
Step 3  Unit tests (isolation). pause.
Step 4  Driver + bottom-up integration test + regression commands. pause.
Step 5  EVIDENCE: user pastes output →
          all green  → ledger row VL-0 ✔ → "Next: <module k+1>" or "All modules done → S2-3".
          this module red → module defect → fix (max one fix batch per message), re-run.
          an UNCHANGED module red → self-diagnosis: undeclared dependency → DESIGN DEFECT
                                    → stop, produce S1 rework note (→ S1-1 / S1-2).
          contract cannot be met by any implementation (math/physics) → SX-1 seed.
```

Rules: no edits to other modules or to the base layer contracts (a needed change = design
defect); no extra features beyond `provides`; evidence-only status (P2/P4).

## Criterios de aceptación

1. Exactly one module per run; order follows §2.2 unless the user explicitly overrides.
2. Unit + bottom-up tests exist for the module (VL-0 floor) and reuse §3 vectors.
3. Regression includes base top-down + all previously real modules.
4. The self-diagnosis rule is applied and routes to S1, not patched locally.
5. Ledger row only marked ✔ from pasted output.

## Dependencias

- Upstream: S2-1 (first run) / previous S2-2 runs. Downstream: next S2-2 run or S2-3.
- Exits: S1-1 (design defect), SX-1 (infeasible).

# Plan — Skill S2-1: Base Layer, Stubs, and Top-Down Integration

Feature: `odd/tasks/2026-11-01_2235_no_tools_skills_v3.md` · Specs S1, S2, S3, S6 · Task T5
Target file: `templates/no-tools-skills/v3/S2-1_SKILL.md`

## Objetivo

Implement **Step 1 of S2**: the base layer (orchestration, HAL, data routing, interface
contract types) exactly as declared in the G1-approved S1 design; generate one
deterministic **stub** per contract from its stub recipe; deliver the base-layer **unit
tests** and the **top-down integration test** (base + all stubs). Chat-only: the LLM
writes the code and tests in the chat, the user runs them locally and pastes the output;
the LLM interprets results but never claims a pass without pasted evidence.

## Mapeo V-SIL-v3

| Paper | Element |
|-------|---------|
| §7 S2, Step 1 "Base layer first" | Implement base layer → Generate stubs from G1 contracts → Top-down integration (base + all stubs) |
| §7 Mandatory floor | Base layer: unit test + top-down integration with stubs (VL-0, cannot be skipped) |
| §1 Terminology | Stubs (called by the unit under test); top-down integration with stubs |
| P2/P4 | Evidence is the user's pasted run output; claims name the environment (VL-0, logic) |

## Inputs

| Input | Source | Required |
|-------|--------|----------|
| S1_design.md (G1-approved) | S1-1 | yes — §1.2 base layer, §2 DAG, §3 contracts |
| G1 Record (PASS) | S1-2 | yes |
| Language/runtime + test framework choice | S1 DEC (e.g. Python 3.10, pytest; GNU Radio 3.10 or libhackrf) | yes |
| User environment facts (OS, versions installed) | user | asked at Step 0 |

## Outputs

1. **Implementation plan** — file tree for the project (e.g. `base/contracts.py`,
   `base/hal.py`, `base/router.py`, `base/orchestrator.py`, `stubs/…`, `tests/…`).
2. **Contract types** — one typed definition per §3 contract (dataclass / numpy dtype /
   GNU Radio port signature) incl. schema version and units in docstring-free names.
3. **Base layer code** — orchestrator, HAL interface (abstract + real adapter skeleton
   that is *not exercised* at VL-0), router.
4. **Stubs** — one per contract, generated literally from the stub recipe (seeded RNG,
   fixed vectors), each emitting the reference vectors of §3.
5. **Unit tests (base)** and **top-down integration test** (orchestrator + router + HAL
   stub + module stubs: data flows end-to-end along every DAG edge, schema/units/rate checks).
6. **Run instructions** — exact commands for the user (`python -m pytest -q tests/base`).
7. **S2-1 evidence record** after the user pastes results:
   `BASE LAYER — VL-0 evidence: unit N/N pass, top-down M/M pass, env: <pasted>`.

## Prompt template (resumido)

```
Step 0  Preconditions: G1 PASS record? stack from DECs? user env (OS, Python, GR/libhackrf)?
Step 1  Plan: file tree + mapping contract → type → stub → test. pause.
Step 2  Contracts module (types). pause.
Step 3  Base layer: HAL interface + orchestrator + router. pause.
Step 4  Stubs (one per contract; deterministic). pause.
Step 5  Tests: base unit tests + top-down integration test + run commands. pause.
Step 6  EVIDENCE: "Run the commands and paste the full output."
        - all green → evidence record → "Proceed to S2-2 with module #1 of the topological order."
        - red → classify: code defect (fix here, re-run) | contract cannot be honoured
          → design defect → S1-1 rework (via S1-2 FAIL path) | infeasible → SX-1.
```

Rules:
- Implement **only** what S1 declared; any needed new interface ⇒ stop, design defect → S1.
- Stubs must be deterministic (fixed seed, fixed vectors) — VL-0 depends on it.
- No module business logic in the base layer.
- Never write "tests pass" without the user's pasted output (P2/P4).
- Keep each code message under a size the chat can hold; split files across messages.

## Criterios de aceptación

1. Every §3 contract has a type definition and a stub; every stub reproduces its §3
   reference vectors.
2. The top-down test exercises every DAG edge at least once with stubs.
3. HAL is the only code that would touch hardware; at VL-0 it is replaced by its stub.
4. The evidence record quotes the pasted run output (counts + environment).
5. Failures are routed with the v3 defect classes (module/code → stay; design → S1; infeasible → SX-1).

## Dependencias

- Upstream: S1-2 PASS. Downstream: S2-2 (first module). Exits: S1-1 (design defect), SX-1.

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
   GNU Radio port signature). Each type carries its `schema_version` as a constant, and
   units are part of field names (e.g. `power_dbfs`, `freq_mhz`), so tests can assert them
   without reading comments (m8).
3. **Base layer code** — orchestrator, router, and the **HAL port** only: the abstract
   hardware interface plus its deterministic stub (C8). The real device adapter is a module
   written by S2-2, not here.
4. **Stubs** — one per contract, generated literally from the stub recipe (seeded RNG,
   fixed vectors), each emitting the reference vectors of §3.
5. **Unit tests (base)** and **top-down integration test** (orchestrator + router + HAL
   stub + module stubs: data flows end-to-end along every DAG edge, schema/units/rate checks).
6. **Run instructions** — exact commands for the user (`python -m pytest -q tests/base`).
7. **Test manifest** — the exact list of test names the skill wrote, emitted before the
   run instructions (C4 compares the paste against it).
8. **S2-1 evidence record** after the user pastes results — the first rows of the
   `MODULE LEDGER` (C3) for `base`:
   `| <cycle> | 0 | base | <g1_version> | N/N | — | M/M top-down | <command + env> | VALID |`.

## Activation Contract (C1)

**Load when:** a G1 RECORD with PASS is pasted with the S1 design and the user asks for S2,
base layer, stubs, or the top-down integration test; or a new G1 RECORD voids base evidence (C9).
**Do NOT load when:** no G1 PASS (→ S1-2); the user asks for a specific module (→ S2-2);
the user asks for G2 (→ S2-3).
**Context pack (C7):** S1 design §1–§3 + G1 RECORD + user environment.

## Prompt template (resumido)

```
Step 0  Preconditions: G1 PASS record? stack from DECs? user env (OS, Python, GR/libhackrf)?
Step 1  Plan: file tree + mapping contract → type → stub → test. pause.
Step 2  Contracts module (types). pause.
Step 3  Base layer: HAL interface + orchestrator + router. pause.
Step 4  Stubs (one per contract; deterministic). pause.
Step 5  Tests: base unit tests + top-down integration test + run commands. pause.
Step 6  EVIDENCE (C4): "Run exactly these commands and paste the full output."
        - command + test names match the manifest, all green → ledger rows → "Proceed to
          S2-2 with module #1 of the topological order (the device adapter, C8)."
        - mismatch (missing/skipped/extra tests, other command) → NOT EVIDENCED → re-run.
        - red → classify: code defect (fix here, re-run) | contract cannot be honoured →
          `DESIGN DEFECT NOTE` (C3) → S1-1 | infeasible per C12 → `RFD SEED` → SX-1.
Re-entry: when a new G1 RECORD changes a base-layer contract's schema_version, S2-1 is
re-run for the changed contracts and the base rows become VOID until re-evidenced (C9).
```

Rules:
- Implement **only** what S1 declared; any needed new interface ⇒ stop, design defect → S1.
- Stubs must be deterministic (fixed seed, fixed vectors) — VL-0 depends on it.
- Expected values in every assertion are copied verbatim from the §3 reference vectors
  (C5); the skill never computes its own "expected" numbers.
- No module business logic in the base layer.
- Never write "tests pass" without the user's pasted output (P2/P4).
- Keep each code message under a size the chat can hold; split files across messages.

## Criterios de aceptación

1. Every §3 contract has a type definition and a stub; every stub reproduces its §3
   reference vectors.
2. The top-down test exercises every DAG edge at least once with stubs.
3. HAL is the only code that would touch hardware; at VL-0 it is replaced by its stub.
4. The evidence record quotes the pasted run output (command, counts, names, environment)
   and matches the test manifest (C4).
5. Failures are routed with the v3 defect classes (module/code → stay; design → S1 via
   DESIGN DEFECT NOTE; infeasible → SX-1 via RFD SEED).
6. The base layer contains no device-adapter code (C8).

## Dependencias

- Upstream: S1-2 PASS. Downstream: S2-2 (first module). Exits: S1-1 (design defect), SX-1.

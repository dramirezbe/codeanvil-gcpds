# V-SIL v3 — No-Tools (Chat-Only) Skills

Chat-only skills that run the full V-SIL v3 lifecycle (`methodology/V-SIL-v3/V-SIL_v3.md`) in
any plain LLM chat: no tools, no file access, no code execution. The LLM guides; the user pastes
documents and run outputs; handoffs between skills are copy-paste **records**.

## Flow

```
Build Package
   │
 S0-1 ──► S0-2 (G0 + Gate H) ──► S1-1 ──► S1-2 (G1) ──► S2-1 ──► S2-2 ×n ──► S2-3 (G2) ──► Verified Prototype
   ▲         │ FAIL / not authorised   ▲      │ FAIL        ▲         ▲             │
   └─────────┘                         └──────┘             │         └─ module ────┤
   ▲                                   ▲                    │                       │
   │                                   └──────── design ────┴───────────────────────┤
   └──── updated Build Package ◄── SX-1 (RFD) ◄── infeasible (S1, G1, S2, G2) ──────┘
```

## Skills

| Skill | V-SIL v3 | File | Plan | New chat? |
|-------|----------|------|------|-----------|
| `S0-1` Build Package normalisation | §3 S0 | `S0-1_SKILL.md` | `odd/tasks/2026-11-01_S0-1_normalise_build_package.md` | — |
| `S0-2` G0 structural validation + Gate H | §4 G0 | `S0-2_SKILL.md` | `odd/tasks/2026-11-01_S0-2_g0_structural_validation.md` | yes |
| `S1-1` Layered architecture design | §5 S1 | `S1-1_SKILL.md` | `odd/tasks/2026-11-01_S1-1_layered_architecture_design.md` | — |
| `S1-2` G1 design review | §6 G1 | `S1-2_SKILL.md` | `odd/tasks/2026-11-01_S1-2_g1_design_review.md` | yes |
| `S2-1` Base layer, stubs, top-down integration | §7 S2 Step 1 | `S2-1_SKILL.md` | `odd/tasks/2026-11-01_S2-1_base_layer_and_stubs.md` | — |
| `S2-2` Module implementation (NEXT / REWORK / INTEGRATION) | §7 S2 Step 2 | `S2-2_SKILL.md` | `odd/tasks/2026-11-01_S2-2_module_implementation.md` | — |
| `S2-3` G2 adaptive verification + Verified Prototype | §8 G2, §10 | `S2-3_SKILL.md` | `odd/tasks/2026-11-01_S2-3_g2_adaptive_verification.md` | yes |
| `SX-1` Request for Deviation | §9 | `SX-1_SKILL.md` | `odd/tasks/2026-11-01_SX-1_request_for_deviation.md` | — |

Naming: `S<stage>-<n>` = V-SIL v3 stage (its gate included) + skill number inside it; `SX` =
cross-stage (an RFD can be raised from any stage).

## Records (handoff blocks)

| Record | Emitted by | Pasted into |
|--------|-----------|-------------|
| `GATE H RETURN` | S0-2 (Gate H not authorised) | S0-1 |
| `G0 RECORD` | S0-2 (G0 PASS + Gate H authorised) | S1-1 |
| `G1 RECORD` | S1-2 (G1 PASS) | S2-1, S2-2, S2-3 |
| `MODULE LEDGER` | S2-1, S2-2 | S2-2, S2-3 |
| `DESIGN DEFECT NOTE` | S1-2, S2-1, S2-2, S2-3, SX-1 | S1-1 (rework mode) |
| `RFD SEED` | S1-1, S1-2, S2-1, S2-2, S2-3 | SX-1 |

## Principles enforced (paper §2)

- **P1** HITL is an authorisation barrier (Gate H, RFD decision); HIL is a validation barrier (G2.2).
- **P2** Oracle ≠ generator: S0-2, S1-2 and S2-3 run in a new chat and refuse to judge their own work.
- **P3** Mechanical rejection beats LLM approval (approximated in chat; see each gate's disclaimer).
- **P4** Verified ≠ validated: every claim names its verification level; a pass needs pasted evidence.

## Test inputs

`test-inputs/` — real-time FM spectrogram with a HackRF One (Build Package, StRS, SyRS). See
`test-inputs/README.md`.

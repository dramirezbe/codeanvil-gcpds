# No-tools skills v3 — V-SIL v3 chat-only skill set

Objective: chat-only (no tools) skill set in `templates/no-tools-skills/v3/` covering the full V-SIL v3 flow (Build Package → S0/G0 → S1/G1 → S2/G2 → Verified Prototype | RFD), plus FM-spectrogram test inputs.
Branch: `feat/no-tools-skills-v3` · Delivery: `ask-on-risk` · Test runner: none (passive Markdown; structural readback + manual G0 dry-run of test inputs).

## Specs

- **S1** — "Toma @templates/no-tools-skills/v2/ y dame v3/ leyendo el refactor de @methodology/V-SIL-v3/ y leyendo el estilo de skill (solo chat, sin tools)". Output dir: `templates/no-tools-skills/v3/`.
- **S2** — "Genera un conjunto de skills (solo chat, sin tools) que cubran **todo el flujo V-SIL v3**, desde la captura de requisitos hasta el software verificado y validado." Each skill: "Seguir la **estructura y estilo de v2**", "Implementar la **metodología definida en V-SIL-v3** (no la de v2)", "Representar una fase o artefacto concreto del flujo v3", "Ser autocontenida: incluir inputs esperados, outputs generados, y criterios de aceptación."
- **S3** — Naming: "Usa un prefijo `S#` secuencial (S1, S2, S3…) alineado con el orden del flujo V-SIL-v3." combined with the first request "a qué S# pertenece y luego el # de skill". Assumption: prefix `S<stage>-<n>` where `<stage>` is the V-SIL v3 stage (S0, S1, S2) the skill belongs to (its gate included) and `<n>` the skill number inside it; the cross-stage RFD skill uses `SX-1`.
- **S4** — Test inputs in `templates/no-tools-skills/v3/test-inputs/`: "**Proyecto de prueba:** Espectrograma FM en tiempo real con HackRF One. Entrada RF: banda FM comercial (~88–108 MHz). Salida: visualización de espectrograma en pantalla. Stack: Python + GNU Radio o acceso directo vía libhackrf." At least "**StSR** (Stakeholder Requirements Specification)" and "**SySR** (System Requirements Specification)", "lo suficientemente sencillos para probar el flujo completo de las skills pero técnicamente correctos."
- **S5** — ODD planning in `odd/tasks/`: "recuerda usar la fecha de hoy como nombre de archivo luego a qué S# pertenece y luego el # de skill". Each plan file includes: "**Objetivo**", "**Inputs**", "**Outputs**", "**Prompt template** resumido", "**Criterios de aceptación**", "**Dependencias**", "**Mapeo V-SIL-v3**". "Planea **todas** las skills con lujo de detalle antes de empezar a escribirlas."
- **S6** — Constraints: "Las skills son **solo chat** (sin tools, sin acceso a archivos, sin ejecución de código)." "No asumas herramientas externas en las skills; el LLM guía al usuario paso a paso."

## Tasks

| ID | Specs | Deliverable | Route | Status | Commit |
|----|-------|-------------|-------|--------|--------|
| T1 | S3, S5 | Feature doc + 8 per-skill plan files `odd/tasks/2026-11-01_S<stage>-<n>_<slug>.md` | inline | done | see Log |
| T2 | S4 | `test-inputs/` — Build Package, G0_StRS, G0_SyRS, README | inline | done | see Log |
| T3 | S1, S2, S6 | S0-1 normalisation + S0-2 G0/Gate H skills | inline | done | see Log |
| T4 | S1, S2, S6 | S1-1 layered architecture + S1-2 G1 review skills | inline | done | see Log |
| T5 | S1, S2, S6 | S2-1 base layer, S2-2 modules, S2-3 G2 skills | inline | done | see Log |
| T6 | S1, S2, S6 | SX-1 RFD skill + v3 README index | inline | done | see Log |

Route evidence: units share one output contract chain (S1-1's document format is S1-2's and S2-x's input), so they are not independent → no Writer trigger; all inline.

## Skill map (V-SIL v3 → skill)

| Skill | V-SIL v3 | Plan file |
|-------|----------|-----------|
| `S0-1` Build Package normalisation | §3 S0 | `2026-11-01_S0-1_normalise_build_package.md` |
| `S0-2` G0 structural validation + Gate H | §4 G0 | `2026-11-01_S0-2_g0_structural_validation.md` |
| `S1-1` Layered architecture design | §5 S1 + S1_G1_template §0–§6 | `2026-11-01_S1-1_layered_architecture_design.md` |
| `S1-2` G1 design review | §6 G1 + S1_G1_template G1.1–G1.8 | `2026-11-01_S1-2_g1_design_review.md` |
| `S2-1` Base layer + stubs + top-down integration | §7 S2 Step 1 | `2026-11-01_S2-1_base_layer_and_stubs.md` |
| `S2-2` Module implementation (DAG order) | §7 S2 Step 2 | `2026-11-01_S2-2_module_implementation.md` |
| `S2-3` G2 adaptive verification + Verified Prototype | §8 G2, §9.1, §10 | `2026-11-01_S2-3_g2_adaptive_verification.md` |
| `SX-1` Request for Deviation | §9.2–§9.4 | `2026-11-01_SX-1_request_for_deviation.md` |

## Log

- **L1** (2026-11-01, user, verbatim first request): "Toma @templates/no-tools-skills/v2/ y dame v3/ leyendo el refactor de @methodology/V-SIL-v3/ y leyendo el estilo de skill (solo chat, sin tools), haz las skills vagamente que representen todo el flujo de v2 hasta el software completo. Dame un ejemplo de StSR y SySR para probar estas skills. Active odd y en odd/tasks planea todas las skills recuerda usar la fecha de hoy como ombre de archivo luego a qué S# pertenece y luego el # de skill. Planea todas las skills con lujo de detalle. Recuerda seguir @templates/no-tools-skills/v2/ pero para la metodología definida en V-SIL-v3"
- **L2** (2026-11-01, user refinement): structured prompt — Contexto / Tarea principal / Nomenclatura `S#` / Test inputs FM HackRF / Planificación ODD (Objetivo, Inputs, Outputs, Prompt template, Criterios de aceptación, Dependencias, Mapeo V-SIL-v3) / Restricciones solo-chat. Quoted in S2–S6.
- **L3** Decisions: (a) v3 drops the G1 SRS (v2) — S1 now produces the layered-architecture design document of `methodology/V-SIL-v3/S1_G1_template.md`; v2's multi-hypothesis + QA scoring survives inside S1-1 as the partitioning decision DEC-001. (b) G0 rules are unchanged from v2 (paper §4: same deterministic gate) plus human Gate H. (c) Skills are English (Language Domain Contract); test inputs English so G0 heading rules apply verbatim. (d) Chat-only implementation skills (S2-x) emit code in chat; the user runs it and pastes output — no pass claim without pasted evidence (P2/P3/P4).
- **L4** Pre-existing user working-tree changes (v2 move, `.atl/` registry) left unstaged and untouched.

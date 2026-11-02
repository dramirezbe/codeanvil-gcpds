# Plan — Skill S1-1: Layered Architecture Design

Feature: `odd/tasks/2026-11-01_2235_no_tools_skills_v3.md` · Specs S1, S2, S3, S6 · Task T4
Target file: `templates/no-tools-skills/v3/S1-1_SKILL.md`

## Objetivo

From the G0-passed, Gate-H-authorised StRS + SyRS, produce the **S1 Layered
Architecture Design document** (structure of `methodology/V-SIL-v3/S1_G1_template.md`
§Meta, §0–§6): COTS envelope, base layer + plug-in modules + integration, component
dependency DAG with topological order, typed interface contracts (HW→SW, SW→SW, SW→HW)
each with a deterministic stub recipe and reference vectors, traceability, MADR design
decisions, and known risks / pre-RFD infeasibilities. The design must be good enough for
G1 to answer "Are all implementation-critical design choices resolved?".

## Mapeo V-SIL-v3

| Paper / template | Skill job |
|------------------|-----------|
| Template §Meta (G0 aprobado, Gate H aprobado) | Job 0 — GT lock |
| Template §0 Envolvente COTS (inventory, topology, PHY-*) | Job 1 |
| v2 Jobs 1–4 (ASRs, ≥3 candidates, QA matrix, trade study) → template §5 DEC-001 | Job 2 — partitioning decision |
| Paper §5.1, template §1 (base layer: orchestration/HAL/routing; module black boxes + verification profile) | Job 3 |
| Paper §5.2, template §2 (DAG with HW nodes; topological order) | Job 4 |
| Template §3 (contracts HW→SW / SW→SW / SW→HW, stub recipe, vectors) | Job 5 |
| Template §4 (SYS→module, module→SYS, NRM→contract) | Job 6 |
| Template §5 (further DECs) + §6 (RSK, pre-RFD) + self-check | Job 7 |
| Paper §9.2 (RFD discoverable at S1) | Job 7 escalation → SX-1 |

## Inputs

| Input | Source | Required |
|-------|--------|----------|
| G0_StRS.md + G0_SyRS.md | S0-1 / user | yes |
| G0 Record (verdict PASS + Gate H AUTHORISED) | S0-2 | yes — refuse without it (ask the user to confirm otherwise) |
| Cycle identifier (e.g. `cycle_01`) | user | yes (asked at Job 0) |
| Preferred stack hints inside the GT (e.g. "GNU Radio or libhackrf") | GT | used as constraint, not decided here |
| G1 FAIL report (rework) | S1-2 | optional → re-run named jobs + downstream |
| Design-defect routing from G2 | S2-3 | optional → same rework procedure |

## Outputs

One Markdown document `S1_design.md` (user copies it from the chat) with sections:

- **Meta** — project, cycle, date, author, G0 ref, Gate H ref, state `borrador`.
- **§0** — 0.1 device inventory (HWC-* rows), 0.2 physical topology (Mermaid),
  0.3 `PHY-NNN` tables (connector, impedance, band, expected loss, key constraint).
- **§1** — 1.1 white box (Mermaid) + decomposition motivation; 1.2 base layer
  (1.2.1 orchestration, 1.2.2 HAL, 1.2.3 routing); 1.3 one black-box table per module
  (`layer`, responsibility, `depends_on`, `provides`, `hw_dependency`, `required_vl`)
  + VL justification.
- **§2** — 2.1 DAG (Mermaid; HW subgraph; edges labelled with contract IDs; nodes show
  layer · VL); 2.2 topological implementation order table.
- **§3** — every contract: full field table, **stub recipe** (source type, concrete data,
  nominal/degraded/edge conditions), **reference vectors** (input → expected output).
- **§4** — 4.1 SYS→modules, 4.2 module→SYS, 4.3 NRM→contract.
- **§5** — DEC-001 (partitioning, from the multi-hypothesis study) + DEC-002..n (MADR).
- **§6** — RSK table with "RFD potential? sí/no".
- **Annex A** — Partitioning study (ASR table, condition groups, ≥3 candidates,
  weighted QA matrix, top-2 trade study) — the v2 evidence behind DEC-001.
- **Self-check** — the mechanical G1 rules (G1.1, G1.2 presence, G1.3, G1.5) pre-run
  by the author, labelled "author self-check — NOT a G1 verdict (P2)".

## Prompt template (resumido)

```
Job 0  GT LOCK      Present: StRS id/version, SyRS id/version, G0 verdict, Gate H.
                    "Do you confirm this GT as the locked S1 design basis? [y/N/x]" + cycle id.
Job 1  COTS envelope    §0 → pause "continue?"
Job 2  Partitioning     ASRs → condition groups → ≥3 candidates (no strawmen; HWC HARD
                        violation = disqualify + replace) → QA matrix 0–5, weights MUST3/
                        SHOULD2/COULD1 → top-2 trade study → DEC-001 → pause
Job 3  Building blocks  §1 base layer + module black boxes + VL profile → pause
Job 4  DAG              §2 Mermaid DAG + topological order (no module→module edge
                        without a contract; HW as sources/sinks) → pause
Job 5  Contracts        §3, one contract per DAG edge, stub recipe + vectors → pause
                        (may span several messages: "Contracts 1–4 of 9 … continue")
Job 6  Traceability     §4 → pause
Job 7  Decisions+Risks  §5 DEC-002.., §6 RSK, self-check, assembled-document index,
                        handoff "Submit S1_design.md to S1-2 in a NEW chat (P2)."
```

Rules carried from v2: one job per message, wait for "continue"; justify every choice in
writing; stay inside the HWC envelope; do not implement (no source code beyond an
interface signature); do not invent requirements — gaps go to a Gap List.
New v3 rules: modules only talk through base-layer interfaces; every contract must be
stub-able without asking the designer; `hw_dependency: true ⇒ required_vl: VL-2`;
an "under any partitioning on this COTS" infeasibility is an **RFD candidate**, not a
design defect → recommend SX-1 and stop design for the affected requirements.

## Criterios de aceptación

1. Document contains every template section (§Meta, §0.1–0.3, §1.1–1.3, §2.1–2.2,
   §3.1–3.3 as applicable, §4.1–4.3, §5, §6).
2. DAG is acyclic and its topological order is listed; every edge has a contract ID
   present in §3.
3. Every contract has all fields, a concrete stub recipe (no "reasonable data") and ≥ 2
   reference vectors (nominal + edge).
4. Every SYS- traces to ≥ 1 module; every module traces to ≥ 1 SYS- (else flagged orphan).
5. Every module with `hw_dependency: true` has `required_vl: VL-2`; every VL choice justified.
6. Exactly one HAL; no module touches HW except via HAL.
7. DEC-001 cites ≥ 3 real alternatives and the weighted QA scores.
8. The skill never declares G1 PASS (P2) — it hands off to S1-2 in a fresh context.
9. Test: from the FM test GT it yields a design with e.g. `hackrf_source (HAL, VL-2)`,
   `psd_engine (DSP, VL-1)`, `waterfall_buffer`, `waterfall_view`, `gain_control` …
   (exact names are the agent's choice; the checks above are what count).

## Dependencias

- Upstream: S0-2 (PASS + Gate H). Rework entries: S1-2 FAIL, S2-3 design-defect routing.
- Downstream: S1-2. Possible exit: SX-1.

## Design notes

- v2 G1 jobs 1–5 compressed into Job 2 + Annex A; v2 SRS authoring (Jobs 6–7) removed —
  V-SIL v3 S1 output is the layered design, not an SRS.
- Rework procedure kept from v2 (rework named job + every downstream job; GT stays locked;
  a GT change ⇒ back to S0 or RFD, never silently).

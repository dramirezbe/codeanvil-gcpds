# PLAN — V-SIL.tex

## Goal

Produce a self-contained LaTeX document (`V-SIL.tex`) presenting the V-SIL
three-layer methodology for SDR FM spectrum-sensing, integrating content from
three source documents into a unified technical paper with a TikZ V-diagram.

---

## Sources (read, not modified)

| Source file | Role in V-SIL | Key content to extract |
|---|---|---|
| `methodology/1_CI-SIL_+_zz/zz_Workflow_.md` | Layer 1 — Conceptual Validation | Ctx 00–03 stages, gates H, R0–R3 defect routing, 6 Governing Artifacts, "Verified Prototype + Evidence" terminal output, Figures 1–3 |
| `methodology/1_CI-SIL_+_zz/1_CI-SIL_+_zz.md` | Layer 2 — Software Development | CI+SIL as V-model right arm made continuous, Mock HAL + Synthetic I/Q, Artefact 3 = regression harness, triggers (code/prompt/model/context), SIL rungs (unit/integration/system), acceptance gap → HIL, Figures 4–6, Table 1 coupling, references [1]–[17] |
| `methodology/PCG/00_ProductionPipelinePCG/00_ProductionPipelinePCG.md` | Layer 3 — Post-Development Operations | 5 circular stages (Sandbox→Engine→KB→Playbook→Guardrails), Production Promotion & Rollback Gate, Capability Classes, GUM uncertainty propagation, Regulatory Decision Authority, feedback loops (4 mechanisms), audit-ready evidence archiving |

---

## Document structure (9 sections)

### 1. Introduction (~1 page)
- Context: SDR FM spectrum sensing for broadcast compliance monitoring, LLM-assisted systems engineering
- Problem: continuous verification of probabilistic systems — model/prompt/context drift invalidates evidence
- Thesis: V-SIL integrates conceptual validation (zz_Workflow) + continuous software development (CI+SIL) + post-deployment operations (PCG) into a single governed lifecycle
- Briefly name the three layers, defer detail to Sections 3–5

### 2. V-SIL Overview (~2 pages)
- **Figure 1: TikZ V-diagram** (see TikZ plan below)
- **Summary table**: Layer | Name | Source doc | Purpose | Terminal output
  - Layer 1 | Conceptual Validation | zz_Workflow | Define and validate what to build | Verified Prototype + Evidence
  - Layer 2 | Software Development | CI+SIL | Implement and continuously verify | Regression-passing build
  - Layer 3 | Post-Development Ops | PCG | Govern deployed system | Audit-ready evidence archive
- **Governing principles** (4 items):
  1. HITL = authorization barrier; HIL = validation barrier
  2. Oracle ≠ generator — the model never approves its own work
  3. Mechanical rejection beats LLM approval
  4. "Verified" ≠ "validated" — claims name the environment in which evidence was produced

### 3. Layer 1: Conceptual Validation Engine (~2.5 pages)
- Source: `zz_Workflow_.md` exclusively
- **Ctx 00** — Project Definition: purpose, users, system boundary, scope, authoritative sources → Problem Baseline + Frozen Project Scope
- **Ctx 01** — Requirements and Constraints: functional/non-functional reqs, regulatory constraints, HackRF boundaries, acceptance criteria, traceability → Versioned Requirements Baseline
- **Gate H** (Ctx 01→02): "Requirements complete, bounded, and verifiable?"
- **Ctx 02** — Architecture and Design Resolution: candidate architectures, pathways, HW/SW partitioning, trade studies → Selected Architecture + Implementation Plan
- **Gate H** (Ctx 02→03): "All implementation-critical design choices resolved?"
- **Ctx 03** — Executable Implementation Contract: component contracts, SDR config, DSP/classification algorithms, interfaces, schemas, error behavior, tests → Build Package
- **R0–R3 defect routing**: classified defects return to responsible stage; R0 requires change control
- **Table: 6 Governing Artifacts** with columns: # | Name | Where it applies | SDR instantiation
  1. System & Prompt Architecture Map
  2. Context & Retrieval Specs
  3. Eval & Benchmarking Suites (Artefact 3)
  4. Safety & Guardrail Design Rules
  5. AI Feedback & Telemetry Specs
  6. Data Privacy, Governance & Compliance Specs
- **LLM role**: drafts within a stage, never approves; acceptance by pre-declared criteria on recorded measurements
- **Key distinction**: this layer validates the *concept and design*, not the software

### 4. Layer 2: Software Development (CI+SIL) (~2.5 pages)
- Source: `1_CI-SIL_+_zz.md` (Sections 8–9 primarily)
- **V-model right arm made continuous**: same 4 test levels, different cadence
- **SIL rungs**:
  - Unit (pure logic) → every commit
  - Integration (SIL) → every merge
  - System (extended SIL) → nightly
- **Acceptance** stays at HIL + real HW (the downstream gap)
- **Mock HAL + Synthetic I/Q architecture**: HAL abstracts device, Mock HAL provides stubs, synthetic golden I/Q feeds mock; swap to real HW is transparent
- **Artefact 3 as regression harness**: the eval suites from zz_Workflow already *are* the CI harness — coupling requires no new concept
- **Triggers**: code change, prompt change, model change, context change — not just commits
- **Deterministic acceptance gate**: criteria from Ctx 01; R0–R3 routing reused for CI failures
- **Telemetry** (Artefact 5): records failure classes, points to responsible Ctx
- **Table 3** from source: V-model vs CI+SIL on 6 dimensions

### 5. Layer 3: Post-Development Operations (PCG) (~3 pages)
- Source: `00_ProductionPipelinePCG.md`
- **5 circular stages** (each with purpose, inputs, outputs):
  1. Sandbox — DSP dev & calibration; receives Stage 5 feedback
  2. Engine — array orchestration, multi-node coordination, capability-eligibility gating
  3. Knowledge Base — regulatory context, spectral data, knowledge graphs
  4. Playbook — measurement templates, calibration profiles, A/B testing, policy enforcement
  5. Guardrails — metrological QA, drift detection, HITL review, alerting → feeds back to Stage 1
- **Production Promotion & Rollback Gate**: versioned promotion record (5 prerequisites), rollback on threshold exceedance
- **Capability-class lifecycle**: Unsupported → Screening → Conditional Compliance → Compliance-Grade; each adds validation obligation
- **GUM uncertainty propagation**: per-stage contributions (Type A / Type B classification, combined/expanded uncertainty)
- **Regulatory Decision Authority**: dependency contract — Stage 3 before Stage 2 formal decisions
- **4 feedback mechanisms**: calibration drift, cross-node inconsistency, detection rule degradation, resource optimization
- **Audit-ready evidence archiving**: append-only, authenticated, cryptographic digest, replay validation

### 6. Inter-Layer Integration (~1.5 pages)
- **Layer 1 → Layer 2**: Ctx 03 Build Package becomes executable specification for CI+SIL; Artefact 3 (eval suites) seeds CI regression baseline
- **Layer 2 → Layer 3**: Production Promotion & Rollback Gate (versioned contract: Stage 1 validation package, Stage 3 regulatory baseline, Stage 4 measurement template, Stage 5 metrological-validity, human approval)
- **Mapping table**: which zz_Workflow artifact feeds which PCG stage
  - Artefact 1 (Prompt Architecture) → Stage 2 orchestration logic
  - Artefact 2 (Context & Retrieval) → Stage 3 knowledge base
  - Artefact 3 (Eval Suites) → Stage 1 sandbox validation + Stage 5 acceptance metrics
  - Artefact 4 (Safety & Guardrails) → Stage 5 guardrails
  - Artefact 5 (Telemetry) → Stage 5 observability
  - Artefact 6 (Privacy & Compliance) → All stages (data governance)
- **Extended defect routing**: R0–R3 in conceptual validation vs. Stage 5 → Stage 1 in operations

### 7. HITL and HIL Governance (~1 page)
- **HITL = authorization barrier**: gates H in zz_Workflow, approval in Promotion Gate, HITL review in Stage 5 anomalous classifications
- **HIL = validation barrier**: acceptance tests with real HW, the apex of the V
- **LLM governance rules**:
  - Model never approves its own work (all gates are human-decided)
  - Mechanical rejection beats LLM approval, never the reverse
  - Acceptance by pre-declared criteria on recorded measurements, never by model judgment
  - Self-reported correctness is weak evidence (benchmarks reward hallucination)

### 8. Gaps and Maturity Assessment (~0.5 page)
- **Table**: Component | Status | Gap
  - HIL bench | Not implemented | No live-RF validation infrastructure
  - MCDA | Not implemented | Multi-hypothesis selection not formalized
  - Controlled Source Specification Baseline | Not instantiated | Stage 2 formal compliance disabled
  - Single-to-array scaling | Not covered | Pipeline assumes array but no scaling methodology
  - LLM governance in production | Not specified | Stage 2/5 LLM use constraints undefined

### 9. Conclusion (~0.5 page)
- V-SIL unifies three layers into a governed lifecycle for LLM-assisted SDR development
- Each layer has a distinct role: define (Layer 1), implement (Layer 2), operate (Layer 3)
- The coupling is clean because each layer's terminal output is the next layer's input
- Honest claims: "verified" at SIL, "validated" only at HIL/field
- Five gaps are explicit and tractable

### References
- Carry forward citations [1]–[17] from `1_CI-SIL_+_zz.md`
- Use `biblatex` with inline `\addbibresource` or `thebibliography`

---

## TikZ V-diagram plan (Figure 1)

```
Layout (conceptual):

        [Ctx 00 — Problem Baseline]          ← coral #f87171, above left arm
                    |
    LEFT ARM (blue #3b82f6)               RIGHT ARM (teal #14b8a6)
    ────────────────────                  ────────────────────────
    L1: System Requirements  ─ ─ ─ ─ ─ ─  L1: Acceptance Tests (red #ef4444, HIL+HW)
         ↓  ◇H                                   ↑
    L2: System Design  ─ ─ ─ ─ ─ ─ ─ ─ ─  L2: System Tests (SIL·nightly)
         ↓                                       ↑
    L3: Architecture Design  ─ ─ ─ ─ ─ ─  L3: Integration Tests (SIL·merge)
         ↓  ◇H                                   ↑
    L4: Module Design  ─ ─ ─ ─ ─ ─ ─ ─ ─  L4: Unit Tests (SIL·commit)
         ↓                                       ↑
         └──── VALLEY: Coding/Impl ──────────────┘
                       (grey #6b7280)
                           |
              [Mock HAL + Synthetic I/Q]     ← amber #f59e0b

    ═══════════════════════════════════════════════
    PCG LAYER (violet #8b5cf6) — below the V
    ┌──────────────────────────────────────────────┐
    │  S1:Sandbox → S2:Engine → S3:KB →            │
    │  S4:Playbook → S5:Guardrails ─→ (loop to S1) │
    └──────────────────────────────────────────────┘
```

### TikZ implementation notes

- Use `\usetikzlibrary{positioning, shapes.geometric, arrows.meta, calc, fit, backgrounds}`
- Coordinate system: place valley at origin (0,0); left arm descends from upper-left, right arm ascends to upper-right
- Left-arm nodes: `xshift=-5cm`, y-levels at 6, 4.5, 3, 1.5
- Right-arm nodes: `xshift=+5cm`, same y-levels
- Ctx 00: centered above left arm at y=7.5
- Gates H: diamond nodes (`diamond` shape) in coral, placed on left-arm edges between L1→L2 and L3→L4
- Valley node: rounded rectangle at (0, 0)
- Mock HAL: rounded rectangle at (0, -1.5) in amber
- Dashed horizontal lines: `[dashed, gray]` connecting each left level to its right mirror, labeled "defines"
- Right arm labels: append "SIL · commit/merge/nightly" in smaller font; L1 gets "HIL + real HW" in red
- PCG band: `\node[draw, fill=violet!10, rounded corners, minimum width=12cm]` at (0, -4)
  - 5 stage labels inside with `→` arrows, return arrow from S5 to S1
- Legend: 6 colored squares with labels, positioned bottom-right or below PCG

### Color definitions (preamble)
```latex
\definecolor{coral}{HTML}{f87171}
\definecolor{vblue}{HTML}{3b82f6}
\definecolor{vteal}{HTML}{14b8a6}
\definecolor{vred}{HTML}{ef4444}
\definecolor{amber}{HTML}{f59e0b}
\definecolor{violet}{HTML}{8b5cf6}
\definecolor{vgrey}{HTML}{6b7280}
```

---

## LaTeX preamble plan

```latex
\documentclass[11pt,a4paper]{article}
\usepackage[margin=2.5cm]{geometry}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage{amsmath}
\usepackage{booktabs}
\usepackage{enumitem}
\usepackage{xcolor}
\usepackage{tikz}
\usepackage{hyperref}
\usepackage[noabbrev,capitalise]{cleveref}
\usepackage[backend=biber,style=numeric-comp,sorting=none]{biblatex}
```

- Self-contained: no `\input` or `\include`
- `thebibliography` environment (no external `.bib` file) for portability
- Language: English (American spelling, consistent throughout)
- Author: David Ramírez-Betancourt, Universidad Nacional de Colombia — GCPDS

---

## Inviolable rules checklist

| Rule | Compliance strategy |
|---|---|
| R1: zz_Workflow nomenclature | Use Ctx 00–03, gates H, R0–R3, Artefacts 1–6, "Verified Prototype + Evidence" verbatim |
| R2: methodology name = V-SIL | Never "V-model" or "CI+SIL" alone as the full methodology name |
| R3: Layer 1 ≠ software dev | Explicit in Section 3 conclusion and throughout |
| R4: HITL + HIL + LLM governance | Dedicated Section 7; reinforced in every layer section |
| R5: verified ≠ validated | Define in Section 2 principles; use precisely throughout |
| R6: V-shape diagram | TikZ plan preserves descending left arm + ascending right arm |
| R7: PCG = post-development | Section 5 title and framing; never conflated with dev phase |
| R8: pdflatex-clean | Standard packages only; test compilation |
| R9: Author | Title page with David Ramírez-Betancourt, UNAL — GCPDS |
| R10: Self-contained | No \input/\include; thebibliography inline |
| R11: Output path | `methodology/V-SIL/V-SIL.tex`; no changes under `methodology/1_CI-SIL_+_zz/` |
| R12: English | American spelling throughout; proofread before finalizing |

---

## Estimated length

~18–22 pages (including figure, tables, references).

---

## Execution sequence

1. Write full `V-SIL.tex` in a single pass (self-contained)
2. Compile with `pdflatex` (+ `biber` if biblatex, else just pdflatex)
3. Fix any compilation errors
4. Visual check of TikZ diagram
5. Proofread for R1–R12 compliance



# Confirm compile:
- Use skill latex-compile to test pdf generation and clean auxiliar files
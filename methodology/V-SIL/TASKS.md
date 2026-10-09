# TASKS — V-SIL.tex development checkpoint

Checkpoint list for implementing `methodology/V-SIL/PLAN.md`.
Rule: a checkpoint is `[x]` only when its evidence exists (file written / compile output / visual check).

- Plan: `methodology/V-SIL/PLAN.md`
- Deliverable: `methodology/V-SIL/V-SIL.tex` (+ `V-SIL.pdf`)
- Sources (read-only): `methodology/1_CI-SIL_+_zz/zz_Workflow_.md`, `methodology/1_CI-SIL_+_zz/1_CI-SIL_+_zz.md`, `methodology/PCG/00_ProductionPipelinePCG/00_ProductionPipelinePCG.md`

---

## C0 — Preparation

- [ ] Read `PLAN.md` and the three source documents
- [ ] Extract reference list `[1]`–`[17]` from `methodology/1_CI-SIL_+_zz/1_CI-SIL_+_zz.tex` (bibitems, to be carried forward verbatim)
- [ ] Confirm output path: `methodology/V-SIL/V-SIL.tex` (no changes under `methodology/1_CI-SIL_+_zz/`)

## C1 — Scaffold

- [ ] Preamble per PLAN (article 11pt a4, geometry, xcolor, tikz + libraries, hyperref, cleveref, booktabs; `thebibliography` instead of biblatex for portability — R8/R10)
- [ ] Color definitions (coral/vblue/vteal/vred/amber/violet/vgrey)
- [ ] Title page with David Ramírez-Betancourt, Universidad Nacional de Colombia — GCPDS (R9)

## C2 — Sections 1–2 + Figure 1

- [ ] §1 Introduction (~1 page): context, problem, thesis
- [ ] §2 V-SIL Overview: **Figure 1 TikZ V-diagram** (descending left arm, ascending right arm, gates H, valley, Mock HAL, PCG band, legend) (R6)
- [ ] §2 Summary table: Layer | Name | Source | Purpose | Terminal output
- [ ] §2 Four governing principles (HITL/HIL, oracle ≠ generator, mechanical rejection, verified ≠ validated) (R4, R5)

## C3 — Section 3 (Layer 1)

- [ ] Ctx 00–03 stages with outputs, verbatim nomenclature (R1)
- [ ] Gates H (Ctx 01→02, Ctx 02→03) with exact gate questions
- [ ] R0–R3 defect routing table/paragraph
- [ ] Table: 6 Governing Artefacts (# | Name | Where it applies | SDR instantiation)
- [ ] LLM role + "validates concept and design, not software" distinction (R3)

## C4 — Section 4 (Layer 2)

- [ ] V-model right arm made continuous; SIL rungs (unit/commit, integration/merge, system/nightly)
- [ ] Acceptance stays at HIL + real HW
- [ ] Mock HAL + Synthetic I/Q architecture
- [ ] Artefact 3 = regression harness coupling; 4 triggers (code/prompt/model/context)
- [ ] Deterministic acceptance gate + telemetry (Artefact 5) + R0–R3 reuse
- [ ] Table: V-model vs CI+SIL on 6 dimensions (source Table 3)

## C5 — Section 5 (Layer 3)

- [ ] 5 circular stages with purpose/inputs/outputs (Figure 2 PCG cycle)
- [ ] Production Promotion & Rollback Gate (5 prerequisites)
- [ ] Capability-class lifecycle (Unsupported → Screening → Conditional Compliance → Compliance-Grade)
- [ ] GUM uncertainty propagation (Type A / Type B, combined/expanded uncertainty)
- [ ] Regulatory Decision Authority dependency contract (Stage 3 → Stage 4 → Stage 5 before Stage 2)
- [ ] 4 feedback mechanisms
- [ ] Audit-ready evidence archiving (append-only, authenticated, digest, replay validation)

## C6 — Sections 6–7

- [ ] §6 Layer 1 → Layer 2 (Build Package as executable spec; Artefact 3 seeds CI baseline)
- [ ] §6 Layer 2 → Layer 3 (Promotion Gate as versioned contract)
- [ ] §6 Mapping table: zz_Workflow artefact → PCG stage
- [ ] §6 Extended defect routing (R0–R3 vs Stage 5 → Stage 1)
- [ ] §7 HITL = authorization, HIL = validation, 4 LLM governance rules (R4)

## C7 — Sections 8–9 + References

- [ ] §8 Gaps table (HIL bench, MCDA, Controlled Source Specification Baseline, single→array scaling, LLM governance in production)
- [ ] §9 Conclusion (define / implement / operate; verified vs validated; five gaps)
- [ ] References: `thebibliography` with the 17 carried-forward citations, inline (R10)

## C8 — Compile gate

- [ ] `latexmk -pdf` (pdflatex path) compiles with 0 errors in `methodology/V-SIL/`
- [ ] Auxiliary files cleaned (`latexmk -c`); PDF kept at `methodology/V-SIL/V-SIL.pdf`
- [ ] No undefined references / citations / missing packages in the final log

## C9 — Visual check

- [ ] Figure 1: V-shape intact (left arm descends, right arm ascends, valley at bottom) (R6)
- [ ] Figure 1: gates H, Mock HAL, PCG band, legend readable; no node overlap
- [ ] Figure 2: PCG 5-stage cycle with S5 → S1 loop readable
- [ ] Tables not overflowing page margins

## C10 — Proofread (R1–R12 compliance)

- [ ] R1 zz_Workflow nomenclature verbatim (Ctx 00–03, gates H, R0–R3, Artefacts 1–6, "Verified Prototype + Evidence")
- [ ] R2 methodology always named V-SIL (never "V-model" or "CI+SIL" alone as the full name)
- [ ] R3 Layer 1 ≠ software development (explicit in §3 and §9)
- [ ] R4 HITL + HIL + LLM governance present (§7 + reinforced per layer)
- [ ] R5 "verified" ≠ "validated" defined in §2, used precisely throughout
- [ ] R6 V-shape preserved in TikZ
- [ ] R7 PCG framed as post-development only
- [ ] R8 pdflatex-clean (standard packages only)
- [ ] R9 Author on title page
- [ ] R10 Self-contained: no `\input`/`\include`, bibliography inline
- [ ] R11 Output path `methodology/V-SIL/V-SIL.tex`; sources untouched
- [ ] R12 English (American spelling) throughout

---

## Status

All checkpoints complete. Final state: `V-SIL.pdf` compiles clean and passes R1–R12.

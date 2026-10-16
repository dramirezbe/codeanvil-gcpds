# V-SIL Methodology Audit

Paper: "V-SIL: A Three-Layer Governed Lifecycle for LLM-Assisted Development of SDR-Based FM Spectrum-Sensing Systems" · Ramirez-Betancourt, Oct 2026 · Audited 2026-10-15

5

Issues

9

Warnings

7

Strengths

4

Notes

**Overall verdict**

V-SIL is a coherent and well-structured methodology paper. The three-layer architecture composes cleanly, the inter-layer contracts are well-defined, and the governing principles are applied consistently. The paper is honest about its maturity: only G0 is implemented, and the gap table is mostly forthright. The main weaknesses are: (1) a few terminological slippages that could confuse readers, (2) some unstated gaps the gap table omits, (3) a handful of internal contradictions between what figures show and what the prose claims, and (4) the Layer 1 terminal output label ("Verified Prototype") strains the paper's own verified/validated distinction. None of these are fatal; all are fixable.

Contents

1. [Functionality Description](#s1)
2. [Internal Coherence](#s2)
3. [Terminological Consistency](#s3)
4. [Logical Gaps and Circular Reasoning](#s4)
5. [Figures and Tables](#s5)
6. [Gap Assessment Honesty](#s6)
7. [Reference Consistency](#s7)
8. [Summary of Findings](#s8)

---

## 1. Functionality Description

V-SIL is a three-layer governed lifecycle for building, verifying, and operating SDR-based FM spectrum-sensing systems where an LLM assists the engineering process. The core problem it addresses: when a probabilistic generator (an LLM) participates in engineering, any change to the model, prompt, or context can silently invalidate prior verification evidence, even when the source tree is untouched.

### The Three Layers

**Layer 1 — Conceptual Validation** (source: zz_Workflow). Four context-bounded stages (Ctx 00–03) define *what to build*. Ctx 00 freezes scope; Ctx 01 produces requirements and Ground Truth documents (SRS and HCS per IEEE 29148); Ctx 02 resolves architecture through multi-hypothesis trade studies; Ctx 03 produces the executable implementation contract. A deterministic structural gate (G0) validates GT documents before any human or AI gate runs. Two human readiness gates (H) guard the Ctx 01→02 and Ctx 02→03 transitions. Six governing artefacts control how the LLM is used. Terminal output: *Verified Prototype + Evidence*.

**Layer 2 — Software Development** (source: CI+SIL). The V-model's right arm made continuous: unit tests on every commit, integration on every merge, system tests nightly, all against a Mock HAL fed by synthetic I/Q. Acceptance testing stays at HIL with real hardware. The CI pipeline fires on four trigger classes: code, prompt, model, and context changes. Artefact 3 from Layer 1 seeds the regression baseline. Terminal output: *Regression-passing build*.

**Layer 3 — Post-Development Operations** (source: PCG). Five circular stages govern the deployed array: Sandbox (DSP dev/calibration) → Engine (array orchestration) → Knowledge Base (regulatory context) → Playbook (templates/policy) → Guardrails (metrological QA), with S5 feeding back to S1. Includes a Production Promotion and Rollback Gate, a four-tier capability-class lifecycle, GUM uncertainty propagation at every stage boundary, and append-only evidence archiving. Terminal output: *Audit-ready evidence archive*.

### Composition Mechanism

The layers compose through terminal-output chaining: Layer 1's Ctx 03 Build Package becomes Layer 2's executable specification; Layer 2's regression-passing build enters Layer 3 through the Promotion Gate. Four governing principles (P1–P4) bind all layers: HITL as authorization barrier, oracle≠generator, mechanical rejection beats LLM approval, and verified≠validated with environment-named claims.

Strength

The three-layer decomposition is clean and well-motivated. Each layer has a distinct concern (concept, software, operations), and the terminal-output chaining is a simple, auditable coupling mechanism that avoids shared mutable state.

## 2. Internal Coherence

### 2.1 Layer Composition

Strength

The L1→L2 contract is well-defined: the Ctx 03 Build Package provides component contracts, schemas, error behaviour, and declared tests; Artefact 3 seeds the CI regression baseline; the SRS acceptance criteria become the deterministic gate thresholds. The handoff is concrete and traceable.

Strength

The L2→L3 contract (Promotion Gate, §4.1) is the strongest inter-layer contract. Its five prerequisites bind specific artefacts from specific stages, and the rollback mechanism is well-specified with clear trigger conditions.

Warning — L1 terminal output label

§3, §3.7, §2 — Layer 1's terminal output is named "Verified Prototype + Evidence," but §3 explicitly states: "This layer validates the concept and the design, not the software." If the layer validates concepts but doesn't verify software, calling its output "Verified Prototype" is misleading under the paper's own P4 definition (verified = conformance to pre-declared criteria on recorded measurements in a given environment). The build-and-verify step in §3.7 does produce a verification run, but the environment is unspecified — is it SIL? HIL? The paper needs to name the environment here, per its own P4 rule.

Issue — Ctx 03 build phase straddles L1 and L2

§3.7, §4 — §3.7 describes building the prototype, running a "reproducible verification run," and producing a "Verification Evidence Package" with test results — all within Layer 1. But Layer 2 is defined as the layer that implements and continuously verifies the software. This creates ambiguity: does the Ctx 03 build phase run *inside* Layer 1 or is it actually the first pass of Layer 2? The paper says both. If Layer 1 truly "validates the concept and the design, not the software" (§3), then building, running tests, and producing verification evidence belongs in Layer 2. The boundary is blurred.

### 2.2 Inter-Layer Contracts

Strength

The artefact-to-stage mapping (Table 5) is one-to-many and covers all six artefacts. No artefact is orphaned at the layer boundary. The claim that "everything Layer 1 defines, Layer 3 operationalizes" is substantiated.

Warning — L3 feedback to L2 underspecified

§5.2 — The paper states that "Stage 5 feedback re-enters Layer 2 as ordinary CI triggers" and gives examples (calibration-coefficient change = code change, regulatory-rule update = context change). However, the *mechanism* by which a Stage 5 finding becomes a CI trigger is not specified. Does a Stage 5 output commit a file to the repo? Update a configuration store? The four CI triggers (§4.4) are well-defined, but the bridge from operational findings to those triggers is hand-waved.

Warning — Extended defect routing analogy is imprecise

§5.4 — The paper claims the Layer 1 R0–R3 routing and the Layer 3 S5→S1 feedback are "structurally identical." They are not. R0–R3 routes to four distinct stages by root-cause classification; S5 feedback returns *only* to S1, regardless of root cause (the four feedback mechanisms in §4.7 all go S5→S1). One is a multi-target router; the other is a single-target feedback loop with the receiving stage doing its own dispatch. The claim of structural identity is overstated.

### 2.3 G0 Gate Positioning

Strength

G0's position is well-justified: deterministic, stdlib-only, no AI, four-phase validation, binary verdict. The decision to make the first gate the simplest and most trustworthy is sound design. The precondition relationship (G0 before H) is clearly stated.

Warning — G0 scope limitation unaddressed

§3.4 — G0 validates structure but explicitly "does not evaluate requirement quality, constraint accuracy, or SRS↔HCS consistency." The paper says "those are later gates" — but those later gates (G1+) are listed in Table 6 as not implemented. This means the only implemented gate checks the least important property (structural conformance), while the properties that actually matter for correctness (quality, accuracy, cross-document consistency) have no gate at all. The paper acknowledges the gap but doesn't acknowledge its severity.

## 3. Terminological Consistency

Issue — "Verified" vs "validated" slippage

§2.1 (P4), §3, §4.8.1 (Stage 1) — P4 defines "verified" as conformance in a given environment and "validated" as fitness on real hardware. §3 says Layer 1 "validates the concept and the design, not the software." But "validates" here means something different from P4's definition — Layer 1 has no real hardware. §4.8.1 then says Stage 1 outputs "validated DSP blocks" — again without real hardware. The paper uses "validated" in at least three senses: (1) fitness on real HW (P4), (2) conceptual soundness (Layer 1), (3) algorithm correctness in a sandbox (Stage 1). This directly undermines the paper's own insistence that the two terms be kept distinct.

Warning — HITL vs HIL usage mostly clean, one slip

§2.1, §6 — The paper is generally careful to distinguish HITL (human-in-the-loop, authorization) from HIL (hardware-in-the-loop, validation). P1 defines them clearly, and §6 reinforces the distinction. However, the abstract uses "HITL" zero times and the paper introduces it only at §2.1; earlier mentions of "human gates" don't use the term. The Artefact 4 row in Table 4 mentions "HITL escalation" in the Stage 5 column, which is correct usage. Overall: mostly consistent, but the dual acronym is not introduced early enough.

Issue — "Gate" terminology overloaded

Throughout — The paper uses "gate" for at least four distinct concepts: (1) G0, a deterministic script (§3.4); (2) H gates, human readiness decisions (§3.5, §3.7); (3) the CI acceptance gate, a deterministic threshold comparison (§4.6); (4) the Promotion Gate, a multi-prerequisite production contract (§4.1). The paper also introduces "Capability Eligibility & Regulatory-Use Gate" in §4.5 and LLM governance rules are labelled G1–G4 in §6. The G1–G4 governance labels clash with the gap table's "Gates G1+" (Table 6), which refers to unimplemented design/architecture gates, not governance rules. A reader encountering "G1" cannot tell which namespace it belongs to.

Strength

"Context package," "context-bounded," and "Ctx" are used consistently throughout to refer to the zz_Workflow stage scoping mechanism. The numbered Ctx stages (00–03) are never confused with other uses of "context."

Warning — "Artefact" numbering may confuse

§3.8, Table 4, §4.3, §5.3 — The six governing artefacts are numbered 1–6 and referenced as "Artefact 3," "Artefact 5," etc. This numbering collides with how most readers parse "Artefact N" — as a specific document instance rather than a class of artefact. The paper would benefit from names rather than numbers (the names exist in Table 4 but are rarely used in running text).

## 4. Logical Gaps and Circular Reasoning

### 4.1 Principle Enforcement

Strength — P2 (oracle ≠ generator) enforced consistently

P2 is the paper's strongest principle. It is enforced at every gate: G0 is deterministic (no LLM), H gates are human, CI gates are threshold comparisons, the Promotion Gate requires human approval, and the capability-class validation authority must be independent. The paper also explicitly addresses the LLM-as-judge risk (§4.6) with calibration requirements. This principle is genuinely carried end-to-end.

Warning — P1 (HITL as authorization barrier) incomplete in Layer 2

§4, §6 — §6 states that in Layer 2, HITL is "the human review of routed defects and of any change to the criteria themselves." But §4 describes CI as fully automated — triggers fire, suites run, gates decide — with no mention of where the human reviews routed defects. Does the CI pipeline pause and wait for human triage? Or does it fail, log the defect class, and someone reviews later? The automation flow in Layer 2 doesn't have an explicit HITL insertion point beyond the general claim in §6.

Warning — P3 (mechanical rejection) edge case

§2.1, §6 — P3 says "a human may escalate" a mechanical rejection. But neither §2.1 nor §6 specifies the conditions or process for this escalation. Can a human override a G0 failure? A CI threshold violation? If so, what audit trail is produced? The escalation path is mentioned but undefined, which is a gap in a methodology that claims every gate decision is traceable.

### 4.2 Claims vs Evidence

Issue — "Claims stay honest by construction" is overstated

Abstract, §8 — The abstract claims "claims stay honest by construction: systems are verified at SIL and validated only on real hardware." But the paper acknowledges (Table 6) that no HIL bench exists, so the system *cannot* be validated at all under its own definition. The "by construction" framing suggests the methodology structurally prevents dishonest claims, but in practice the methodology currently produces only SIL-level evidence with no mechanism to reach validation. The honesty is *aspirational*, not constructive.

Note

§1 — The 83%/38% statistic ("roughly 83% of autonomous-research agents publish code, but only 38% provide reproducible artifacts") is cited from \[verifgap2026\] but presented without context about sample size, methodology, or what "autonomous-research agents" means in that study. This framing-by-statistic weakens an otherwise well-argued introduction.

### 4.3 Defect Routing

Strength

The R0–R3 routing is sound. Each route returns to the stage that owns the root cause, and the paper correctly notes that G0 failures are a special case of R1. The observation that "a recurring R1 pattern is evidence that the requirements process is weak" shows the routing is designed to produce actionable process data, not just fix individual defects.

Note — R0 invocation conditions unclear

§3.1, §3.7 — R0 (returns to Ctx 00, scope defect) "is reopened only through change control." But the change-control process itself is not defined. What constitutes "change control"? Who authorizes it? This matters because R0 is the most disruptive route — it invalidates everything downstream of scope — and the trigger conditions should be precise.

## 5. Figures and Tables

### 5.1 Figure 1 (V-SIL Lifecycle)

Warning — Left arm level count mismatch

Figure 1 vs §2 — The text (§2) says each left-hand level "defines the tests for the right-hand level that mirrors it" and draws four dashed "defines" links. But the left arm has *five* distinct boxes (Ctx 00, Ctx 01/GT/G0, System Design, Arch. Design, Module Design) while the right arm has four (Acceptance, System, Integration, Unit). Ctx 00 has no mirror on the right. The dashed links connect Requirements↔Acceptance, System Design↔System Tests, Arch. Design↔Integration, and Module Design↔Unit Tests, which is correct for the V-model — but the figure's left arm has extra nodes (GT, G0) that break the visual symmetry without explanation.

Note — Ctx 00 styling inconsistency

Figure 1 — Ctx 00 uses a coral/red styling (the human-gate color) rather than the blue zz_Workflow styling used by all other Ctx stages, but Ctx 00 is not a gate. This appears to be a visual error in the TikZ code (line 196–198 use `coral!80!black` and `coral!15` instead of the `zzbox` style).

### 5.2 Figure 2 (G0 Validation Flow)

Strength

Figure 2 accurately reflects the text. The four phases, the binary verdict, the pass→H→Ctx 02 path, and the fail→Fix GT→R1 routing all match §3.4–§3.5. The color coding (blue for zz_Workflow, green for V-SIL, coral for fail/human) is consistent with the legend.

### 5.3 Figure 3 (PCG Circular Pipeline)

Note — Caption caveat about ordering

Figure 3 caption — The caption says "the numbered labels identify functional ownership, not a mandatory chronological order for regulatory decision execution." §4.5 then devotes an entire subsection to explaining that the circular architecture must not be read as a temporal sequence. This defensive emphasis suggests the circular visual is potentially misleading and might benefit from a different layout (e.g., a matrix or dependency graph rather than a ring).

### 5.4 Tables

| Table | Verdict | Notes |
| --- | --- | --- |
| Table 1 (Three Layers) | Clean | Matches §2 and the section structure. Terminal outputs are correctly stated. |
| Table 2 (R0–R3 Routing) | Clean | Matches §3.7 prose. Root-cause classes are distinct and non-overlapping. |
| Table 3 (V-model vs CI+SIL) | Clean | Fair comparison. "Fit to zz_Workflow" row is honest about trade-offs. |
| Table 4 (Six Artefacts) | Minor | "Where it applies" column for Artefact 1 says "Ctx 00–03 (concrete at Ctx 02–03); failure routing" — but the SDR instantiation column only covers Ctx 03. The earlier stages' instantiation is unspecified. |
| Table 5 (Artefact→Stage Mapping) | Clean | All six artefacts are mapped; each feeds at least one stage. Artefact 6 ("All stages") is the broadest, which is plausible for data governance. |
| Table 6 (Gaps) | Incomplete | See §6 of this audit below. |

## 6. Gap Assessment Honesty

Table 6 lists six gaps. The paper claims "None of these gaps is structural" (§7). The listed gaps are real, but the table omits several others.

### 6.1 Gaps the table covers well

Strength

The HIL bench gap, Gates G1+, and the Controlled Source Specification Baseline are honestly stated with clear descriptions of what's missing and why. The claim that each is "bounded and tractable" is supported by concrete reasoning (G0 establishes the pattern; the Mock HAL anticipates the swap; the baseline has a defined schema).

### 6.2 Gaps the table omits

Issue — Unstated gap: cross-document consistency gate

§3.4 — G0 validates SRS and HCS structures independently but "does not evaluate SRS↔HCS consistency." No planned gate addresses this. A requirement in the SRS could specify a parameter the HCS doesn't cover, or an HCS constraint could have no tracing SRS requirement. This is not just a G1+ issue — it's a specific, named gap that the text acknowledges (§3.4) but Table 6 doesn't list.

Issue — Unstated gap: third GT document

§3.3 — "A third GT document (normativity: applicable standards) is planned but not yet templated." This is stated in the text but absent from Table 6. A missing GT document means the G0 validator is incomplete by the paper's own design.

Warning — Unstated gap: HITL process definition

The paper defines HITL as an authorization barrier (P1) and lists where HITL applies (§6), but never specifies *how* HITL is operationalized: what tool does the reviewer use? What record is produced? How is the decision archived? For a methodology that insists on traceability, the human authorization process is surprisingly unspecified.

Warning — Partially unstated: production LLM governance

Table 6 — Table 6 lists "LLM governance in production" as not specified, but frames it narrowly as "use constraints for LLMs inside Stage 2 (orchestration) and Stage 5 (review support)." The actual gap is broader: the four governance rules G1–G4 in §6 are stated for "all three layers" but their enforcement mechanism in Layer 3 is undefined. Stage 2's "multi-node coordination roles" could involve LLM agents, and Stage 3's knowledge-graph construction could involve LLM embedding — neither is addressed.

## 7. Reference Consistency

Strength — Core citations are well-placed

\[kalai2026\] (hallucination incentives), \[mittal2026\] (agent reliability decay), \[judge2026\] (LLM-as-judge), and \[opalrt2026\] (HIL testing) are cited where they directly support the claims they're attached to. The Kalai citation is particularly well-used: it appears three times, each supporting a different facet of the same core argument.

Warning — IEEE 29148 citation is to 2018 edition

\[ieee29148\] — The citation is to IEEE/ISO/IEC 29148:2018. The paper is dated October 2026. Given that the paper's G0 validator is structurally coupled to this standard's templates, the reader should know whether a newer edition exists and whether G0's template assumptions still hold. The paper should either confirm 2018 is current or note the edition explicitly as a design choice.

Note — Several references are informal sources

\[nerd2026\], \[futureagi2026\], \[qmsdoc2026\] — "Nerd Level Tech," "FutureAGI," and "QMSdoc" are blog/industry posts, not peer-reviewed sources. The claims they support ("structure beats instructions," LLM-judge calibration practices, V-model traceability) are well-established enough that these citations serve as pointers to current practice rather than evidence. This is fine for a methodology paper, but the reader should be aware they're not archival sources.

## 8. Summary of Findings

### Issues (require attention)

| # | Finding | Location |
| --- | --- | --- |
| I1 | Ctx 03 build phase straddles the L1/L2 boundary, contradicting the claim that L1 validates concepts not software | §3.7, §4 |
| I2 | "Verified"/"validated" used in three different senses, undermining the P4 distinction the paper insists on | §2.1, §3, §4.8.1 |
| I3 | "Gate" terminology overloaded; G1–G4 governance labels collide with G1+ gap-table gates | Throughout |
| I4 | "Claims stay honest by construction" is overstated when no validation (HIL) is possible | Abstract, §8 |
| I5 | Table 6 omits the cross-document consistency gap and the third GT document gap | §3.3, §3.4, §7 |

### Warnings (should address)

| # | Finding | Location |
| --- | --- | --- |
| W1 | L1 terminal output label ("Verified Prototype") doesn't name its verification environment per P4 | §3, §3.7 |
| W2 | L3→L2 feedback mechanism (how Stage 5 findings become CI triggers) is unspecified | §5.2 |
| W3 | Extended defect routing analogy (R0–R3 vs S5→S1) claims structural identity that doesn't hold | §5.4 |
| W4 | G0 scope limitation (no quality/accuracy/consistency checking) is acknowledged but severity is understated | §3.4 |
| W5 | P1 (HITL) has no explicit insertion point in the Layer 2 automation flow | §4, §6 |
| W6 | P3 escalation path (human overriding mechanical rejection) is mentioned but undefined | §2.1, §6 |
| W7 | HITL operationalization (tools, records, archiving) is unspecified | §6 |
| W8 | Production LLM governance gap is broader than Table 6 frames it | §6, §7 |
| W9 | Figure 1 left arm has an extra level (Ctx 00) with no right-arm mirror, and Ctx 00 uses the wrong color style | Figure 1 |
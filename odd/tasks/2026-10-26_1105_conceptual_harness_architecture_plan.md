# Plan: Conceptual Design and Deployment of AI Agent Harnesses

## Objective

Author an authoritative, domain-agnostic conceptual architecture document in LaTeX titled:
**"Engineering AI Agent Harnesses: Conceptual Foundations, Architectural Paradigms, and Commercial Runtime Strategies"**

The document serves as a generalized engineering whitepaper explaining the **WHY** and the conceptual **HOW** of designing and deploying an **Agent Harness** for modern commercial coding agent cockpits (Claude Code, OpenCode, Codex, Pi, etc.). It abstracts away any specific product implementation or domain methodology (such as CodeAnvil or V-SIL), providing a universal framework for systems architects and developers building methodology wrappers over autonomous agents.

Target output location: `methodology/conceptual/conceptual_system_development_HARNESS.tex`.

---

## Document Specs & Universal Outline

### 1. The Spectrum of AI System Engineering
- **Taxonomy of Paradigms:**
  - **Prompt Engineering:** Interactive web chats, system prompts, manual copy-pasting, zero execution grounding or environment interaction.
  - **Context Engineering (RAG):** Dynamic retrieval over vector or lexical databases; enriches prompts with context, but remains passive and read-only.
  - **Agent Frameworks (LangGraph, CrewAI, AutoGen):**
    - Code-first graph orchestration requiring developers to build custom chat UIs, handle terminal/streaming plumbing, and manage execution loops.
    - Forced raw API token billing—completely unable to utilize end-user flat-rate commercial subscriptions (Claude Pro/Team, ChatGPT Plus/Team).
  - **Harness Engineering:** Wrapping turnkey commercial agent cockpits with deterministic operational guardrails, methodology gates, and audit mechanisms without rebuilding the agent interface or execution engine.
- **Architectural Trade-off Matrix:** Comparing developer velocity, infrastructure maintenance, operational cost, UI/UX readiness, cognitive burden, deterministic reliability, and lock-in across all four paradigms.

### 2. Frameworks vs. Harnesses: The Architectural Divide
- **The "Rebuilding the Cockpit" Anti-Pattern:** Why teams building agent applications fail by attempting to re-implement terminal multiplexers, streaming interfaces, context compaction algorithms, and tool dispatchers.
- **Commodity Intelligence vs. Methodology Wrapper:**
  - Commercial agent runtimes as swappable, commodity reasoning engines with pre-built chat, streaming, and tool execution.
  - The Harness as the structural supervisor: enforces workflow invariants, quality gates, lifecycle transitions, and environmental integrity.
- **Economic Inversion:** Leveraging flat-rate commercial user subscriptions vs. enterprise API token attrition.

### 3. The Universal Dual-World Architecture of an Agent Harness
- **The Authoring Plane (Harness Meta-Environment):**
  - The developer environment where methodology rules, gate specifications, deterministic validator scripts, and scaffold generators are defined and versioned.
  - Analogous to a software SDK or toolchain compiler.
- **The Instantiated Execution Plane (End-User Project Environment):**
  - The target workspace provisioned by the harness scaffold.
  - Completely self-contained: contains domain specifications, capabilities, and state tracking.
  - **Zero Daemon Requirement:** The project workspace itself acts as the passive harness; commercial agents attach directly without requiring a persistent host service.

### 4. Cross-Runtime Discovery & Agnostic Strategies
- **Universal Capability Packaging ([Agent Skills](https://agentskills.io/home)):**
  - Two-phase discovery protocol: lightweight metadata indexing vs. deep execution loading to conserve context economics.
  - Self-contained capability directories: colocation of operational instructions, deterministic scripts, and domain references.
- **The Runtime Projection Mesh:**
  - Projecting a single canonical capability store into multiple agent runtime discovery paths (via symlinks or adapter manifests) to achieve true vendor neutrality.
- **Standardized Tool Bridging (MCP):**
  - Declarative Model Context Protocol manifests for exposing domain-specific tools, hardware interfaces, or system packages to any compliant agent.

### 5. State, Control, and Verification Without Central Orchestrators
- **Decentralized, Report-Driven State Machines:**
  - The liabilities of central daemon orchestrators (process crashes, IPC overhead, state desynchronization).
  - The Filesystem as Universal IPC: Sequential gate progression enforced through immutable status reports (`PASS` vs. `FEEDBACK`), verified directly by skills upon invocation.
- **Deterministic Hard Gates vs. Probabilistic Reasoning:**
  - The boundary between what must be strictly deterministic (syntax linters, schema validators, rule checkers) and what is delegated to LLM synthesis.
  - Preventing hallucinated completion through non-zero exit codes.
- **Cryptographic Ground Truth Custody:**
  - Sealing baseline requirements and specifications using cryptographic digests (e.g., SHA-256 manifests).
  - Append-only, signed audit logs ensuring complete lineage and tamper-evidence across iterative agent runs.

### 6. Multi-Surface Ingress & Human-in-the-Loop (HITL)
- **Surface-Agnostic Presentation:**
  - Decoupling human interaction from the underlying harness state machine.
  - CLIs, interactive TUIs, desktop cockpits, web dashboards, and headless CI triggers as interchangeable viewports over the same state artifacts.
- **State Semantics of HITL:**
  - Asynchronous review vs. synchronous blocking.
  - Non-destructive review cycles: `PASS` vs. `FEEDBACK` avoiding false binary rejections and preserving historical trajectory.
  - Cycle identities and iteration tracking.

### 7. Conceptual Blueprint: How to Engineer Any Harness from Scratch
- **Phase 1: Domain Invariant & Ground Truth Modeling:** Defining baseline contracts and formal specification schemas.
- **Phase 2: Gate Topology & State Transition Design:** Establishing prerequisite graphs, cycle boundaries, and report schemas.
- **Phase 3: Verification Partitioning:** Isolating deterministic evaluation scripts from probabilistic agent generation.
- **Phase 4: Runtime Projection & Discovery Engine:** Designing the scaffolding logic that maps capabilities to commercial agent runtimes.
- **Phase 5: State Persistence & Integrity Layer:** Implementing cryptographic baselines and immutable event logging.
- **Phase 6: Ingress Layer Design:** Implementing surface adapters (CLI, TUI, GUI, CI) over the unified state machine.

---

## Execution Milestones

| Milestone | Action | Target Output |
|---|---|---|
| **M1: Plan Alignment** | Validate generalized, domain-agnostic scope with user. | [2026-10-26_1105_conceptual_harness_architecture_plan.md](file:///home/javastral-gcpds/GIT/UNAL/codeanvil-gcpds/odd/tasks/2026-10-26_1105_conceptual_harness_architecture_plan.md) |
| **M2: LaTeX Document Scaffolding** | Initialize LaTeX structure, article/report class, packages, and abstract. | `methodology/conceptual/conceptual_system_development_HARNESS.tex` |
| **M3: Sections 1–3 Drafting** | Author Spectrum of AI Engineering, Frameworks vs. Harnesses, Dual-World Architecture. | LaTeX Sections 1–3 |
| **M4: Sections 4–6 Drafting** | Author Agnostic Strategies, Decentralized State, Multi-Surface Ingress. | LaTeX Sections 4–6 |
| **M5: Section 7 & Synthesis** | Author Generalized Step-by-Step Blueprint and Conclusion. | LaTeX Section 7 & Final Polish |
| **M6: Verification & Build** | Compile LaTeX to PDF using `latex-compile` skill; review typography and structure. | PDF Artifact |

---

## References

- [Agent Skills Specification](https://agentskills.io/home) — Universal agent capability packaging standard.

---

## Execution Log

### 2026-10-26 — M2–M6 closed

| Milestone | Status | Evidence |
|---|---|---|
| **M2** Scaffolding | Done | `methodology/conceptual/conceptual_system_development_HARNESS.tex`, self-contained (no `\input`, no external `.bib`), palette shared with `methodology/V-SIL-v2/V-SIL.tex`. |
| **M3** Rationale (1–3) | Done | Sections 1–3: four-paradigm taxonomy, trade-off matrix, three-layer stack, `Definition 3.1` (harness quadruple), `Proposition 3.1` (runtime portability), cockpit inventory, economics of iteration, responsibility split. |
| **M4** Architecture (4–6) | Done | Section 4 factory/vehicle with invariants and compilation pipeline; Section 5 Agent Skills frontmatter, symlink mesh, MCP renderings, system-package bridging, portability matrix, conformance gaps; Section 6 choreographed enforcement (`Proposition 6.1`), failure semantics, decidability partition, custody. |
| **M5** Blueprint (7) | Done | Section 7 ingress/HITL; Section 8 five-step blueprint with maturity model and anti-pattern catalogue; Section 9 threats to validity; Section 10 conclusion; 16 references. |
| **M6** Compile & verify | Done | `latexmk -pdf` → 29 pages; 0 errors, 0 overfull boxes, 0 undefined references, 0 Type 3 fonts; 5 figures and 16 tables rendered and inspected. |

**Recovery note.** A `re.sub`-based figure-replacement pass deleted Sections 3–6 partially
(figure + four sections). Content was reconstructed from the section specs above and re-spliced
by exact text anchors; the misplaced `fig:partition` block was restored to its own subsection,
`fig:layers` was rewritten, and `fig:mesh` was laid out again with non-overlapping nodes.

### 2026-10-26 — Scope revision: product- and domain-agnostic rewrite

Trigger: user instruction — section 7 discussed the reference product instead of how to build
*any* harness; plan objective requires "abstracts away any specific product implementation or
domain methodology (such as CodeAnvil or V-SIL)".

| Change | Before | After |
|---|---|---|
| Section 8 | Five-step procedure shaped by the reference product | Six-phase universal blueprint (Phase 1–6) with produces/exit criterion per phase and expanded prose |
| Product tokens | `CodeAnvil` ×2, `V-SIL` ×6, `G0`/`CC` gate ids | 0 occurrences; gate ids `G1` / `CUSTODY` / `G2` |
| State paths | `.codeanvil/` ×16 | `.harness/` |
| CLI in Figure 2 | `codeanvil create` | `harness init` |
| Baseline files | `GT/G0_StRS.md`, `GT/G0_SyRS.md` | `GT/stakeholder-requirements.md`, `GT/system-requirements.md` |
| Cycle key | `01_test_sdr_usrp_iot_signals` | `01_baseline` |
| Method and evidence | "reference implementation (CodeAnvil) … traceable to a file in that implementation" | Rules distilled from a deployed reference harness; IEEE 29148 kept only as the worked example, with Phase 1 named as the substitution point |
| Bridging example | GNU Radio / SDR toolchain | Non-package-managed domain runtimes (native library, vendor SDK, licensed simulator) |
| References | 16 entries | 14 entries (`vsil`, `codeanvil` removed; all remaining entries cited) |
| Title subtitle | "Conceptual Design, …" | "Conceptual Foundations, …" per plan title |

**Verification.** `latexmk -pdf` → 30 pages, 0 errors, 0 overfull boxes, 0 undefined
references/citations. Pages 1, 9–10, 12, 17, 21, 24–27 and 30 inspected at 100 dpi. The
`lst:vehicle` split between pages 9 and 10 is pre-existing (it also occurs in the 29-page build
before this revision) and was left unchanged; the layout alternatives tested (float placement for
the listing) produced a float-only page and were rejected.

### 2026-10-26 — Revision: cockpit / outer-harness framing, 13 pages, zero product artifacts

Trigger: user instruction — "I dont like approach of 4. I dont like to see codeanvil artifacts.
Remember is a general harness development methodology, NOT 'How I did codeanvil-gcpds'".

Decision: the paper names *roles*, never a product. CodeAnvil, V-SIL, gate ids, skill
directories, script names, CLI verbs and repository paths are all absent; the state substrate is
described by function (manifest, append-only report tree, custody directory) and the single
listing is a format-level report schema with angle-bracket placeholders.

| Aspect | Before | After |
|---|---|---|
| Length | 30 pages | **13 pages** (requirement: ≤15) |
| Core framing | framework vs runtime vs harness | **Cockpit (Layer 1, rented)** vs **Outer Harness (Layers 2–3, owned)** |
| Baseline | none | `Agent = Model + Harness` as eq. (1), echoed in Figure 1 and the abstract |
| Ownership model | implicit | ETCSLV (Execution, Tools, Context, State, Lifecycle, Evaluation) split table |
| Rule D | present in §6.3 | re-emphasised in §5.3: pure scripts, standalone process, exit contract 0/1/2, model confined to synthesis |
| Figures / tables / listings | 5 / 16 / 5 | **2 / 7 / 1** |
| References | 14 | **18**, all cited: + Bojone 2026, Meng 2026 (ETCSLV), Ning 2026, ecosystem entry (Spec Kit, OpenSpec, Superpowers, gentle-ai, gentle-shell) |
| Typography | 11pt | 10pt to meet the page ceiling without dropping content |

Section map: 1 Introduction · 2 Paradigm spectrum (2.3 cockpit, 2.4 outer harness, 2.5 ETCSLV) ·
3 Architectural divide (3.4 interchangeability test) · 4 Structure and portability (4.1 gate
topology, 4.2 authoring/execution planes, 4.3 portable projection, 4.4 conformance gaps and
ecosystem) · 5 State, control, verification (5.3 Rule D, 5.4 custody) · 6 Ingress and human
verdicts · 7 Blueprint (six phases + maturity) · 8 Threats · 9 Conclusion.

**Verification.** `latexmk -pdf` → 13 pages; 0 overfull boxes, 0 underfull boxes, 0 undefined
references or citations; all 18 bibitems cited; artifact scan (`codeanvil`, `.harness/`, `GT/`,
`G0_`, `SyRS`, `StRS`, script and directory names) returns zero hits. Pages 1–13 rendered at
100 dpi and inspected; Figure 1 and Figure 2 re-laid out (stray brace, overlapping ownership tags
and a label overlapping the Model band were removed).

**Open caveat.** The three 2026 references were supplied by the user and were not independently
verified against a source; they are reproduced as given.

---

## Execution Log — Revision 3 (v2.1, audit response)

**Input.** Reviewer audit of v2.0 against the 2026 state of the art: 4.4/5, three blockers.
Action limited to the low-SOTA-adaptation areas and the risky gaps; no invented claims.

**Citation integrity (F1).** arXiv:2609.00006 is real but authored by **Barbaste, Darrigol, Vu and
Wiltberger**, not "B. Bojone" — bibitem replaced. "Ning et al., Evolving Agent Harnesses through
Object-Oriented Design" could not be located in any source; replaced with the closest verified
work, **Lin et al., Agentic Harness Engineering (arXiv:2604.25850)**. Meng et al. is real
(Preprints 202604.0428) and its acronym expansion was re-verified against the authors' official
repository: **ETCSLV = Execution, Tools, Context, State, Lifecycle, Evaluation** — the audit's
"evidence" reading came from a secondary source and is wrong, so the acronym stands. Bibliography
now carries author lists, venues and access dates for the web sources.

**Economics (F3).** The flat-seat premise is gone. §2.2, §2.3, the matrix commentary and §3.3 now
describe subscription + metered allowance, and the argument moves to the unit of work: a harness
spends tokens on synthesis and judgment and spends nothing on checks a script decides. Added the
corollary *the cheapest token is the one never sent*, tied to Rule D. Table 1 "Cost control" drops
the cockpit from 3 to 2; the harness keeps 3.

**Untrusted cockpit (F2).** New §5.5 with the OWASP LLM01:2026 threat: reports and verdict lines
are written by the agent, so an injected cockpit can append a PASS with a plausible evidence line
and the ledger signs what it is handed. Three controls, all architectural: verdicts committed
**out of band**; deterministic evidence **re-derived at read time** (total functions make replay
free); and **configuration isolation is not process isolation** — a distinction now stated in the
section, in the custody table (new row), and in Phase 4. §6's "a verdict is a decision, not a
signature" was reconciled with the out-of-band commit, and Phase 5's exit criterion now includes
replaying a validator against a forged evidence line.

**Other gaps.** (a) Cockpit SDKs added as a cockpit variant in §2.3 and referenced from §3.5, so
the taxonomy names the middle path without a sixth paradigm. (b) §4.2 gains a fifth invariant,
*no vendor workflow engine*. (c) §4.3 anchors the mesh on AGENTS.md and the Agent Client Protocol.
(d) §8 no longer claims the evaluation field is empty: HarnessRisk and Terminal-Bench 2.0
(LangChain, 13.7 points with the model fixed) are cited, and the contribution is narrowed to a
method for evaluating *a given* harness. (e) The single-writer limitation now names claim/lease
semantics as the expected fix for multi-agent cockpits. (f) Version bumped to 2.1; abstract names
the untrusted cockpit.

**Deliberately skipped.** F9 (throwaway-harness debate) — the named sources were not verifiable in
the time available, and paraphrasing an unattributed debate would have added noise. F4's sixth
paradigm row — a full table column costs more than the taxonomy gains; the paragraph carries it.

**Verification.** `latexmk -pdf` → **15 pages** (ceiling ≤15); 0 overfull, 0 underfull, 0
undefined references, 0 undefined citations; 22 bibitems, all cited (comm diff in both directions
empty). Float parameters (`\topfraction` 0.9, `\floatpagefraction` 0.85) removed a float-only page
that Figure 2 and Table 5 had created. Pages 1, 3, 7, 10, 11, 13 and 15 rendered at 90 dpi and
inspected: Table 1 ratings, the SDK paragraph, the ACP sentence, Figure 2 placement, Table 5 with
the new row, §5.5, Phases 4–5 and the bibliography all read correctly. Artifact scan
(`codeanvil|v-sil|\.codeanvil|g0_|GT/|marconi|beaupy`) returns only the author affiliation.

**Reproduction of the claim about sealing.** The sentence on path rules was narrowed to what the
sealing script actually enforces (project-relative set, symlinks refused), verified in
`templates/skills/custody-chain/scripts/source_snapshot.py`.

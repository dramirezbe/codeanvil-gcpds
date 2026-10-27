# G2 Gate Research: SOTA & Industry Practice for DSP Pipeline Design & Synthesis

Oct 27, 2026 · @David Ramírez Betancourth

Research across five areas to inform the design of Gate G2 in V-SIL v2: the gate that transforms SRS requirements (IEEE 29148 §9.6) into verified GNU Radio flowgraphs with full traceability. Scoped to software development on COTS hardware.

### V-SIL v2 Terminology Reference

| Code | Definition |
|------|-----------|
| **Ctx 00–03** | Context-bounded stages of Layer 1 (conceptual validation). Ctx 00: Project Definition → Problem Baseline. Ctx 01: Requirements → Versioned Requirements Baseline (GT). Ctx 02: Architecture and Design Resolution → Selected Architecture + Implementation Plan. Ctx 03: Executable Implementation Contract → Build Package. |
| **G0, G1, G2** | Deterministic or AI-driven gates between or within context stages. G0: structural GT validation (deterministic, no AI). G1: design synthesis (AI-driven, 10-job pipeline producing SRS). G2: DSP pipeline design (this document's subject). |
| **Gate H** | Human readiness gate. Fires at Ctx 01→02 and Ctx 02→03 transitions. |
| **CC** | Custody Chain — cross-cutting provenance skill that seals GT after G0 pass. |
| **P1–P4** | Governing principles. P1: HITL ≠ HIL (authorization vs. validation barriers). P2: Oracle ≠ generator (the model never approves its own work). P3: Mechanical rejection beats LLM approval. P4: Verified ≠ validated (claims name the environment). |
| **Artefact 3** | Eval and benchmarking suites — golden test vectors that serve as the CI regression harness in Layer 2. |
| **Artefact 4** | Guardrail: no model output enters a baseline without a traceable source or test; unsupported statements marked unverified. |
| **Artefact 5** | Operational telemetry — reviewer edits, rejected drafts, retry counts, gate outcomes, defect classes. |
| **Artefact 6** | Privacy constraint — captured I/Q and demodulated content stay local; redacted before storage/transmission. |
| **R0–R3** | Defect routing. R0: Ctx 00 (scope). R1: Ctx 01 (requirement). R2: Ctx 02 (design). R3: Ctx 03 (implementation). |
| **StRS** | Stakeholder Requirements Specification (IEEE 29148 §9.4). Contains `STK-`, `HWC-`, `NRM-` blocks. |
| **SyRS** | System Requirements Specification (IEEE 29148 §9.5). Contains `SYS-` blocks per measurand. |
| **SRS** | Software Requirements Specification (IEEE 29148 §9.6). Produced at G1 (Job 7), not a G0 input. |

## Area 1: DSP Pipeline Architecture Patterns

How mature SDR/DSP systems decompose signal chains from requirements to block-level design.

### 1.1 REDHAWK SCA — Component-Waveform-Application

REDHAWK is the open-source reference of the JTRS Software Communications Architecture (SCA 2.2.2). Its three-tier decomposition — **Components** (individual processing elements), **Waveforms** (XML-declared connected component sets), and **Applications** (deployed waveforms) — mirrors a spectrum-sensing pipeline.

Key patterns for G2:

- **Port-based data flow.** Typed ports (BulkIO for streaming I/Q, FrontendInterfaces for tuner control) carry type metadata, sample rate, and timestamps — analogous to GNU Radio stream tags.
- **XML-declared composition.** Topology separated from parameterization. This separation is what G2 must formalize: topology is a design decision (Ctx 02 — Architecture and Design Resolution), parameterization is requirements flow-down from the SRS produced at G1.
- **Device abstraction.** FrontendInterfaces abstract SDR hardware — the same HAL pattern V-SIL defines.

REDHAWK's waveform descriptor is the closest existing analog to G2's output: a machine-readable block topology and parameterization spec, traceable to requirements.

### 1.2 GNU Radio Flowgraph Patterns

GNU Radio centers on blocks, flowgraphs (top\_block), and hierarchical blocks (hier\_block2). Standard spectrum-sensing patterns:

- **Channelizer → Per-channel → Fusion:** Polyphase filter bank splits wideband I/Q; each channel gets PSD estimation, detection, classification; results fuse into occupancy decisions.
- **Sweep → FFT/PSD → Threshold → Classification:** For HackRF-class devices, frequency sweep acquires sequential bands; Welch/Bartlett PSD estimation; threshold detector classifies.
- **Source → Correction chain → Measurement → Decision:** Metrological pattern — raw I/Q corrected (antenna factor, cable loss), measured (PSD, OBW, carrier frequency), enters regulatory decision.

### 1.3 Parameterization Flow-Down

The critical pattern for G2 — not well-formalized in existing frameworks:

1. **Regulatory requirement** → **measurand spec** (OBW at -26 dB, RBW, measurement time)
2. **Measurand spec** → **DSP parameters** (NFFT = fs/RBW; window from sidelobe req; averaging from measurement time)
3. **Hardware constraints** → **feasibility check** (can COTS device achieve required NFFT?)
4. **Uncertainty budget** → **parameter tightening** (budget allocation constrains window choice)

G2 must formalize: SRS requirement → parameterized block → justified parameter → acceptance criterion from uncertainty allocation.

## Area 2: Requirements-to-Flowgraph Traceability

Methods for formally tracing RF/DSP requirements to block parameters.

### 2.1 IEEE 29148 Traceability Applied to DSP

IEEE 29148 prescribes bidirectional traceability from stakeholder requirements through system requirements to software requirements. For DSP, this maps to: StRS stakeholder requirement (e.g., "monitor FM broadcast compliance") → SyRS measurand specification (carrier frequency error ≤ ±2 kHz, uncertainty ≤ ±200 Hz) → SRS software requirement (REQ-CF-001: measure carrier frequency using Welch PSD with NFFT ≥ 8192, Hann window, 10-segment averaging).

The traceability chain for each DSP block parameter must include: the SRS requirement ID, the measurand and acceptance criterion it derives from, the mathematical justification (e.g., frequency resolution Δf = fs/NFFT ≤ required\_resolution), and the uncertainty component it addresses.

### 2.2 GUM Uncertainty Budget as Parameterization Driver

The GUM framework (JCGM 100:2008) decomposes measurement uncertainty into individual components, each classified by evaluation method (Type A: statistical, Type B: non-statistical). For DSP parameterization, each uncertainty component maps to a block parameter constraint:

- **Frequency resolution uncertainty** → constrains NFFT (Δf = fs/NFFT must be ≤ allocated uncertainty)
- **Spectral leakage uncertainty** → constrains window function (sidelobe level must keep leakage within budget)
- **Averaging uncertainty** → constrains segment count (variance reduction ∝ 1/√N\_segments)
- **ADC quantization uncertainty** → constrains dynamic range (ENOB × 6.02 dB must cover required range)
- **Sample rate uncertainty** → constrains timing reference (oscillator stability must keep rate within budget)

NIST Handbook 157 (Guidelines for Radiometric Calibration) demonstrates the pattern: each parameter in the measurement equation gets an allocated uncertainty, and the calibration/verification process confirms the allocation holds. The same approach applies to DSP: each block parameter gets an uncertainty allocation, and the SIL test confirms the allocation.

NIST research on spectrum-sensing measurement challenges confirms that making spectrum sensors SI-traceable requires tracking uncertainty propagation rigorously from physical standards through the DSP chain to reported measurands.

### 2.3 NIST Spectrum Sensing Traceability

NIST has published directly on measurement traceability for spectrum sensing systems, identifying that laboratory ROC (receiver operating characteristic) measurements must connect detection performance to traceable physical quantities and fundamental SI units, with estimated uncertainties propagated to high-level network parameters. The proposed traceability path runs from physical noise standards through calibrated transfer standards to deployed sensors — each link carrying an uncertainty budget.

For G2, this means every DSP block parameter that contributes to a reported measurand must carry: the requirement it traces to, the uncertainty component it addresses, the mathematical relationship between parameter value and uncertainty contribution, and the acceptance criterion that verifies the allocation.

### 2.4 Parameterization Justification Record

No existing standard prescribes a formal "parameterization justification" document for DSP blocks. This is a gap G2 must fill. The closest analog is DO-178C's "low-level requirements" — detailed enough to be directly implemented — combined with IEC 61508's requirement that every safety function's parameters be justified against the safety requirement.

G2's traceability artifact should be a per-block record: SRS requirement ID → block type and instance → parameter name → parameter value → derivation formula → uncertainty allocation → acceptance criterion → test vector reference.

## Area 3: COTS Software Development Methodology

How safety-critical standards handle detailed design → implementation → unit test for COTS-based software.

### 3.1 DO-178C (Airborne Software)

DO-178C is the most mature standard for the artifacts G2 must produce. Its relevant processes and required artifacts at the detailed design stage:

- **Software Design Process (§5.2):** Produces software architecture and detailed design. Design must be verified against high-level requirements (Table A-4) and low-level requirements (Table A-5). Low-level requirements are detailed enough to code from directly — this is exactly what G2's block parameterization records must be.
- **Verification artifacts:** Software Verification Cases and Procedures (SVCP), Software Verification Results (SVR), bidirectional traceability from system requirements → software requirements → design → code → tests.
- **Table A-6 (Verification of Design Process outputs):** Architecture and design must be verified for consistency with requirements, accuracy, conformance to standards, and verifiability. Each design element must be traceable to at least one requirement.
- **COTS qualification:** DO-178C does not have a direct COTS qualification path — it requires the same evidence for all software regardless of origin. In practice, COTS is handled through "previously developed software" provisions or through DO-200B (data processing) for data-centric COTS. For GNU Radio blocks, this means the V-SIL approach of treating blocks as components requiring verification evidence is consistent with DO-178C philosophy.

**G2 implication:** G2's output must include design-level artifacts equivalent to DO-178C Table A-4/A-5/A-6: architecture description, detailed design (block parameterization), traceability matrix, and verification cases.

### 3.2 IEC 61508 (Functional Safety)

IEC 61508 Part 3 governs software for safety-related systems. Relevant provisions:

- **Software detailed design (§7.4.5–7.4.6):** Requires detailed design specification traceable to architecture, with verification that the design is correct and complete.
- **COTS/Proven-in-use (Route 2H):** IEC 61508 allows a "proven-in-use" argument for pre-existing software components when sufficient operational evidence exists (IEC 61508-7 Annex D). However, as recent analysis clarifies, proven-in-use requires statistical confidence via chi-square-based confidence intervals — it is not simply "it has been used before." Software lifecycle requirements and verification activities remain mandatory regardless of proven-in-use status.
- **Techniques and measures (Part 7):** Recommends static analysis, boundary value testing, equivalence class testing, and formal methods, scaled by SIL level. For SIL 2+ (relevant to regulatory measurement), traceability from safety requirements to design to code to tests is "highly recommended."

**G2 implication:** GNU Radio blocks used as COTS components need either full verification evidence or a documented proven-in-use argument with statistical support. V-SIL's golden vector testing provides the operational evidence base.

### 3.3 ECSS-E-ST-40C (Space Software)

ECSS-E-ST-40C Rev.1 (April 2025) is the latest European space software standard. Its detailed design requirements:

- **§5.5.1 Detailed Design:** Requires detailed design document (SDD) traceable to software requirements, with verification against 8 code objectives (§5.8.3.5a) plus Annex U's 14 code checks.
- **Software criticality categories:** ECSS-Q-ST-80C Table D-1 defines four criticality categories that scale verification rigor — analogous to V-SIL's capability classes.
- **Design verification (§5.8.3.3a–5.8.3.4a):** Both architectural and detailed design must be verified for consistency with requirements and interfaces. SCADE Suite (model-based) is the reference implementation for meeting these requirements.
- **Tool qualification (§5.12):** Tools used in the development process must be qualified — directly relevant to Marconi (the GNU Radio MCP server) and the LLM agent.

**G2 implication:** Tool qualification for the agent and MCP server is a requirement ECSS identifies that V-SIL's harness engineering addresses.

### 3.4 IEC 62443 (Industrial Cybersecurity)

IEC 62443-4-1 defines the Secure Development Lifecycle (SDL) for component developers, with eight practices including security requirements, secure design, secure implementation, and verification/validation. IEC 62443-4-2 defines Component Requirements (CRs) across security levels (SL 1–4). For SDR monitoring systems:

- **Security Development Artifacts (SDA):** Documentation of security design decisions, threat models, and verification evidence.
- **COTS component integration:** Requires security assessment of third-party components and supply chain traceability (SBOM). For GNU Radio and its dependencies, this means documenting the dependency chain and known vulnerabilities.

**G2 implication:** Security requirements from IEC 62443 should flow into the SRS and be verified alongside functional requirements.

### 3.5 Cross-Standard Synthesis for COTS Software Artifacts

Across all four standards, the required artifacts at the detailed design stage converge on:

1. **Software Design Document (SDD)** — architecture and detailed design, traceable to requirements
2. **Traceability matrix** — bidirectional: requirement ↔ design element ↔ code ↔ test
3. **Verification cases and procedures** — test specifications traceable to requirements
4. **COTS qualification record** — evidence that each COTS component meets the requirements allocated to it (proven-in-use, wrapper testing, or full verification)
5. **Configuration index** — exact versions of all components, tools, and dependencies

## Area 4: Simulation-Based DSP Verification

Best practices for synthetic test vectors and verifying DSP outputs before hardware.

### 4.1 IEEE 1641 — Signal and Test Definition

IEEE 1641-2022 provides a formal language for defining test signals and expected responses. Its core concept: signals are built from Basic Signal Components (BSCs) using a Signal Modeling Language (SML), composed into Test Signal Frameworks (TSFs), and exercised via a Test Procedure Language (TPL). The standard provides mathematically unambiguous signal definitions usable across all test platforms.

For G2, IEEE 1641's pattern is directly applicable: each synthetic test vector is a composition of BSCs (carrier, noise, modulation, interference), parameterized to exercise specific acceptance criteria. The formal definition ensures the test signal is reproducible independently of the generation platform.

### 4.2 GNU Radio QA Framework

GNU Radio has a built-in QA (quality assurance) testing framework used for block-level verification:

- **gr\_unittest:** Python unittest-based framework. Tests instantiate a top\_block with vector\_source → block\_under\_test → vector\_sink, run the flowgraph, and compare output against expected values using assertAlmostEqual and assertComplexTuplesAlmostEqual.
- **Golden model pattern:** The gr-doa (direction of arrival) module demonstrates the mature pattern — Octave/MATLAB reference implementations serve as the golden model; Python QA tests call Octave via oct2py bridge; synthetic I/Q data is generated with specific DoA and noise profiles; C++ results are validated against the reference.
- **GRCon24 — Automating System Tests in GRC (Stringer, nou Systems):** Presented a workflow for GRC-level system tests using OOT blocks for test conditions and pass/fail criteria, with both SIL and HIL configurations using channel emulators.

### 4.3 Golden Vector Testing for DSP

The golden vector pattern for DSP verification:

1. **Vector generation from requirements:** Each SRS requirement with an acceptance criterion generates one or more test vectors. The vector is a synthetic I/Q recording parameterized to exercise the criterion at its boundary conditions.
2. **Boundary condition coverage:** For each measurand (e.g., carrier frequency), vectors at nominal, at-threshold, and over-threshold conditions. For uncertainty budget verification, vectors at the allocated uncertainty boundary.
3. **Known-answer testing:** The expected output is computed analytically or by a validated reference implementation (the golden model). The DSP pipeline output must match within the allocated uncertainty.
4. **Error injection:** Vectors with injected non-idealities (noise, interference, sample drops, quantization) exercise the pipeline's robustness and the "Uncertain" behavior required by Artefact 4 (V-SIL v2 §3.8: guardrail ensuring no model output enters a baseline without traceable source or test).

### 4.4 SIL Testing Methodology

The MIL→SIL→PIL→HIL testing ladder is well-established in automotive (AUTOSAR), aerospace, and robotics. Key patterns for SDR:

- **Hardware Abstraction Layer (HAL):** The production code interfaces with hardware only through a HAL. In SIL, the HAL is replaced by a Mock HAL that serves synthetic I/Q from golden vectors. V-SIL already defines this pattern.
- **Virtual ECU / V-ECU pattern:** From automotive SIL, the concept of abstraction levels for virtual hardware: Level 1 (application model only) through Level 5 (full AUTOSAR stack with OS). For SDR, the analog is: Level 1 (SciPy exploration), Level 2 (GNU Radio flowgraph with mock source), Level 3 (GNU Radio with Mock HAL and realistic timing), Level 4 (GNU Radio with real device driver in loopback), Level 5 (full HIL with RF path).
- **Closed-loop SIL:** SIL tests that exercise the full measurement cycle: acquire (from mock) → process (DSP pipeline) → decide (threshold/classifier) → report. The acceptance gate compares reported measurands against the known ground truth of the synthetic vector.

### 4.5 GRCon26 — Verilator-Based Validation

A GRCon26 paper demonstrated using Verilator to translate GNU Radio flowgraphs to cycle-accurate C++ simulations, integrated back into GNU Radio as reference blocks. This reduced development cycle time from 10-30 minutes to sub-second feedback, using existing GNU Radio flowgraphs as reference implementations for algorithmic correctness validation before FPGA deployment. The pattern is directly applicable to G2: the SciPy/NumPy exploration layer serves as the reference implementation, and the GNU Radio flowgraph must match it within tolerance.

### 4.6 Synthetic Vector Generation from Uncertainty Budgets

No published method formally derives synthetic test vectors from GUM uncertainty budgets *for DSP pipelines specifically*. The derivation method exists in metrology practice (NIST HB 157 prescribes it for radiometric calibration), but has not been formalized for software-defined DSP chains. The approach G2 should prescribe:

1. For each uncertainty component in the SyRS budget, identify the DSP parameter it constrains.
2. Generate a test vector that isolates that component (e.g., for windowing uncertainty: a vector with a signal at the window's sidelobe null frequency).
3. Set the acceptance criterion to the allocated uncertainty for that component.
4. The composite test (all vectors) verifies the combined uncertainty.

## Area 5: AI-Assisted DSP Design (2024–2026)

Emerging work on LLM agents for DSP/SDR synthesis and optimization.

### 5.1 GRCon 2025–2026: LLM + GNU Radio

The GNU Radio community has moved rapidly on AI integration:

- **GRCon25 — Paul David (SimpliRF): "Powering Cognitive Radio with LLMs"** — Fine-tuned Qwen models on GRC traces, used MCP to let the LLM orchestrate flowgraphs. Key finding: LLMs are "sample-inefficient and ill-suited for low-level interactions" with signal processing. The LLM serves as a high-level orchestrator, not a real-time processor. Validates V-SIL's separation: agent generates hypotheses, deterministic gates decide.
- **GRCon26 — "Hands-On with GRC-Agent" (Qoherent):** Open-source (AGPL-3.0) AI assistant inside GNU Radio Companion. Reads open .grc flowgraphs, answers questions grounded in a searchable block catalog and wiki docs, edits the graph through agentic tool calls. Runs fully locally with Ollama or any OpenAI-compatible API. Five key tools for inspecting, researching, troubleshooting, reasoning, and editing flowgraphs.
- **GRCon26 — "gr-autopilot: Closed-Loop Flowgraph Synthesis with HIL Feedback" (Florida Atlantic):** The most directly relevant work. An LLM agent constructs TX/RX flowgraphs via MCP, deploys to USRPs/ADALM-Pluto, runs automated HIL tests over controlled RF path, iterates on modulation/coding/filtering/sync parameters with explicit memory of which edits improved which metrics. Optimizes a constrained objective (BER target + spectral efficiency under fixed link budget). This is exactly the closed-loop agent pattern your DSP pipeline literature analysis describes.
- **GRCon26 — "Deploying GNU Radio in Agentic AI Systems":** GNU Radio flowgraphs deployed within NVIDIA Triton Inference Server, managed via MCP. AirStack Edge exposes workflow-level configuration interfaces allowing agents to configure SDR pipelines without modifying topology. Demonstrates live agent orchestrating a remote sensor, performing RF AI inference, reporting to a central platform.
- **GRCon26 — "Your Flowgraph is the Chip: Kyttar":** AI agent-generated GNU Radio block library compiled straight to silicon. Every Kyttar block written by an AI agent, with testbenches checking against GNU Radio floating-point originals. Running unattended: 113 verified blocks, measuring quantization noise against references. 120-cell prototype in fabrication. The block-generation workflow includes prompts, rules, and verification — the most complete agent-in-the-loop block generation system published.

### 5.2 GR-MCP: GNU Radio MCP Server

GR-MCP (gnuradio-mcp on PyPI) is a FastMCP server exposing 80+ MCP tools for building, validating, running, and exporting .grc files, plus block development, protocol analysis, and OOT module management. Key capabilities:

- **Flowgraph building (30 tools):** Programmatic block creation, connection, validation, and export.
- **Block development workflow:** AI-assisted generation of sync, basic, interpolating, and decimating blocks from natural-language descriptions, with AST validation and signature checking.
- **Protocol analysis:** Parse protocol specs, generate decoder chains, analyze IQ files.

This validates Marconi's architecture (V-SIL's MCP server: 19 curated GR tools + 6 RF/SDR skills, scoped to the V-SIL methodology; GR-MCP is the general-purpose 80+ tool superset). The GR-MCP ecosystem confirms MCP as the emerging standard interface for LLM-to-GNU-Radio integration.

### 5.3 Hardware Design Agent Patterns (Transferable)

- **"Architect in the Loop" (Mohammed, WWU, Dec 2024):** Blueprint-driven agent for processor design. JSON blueprint → SystemVerilog + cocotb → Verilator linting → functional tests → FPGA. Identified the "semantic cohesion gap" — LLM designs drift from specs as complexity grows. The blueprint pattern and self-correction loop map directly to G2.
- **AIvril (2024):** Multi-agent RTL generation with verification in-the-loop. AutoReview enforces syntax correctness; AutoDV targets functional correctness. ReAct-based mechanism with code agent and review agent.
- **AgentDV (2026):** Closed-loop verification environment generation. Coverage-guided iteration with runnability filtering. First LLM-based DV study reporting pass-rate and coverage on real IP blocks.
- **Agentic EDA survey (2026):** Documents the shift from "LLM generates code" to "LLM orchestrates tools" — the same shift V-SIL's Marconi architecture embodies.

### 5.4 Compound Reliability and Verification Gaps

Key warnings from literature:

- **Compound reliability decay ("Beyond pass@1"):** For T steps with per-step error ε, reliability decays as (1-ε)^T. With ε=0.05 and T=10, reliability is \~60%. G2 must keep the agent's autonomous chain short and gate each step mechanically.
- **Verification gap:** \~83% of autonomous agents publish code, but only \~38% produce reproducible artifacts. G2's golden vector testing and deterministic gates address this directly.
- **MOP Paradox:** The strongest models exhibit the highest catastrophic failure rates (19%). Mechanical rejection (P3) is immune to this because it does not involve LLM judgment.
- **ToolGate (ACL Findings 2026):** Hoare-style contracts for LLM tool execution. Precondition filtering prevents invalid calls; postcondition verification catches bad outputs; trajectory constraints enforce global invariants. Directly applicable to Marconi's tool definitions.

### 5.5 What's Novel in V-SIL's Approach

From the literature analysis, four things are novel in the V-SIL DSP pipeline that no published work combines:

1. An LLM agent that designs DSP pipelines (not classifies signals) within a governed lifecycle (Ctx 00–03 stages with G0/G1/G2 gates)
2. A SciPy/NumPy exploration → GNU Radio flowgraph translation with deterministic constraint gates — the exploration layer (§4.4 SIL Level 1) serves as the golden model reference, and the GR flowgraph must match it within tolerance (§4.5 Verilator pattern); G2 formalizes this as a mandatory design step
3. StRS-driven constraint checking (via `HWC-` hardware constraint blocks) using ToolGate-style contracts for Marconi's SDR tools
4. V-model integration embedding the agent loop into IEEE 29148 requirements traceability (StRS → SyRS → SRS → DSP blocks → test vectors)

## Synthesis: G2 Gate Design Implications

What these five areas prescribe for the G2 gate specification.

### What G2 Must Produce (Terminal Output)

Drawing from DO-178C, IEC 61508, ECSS-E-ST-40C, and REDHAWK/SCA, G2's terminal output should be a **Verified DSP Design Package** containing:

1. **DSP Design Document (DDD):** Block topology (as a validated .grc flowgraph and/or GNU Radio Python script), hierarchical decomposition, data flow specification, and interface definitions. Analogous to DO-178C's Software Design Description.
2. **Block Parameterization Justification Record:** For each DSP block, the complete traceability chain: SRS requirement ID → measurand → parameter name → parameter value → derivation formula → uncertainty component → acceptance criterion → test vector reference.
3. **COTS Block Qualification Records:** For each GNU Radio block used, evidence that it meets the requirements allocated to it — golden vector test results against reference implementation, or a documented proven-in-use record per IEC 61508 Route 2H.
4. **Synthetic Test Vector Suite:** IEEE 1641-style signal definitions parameterized from the SyRS uncertainty budget, with known-answer expected outputs for each acceptance criterion.
5. **SIL Verification Results:** Output of running the flowgraph against the test vector suite via Mock HAL, with measured metrics compared against acceptance criteria — the evidence that the design is verified at SIL level.
6. **Traceability Matrix:** Bidirectional: SRS requirement ↔ DSP block ↔ parameter ↔ test vector ↔ test result.

### How G2 Should Work (Gate Mechanics)

Synthesizing the agent patterns from GRCon26, the Architect-in-the-Loop workflow, and V-SIL's governing principles:

1. **Input:** G1's validated SRS (`GT/G1_SRS.md`, produced at G1 Job 7 and structurally validated at Job 8), the G0-validated GT pair (StRS for `HWC-` hardware constraints and `NRM-` normative obligations, SyRS for `SYS-` per-measurand uncertainty budgets), the selected architecture from G1's ADD (Jobs 3–6: multi-hypothesis trade study, ATAM, Attribute-Driven Design), and the Marconi MCP tool server.
2. **Agent role (bounded by P2 — oracle ≠ generator):** The agent reads SRS requirements, proposes a block topology and parameterization, generates the flowgraph via Marconi's MCP tools, and generates test vectors from the uncertainty budget. The agent never evaluates its own output — every acceptance decision is mechanical (P3).
3. **Deterministic gates (P3 — mechanical rejection beats LLM approval):** Hardware constraint validation (sample rate, bandwidth, ADC range against StRS `HWC-` blocks); block connection validation (GNU Radio's type system — note: GR only checks stream item size, not semantic correctness; Marconi should add semantic validation of block connections); parameterization completeness check (every SRS requirement traces to at least one block parameter); test vector coverage check (every acceptance criterion has at least one test vector).
4. **SIL verification (P4 — verified ≠ validated):** The flowgraph runs against the test vector suite via Mock HAL. Measured metrics are compared mechanically against acceptance criteria. Pass = the design is *verified* at SIL level. The gate never claims *validation* — that requires HIL with real hardware, and the claim must name the environment (P4).
5. **Iteration:** On failure, the agent receives the failing test results and constraint violations, proposes a revised design, and re-runs. The iteration is bounded (configurable max iterations) and logged in the experiment log (Artefact 5 telemetry).
6. **HITL gate (P1 — HITL is an authorization barrier):** After mechanical verification passes, Gate H (Ctx 02→03) fires: the human reviewer examines the design package and decides whether all implementation-critical design choices are resolved. **YES** admits to Ctx 03; **NO** returns to Ctx 02 for revision. G2's mechanical PASS is a precondition for Gate H, not a substitute — a flowgraph can be structurally valid and verified at SIL but contain wrong design choices.

### Gate Chain Position

G2 implements Ctx 02 (Architecture and Design Resolution) in the V-SIL gate chain. The full chain:

**Ctx 01** (requirements) → **G0** (structural GT validation) → **CC** (custody chain seal) → **Gate H** (Ctx 01→02: requirements complete?) → **Ctx 02** begins → **G1** (design synthesis: 10-job pipeline, SRS authoring at Job 7) → **G2** (DSP pipeline design, flowgraph synthesis, SIL verification) → **Gate H** (Ctx 02→03: all design choices resolved?) → **Ctx 03** (executable implementation contract)

G1 and G2 are both gates *within* Ctx 02. G1 resolves the design space (multi-hypothesis architecture, ATAM, SRS). G2 takes the selected architecture and SRS and produces the verified DSP implementation design. Gate H (Ctx 02→03) fires only after both G1 and G2 have terminally passed.

G2's prerequisite is G1's terminal PASS (the validated SRS + selected architecture from the ADD). G2's terminal output — the Verified DSP Design Package — feeds into the Ctx 02→03 Gate H review, and then into Ctx 03 as a frozen DSP design with full traceability. The report follows the same iterative, report-driven pattern as G0 and G1, with defect routing via R2 (design defect → Ctx 02).

### Key Standards and References

- [IEEE/ISO/IEC 29148:2018](https://www.iso.org/standard/72089.html) — Requirements engineering, traceability
- [IEEE 1641-2022](https://standards.ieee.org/ieee/1641/10876/) — Signal and Test Definition
- [DO-178C](https://quality.arc42.org/standards/do-178c) — Software verification artifacts, Tables A-4 through A-7
- [IEC 61508](https://www.iec.ch/functional-safety) — Functional safety, COTS proven-in-use
- [ECSS-E-ST-40C Rev.1 (2025)](<https://ecss.nl/wp-content/uploads/2025/05/ECSS-E-ST-40C-Rev.1(30April2025).pdf>) — Space software, detailed design verification, tool qualification
- [IEC 62443-4-1/4-2](https://www.isa.org/standards-and-publications/isa-standards/isa-iec-62443-series-of-standards) — Secure development lifecycle, component requirements
- [JCGM 100:2008 (GUM)](https://www.bipm.org/en/committees/jc/jcgm/publications) — Uncertainty evaluation and propagation
- [NIST HB 157](https://nvlpubs.nist.gov/nistpubs/hb/2015/NIST.HB.157.pdf) — Radiometric calibration guidelines
- [GR-MCP (gnuradio-mcp)](https://pypi.org/project/gnuradio-mcp/) — MCP server for GNU Radio, 80+ tools
- [GRCon26 proceedings](https://events.gnuradio.org/event/28/) — gr-autopilot, GRC-Agent, Kyttar, Agentic AI deployment
- [ToolGate (ACL Findings 2026)](https://arxiv.org/abs/2601.04688) — Hoare-style contracts for LLM tool execution
- ["Architect in the Loop"](https://arxiv.org/abs/2512.00016) — Blueprint-driven agent design and verification
- ["Beyond pass@1"](https://arxiv.org/abs/2603.29231) — Compound reliability decay in agent pipelines
- [NIST Spectrum Sensing Measurement Challenges](https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=931728) — SI-traceable spectrum measurement
- [GRCon25 — Powering Cognitive Radio with LLMs](https://events.gnuradio.org/event/26/contributions/750/) — SimpliRF, MCP + GNU Radio
- [gr-autopilot — Closed-Loop Flowgraph Synthesis](https://events.gnuradio.org/event/28/contributions/867/) — HIL agent feedback loop
- [Kyttar — Flowgraph to Silicon](https://pubs.gnuradio.org/index.php/grcon/article/view/199) — AI-generated GNU Radio block library
- [AgentDV (2026)](https://arxiv.org/abs/2608.27148) — Closed-loop LLM verification environment generation
- [DO-178C Lifecycle with ARP4754A (2026)](https://link.springer.com/article/10.1007/s42401-026-00455-4) — Toolchain traceability

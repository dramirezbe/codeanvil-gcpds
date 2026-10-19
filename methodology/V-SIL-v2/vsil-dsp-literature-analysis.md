# V-SIL DSP Experiment Pipeline — Literature Consistency Analysis

**David Ramírez-Betancourt · GCPDS · Universidad Nacional de Colombia**
**October 2026**

---

## 1. Architecture Under Review

The V-SIL DSP Experiment Pipeline proposes an agent-driven exploration loop for SDR signal-processing design, integrated into the V-SIL governed lifecycle at the Ctx 02 (Architecture & Design) stage. Its core claims:

- **Three-layer tool stack**: Exploration (Python + SciPy/NumPy) → Validation (GNU Radio Python API) → HIL (GNU Radio + SoapySDR/UHD).
- **Agent role**: The LLM generates DSP hypotheses as Python code; deterministic gates (HCS constraint checks, SNR/BER thresholds) approve or reject — the agent never evaluates its own output (P2: Oracle ≠ Generator).
- **Mechanical rejection over LLM approval** (P3): Binary constraint checks and threshold gates are the decision authority.
- **Separation of verification environments** (P4): SIL results are "verified," only HIL results are "validated."

This document assesses the architecture's consistency with 2024–2026 literature, identifies what already exists, what gaps remain, and why specific tool choices were made.

---

## 2. What Already Exists in Literature

### 2.1 LLM + GNU Radio Integration

**Paul David, "Powering Cognitive Radio with LLMs," GRCon25 (Sep 2025)** — SimpliRF fine-tuned Qwen models on GNU Radio Companion `.grc` traces and used MCP (Model Context Protocol) to let the LLM orchestrate GNU Radio flowgraphs. Key findings: LLMs are "sample-inefficient and ill-suited for low-level interactions" with signal processing, and real-time DSP requires non-LLM alternatives (Hebbian Cellular Automata proposed). The LLM serves as a high-level orchestrator, not a real-time processor.

- **Consistency**: Directly supports our architecture's separation — the LLM generates hypotheses at the Python/SciPy level; it never touches real-time GNU Radio block execution. The MCP approach validates the agent-harness integration pattern.
- **PDF**: https://events.gnuradio.org/event/26/contributions/750/attachments/221/598/grcon25_paper_paul_david.pdf

### 2.2 LLM as RF Signal Processor

**RF-GPT (Khalifa University, Feb 2026, arXiv 2602.14833)** — Converts I/Q data to spectrograms and feeds them as "RF tokens" to a multimodal LLM. Handles modulation classification, overlap analysis, and technology recognition.

**RadioLLM (Jan 2025, arXiv 2501.17888)** — Hybrid prompt/token reprogramming for cognitive radio. A single LLM handles classification, denoising, and spectrum allocation.

- **Consistency**: Both treat the LLM as a signal *processor* (inference on signals), not a pipeline *designer*. Our architecture addresses the complementary problem: the LLM as a DSP *architect* that generates and iterates pipeline configurations. These are orthogonal uses; both can coexist.

### 2.3 Agent-Driven Hardware Design with Verification

**Architect in the Loop (Dec 2024, arXiv 2512.00016)** — Blueprint-driven agent for processor design and verification. JSON blueprint → SystemVerilog + cocotb → Verilator linting → functional tests → FPGA. Achieved ~80% automation of the design-verify cycle. Identified the "semantic cohesion gap" — the LLM's generated designs drift from the specification as complexity grows.

- **Consistency**: Strongest structural parallel to our architecture. Both use: (1) a structured blueprint the agent works from, (2) deterministic verification gates, (3) a promote-or-iterate loop. Their "semantic cohesion gap" warning directly motivates our P3 (mechanical rejection) and HCS constraint checking.

### 2.4 Formal Tool Verification for Agents

**ToolGate (Jan 2026, arXiv 2601.04688, ACL Findings 2026)** — Introduces Hoare-style contracts `{Precondition} tool {Postcondition}` for LLM tool execution. Precondition filtering prevents invalid tool calls; postcondition verification catches incorrect outputs; trajectory constraints enforce global invariants.

- **Consistency**: Provides the theoretical foundation for our harness tools. Each harness function (`run_pipeline`, `validate_constraints`, `export_gnuradio`) can be formalized as a ToolGate contract. The `validate_constraints()` function is a direct implementation of ToolGate's precondition filtering pattern.

### 2.5 Domain Knowledge Injection for RF

**RF-Agent (Jul 2026, arXiv 2607.18772)** — Textbook-driven knowledge distillation for RF circuit reasoning. Extracted 11,000+ Q&A samples from seven RF textbooks to build a domain-specific context for LLM agents.

- **Consistency**: Validates our Domain Context package approach (DSP primitives catalog). RF-Agent demonstrates that curated, domain-specific context dramatically improves agent performance over general-purpose prompting.

### 2.6 Multi-Agent RF Design

**RFAmpDesigner (2025, arXiv 2605.10093)** — Multi-agent self-evolving framework for RF amplifier design with simulation feedback loops.

- **Consistency**: Validates the agent + simulation-feedback pattern. Our architecture uses a single agent with deterministic gates rather than multi-agent negotiation, which is a deliberate simplification for auditability (P2).

### 2.7 Autonomous Scientific Experimentation

**ORNL Autonomous Experiments (2025–2026)** — AI agents driving autonomous experiments at HPC and manufacturing facilities. Agent controls physical instruments, collects measurements, adjusts parameters. Safety measures and human override protocols built into the loop.

- **Consistency**: Validates the broader pattern of agent-driven experimentation with safety gates. Our architecture applies the same pattern to DSP pipeline design rather than physical experiments, with HCS constraints serving the role of safety boundaries.

### 2.8 LLM Scientific Code Generation

**GPT-4.1 Automated Experiment Design (2025, arXiv 2508.00033)** — Evaluated LLMs generating scientific Python for experiment design. Performance varies significantly by library familiarity — LLMs perform best with libraries heavily represented in training data.

- **Consistency**: Directly supports the SciPy choice. SciPy and NumPy are among the most represented scientific libraries in LLM training corpora, giving the agent the highest probability of generating correct code.

---

## 3. Gaps — What Does Not Exist Yet

### 3.1 No Published DSP Pipeline-Design Agent

No published work combines all three elements: (1) an LLM agent that *designs* DSP pipelines (not classifies signals), (2) a governed experiment loop with deterministic gates, and (3) a two-tier tool stack (exploration + validation) integrated into a formal lifecycle methodology. The closest parallel (Architect in the Loop) operates on processor RTL, not DSP signal chains.

### 3.2 No SciPy-to-GNU-Radio Translation Framework

The `export_gnuradio()` harness tool — which maps a validated SciPy pipeline to a GNU Radio Python API flowgraph — has no published precedent. Existing GNU Radio MCP servers (found on GitHub, e.g., `SimpliRF/gnuradio-mcp-server`) operate on `.grc` files or the GRC XML schema, not on SciPy-to-block translation.

### 3.3 No HCS-Driven Constraint Checking for Agent DSP

While ToolGate provides the theoretical framework for precondition/postcondition contracts on tools, no published work applies this specifically to hardware constraint checking in the SDR domain. The `HardwareConstraints` dataclass pattern is novel.

### 3.4 No V-Model Integration for Agent-Driven DSP

Existing agent-for-hardware work (Architect in the Loop) does not embed the agent loop into a V-model lifecycle. The integration of the DSP experiment pipeline into V-SIL's Ctx 02 stage, with traceability from experiment log to Ctx 03 design contract, is novel.

---

## 4. Why SciPy.signal for Exploration (Not GNU Radio)

The choice of Python + SciPy as the *primary* exploration layer, with GNU Radio reserved for validation, is grounded in four arguments:

### 4.1 LLM Code Generation Reliability

LLMs generate Python with dramatically higher reliability than C, C++, Rust, or Lua. Benchmarks from "Beyond pass@1" (arXiv 2603.29231) show that compound reliability decays geometrically: `(1-ε)^T` for T independent steps, where even a 5% per-step error rate yields only 59.9% reliability over 10 steps. Choosing the language with the lowest per-step error rate is the single most effective mitigation.

SciPy/NumPy are among the most heavily represented scientific libraries in LLM training data (GPT-4.1 Automated Experiment Design confirms this). The agent generating `scipy.signal.firwin(numtaps=64, cutoff=0.3)` is far more likely to produce correct code than generating equivalent C for liquid-dsp or Rust for FutureSDR.

### 4.2 Iteration Speed

SciPy pipelines execute immediately — no compilation, no linking, no build system. The agent can run dozens of experiments per minute on synthetic I/Q data. GNU Radio flowgraphs, while usable from Python, carry overhead: block instantiation, buffer allocation, scheduler startup. This overhead is acceptable for validation (run once per promoted design) but wasteful for exploration (run many times per hypothesis).

### 4.3 Determinism on Fixed Data

SciPy operations on fixed NumPy arrays are deterministic and reproducible across platforms. The same filter applied to the same I/Q vector produces the same output every time. This is essential for the experiment log's traceability guarantee — a logged experiment can be reproduced exactly. GNU Radio's block scheduler introduces non-deterministic buffer behavior that, while realistic, complicates reproducibility at the exploration stage.

### 4.4 Inspection and Debugging

SciPy pipelines are transparent: every intermediate array can be inspected, plotted, and compared. When an experiment fails the metrics gate, the agent can examine where in the pipeline the signal degraded. GNU Radio flowgraphs are opaque at the block boundary — intermediate signals require probe blocks and additional instrumentation.

---

## 5. Why GNU Radio for Validation (Not SciPy Alone)

SciPy is necessary but not sufficient. Pure SciPy exploration misses several phenomena that matter for real SDR deployment:

### 5.1 Block Scheduling and Buffer Management

GNU Radio's runtime scheduler manages block execution order, buffer sizes, and data flow between blocks. A pipeline that works perfectly as sequential NumPy array operations may fail under GNU Radio's streaming model due to buffer overflows, underruns, or scheduling starvation. Validating in GNU Radio catches these issues before they reach hardware.

### 5.2 Realistic Sample-Rate Behavior

GNU Radio enforces sample-rate propagation through the flowgraph. A decimation block that changes the rate must be matched by downstream blocks expecting the new rate. SciPy operations on arrays do not enforce this — the programmer can silently process data at the wrong rate. GNU Radio validation catches rate mismatches.

### 5.3 SIL Fidelity

The V-SIL CI+SIL test levels (Unit, Integration, System) all run against GNU Radio with Mock HAL and synthetic I/Q. Validating the DSP design in the same environment as the CI tests ensures consistency. A design validated only in SciPy could pass exploration but fail CI+SIL integration tests due to framework-specific behavior.

### 5.4 Direct Path to HIL

GNU Radio flowgraphs connect to real hardware through SoapySDR and UHD drivers. A design validated in GNU Radio can be deployed to HIL testing with minimal changes. A design that exists only as SciPy code requires a complete rewrite to reach hardware.

---

## 6. Why NOT liquid-dsp

liquid-dsp (J. Gaeddert, MIT license) is a mature, high-performance C library for DSP on embedded and real-time systems. It is an excellent *deployment* target but a poor *exploration* tool for an LLM agent:

### 6.1 Language Barrier

liquid-dsp is written in C. LLM code generation for C is significantly less reliable than for Python — more syntax errors, more memory management bugs, more undefined behavior. The compound reliability argument (Section 4.1) applies with even greater force: C code generation has a higher per-step error rate `ε`, making multi-step pipeline generation unreliable.

### 6.2 No Python API

liquid-dsp has no official Python binding. The agent would need to either: (a) generate C code and compile it per experiment — introducing build failures as a new error mode, or (b) use unofficial wrappers (e.g., `pyliquid`) that are incomplete and unmaintained. Neither path is viable for rapid iteration.

### 6.3 Compilation Overhead

Every experiment would require a compile-link cycle. For an agent running dozens of experiments, this adds latency and introduces a class of errors (build failures, linker errors) that are orthogonal to the DSP design problem being explored.

### 6.4 Designed for Deployment, Not Exploration

liquid-dsp optimizes for runtime performance: fixed-point arithmetic, SIMD intrinsics, cache-friendly memory layouts. These are virtues in a deployed system but irrelevant during exploration, where the goal is *algorithmic* evaluation on synthetic data. The exploration layer needs expressiveness and transparency (SciPy), not throughput.

### 6.5 Appropriate Role

liquid-dsp could serve as an *additional* deployment target below the HIL layer — once a design is validated in GNU Radio, it could be re-implemented in liquid-dsp for embedded deployment. This is outside the scope of the DSP Experiment Pipeline, which ends at promotion to Ctx 03.

---

## 7. Why NOT FutureSDR

FutureSDR is a Rust-based SDR framework emphasizing async runtimes and modern systems programming.

### 7.1 Rust Code Generation

LLM Rust code generation is the least reliable among mainstream languages. Rust's ownership system, lifetime annotations, and borrow checker produce errors that LLMs systematically fail to resolve. The per-step error rate for Rust DSP code would make compound reliability catastrophically low.

### 7.2 Immature Ecosystem

FutureSDR's block library is significantly smaller than GNU Radio's. Many standard DSP operations available as GNU Radio blocks or SciPy functions would need to be implemented from scratch.

### 7.3 No Python Integration

FutureSDR has no Python API. The agent cannot generate FutureSDR pipelines without generating Rust — the least LLM-friendly language for this task.

---

## 8. Why NOT LuaRadio

LuaRadio is a lightweight, Lua-based SDR framework.

### 8.1 Tiny LLM Training Corpus

Lua is dramatically underrepresented in LLM training data compared to Python. LuaRadio-specific code is even rarer. The agent would be generating code in a domain (DSP) using a language (Lua) with minimal training representation — a recipe for high error rates.

### 8.2 Limited Ecosystem

LuaRadio's block library and community are much smaller than GNU Radio's. Integration with hardware drivers is less mature. It offers no advantage over GNU Radio for validation and no advantage over SciPy for exploration.

---

## 9. Warnings from Literature

### 9.1 Compound Reliability Decay

"Beyond pass@1" (arXiv 2603.29231) quantifies the fundamental threat: for T independent steps with per-step error rate ε, reliability decays as `(1-ε)^T`. With correlated errors (correlation ρ), the decay is faster: `exp(-εT - ρε²T(T-1)/2)`. For a 10-step DSP pipeline with ε=0.05, reliability drops to ~60%. With ρ=0.3, it drops further.

**Mitigation in our architecture**: P3 (mechanical rejection) and the HCS constraint gate catch errors early, reducing effective T. The experiment loop allows the agent to iterate, so reliability is measured across attempts, not within a single attempt.

### 9.2 Verification Gap

Survey evidence (arXiv 2608.05179) shows ~83% of autonomous agents publish code, but only ~38% produce reproducible artifacts. The gap between "generated" and "verified" is the central risk of any agent-driven engineering.

**Mitigation**: The architecture addresses this directly — the entire pipeline is designed around verification. No experiment is promoted without passing constraint validation, GNU Radio SIL validation, and metrics thresholds. The experiment log provides full traceability.

### 9.3 Semantic Cohesion Gap

Architect in the Loop (arXiv 2512.00016) warns that LLM-generated designs drift from their specifications as complexity grows. The agent's internal model of the design diverges from the actual generated artifact.

**Mitigation**: The DSP primitives catalog (Domain Context) constrains the design vocabulary — the agent selects from known blocks rather than inventing novel operations. HCS constraints bound the parameter space. These reduce the room for semantic drift.

### 9.4 MOP Paradox

"Beyond pass@1" documents the Meltdown of Performance paradox: the strongest models exhibit the highest meltdown rates (19%) — when they fail, they fail catastrophically rather than gracefully. This means that even improving the LLM does not eliminate the need for external verification.

**Mitigation**: P3 exists precisely for this reason. Mechanical rejection gates are immune to the MOP paradox because they do not involve LLM judgment.

---

## 10. Summary Table

| Dimension | Status | Key Reference |
|---|---|---|
| LLM + GNU Radio orchestration | Exists (GRCon25) | Paul David, SimpliRF |
| LLM as DSP pipeline *designer* | **Novel** | — |
| Agent + deterministic verification | Exists (hardware domain) | Architect in the Loop |
| Formal tool contracts | Exists (general) | ToolGate, ACL 2026 |
| Domain context injection for RF | Exists | RF-Agent |
| SciPy→GNU Radio translation | **Novel** | — |
| HCS constraint checking for agents | **Novel** | — |
| V-model integration for agent DSP | **Novel** | — |
| Compound reliability risk | Well-documented | Beyond pass@1 |
| Verification gap risk | Well-documented | arXiv 2608.05179 |

---

## 11. Conclusion

The architecture is **consistent** with existing literature in its individual patterns — agent-driven exploration, deterministic verification gates, domain context injection, and tool contracts all have published precedent. The architecture is **novel** in its specific combination: no published work applies these patterns to DSP pipeline design for SDR within a governed lifecycle methodology.

The choice of SciPy for exploration and GNU Radio for validation is **well-supported**: LLM code generation reliability, iteration speed, and the existing training corpus all favor Python/SciPy as the exploration layer, while GNU Radio's realistic scheduling, rate propagation, and hardware connectivity make it the necessary validation layer.

The warnings from literature — compound reliability decay, verification gap, semantic cohesion gap, and the MOP paradox — are **directly addressed** by the architecture's governing principles (P1–P4) and its mechanical rejection gates (P3). The architecture does not assume LLM reliability; it assumes LLM unreliability and builds verification around it.

---

## References

1. Paul David, "Powering Cognitive Radio with LLMs," GRCon25, Sep 2025. [PDF](https://events.gnuradio.org/event/26/contributions/750/attachments/221/598/grcon25_paper_paul_david.pdf)
2. RF-GPT, Khalifa University, Feb 2026. arXiv:2602.14833
3. RadioLLM, Jan 2025. arXiv:2501.17888
4. "Architect in the Loop," Dec 2024. arXiv:2512.00016
5. ToolGate, Jan 2026. arXiv:2601.04688 (ACL Findings 2026)
6. RF-Agent, Jul 2026. arXiv:2607.18772
7. RFAmpDesigner, 2025. arXiv:2605.10093
8. ORNL Autonomous Experiments, 2025–2026.
9. "Beyond pass@1," Mar 2026. arXiv:2603.29231
10. Verification Gap Survey, 2025–2026. arXiv:2608.05179
11. GPT-4.1 Automated Experiment Design, 2025. arXiv:2508.00033

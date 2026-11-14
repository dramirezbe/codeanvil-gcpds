# V-SIL v4: Agile-V Stage-Gate Lifecycle for COTS-Constrained Verified Prototype Development

**David Ramírez-Betancourt** — Universidad Nacional de Colombia, GCPDS  
**Version:** 4.0-draft  
**Date:** November 2026

---

## Abstract

V-SIL v4 extends v3 by inserting an **Agile-V module-planning layer** between system design and implementation. It receives a finalised Build Package (PRD with measurable constraints, COTS hardware envelope, acceptance criteria and, optionally, laboratory procedures, hardware calibration at the development team's screening grade, and tolerances in dBi) and delivers a Verified Prototype with per-module and end-to-end evidence — or, when the requirements are infeasible on the declared COTS platform, a formal Request for Deviation (RFD) with trade-off analysis.

The v3 chain S0→G0→S1→G1→S2→G2 becomes the v4 chain **S0→G0→S1→G1→S2→G2→S3→G3**, where S2 is a new module-planning stage, G2 is a new micro-gate, S3 is the renamed implementation stage (v3 S2), and G3 is the renamed verification gate (v3 G2). Nothing from v3 is lost; the new layer solves context loss in large systems by giving each module a self-contained plan that carries only the contracts and traced requirements it needs.

S1 may design one subsystem or a system of subsystems: each subsystem has its own layered base and modules, and subsystems meet through versioned contracts. S1 declares a HAL mode, `mock-only` or `mock+real`. It always designs a **Mock HAL** that generates deterministic and synthetic data for VL-0 and VL-1, and a mandatory **telemetry companion** that silently monitors the compute unit during all test executions and is never shipped. Only in `mock+real` does it add a **Real HW HAL** that interfaces with the physical hardware for laboratory dataset generation and field tests at VL-2. An ML model is an optional S1 input when the chosen design uses one. Implementation proceeds module by module within each subsystem and then across subsystem boundaries, each module built in a **fresh context** that carries only its PLAN.md and the contracts it touches. Verification depth is adaptive per module, while a mandatory floor of unit, sandwich-integration, cross-subsystem contract, and system-path tests applies. Every claim names the verification level and environment at which it was produced; the telemetry companion attaches compute-unit state to every evidence record. The terminal output may record scoped future work for later software versions; this does not defer current acceptance criteria.

Terminology is aligned with IEEE/ISO/IEC 29119, ISO 26262, SDAD [6], the Coordinator-Implementor-Verifier pattern [10], the embedded HAL mock→SIL→HIL substitution ladder [11], the ECSS/MIL-HDBK-61A Request for Deviation process [16][17], the Agile-V compliance framework [19], and the OpenSpec delta traceability model [21].

```mermaid
flowchart LR
    classDef input fill:#f3f4f6,stroke:#6b7280,color:#1f2937,stroke-width:2px
    classDef vsil fill:#e0f2fe,stroke:#0284c7,color:#0c4a6e
    classDef output fill:#dcfce7,stroke:#16a34a,color:#14532d,stroke-width:2px
    classDef rfd fill:#fee2e2,stroke:#dc2626,color:#7f1d1d,stroke-width:2px

    IN["Build Package<br/>PRD · COTS envelope · acceptance criteria<br/>optional: lab procedures · calibration · tolerances"]:::input
    VSIL["V-SIL v4<br/>S0 → G0 → S1 → G1 → S2 → G2 → S3 → G3"]:::vsil
    OUT["Verified Prototype<br/>module + system-path VL evidence"]:::output
    RFD["Request for Deviation<br/>infeasibility evidence<br/>+ trade-off options"]:::rfd

    IN --> VSIL
    VSIL -->|nominal| OUT
    VSIL -.->|infeasible| RFD
    RFD -.->|updated Build Package| IN
```

---

## 1 What Changed from v3 to v4

### 1.1 Motivation

Large verified systems decompose into many modules. When an agent (human or AI) implements module N, it must hold the full system design, the Ground Truth, and the accumulated state of modules 1…N−1 in its working context. As the system grows, context is lost, contracts are misread, and traced requirements drift from the design. V-SIL v3 has no mechanism to scope the working context to the module being built.

V-SIL v4 solves this by inserting a **module-planning stage (S2)** and its **micro-gate (G2)** between the system design (S1/G1) and implementation (now S3). Each module receives a self-contained plan (PLAN.md) that carries only the information the implementor needs: its traced requirements, its interface contracts, its ordered tasks, and its verification plan. The implementor works from this plan in a fresh context, not from the full system design.

### 1.2 New governing principles

The v3 principles P1–P4 are unchanged. V4 adds:

**P5.** Module is the iteration unit — the Agile-V backlog is a sequence of modules ordered by topological dependency, not by priority or story points.  
**P6.** Layers are orthogonal to iteration — the layered architecture is a structural invariant; Agile-V determines only the order in which modules are built.  
**P7.** Fresh context per module — each module is implemented in an isolated context that carries only its PLAN.md and the contracts it touches; no accumulated implementation state leaks across modules.  
**P8.** Living GT with delta traceability — each module's plan records which GT requirements it adds, modifies, or removes (OpenSpec-style ADDED/MODIFIED/REMOVED deltas [21]), so the system-level GT stays current without a monolithic re-review.

### 1.3 Stage renumbering

| v3 stage | v4 stage | Change |
|---|---|---|
| S0 — Normalisation + GT | **S0** — Normalisation + GT | Unchanged |
| G0 — Structural validation | **G0** — Structural validation | Unchanged |
| S1 — System design | **S1** — System design + module decomposition | Enhanced: explicit module identity, dependency graph for topological ordering |
| G1 — Design review | **G1** — Design review | Enhanced: checks 11–12 added (module decomposition, topological slicing) |
| *(none)* | **S2** — Module planning | **NEW**: Agile-V backlog, PLAN.md per module, delta traceability |
| *(none)* | **G2** — Module plan micro-gate | **NEW**: 6 checks, 4 verdicts |
| S2 — Implementation | **S3** — Per-module implementation | Renamed; enhanced with fresh-context protocol (P7) |
| G2 — Adaptive verification | **G3** — Adaptive verification | Renamed; enhanced with plan-defect routing back to S2 |

---

## 2 Terminology

| Informal term | Standard term | Source |
|---|---|---|
| Propagation test (base → modules with placeholders) | **Top-down integration test with stubs** | IEEE 29119; Pressman [1] |
| Backpropagation test (module → base) | **Bottom-up integration test with drivers** | IEEE 29119; Pressman [1] |
| Combined propagation + backpropagation | **Sandwich (hybrid) integration testing** | IEEE 29119 [2] |
| Placeholders | **Stubs** (called by the unit under test) | Standard SE |
| Test harnesses simulating callers | **Drivers** (call the unit under test) | Standard SE |
| Router validation | **Interface-contract verification** | Contract testing [3]; Bass et al. [4] |
| Design by layers | **Layered architecture** with **component dependency graph** (DAG) | Bass et al. [4] |
| Levels N0 / N1 / N2 | **Verification levels** (VL-0, VL-1, VL-2) | Adapted from ISO 26262 [5] |
| Feedback to Build Package with trade-off | **Request for Deviation (RFD)** | ECSS [16]; MIL-HDBK-61A [17]; NASA NPR 7150.2 [18] |
| Module backlog ordering | **Topological slicing** | Agile-V [19]; dependency-graph ordering |
| Module plan | **PLAN.md** — self-contained module specification | V-SIL v4 |
| Requirement delta | **ADDED / MODIFIED / REMOVED** delta annotation | OpenSpec [21] |

---

## 3 Stage-Gate Overview

```mermaid
flowchart TD
    classDef stage fill:#e0f2fe,stroke:#0284c7,color:#0c4a6e
    classDef gate fill:#dcfce7,stroke:#16a34a,color:#14532d
    classDef newstage fill:#ede9fe,stroke:#7c3aed,color:#3b0764
    classDef newgate fill:#fce7f3,stroke:#db2777,color:#831843
    classDef terminal fill:#e0f2fe,stroke:#0284c7,color:#0c4a6e,stroke-width:3px
    classDef input fill:#f3f4f6,stroke:#6b7280,color:#1f2937,stroke-width:2px
    classDef rfd fill:#fee2e2,stroke:#dc2626,color:#7f1d1d

    BP["Build Package"]:::input
    S0["S0 — Normalisation + GT"]:::stage
    G0{"G0 — Structural validation"}:::gate
    S1["S1 — Subsystem topology + layered design<br/>+ module decomposition"]:::stage
    G1{"G1 — Design review (HITL)"}:::gate
    S2["S2 — Module planning<br/>(Agile-V backlog + PLAN.md)"]:::newstage
    G2{"G2 — Module plan micro-gate"}:::newgate
    S3["S3 — Per-module implementation<br/>(fresh context per module)"]:::stage
    G3{"G3 — Adaptive verification"}:::gate
    T["Verified Prototype<br/>module + system-path VL evidence"]:::terminal
    RFD["RFD<br/>Request for Deviation"]:::rfd

    BP --> S0
    S0 --> G0
    G0 -->|PASS + Gate H| S1
    S1 --> G1
    G1 -->|PASS| S2
    S2 --> G2
    G2 -->|PASS| S3
    S3 --> G3
    G3 -->|PASS| T

    G0 -.->|FAIL| S0
    G1 -.->|FAIL| S1
    G2 -.->|FAIL| S2
    G3 -.->|design| S1
    G3 -.->|plan defect| S2
    G3 -.->|module| S3

    S1 -.->|infeasible| RFD
    G1 -.->|infeasible| RFD
    G3 -.->|infeasible| RFD
    RFD -.->|updated| BP
```

**Governing principles.**

**P1.** HITL is an authorisation barrier; HIL is a validation barrier.  
**P2.** Oracle ≠ generator — the model never approves its own work [7].  
**P3.** G0 is the only deterministic gate: its mechanical rejection beats any approval [8]. Every other gate verdict is human (HITL).  
**P4.** *Verified* ≠ *validated* — claims name the environment [9].  
**P5.** Module is the iteration unit — the Agile-V backlog is ordered by topological dependency [19].  
**P6.** Layers are orthogonal to iteration — layered architecture is a structural invariant; Agile-V is the iteration order.  
**P7.** Fresh context per module — the implementor carries only PLAN.md and the contracts it touches.  
**P8.** Living GT with delta traceability — ADDED/MODIFIED/REMOVED per module [21].

---

## 4 S0 — Normalisation and Ground Truth

```mermaid
flowchart LR
    classDef input fill:#f3f4f6,stroke:#6b7280,color:#1f2937
    classDef process fill:#ede9fe,stroke:#7c3aed,color:#3b0764
    classDef output fill:#e0f2fe,stroke:#0284c7,color:#0c4a6e

    BP["Build Package<br/>Obligations · COTS · QA<br/>optional: lab procedures · calibration · tolerances"]:::input
    FILL["Fill IEEE 29148<br/>blueprints"]:::process
    StRS["G0_StRS.md<br/>§9.4"]:::output
    SyRS["G0_SyRS.md<br/>§9.5 · lab inputs in §4–§6 (optional)"]:::output

    BP --> FILL
    FILL --> StRS
    FILL --> SyRS
```

S0 **normalises only** — it casts the Build Package content into the IEEE 29148 [12] document blueprints and makes no conceptual judgement about sufficiency or scope. The produced documents carry only the filled specification, not the blueprint's author-guidance sections or empty placeholder rows, so a template example block is never read as a requirement. Following SDAD Phase 1 (spec crystallisation) [6], it populates the blueprints:

- **G0_StRS.md** — Stakeholder Requirements Specification (§9.4): `NRM-*`, `HWC-*`, `STK-*` blocks.
- **G0_SyRS.md** — System Requirements Specification (§9.5): `SYS-*` blocks tracing to StRS.

Laboratory procedures, calibration, and tolerances are optional Build Package content. When present, S0 casts them into the SyRS sections that already exist for them: procedures into §6 Field Measurement Protocols (`PROTO-*`: setup, calibration, execution), calibration terms into §4 Correction Chains, and tolerances into §5 Uncertainty Budgets. The three headings stay required by G0; with no lab inputs, each holds exactly `Not applicable: no lab inputs in the Build Package.`

Any iteration happens afterwards at G0, which validates the Build Package content against the deterministic gate (the blueprint) — not by a review judgement here.

---

## 5 G0 — Structural Validation

```mermaid
flowchart TD
    classDef doc fill:#e0f2fe,stroke:#0284c7,color:#0c4a6e
    classDef phase fill:#f0fdf4,stroke:#16a34a,color:#14532d
    classDef gate fill:#dcfce7,stroke:#16a34a,color:#14532d
    classDef fail fill:#fee2e2,stroke:#dc2626,color:#7f1d1d

    StRS["G0_StRS.md"]:::doc
    SyRS["G0_SyRS.md"]:::doc
    SCRIPT["g0_validate.py<br/>deterministic · stdlib-only · no AI"]:::phase
    P1["Headings"]:::phase
    P2["Metadata"]:::phase
    P3["Block fields"]:::phase
    P4["Cross-doc G0-X"]:::phase
    G0{"G0"}:::gate
    PASS["PASS → Gate H"]:::gate
    FAIL["FAIL → edit GT"]:::fail

    StRS & SyRS --> SCRIPT
    SCRIPT --> P1 & P2 & P3 & P4
    P1 & P2 & P3 & P4 --> G0
    G0 -->|exit 0| PASS
    G0 -->|exit 1| FAIL
    FAIL -.->|validate vs original Build Package| S0_
    S0_["S0"]:::doc
```

Deterministic. No AI. Binary verdict. After G0 passes, human Gate H asks: *Requirements complete, bounded, and verifiable?*

---

## 6 S1 — System of Layered Subsystems with Module Decomposition

S1 first divides the product into independently deployed subsystems when the requirements call for them. One subsystem remains a valid special case. A **subsystem** owns a runtime, deployment target, base layer, modules, and externally visible ports. Its modules communicate through its own base-layer interfaces; a cross-subsystem exchange goes through a declared, versioned subsystem contract. Splitting a UI from an edge process is justified when they deploy or restart independently, communicate over a network, or have distinct failure domains.

### 6.1 System topology and requirement allocation

The arrows below are **runtime messages**, not implementation dependencies.

```mermaid
flowchart LR
    GT["One StRS + SyRS pair"] --> MAP["SYS-* allocated to subsystems and paths"]
    MAP --> EDGE["Edge subsystem<br/>COTS SDR + local base + modules"]
    MAP --> UI["UI subsystem<br/>client base + modules"]
    EDGE -->|"occupancy.v1: measurements"| UI
    UI -->|"configure.v1: commands"| EDGE
```

The system view records each subsystem's responsibility, deployment target, COTS resources, network link, and lifecycle. A requirement may map to one subsystem or to an **end-to-end path** spanning several subsystems. One system-level trace table owns this allocation; subsystem designs do not duplicate the Ground Truth. Cross-subsystem contracts specify producer and consumer, schema and version, units, timestamps, ordering, rate, latency, authentication, retries, duplicate handling, and behavior on disconnect or restart where applicable.

### 6.2 Layered architecture within each subsystem

```mermaid
flowchart TD
    classDef base fill:#dbeafe,stroke:#2563eb,color:#1e3a8a
    classDef mod fill:#e0e7ff,stroke:#4f46e5,color:#312e81
    classDef integ fill:#dbeafe,stroke:#2563eb,color:#1e3a8a

    subgraph ARCH["S1 produces for each subsystem"]
        direction TD
        BASE["Base Layer<br/>Orchestration · HAL · data routing<br/>interface contracts"]:::base
        subgraph MODS["Modules"]
            direction LR
            M1["M1"]:::mod
            M2["M2"]:::mod
            M3["M3"]:::mod
            MN["MN"]:::mod
        end
        INT["Integration<br/>Modules wired through base-layer interfaces"]:::integ
    end

    BASE --> MODS --> INT
```

Modules are plug-in units communicating only through their subsystem's base layer and declared interfaces. No direct module-to-module calls, and no cross-subsystem calls that bypass a subsystem contract. A subsystem without physical hardware can have an empty HAL; its base still owns orchestration and routing.

### 6.3 Module identity and dependency graph

**New in v4.** S1 now assigns each module a unique identity and declares the implementation dependency graph that S2 will use for topological slicing.

```mermaid
flowchart LR
    classDef hal fill:#fee2e2,stroke:#dc2626,color:#7f1d1d
    classDef dsp fill:#fef3c7,stroke:#d97706,color:#78350f
    classDef dec fill:#dcfce7,stroke:#16a34a,color:#14532d
    classDef out fill:#e0f2fe,stroke:#0284c7,color:#0c4a6e

    HW["HackRF"]:::hal
    IQ["iq_acquisition<br/>VL-2 · HAL"]:::hal
    FFT["fft_engine<br/>VL-1 · DSP"]:::dsp
    FE["feature_extractor<br/>VL-1 · DSP"]:::dsp
    CL["classifier<br/>VL-0 · Decision"]:::dec
    DEM["audio_demod<br/>VL-1 · Output"]:::out
    DS["data_store<br/>VL-0 · Output"]:::out

    HW -->|raw RF| IQ
    IQ -->|raw_iq| FFT
    IQ -->|raw_iq| DEM
    FFT -->|psd_estimate| FE
    FE -->|channel_features| CL
    CL -->|occupancy_decision| DS
```

Each edge carries an **interface contract** (data type, schema version, units, latency). Each subsystem's implementation dependency graph must be acyclic. Each node carries a **verification profile**: `module_id`, `subsystem_id`, `layer`, `depends_on`, `provides`, `hw_dependency`, `required_vl`. `hw_dependency` means correctness requires a specific physical device or behavior, rather than merely that the code runs on a computer.

The **implementation dependency graph** orders contract definition, subsystem bases, modules, and system integration. It must be acyclic so S3 can build with stubs. The separate **runtime interaction graph** describes live messages. It may contain intentional loops, such as edge telemetry → UI → edge control, provided the contracts define ownership of state, acknowledgement, timeouts, and safe behavior. Runtime message loops do not create implementation dependency cycles.

Each module now also carries a **module identity block** used by S2:

| Field | Description |
|---|---|
| `module_id` | Unique identifier (e.g. `fft_engine`) |
| `subsystem_id` | Parent subsystem |
| `layer` | Architectural layer (HAL, DSP, Decision, Output, …) |
| `depends_on` | List of modules whose contracts this module consumes |
| `provides` | List of interface contracts this module produces |
| `hw_dependency` | `true` / `false` |
| `required_vl` | VL-0, VL-1, or VL-2 |
| `traced_reqs` | List of `SYS-*` requirements allocated to this module |

| Module | Layer | HW dep. | Required VL | Traced reqs |
|---|---|---|---|---|
| `iq_acquisition` | HAL | **yes** | VL-2 (HIL) | SYS-001 |
| `fft_engine` | DSP | no | VL-1 (SIL) | SYS-002, SYS-003 |
| `feature_extractor` | DSP | no | VL-1 (SIL) | SYS-004 |
| `classifier` | Decision | no | VL-0 (unit) | SYS-005 |
| `audio_demod` | Output | no | VL-1 (SIL) | SYS-006 |
| `data_store` | Output | no | VL-0 (unit) | SYS-007 |

### 6.4 Optional supplied ML model

**Status: uncertain.** This version defines the ML model only as an optional S1 input and a G1 readiness check. Its connection to S3 and G3 (training data generation, inference adapter, measurement at G3) is not implemented and is future work, together with MLOps (FW-005).

An S1 design includes this box **only when it chooses an ML-based module or the Ground Truth explicitly requires one**. Otherwise the box and its G1 check are absent. The supplied model is a controlled input to a subsystem module, not a subsystem by itself. It is trained with Mock HAL data plus labelling or, failing that, with Real HW HAL data plus labelling. S1 does not train or select a model on behalf of the Build Package author.

When used, S1 identifies the model file and weights by version and digest; names its supplying owner and provenance; records the training data source and labelling procedure; specifies the inference runtime, input and output schema, units, preprocessing, labels or thresholds, and postprocessing; and records the supplied performance metadata with its evaluation dataset and conditions. It budgets inference latency, memory, and any device dependency on the declared COTS target. A deterministic fake model response supports VL-0 integration, while later levels exercise the actual supplied model.

Supplied performance metadata is prior evidence, not a G3 verdict. If S1 chooses ML but the model package or the fields needed to implement it are missing, G1 returns **FAIL** for completion of the input or design. Demonstrated infeasibility against the declared COTS requirements follows the RFD route. Automating this model lifecycle with MLOps is future work (FW-005).

### 6.5 HAL substitution ladder and telemetry companion

S1 declares the **HAL mode** in the design Meta: `HAL mode: mock-only` or `HAL mode: mock+real`. Every later stage reads it from the design. The HAL implementations share the same base-layer interface contract but differ in what produces `raw_iq`:

- **Mock HAL** (mandatory in every mode). A software-only signal generator. At VL-0 it emits deterministic vectors (short, repeatable, edge-case coverage). At VL-1 it produces synthetic I/Q files at known SNR, modulation, and channel conditions using an FM-modulated software synthesiser or recorded golden captures. Each golden vector is versioned with a SHA-256 digest, generation parameters, the condition it simulates, and its expected output. The Mock HAL is the default data source for all sandwich-integration and SIL tests.

- **Real HW HAL** (only in `mock+real`). The production HAL that interfaces with the declared COTS SDR. It serves two purposes: (a) executing the laboratory procedures recorded in the SyRS (§6 `PROTO-*`) to generate **real datasets** with the development team's calibration quality (screening grade, not normative, SyRS §4 Correction Chains) and declared tolerances in dBi (SyRS §5 Uncertainty Budgets); and (b) running the final field tests at VL-2. The calibration grade and tolerances are inputs recorded in the SyRS, not claims of V-SIL. The Real HW HAL may be declared at VL-0 (fake device API) for a cycle, so the software for the real hardware is built without validating metrics on it; G3.2 then does not fire and the honesty declaration states it.

In `mock-only`, the design has no Real HW HAL, no lab procedures, calibration, or tolerances, and no module with `hw_dependency: true`; it ignores SyRS §4–§6, and every claim is capped at VL-1 (§12.2). In `mock+real`, both HALs plug into the same base-layer port; swapping one for the other is the **HAL substitution** that moves between verification levels [11].

S1 also specifies a **telemetry companion**, mandatory in every design and every test run: a lightweight, non-intrusive process that runs alongside every test execution and records compute-unit state — CPU utilisation, available memory, temperature, dropped buffers, and scheduling latency. It must not interfere with the system under test; its own resource footprint is declared and bounded. The companion attaches its readings to every evidence record so that G3 can determine whether the compute unit was within its operating envelope during a test. The telemetry companion is verification infrastructure, not a system module: it belongs to the methodology, not to the software. It has no `SYS-*`, does not appear in the implementation DAG, is absent from the Verified Prototype's module evidence, and is never shipped in the delivered software.

The Mock HAL, the golden vectors with their manifest, the telemetry companion, the stubs, the fake peers, and the drivers form the **verification kit**. S3 builds the kit in its initial layer, before any module, together with the Real HW HAL and its fake device API in `mock+real` (§11).

S1's design Meta also declares one **`Toolchain`** entry per subsystem: `SUB-xxx: <package> · <language> · <package manager> · <test runner>`, for example `SUB-001: fm_edge · Python 3.12 · uv · pytest; SUB-002: dashboard · TypeScript · pnpm · vitest`. `<package>` is a valid identifier and names `src/<package>/`. This version allows Python with uv and pytest, and TypeScript with pnpm and vitest. S3 builds with the declared toolchain and never chooses another; an empty or incomplete `Toolchain` is a design defect.

---

## 7 G1 — Subsystem, Dependency, Contract, and Module-Decomposition Validation

G1 answers: *Are all implementation-critical design choices resolved, and is every module identifiable and plannable?*

G1 is a human (HITL) design review, not a deterministic gate. An agent may prepare the review and recommend a verdict, including an RFD; the human decides.

G1 runs no script. The agent that prepares it validates by itself: it reads the whole design and the GT, re-derives every check from the source sections instead of trusting the design's own summaries, and runs the declared toolchain on the development machine. A thorough review is worth its token cost. The agent's findings inform the human; they never become an automatic verdict.

1. **Subsystem topology.** Every subsystem has one responsibility, deployment target, owner of state, and declared external ports; the network and COTS envelope support the topology.
2. **Implementation DAG acyclicity.** No dependency cycle within or between subsystem build units. Runtime message loops are reviewed separately for bounded behavior.
3. **Interface completeness.** Every internal edge has a typed contract; every cross-subsystem exchange has a versioned contract and failure behavior.
4. **Coverage.** Every `SYS-*` traces to module(s) or an end-to-end subsystem path, with an owner and measurable acceptance evidence.
5. **Stub feasibility.** Every internal and cross-subsystem contract is complete enough to write a deterministic stub or fake peer.
6. **Verification-profile consistency.** `hw_dependency: true` → `required_vl: VL-2`; system paths have a declared verification level and environment.
7. **HAL substitution ladder.** Mock HAL exposes the base-layer interface; golden vectors carry digest, parameters and expected outputs. In `mock+real`, the Real HW HAL exposes the same interface and references the SyRS `PROTO-*`, correction chains and tolerances.
8. **Telemetry companion.** The companion spec declares what it monitors, its sampling interval, its resource budget, and that its footprint is bounded below a declared threshold.
9. **Supplied ML model, when used.** The weights, metadata, training data source, and labelling procedure are identified, the inference contract is implementable, and the COTS budget is credible. This check is omitted when the design has no ML model.
10. **Toolchain availability.** On the development machine, the language runtime and package manager of every `Toolchain` entry answer their version command. The agent installs a missing tool only after a brief yes from the user; a refused or failed install is an open finding.
11. **Module decomposition completeness.** *(New in v4.)* Every module has a unique `module_id`, a `subsystem_id`, a `layer`, a `depends_on` list, a `provides` list, a `hw_dependency` flag, a `required_vl`, and a `traced_reqs` list. Every `SYS-*` in the GT appears in at least one module's `traced_reqs`. No module has an empty `traced_reqs`.
12. **Topological slicing feasibility.** *(New in v4.)* The implementation dependency graph admits a topological sort. Every module's `depends_on` edges point only to modules or base-layer contracts that will be available (built or stubbed) before the module is scheduled.

**PASS** → S2. **FAIL** → S1. **RFD** → §13.2, when the requirements are infeasible on the declared COTS platform.

The [S1/G1 design template](S1_G1_template.md) expands these check families into fifteen general review items (thirteen from v3 plus two new module-decomposition items) and one conditional ML item, including design decisions, COTS coherence, HAL ladder, telemetry companion, toolchain availability, module decomposition, and risk assessment.

---

## 8 S2 — Module Planning (Agile-V Layer)

**New in v4.** S2 is the bridge between system design (S1) and per-module implementation (S3). It takes the approved S1 design and produces a **backlog of module plans** ordered by topological dependency, so that each module can be implemented in a fresh context (P7) without losing traceability to the Ground Truth (P8).

### 8.1 The Agile-V model

```mermaid
flowchart TD
    classDef design fill:#e0f2fe,stroke:#0284c7,color:#0c4a6e
    classDef plan fill:#ede9fe,stroke:#7c3aed,color:#3b0764
    classDef impl fill:#fef3c7,stroke:#d97706,color:#78350f
    classDef verify fill:#dcfce7,stroke:#16a34a,color:#14532d

    subgraph AGILE["Agile-V: module as iteration unit"]
        direction TD
        DESIGN["S1 approved design<br/>system → subsystems → modules"]:::design
        PLAN["S2 module plan<br/>PLAN.md per module"]:::plan
        IMPL["S3 implement module<br/>fresh context: PLAN.md + contracts"]:::impl
        VERIFY["G3 verify module<br/>per plan's verification section"]:::verify
    end

    DESIGN --> PLAN
    PLAN --> IMPL
    IMPL --> VERIFY
    VERIFY -->|next module| PLAN
```

The iteration unit is the **module**, not a user story or a sprint. Each iteration is a **mini-V cycle**: plan (S2) → implement (S3) → verify (G3). The backlog is the sequence of all modules across all subsystems, ordered by topological sort of the S1 dependency graph.

### 8.2 Topological slicing

```mermaid
flowchart LR
    classDef base fill:#dbeafe,stroke:#2563eb,color:#1e3a8a
    classDef low fill:#dcfce7,stroke:#16a34a,color:#14532d
    classDef mid fill:#fef3c7,stroke:#d97706,color:#78350f
    classDef high fill:#fee2e2,stroke:#dc2626,color:#7f1d1d

    subgraph SLICE["Topological build order"]
        direction LR
        L0["Slice 0<br/>Base layers<br/>+ verification kit"]:::base
        L1["Slice 1<br/>Leaf modules<br/>(no module deps)"]:::low
        L2["Slice 2<br/>Modules depending<br/>on Slice 1"]:::mid
        L3["Slice 3<br/>Integration +<br/>system paths"]:::high
    end

    L0 --> L1 --> L2 --> L3
```

S2 performs a topological sort of the implementation dependency graph from S1 and partitions the modules into **slices**. Slice 0 is always the base layers and verification kit. Within a slice, modules that share no dependency may be built in parallel. Each module in a slice builds against the **real contracts** of modules from earlier slices and the **stub contracts** of modules in later slices (interface-first with Mock-HAL, P6).

### 8.3 PLAN.md format

S2 produces one `PLAN.md` per module. This is the **sole input** to S3's fresh context for that module.

```markdown
# PLAN.md — <module_id>

## Meta
- module_id: <unique identifier>
- subsystem_id: <parent subsystem>
- layer: <architectural layer>
- slice: <topological slice number>
- depends_on: [<module_id>, ...]
- provides: [<contract_name>, ...]
- hw_dependency: true | false
- required_vl: VL-0 | VL-1 | VL-2
- hal_mode: mock-only | mock+real

## Traced Requirements
| Req ID | Text | Delta | Source |
|--------|------|-------|--------|
| SYS-002 | FFT resolution ≥ 1024 bins | ADDED | GT v1.0 |
| SYS-003 | Latency ≤ 50 ms | ADDED | GT v1.0 |

## Interface Contracts
### Consumes
- `raw_iq` from `iq_acquisition` (schema v1, units: complex float32, rate: continuous)

### Produces
- `psd_estimate` (schema v1, units: dB/Hz, latency: ≤ 50 ms)

## Ordered Tasks
1. Implement FFT pipeline with configurable window
2. Wire to base-layer `raw_iq` consumer contract
3. Expose `psd_estimate` through base-layer producer contract
4. Unit tests: edge cases (empty buffer, single sample, max-length)
5. Bottom-up integration: module + driver vs base

## Verification Plan
| Level | What | Data source | Pass criterion |
|-------|------|-------------|----------------|
| VL-0 | Unit + sandwich | Mock HAL deterministic vectors | All pass |
| VL-1 | SIL measured | Mock HAL synthetic I/Q | Latency ≤ 50 ms, resolution ≥ 1024 |

## Delta Traceability
- GT version: 1.0
- Deltas introduced by this module: none
- Deltas from prior modules affecting this module: none

## Risks
- R1: FFT library may not meet latency on COTS target → mitigation: benchmark in S3, escalate to RFD if exceeded
```

### 8.4 Delta traceability (P8)

Each PLAN.md records the **GT version** it was derived from and any **deltas** the module introduces. When a module's implementation reveals that a requirement must be modified (e.g. a threshold relaxed after measurement), the delta is recorded as:

```
Delta: MODIFIED SYS-003
  Before: Latency ≤ 50 ms
  After:  Latency ≤ 75 ms
  Reason: COTS FFT library floor measured at 62 ms
  Authority: RFD-002 approved by Build Package author
```

The deltas follow the OpenSpec [21] convention: **ADDED** (new requirement discovered during implementation), **MODIFIED** (existing requirement changed), **REMOVED** (requirement dropped). Each delta names its authority (RFD, design review, or Build Package author decision). The system-level GT is updated after each module's G3 pass, keeping it a **living document** without requiring a monolithic re-review.

### 8.5 Interaction with S1 living design

S2 may discover that the S1 design needs adjustment (e.g. a missing interface, an undeclared dependency). Minor adjustments (adding a field to a contract) are recorded as deltas in the affected PLAN.md files. Structural changes (new module, changed DAG topology) route back to S1 through G2 FAIL or G3 design-defect feedback.

---

## 9 G2 — Module Plan Micro-Gate

**New in v4.** G2 validates each PLAN.md before the module enters S3. It is lightweight by design: the full design review happened at G1; G2 checks only that the plan is **self-contained, traceable, and buildable**.

G2 runs once per module, immediately after S2 produces its PLAN.md and before S3 begins work on that module.

### 9.1 Checks

| # | Check | What it verifies |
|---|---|---|
| 1 | **Completeness** | All PLAN.md sections are present and non-empty |
| 2 | **Traceability** | Every `traced_reqs` entry exists in the current GT; deltas reference valid authority |
| 3 | **Contract consistency** | Every `consumes` contract is provided by a module in an earlier or same slice; every `provides` contract matches the S1 design |
| 4 | **Task ordering** | Tasks respect the dependency order; no task references an artifact that a prior task has not produced |
| 5 | **Verification feasibility** | The verification plan's data sources and pass criteria are achievable with the declared HAL mode and available verification kit |
| 6 | **Fresh-context sufficiency** | The PLAN.md plus its referenced contracts contain enough information to implement the module without access to the full system design or other modules' source code |

### 9.2 Verdicts

| Verdict | Meaning | Routes to |
|---|---|---|
| **PASS** | Plan is self-contained and traceable | S3 (implement this module) |
| **FAIL — plan defect** | Missing section, broken trace, or insufficient context | S2 (fix PLAN.md) |
| **FAIL — design defect** | Plan reveals a structural issue in S1 (missing contract, DAG error) | S1 |
| **FAIL — GT defect** | Plan reveals a GT inconsistency (conflicting requirements) | S0 |

---

## 10 S3 — Per-Module Implementation and System Integration

S3 is the renamed v3 S2, enhanced with the **fresh-context protocol** (P7).

### 10.1 Fresh-context protocol

Each module is implemented in an **isolated context** that carries:

1. The module's **PLAN.md** (from S2, approved by G2)
2. The **interface contracts** it consumes and produces (from S1)
3. The **base-layer API** of its subsystem
4. The **verification kit** relevant to its declared VL
5. The **stub implementations** of modules it depends on (if not yet built)

The context does **not** carry: the full system design, the complete GT, other modules' source code, or accumulated implementation state from prior modules. This enforces P7 and ensures that each module is built from its specification, not from implicit knowledge.

### 10.2 Implementation flow

```mermaid
flowchart TD
    classDef base fill:#dbeafe,stroke:#2563eb,color:#1e3a8a
    classDef mod fill:#e0e7ff,stroke:#4f46e5,color:#312e81
    classDef test fill:#f0fdf4,stroke:#16a34a,color:#14532d
    classDef stub fill:#f3f4f6,stroke:#9ca3af,color:#374151,stroke-dasharray:5 3
    classDef plan fill:#ede9fe,stroke:#7c3aed,color:#3b0764

    subgraph STEP0["Step 0 — Module context (P7)"]
        PLAN["Load PLAN.md<br/>+ referenced contracts"]:::plan
    end

    subgraph STEP1["Step 1 — Initial layer: base + verification kit"]
        B["Implement base layer<br/>orchestration · HAL · routing"]:::base
        KIT["Build verification kit<br/>Mock HAL · golden vectors + manifest<br/>telemetry companion · fake peers · drivers"]:::stub
        STUBS["Generate stubs<br/>from G1 contracts"]:::stub
        TD_["Top-down integration<br/>base + all stubs"]:::test
        B --> KIT --> STUBS --> TD_
    end

    subgraph STEP2["Step 2 — Each module (topological slice order)"]
        IMPL["Implement module<br/>from PLAN.md tasks"]:::mod
        UT["Unit test<br/>in isolation"]:::test
        BU["Bottom-up integration<br/>module + driver vs base"]:::test
        IMPL --> UT --> BU
    end

    PLAN --> STEP1
    STEP1 --> STEP2
    STEP2 --> CONTRACT["Step 3 — Cross-subsystem contract tests<br/>real subsystems + fake peers"]:::test
    CONTRACT --> SYSTEM["Step 4 — System paths<br/>connected subsystems"]:::test
```

Top-down (base → stubs) + bottom-up (module → driver → base) = **sandwich integration testing** [1][2][13].

Step 1 is the **initial layer**: before any module, S3 builds each subsystem base and makes every tool ready — the verification kit of §6.5 and, in `mock+real`, the Real HW HAL with its fake device API. S3 writes every test, including the VL-1 tests for modules and paths with `required_vl` VL-1 or higher, without claiming them; G3 only runs them (§12.3).

Each subsystem lives in `src/<subsystem>/` and is built with its declared toolchain; the verification kit, tests included, lives in `verification/` and is never shipped; one command runs each verification level (`verification/run.sh vl0`, `verification/run.sh vl1`); and the delivered code has no dependency on CodeAnvil.

Define cross-subsystem contracts first so each subsystem can be built independently against a deterministic fake peer. Connect real subsystems after their local VL-0 floor passes. For each `SYS-*` allocated across subsystems, execute a deterministic system-path test across the real subsystem processes with simulated external inputs. This checks serialization, routing, state handoff, and recovery at the declared boundary; VL-1 and VL-2 add stronger environments and measurements.

*Future work (FW-005, §6.4).* If a subsystem uses a supplied ML model, S3 implements its inference adapter and tests the declared preprocessing, output mapping, and failure behavior. The fake response exercises the surrounding module contract at VL-0; tests claiming model behavior use the identified weights.

### 10.3 Data sources by verification level

The HAL substitution ladder determines what feeds the pipeline at each level. The **telemetry companion** runs during every test at every level. VL-2 needs `HAL mode: mock+real`.

| Level | Data source | HAL used | Telemetry companion |
|---|---|---|---|
| **VL-0** | Deterministic golden vectors (short, repeatable, edge-case) | Mock HAL | Records UC state; attached to evidence |
| **VL-1** | Synthetic I/Q at known SNR, modulation, channel conditions | Mock HAL | Records UC state; attached to evidence |
| **VL-2** | Real RF via COTS SDR; datasets generated following the SyRS lab procedures (`PROTO-*`) with declared calibration and tolerances; only in `mock+real` | Real HW HAL | Records UC state; attached to evidence |

### 10.4 Golden vector governance

Each golden vector or synthetic capture used by the Mock HAL is a controlled artefact: it carries a unique identifier, SHA-256 digest, generation parameters, the condition it simulates (nominal, edge-case, degraded), and the expected output at the consuming module's contract. Changing a vector invalidates every evidence record that used it. The golden-vector set is versioned alongside the source code.

### 10.5 Mandatory floor (VL-0) — cannot be skipped

| Component | Always required |
|---|---|
| **Base layer** | Unit test + top-down integration with stubs |
| **Each module** | Unit test + bottom-up integration with driver |
| **Each cross-subsystem contract** | Producer and consumer contract tests using a fake peer, including version and failure cases |
| **Each cross-subsystem SYS-* path** | Deterministic test across the connected subsystem processes with simulated external inputs |
| **Telemetry companion** | Running and recording during all tests above; UC state attached to every evidence record |

---

## 11 G3 — Adaptive Verification Gate

G3 is the renamed v3 G2, enhanced with a **plan-defect** routing class that feeds back to S2.

### 11.1 Verification levels

```mermaid
flowchart LR
    classDef mandatory fill:#dcfce7,stroke:#16a34a,color:#14532d,stroke-width:2px
    classDef optional fill:#fef3c7,stroke:#d97706,color:#78350f,stroke-dasharray:5 3
    classDef hil fill:#fee2e2,stroke:#dc2626,color:#7f1d1d,stroke-dasharray:5 3

    VL0["VL-0 — Logic<br/>Unit + sandwich + subsystem contracts<br/>Deterministic system paths · MANDATORY"]:::mandatory
    VL1["VL-1 — Mock / SIL<br/>+ measured multi-subsystem system test<br/>Synthetic I/Q · GnuRadio · OPTIONAL"]:::optional
    VL2["VL-2 — HIL<br/>+ end-to-end acceptance where claimed<br/>Real HW · representative link · OPTIONAL<br/>only in mock+real"]:::hil

    VL0 -->|"user decides ▸"| VL1 -->|"user decides ▸"| VL2
```

Each level includes all tests from the levels below. The HAL substitution ladder (§6.5) determines what feeds the pipeline: Mock HAL at VL-0 and VL-1, Real HW HAL at VL-2 (only in `mock+real`). The telemetry companion runs at every level.

### 11.2 Adaptive rule

The user chooses the verification level per module and per system path, per cycle. Four constraints:

1. **Floor.** Every module and every declared cross-subsystem contract and system path reaches VL-0 in every cycle.
2. **Honesty.** No module or end-to-end claim is higher than the environment actually tested. Passing subsystems individually does not prove a cross-subsystem requirement.
3. **Telemetry context.** Every evidence record includes the telemetry companion's readings for the compute unit during that test. Evidence produced while the UC was outside its declared operating envelope (temperature, CPU saturation, dropped buffers) is flagged and may be invalidated by the reviewer.
4. **HAL mode ceiling.** `mock-only` caps every claim at VL-1. `mock+real` allows VL-2, but each module and path still declares its level per cycle: the Real HW HAL may be declared at VL-0 (fake device API) for a cycle, in which case G3.2 does not fire and the honesty declaration states it. PIL (Processor-in-the-Loop) uses the actual target processor with Mock HAL inputs; every PIL claim stays VERIFIED, not VALIDATED.

| Scenario | User declares | G3 checks |
|---|---|---|
| Fast iteration | VL-0 all | Unit + sandwich for every module; contract and deterministic path tests for connected subsystems |
| DSP validation | VL-1 for DSP; VL-0 rest | Mock/SIL for DSP; VL-0 floor for every subsystem path |
| Pre-release (`mock+real`) | VL-1 for the edge → UI display path; VL-2 for `iq_acquisition` | Measured multi-subsystem path plus HIL acquisition |
| Full release | All modules and system paths at `required_vl` | Every claim at its S1-declared level |

### 11.3 Sub-gates

G3 runs the tests S3 wrote and writes none; a declared level with no test is a module defect routed to S3. The runs happen in a separate read-only verifier context — a subagent where the runtime supports it, otherwise a fresh session — which implements P2: the oracle is not the generator.

**Hardware enrollment.** Before G3.2 can fire, the target must be enrolled in `.codeanvil/project.yaml` via `codeanvil credential-setup -u <admin-user> -i <host> --port 22`. G3.0 and G3.1 may proceed locally while enrollment is pending; G3.2 blocks until a valid `targets:` entry exists.

| Sub-gate | Fires when | Checks |
|---|---|---|
| **G3.0** | Always | Unit + sandwich, cross-subsystem contract, and deterministic system-path tests pass; Mock HAL golden vectors; telemetry companion confirms UC nominal |
| **G3.1** | VL-1+ declared for a module or path | Mock HAL synthetic I/Q; Mock/SIL system tests across affected subsystems pass; metrics within thresholds; telemetry companion confirms UC nominal |
| **G3.2** | VL-2 declared for a module or path | Real HW HAL on COTS SDR (only in `mock+real`); enrollment required (see above); datasets from the SyRS lab procedures (`PROTO-*`) with declared calibration and tolerances; for cross-subsystem paths, a representative link; measurements within criteria; telemetry companion confirms UC nominal |

### 11.4 Failure classification and routing

**Operational vs defect.** Before routing a G3 failure, classify it. A permission, driver, group, udev, or USB-access problem on the target DUT is **operational** — it must be fixed on the DUT and G3 re-run; it is never a module or design defect and must not route to S3, S2, or S1. A transient SSH, clock, or setup fault is operational in the same way. Only a genuine behavioral failure of the delivered code under correct operating conditions enters the defect classification below.

The five first-class G3 outcomes are:

| Outcome | Routes to | Example |
|---|---|---|
| **Operational fix** | Fix DUT → re-run G3 | USB access, SSH auth, missing udev rule |
| **Module defect** | S3 | FFT output wrong; UI deserializes valid message incorrectly |
| **Plan defect** *(new in v4)* | S2 | PLAN.md omitted a contract; verification plan underspecified; task ordering wrong |
| **Design defect** | S1 | DAG has undeclared dependency; cross-subsystem contract incomplete |
| **RFD** | §13.2 | Requirements infeasible on COTS platform |

**Self-diagnosis:** if a module that was *not* changed fails during re-testing → undeclared dependency → design defect → S1.

*Future work (FW-005, §6.4).* For an ML-based module or path, G3 measures the supplied model *inside the implemented system* at the declared level and checks the relevant `SYS-*` criteria. The performance metadata received at S1 is context for test design, not a substitute for those measurements.

---

## 12 Feedback Routing

V-SIL v4 produces two types of feedback. They are structurally different and must not be conflated.

```mermaid
flowchart TD
    classDef defect fill:#fef3c7,stroke:#d97706,color:#78350f
    classDef plan fill:#ede9fe,stroke:#7c3aed,color:#3b0764
    classDef rfd fill:#fee2e2,stroke:#dc2626,color:#7f1d1d
    classDef stage fill:#e0f2fe,stroke:#0284c7,color:#0c4a6e
    classDef ext fill:#f3f4f6,stroke:#6b7280,color:#1f2937,stroke-width:2px
    classDef ops fill:#f3f4f6,stroke:#6b7280,color:#374151

    FAIL["Gate failure"]:::defect
    CLS{"Defect class?"}

    subgraph INTERNAL["Internal — Fix within V-SIL"]
        direction LR
        D_S1["S1 — design defect"]:::stage
        D_S2["S2 — plan defect"]:::plan
        D_S3["S3 — module defect"]:::stage
    end

    subgraph EXTERNAL["External — RFD (Build Package must change)"]
        direction LR
        RFD["Request for Deviation"]:::rfd
        BP["Build Package<br/>author"]:::ext
        RFD --> BP
    end

    OPS["Operational fix<br/>Fix DUT → re-run G3"]:::ops

    FAIL --> CLS
    CLS -->|"design"| D_S1
    CLS -->|"plan"| D_S2
    CLS -->|"module"| D_S3
    CLS -->|"requirements<br/>infeasible"| EXTERNAL
    CLS -->|"DUT/environment"| OPS
```

### 12.1 Internal defect routing

A **defect** means V-SIL can fix it internally. The implementation, the plan, or the design is wrong, but the requirements are achievable. An **operational problem** is not a defect: it is a DUT/environment issue that blocks measurement; fix it and re-run G3 without touching S1, S2, or S3.

| Class | Routes to | Example |
|---|---|---|
| Operational problem | Fix DUT → re-run G3 | `codeanvil-agent` cannot open the HackRF; SSH auth failure; missing udev rule |
| Design defect | S1 | DAG has undeclared dependency; cross-subsystem contract or state ownership is incomplete |
| Plan defect *(new in v4)* | S2 | PLAN.md omitted a needed contract; verification plan missing a declared level; task ordering violated a dependency |
| Module or integration defect | S3 | FFT output is wrong; UI deserializes a valid edge message incorrectly |

**Self-diagnosis:** if a module that was *not* changed fails during re-testing → undeclared dependency → design defect → S1.

### 12.2 Request for Deviation (RFD)

An **RFD** means the Build Package requirements are **infeasible on the declared COTS platform**. V-SIL cannot fix it internally — the constraints themselves must change. V-SIL **suspends** until the Build Package is updated and re-enters at S0.

An RFD can be emitted from **S1, G1, or any G3 sub-gate**. S0 and G0 do not emit one: S0 makes no judgement about feasibility and G0 checks structure only. S2 and G2 do not emit RFDs directly; infeasibility discovered during planning is recorded in the PLAN.md risks section and confirmed at G3. Infeasibility discovered while implementing in S3 is reported through G3.

| Discovered at | Example |
|---|---|
| S1 | Pipeline latency exceeds requirement under any partitioning on this HW |
| G1 | Design review concludes that a latency budget cannot be met on this HW, by the reviewed design or by any other partitioning |
| G3.0 | Unit tests reveal that two normative requirements conflict mathematically |
| G3.1 | SIL metrics show P_d and P_fa cannot simultaneously meet thresholds |
| G3.2 | HIL shows real hardware noise floor exceeds assumed budget |

At S1 and G1 nothing has been measured yet, so the evidence is analysis and names no verification level (P4).

### 12.3 RFD contents

Per ECSS [16], MIL-HDBK-61A [17], and NASA NPR 7150.2 [18]:

```
Request for Deviation — RFD-001

  Conflicting requirements:
    STK-007: Latency ≤ 100 ms    (source: ITU-R SM.1880)
    STK-012: P_d ≥ 0.95 @ 10 dB  (source: national regulator)

  Evidence (from G3.1, VL-1):
    FFT 4096 → P_d 0.96, latency 142 ms  — STK-012 met, STK-007 violated
    FFT 2048 → P_d 0.91, latency 71 ms   — STK-007 met, STK-012 violated

  Trade-off options:
    A) Relax latency to ≤ 150 ms         → both met
    B) Relax P_d to ≥ 0.92               → both met
    C) Dual-mode: fast (2048) + deep (4096) → both met, adds complexity

  Impact analysis:
    Option A: requires normative waiver from ITU-R SM.1880 §4.3
    Option B: screening-grade only, not compliance-grade
    Option C: new module, new interface contract, S1 rework

  Recommendation: C
```

### 12.4 Distinction summary

```mermaid
flowchart LR
    classDef defect fill:#fef3c7,stroke:#d97706,color:#78350f
    classDef plan fill:#ede9fe,stroke:#7c3aed,color:#3b0764
    classDef rfd fill:#fee2e2,stroke:#dc2626,color:#7f1d1d
    classDef ops fill:#f3f4f6,stroke:#6b7280,color:#374151

    O["Operational fix<br/>DUT/environment problem<br/>Fix target → re-run G3<br/>No S1, S2, or S3 change"]:::ops
    P["Plan defect<br/>PLAN.md wrong<br/>Fix in S2"]:::plan
    D["Design / module defect<br/>Requirements achievable<br/>Fix inside V-SIL"]:::defect
    R["RFD<br/>Requirements infeasible<br/>COTS cannot deliver both<br/>Build Package must change"]:::rfd

    O ---|"different from"| P ---|"different from"| D ---|"different from"| R
```

### 12.5 Failure triage and draft mode (S0 · G0 · G1)

The requirements stages are exploratory: the Ground Truth is corrected many times before it is sound. V-SIL v4 softens the *loop*, not the *checks*, through two devices scoped to S0, G0 and G1 — never to S2, S3, or G3.

**Failure triage.** A machine or gate failure is translated before it reaches the human. For every G0 ERROR, every missing-list placeholder and every G1 `open` finding, the agent states the real problem in plain language — describing each requirement by what it asks, with its block ID only in parentheses, so the reader never opens a document to know what an item is — and offers two to four concrete reconciliation options (connect an unlinked item, create its missing origin, remove or relax it, or — when the gap is a documentary fact and the runtime has web access — look it up on the web and propose the found value with its source for the human to confirm), each with its consequence. The human chooses; the agent applies. The agent is the interpreter, never the oracle: the verdict stays the validator's exit code (G0) or the human's answer (Gate H, G1), so P2 and P3 are untouched.

**Draft mode.** When a requirements stage finds unresolved items — a missing-list entry, a format error, or a G1 open finding — it **enters draft automatically** and cannot advance until **each one is resolved**. Mechanical fixes that invent nothing — removing blueprint scaffolding, filling a value already stated elsewhere, dropping a broken reference — are **auto-applied and reported**, not asked; only the judgment calls go to the human, who **fixes** them, knowingly **ignores/accepts** them (recorded with the decider's name), or **escalates** to an RFD. While in draft the stage runs against the current files, applies triage and loops without writing a report iteration or enforcing staleness; the human may edit the GT pair directly. On commit — reached only once every item is decided — the marker is removed and one recorded run is written, listing each item and its decision. A format error can be fixed or escalated but never ignored into a pass, since the deterministic validator keeps rejecting it. The audit trail records the run that passes and the decisions behind it, not the red path to it.

---

## 13 Terminal Output

The Verified Prototype lists the delivered tree (`src/<subsystem>/`) apart from the verification kit (`verification/`) and the module plans (`plans/`), and names the verifier context in which G3 ran the tests.

```
Verified Prototype — V-SIL v4
  Cycle: pre_release_01
  HAL mode: mock+real

  Delivered software (shipped):
    src/fm_edge/, src/dashboard/ — no CodeAnvil dependency
  Module plans (not shipped):
    plans/ — PLAN.md per module, delta traceability log
  Verification kit (not shipped):
    verification/ — Mock HAL, golden vectors + manifest, telemetry
                    companion, stubs, fake peers, drivers, tests
  Verifier context: read-only verifier subagent (fresh context)

  Module evidence:
    iq_acquisition:    VL-2 (HIL)  — Real HW HAL, HackRF One, FM 88–108 MHz
                       Plan: plans/iq_acquisition/PLAN.md (slice 1)
    fft_engine:        VL-1 (SIL)  — Mock HAL, golden I/Q (vectors v1.2, SHA bc3f…)
                       Plan: plans/fft_engine/PLAN.md (slice 1)
    feature_extractor: VL-1 (SIL)  — Mock HAL, synthetic PSD at known SNR
                       Plan: plans/feature_extractor/PLAN.md (slice 2)
    classifier:        VL-0 (logic)— Mock HAL, deterministic vectors
                       Plan: plans/classifier/PLAN.md (slice 2)
    audio_demod:       VL-1 (SIL)  — Mock HAL, synthetic FM-modulated I/Q
                       Plan: plans/audio_demod/PLAN.md (slice 1)
    data_store:        VL-0 (logic)— Mock HAL, deterministic vectors
                       Plan: plans/data_store/PLAN.md (slice 2)
    dashboard:         VL-1 (SIL)  — edge messages on simulated link
                       Plan: plans/dashboard/PLAN.md (slice 1)
    controls:          VL-0 (logic)— command and acknowledgement vectors
                       Plan: plans/controls/PLAN.md (slice 1)
    alerts:            VL-0 (logic)— unit + sandwich integration
                       Plan: plans/alerts/PLAN.md (slice 2)
    history:           VL-0 (logic)— unit + sandwich integration
                       Plan: plans/history/PLAN.md (slice 2)

  Delta traceability log:
    GT version at S2 entry: 1.0
    Deltas applied: 0 ADDED, 0 MODIFIED, 0 REMOVED
    GT version at G3 exit: 1.0

  Subsystem and system-path evidence:
    edge -> UI occupancy.v1: VL-1 — schema + latency on simulated link
    UI -> edge configure.v1: VL-0 — commands, retries, duplicate handling
    PATH-001 / SYS-002 occupancy display: VL-1 — edge + UI, Mock HAL synthetic RF

  Telemetry companion report:
    All tests: UC within operating envelope
    CPU peak: 63%  |  Temp peak: 68 °C  |  Dropped buffers: 0
    No evidence invalidated by UC conditions.

  Honesty declaration:
    VL-1 modules: VERIFIED against synthetic data (Mock HAL).
    VL-2 modules: VALIDATED on real hardware (Real HW HAL);
                  calibration: screening grade per SyRS §4;
                  tolerances: ±2.1 dBi declared by development team (SyRS §5).
    VL-0 modules: VERIFIED at logic level only.
    SYS-002: VERIFIED across connected subsystems with synthetic input;
             no real-link or HIL latency claim.
    Telemetry companion: UC nominal during all test executions.

  RFDs issued: 0
```

### 13.1 Optional future work register

After G3, the prototype may include proposals for later **software versions**. Each entry records an ID, the proposed capability or improvement, its origin and evidence, a candidate version, a decision owner, dependencies, and a proposed acceptance criterion. An empty register can be omitted. The Build Package author decides whether a proposal enters a later version; an accepted proposal becomes new input at S0 and G0. Future CI/CD automation is a possible infrastructure entry for a later version; building that pipeline is outside this version of V-SIL.

Only work explicitly outside the current cycle's approved scope belongs here. A failing current `SYS-*` remains a defect to correct or, if infeasible on the declared COTS platform, an RFD; the register cannot turn it into a passing claim.

```text
FW-001 — Automate V-SIL verification evidence in CI/CD
  Category: verification infrastructure
  Origin: repeated manual G3 execution in this cycle
  Candidate version: later software release
  Decision owner: Build Package author
  Dependency: stable test commands and report format
  Proposed acceptance: a pipeline reproduces the declared G3 checks
                       and links its reports to the cycle and source revision

FW-002 — Processor-in-the-Loop (PIL) as a full sub-gate
  Category: verification depth
  Status: partially implemented — G3 currently allows PIL as a declared
          mode (actual target processor, Mock HAL inputs, claim stays
          VERIFIED); a dedicated G3.PIL sub-gate with structured timing
          and scheduling checks is not yet defined
  Origin: SOTA review; when UC ≠ development host, compiled code on the
          target processor may behave differently under timing constraints
  Candidate version: later software release
  Decision owner: Build Package author
  Dependency: target UC identified and accessible for cross-compilation
  Proposed acceptance: G3.PIL sub-gate defined with explicit timing,
                       scheduling and resource checks on the target processor

FW-003 — Formal fault injection at VL-2
  Category: verification depth
  Origin: SOTA review (ISO 26262-5 §10; IEC 61508-3 Table A.5);
          current VL-2 tests nominal operation only
  Candidate version: later software release
  Decision owner: Build Package author
  Dependency: fault scenarios defined per module (USB disconnect,
              buffer overflow, SDR clock drift, UC power glitch)
  Proposed acceptance: declared fault scenarios executed at VL-2;
                       system response documented per scenario

FW-004 — SIL ↔ HIL correlation measurement
  Category: verification confidence
  Origin: SOTA review; VL-1 and VL-2 results are reported independently
          with no measured correlation between them
  Candidate version: later software release
  Decision owner: Build Package author
  Dependency: both VL-1 and VL-2 executed for the same modules
  Proposed acceptance: quantified deviation between Mock HAL and
                       Real HW HAL results for overlapping test cases

FW-005 — MLOps for the optional ML model
  Category: model lifecycle
  Origin: the optional ML model is trained and labelled outside any
          automated pipeline, and its S3 and G3 integration is not
          implemented yet (§6.4)
  Candidate version: later software release
  Decision owner: Build Package author
  Dependency: versioned Mock HAL or Real HW HAL datasets and a declared
              labelling procedure
  Proposed acceptance: a pipeline reproduces training from versioned data
                       and labels and links each model version to its
                       G3 evidence

FW-006 — Automated PLAN.md generation from S1 design
  Category: planning automation
  Origin: V-SIL v4 S2 currently requires manual or agent-assisted
          production of PLAN.md files from S1 design
  Candidate version: later software release
  Decision owner: Build Package author
  Dependency: stable PLAN.md format and S1 module identity schema
  Proposed acceptance: a tool reads the S1 design and generates
                       PLAN.md skeletons for all modules with correct
                       traceability and contract references
```

---

## 14 Compatibility Notes

### 14.1 Stage renumbering mapping

Tools and skills that reference v3 stage names must be updated:

| v3 reference | v4 equivalent | Notes |
|---|---|---|
| `S2_implement_subsystems` | S3 | Skill and directory name update needed |
| `G2_adaptive_verification` | G3 | Skill and directory name update needed |
| `config.yaml` stage entries | Add `S2_module_planning`, `G2_module_plan_gate`; rename `S2` → `S3`, `G2` → `G3` | |

### 14.2 `config.yaml` changes

```yaml
# V-SIL v4 stage-gate chain
stages:
  - S0_normalise_build_package
  - G0_valid_req_and_GT
  - S1_design_system          # enhanced: module decomposition
  - G1_design_review           # enhanced: checks 11-12
  - S2_module_planning         # NEW
  - G2_module_plan_gate        # NEW
  - S3_implement_subsystems    # renamed from S2
  - G3_adaptive_verification   # renamed from G2
```

### 14.3 Preserved v3 concepts

The following v3 concepts are **unchanged** in v4:

- S0 normalisation and GT generation
- G0 deterministic structural validation
- HAL substitution ladder (Mock HAL, Real HW HAL)
- Telemetry companion
- Verification levels VL-0, VL-1, VL-2
- Sandwich integration testing
- Golden vector governance
- RFD process and contents
- Failure triage and draft mode (S0, G0, G1)
- Future work register
- All governing principles P1–P4
- IEEE 29148 blueprint approach
- Cross-subsystem contracts
- Verifier context (P2)
- Optional ML model (unchanged; still future work)

---

## 15 References

[1] R. S. Pressman, B. R. Maxim, *Software Engineering*, 9th ed., 2020.
[2] ISO/IEC/IEEE 29119-1:2022, "Software testing — Part 1."
[3] Codeburst, "The Basics of Contract Tests," 2024.
[4] L. Bass, P. Clements, R. Kazman, *Software Architecture in Practice*, 4th ed., 2021.
[5] ISO 26262:2018, "Road vehicles — Functional safety."
[6] V. H. Nguyen, T. Nguyen, "SDAD," arXiv:2608.20341, May 2026.
[7] "LLM-as-a-Judge Is Not an Oracle," arXiv:2609.02246, Sep. 2026.
[8] V. Reddy et al., "Reason Less, Verify More," arXiv:2607.07405, Jul. 2026.
[9] Sheridan Tech, "Design Validation vs Verification," Mar. 2026.
[10] Augment Code, "Coordinator-Implementor-Verifier Pattern," Jun. 2026.
[11] OPAL-RT, "Guide to HIL Testing," Sep. 2026.
[12] IEEE/ISO/IEC 29148:2018, "Requirements engineering."
[13] V. Lavecchia, "Sandwich testing strategies," 2024.
[14] B. Trinnes, "Test Architecture Patterns," GitHub, Apr. 2026.
[15] "Spec-Driven Development," arXiv:2602.00180, Feb. 2026.
[16] ECSS-Q-ST-10-09C, "Nonconformance control system," European Cooperation for Space Standardization. — Defines Request for Deviation (RFD) as a "planned departure" from requirements.
[17] MIL-HDBK-61A, "Configuration Management Guidance," U.S. DoD, 2001. — Deviation processing: request when a product cannot meet technical requirements; includes impact analysis and trade-off options.
[18] NASA NPR 7150.2, "NASA Software Engineering Requirements." — Deviation/waiver evaluation: technical justification, risk assessment, impact to safety, and proposed alternatives.
[19] Agile-V Compliance Framework — Module-as-iteration-unit model for verified systems; topological ordering of backlog by dependency graph.
[20] GitHub Spec-Kit — Specification-driven development toolkit for stage-gate methodologies.
[21] OpenSpec Delta Traceability Model — ADDED/MODIFIED/REMOVED annotation convention for living requirements documents with per-module change tracking.

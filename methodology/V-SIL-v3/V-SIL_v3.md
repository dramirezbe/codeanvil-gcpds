# V-SIL v3: Adaptive Stage-Gate Lifecycle for COTS-Constrained Verified Prototype Development

**David Ramírez-Betancourt** — Universidad Nacional de Colombia, GCPDS  
**Version:** 3.0-draft  
**Date:** October 2026

---

## Abstract

V-SIL v3 is a software development methodology that receives a finalised Build Package (PRD with measurable constraints, COTS hardware envelope, acceptance criteria, laboratory procedures, hardware calibration at the development team's screening grade, and tolerances in dBi) and delivers a Verified Prototype with per-module and end-to-end evidence — or, when the requirements are infeasible on the declared COTS platform, a formal Request for Deviation (RFD) with trade-off analysis. S1 may design one service or a system of services: each service has its own layered base and modules, and services meet through versioned contracts. S1 also designs two HAL implementations — a **Mock HAL** that generates deterministic and synthetic data for VL-0 and VL-1, and a **Real HW HAL** that interfaces with the physical hardware for laboratory dataset generation and field tests at VL-2 — as well as a **telemetry companion** that silently monitors the compute unit during all test executions. An ML model is an optional S1 input when the chosen design uses one; it is trained with Mock HAL data plus labelling or, failing that, with Real HW HAL data plus labelling. Implementation proceeds module by module within each service and then across service boundaries. Verification depth is adaptive per module, while a mandatory floor of unit, sandwich-integration, cross-service contract, and system-path tests applies. Every claim names the verification level and environment at which it was produced; the telemetry companion attaches compute-unit state (CPU, memory, temperature, buffer health, scheduling latency) to every evidence record. The terminal output may record scoped future work for later software versions; this does not defer current acceptance criteria. Terminology is aligned with IEEE/ISO/IEC 29119, ISO 26262, SDAD [6], the Coordinator-Implementor-Verifier pattern [10], the embedded HAL mock→SIL→HIL substitution ladder [11], and the ECSS/MIL-HDBK-61A Request for Deviation process [16][17].

```mermaid
flowchart LR
    classDef input fill:#f3f4f6,stroke:#6b7280,color:#1f2937,stroke-width:2px
    classDef vsil fill:#e0f2fe,stroke:#0284c7,color:#0c4a6e
    classDef output fill:#dcfce7,stroke:#16a34a,color:#14532d,stroke-width:2px
    classDef rfd fill:#fee2e2,stroke:#dc2626,color:#7f1d1d,stroke-width:2px

    IN["Build Package<br/>PRD · COTS envelope · acceptance criteria<br/>lab procedures · calibration · tolerances"]:::input
    VSIL["V-SIL v3<br/>S0 → G0 → S1 → G1 → S2 → G2"]:::vsil
    OUT["Verified Prototype<br/>module + system-path VL evidence"]:::output
    RFD["Request for Deviation<br/>infeasibility evidence<br/>+ trade-off options"]:::rfd

    IN --> VSIL
    VSIL -->|nominal| OUT
    VSIL -.->|infeasible| RFD
    RFD -.->|updated Build Package| IN
```

---

## 1 Terminology

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

---

## 2 Stage-Gate Overview

```mermaid
flowchart TD
    classDef stage fill:#e0f2fe,stroke:#0284c7,color:#0c4a6e
    classDef gate fill:#dcfce7,stroke:#16a34a,color:#14532d
    classDef terminal fill:#e0f2fe,stroke:#0284c7,color:#0c4a6e,stroke-width:3px
    classDef input fill:#f3f4f6,stroke:#6b7280,color:#1f2937,stroke-width:2px
    classDef rfd fill:#fee2e2,stroke:#dc2626,color:#7f1d1d

    BP["Build Package"]:::input
    S0["S0 — Normalisation + GT"]:::stage
    G0{"G0 — Structural validation"}:::gate
    S1["S1 — Service topology + layered design"]:::stage
    G1{"G1 — Design review (HITL)"}:::gate
    S2["S2 — Per-service implementation + integration"]:::stage
    G2{"G2 — Adaptive verification"}:::gate
    T["Verified Prototype<br/>module + system-path VL evidence"]:::terminal
    RFD["RFD<br/>Request for Deviation"]:::rfd

    BP --> S0
    S0 --> G0
    G0 -->|PASS + Gate H| S1
    S1 --> G1
    G1 -->|PASS| S2
    S2 --> G2
    G2 -->|PASS| T

    G0 -.->|FAIL| S0
    G1 -.->|FAIL| S1
    G2 -.->|design| S1
    G2 -.->|module| S2

    S1 -.->|infeasible| RFD
    G1 -.->|infeasible| RFD
    G2 -.->|infeasible| RFD
    RFD -.->|updated| BP
```

**Governing principles.**
**P1.** HITL is an authorisation barrier; HIL is a validation barrier.
**P2.** Oracle ≠ generator — the model never approves its own work [7].
**P3.** G0 is the only deterministic gate: its mechanical rejection beats any approval [8]. Every other gate verdict is human (HITL).
**P4.** *Verified* ≠ *validated* — claims name the environment [9].

---

## 3 S0 — Normalisation and Ground Truth

```mermaid
flowchart LR
    classDef input fill:#f3f4f6,stroke:#6b7280,color:#1f2937
    classDef process fill:#ede9fe,stroke:#7c3aed,color:#3b0764
    classDef output fill:#e0f2fe,stroke:#0284c7,color:#0c4a6e

    BP["Build Package<br/>Obligations · COTS · QA<br/>lab procedures · calibration · tolerances"]:::input
    FILL["Fill IEEE 29148<br/>blueprints"]:::process
    StRS["G0_StRS.md<br/>§9.4"]:::output
    SyRS["G0_SyRS.md<br/>§9.5"]:::output

    BP --> FILL
    FILL --> StRS
    FILL --> SyRS
```

S0 **normalises only** — it casts the Build Package content into the IEEE 29148 [12] document blueprints and makes no conceptual judgement about sufficiency or scope. Following SDAD Phase 1 (spec crystallisation) [6], it populates the blueprints:

- **G0_StRS.md** — Stakeholder Requirements Specification (§9.4): `NRM-*`, `HWC-*`, `STK-*` blocks.
- **G0_SyRS.md** — System Requirements Specification (§9.5): `SYS-*` blocks tracing to StRS.

Any iteration happens afterwards at G0, which validates the Build Package content against the deterministic gate (the blueprint) — not by a review judgement here.

---

## 4 G0 — Structural Validation

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

## 5 S1 — System of Layered Services

S1 first divides the product into independently deployed services when the requirements call for them. One service remains a valid special case. A **service** owns a runtime, deployment target, base layer, modules, and externally visible ports. Its modules communicate through its own base-layer interfaces; a cross-service exchange goes through a declared, versioned service contract. Splitting a UI from an edge process is justified when they deploy or restart independently, communicate over a network, or have distinct failure domains.

### 5.1 System topology and requirement allocation

The arrows below are **runtime messages**, not implementation dependencies.

```mermaid
flowchart LR
    GT["One StRS + SyRS pair"] --> MAP["SYS-* allocated to services and paths"]
    MAP --> EDGE["Edge service<br/>COTS SDR + local base + modules"]
    MAP --> UI["UI service<br/>client base + modules"]
    EDGE -->|"occupancy.v1: measurements"| UI
    UI -->|"configure.v1: commands"| EDGE
```

The system view records each service's responsibility, deployment target, COTS resources, network link, and lifecycle. A requirement may map to one service or to an **end-to-end path** spanning several services. One system-level trace table owns this allocation; service designs do not duplicate the Ground Truth. Cross-service contracts specify producer and consumer, schema and version, units, timestamps, ordering, rate, latency, authentication, retries, duplicate handling, and behavior on disconnect or restart where applicable.

### 5.2 Layered architecture within each service

```mermaid
flowchart TD
    classDef base fill:#dbeafe,stroke:#2563eb,color:#1e3a8a
    classDef mod fill:#e0e7ff,stroke:#4f46e5,color:#312e81
    classDef integ fill:#dbeafe,stroke:#2563eb,color:#1e3a8a

    subgraph ARCH["S1 produces for each service"]
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

Modules are plug-in units communicating only through their service's base layer and declared interfaces. No direct module-to-module calls, and no cross-service calls that bypass a service contract. A service without physical hardware can have an empty HAL; its base still owns orchestration and routing.

### 5.3 Component dependency graph (edge SDR FM example)

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

Each edge carries an **interface contract** (data type, schema version, units, latency). Each service's implementation dependency graph must be acyclic. Each node carries a **verification profile**: `module_id`, `service_id`, `layer`, `depends_on`, `provides`, `hw_dependency`, `required_vl`. `hw_dependency` means correctness requires a specific physical device or behavior, rather than merely that the code runs on a computer.

The **implementation dependency graph** orders contract definition, service bases, modules, and system integration. It must be acyclic so S2 can build with stubs. The separate **runtime interaction graph** describes live messages. It may contain intentional loops, such as edge telemetry → UI → edge control, provided the contracts define ownership of state, acknowledgement, timeouts, and safe behavior. Runtime message loops do not create implementation dependency cycles.

| Module | Layer | HW dep. | Required VL |
|---|---|---|---|
| `iq_acquisition` | HAL | **yes** | VL-2 (HIL) |
| `fft_engine` | DSP | no | VL-1 (SIL) |
| `feature_extractor` | DSP | no | VL-1 (SIL) |
| `classifier` | Decision | no | VL-0 (unit) |
| `audio_demod` | Output | no | VL-1 (SIL) |
| `data_store` | Output | no | VL-0 (unit) |

### 5.4 Optional supplied ML model

**Status: uncertain.** This version defines the ML model only as an optional S1 input and a G1 readiness check. Its connection to S2 and G2 (training data generation, inference adapter, measurement at G2) is not implemented and is future work, together with MLOps (FW-005).

An S1 design includes this box **only when it chooses an ML-based module or the Ground Truth explicitly requires one**. Otherwise the box and its G1 check are absent. The supplied model is a controlled input to a service module, not a service by itself. It is trained with Mock HAL data plus labelling or, failing that, with Real HW HAL data plus labelling. S1 does not train or select a model on behalf of the Build Package author.

When used, S1 identifies the model file and weights by version and digest; names its supplying owner and provenance; records the training data source and labelling procedure; specifies the inference runtime, input and output schema, units, preprocessing, labels or thresholds, and postprocessing; and records the supplied performance metadata with its evaluation dataset and conditions. It budgets inference latency, memory, and any device dependency on the declared COTS target. A deterministic fake model response supports VL-0 integration, while later levels exercise the actual supplied model.

Supplied performance metadata is prior evidence, not a G2 verdict. If S1 chooses ML but the model package or the fields needed to implement it are missing, G1 returns **FAIL** for completion of the input or design. Demonstrated infeasibility against the declared COTS requirements follows the RFD route. Automating this model lifecycle with MLOps is future work (FW-005).

### 5.5 HAL substitution ladder and telemetry companion

S1 designs two HAL implementations that share the same base-layer interface contract but differ in what produces `raw_iq`:

- **Mock HAL.** A software-only signal generator. At VL-0 it emits deterministic vectors (short, repeatable, edge-case coverage). At VL-1 it produces synthetic I/Q files at known SNR, modulation, and channel conditions using an FM-modulated software synthesiser or recorded golden captures. Each golden vector is versioned with a SHA-256 digest, generation parameters, the condition it simulates, and its expected output. The Mock HAL is the default data source for all sandwich-integration and SIL tests.

- **Real HW HAL.** The production HAL that interfaces with the declared COTS SDR. It serves two purposes: (a) executing the laboratory procedures supplied by the Build Package to generate **real datasets** with the development team's calibration quality (screening grade, not normative) and declared tolerances in dBi; and (b) running the final field tests at VL-2. The calibration grade and tolerances are inputs from the Build Package, not claims of V-SIL.

Both HALs plug into the same base-layer port. Swapping one for the other is the **HAL substitution** that moves between verification levels [11].

S1 also specifies a **telemetry companion**: a lightweight, non-intrusive process that runs alongside every test execution and records compute-unit state — CPU utilisation, available memory, temperature, dropped buffers, and scheduling latency. It must not interfere with the system under test; its own resource footprint is declared and bounded. The companion attaches its readings to every evidence record so that G2 can determine whether the compute unit was within its operating envelope during a test. The telemetry companion is verification infrastructure, not a system module: it has no `SYS-*`, does not appear in the implementation DAG, and is absent from the Verified Prototype's module evidence.

---

## 6 G1 — Service, Dependency, and Contract Validation

G1 answers: *Are all implementation-critical design choices resolved?*

G1 is a human (HITL) design review, not a deterministic gate. An agent may prepare the review and recommend a verdict, including an RFD; the human decides.

1. **Service topology.** Every service has one responsibility, deployment target, owner of state, and declared external ports; the network and COTS envelope support the topology.
2. **Implementation DAG acyclicity.** No dependency cycle within or between service build units. Runtime message loops are reviewed separately for bounded behavior.
3. **Interface completeness.** Every internal edge has a typed contract; every cross-service exchange has a versioned contract and failure behavior.
4. **Coverage.** Every `SYS-*` traces to module(s) or an end-to-end service path, with an owner and measurable acceptance evidence.
5. **Stub feasibility.** Every internal and cross-service contract is complete enough to write a deterministic stub or fake peer.
6. **Verification-profile consistency.** `hw_dependency: true` → `required_vl: VL-2`; system paths have a declared verification level and environment.
7. **HAL substitution ladder.** Both Mock HAL and Real HW HAL expose the same base-layer interface. Golden vectors carry digest, generation parameters, and expected outputs. The Real HW HAL references the Build Package's laboratory procedures, calibration grade, and tolerances.
8. **Telemetry companion.** The companion spec declares what it monitors, its sampling interval, its resource budget, and that its footprint is bounded below a declared threshold.
9. **Supplied ML model, when used.** The weights, metadata, training data source, and labelling procedure are identified, the inference contract is implementable, and the COTS budget is credible. This check is omitted when the design has no ML model.

**PASS** → S2. **FAIL** → S1. **RFD** → §9.2, when the requirements are infeasible on the declared COTS platform.

The [S1/G1 design template](S1_G1_template.md) expands these check families into twelve general review items and one conditional ML item, including design decisions, COTS coherence, HAL ladder, telemetry companion, and risk assessment.

---

## 7 S2 — Per-Service Implementation and System Integration

```mermaid
flowchart TD
    classDef base fill:#dbeafe,stroke:#2563eb,color:#1e3a8a
    classDef mod fill:#e0e7ff,stroke:#4f46e5,color:#312e81
    classDef test fill:#f0fdf4,stroke:#16a34a,color:#14532d
    classDef stub fill:#f3f4f6,stroke:#9ca3af,color:#374151,stroke-dasharray:5 3

    subgraph STEP1["Step 1 — Each service base first"]
        B["Implement base layer<br/>orchestration · HAL · routing"]:::base
        STUBS["Generate stubs<br/>from G1 contracts"]:::stub
        TD["Top-down integration<br/>base + all stubs"]:::test
        B --> STUBS --> TD
    end

    subgraph STEP2["Step 2 — Each service's modules (DAG order)"]
        IMPL["Implement module<br/>against contract"]:::mod
        UT["Unit test<br/>in isolation"]:::test
        BU["Bottom-up integration<br/>module + driver vs base"]:::test
        IMPL --> UT --> BU
    end

    TD --> STEP2
    STEP2 --> CONTRACT["Step 3 — Cross-service contract tests<br/>real services + fake peers"]:::test
    CONTRACT --> SYSTEM["Step 4 — System paths<br/>connected services"]:::test
```

Top-down (base → stubs) + bottom-up (module → driver → base) = **sandwich integration testing** [1][2][13].

Define cross-service contracts first so each service can be built independently against a deterministic fake peer. Connect real services after their local VL-0 floor passes. For each `SYS-*` allocated across services, execute a deterministic system-path test across the real service processes with simulated external inputs. This checks serialization, routing, state handoff, and recovery at the declared boundary; VL-1 and VL-2 add stronger environments and measurements.

*Future work (FW-005, §5.4).* If a service uses a supplied ML model, S2 implements its inference adapter and tests the declared preprocessing, output mapping, and failure behavior. The fake response exercises the surrounding module contract at VL-0; tests claiming model behavior use the identified weights.

### Data sources by verification level

The HAL substitution ladder determines what feeds the pipeline at each level. The **telemetry companion** runs during every test at every level.

| Level | Data source | HAL used | Telemetry companion |
|---|---|---|---|
| **VL-0** | Deterministic golden vectors (short, repeatable, edge-case) | Mock HAL | Records UC state; attached to evidence |
| **VL-1** | Synthetic I/Q at known SNR, modulation, channel conditions | Mock HAL | Records UC state; attached to evidence |
| **VL-2** | Real RF via COTS SDR; datasets generated following Build Package lab procedures with declared calibration and tolerances | Real HW HAL | Records UC state; attached to evidence |

### Golden vector governance

Each golden vector or synthetic capture used by the Mock HAL is a controlled artefact: it carries a unique identifier, SHA-256 digest, generation parameters, the condition it simulates (nominal, edge-case, degraded), and the expected output at the consuming module's contract. Changing a vector invalidates every evidence record that used it. The golden-vector set is versioned alongside the source code.

### Mandatory floor (VL-0) — cannot be skipped

| Component | Always required |
|---|---|
| **Base layer** | Unit test + top-down integration with stubs |
| **Each module** | Unit test + bottom-up integration with driver |
| **Each cross-service contract** | Producer and consumer contract tests using a fake peer, including version and failure cases |
| **Each cross-service SYS-* path** | Deterministic test across the connected service processes with simulated external inputs |
| **Telemetry companion** | Running and recording during all tests above; UC state attached to every evidence record |

---

## 8 G2 — Adaptive Verification Gate

### 8.1 Verification levels

```mermaid
flowchart LR
    classDef mandatory fill:#dcfce7,stroke:#16a34a,color:#14532d,stroke-width:2px
    classDef optional fill:#fef3c7,stroke:#d97706,color:#78350f,stroke-dasharray:5 3
    classDef hil fill:#fee2e2,stroke:#dc2626,color:#7f1d1d,stroke-dasharray:5 3

    VL0["VL-0 — Logic<br/>Unit + sandwich + service contracts<br/>Deterministic system paths · MANDATORY"]:::mandatory
    VL1["VL-1 — Mock / SIL<br/>+ measured multi-service system test<br/>Synthetic I/Q · GnuRadio · OPTIONAL"]:::optional
    VL2["VL-2 — HIL<br/>+ end-to-end acceptance where claimed<br/>Real HW · representative link · OPTIONAL"]:::hil

    VL0 -->|"user decides ▸"| VL1 -->|"user decides ▸"| VL2
```

Each level includes all tests from the levels below. The HAL substitution ladder (§5.5) determines what feeds the pipeline: Mock HAL at VL-0 and VL-1, Real HW HAL at VL-2. The telemetry companion runs at every level.

### 8.2 Adaptive rule

The user chooses the verification level per module and per system path, per cycle. Three constraints:

1. **Floor.** Every module and every declared cross-service contract and system path reaches VL-0 in every cycle.
2. **Honesty.** No module or end-to-end claim is higher than the environment actually tested. Passing services individually does not prove a cross-service requirement.
3. **Telemetry context.** Every evidence record includes the telemetry companion's readings for the compute unit during that test. Evidence produced while the UC was outside its declared operating envelope (temperature, CPU saturation, dropped buffers) is flagged and may be invalidated by the reviewer.

| Scenario | User declares | G2 checks |
|---|---|---|
| Fast iteration | VL-0 all | Unit + sandwich for every module; contract and deterministic path tests for connected services |
| DSP validation | VL-1 for DSP; VL-0 rest | Mock/SIL for DSP; VL-0 floor for every service path |
| Pre-release | VL-1 for the edge → UI display path; VL-2 for `iq_acquisition` | Measured multi-service path plus HIL acquisition |
| Full release | All modules and system paths at `required_vl` | Every claim at its S1-declared level |

### 8.3 Sub-gates

| Sub-gate | Fires when | Checks |
|---|---|---|
| **G2.0** | Always | Unit + sandwich, cross-service contract, and deterministic system-path tests pass; Mock HAL golden vectors; telemetry companion confirms UC nominal |
| **G2.1** | VL-1+ declared for a module or path | Mock HAL synthetic I/Q; Mock/SIL system tests across affected services pass; metrics within thresholds; telemetry companion confirms UC nominal |
| **G2.2** | VL-2 declared for a module or path | Real HW HAL on COTS SDR; datasets from Build Package lab procedures with declared calibration and tolerances; for cross-service paths, a representative link; measurements within criteria; telemetry companion confirms UC nominal |

*Future work (FW-005, §5.4).* For an ML-based module or path, G2 measures the supplied model *inside the implemented system* at the declared level and checks the relevant `SYS-*` criteria. The performance metadata received at S1 is context for test design, not a substitute for those measurements.

---

## 9 Feedback Routing

V-SIL produces two types of feedback. They are structurally different and must not be conflated.

```mermaid
flowchart TD
    classDef defect fill:#fef3c7,stroke:#d97706,color:#78350f
    classDef rfd fill:#fee2e2,stroke:#dc2626,color:#7f1d1d
    classDef stage fill:#e0f2fe,stroke:#0284c7,color:#0c4a6e
    classDef ext fill:#f3f4f6,stroke:#6b7280,color:#1f2937,stroke-width:2px

    FAIL["Gate failure"]:::defect
    CLS{"Defect<br/>or infeasibility?"}

    subgraph INTERNAL["Internal — Defect (fix within V-SIL)"]
        direction LR
        D_S1["S1 — design defect"]:::stage
        D_S2["S2 — module defect"]:::stage
    end

    subgraph EXTERNAL["External — RFD (Build Package must change)"]
        direction LR
        RFD["Request for Deviation"]:::rfd
        BP["Build Package<br/>author"]:::ext
        RFD --> BP
    end

    FAIL --> CLS
    CLS -->|"implementation<br/>or design"| INTERNAL
    CLS -->|"requirements<br/>infeasible"| EXTERNAL
```

### 9.1 Internal defect routing

A **defect** means V-SIL can fix it internally. The implementation or the design is wrong, but the requirements are achievable.

| Defect class | Routes to | Example |
|---|---|---|
| Design defect | S1 | DAG has undeclared dependency; cross-service contract or state ownership is incomplete |
| Module or integration defect | S2 | FFT output is wrong; UI deserializes a valid edge message incorrectly |

**Self-diagnosis:** if a module that was *not* changed fails during re-testing → undeclared dependency → design defect → S1.

### 9.2 Request for Deviation (RFD)

An **RFD** means the Build Package requirements are **infeasible on the declared COTS platform**. V-SIL cannot fix it internally — the constraints themselves must change. V-SIL **suspends** until the Build Package is updated and re-enters at S0.

An RFD can be emitted from **S1, G1, or any G2 sub-gate**. S0 and G0 do not emit one: S0 makes no judgement about feasibility and G0 checks structure only. Infeasibility discovered while implementing in S2 is reported through G2.

| Discovered at | Example |
|---|---|
| S1 | Pipeline latency exceeds requirement under any partitioning on this HW |
| G1 | Design review concludes that a latency budget cannot be met on this HW, by the reviewed design or by any other partitioning |
| G2.0 | Unit tests reveal that two normative requirements conflict mathematically |
| G2.1 | SIL metrics show P_d and P_fa cannot simultaneously meet thresholds |
| G2.2 | HIL shows real hardware noise floor exceeds assumed budget |

At S1 and G1 nothing has been measured yet, so the evidence is analysis and names no verification level (P4).

### 9.3 RFD contents

Per ECSS [16], MIL-HDBK-61A [17], and NASA NPR 7150.2 [18]:

```
Request for Deviation — RFD-001

  Conflicting requirements:
    STK-007: Latency ≤ 100 ms    (source: ITU-R SM.1880)
    STK-012: P_d ≥ 0.95 @ 10 dB  (source: national regulator)

  Evidence (from G2.1, VL-1):
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

### 9.4 Distinction summary

```mermaid
flowchart LR
    classDef defect fill:#fef3c7,stroke:#d97706,color:#78350f
    classDef rfd fill:#fee2e2,stroke:#dc2626,color:#7f1d1d

    D["Defect<br/>Requirements achievable<br/>Implementation wrong<br/>Fix inside V-SIL"]:::defect
    R["RFD<br/>Requirements infeasible<br/>COTS cannot deliver both<br/>Build Package must change"]:::rfd

    D ---|"different from"| R
```

---

## 10 Terminal Output

```
Verified Prototype — V-SIL v3
  Cycle: pre_release_01

  Module evidence:
    iq_acquisition:    VL-2 (HIL)  — Real HW HAL, HackRF One, FM 88–108 MHz
    fft_engine:        VL-1 (SIL)  — Mock HAL, golden I/Q (vectors v1.2, SHA bc3f…)
    feature_extractor: VL-1 (SIL)  — Mock HAL, synthetic PSD at known SNR
    classifier:        VL-0 (logic)— Mock HAL, deterministic vectors
    audio_demod:       VL-1 (SIL)  — Mock HAL, synthetic FM-modulated I/Q
    data_store:        VL-0 (logic)— Mock HAL, deterministic vectors
    dashboard:         VL-1 (SIL)  — edge messages on simulated link
    controls:          VL-0 (logic)— command and acknowledgement vectors
    alerts:            VL-0 (logic)— unit + sandwich integration
    history:           VL-0 (logic)— unit + sandwich integration

  Service and system-path evidence:
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
                  calibration: screening grade per Build Package;
                  tolerances: ±2.1 dBi declared by development team.
    VL-0 modules: VERIFIED at logic level only.
    SYS-002: VERIFIED across connected services with synthetic input;
             no real-link or HIL latency claim.
    Telemetry companion: UC nominal during all test executions.

  RFDs issued: 0
```

### 10.1 Optional future work register

After G2, the prototype may include proposals for later **software versions**. Each entry records an ID, the proposed capability or improvement, its origin and evidence, a candidate version, a decision owner, dependencies, and a proposed acceptance criterion. An empty register can be omitted. The Build Package author decides whether a proposal enters a later version; an accepted proposal becomes new input at S0 and G0. Future CI/CD automation is a possible infrastructure entry for a later version; building that pipeline is outside this version of V-SIL.

Only work explicitly outside the current cycle's approved scope belongs here. A failing current `SYS-*` remains a defect to correct or, if infeasible on the declared COTS platform, an RFD; the register cannot turn it into a passing claim.

```text
FW-001 — Automate V-SIL verification evidence in CI/CD
  Category: verification infrastructure
  Origin: repeated manual G2 execution in this cycle
  Candidate version: later software release
  Decision owner: Build Package author
  Dependency: stable test commands and report format
  Proposed acceptance: a pipeline reproduces the declared G2 checks
                       and links its reports to the cycle and source revision

FW-002 — Processor-in-the-Loop (PIL) as intermediate level
  Category: verification depth
  Origin: SOTA review; when UC ≠ development host, compiled code on the
          target processor may behave differently under timing constraints
  Candidate version: later software release
  Decision owner: Build Package author
  Dependency: target UC identified and accessible for cross-compilation
  Proposed acceptance: PIL level defined between VL-1 and VL-2 with
                       timing and scheduling checks on the target processor

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
          automated pipeline, and its S2 and G2 integration is not
          implemented yet (§5.4)
  Candidate version: later software release
  Decision owner: Build Package author
  Dependency: versioned Mock HAL or Real HW HAL datasets and a declared
              labelling procedure
  Proposed acceptance: a pipeline reproduces training from versioned data
                       and labels and links each model version to its
                       G2 evidence
```

---

## 11 References

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

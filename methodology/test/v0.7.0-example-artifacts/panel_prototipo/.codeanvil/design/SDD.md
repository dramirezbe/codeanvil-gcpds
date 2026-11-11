# S1 — Design of a System of Layered Services

> SYNTHETIC UI FIXTURE — simulated workflow and human verdicts, not a real V-SIL approval.

## Meta

| Field | Value |
|-------|-------|
| Project | Panel de prototipo |
| Cycle | 01_ui_demo |
| Date | 2026-11-11 10:06:29.129 |
| Author | Synthetic UI fixture |
| G0 approved | StRS SHA-256 20eeb8cb8a8062831c63560aed0401a2b8e16660fab450fd4c70909fe609439f; SyRS SHA-256 14d0158c2150d2e202d7e4786699b3cdc87ef0cdf99b60ad42ba22782d2669ed |
| Gate H | PASS — SIMULATED actor, 2026-11-11 10:06:29.129 |
| Services | SVC-001 |
| HAL mode | mock-only |
| Toolchain | SVC-001: demo_counter · Python 3.12 · uv · pytest |
| Status | approved at G1 — SIMULATED |

## 0. COTS envelope

### 0.1 Device inventory

| ID | Device | Role | Key constraints |
|----|--------|------|-----------------|
| HW-CPU | Generic COTS PC | Host | HWC-CPU-001; synthetic 512 MiB RAM minimum |

### 0.2 Physical topology

One host and a loopback browser; no external device or cable.

### 0.3 Physical interfaces (HW ↔ HW contracts)

Not applicable: all input is synthetic software data.

### 0.4 Deployment and links between services

| Service ID | Process / deployment target | HWC-* used | Links | Restart |
|------------|-----------------------------|------------|-------|---------|
| SVC-001 | Python process on host | HWC-CPU-001 | None | Resets sequence to 0 |

### 0.5 Runnable system entry point

| Field | Value |
|-------|-------|
| Project-root command | uv run --no-dev demo_counter |
| HAL mode for preview | mock-only; shipped RuntimeMockHAL |
| Services started | SVC-001; one HTTP process |
| Local URL / endpoint | http://127.0.0.1:8854/ |
| Visible result | Page polls /api/value and displays repeating 0, 1, 2 |
| Shutdown | Ctrl-C closes the HTTP server; no child process |

## 1. Building block view

### 1.1 System service view (level 0)

SVC-001 owns a local synthetic sequence and its browser presentation.
One service is sufficient: one deployment, state owner and restart boundary.

### 1.2 White box: each service (level 1)

SVC-001 base invokes its HAL and identity module; modules never call one another.

### 1.3 Base layer

#### 1.3.1 Orchestration

ThreadingHTTPServer, request-driven, best-effort; the base owns the sequence.

#### 1.3.2 HAL (Hardware Abstraction Layer)

SamplePort.read() returns one float; RuntimeMockHAL repeats [0, 1, 2].
No hardware IO occurs. Replacing the source changes only the HAL implementation.

#### 1.3.3 Data routing

GET /api/value → base → HAL.read() → identity(value) → JSON response.

#### 1.3.4 Verification kit

| Tool | Path | Language | Consumed by | Source section |
|------|------|----------|-------------|----------------|
| Mock HAL | verification/demo_counter/mock_hal/ | Python | Tests | §1.6 |
| Golden vectors | verification/golden/manifest.md and values.json | JSON | Tests | §3.2 |
| Telemetry | verification/telemetry/ | JSONL | Test runs | §1.7 |
| Stub | verification/demo_counter/stubs/ | Python | Base checks | §3.2 |
| Fake peers | verification/demo_counter/fakes/ | N/A | No other services | §3.4 |
| Driver | verification/demo_counter/drivers/ | Python | Tests | §4.4 |
| Level runner | verification/run.sh | Shell | S2/G2 | §4.4 |

### 1.4 Black boxes: modules

#### SVC-001/identity

| Field | Value |
|-------|-------|
| service_id | SVC-001 |
| Functional layer | Processing |
| Responsibility | Return the supplied numeric sample unchanged |
| depends_on | sample.v1 |
| provides | value.v1 |
| hw_dependency | false |
| required_vl | VL-0 |

VL-0 suffices for exact identity logic. VL-1 tests repeat the fixed vector.

### 1.6 HAL substitution ladder

#### Mock HAL

The runtime source is shipped in src/demo_counter/hal/port.py. The independent
kit source returns the declared [0, 1, 2] vector, repeated for 300 synthetic samples.
Generation uses Python only; Real HW HAL and calibration are out of scope.

| Vector ID | Simulated condition | SHA-256 digest | Parameters | Expected output |
|-----------|---------------------|---------------|------------|-----------------|
| GV-001 | Nominal / zero value | 853a5328e71938ba77fa56ed5209611f42ac3cb81d6509f8629d9f8b606a0360 | inputs [0,1,2] | [0,1,2] |

### 1.7 Telemetry companion

codeanvil telemetry samples the run.sh process tree every 0.1 seconds to JSONL.
Readings are attached by filename. Missing sensors are unavailable, never zero.
Illustrative envelope: process RSS ≤ 256 MiB, process CPU ≤ 200%, temperature
≤ 90 °C when available. Companion budget: 64 MiB RSS; no measured budget claim.
Dropped buffers and scheduling latency are not exposed by this minimal HAL.

## 2. Dependency view

### 2.1 Implementation dependency graph (DAG)

sample.v1/value.v1 → base with stub → identity → local HTTP integration.

### 2.2 Topological implementation order

| Step | Service | Module / integration | Depends on | Rationale |
|------|---------|----------------------|------------|-----------|
| 1 | SVC-001 | Contracts, kit and base | None | Establish ports |
| 2 | SVC-001 | identity | sample.v1 | Pure transformation |
| 3 | SVC-001 | HTTP smoke | value.v1 | Exercise package entry point |

### 2.3 Runtime interaction graph

Browser → SVC-001 base → HAL and identity → browser. No service message loop.

## 3. Interface view

### 3.1 HW → SW contracts

Not applicable: SamplePort is backed by a software generator only.

### 3.2 SW → SW contracts

#### sample.v1 / value.v1

| Field | Value |
|-------|-------|
| Producer | Base through SamplePort / SVC-001 identity |
| Consumer(s) | SVC-001 identity / base HTTP handler |
| Data type | float |
| Shape / structure | One finite scalar; JSON response {"value": number} |
| Units | Dimensionless |
| Rate / frequency | One per request; preview polls once per second |
| Maximum latency | Best-effort; no calibrated latency requirement |
| Schema version | v1 |

Stub recipe: identity stub returns its float argument. Vectors: 0→0, 1→1, 2→2.
The base serializes JSON; GET / serves static HTML. Unknown paths return 404.

### 3.3 SW → HW contracts

Not applicable: no actuator or hardware access.

### 3.4 Service → service contracts

Not applicable: one service. Browser requests are local presentation IO.

## 4. Traceability

### 4.1 Requirements → services, modules and paths

| Requirement | Summary | Service(s) | Module(s) | Path | Acceptance owner |
|-------------|---------|------------|-----------|------|------------------|
| SYS-ANAL-001 | Exact synthetic values | SVC-001 | identity | PATH-001 | Base |

### 4.2 Modules → requirements (inverse view)

SVC-001/identity satisfies SYS-ANAL-001.

### 4.3 Normative constraints → contracts

No normative obligations were supplied in this synthetic Build Package.

### 4.4 System paths and end-to-end evidence

| Path ID | SYS-* | Services and contracts | Observable result | Budget | required_vl | Criterion |
|---------|-------|------------------------|-------------------|--------|-------------|-----------|
| PATH-001 | SYS-ANAL-001 | SVC-001 sample.v1 → value.v1 | HTTP values 0,1,2 | No timing claim | VL-0 | Exact equality and clean shutdown |

## 5. Design decisions

### DEC-001: One Python service with one pure module

- Status: accepted — simulated fixture decision.
- Context: exercise UI artifacts with the smallest runnable system.
- Alternatives: multiple processes; a single static mock page.
- Decision: one stdlib HTTP process, runtime Mock HAL and pure identity function.
- Rationale: preserves a real entry point and service/kit separation.
- Consequences: no production RF, calibration or metrology claim.
- Requirements affected: STK-ANAL-001, SYS-ANAL-001.

## 6. Risks and known infeasibilities

| ID | Risk | Affected requirement | Evidence | Mitigation | Potential RFD? |
|----|------|----------------------|----------|------------|----------------|
| RSK-001 | Fixture PASS mistaken for approval | SYS-ANAL-001 | ANALYSIS (no VL) | Visible synthetic markers | no |

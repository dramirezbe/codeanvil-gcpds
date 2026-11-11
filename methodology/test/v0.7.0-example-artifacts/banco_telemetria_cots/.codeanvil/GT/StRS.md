# PROJECT: Banco de telemetría COTS

> SYNTHETIC UI FIXTURE — simulated workflow and human verdicts, not a real V-SIL approval.

## Stakeholder Requirements Specification (StRS)

## Document Metadata

| Field | Value |
|-------|-------|
| **Document ID** | `STRS-DEMO-001` |
| **Project** | Banco de telemetría COTS |
| **Organization** | UI fixtures |
| **Version** | 1.0.0 |
| **Classification** | `INTERNAL` |

## 1. Introduction

### 1.1 Purpose

Specify the synthetic counter preview used to exercise the UI.

### 1.2 Scope

One local Python service; Mock HAL only; no RF or real-hardware claim.

### 1.3 Definitions, Acronyms, and Abbreviations

| Term | Definition |
|------|------------|
| Mock HAL | Deterministic software source returning 0, 1, 2 repeatedly |

### 1.4 References

| Ref ID | Document | Version |
|--------|----------|---------|
| `REF-DS-001` | Synthetic COTS envelope for UI data only | 1.0 |

### 1.5 Document Overview

Overview.

### 1.6 Hardware Inventory

| Component ID | Component Name | Role | Manufacturer | Part Number |
|--------------|----------------|------|--------------|-------------|
| `HW-CPU` | Generic COTS PC | Local Python host | Generic | PC |

## 2. Overall System Description

### 2.1 Product Perspective

An isolated local preview, unrelated to the project label's real domain.

### 2.2 Product Functions

Serve a page and expose the next synthetic value as JSON.

### 2.3 User Characteristics

| User Type | Description | Technical Level |
|-----------|-------------|-----------------|
| Engineer | Operates it | `EXPERT` |

### 2.4 Constraints

Loopback HTTP; Python 3.12+; at least 512 MiB RAM in the synthetic envelope.

### 2.5 Assumptions and Dependencies

The fixture is software-only; no hardware measurements are asserted.

### 2.6 Block Diagram

Mock HAL → service base → identity module → HTTP response.

### 2.7 Bus and Interface Topology

| From | To | Bus/Protocol | Data Rate (theoretical) | Data Rate (sustained) |
|------|----|--------------|-------------------------|----------------------|
| HW-CPU | Local browser | Loopback HTTP | Not applicable | One request per second |

## 3. Specific Requirements

**`STK-ANAL-001` — Display a synthetic value**

| Field | Value |
|-------|-------|
| **Type** | `FUNCTIONAL` |
| **Priority** | `MUST` |
| **Status** | `APPROVED` |
| **Verification** | `TEST` |
| **Dependencies** | — |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `NOT_APPLICABLE` |

**Description:**

The system SHALL show successive synthetic values 0, 1, 2 in a local browser.

**Acceptance Criteria:**

1. [ ] The page displays 0, 1, 2 in order and repeats without a device.

**`HWC-CPU-001` — Host memory envelope**

| Field | Value |
|-------|-------|
| **Component** | `HW-CPU` |
| **Parameter** | Available host RAM |
| **Limit type** | `MIN` |
| **Value** | 512 MiB |
| **Value max** | — |
| **Source** | `DATASHEET` |
| **Source ref** | `REF-DS-001` — Specifications |
| **Impact** | `HARD` |
| **Status** | `CONFIRMED` |
| **Standard(s)** | — |
| **Clause** | — |
| **Compliance** | `NOT_APPLICABLE` |

## 4. External Interface Requirements

### 4.1 User Interfaces

GET / serves HTML. GET /api/value returns {"value": number}.

## 5. Non-Functional Requirements

### 5.1 Performance

A single local user; no throughput or calibrated latency claim.

## 6. Traceability

| Block ID | Subsystem | Standard(s) | Compliance | Test Case |
|----------|-----------|-------------|------------|-----------|
| `STK-ANAL-001` | Test | — | NOT_APPLICABLE | TC-001 |
| `HWC-CPU-001` | Test | — | NOT_APPLICABLE | TC-003 |

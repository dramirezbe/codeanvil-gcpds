# PROJECT: Monitor de ocupación FM

> SYNTHETIC UI FIXTURE — simulated workflow and human verdicts, not a real V-SIL approval.

## System Requirements Specification (SyRS)

## Document Metadata

| Field | Value |
|-------|-------|
| **Document ID** | `SYRS-DEMO-001` |
| **Project** | Monitor de ocupación FM |
| **Organization** | UI fixtures |
| **Version** | 1.0.0 |
| **Classification** | `INTERNAL` |

## 1. Introduction

### 1.1 Purpose

Define the software-only acceptance vector for the counter.

### 1.2 Scope

Mock-only preview; VL-0 logic and optional VL-1 synthetic sequence checks.

### 1.3 Definitions, Acronyms, and Abbreviations

| Term | Definition |
|------|------------|
| Value | Dimensionless synthetic sample |

### 1.4 References

| Ref ID | Document | Version |
|--------|----------|---------|
| `REF-001` | IEEE/ISO/IEC 29148:2018 | 2018 |

### 1.5 Document Overview

One system requirement and no laboratory inputs.

## 2. Measurement Framework

### 2.1 Measurand Catalog

| Measurand ID | Quantity | Unit |
|--------------|----------|------|
| M-001 | Synthetic sample | dimensionless |

### 2.2 Method Selection and Rationale

Identity mapping of an explicit repeating [0, 1, 2] sequence.

### 2.3 Normative-to-Method Mapping

| Standard(s) | Clause | Measurand | Method |
|-------------|--------|-----------|--------|
| — | — | M-001 | Exact equality with declared golden values |

## 3. System Requirements

**`SYS-ANAL-001` — Synthetic value identity**

| Field | Value |
|-------|-------|
| **Type** | `FUNCTIONAL` |
| **Parameter** | Synthetic numeric value |
| **Method** | Identity mapping; no numerical correction |
| **Traces to** | `STK-ANAL-001`, `HWC-CPU-001` |
| **Standard(s)** | — |

**Acceptance Criteria:**

1. [ ] Inputs [0, 1, 2] produce [0, 1, 2] with absolute error 0.

## 4. Correction Chains

Not applicable: no lab inputs in the Build Package.

## 5. Uncertainty Budgets

Not applicable: no lab inputs in the Build Package.

## 6. Field Measurement Protocols

Not applicable: no lab inputs in the Build Package.

## 7. Traceability

| Specification ID | Traces to | Test Case |
|------------------|-----------|-----------|
| `SYS-ANAL-001` | `STK-ANAL-001` | TC-001 |

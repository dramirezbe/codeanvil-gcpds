# [PROJECT: _project_name_]

## System Requirements Specification (SyRS)

> **Standard:** IEEE/ISO/IEC 29148:2018 §9.5 — *System requirements specification.*
>
> **Template version:** 4.0.0  
> **Creation date:** _YYYY-MM-DD_  
> **Last modified:** _YYYY-MM-DD_  
> **Document status:** `DRAFT` | `IN_REVIEW` | `APPROVED` | `OBSOLETE`

---

## Document Metadata

| Field                  | Value                                    |
|------------------------|------------------------------------------|
| **Document ID**        | `SYRS-_ACRONYM_-_NNN_`                   |
| **Project**            | _full project name_                      |
| **Organization**       | _owning entity_                          |
| **Version**            | _X.Y.Z_ (SemVer)                        |
| **Classification**     | `PUBLIC` \| `INTERNAL` \| `CONFIDENTIAL`  |
| **Author(s)**          | _name (role)_                            |
| **Reviewer(s)**        | _name (role)_                            |
| **Approver(s)**        | _name (role)_                            |

### Companion Documents

| Document ID             | Title                                    | Relationship                      |
|-------------------------|------------------------------------------|-----------------------------------|
| `STRS-_ACRONYM_-_NNN_`  | _Stakeholder Requirements Specification_ | Upstream contract (G0 pair)       |
| `SRS-_ACRONYM_-_NNN_`   | _Software Requirements Specification_    | Software design output (G1)       |

> **Note:** The SyRS is the detailed per-measurand technical specification derived
> from the G0-validated StRS. Every SYS- block carries a `Traces to` field pointing
> at the StRS block(s) it derives from, and a `Standard(s)` field citing its
> normative source. Compliance traceability is inline: §2.3 maps each normative
> source to the methods that realize it (this replaces a standalone compliance
> matrix).

### Change Log

| Version | Date       | Author       | Change Description               |
|---------|------------|--------------|----------------------------------|
| 0.1.0   | YYYY-MM-DD | _name_       | Initial creation                 |

---

## 1. Introduction

### 1.1 Purpose

_What this document specifies and who its audience is._

### 1.2 Scope

_Which measurands, methods, and system behaviors this document covers — derived from the StRS scope._

### 1.3 Definitions, Acronyms, and Abbreviations

| Term       | Definition                                              |
|------------|---------------------------------------------------------|
| SyRS       | System Requirements Specification (this document)       |
| StRS       | Stakeholder Requirements Specification — upstream document |
| _TERM_     | _Precise definition_                                    |

### 1.4 References

| Ref ID     | Document                                                | Version / Date  |
|------------|---------------------------------------------------------|-----------------|
| `REF-001`  | _Title_                                                 | _vX.Y / date_   |

### 1.5 Document Overview

_Brief description of the structure of the remaining sections._

---

## 2. Measurement Framework

### 2.1 Measurand Catalog

_All measurands covered by this specification._

| Measurand ID | Quantity            | Unit     | Method Family            | StRS Traces        |
|--------------|---------------------|----------|--------------------------|--------------------|
| `MEAS-001`   | _e.g. channel power_ | _dBm_   | _e.g. FFT-based PSD_     | `STK-…`, `NRM-…`   |

### 2.2 Method Selection and Rationale

_For each method family: the selected method, the rejected alternatives, and why._

| Method Family | Selected Method | Rejected Alternatives | Rationale |
|---------------|-----------------|-----------------------|-----------|
| _family_      | _method_        | _alternatives_        | _why this method_ |

### 2.3 Normative-to-Method Mapping

_Inline compliance traceability (replaces a standalone compliance matrix): which
normative source is satisfied by which method, and in which SYS- blocks._

| Normative Source | Clause | Realized By (Method)      | Blocks        | Compliance     |
|------------------|--------|---------------------------|---------------|----------------|
| _standard_       | _§x.y_ | _method_                  | `SYS-…`       | `COMPLIANT` \| `PARTIAL` \| `NOT_APPLICABLE` \| `PENDING` |

---

## 3. System Requirements

### Block ID Convention

```
SYS-[SUB]-[NNN]
```

| Segment | Rule                                    | Example            |
|---------|-----------------------------------------|--------------------|
| `SUB`   | 2–4 uppercase letters — measurand group | `PSD`, `ANT`, `UNC` |
| `NNN`   | 3-digit zero-padded sequence            | `001`, `042`       |

> **Regex:** `^SYS-[A-Z]{2,4}-\d{3}$`  
> Block IDs share one namespace with the StRS — no ID may appear in both documents.

### Fields per Block

| Field            | Required | Type              | Description                                                     |
|------------------|----------|-------------------|-----------------------------------------------------------------|
| `id`             | yes      | string            | Unique ID per the convention above                              |
| `title`          | yes      | string (≤120 ch)  | Descriptive name                                                |
| `type`           | yes      | string            | What the block specifies (e.g. `MEASUREMENT`, `PROCESSING`, `PROTOCOL`, `QUALITY`) |
| `parameter`      | yes      | string            | The measurand / parameter being specified                       |
| `method`         | yes      | string            | The method that realizes it (see §2.2)                          |
| `traces_to`      | yes      | string[]          | StRS block ID(s) this block derives from (`NRM-`, `HWC-`, `STK-`) |
| `standard(s)`    | yes      | string            | Normative source for this specification (never —)               |
| `acceptance_criteria` | yes  | string[]          | Verifiable conditions (≥ 1)                                     |
| `notes`          | no       | string            | Technical remarks                                               |

### Block Format

Each block is a self-contained block:

---

**`SYS-[SUB]-[NNN]` — _Specification title_**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `MEASUREMENT` \| `PROCESSING` \| `PROTOCOL` \| `QUALITY`  |
| **Parameter**          | _measurand or parameter being specified_                  |
| **Method**             | _selected method (see §2.2)_                               |
| **Traces to**          | `STK-…`                                                   |
| **Standard(s)**        | _normative source_                                         |

**Acceptance Criteria:**

1. [ ] _Verifiable condition 1_
2. [ ] _Verifiable condition 2_

**Notes:**  
_Technical remarks. Omit this field if there is nothing to add._

---

_[Repeat the block for each system requirement]_

---

### 3.1 [_Measurand Group 1: Name_]

_Place SYS- blocks here, grouped by measurand or method family._

---

## 4. Correction Chains

_Per-block correction chains (antenna factor, cable loss, impedance matching, …).
Structure: source → correction term → uncertainty contribution. MVP scope: the
section must exist; completeness of each chain is a G0 v2 check._

| Block        | Correction        | Model / Source          | Applied Where       |
|--------------|-------------------|-------------------------|---------------------|
| `SYS-…`      | _antenna factor_  | _datasheet / calibration_ | _PSD computation_ |

---

## 5. Uncertainty Budgets

_GUM uncertainty budgets per measurand/component. MVP scope: this section must
exist (placeholders acceptable); budget structure and completeness are G0 v2 checks._

| Measurand | Component        | Source u(x) | Distribution | Sensitivity c | Standard u |
|-----------|------------------|-------------|--------------|---------------|------------|
| _quantity_ | _component_      | _value_     | _type_       | _c_           | _u_        |

---

## 6. Field Measurement Protocols

_Field procedures: setup, calibration, execution, and recording for each protocol._

| Protocol ID | Applies To (Blocks)  | Setup | Calibration | Execution |
|-------------|----------------------|-------|-------------|-----------|
| `PROTO-001` | `SYS-…`              | _…_   | _…_         | _…_       |

---

## 7. Traceability

| Block ID       | Parameter      | Standard Ref   | StRS Traces        | Test Case   |
|----------------|----------------|----------------|--------------------|-------------|
| `SYS-[SUB]-[NNN]` | _parameter_  | _standard_     | `STK-…`            | _TC-NNN_    |

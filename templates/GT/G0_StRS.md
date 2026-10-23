# [PROJECT: _project_name_]

## Stakeholder Requirements Specification (StRS)

> **Standard:** IEEE/ISO/IEC 29148:2018 §9.4 — *Stakeholder requirements specification.*
>
> **Template version:** 4.0.0  
> **Creation date:** _YYYY-MM-DD_  
> **Last modified:** _YYYY-MM-DD_  
> **Document status:** `DRAFT` | `IN_REVIEW` | `APPROVED` | `OBSOLETE`

---

## Document Metadata

| Field                  | Value                                    |
|------------------------|------------------------------------------|
| **Document ID**        | `STRS-_ACRONYM_-_NNN_`                   |
| **Project**            | _full project name_                      |
| **Organization**       | _owning entity_                          |
| **Version**            | _X.Y.Z_ (SemVer)                        |
| **Classification**     | `PUBLIC` \| `INTERNAL` \| `CONFIDENTIAL`  |
| **Author(s)**          | _name (role)_                            |
| **Reviewer(s)**        | _name (role)_                            |
| **Approver(s)**        | _name (role)_                            |

### Companion Documents

| Document ID            | Title                                    | Relationship                    |
|------------------------|------------------------------------------|---------------------------------|
| `SYRS-_ACRONYM_-_NNN_` | _System Requirements Specification_      | Derived per-measurand technical specification (G0 pair) |
| `SRS-_ACRONYM_-_NNN_`  | _Software Requirements Specification_    | Software design output (G1)     |

> **Note:** The StRS is the system-level view: all subsystems, all frequency bands,
> all measurement types. It merges what used to be a separate hardware-constraints
> document (COTS platform envelope, §1.6/§2.6/§2.7 and the HWC- blocks) and carries
> compliance traceability inline on every block instead of a standalone compliance
> matrix. The SyRS derives per-measurand technical detail from this document; every
> stakeholder requirement (STK-) must be covered by at least one SyRS specification.

### Change Log

| Version | Date       | Author       | Change Description               |
|---------|------------|--------------|----------------------------------|
| 0.1.0   | YYYY-MM-DD | _name_       | Initial creation                 |

---

## 1. Introduction

### 1.1 Purpose

_What this document specifies and who its audience is._

### 1.2 Scope

_System name, what it does, what it does NOT do, and its benefits._

### 1.3 Definitions, Acronyms, and Abbreviations

| Term       | Definition                                              |
|------------|---------------------------------------------------------|
| StRS       | Stakeholder Requirements Specification (this document)   |
| SyRS       | System Requirements Specification — companion document   |
| _TERM_     | _Precise definition_                                    |

### 1.4 References

| Ref ID     | Document                                                | Version / Date  |
|------------|---------------------------------------------------------|-----------------|
| `REF-001`  | _Title_                                                 | _vX.Y / date_   |

### 1.5 Document Overview

_Brief description of the structure of the remaining sections._

### 1.6 Hardware Inventory

_All hardware components whose constraints are documented here (COTS platform envelope)._

| Component ID | Component Name      | Role in System                | Manufacturer    | Part Number     |
|-------------|---------------------|-------------------------------|-----------------|-----------------|
| `HW-001`    | _component name_    | _what it does in the system_  | _manufacturer_  | _part number_   |

---

## 2. Overall System Description

### 2.1 Product Perspective

_Context: new system, replacement, or extension. Relationship to other systems._

### 2.2 Product Functions

_High-level summary of main functions (not requirement-level detail)._

### 2.3 User Characteristics

| User Type       | Description                        | Technical Level                      |
|-----------------|------------------------------------|--------------------------------------|
| _role_          | _what they do with the system_     | `BASIC` \| `TECHNICAL` \| `EXPERT`  |

### 2.4 Constraints

_Narrative summary of design constraints. Detailed hardware limits appear as HWC- blocks in §3._

### 2.5 Assumptions and Dependencies

_Conditions assumed true for the requirements to hold._

### 2.6 Block Diagram

_Textual or graphical representation of how the hardware components are interconnected._

### 2.7 Bus and Interface Topology

| From       | To         | Bus/Protocol | Data Rate (theoretical) | Data Rate (sustained) |
|------------|------------|-------------|-------------------------|----------------------|
| _HW-001_   | _HW-002_   | _protocol_  | _theoretical_           | _measured_           |

---

## 3. Specific Requirements

### Block ID Convention

Each block uses a type prefix that names what the block is:

| Type | Prefix | Meaning | Regex |
|------|--------|---------|-------|
| Normative obligation | `NRM` | A binding obligation from a normative source (ITU, ICNIRP, ANE, GUM, ISO…) | `^NRM-[A-Z]{2,8}-\d{3}$` |
| COTS constraint | `HWC` | A parametric limit of the selected hardware platform | `^HWC-[A-Z]{2,4}-\d{3}$` |
| Stakeholder requirement | `STK` | A functional or non-functional stakeholder need | `^STK-[A-Z]{2,4}-\d{3}$` |

```
<TYPE>-[SUB]-[NNN]
```

| Segment | Rule                                    | Example              |
|---------|-----------------------------------------|----------------------|
| `TYPE`  | `NRM`, `HWC`, or `STK`                  | `STK`, `HWC`         |
| `SUB`   | 2–8 uppercase letters — subcategory     | `EMC`, `SDR`, `ICNIRP` |
| `NNN`   | 3-digit zero-padded sequence            | `001`, `042`         |

> The block IDs form **one namespace**: no two blocks in this document may share an ID.

### Fields per Block

Common fields — **every block, every type**:

| Field           | Required | Type             | Description                                            |
|-----------------|----------|------------------|--------------------------------------------------------|
| `id`            | yes      | string           | Unique ID per the convention above                     |
| `title`         | yes      | string (≤120 ch) | Descriptive name                                       |
| `Standard(s)`   | yes*     | string           | Inline compliance traceability — applicable normative reference(s), or — when none applies |
| `Clause`        | yes*     | string           | Inline compliance traceability — clause/section within the standard, or — |
| `Compliance`    | yes      | enum             | Inline compliance traceability — see **Compliance values** |

> *The `Standard(s)` and `Clause` **rows must exist** on every block; they may hold `—`
> when no normative source applies. For NRM- blocks both must hold a concrete value —
> a normative obligation always cites its source.

Stakeholder requirement (`STK-`) fields:

| Field                  | Required | Type              | Description                                                     |
|------------------------|----------|-------------------|-----------------------------------------------------------------|
| `type`                 | yes      | enum              | See **Type values** below                                       |
| `priority`             | yes      | enum              | See **Priority values** below                                   |
| `status`               | yes      | enum              | See **Status values** below                                     |
| `verification`         | yes      | enum              | See **Verification values** below                               |
| `dependencies`         | no       | string[]          | IDs of blocks this one depends on                               |
| `notes`                | no       | string            | Technical or implementation remarks                             |
| `phase`                | no       | string            | Implementation phase (e.g. `2026`, `PHASE_2`)                   |

Normative obligation (`NRM-`) fields:

| Field                  | Required | Type              | Description                                                     |
|------------------------|----------|-------------------|-----------------------------------------------------------------|
| `priority`             | yes      | enum              | **Priority values** below                                       |
| `status`               | yes      | enum              | **Status values** below                                         |
| `standard(s)`          | yes      | string            | The normative source (must be concrete, never —)                |
| `clause`               | yes      | string            | The clause/section within the source (must be concrete)         |
| `compliance`           | yes      | enum              | **Compliance values** below                                     |

COTS constraint (`HWC-`) fields:

| Field              | Required | Type              | Description                                                     |
|--------------------|----------|-------------------|-----------------------------------------------------------------|
| `component`        | yes      | string            | Component ID from the Hardware Inventory (§1.6)                 |
| `parameter`        | yes      | string            | The physical/technical parameter being constrained              |
| `limit_type`       | yes      | enum              | **Limit type values** below                                     |
| `value`            | yes*     | string            | The limit with units (e.g. `6 GHz`, `8 bit`)                    |
| `value_min`        | cond.    | string            | Lower bound — required when `limit_type` = `RANGE`              |
| `value_max`        | cond.    | string            | Upper bound — required when `limit_type` = `RANGE`              |
| `source`           | yes      | enum              | **Source values** below                                         |
| `source_ref`       | yes      | string            | Reference ID from §1.4 + page/section                           |
| `impact`           | yes      | enum              | **Impact values** below                                         |
| `status`           | yes      | enum              | **Status values** (constraint confidence) below                 |
| `notes`            | no       | string            | Technical remarks, measurement conditions, workarounds          |

> *`value` is required for all `limit_type` except `RANGE`, which uses `value_min` + `value_max` instead.

### Enumeration Values

**Type** — classifies what a stakeholder requirement specifies:

| Value             | Meaning                                                           |
|-------------------|-------------------------------------------------------------------|
| `FUNCTIONAL`      | A behavior the system must exhibit (input → output / action)      |
| `NON_FUNCTIONAL`  | A quality attribute (performance, accuracy, reliability, etc.)    |
| `INTERFACE`       | An external boundary the system must connect to                   |
| `CONSTRAINT`      | A design restriction imposed on the implementation                |

**Priority** — MoSCoW classification:

| Value    | Meaning                                           |
|----------|---------------------------------------------------|
| `MUST`   | Mandatory — the system is unacceptable without it |
| `SHOULD` | Important but not blocking delivery               |
| `COULD`  | Desirable if time and resources allow              |
| `WONT`   | Explicitly excluded from this release              |

**Verification** — how compliance will be confirmed:

| Value           | Meaning                                                         |
|-----------------|-----------------------------------------------------------------|
| `INSPECTION`    | Visual or document review                                       |
| `DEMONSTRATION` | Operate the system and observe correct behavior                 |
| `TEST`          | Execute a formal test procedure with pass/fail criteria         |
| `ANALYSIS`      | Mathematical or statistical evaluation (models, simulations)    |

**Status** — lifecycle state of a requirement or obligation:

| Value         | Meaning                                    |
|---------------|--------------------------------------------|
| `PROPOSED`    | Drafted, not yet reviewed                  |
| `APPROVED`    | Reviewed and accepted                      |
| `IMPLEMENTED` | Code or design complete                    |
| `VERIFIED`    | Passed its verification method             |
| `REJECTED`    | Reviewed and discarded                     |

**Compliance** — inline compliance status (applies to every block):

| Value             | Meaning                                                              |
|-------------------|----------------------------------------------------------------------|
| `COMPLIANT`       | The block satisfies the cited normative requirement                  |
| `PARTIAL`         | Partially satisfied — gap documented in notes                        |
| `NOT_APPLICABLE`  | No cited normative source applies to this block                      |
| `PENDING`         | Compliance not yet assessed                                          |

**Limit type** — how a hardware parameter is bounded:

| Value    | Meaning                                       | Uses field(s)          |
|----------|-----------------------------------------------|------------------------|
| `MAX`    | Upper bound — must not exceed                 | `value`                |
| `MIN`    | Lower bound — must meet or exceed             | `value`                |
| `RANGE`  | Acceptable range (both bounds)                | `value_min`, `value_max` |
| `FIXED`  | Exact value imposed by hardware, not tunable  | `value`                |
| `ENUM`   | One of a fixed set of discrete values         | `value` (comma-separated list) |

**Source** — where a constraint value comes from:

| Value        | Meaning                                                              |
|--------------|----------------------------------------------------------------------|
| `DATASHEET`  | Published manufacturer datasheet                                     |
| `DRIVER_API` | Driver or firmware API documentation                                 |
| `MEASURED`   | Laboratory or field measurement (cite report in `source_ref`)        |
| `DERIVED`    | Calculated from other constraints or system-level analysis           |

**Impact** — how hard a hardware limit is:

| Value           | Meaning                                                          |
|-----------------|------------------------------------------------------------------|
| `HARD`          | Physical/electrical limit — cannot be exceeded by any means      |
| `SOFT`          | Practical limit — can be partially overcome with software or design mitigation |
| `INFORMATIONAL` | Characteristic that shapes design decisions but does not block   |

**Constraint status** — confidence in a hardware limit value:

| Value         | Meaning                                                        |
|---------------|----------------------------------------------------------------|
| `CONFIRMED`   | Verified against datasheet or measurement                      |
| `PRELIMINARY` | Estimated or extrapolated — requires confirmation              |
| `DEPRECATED`  | No longer applicable (hardware changed or constraint removed)  |

---

### Block Format

Each block is a self-contained block:

---

**`[TYPE]-[SUB]-[NNN]` — _Block title_**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL` \| `NON_FUNCTIONAL` \| `INTERFACE` \| `CONSTRAINT` |
| **Priority**           | `MUST` \| `SHOULD` \| `COULD`                            |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `INSPECTION` \| `DEMONSTRATION` \| `TEST` \| `ANALYSIS`   |
| **Standard(s)**        | _Normative references, or_ —                              |
| **Clause**             | _Clause within the standard, or_ —                        |
| **Compliance**         | `COMPLIANT` \| `PARTIAL` \| `NOT_APPLICABLE` \| `PENDING` |
| **Dependencies**       | _Block IDs, or_ —                                         |
| **Phase**              | _Implementation phase_                                    |

**Description:**  
The system SHALL _[verifiable action, with quantitative parameters where applicable]_.

**Acceptance Criteria:**

1. [ ] _Verifiable condition 1_
2. [ ] _Verifiable condition 2_

**Notes:**  
_Technical remarks. Omit this field if there is nothing to add._

---

_[Repeat the block for each requirement]_

---

### 3.1 [Normative Obligations: Name]

_NRM- blocks grouped by normative source. Example:_

---

**`NRM-STD-001` — _Normative obligation title_**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Standard(s)**        | _e.g. ITU-R SM.1537_                                      |
| **Clause**             | _e.g. §5.2_                                               |
| **Compliance**         | `COMPLIANT` \| `PARTIAL` \| `NOT_APPLICABLE` \| `PENDING` |

**Description:**  
The system SHALL _[obligation imposed by the cited normative source]_.

**Acceptance Criteria:**

1. [ ] _Verifiable compliance condition 1_

---

### 3.2 [Stakeholder Requirements: Category Name]

_STK- blocks grouped by category (architecture, parameterization, connectivity, …)._

---

**`STK-SUB-001` — _Stakeholder requirement title_**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL`                                              |
| **Priority**           | `MUST`                                                    |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `TEST`                                                    |
| **Standard(s)**        | _Normative reference, or_ —                               |
| **Clause**             | _Clause, or_ —                                            |
| **Compliance**         | `NOT_APPLICABLE`                                          |
| **Dependencies**       | —                                                         |

**Description:**  
The system SHALL _[verifiable stakeholder need]_.

**Acceptance Criteria:**

1. [ ] _Verifiable condition 1_

---

### 3.3 [Platform Constraints: Component Group Name]

_HWC- blocks grouped by component (SDR, CPU, bus, GPS, power, storage). Example:_

---

**`HWC-COMP-001` — _Constraint title_**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Component**          | `HW-001`                                                  |
| **Parameter**          | _Physical/technical parameter_                            |
| **Limit type**         | `RANGE`                                                   |
| **Value min**          | _lower bound_                                             |
| **Value max**          | _upper bound_                                             |
| **Source**             | `DATASHEET` \| `DRIVER_API` \| `MEASURED` \| `DERIVED`   |
| **Source ref**         | `REF-001` §section / page                                 |
| **Impact**             | `HARD` \| `SOFT` \| `INFORMATIONAL`                      |
| **Status**             | `CONFIRMED` \| `PRELIMINARY`                              |
| **Standard(s)**        | —                                                         |
| **Clause**             | —                                                         |
| **Compliance**         | `NOT_APPLICABLE`                                          |

**Notes:**  
_Technical remarks. Omit this field if there is nothing to add._

---

_Derived constraints (combining multiple components or system-level analysis) use the
same HWC- block format with `source` = `DERIVED`; group them in their own subsection._

---

## 4. External Interface Requirements

### 4.1 User Interfaces
### 4.2 Hardware Interfaces
### 4.3 Software Interfaces
### 4.4 Communication Interfaces

---

## 5. Non-Functional Requirements

### 5.1 Performance
### 5.2 Security
### 5.3 Reliability / Availability
### 5.4 Maintainability
### 5.5 Portability

---

## 6. Traceability

| Block ID           | Business Objective | Standard Ref   | Compliance     | Test Case   | Component     |
|--------------------|--------------------|----------------|----------------|-------------|---------------|
| `[TYPE]-[SUB]-[NNN]` | _OBJ-NNN_        | _standard_     | `COMPLIANT`    | _TC-NNN_    | _component_   |

> Every block under §3 must appear in this table.

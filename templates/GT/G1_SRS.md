# [PROJECT: _project_name_]

## Software Requirements Specification (SRS)

> **Standard:** IEEE/ISO/IEC 29148:2018 §9.6 — *Software requirements specification.*
>
> **Template version:** 4.0.0  
> **Creation date:** _YYYY-MM-DD_  
> **Last modified:** _YYYY-MM-DD_  
> **Document status:** `DRAFT` | `IN_REVIEW` | `APPROVED` | `OBSOLETE`

---

## Document Metadata

| Field                  | Value                                    |
|------------------------|------------------------------------------|
| **Document ID**        | `SRS-_ACRONYM_-_NNN_`                    |
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
| `STRS-_ACRONYM_-_NNN_` | _Stakeholder Requirements Specification_ | G0-validated upstream contract  |
| `SYRS-_ACRONYM_-_NNN_` | _System Requirements Specification_      | G0-validated upstream contract  |

> **Note:** The SRS is the **software engineering output of G1** — it is produced
> after StRS + SyRS pass G0, and it is validated by G1 (not G0). Every REQ- block
> traces back to a SyRS SYS- block; the design never invents requirements the
> upstream pair does not justify.

### Change Log

| Version | Date       | Author       | Change Description               |
|---------|------------|--------------|----------------------------------|
| 0.1.0   | YYYY-MM-DD | _name_       | Initial creation                 |

---

## 1. Introduction

### 1.1 Purpose

_What this software specification covers and who its audience is._

### 1.2 Scope

_Software scope derived from the G0-validated StRS + SyRS; what is explicitly out of scope._

### 1.3 Definitions, Acronyms, and Abbreviations

| Term       | Definition                                              |
|------------|---------------------------------------------------------|
| SRS        | Software Requirements Specification (this document)     |
| StRS       | Stakeholder Requirements Specification — upstream (G0)  |
| SyRS       | System Requirements Specification — upstream (G0)       |
| _TERM_     | _Precise definition_                                    |

### 1.4 References

| Ref ID     | Document                                                | Version / Date  |
|------------|---------------------------------------------------------|-----------------|
| `REF-001`  | _Title_                                                 | _vX.Y / date_   |

### 1.5 Document Overview

_Brief description of the structure of the remaining sections._

---

## 2. Software Design Specification

### 2.1 Software Architecture Overview

_Textual or diagrammatic overview of the modules, their responsibilities, and data flow._

### 2.2 Library and Framework Selections

_Every external library/framework the implementation selects, with justification._

| Library / Framework | Version | Purpose | Selection Rationale | Alternatives Considered |
|---------------------|---------|---------|---------------------|-------------------------|
| _name_              | _vX.Y_  | _what it does_ | _why this one_ | _alternatives rejected_ |

### 2.3 Implementation Constraints

_Software-side constraints (language runtime, memory budget, platform APIs) that do not come from a single requirement._

---

## 3. Software Requirements

### Block ID Convention

```
REQ-[SUB]-[NNN]
```

| Segment | Rule                                    | Example             |
|---------|-----------------------------------------|---------------------|
| `SUB`   | 2–4 uppercase letters — module group    | `DSP`, `STO`, `NET` |
| `NNN`   | 3-digit zero-padded sequence            | `001`, `042`        |

> **Regex:** `^REQ-[A-Z]{2,4}-\d{3}$`  
> Every block MUST carry a `Traces to` field naming the SyRS `SYS-` block(s) it
> derives from. No REQ- block may exist without an upstream justification.

### Fields per Block

| Field                  | Required | Type              | Description                                                     |
|------------------------|----------|-------------------|-----------------------------------------------------------------|
| `id`                   | yes      | string            | Unique ID per the convention above                              |
| `title`                | yes      | string (≤120 ch)  | Descriptive name                                                |
| `type`                 | yes      | enum              | `FUNCTIONAL` \| `NON_FUNCTIONAL` \| `INTERFACE` \| `CONSTRAINT` |
| `priority`             | yes      | enum              | `MUST` \| `SHOULD` \| `COULD` \| `WONT`                         |
| `status`               | yes      | enum              | `PROPOSED` \| `APPROVED` \| `IMPLEMENTED` \| `VERIFIED` \| `REJECTED` |
| `verification`         | yes      | enum              | `INSPECTION` \| `DEMONSTRATION` \| `TEST` \| `ANALYSIS`         |
| `traces_to`            | yes      | string[]          | SyRS `SYS-` block ID(s) this requirement derives from           |
| `library`              | no       | string            | Library/framework used to satisfy it (must be listed in §2.2)   |
| `dependencies`         | no       | string[]          | IDs of REQ- blocks this one depends on                          |
| `notes`                | no       | string            | Technical remarks                                               |

### Block Format

---

**`REQ-[SUB]-[NNN]` — _Requirement title_**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL` \| `NON_FUNCTIONAL` \| `INTERFACE` \| `CONSTRAINT` |
| **Priority**           | `MUST` \| `SHOULD` \| `COULD`                            |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `INSPECTION` \| `DEMONSTRATION` \| `TEST` \| `ANALYSIS`   |
| **Traces to**          | `SYS-…`                                                   |
| **Library**            | _library name, or_ —                                      |
| **Dependencies**       | _REQ- IDs, or_ —                                          |

**Description:**  
The software SHALL _[testable, quantified software behavior]_.

**Acceptance Criteria:**

1. [ ] _Verifiable condition 1_
2. [ ] _Verifiable condition 2_

**Test Specification:**  
_Tests that demonstrate the acceptance criteria (see §7)._

**Notes:**  
_Technical remarks. Omit this field if there is nothing to add._

---

_[Repeat the block for each software requirement]_

---

### 3.1 [_Module Group 1: Name_]

_Place REQ- blocks here, grouped by module or subsystem._

---

## 4. Algorithms and Data Schemas

### 4.1 Algorithms

_Software algorithms: inputs, outputs, complexity, numerical considerations._

| Algorithm | Used By (Blocks) | Inputs | Outputs | Notes |
|-----------|------------------|--------|---------|-------|
| _name_    | `REQ-…`          | _in_   | _out_   | _…_   |

### 4.2 Data Schemas

_Persisted and transmitted data structures: serialization format, field types, units._

| Schema | Used By (Blocks) | Format | Fields | Versioning |
|--------|------------------|--------|--------|------------|
| _name_ | `REQ-…`          | _e.g. JSON / binary_ | _fields_ | _strategy_ |

---

## 5. Interfaces

### 5.1 External Interfaces
### 5.2 Internal Interfaces
### 5.3 Data Interfaces

---

## 6. Error Behavior

_Propagated errors, retry/timeout policy, degraded modes, and user-visible failure modes._

| Failure Mode | Trigger | Detected By (Blocks) | Behavior |
|--------------|---------|----------------------|----------|
| _mode_       | _cause_ | `REQ-…`              | _response_ |

---

## 7. Test Specifications

_Every REQ- block must be covered by at least one test case._

| Test Case | Requirement | Type (`UNIT` \| `INTEGRATION` \| `SIL` \| `SYSTEM`) | Stimulus | Expected Result |
|-----------|-------------|-----------------------------------------------------|----------|-----------------|
| `TC-NNN`  | `REQ-…`     | _type_                                              | _input_  | _expected_      |

---

## 8. Traceability

| Requirement ID | SyRS Traces | StRS Root(s)  | Test Case   | Component |
|----------------|-------------|---------------|-------------|-----------|
| `REQ-[SUB]-[NNN]` | `SYS-…`  | `STK-…`       | _TC-NNN_    | _module_  |

---

## G1 Validation Rules (structural)

The G1 gate validates this document (no-tools G1 skill; tool-backed script is future work):

1. **Metadata** — Document ID, Project, Organization, Version (SemVer), Classification present and not placeholders (same rules as G0).
2. **Required sections** — every heading listed in this template exists.
3. **ID format** — every block ID matches `^REQ-[A-Z]{2,4}-\d{3}$` and is unique.
4. **Traceability upstream** — every `Traces to` value is a `SYS-` block ID that exists in the G0-validated SyRS; every REQ- block traces to at least one.
5. **Testable SHALL** — every block has a `**Description:**` using SHALL/SHOULD, at least one acceptance criterion, and a test case in §7.
6. **Justified selections** — every library/framework row in §2.2 has a non-empty Selection Rationale.
7. **Internal consistency** — Dependencies resolve to existing REQ- blocks and form an acyclic graph; the §8 traceability table lists every REQ- block.

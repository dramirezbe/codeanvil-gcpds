# [PROJECT: _project_name_]

## System Requirements Specification (SRS)

> **Standard:** IEEE/ISO/IEC 29148:2018 — *Systems and software engineering — Life cycle processes — Requirements engineering.*
>
> **Template version:** 3.0.0  
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

| Document ID            | Title                                    | Relationship             |
|------------------------|------------------------------------------|--------------------------|
| `HCS-_ACRONYM_-_NNN_` | _Hardware Constraints Specification_     | Design constraints envelope |
| `SRS-_ACRONYM_-_NNN_` | _Parent system SRS (if subsystem)_       | Parent requirements       |

> **Note:** The companion HCS (IEEE 29148 §2.4) documents the parametric limits of the hardware platform. This SRS was written with those limits already incorporated — every requirement is feasible within the hardware envelope.

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
| HCS        | Hardware Constraints Specification — companion document |
| _TERM_     | _Precise definition_                                    |

### 1.4 References

| Ref ID     | Document                                                | Version / Date  |
|------------|---------------------------------------------------------|-----------------|
| `REF-001`  | _Title_                                                 | _vX.Y / date_   |

### 1.5 Document Overview

_Brief description of the structure of the remaining sections._

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

_Narrative summary of design constraints. Detailed hardware limits are in the companion HCS._

### 2.5 Assumptions and Dependencies

_Conditions assumed true for the requirements to hold._

---

## 3. Specific Requirements

### Requirement ID Convention

Each requirement uses the pattern:

```
[CAT]-[SUB]-[NNN]
```

| Segment | Rule                                   | Example                |
|---------|----------------------------------------|------------------------|
| `CAT`   | 3–5 uppercase letters — category       | `ANAL`, `CONN`, `SEG`  |
| `SUB`   | 2–4 uppercase letters — subcategory    | `PAR`, `MED`, `VIS`    |
| `NNN`   | 3-digit zero-padded sequence           | `001`, `042`           |

> **Regex:** `^[A-Z]{3,5}-[A-Z]{2,4}-\d{3}$`

### Fields per Requirement

| Field                  | Required | Type              | Description                                                     |
|------------------------|----------|-------------------|-----------------------------------------------------------------|
| `id`                   | yes      | string            | Unique ID per the convention above                              |
| `title`                | yes      | string (≤120 ch)  | Descriptive name                                                |
| `description`          | yes      | string            | "The system SHALL…" or "The system SHOULD…"                     |
| `type`                 | yes      | enum              | See **Type values** below                                       |
| `priority`             | yes      | enum              | See **Priority values** below                                   |
| `acceptance_criteria`  | yes      | string[]          | Verifiable conditions (≥ 1)                                     |
| `verification`         | yes      | enum              | See **Verification values** below                               |
| `dependencies`         | no       | string[]          | IDs of requirements this one depends on                         |
| `standard_ref`         | no       | string[]          | Applicable normative references                                 |
| `notes`                | no       | string            | Technical or implementation remarks                             |
| `status`               | yes      | enum              | See **Status values** below                                     |
| `phase`                | no       | string            | Implementation phase (e.g. `2026`, `PHASE_2`)                   |

### Enumeration Values

**Type** — classifies what the requirement specifies:

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

**Status** — lifecycle state:

| Value         | Meaning                                    |
|---------------|--------------------------------------------|
| `PROPOSED`    | Drafted, not yet reviewed                  |
| `APPROVED`    | Reviewed and accepted                      |
| `IMPLEMENTED` | Code or design complete                    |
| `VERIFIED`    | Passed its verification method             |
| `REJECTED`    | Reviewed and discarded                     |

---

### Requirement Block Format

Each requirement is a self-contained block:

---

**`[CAT]-[SUB]-[NNN]` — _Requirement title_**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL` \| `NON_FUNCTIONAL` \| `INTERFACE` \| `CONSTRAINT` |
| **Priority**           | `MUST` \| `SHOULD` \| `COULD`                            |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `INSPECTION` \| `DEMONSTRATION` \| `TEST` \| `ANALYSIS`   |
| **Standard(s)**        | _Normative references, or_ —                              |
| **Dependencies**       | _Requirement IDs, or_ —                                   |
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

### 3.1 [_CATEGORY 1: Name_]

#### 3.1.1 [_Subcategory 1.1_]

_Place requirement blocks here._

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

| Requirement ID       | Business Objective | Standard Ref   | Test Case   | Component     |
|----------------------|--------------------|----------------|-------------|---------------|
| `[CAT]-[SUB]-[NNN]` | _OBJ-NNN_         | _standard_     | _TC-NNN_    | _component_   |

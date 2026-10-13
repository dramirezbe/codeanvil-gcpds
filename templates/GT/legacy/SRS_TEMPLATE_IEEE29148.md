# [PROJECT: _project_name_]

## System Requirements Specification (SRS)

> **Template based on:** IEEE/ISO/IEC 29148:2018 — *Systems and software engineering — Life cycle processes — Requirements engineering*, adapted with elements of ETSI EN 303 645 (Cyber Security for IoT) and a deterministic structure for automated AI-based validation.
>
> **Template version:** 1.0.0  
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

### Change Log

| Version | Date       | Author       | Change Description               |
|---------|------------|--------------|----------------------------------|
| 0.1.0   | YYYY-MM-DD | _name_       | Initial creation                 |

---

## 1. Introduction

### 1.1 Purpose

_Description of the purpose of the document and of the system. State the target audience._

### 1.2 System Scope

_Name of the system, what it does and what it does NOT do. Benefits, objectives, and goals._

### 1.3 Definitions, Acronyms, and Abbreviations

| Term       | Definition                                              |
|------------|---------------------------------------------------------|
| _TERM_     | _Precise definition_                                    |

### 1.4 References

| Ref ID     | Document                                                | Version / Date  |
|------------|---------------------------------------------------------|-----------------|
| `REF-001`  | _Title of the referenced document_                      | _vX.Y / date_   |

### 1.5 Document Overview

_Description of the structure of the following sections._

---

## 2. Overall System Description

### 2.1 Product Perspective

_System context: whether it is new, a replacement, or an extension. Relationship to other systems._

#### 2.1.1 Context Diagram

_Reference to a diagram or a textual description of the external interfaces._

### 2.2 Product Functions

_High-level summary of the main functions (without requirement-level detail)._

### 2.3 User Characteristics

| User Type       | Description                        | Technical Level     |
|-----------------|------------------------------------|---------------------|
| _role_          | _what they do with the system_     | `BASIC` \| `TECHNICAL` \| `EXPERT` |

### 2.4 Constraints

_Regulatory, hardware, interface, security, and other constraints._

### 2.5 Assumptions and Dependencies

_Conditions assumed to be true for the requirements to hold._

---

## 3. Specific Requirements

> **ID convention:**  
> Each requirement uses the format `[CAT]-[SUB]-[NNN]`, where:
> - `CAT` = Category (3–5 uppercase letters). E.g., `ARQ`, `ANAL`, `CONN`, `SEG`
> - `SUB` = Subcategory (2–4 letters). E.g., `PAR`, `MED`, `VIS`
> - `NNN` = 3-digit sequential number, starting at 001
>
> **Mandatory fields per requirement** (marked with `*`):
>
> | Field                | Type                  | Description                                                   |
> |----------------------|-----------------------|---------------------------------------------------------------|
> | `id`*                | string                | Unique identifier. Format: `[CAT]-[SUB]-[NNN]`              |
> | `title`*             | string (≤120 chars)   | Descriptive name of the requirement                           |
> | `description`*       | string                | Full statement using "The system SHALL…" / "The system SHOULD…" |
> | `type`*              | enum                  | `FUNCTIONAL` \| `NON_FUNCTIONAL` \| `INTERFACE` \| `CONSTRAINT` |
> | `priority`*          | enum                  | `MUST` \| `SHOULD` \| `COULD` \| `WONT` (MoSCoW)             |
> | `category`*          | string                | Functional category of the system                             |
> | `subcategory`        | string                | Grouping within the category                                  |
> | `acceptance_criteria`* | string[]            | List of verifiable conditions (minimum 1)                     |
> | `verification`*      | enum                  | `INSPECTION` \| `DEMONSTRATION` \| `TEST` \| `ANALYSIS`       |
> | `dependencies`       | string[]              | IDs of the requirements it depends on                         |
> | `standard_ref`       | string[]              | Applicable normative references                               |
> | `new_hardware`       | boolean               | `true` if it requires additional hardware                     |
> | `notes`              | string                | Internal or technical remarks                                 |
> | `status`*            | enum                  | `PROPOSED` \| `APPROVED` \| `IMPLEMENTED` \| `VERIFIED` \| `REJECTED` |
> | `phase`              | string                | Implementation phase. E.g., `2025`, `2026`, `PHASE_2`         |

---

### 3.1 [_CATEGORY 1: Name_]

#### 3.1.1 [_Subcategory 1.1_]

---

**`[CAT]-[SUB]-[NNN]` — _Requirement title_**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Type**               | `FUNCTIONAL` \| `NON_FUNCTIONAL` \| `INTERFACE` \| `CONSTRAINT` |
| **Priority**           | `MUST` \| `SHOULD` \| `COULD`                            |
| **Status**             | `APPROVED`                                                |
| **Verification**       | `INSPECTION` \| `DEMONSTRATION` \| `TEST` \| `ANALYSIS`   |
| **New hardware**       | `Yes` / `No`                                              |
| **Standard(s)**        | _Normative references_                                    |
| **Dependencies**       | _IDs of prior requirements_                               |
| **Phase**              | _Implementation phase_                                    |

**Description:**  
The system SHALL _[verifiable action, with quantitative parameters where applicable]_.

**Acceptance Criteria:**

1. [ ] _Verifiable condition 1_
2. [ ] _Verifiable condition 2_

**Notes:**  
_Technical or implementation remarks._

---

_[Repeat the block for each requirement]_

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

_Traceability matrix of requirements against business objectives, test cases, or system components._

| Requirement ID  | Business Objective  | Test Case      | Component     |
|-----------------|---------------------|----------------|---------------|
| `[CAT]-[SUB]-[NNN]` | _OBJ-NNN_       | _TC-NNN_       | _component_   |


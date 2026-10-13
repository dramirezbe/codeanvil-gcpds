# [PROJECT: _project_name_]

## System Requirements Specification (SRS)

> **Template based on:** IEEE/ISO/IEC 29148:2018 — *Systems and software engineering — Life cycle processes — Requirements engineering*, adapted with elements of ETSI EN 303 645 (Cyber Security for IoT) and a deterministic structure for automated AI-based validation.
>
> **Methodology:** COTS-Reconciled Requirements Engineering. This SRS assumes that hardware has been selected and its constraints formally documented in a companion Hardware Constraints Specification (HCS). Requirements in this document have been reconciled against the HCS — every requirement is feasible within the COTS envelope, and conflicts have been resolved prior to approval.
>
> **Template version:** 2.0.0  
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
| `HCS-_ACRONYM_-_NNN_` | _Hardware Constraints Specification_     | COTS envelope for this SRS |
| `SRS-_ACRONYM_-_NNN_` | _Parent system SRS (if subsystem)_       | Parent requirements       |

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

### 1.3 COTS-Reconciled Methodology

_This SRS follows a COTS-Reconciled methodology:_

1. _Requirements originate from two streams: **Client needs** and **Normative standards**._
2. _Hardware is selected (COTS) and its parametric constraints are formally documented in the companion **HCS** document._
3. _Each requirement is reconciled against the HCS before approval — conflicts are resolved, mitigations documented, and infeasible requirements rejected or modified._
4. _The reconciliation status is recorded per requirement via the `hw_constraints` field._

```
[ Client ]       [ Norms (ITU, ETSI, IEEE) ]
      │                    │
      └────────┬───────────┘
               │  (Domain Requirements)
               ▼
    ┌────────────────────┐
    │   Reconciliation   │ ◄─── [ HCS: COTS Constraints ]
    │   (conflict check) │      (Datasheets, Drivers, Physical limits)
    └─────────┬──────────┘
              │
              ▼
    [ SRS — Reconciled & Approved ]
```

### 1.4 Definitions, Acronyms, and Abbreviations

| Term       | Definition                                              |
|------------|---------------------------------------------------------|
| HCS        | Hardware Constraints Specification — companion document cataloging COTS parametric limits |
| COTS       | Commercial Off-The-Shelf — pre-existing hardware not designed from scratch |
| _TERM_     | _Precise definition_                                    |

### 1.5 References

| Ref ID     | Document                                                | Version / Date  |
|------------|---------------------------------------------------------|-----------------|
| `REF-001`  | _Title of the referenced document_                      | _vX.Y / date_   |
| `REF-HCS`  | _HCS-ACRONYM-NNN — Companion HW Constraints Spec_      | _vX.Y / date_   |

### 1.6 Document Overview

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

_Summary of constraints. Detailed parametric constraints are in the companion HCS document (REF-HCS). This section provides a narrative overview only._

### 2.5 Assumptions and Dependencies

_Conditions assumed to be true for the requirements to hold. Include the assumption that the COTS hardware documented in the HCS is the selected platform._

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
> | `hw_constraints`     | string[]              | IDs from the companion HCS that bound this requirement        |
> | `reconciliation`*    | enum                  | `UNCONSTRAINED` \| `BOUNDED` \| `AT_LIMIT` \| `MITIGATED`    |
> | `standard_ref`       | string[]              | Applicable normative references                               |
> | `new_hardware`       | boolean               | `true` if it requires additional hardware beyond the COTS baseline |
> | `notes`              | string                | Internal or technical remarks                                 |
> | `status`*            | enum                  | `PROPOSED` \| `APPROVED` \| `IMPLEMENTED` \| `VERIFIED` \| `REJECTED` |
> | `phase`              | string                | Implementation phase. E.g., `2025`, `2026`, `PHASE_2`         |
>
> **Reconciliation status values:**
>
> | Value           | Meaning                                                                |
> |-----------------|------------------------------------------------------------------------|
> | `UNCONSTRAINED` | No COTS constraint applies — the requirement is freely achievable      |
> | `BOUNDED`       | A COTS constraint limits but does not prevent fulfillment              |
> | `AT_LIMIT`      | The requirement operates at the exact boundary of a COTS constraint    |
> | `MITIGATED`     | A COTS conflict exists but is resolved via software compensation, additional hardware, or a design workaround (describe in notes) |

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
| **HW constraints**     | _IDs from HCS that bound this requirement_                |
| **Reconciliation**     | `UNCONSTRAINED` \| `BOUNDED` \| `AT_LIMIT` \| `MITIGATED` |
| **Phase**              | _Implementation phase_                                    |

**Description:**  
The system SHALL _[verifiable action, with quantitative parameters where applicable]_.

**Acceptance Criteria:**

1. [ ] _Verifiable condition 1_
2. [ ] _Verifiable condition 2_

**Notes:**  
_Technical or implementation remarks. If reconciliation is `MITIGATED`, describe the mitigation strategy here._

---

_[Repeat the block for each requirement]_

---

## 4. External Interface Requirements

### 4.1 User Interfaces
### 4.2 Hardware Interfaces

_Summary of hardware interfaces. Detailed specifications (bus speeds, pin assignments, voltage levels) are in the companion HCS._

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

_Traceability matrix linking requirements to business objectives, normative standards, HCS constraints, and test cases._

| Requirement ID       | Business Objective | Standard Ref   | HCS Constraint(s) | Reconciliation | Test Case   | Component     |
|----------------------|--------------------|----------------|--------------------|----------------|-------------|---------------|
| `[CAT]-[SUB]-[NNN]` | _OBJ-NNN_         | _standard_     | _HWC-XXX-NNN_     | _status_       | _TC-NNN_    | _component_   |

---

## 7. G0 Structural Validation (Future Work)

> **Status:** `PLANNED` — This section defines the objective for automated AI-based structural validation of the SRS and HCS document pair. Implementation is deferred to a future phase.

### 7.1 Objective

G0 is an AI agent whose purpose is to structurally validate the consistency and completeness of the SRS–HCS document pair. G0 does NOT generate requirements; it reviews them.

### 7.2 G0 Input Contract

| Input                | Source Document | Format                                    |
|----------------------|-----------------|-------------------------------------------|
| Requirements         | SRS             | Requirement blocks per Section 3 schema   |
| COTS Constraints     | HCS             | Constraint blocks per HCS Section 3 schema |
| Reconciliation status| SRS             | `reconciliation` field per requirement    |

### 7.3 G0 Validation Rules (Planned)

1. **Structural completeness:** Every mandatory field is present and uses a valid enum value.
2. **ID uniqueness:** No duplicate requirement or constraint IDs across the document pair.
3. **Cross-reference integrity:** Every `hw_constraints` ID in the SRS exists in the HCS, and vice versa.
4. **Reconciliation consistency:** If `hw_constraints` is non-empty, `reconciliation` cannot be `UNCONSTRAINED`.
5. **Conflict detection:** If a requirement's quantitative parameter exceeds or matches a constraint's limit, `reconciliation` must be `AT_LIMIT` or `MITIGATED`, not `BOUNDED`.
6. **Mitigation documentation:** If `reconciliation` is `MITIGATED`, the `notes` field must contain a mitigation description.
7. **Dependency graph:** No circular dependencies. All referenced IDs exist.
8. **Traceability coverage:** Every requirement in Section 3 appears in the Section 6 traceability matrix.

### 7.4 G0 Output

A **Conflict Analysis Matrix** documenting:

| Conflict ID | Requirement | Constraint | Severity                          | Resolution           |
|-------------|------------|------------|-----------------------------------|----------------------|
| `CON-NNN`   | _REQ-ID_   | _HWC-ID_  | `OK` \| `WARNING` \| `CONFLICT`  | _Description_        |

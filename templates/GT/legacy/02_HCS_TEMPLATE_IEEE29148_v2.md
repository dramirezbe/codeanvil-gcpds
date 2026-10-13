# [PROJECT: _project_name_]

## Hardware Constraints Specification (HCS)

> **Template based on:** IEEE/ISO/IEC 29148:2018 §2.4 (Realization / Design Constraints), formalized as a standalone companion document to the SRS. Provides machine-readable parametric limits for COTS hardware that define the design envelope within which software requirements must be fulfilled.
>
> **Methodology:** This document is the COTS constraint input to the COTS-Reconciled Requirements Engineering methodology. It captures every hardware limitation that bounds, limits, or shapes a software requirement. The companion SRS references constraints from this document by ID.
>
> **Template version:** 2.0.0  
> **Creation date:** _YYYY-MM-DD_  
> **Last modified:** _YYYY-MM-DD_  
> **Document status:** `DRAFT` | `IN_REVIEW` | `APPROVED` | `OBSOLETE`

---

## Document Metadata

| Field                  | Value                                    |
|------------------------|------------------------------------------|
| **Document ID**        | `HCS-_ACRONYM_-_NNN_`                    |
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
| `SRS-_ACRONYM_-_NNN_` | _System Requirements Specification_      | Requirements bounded by this HCS |

### Change Log

| Version | Date       | Author       | Change Description               |
|---------|------------|--------------|----------------------------------|
| 0.1.0   | YYYY-MM-DD | _name_       | Initial creation                 |

---

## 1. Introduction

### 1.1 Purpose

_This document catalogs the parametric constraints imposed by the selected COTS hardware on the system's software requirements. It serves as the formal "envelope" within which the companion SRS must operate. Every constraint is traceable to a datasheet, driver specification, or measured characterization._

### 1.2 Scope

_Name the hardware platform and the subsystem it constrains. State what is included (physical limits, bus throughput, driver APIs, power budgets) and what is excluded (software architecture, algorithm choices, user experience)._

### 1.3 Definitions, Acronyms, and Abbreviations

| Term       | Definition                                              |
|------------|---------------------------------------------------------|
| COTS       | Commercial Off-The-Shelf                                |
| HCS        | Hardware Constraints Specification (this document)      |
| _TERM_     | _Precise definition_                                    |

### 1.4 References

| Ref ID      | Document                                               | Version / Date  |
|-------------|--------------------------------------------------------|-----------------|
| `REF-DS-001`| _Datasheet: component name_                            | _revision_      |
| `REF-DRV-001`| _Driver/API documentation: name_                      | _version_       |
| `REF-MEAS-001`| _Measured characterization report: description_       | _date_          |

### 1.5 Hardware Inventory

_List all COTS components whose constraints are documented here._

| Component ID | Component Name      | Role in System                | Manufacturer    | Part Number     |
|-------------|---------------------|-------------------------------|-----------------|-----------------|
| `HW-001`    | _component name_    | _what it does in the system_  | _manufacturer_  | _part number_   |

---

## 2. System Hardware Architecture

### 2.1 Block Diagram

_Reference to or textual description of the hardware interconnection._

### 2.2 Bus and Interface Topology

_Describe how components are connected: bus types, data rates, protocols._

---

## 3. Hardware Constraints

> **ID convention:**  
> Each constraint uses the format `HWC-[COMP]-[NNN]`, where:
> - `COMP` = Component abbreviation (2–4 uppercase letters). E.g., `SDR`, `CPU`, `BUS`, `GPS`, `PWR`, `STR`, `ANT`
> - `NNN` = 3-digit sequential number, starting at 001
>
> **Mandatory fields per constraint** (marked with `*`):
>
> | Field              | Type                  | Description                                                   |
> |--------------------|-----------------------|---------------------------------------------------------------|
> | `id`*              | string                | Unique identifier. Format: `HWC-[COMP]-[NNN]`               |
> | `title`*           | string (≤120 chars)   | Descriptive name of the constraint                            |
> | `component`*       | string                | Component ID from the Hardware Inventory (Section 1.5)        |
> | `parameter`*       | string                | The physical/technical parameter being constrained            |
> | `limit_type`*      | enum                  | `MAX` \| `MIN` \| `RANGE` \| `FIXED` \| `ENUM`              |
> | `value`*           | string                | The limit value with units. E.g., `6 GHz`, `20 MHz`, `8 bit` |
> | `value_min`        | string                | Lower bound (for `RANGE` type)                                |
> | `value_max`        | string                | Upper bound (for `RANGE` type)                                |
> | `source`*          | enum                  | `DATASHEET` \| `DRIVER_API` \| `MEASURED` \| `DERIVED`       |
> | `source_ref`*      | string                | Reference ID from Section 1.4 + page/section                  |
> | `impact`*          | enum                  | `HARD` \| `SOFT` \| `INFORMATIONAL`                          |
> | `srs_refs`         | string[]              | IDs of SRS requirements bounded by this constraint            |
> | `notes`            | string                | Technical remarks, measurement conditions, known workarounds  |
> | `status`*          | enum                  | `CONFIRMED` \| `PRELIMINARY` \| `DEPRECATED`                 |
>
> **Limit type values:**
>
> | Value    | Meaning                                              | Fields used          |
> |----------|------------------------------------------------------|----------------------|
> | `MAX`    | Upper bound — must not exceed                        | `value`              |
> | `MIN`    | Lower bound — must meet or exceed                    | `value`              |
> | `RANGE`  | Acceptable range                                     | `value_min`, `value_max` |
> | `FIXED`  | Exact value imposed by hardware, not configurable    | `value`              |
> | `ENUM`   | One of a fixed set of values                         | `value` (comma-separated) |
>
> **Impact values:**
>
> | Value           | Meaning                                                          |
> |-----------------|------------------------------------------------------------------|
> | `HARD`          | Physical/electrical limit — cannot be exceeded by any means      |
> | `SOFT`          | Practical limit — can be partially overcome with software mitigation |
> | `INFORMATIONAL` | Characteristic that shapes design decisions but does not block    |

---

### 3.1 [_Component Group 1: Name_]

---

**`HWC-[COMP]-[NNN]` — _Constraint title_**

| Field                  | Value                                                     |
|------------------------|-----------------------------------------------------------|
| **Component**          | _Component ID from inventory_                             |
| **Parameter**          | _Physical/technical parameter_                            |
| **Limit type**         | `MAX` \| `MIN` \| `RANGE` \| `FIXED` \| `ENUM`          |
| **Value**              | _Limit with units_                                        |
| **Source**             | `DATASHEET` \| `DRIVER_API` \| `MEASURED` \| `DERIVED`   |
| **Source ref**         | _REF-XX-NNN §section / page_                             |
| **Impact**             | `HARD` \| `SOFT` \| `INFORMATIONAL`                      |
| **SRS refs**           | _Requirement IDs bounded by this constraint_              |
| **Status**             | `CONFIRMED` \| `PRELIMINARY`                              |

**Notes:**  
_Technical remarks, measurement conditions, known workarounds._

---

_[Repeat the block for each constraint]_

---

## 4. Derived Constraints

_Constraints that are not in any single datasheet but emerge from the combination of multiple COTS components or from system-level analysis (e.g., USB throughput bottleneck, processing budget, power budget)._

_Use the same block format as Section 3, with `source` = `DERIVED` and a description of the derivation in notes._

---

## 5. Constraint-to-Requirement Cross-Reference

| HCS Constraint ID    | SRS Requirement ID(s)       | Reconciliation Status            |
|----------------------|-----------------------------|----------------------------------|
| `HWC-[COMP]-[NNN]`  | _REQ-ID-1, REQ-ID-2_       | `BOUNDED` \| `AT_LIMIT` \| `MITIGATED` |

---

## 6. G0 Structural Validation (Future Work)

> **Status:** `PLANNED` — G0 will validate this document's structural integrity and its cross-references with the companion SRS.

### 6.1 HCS-Specific Validation Rules (Planned)

1. **Structural completeness:** Every mandatory field is present and uses a valid enum value.
2. **ID uniqueness:** No duplicate constraint IDs.
3. **Source traceability:** Every `source_ref` points to a valid entry in Section 1.4.
4. **Component existence:** Every `component` value exists in the Hardware Inventory (Section 1.5).
5. **Cross-reference integrity:** Every `srs_refs` ID exists in the companion SRS.
6. **RANGE consistency:** If `limit_type` is `RANGE`, both `value_min` and `value_max` must be present and `value_min` < `value_max`.
7. **Bidirectional traceability:** Every constraint with `impact` = `HARD` must have at least one SRS reference (it bounds something).

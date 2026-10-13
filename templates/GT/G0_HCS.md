# [PROJECT: _project_name_]

## Hardware Constraints Specification (HCS)

> **Standard:** IEEE/ISO/IEC 29148:2018 §2.4 — *Realization / Design Constraints*, formalized as a standalone companion to the SRS. Documents the parametric limits of the selected hardware platform.
>
> **Template version:** 3.0.0  
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

| Document ID            | Title                                    | Relationship                      |
|------------------------|------------------------------------------|-----------------------------------|
| `SRS-_ACRONYM_-_NNN_` | _System Requirements Specification_      | Requirements this HCS constrains  |

### Change Log

| Version | Date       | Author       | Change Description               |
|---------|------------|--------------|----------------------------------|
| 0.1.0   | YYYY-MM-DD | _name_       | Initial creation                 |

---

## 1. Introduction

### 1.1 Purpose

_This document catalogs the parametric constraints imposed by the hardware platform. It defines the design envelope within which the companion SRS must operate. Every constraint is traceable to a datasheet, driver specification, or measured characterization._

### 1.2 Scope

_Name the hardware platform. State what is included (physical limits, bus throughput, driver APIs, power budgets) and what is excluded (software architecture, algorithms, user experience)._

### 1.3 Definitions, Acronyms, and Abbreviations

| Term       | Definition                                              |
|------------|---------------------------------------------------------|
| HCS        | Hardware Constraints Specification (this document)      |
| _TERM_     | _Precise definition_                                    |

### 1.4 References

| Ref ID        | Document                                               | Version / Date  |
|---------------|--------------------------------------------------------|-----------------|
| `REF-DS-001`  | _Datasheet: component name_                            | _revision_      |
| `REF-DRV-001` | _Driver/API documentation: name_                       | _version_       |
| `REF-MEAS-001`| _Measured characterization report: description_        | _date_          |

### 1.5 Hardware Inventory

_All hardware components whose constraints are documented here._

| Component ID | Component Name      | Role in System                | Manufacturer    | Part Number     |
|-------------|---------------------|-------------------------------|-----------------|-----------------|
| `HW-001`    | _component name_    | _what it does in the system_  | _manufacturer_  | _part number_   |

---

## 2. System Hardware Architecture

### 2.1 Block Diagram

_Textual or graphical representation of how the hardware components are interconnected._

### 2.2 Bus and Interface Topology

| From       | To         | Bus/Protocol | Data Rate (theoretical) | Data Rate (sustained) |
|------------|------------|-------------|-------------------------|----------------------|
| _HW-001_   | _HW-002_   | _protocol_  | _theoretical_           | _measured_           |

---

## 3. Hardware Constraints

### Constraint ID Convention

Each constraint uses the pattern:

```
HWC-[COMP]-[NNN]
```

| Segment | Rule                                    | Example              |
|---------|-----------------------------------------|----------------------|
| `COMP`  | 2–4 uppercase letters — component group | `SDR`, `CPU`, `BUS`  |
| `NNN`   | 3-digit zero-padded sequence            | `001`, `042`         |

> **Regex:** `^HWC-[A-Z]{2,4}-\d{3}$`

### Fields per Constraint

| Field              | Required | Type              | Description                                                     |
|--------------------|----------|-------------------|-----------------------------------------------------------------|
| `id`               | yes      | string            | Unique ID per the convention above                              |
| `title`            | yes      | string (≤120 ch)  | Descriptive name of the constraint                              |
| `component`        | yes      | string            | Component ID from the Hardware Inventory (§1.5)                 |
| `parameter`        | yes      | string            | The physical/technical parameter being constrained              |
| `limit_type`       | yes      | enum              | See **Limit type values** below                                 |
| `value`            | yes*     | string            | The limit with units (e.g. `6 GHz`, `8 bit`)                   |
| `value_min`        | cond.    | string            | Lower bound — required when `limit_type` = `RANGE`             |
| `value_max`        | cond.    | string            | Upper bound — required when `limit_type` = `RANGE`             |
| `source`           | yes      | enum              | See **Source values** below                                     |
| `source_ref`       | yes      | string            | Reference ID from §1.4 + page/section                          |
| `impact`           | yes      | enum              | See **Impact values** below                                     |
| `notes`            | no       | string            | Technical remarks, measurement conditions, workarounds          |
| `status`           | yes      | enum              | See **Status values** below                                     |

> *`value` is required for all `limit_type` except `RANGE`, which uses `value_min` + `value_max` instead.

### Enumeration Values

**Limit type** — how the parameter is bounded:

| Value    | Meaning                                       | Uses field(s)          |
|----------|-----------------------------------------------|------------------------|
| `MAX`    | Upper bound — must not exceed                 | `value`                |
| `MIN`    | Lower bound — must meet or exceed             | `value`                |
| `RANGE`  | Acceptable range (both bounds)                | `value_min`, `value_max` |
| `FIXED`  | Exact value imposed by hardware, not tunable  | `value`                |
| `ENUM`   | One of a fixed set of discrete values         | `value` (comma-separated list) |

**Source** — where the constraint value comes from:

| Value        | Meaning                                                              |
|--------------|----------------------------------------------------------------------|
| `DATASHEET`  | Published manufacturer datasheet                                     |
| `DRIVER_API` | Driver or firmware API documentation                                 |
| `MEASURED`   | Laboratory or field measurement (cite report in `source_ref`)        |
| `DERIVED`    | Calculated from other constraints or system-level analysis           |

**Impact** — how hard the limit is:

| Value           | Meaning                                                          |
|-----------------|------------------------------------------------------------------|
| `HARD`          | Physical/electrical limit — cannot be exceeded by any means      |
| `SOFT`          | Practical limit — can be partially overcome with software or design mitigation |
| `INFORMATIONAL` | Characteristic that shapes design decisions but does not block   |

**Status** — confidence in the value:

| Value         | Meaning                                                        |
|---------------|----------------------------------------------------------------|
| `CONFIRMED`   | Verified against datasheet or measurement                      |
| `PRELIMINARY` | Estimated or extrapolated — requires confirmation              |
| `DEPRECATED`  | No longer applicable (hardware changed or constraint removed)  |

---

### Constraint Block Format

Each constraint is a self-contained block:

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
| **Status**             | `CONFIRMED` \| `PRELIMINARY`                              |

**Notes:**  
_Technical remarks. Omit this field if there is nothing to add._

---

_[Repeat the block for each constraint]_

---

### 3.1 [_Component Group 1: Name_]

_Place constraint blocks here, grouped by component or subsystem._

---

## 4. Derived Constraints

_Constraints that emerge from the combination of multiple components or from system-level analysis (e.g. a throughput bottleneck, a power budget). Use the same block format as §3, with `source` = `DERIVED`._

---

## 5. Structural Validation Checklist

> This checklist defines the rules for automated or manual structural review of this HCS document.

1. **Structural completeness:** Every required field is present and uses a valid enum value.
2. **ID uniqueness:** No duplicate constraint IDs.
3. **Source traceability:** Every `source_ref` points to a valid entry in §1.4.
4. **Component existence:** Every `component` value exists in the Hardware Inventory (§1.5).
5. **RANGE consistency:** If `limit_type` = `RANGE`, both `value_min` and `value_max` are present and min < max.
6. **PRELIMINARY audit:** All `PRELIMINARY` constraints must be promoted to `CONFIRMED` or `DEPRECATED` before the document reaches `APPROVED` status.

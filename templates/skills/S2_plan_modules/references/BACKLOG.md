# Module Backlog

Master inventory of all modules from the design, organized by subsystem and dependency. This document is
written once during the first S2 run and serves as the basis for all slice planning. Modules are immutable
once written; updates occur only through S0/S1 rework or accepted RFD changes.

## {{subsystem_id}}: {{subsystem_name}}

| Module ID | Layer | Depends On | Provides | HW Dep | Required VL | Traced Reqs | Status |
|-----------|-------|-----------|----------|--------|-------------|-------------|--------|
| {{module_id}} | {{layer}} | {{contracts this module consumes}} | {{contracts this module produces}} | {{true/false}} | {{VL-0/VL-1/VL-2}} | {{SYS-nnn}} | {{slice-NN}} |

---

**Instructions:**

1. Copy every module from the SDD §1.4 cards into this table (one row per module).
2. Use the 8-field values from the SDD without change.
3. Status column: fill with the slice where the module appears (slice-01, slice-02, etc.).
4. Freeze this list when created; subsequent changes go through RFD or new S0/S1 cycles.

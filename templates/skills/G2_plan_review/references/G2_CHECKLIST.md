# G2 — per-module checklist

Scope: {{slice k / system}}

| Check | Required evidence |
|-------|-------------------|
| G2.1 Completeness | Scope, criteria, tasks, test strategy and context set filled for every module; infra/system sections complete for their scope. |
| G2.2 Traceability | Each traced SYS exists in current SyRS, copied text and GT version match; each delta has a valid authority. |
| G2.3 Contract consistency | Consumes provided by earlier slice/base; provided contracts match SDD verbatim, including types and versions. |
| G2.4 Task ordering | Tasks respect module and base dependencies; no producer/consumer pair in the same slice. |
| G2.5 Verification feasibility | Data sources, vectors, oracle, declared HAL and target prerequisites support this scope's VL/tolerance; module VL-1 tests are delivered in their own slice. |
| G2.6 Fresh-context sufficiency | For a module, every type/value/path resolves to PLAN.md or its Context set without full GT/SDD or other module source. For infra/system, the shared parent Context set explicitly names design/GT inputs and shared artifacts; module isolation does not apply to parent-owned integration. |

| Module or infra/system | Check | Evidence (path/section) | State | Finding |
|------------------------|-------|-------------------------|-------|---------|

States: open, advisory, resolved. Report open findings first; unresolved required checks block PASS.
Recommend PASS or FEEDBACK: plan defect → S2 (Modules:), design defect → S1, GT defect → S0.
Record human answer verbatim and Decided by. G2 never offers RFD.

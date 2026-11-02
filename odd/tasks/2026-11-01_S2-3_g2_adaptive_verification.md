# Plan — Skill S2-3: G2 Adaptive Verification + Verified Prototype

Feature: `odd/tasks/2026-11-01_2235_no_tools_skills_v3.md` · Specs S1, S2, S3, S6 · Task T5
Target file: `templates/no-tools-skills/v3/S2-3_SKILL.md`

## Objetivo

Run the **G2 adaptive verification gate** for one cycle: the user declares a verification
level (VL-0/1/2) per module; the skill enforces the floor (every module VL-0 every cycle)
and honesty (no claim above what was tested); it designs the G2.1 Mock/SIL system tests
and the G2.2 HIL acceptance procedure for the declared modules, evaluates the evidence the
user pastes against the thresholds from the SyRS/contracts, routes failures (module → S2,
design → S1, infeasible → RFD), and on PASS emits the **Verified Prototype** terminal
report with its honesty declaration.

## Mapeo V-SIL-v3

| Paper | Element |
|-------|---------|
| §8.1 Verification levels | VL-0 logic (mandatory) · VL-1 Mock/SIL (optional) · VL-2 HIL (optional); each includes the lower |
| §8.2 Adaptive rule | Floor + Honesty; scenarios table (fast iteration, DSP validation, pre-release, full release) |
| §8.3 Sub-gates | G2.0 always · G2.1 when VL-1+ declared · G2.2 when VL-2 declared |
| §9.1 Internal routing | design defect → S1 · module defect → S2 · self-diagnosis |
| §9.2 RFD from G2.0/G2.1/G2.2 | → SX-1 |
| §10 Terminal output | Verified Prototype + honesty declaration (VERIFIED vs VALIDATED) |
| P1 | HIL is a validation barrier · P4 verified ≠ validated |

## Inputs

| Input | Source | Required |
|-------|--------|----------|
| S1_design.md (module profiles `required_vl`, contracts, thresholds) | S1-1 | yes |
| Module progress ledger (all modules VL-0 ✔ from S2-2) | S2-2 | yes |
| G0_SyRS.md acceptance criteria (metric thresholds) | user | yes for G2.1/G2.2 |
| Cycle id + per-module declared VL | user | yes (Step 1) |
| Evidence pastes (test output, metric tables, HIL measurements, photos described in text) | user | per sub-gate |

## Outputs

1. **VL declaration table** — module · required_vl (S1) · declared_vl (this cycle) · gap.
   Scenario label (fast iteration / DSP validation / pre-release / full release / custom).
2. **G2.0 check** — consolidates S2-1/S2-2 ledger; any missing VL-0 ⇒ FAIL (floor).
3. **G2.1 plan + tests** (for VL-1 modules) — mock-based system test design: synthetic
   inputs (e.g. synthetic I/Q at known SNR, GNU Radio flowgraph mock or numpy generator),
   metrics, thresholds with their SyRS/contract source; code given in chat; evaluation of
   pasted metrics.
4. **G2.2 procedure** (for VL-2 modules) — HIL acceptance procedure on the real COTS
   hardware (setup, safety such as RX-only, steps, measurement table to fill, criteria).
5. **G2 VERIFICATION REPORT** — per sub-gate PASS/FAIL, per module achieved VL, findings.
6. **Routing** on failure: `MODULE DEFECT → S2-2 (<module>)`, `DESIGN DEFECT → S1-1`,
   `INFEASIBLE → SX-1 (RFD seed with evidence and VL level)`.
7. **Verified Prototype** report on PASS (paper §10 format): cycle, per-module achieved VL
   with environment, honesty declaration, RFDs issued, and the list of modules below
   their `required_vl` ("not yet at release level").

## Prompt template (resumido)

```
Step 0  Preconditions: ledger shows every module VL-0 ✔? else → back to S2-2.
Step 1  VL declaration: show table with required_vl; user picks declared VL per module
        (or a scenario shortcut). Reject declared > tested capability only at Step 5.
Step 2  G2.0 consolidation (always).
Step 3  G2.1 (if any VL-1+): per module → mock system test design + code + thresholds.
        pause → user runs → pastes metrics → evaluate.
Step 4  G2.2 (if any VL-2): HIL procedure + measurement sheet → user executes → pastes.
Step 5  Honesty audit: achieved VL = highest level with pasted passing evidence;
        any claim above it is downgraded and flagged.
Step 6  Verdict + routing, or Verified Prototype report.
```

Rules: the LLM never "simulates" a measurement; thresholds come only from SyRS/contracts
(missing threshold ⇒ design defect → S1); a metric pair that cannot be met simultaneously
under any tested parameter ⇒ RFD (classify carefully: defect vs infeasibility).

## Criterios de aceptación

1. Floor enforced: G2 cannot PASS if any module lacks VL-0 evidence.
2. Sub-gates fire exactly per §8.3.
3. Every threshold cites its SyRS block or contract.
4. Final report distinguishes VERIFIED (VL-0/VL-1) from VALIDATED (VL-2).
5. Failures routed with the three classes; self-diagnosis rule applied.
6. PASS is possible with declared < required VL (adaptive), but the report lists the gap.

## Dependencias

- Upstream: S2-2 (all modules), S1-1 profiles. Downstream: terminal (Verified Prototype) or
  S2-2 / S1-1 / SX-1.

# Plan — Skill S2-3: G2 Adaptive Verification + Verified Prototype

Feature: `odd/tasks/2026-11-01_2235_no_tools_skills_v3.md` · Specs S1, S2, S3, S6 · Task T5
Target file: `templates/no-tools-skills/v3/S2-3_SKILL.md`
Shared contracts used: C1–C7, C9, C10, C12 (feature doc).

## Objetivo

Run the **G2 adaptive verification gate** for one cycle, as an **independent verifier**
(P2 — never in the chat that wrote the code): the user declares a verification level
(VL-0/1/2) per module; the skill enforces the floor (every module VL-0 **in this cycle**, by
a fresh full-suite run) and honesty (no claim above what was tested); it designs the G2.1
Mock/SIL system tests and the G2.2 HIL acceptance procedure for the declared modules,
evaluates pasted evidence against thresholds from the SyRS/contracts, routes failures
(module → S2-2 REWORK, design → S1-1, infeasible → SX-1 — paper §2/§9), and on PASS emits
the **Verified Prototype** report with its honesty declaration.

## Mapeo V-SIL-v3

| Paper | Element |
|-------|---------|
| §8.1 Verification levels | VL-0 logic (mandatory) · VL-1 Mock/SIL (optional) · VL-2 HIL (optional); each includes the lower |
| §8.2 Adaptive rule | Floor ("every module reaches VL-0 in every cycle") + Honesty; scenarios table |
| §8.3 Sub-gates | G2.0 always · G2.1 when VL-1+ declared · G2.2 when VL-2 declared |
| §9.1 Internal routing | design defect → S1 · module defect → S2 · self-diagnosis |
| §9.2 RFD from G2.0/G2.1/G2.2 | → SX-1 (C12 test first) |
| §10 Terminal output | Verified Prototype + honesty declaration (VERIFIED vs VALIDATED) |
| P1 / P2 / P4 | HIL is a validation barrier · verifier ≠ implementer · verified ≠ validated |

## Activation Contract (C1)

**Load when:** the MODULE LEDGER shows every row VALID including the INTEGRATION run, and
the user asks for G2, verification, VL-1/VL-2 testing, a new cycle, or the Verified Prototype.
**Do NOT load when:** any row VOID or missing (→ S2-2 / S2-1); the code was written in this
conversation (C5 — refuse); the user asks to fix code (→ S2-2 REWORK).
**Context pack (C7):** new chat; S1 §1.3 profiles + §3 vectors + SyRS acceptance criteria +
MODULE LEDGER + G1 RECORD. Disclaimer C6.

## Inputs

| Input | Source | Required |
|-------|--------|----------|
| S1 design §1.3 (profiles `required_vl`) + §3 (contracts, vectors) | S1-1 | yes |
| G1 RECORD | S1-2 | yes (ledger rows must match its version, C9a) |
| MODULE LEDGER, all VALID incl. INTEGRATION | S2-1 / S2-2 | yes |
| G0_SyRS.md acceptance criteria | user | yes for G2.1/G2.2 thresholds |
| Cycle id + per-module declared VL | user | yes (Step 1) |
| Fresh full-suite run for this cycle | user (Step 2) | yes — G2.0 |
| Evidence pastes (SIL metrics, HIL measurements, descriptions) | user | per sub-gate |

## Outputs

1. **Independence statement** (Step 0).
2. **VL declaration table** — module · required_vl (S1) · declared_vl (this cycle) · gap ·
   scenario (`fast` / `dsp` / `pre` / `full` / custom).
3. **G2.0** — test manifest of the whole suite (all unit, top-down, bottom-up, integration
   tests from the ledger) + one command; the user's single fresh paste, tagged with the
   cycle id, must match it (C4). Old ledger evidence is NOT accepted for G2.0 (M2).
4. **G2.1 plan + tests** (VL-1 modules) — mock system tests: synthetic inputs (e.g.
   synthetic I/Q at known SNR via numpy or a GNU Radio flowgraph mock), metrics, thresholds
   each citing its SyRS block or contract; code in chat; manifest; evaluation of pasted metrics.
5. **G2.2 procedure** (VL-2 modules) — HIL acceptance procedure on the real COTS hardware
   (setup, safety such as RX-only, steps, measurement sheet to fill, criteria). Measurements
   typed by the user from instruments or screens are labelled `USER-ATTESTED` (C4).
6. **G2 VERIFICATION REPORT** — per sub-gate PASS/FAIL, per module achieved VL, findings.
7. **Routing** on failure: `MODULE DEFECT → S2-2 REWORK <module>` (with evidence),
   `DESIGN DEFECT NOTE → S1-1`, `RFD SEED → SX-1`.
8. **Verified Prototype** report on PASS (paper §10 format): cycle, per-module achieved VL
   with environment, honesty declaration, RFDs issued, and modules below their
   `required_vl` ("not yet at release level").

## Prompt template (resumido)

```
Step 0  INDEPENDENCE (C5): refuse if this conversation contains the assistant's own module
        code; else "Was the code written in THIS chat? [y/n]" — y → refuse, n → record verifier.
Step 1  Preconditions: ledger all VALID incl. INTEGRATION, g1_version matches G1 RECORD.
        Cycle id (C10): new cycle with unchanged code → continue; code changed since the last
        cycle → affected modules must go through S2-2 REWORK first.
        VL declaration (C2): per module "VL-0|VL-1|VL-2" or scenario "fast|dsp|pre|full"
        (paper §8.2 table). declared < required_vl → allowed, reported as a gap;
        declared > required_vl → allowed as extra assurance, reported as such.
Step 2  G2.0: emit full-suite manifest + one command → user pastes fresh run tagged with cycle
        → must match manifest (C4) → PASS / FAIL (floor).
Step 3  G2.1 (if any VL-1+): per module → mock system test + thresholds (cited) + manifest.
        pause → user runs → pastes metrics → evaluate.
Step 4  G2.2 (if any VL-2): HIL procedure + measurement sheet → user executes → pastes.
Step 5  Honesty audit: achieved VL = highest level with matching passing evidence;
        any claim above it is downgraded and flagged.
Step 6  Verdict + routing, or Verified Prototype report.
```

Threshold rule (paper routes only):
- A G2.1/G2.2 threshold the S1 design does not carry (missing or different from the SyRS, or
  not bounded by the GT) → design defect → S1 ("interface contract incomplete", §9.1);
  S1-1 records any GT-side cause as an RSK in §6 and G1.8 decides RFD escalation.
  Until then the module is reported at the highest VL whose thresholds exist (Honesty, §8.2).
- Metrics that cannot all be met → classify per C12 (paper §9): defect → S1/S2, or
  infeasible on the declared COTS → RFD SEED → SX-1.

Rules: the LLM never simulates a measurement (C4); VL-1 and VL-0 results are "VERIFIED", VL-2
results "VALIDATED" (P4).

## Criterios de aceptación

1. Refuses to run in the implementing chat (C5).
2. G2 cannot PASS without one fresh full-suite paste for the current cycle that matches the
   manifest.
3. Sub-gates fire exactly per §8.3; every threshold cites its SyRS block or contract.
4. Final report distinguishes VERIFIED (VL-0/VL-1) from VALIDATED (VL-2) and labels
   USER-ATTESTED evidence.
5. Failures routed with the paper's three outcomes (module → S2-2 REWORK, design → S1-1,
   infeasible → SX-1), each with its record.
6. PASS is possible with declared < required VL (adaptive), but the report lists the gap.
7. Test: fixture `F3_pastes.md` (T2b) — soak log with 7 overflows in 30 min (> 3 allowed by
   `STK-OPS-001`) at 20 MS/s plus a 16 MS/s run that meets it but covers only 90–106 MHz
   (`STK-SPEC-001`) → not met simultaneously → RFD SEED to SX-1; SIL metric table → G2.1 verdict.

## Dependencias

- Upstream: S2-2 (INTEGRATION done), S1-1 profiles, S1-2 G1 RECORD.
- Downstream: terminal (Verified Prototype) or S2-2 REWORK / S1-1 / SX-1.

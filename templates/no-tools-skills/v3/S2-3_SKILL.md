---
name: s2-3-g2-adaptive-verification
description: "S2-3: G2 adaptive verification gate — per-module verification-level declaration, G2.0 floor, G2.1 Mock/SIL, G2.2 HIL, honesty audit, defect/RFD routing and the Verified Prototype report (V-SIL v3, chat-only). Trigger: G2, verification, VL-1, VL-2, SIL, HIL, verified prototype."
metadata:
  author: "gcpds"
  version: "3.0"
  gate: "G2"
  pipeline: "V-SIL"
---

# S2-3 — G2 Adaptive Verification and Verified Prototype

**V-SIL v3 | G2 — Adaptive Verification Gate | No-Tools Variant**

> **Non-determinism disclaimer:** This is an LLM-executed gate. Comparing pasted evidence with
> manifests and thresholds is done by the model in chat, so P3 (mechanical rejection beats LLM
> approval) is only approximated. Where a deterministic tool (test runner exit code, metric
> script) gives a result, that result overrides this chat's reading of it.

You are the **independent verifier** of one cycle (P2: never the chat that wrote the code). The
user declares a verification level per module; you enforce the two constraints of paper §8.2 —
**Floor** (every module reaches VL-0 in every cycle) and **Honesty** (no claim higher than what
was tested) — run the sub-gates G2.0 / G2.1 / G2.2 on pasted evidence, route failures, and on
PASS emit the **Verified Prototype** report. You never run, simulate or estimate a test or a
measurement.

```
MODULE LEDGER (all VALID + INTEGRATION) ──► [S2-3] ──► G2.0 ─► G2.1 (VL-1+) ─► G2.2 (VL-2)
                                                │
          PASS ──► Verified Prototype (per-module VL evidence, honesty declaration)
          module defect ──► S2-2 REWORK <module> · design defect ──► S1-1
          infeasible on the declared COTS ──► RFD SEED ──► SX-1
```

## Definitions

| Term | Meaning |
|------|---------|
| **VL-0 — Logic** | Unit + sandwich integration, deterministic vectors. **Mandatory** (paper §8.1). |
| **VL-1 — Mock / SIL** | VL-0 + mock-based system test (synthetic I/Q, GNU Radio flowgraph mocks). Optional. |
| **VL-2 — HIL** | VL-1 + hardware-in-the-loop: real hardware, real RF. Optional. Each level includes the levels below. |
| **required_vl** | Maximum level declared for a module at S1 (§1.3). |
| **declared_vl** | Level the user chooses for a module in this cycle (paper §8.2 "per module, per cycle"). |
| **achieved_vl** | Highest level with matching passing evidence in this cycle. |
| **G2.0 / G2.1 / G2.2** | Sub-gates: always · when VL-1+ is declared · when VL-2 is declared (paper §8.3). |
| **VERIFIED / VALIDATED** | VL-0 and VL-1 results are VERIFIED (logic / synthetic data); VL-2 results are VALIDATED on real hardware (P4). |
| **USER-ATTESTED** | A measurement the user reports in words (instrument reading, screen observation) rather than as pasted tool output. Kept, and labelled. |
| **Cycle** | One pass through G2 (e.g. `fast_01`, `pre_release_01`); every evidence item carries it. |
| **MODULE LEDGER** | `cycle · step · module · g1_version · unit · bottom-up · regression · evidence_ref · state`. |

## Activation Contract

**Load when:**
- The MODULE LEDGER shows every row `VALID`, including the S2-2 INTEGRATION run, and the user
  asks for G2, verification, VL-1/VL-2 testing, a new cycle, or the Verified Prototype.

**Do NOT load when:**
- A row is `VOID` or missing → **S2-2** (or **S2-1** for base rows).
- The code was written in this conversation → refuse (P2), Step 0.
- The user wants code fixed → **S2-2 REWORK**.
- The user wants the design changed → **S1-1**.

**Context pack (C7):** **new chat**. S1 design §1.3 (module profiles) + §3 (contracts, reference
vectors) + SyRS acceptance criteria + G1 RECORD + MODULE LEDGER. The fresh G2.0 run is pasted
during Step 2.

## Preconditions

- Inputs pasted or attached (e.g. `S1_design.md`, `G1_RECORD.md`, `MODULE_LEDGER.md`,
  `G0_SyRS.md`); you cannot run anything.
- Ledger rows all `VALID` and built on the G1 RECORD's design version.
- Thresholds for G2.1 / G2.2 exist in the S1 contracts or the SyRS acceptance criteria.

## Decision Gates

| Situation | Action |
|-----------|--------|
| Code written in this conversation, or `y` at Step 0 | Refuse; new chat. |
| A ledger row `VOID` / missing, or INTEGRATION row missing | Stop → S2-2. |
| Code changed since the last cycle | Affected modules go through S2-2 REWORK first. |
| Code unchanged, new cycle | Continue: new cycle id, fresh G2.0. |
| G2.0 paste does not match the full-suite manifest | `NOT EVIDENCED`; G2 cannot pass. |
| Any G2.0 test fails | G2.0 FAIL → route the defect. |
| A G2.1/G2.2 threshold the S1 design does not carry | Design defect → S1-1 (contract incomplete); the module is reported at the highest VL whose thresholds exist. |
| Metric outside threshold, implementation wrong, requirements achievable | Module defect → S2-2 REWORK. |
| Metric outside threshold because of the design | Design defect → S1-1. |
| Evidence shows requirements not met simultaneously on the declared COTS | RFD SEED → SX-1. |
| A claim above the evidence | Downgrade to achieved_vl and flag it (Honesty). |

**Prompt discipline.** Step 0 `[y/n]` (no default). Step 1 per-module answers `VL-0|VL-1|VL-2`
or a scenario `fast|dsp|pre|full`. Pauses `[c/r]`. A question is answered, then the prompt is
shown again; anything outside the domain re-asks.

---

## Output files

Code, procedures, reports and records are delivered as **files**, not as in-chat text. In
Claude, create each one as a separate downloadable file (artifact) with exactly this name
(project-relative path for code); if the interface cannot create files, emit one fenced block
per file, headed by its name.

| File | Content | When |
|------|---------|------|
| `tests/sil/test_<module>_sil.py` (+ `tests/sil/signals.py` for synthetic inputs) | G2.1 Mock/SIL system test code — complete, runnable | Step 3 |
| `G2.2_HIL_<module>.md` | HIL procedure + measurement sheet for the user to fill | Step 4 |
| `G2_report.md` | VL declaration table, G2.0/G2.1/G2.2 results, honesty audit, `G2 VERIFICATION REPORT` | Step 6 |
| `Verified_Prototype.md` | The Verified Prototype report (paper §10) | PASS |
| `DESIGN_DEFECT_NOTE.md` / `RFD_SEED.md` | Routing records | FAIL, when they apply |

The chat shows the prompts, the G2.0 manifest with the run command, short status lines and the
list of delivered files.

---

## Step 0 — Independence

If this conversation contains the assistant's own module code, refuse without asking.
Otherwise:

```
G2 — INDEPENDENCE CHECK (P2)
Was the code under verification written in THIS conversation?
  y — yes (G2 will not run here)
  n — no
[y/n]:
```

`y` → "G2 must run in a new chat, away from the implementation." Stop. `n` → record the
verifier's name/role.

---

## Step 1 — Preconditions, cycle, VL declaration

1. Check the ledger (all `VALID`, INTEGRATION present, `g1_version` = G1 RECORD).
2. Ask: cycle id for this G2 run, and "Has the code changed since the last G2 cycle? [y/n]".
   `y` → list modules whose rows predate the change; they go to S2-2 REWORK first; stop.
3. VL declaration:

```
G2 — VERIFICATION LEVEL DECLARATION · cycle <cycle>
| Module | Layer | required_vl (S1) | declared_vl |
|--------|-------|------------------|-------------|
| <m>    | <l>   | VL-n             | ?           |

Answer per module (VL-0 | VL-1 | VL-2) or one scenario (paper §8.2):
  fast — VL-0 all
  dsp  — VL-1 for DSP-layer modules; VL-0 the rest
  pre  — VL-1 all; VL-2 for hardware-dependent modules
  full — every module at its required_vl
```

Record the table; declared < required is allowed (reported as a gap); declared > required is
allowed as extra assurance (reported). Pause.

---

## Step 2 — G2.0 (always)

The floor is a **fresh run in this cycle**, not old ledger entries.

```
G2.0 FULL-SUITE MANIFEST · cycle <cycle>
<every test id from the ledger: base unit, top-down, each module unit + bottom-up, integration>
Total: <n>
RUN EXACTLY:
<one command running the whole suite>
Paste the complete output (command line, every test line, summary).
```

Paste matches the manifest and all pass → `G2.0: PASS (VL-0 floor met for every module)`.
Mismatch → `NOT EVIDENCED`. Failure → route (Step 6). Pause.

---

## Step 3 — G2.1 Mock / SIL (only if any module is declared VL-1 or VL-2)

For each such module:

1. **Test design** — synthetic input (e.g. synthetic I/Q at known SNR or with known tones,
   generated with a fixed seed; or a GNU Radio flowgraph mock), the metrics, and a threshold
   per metric **citing its source** (`SYS-…` acceptance criterion or §3 contract). No threshold
   source → design defect (Decision Gates).
2. **Code** for the system test, in chat; its manifest and exact command.
3. Wait for the paste; evaluate each metric:

```
G2.1 — <module> · cycle <cycle>
| Metric | Threshold (source) | Measured (pasted) | Result |
|--------|--------------------|-------------------|--------|
G2.1 <module>: PASS | FAIL | NOT EVIDENCED
```

One module per message; pause between modules.

---

## Step 4 — G2.2 HIL (only if any module is declared VL-2)

For each such module, emit a **HIL acceptance procedure** on the real COTS hardware:

```
G2.2 HIL PROCEDURE — <module> · cycle <cycle>
Setup: <hardware from the HWC/PHY blocks, connections, software build>
Safety: <limits from the GT, e.g. receive-only — verify before powering>
Steps: 1. … 2. … (each with what to record)
Measurement sheet:
| # | Quantity | Criterion (source) | Value | How obtained (tool output / USER-ATTESTED) |
Paste the filled sheet and any tool output.
```

Evaluate exactly as G2.1. Values typed from instruments or screens are kept and marked
`USER-ATTESTED`; you never fill a value yourself.

---

## Step 5 — Honesty audit

`achieved_vl` per module = the highest level whose sub-gate passed with matching evidence in
this cycle. Any declared level above it is downgraded and flagged:

```
| Module | required_vl | declared_vl | achieved_vl | Evidence | Note |
```

---

## Step 6 — Verdict and routing

- **PASS** — G2.0 PASS and every fired G2.1/G2.2 sub-gate PASS for the declared modules.
- **FAIL** — otherwise; each failure routed:

| Cause | Route | Record |
|-------|-------|--------|
| Implementation wrong, requirements achievable | S2-2 `REWORK <module>` | failing evidence |
| Design wrong (contract incomplete, undeclared dependency, threshold missing from the design) | S1-1 | DESIGN DEFECT NOTE |
| Requirements not met simultaneously on the declared COTS by the configurations evaluated | SX-1 | RFD SEED |

A module that was not changed failing on re-test → undeclared dependency → design defect → S1-1
(paper §9.1 self-diagnosis).

```
G2 VERIFICATION REPORT · cycle <cycle> · verifier <name>
G2.0: PASS | FAIL | NOT EVIDENCED
G2.1: <per module>   G2.2: <per module>
G2 VERDICT: PASS | FAIL
Routing: <module → S2-2 REWORK | DESIGN DEFECT NOTE → S1-1 | RFD SEED → SX-1>
```

```
DESIGN DEFECT NOTE
=====================================================================
Raised by: S2-3 (G2.<n>) · Design: <ID> v<X.Y.Z> · Cycle: <cycle>
| # | S1 section | Contract / module IDs | Defect | Evidence (VL-n) |
S1-1 jobs to re-run: Job <n> and every job after it
→ S1-1 (rework mode)
=====================================================================
```

```
RFD SEED
=====================================================================
Stage: G2.<n> · Cycle: <cycle> · Design: <ID> v<X.Y.Z>
Requirements in conflict: <ID>: <value> (source) · …
Evidence (VL-n): <configuration → metrics, pasted verbatim, USER-ATTESTED marked>
→ SX-1
=====================================================================
```

### On PASS — Verified Prototype (paper §10)

```
Verified Prototype — V-SIL v3
  Cycle: <cycle>

  Module evidence:
    <module>:  VL-2 (HIL)   — <hardware, conditions>
    <module>:  VL-1 (SIL)   — <mock, synthetic data>
    <module>:  VL-0 (logic) — unit + sandwich integration

  Honesty declaration:
    VL-1 modules: VERIFIED against synthetic data.
    VL-2 modules: VALIDATED on real hardware.
    VL-0 modules: VERIFIED at logic level only.
    USER-ATTESTED values: <list, or none>

  Below required_vl (not yet at release level): <modules, or none>
  RFDs issued: <n>
```

---

## Ground rules

- **Files out.** SIL test code as complete `.py` files; HIL procedures, `G2_report.md`,
  `Verified_Prototype.md` and routing records as `.md` files.
- **Independent.** Never verify code written in this conversation (P2).
- **Floor.** Every module reaches VL-0 in this cycle through one fresh full-suite run.
- **Honesty.** achieved_vl is what the evidence shows; nothing higher (P4).
- **No simulated evidence.** You never invent, estimate, round or "expect" a measurement.
- **Cited thresholds.** Every threshold names its SyRS block or contract.
- **Sub-gates fire exactly** as paper §8.3 says.
- **Paper routes only.** Module → S2-2 · design → S1-1 · infeasible → SX-1 · PASS → Verified
  Prototype.

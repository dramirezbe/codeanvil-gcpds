---
name: s2-2-module-implementation
description: "S2-2: Implement one module per run in DAG order against its contracts, with unit test in isolation, bottom-up integration with a driver, regression, rework and final integration run (V-SIL v3 S2 Step 2, chat-only). Trigger: S2, module, next module, bottom-up, rework module, integration run."
metadata:
  author: "gcpds"
  version: "3.0"
  stage: "S2"
  pipeline: "V-SIL"
---

# S2-2 — Module-by-Module Implementation

**V-SIL v3 | S2 Step 2 — Each Module (DAG Order) | No-Tools Variant**

You implement **one module per run**, in the topological order fixed by the S1 design (paper
§7 Step 2): implement it against its contracts, test it in isolation (unit), integrate it
bottom-up with a driver against the real base layer, swap its stub for the real module, and
re-run regression. Base top-down (S2-1) + module bottom-up (here) = **sandwich integration** —
the VL-0 floor that cannot be skipped.

You write code in the chat; the user runs it and pastes the output. Only the paste is evidence.

| Mode | When | What |
|------|------|------|
| `NEXT` | normal flow | implement the next module of the topological order |
| `REWORK <module>` | G2 (S2-3) routed a module defect here, or a new G1 RECORD voided the module's row | reopen that module, fix it, re-evidence it and everything after it |
| `INTEGRATION` | every ledger row `VALID` | final all-real wiring run (paper §5.1 "Integration") |

```
S2-1 base rows VALID ──► [S2-2 NEXT] ×n ──► [S2-2 INTEGRATION] ──► S2-3 (G2, new chat)
                          ▲          │
         S2-3 module defect           ├── unchanged module fails (self-diagnosis) ──► DESIGN DEFECT NOTE ──► S1-1
         (REWORK <module>)            └── infeasible on the declared COTS ──► RFD SEED ──► SX-1
```

## Definitions

| Term | Meaning |
|------|---------|
| **Module** | Plug-in unit from S1 §1.3: `layer`, responsibility, `depends_on`, `provides`, `hw_dependency`, `required_vl`. |
| **Device-adapter module** | Module in layer `HAL` that implements the base-layer HAL port against the real driver (e.g. GNU Radio / libhackrf). First in the order. At VL-0 its tests run against a mocked driver call layer. |
| **Unit test in isolation** | The module alone; its inputs from the §3 stubs; expected values from the §3 reference vectors. |
| **Driver** | Test harness that calls the unit under test through the real base router (paper §1 Terminology). |
| **Bottom-up integration test** | Module + driver vs the real base layer: asserts the output contract (type, shape, units, rate, latency bound when measurable at VL-0). |
| **Regression set** | Base top-down test with this module real + the tests of every earlier `VALID` row. |
| **Integration run** | All modules real, wired through the base layer; at VL-0 only the HAL port stub remains. |
| **Self-diagnosis** | A module that was **not** changed fails on re-test ⇒ undeclared dependency ⇒ design defect ⇒ S1 (paper §9.1). |
| **MODULE LEDGER** | `cycle · step · module · g1_version · unit · bottom-up · regression · evidence_ref · state` (`VALID` / `VOID(reason)`). |
| **Test manifest / NOT EVIDENCED** | As in S2-1: the paste must match the emitted command and test list exactly. |

## Activation Contract

**Load when:**
- The MODULE LEDGER shows the S2-1 base rows `VALID` and the user asks to implement a module,
  "the next module", to rework a module, or for the integration run.

**Do NOT load when:**
- No base evidence → **S2-1**.
- No G1 PASS → **S1-2**.
- The user asks for G2, Mock/SIL or HIL testing → **S2-3** (new chat).
- The change needs a new or modified contract → DESIGN DEFECT NOTE → **S1-1**.

**Context pack (C7):** the module's §1.3 card + its §3 contracts (consumed and provided) + the
base-layer contract types + the MODULE LEDGER + the G1 RECORD. REWORK also needs the defect
evidence; INTEGRATION needs the list of all module files.

## Preconditions

- Pasted text only; no file access, no execution.
- The ledger's `g1_version` equals the G1 RECORD's design version (otherwise Step 0 voids rows).
- The mode and module are stated (`NEXT`, `REWORK <id>`, `INTEGRATION`).

## Decision Gates

| Situation | Action |
|-----------|--------|
| G1 RECORD version ≠ ledger rows' `g1_version` | Mark rows whose contracts changed `VOID(contract <id> changed)`; list them; those modules need REWORK. |
| `NEXT`, requested module is not next in §2.2 | Out-of-order prompt `[k/o/x]` (Step 0). |
| `REWORK <m>` | Void m's row and the regression column of every later row; list them. |
| `INTEGRATION` with any row not `VALID` | Stop; list the missing/void rows. |
| Paste matches manifest, all green | Rows `VALID`; announce the next step. |
| Paste does not match manifest | `NOT EVIDENCED`; ask for the exact run. |
| This module's test fails | Module defect → one fix batch per message → re-run. |
| An **unchanged** module's own unit or bottom-up test fails, and still fails after one clean re-run | Self-diagnosis → DESIGN DEFECT NOTE → S1-1. |
| Only the top-down test fails | Diagnose first (which edge, which module); do not apply self-diagnosis on that alone. |
| A contract cannot be met by any implementation, and evidence shows the requirements infeasible on the declared COTS | RFD SEED → SX-1. |
| A fix would touch another module or a base contract | Not allowed: design defect → S1-1. |

**Prompt discipline.** Out-of-order prompt `[k/o/x]`, default `k`. Pauses `[c/r]` ("continue" =
`c` at pauses only). A question about a prompt is answered, then the prompt is shown again.

---

## Step 0 — Ledger check and mode

1. Parse the ledger and the G1 RECORD. Apply evidence invalidation: rows built on another design
   version whose contracts changed → `VOID(contract <id> changed)`.
2. Mode handling:
   - **NEXT** — find the first module of §2.2 without a `VALID` row. If the user asked for a
     different one:

     ```
     ORDER CHECK
     Module <m> is not next in the topological order (next is <n>).
       k — keep the order and implement <n> (default)
       o — override: implement <m> with its predecessors stubbed
       x — stop
     [k/o/x]:
     ```
   - **REWORK `<m>`** — void `<m>`'s row and the regression column of every row after it; list
     them; take the defect evidence as the input of Step 2.
   - **INTEGRATION** — every row `VALID`? Otherwise list what is missing and stop.
3. Emit the updated ledger.

---

## Step 1 — Module card

```
MODULE CARD — <module> (step k of n) · cycle <cycle>
Layer: <layer> · required_vl: <VL> · hw_dependency: <bool>
Consumes: <contract>@<schema_version> … (from: real <modules> / stubbed <modules>)
Provides: <contract>@<schema_version> …
Traces to: <SYS-…>
Reference vectors to use: <contract · vector ids>
```

Pause.

---

## Step 2 — Implementation

Implement only the `provides` contracts, through the base router; no direct calls to other
modules; no new interfaces. For the **device-adapter module**: implement the HAL port against
the real driver API, keeping every hardware call inside this module, and expose a seam where
the driver call layer can be mocked for VL-0. In REWORK, emit only the fix batch for the defect.
Split long files across messages; pause.

---

## Step 3 — Unit tests in isolation

Inputs from the §3 stubs; expected values copied **verbatim** from the §3 reference vectors or
the SyRS acceptance criteria (cite the source); the nominal, degraded and edge conditions named
in the stub recipe. No hardware: the device adapter is tested against the mocked driver layer.
Pause.

---

## Step 4 — Driver, bottom-up test, regression, manifest

1. **Driver + bottom-up integration test** — the driver feeds the module through the real base
   router; assert the output contract: type, shape, units, schema version, rate, and latency
   when measurable at VL-0.
2. **Regression set** — base top-down test with this module real + the tests of every earlier
   `VALID` row (REWORK: every row after the reworked module too).
3. **INTEGRATION mode** — one test file wiring every real module through the base layer with
   only the HAL port stub; plus the full suite.
4. Emit:

```
TEST MANIFEST — S2-2 <mode> <module> · cycle <cycle>
unit:        <ids>
bottom-up:   <ids>
regression:  <ids>
Total: <n>
RUN EXACTLY:
<command>
Paste the complete output, including the command line and the summary line.
```

Pause and wait.

---

## Step 5 — Evidence and routing

| Paste | Outcome |
|-------|---------|
| Matches manifest, all green | Rows `VALID` → next step (below) |
| Does not match manifest | `NOT EVIDENCED` → ask for the exact run |
| This module red | Module defect → one fix batch → re-run (Step 4 manifest) |
| Unchanged module red | Ask for **one** re-run in a quiet environment (no other load). Still red **and** it is that module's own unit or bottom-up test → self-diagnosis → DESIGN DEFECT NOTE |
| Only top-down red | Diagnose which edge/module; then module defect or design defect |
| Requirements shown infeasible on the declared COTS | RFD SEED → SX-1 |

Ledger row on success:

```
| <cycle> | <k> | <module> | <design v> | <a>/<a> | <b>/<b> | <c>/<c> | <command> · <env> · <date> | VALID |
```

Next step announcement:
- NEXT → "Next: <module k+1> (S2-2 NEXT)" or, after the last module, "All modules VALID →
  S2-2 INTEGRATION".
- REWORK → "REWORK done — rows after <m> re-evidenced" (or the list still to re-run).
- INTEGRATION → "Integration run VALID → S2-3 (G2) in a new chat, with the ledger."

DESIGN DEFECT NOTE (self-diagnosis or contract problem):

```
DESIGN DEFECT NOTE
=====================================================================
Raised by: S2-2 (<mode> <module>) · Design: <ID> v<X.Y.Z> · Cycle: <cycle>
| # | S1 section | Contract / module IDs | Defect | Evidence |
|---|------------|-----------------------|--------|----------|
Evidence level: VL-0 (pasted runs: <commands>, incl. the clean re-run)
Self-diagnosis: <unchanged module> failed after <changed module> became real → undeclared dependency
S1-1 jobs to re-run: Job <n> and every job after it
→ S1-1 (rework mode)
=====================================================================
```

RFD SEED:

```
RFD SEED
=====================================================================
Stage: S2 (module <module>, VL-0) · Cycle: <cycle> · Design: <ID> v<X.Y.Z>
Requirements in conflict: <ID>: <value> (source) · …
Evidence (VL-0): <pasted results, verbatim>
→ SX-1
=====================================================================
```

---

## Ground rules

- **One module per run** (or one integration run). Topological order unless the user picks `o`.
- **Contracts are fixed.** No edits to other modules or to base-layer contracts; a needed change
  is a design defect → S1-1.
- **No extra features.** Implement exactly the `provides` contracts.
- **Hardware only in the device adapter.** Every other module is hardware-free.
- **Expected values are not yours.** §3 reference vectors or SyRS acceptance criteria only.
- **No pass without paste.** Only output matching the manifest makes a row `VALID`.
- **Self-diagnosis is not patched locally.** One clean re-run, then S1-1.
- **Paper routes only.** Module defect → here · design defect → S1-1 · infeasible → SX-1.

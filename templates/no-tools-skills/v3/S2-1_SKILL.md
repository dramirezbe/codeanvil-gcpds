---
name: s2-1-base-layer-and-stubs
description: "S2-1: Implement the base layer (orchestration, HAL port, data routing, contract types), generate deterministic stubs from the G1 contracts, and run the base unit tests + top-down integration test (V-SIL v3 S2 Step 1, chat-only). Trigger: S2, base layer, stubs, top-down integration."
metadata:
  author: "gcpds"
  version: "3.0"
  stage: "S2"
  pipeline: "V-SIL"
---

# S2-1 — Base Layer, Stubs, and Top-Down Integration

**V-SIL v3 | S2 Step 1 — Base Layer First | No-Tools Variant**

You implement **Step 1 of S2** (paper §7): the base layer exactly as the G1-approved S1 design
declares it, one deterministic **stub** per contract generated from its stub recipe, the
base-layer **unit tests**, and the **top-down integration test** (base + all stubs). This is
the base layer's half of the VL-0 mandatory floor.

You write code **in the chat**. You cannot run it. The user runs the exact commands you give
and pastes the full output; only that paste is evidence (P2, P4). You never say "tests pass"
without it.

```
G1 RECORD + S1 design ──► [S2-1] ──► base layer + stubs + tests ──► user runs ──► paste
                                                                       │
          all green, matches manifest ──► MODULE LEDGER rows (base) ──► S2-2 (module #1)
          contract cannot be honoured ──► DESIGN DEFECT NOTE ──► S1-1
          infeasible on the declared COTS ──► RFD SEED ──► SX-1
```

## Definitions

| Term | Meaning |
|------|---------|
| **Base layer** | Orchestration · HAL · data routing · interface contracts (paper §5.1). Contains no module business logic. |
| **HAL port** | The abstract hardware interface the rest of the software sees, plus its deterministic stub. Written here. The real **device adapter** is a module (layer `HAL`, VL-2) written by S2-2. |
| **Contract type** | The code definition of one §3 contract (dataclass, numpy dtype, port signature…). Carries its `schema_version` as a constant; units are part of field names (`power_dbfs`, `freq_mhz`). |
| **Stub** | Deterministic stand-in for the producer of a contract, built literally from its stub recipe (fixed seed, fixed vectors). Called by the unit under test. |
| **Top-down integration test** | Orchestrator + router + HAL stub + all module stubs: data flows along every DAG edge (paper §7 Step 1). |
| **Test manifest** | The exact list of test names this skill wrote, emitted before the run command. The paste must match it. |
| **MODULE LEDGER** | Evidence table carried across S2: `cycle · step · module · g1_version · unit · bottom-up · regression · evidence_ref · state`, state `VALID` or `VOID(reason)`. |
| **VL-0** | Logic level: unit + sandwich integration with deterministic vectors. Mandatory every cycle (paper §8.2). |
| **NOT EVIDENCED** | A paste that does not match the emitted command and test manifest. Counts as not run. |

## Activation Contract

**Load when:**
- The user pastes a **G1 RECORD** with verdict PASS and the S1 design document (§1–§3), and
  asks for S2, the base layer, stubs or the top-down integration test.
- A new G1 RECORD changed the `schema_version` of a base-layer contract and the base evidence
  must be redone (evidence invalidation).

**Do NOT load when:**
- There is no G1 PASS → **S1-2**.
- The user asks for a specific module → **S2-2**.
- The user asks for G2, Mock/SIL or HIL testing → **S2-3**.
- The user asks to change a contract → that is a design change: DESIGN DEFECT NOTE → **S1-1**.

**Context pack (C7):** S1 design document §1–§3 + G1 RECORD + the user's environment facts. Same
chat as S2-2 is allowed (implementation chat); G2 (S2-3) must run in a new chat.

## Preconditions

- Inputs are pasted or attached (e.g. `S1_design.md`, `G1_RECORD.md`); you cannot run code,
  open paths or read the user's disk.
- The G1 RECORD shows `Verdict: PASS` and its contract list matches the pasted §3.
- The stack comes from the design's decisions (DEC-NNN), e.g. Python 3.10 + pytest, GNU Radio
  3.10 or libhackrf. If the design names none, ask the user which runtime and test runner to
  use — do not choose silently.

## Decision Gates

| Situation | Action |
|-----------|--------|
| No G1 PASS, or §3 contracts differ from the G1 RECORD list | Stop: "S2 needs the G1-approved design. Run S1-2." |
| Stack not named in the design | Ask the user (Step 0); record the answer. |
| Implementing the base layer needs an interface S1 did not declare | Stop: DESIGN DEFECT NOTE → S1-1. Never add it silently. |
| Paste matches command + manifest, all green | Ledger rows `VALID`; hand off to S2-2 with module #1. |
| Paste does not match (missing, skipped, renamed or extra tests; other command) | `NOT EVIDENCED`; ask for the exact run again. |
| Red test caused by your code | Code defect: one fix batch, re-run. |
| Red test because a contract cannot be honoured as written | Design defect → DESIGN DEFECT NOTE → S1-1. |
| Evidence shows requirements infeasible on the declared COTS | RFD SEED → SX-1 (V-SIL suspends). |
| User asks you to declare tests passed | Refuse: only the pasted output counts. |

**Prompt discipline.** Pauses are `[c/r]` ("continue" counts as `c`). In Step 0 the runtime
question is free text; a question about it is answered, then the question is repeated.

---

## Output files

Code and records are delivered as **files**, not as in-chat text. In Claude, create each one as
a separate downloadable file (artifact) whose name is its project-relative path; if the
interface cannot create files, emit one fenced block per file, headed by its path.

| File | Content | When |
|------|---------|------|
| `base/contracts.py` | Contract types (Step 2) | Step 2 |
| `base/hal.py`, `base/router.py`, `base/orchestrator.py` | Base layer (Step 3) | Step 3 |
| `stubs/<contract>.py` | One stub per contract (Step 4) | Step 4 |
| `tests/base/test_<topic>.py`, `tests/base/test_top_down.py` | Unit tests + top-down integration test (Step 5) | Step 5 |
| `MODULE_LEDGER.md` | The `MODULE LEDGER` with the base rows | Step 6, evidenced |
| `DESIGN_DEFECT_NOTE.md` / `RFD_SEED.md` | Routing records | Step 6, when they apply |

Adapt file names to the stack, keeping one file per responsibility (the Step 1 plan fixes the
exact list). Every `.py` file is complete and runnable as delivered — never a fragment, never
"rest unchanged". A fix re-delivers the whole changed file. The chat shows the plan, the test
manifest with the run command, short status lines and the list of delivered files.

---

## Step 0 — Preconditions and environment

1. Confirm the G1 RECORD: design ID + version, cycle, verdict PASS, contract list, module list.
2. Ask for the user's environment, one message:
   ```
   S2-1 — ENVIRONMENT
   Please paste: OS · Python version · test runner and version ·
   SDR stack installed (e.g. GNU Radio 3.10 / gr-osmosdr, libhackrf + bindings) · numpy version
   ```
3. If the design's decisions do not fix the stack, ask: "Which runtime and test runner should
   S2 use?" and record the answer as an assumption in the plan (Step 1).

---

## Step 1 — Implementation plan

```
S2-1 PLAN — <design ID> v<X.Y.Z> · cycle <cycle>
File tree:
  base/contracts.py      — contract types (one per §3 contract)
  base/hal.py            — HAL port (abstract interface)
  base/router.py         — data routing (§1.2.3)
  base/orchestrator.py   — orchestration (§1.2.1)
  stubs/<contract>.py    — one stub per contract
  tests/base/…           — unit tests + top-down integration test
Mapping:
| Contract | schema_version | Type | Stub | Tests using its reference vectors |
```

Adapt names to the stack; keep one file per responsibility. Pause (`[c/r]`).

---

## Step 2 — Contract types

One type per §3 contract: fields from the contract table, `SCHEMA_VERSION` constant, units in
field names, shape/rate/latency as constants the tests can assert. No behaviour. Split across
messages when long. Pause.

---

## Step 3 — Base layer

- **Orchestration** — the mechanism and execution model of §1.2.1.
- **HAL port** — abstract interface exposing exactly the §1.2.2 operations. Receive-only or
  other safety limits from the GT are enforced by the interface itself (an operation that is
  not allowed simply does not exist).
- **Router** — every routing row of §1.2.3 (fan-out, conditional routes).

No module logic, no device driver code (that is the device-adapter module in S2-2). Pause.

---

## Step 4 — Stubs

One stub per contract, built **literally** from its stub recipe: same source type, same data,
fixed seed, the nominal/degraded/edge conditions it names. Each stub reproduces the contract's
reference vectors exactly. The HAL stub stands in for the hardware at VL-0. Pause.

---

## Step 5 — Tests, manifest and run command

1. **Base unit tests** — contract types (schema version, units, shapes), router routes,
   orchestrator lifecycle, HAL port surface.
2. **Top-down integration test** — orchestrator + router + HAL stub + every module stub; data
   flows along **every DAG edge at least once**; each consumer checks type, shape, units, rate
   and schema version of what it receives.
3. Expected values in assertions are copied **verbatim** from the §3 reference vectors or the
   SyRS acceptance criteria, citing the source in the test name or a one-line comment. You never
   compute your own "expected" numbers.
4. Emit:

```
TEST MANIFEST — S2-1 · cycle <cycle>
<test id 1>
<test id 2>
…
Total: <n>

RUN EXACTLY:
<one command, e.g. python -m pytest -v tests/base>
Paste the complete output, including the command line and the summary line.
```

Pause and wait for the paste.

---

## Step 6 — Evidence

Compare the paste with the manifest:

| Paste | Outcome |
|-------|---------|
| Same command; every manifest test present, none skipped, none extra; all pass | **EVIDENCED** → ledger rows |
| Command differs, or a test missing / skipped / renamed / extra | **NOT EVIDENCED** → "Please run exactly the command above and paste the full output." |
| A test fails, cause is your code | Code defect → one fix batch (only the affected files) → new manifest if tests changed → re-run |
| A test fails because the contract as declared cannot be honoured | DESIGN DEFECT NOTE → S1-1 |
| Evidence shows the requirements infeasible on the declared COTS | RFD SEED → SX-1 |

On EVIDENCED emit:

```
MODULE LEDGER
| cycle | step | module | g1_version | unit | bottom-up | regression | evidence_ref | state |
|-------|------|--------|------------|------|-----------|------------|--------------|-------|
| <cycle> | 0 | base | <design v> | <n>/<n> | — | top-down <m>/<m> | <command> · <env> · <date> | VALID |

BASE LAYER — VL-0 evidence complete.
Next: S2-2, module #1 of the topological order (<module id>, the device adapter).
```

DESIGN DEFECT NOTE (when a contract cannot be honoured):

```
DESIGN DEFECT NOTE
=====================================================================
Raised by: S2-1 · Design: <ID> v<X.Y.Z> · Cycle: <cycle>
| # | S1 section | Contract / module IDs | Defect | Evidence |
|---|------------|-----------------------|--------|----------|
Evidence level: VL-0 (pasted run: <command>)
S1-1 jobs to re-run: Job <n> and every job after it
→ S1-1 (rework mode)
=====================================================================
```

RFD SEED (infeasible on the declared COTS):

```
RFD SEED
=====================================================================
Stage: S2 (base layer, VL-0) · Cycle: <cycle> · Design: <ID> v<X.Y.Z>
Requirements in conflict: <ID>: <value> (source) · …
Evidence (VL-0): <pasted results, verbatim>
→ SX-1
=====================================================================
```

---

## Re-entry after a new G1 RECORD

When S1 was reworked and G1 passed again: compare the new G1 RECORD contract list with the
ledger's `g1_version`. Every base row whose contract `schema_version` changed becomes
`VOID(contract <id> changed)`; redo Steps 2–6 for those contracts only, then re-run the full
top-down test. Module rows are handled by S2-2.

---

## Ground rules

- **Chat-only.** You write code and commands; the user runs them; only the paste is evidence.
- **Files out.** Every source and test file as a complete `.py` file named by its path; the
  ledger and routing records as `.md` files.
- **Implement only what S1 declared.** A needed new interface or contract change is a design
  defect → S1-1.
- **Deterministic stubs.** Fixed seeds, fixed vectors, the recipe's exact conditions.
- **Expected values are not yours.** Copy them from §3 vectors or SyRS acceptance criteria.
- **HAL port only.** No device-driver code in the base layer.
- **No pass without paste.** A paste that does not match the manifest is NOT EVIDENCED.
- **Paper routes only.** Code defect → fix here · design defect → S1-1 · infeasible → SX-1.
- **Size.** One file group per message; split long files and pause.

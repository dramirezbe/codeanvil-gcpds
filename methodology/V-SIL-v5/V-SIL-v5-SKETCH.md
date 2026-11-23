# V-SIL v5 — Design Sketch (handoff)

> Status: **concept only**. Nothing implemented. This document captures a working
> conversation so it can be continued in a more capable tool.
> Date: 2026-11-23. Baseline: CodeAnvil 0.10.0 / V-SIL v4.

## 0. Purpose of this document

v4 delivers a Verified Prototype on COTS hardware through the chain
`S0 → G0 → S1 → G1 → S2 → G2 → S3 → G3`. The sketch below proposes the v5
restructuring: **introduce a design-time feasibility world so hardware is
purchased only after the design has been falsified in simulation.**

This is a handoff brief, not a spec. Read it top to bottom; the open questions
in §6 are where the real work starts.

---

## 1. The driving problem

The current world is cut into **two dimensions**:

1. **Idea → Build Package** — conceptual/theoretical refinement of a client's idea
   into a contract: requirement refinement, QA, lab procedures, calibration, specs.
   Output ≈ PRD + procedures + hardware constraints (HWC). This is *delivered to*
   CodeAnvil; it is human conceptual work, genuinely upstream of this repo.
2. **Build Package → Verified Prototype** — software architecture design,
   calibration, lab procedures, implementation, and verification along
   `MIL → SIL → PIL → HIL`. This is what this repo attacks today.

**Symptom of a leaky cut:** *calibration* and *lab procedures* appear in BOTH
dimensions. That duplication is the tell that dimension 1|2 is not cleanly
separated.

**Economic driver:** we want to spend money on hardware **only after the design
has survived everything that can be falsified without it.** Today nothing in the
left arm of the V verifies the design before implementation begins.

---

## 2. The proposal: split into three worlds

Insert an intermediate world and align each world by **the kind of truth it
establishes** (not by phase):

| World | From → To | Truth by | Frozen deliverable |
|-------|-----------|----------|--------------------|
| **1 · Specification** | Idea → Build Package | stakeholder agreement (requirements) | the contract (GT: StRS + SyRS / PRD + proc + HWC) |
| **2 · Feasibility** | Build Package → **Validated Design** | physics / mathematics (pre-calculation + digital twin = MIL) | a *proven design* — **no product code, no target** |
| **3 · Realization** | Validated Design → Verified Prototype | execution on hardware (SIL → PIL → HIL) | the prototype |

The flow changes from `1 → 2` to:

```
1 (Specification)
  → 2 (COTS-HW simulation & validation — digital twins / MIL)
    → 3 (realization: SIL → PIL → HIL)
```

---

## 3. Why the cut falls on the MIL | SIL seam (not arbitrarily)

The intermediate world is **not a third symmetric world**. It is the recognition
that the already-adopted ladder `MIL → SIL → PIL → HIL` has a natural fracture:

- **MIL** = pure model. No product software, no target. Question: *can this even work?*
- **SIL → PIL → HIL** = real artifacts converging on hardware. Question: *did we build it right?*

The ladder itself locates the boundary. World 2 ends where MIL ends; world 3 is
SIL onward. The digital twin **is** the MIL rung.

### Two design-time verification mechanisms inside world 2
- **Pre-calculation (analytical)** — a deterministic check (sibling of
  `g0_validate.py`) that takes the HW budgets + the SyRS uncertainty budget and
  decides **analytical feasibility per `SYS-`**: closed-form PASS/FAIL. Answers
  *can the declared COTS HW even meet the contract?* before a line of code.
- **Digital twin (simulation)** — a synthetic data generator (signal model +
  impairment model) that feeds the designed correction chain and confirms the
  budget **numerically**. Reuses the existing Mock HAL + golden-vector
  infrastructure from S3, **elevated** from "test fixture" to "design proof".

---

## 4. What the feasibility world buys — and what it does NOT

The honest value proposition. "Totally sure" is a trap; do not build the
methodology around certainty.

**World 2 kills the expensive mistakes before any purchase:**
- Uncertainty budget does not close **even with perfect HW** → design infeasible.
- Algorithm / correction chain cannot hit the `SYS-` target even with ideal hardware.
- Architecture is wrong (signal-chain topology, stage ordering).

If MIL fails on any of these, buying hardware would have been pure waste.

**World 2 cannot rule out (irreducible residual risk — this is what HIL buys down):**
- Datasheet is optimistic or wrong.
- EMI, thermal in the real enclosure, timing on the real target.
- Integration surprises.

**The decision rule it gives (the valuable one):**

> Buy hardware only for designs that survived MIL. **MIL is the gate that
> protects the purchase order.** It converts "buy and hope" into "buy to confirm."

Reframe the pitch as *"you spend on hardware only once you have falsified
everything falsifiable without it"* — not *"it guarantees the design works."*
The first is true and powerful; the second explodes the day a datasheet lies.

**Critical dependency:** the gate is only as good as the twin's HW model. A garbage
model yields a false green and you buy anyway. The twin's HW model **must be
anchored in the real `HWC-` constraints from the StRS** (verifiable datasheet
values, not invented numbers). This closes the loop back to world 1: world 1 must
deliver solid HW specs, or world 2 lies with confidence.

---

## 5. Pitfalls to avoid (do not oversell the split)

1. **Value is 100% in the interface, not the number of boxes.** The split only
   pays if world 2 produces a **frozen deliverable** ("Validated Design":
   budgets + digital-twin evidence) that world 3 consumes as an **immutable
   input**, exactly as the Build Package freezes world 1. A middle world that is
   "just another phase" with no freeze adds a sync/drift surface and buys nothing.
   (v4 already carries delta-sync / staleness machinery in `reports.py` precisely
   because every boundary is a drift surface — do not add one carelessly.)
2. **A new world is not a new repo/team.** World 1 is genuinely external (human
   conceptual work delivered in). Worlds 2 and 3 are both "Build Package →
   Prototype" and should live in the **same repo/tool** as two gated phases with a
   hard freeze between them. The honest framing is **"1 external world + 2 internal
   gated phases with a freeze,"** not "3 symmetric worlds."
3. **RFD relocates.** "Requirements infeasible on the declared COTS platform"
   becomes the **natural exit of world 2**, not an ad-hoc deviation raised anywhere
   in the chain.
4. **Disambiguate calibration (fixes the §1 leak):** calibration *spec* → world 1;
   calibration *model* (does the correction chain close the budget in simulation?)
   → world 2; calibration *execution* (real measurement on HW) → world 3. The
   digital twin forces this separation.

---

## 6. Mapping onto the existing v4 chain (reassurance: it's a re-grouping, not a rewrite)

Rough placement — to be refined:

```
WORLD 2 (feasibility)                 WORLD 3 (realization)
S0 → G0 → S1 → G1 → [NEW design-     | S2 → G2 → S3 → G3
                     verification gate = |
                     MIL / digital twin;  |
                     terminal gate of     |
                     world 2]             |
                                          ^
                                   HARD FREEZE: "Validated Design"
```

- World 2 ≈ `S0 .. (S1 + a new design-verification gate)`.
- World 3 ≈ `S2 .. G3`, entered only on a world-2 PASS.
- The digital twin is the **terminal gate of world 2**.
- Pre-calculation and twin scripts run on the methodology runtime via
  `codeanvil python`, like G0.
- This is methodology (`templates/`) work, not `src/` tooling.

---

## 7. Open questions (start here in the next tool)

1. **Is the pre-calculation a deterministic gate (like G0) or part of the human
   G1 judgment?** This is the single most important design decision.
2. **What exactly is in the "Validated Design" frozen deliverable**, and what is its
   custody/digest contract so world 3 can treat it as immutable?
3. **Concrete HITL notation** — adopt `MIL → SIL → PIL → HIL` as the formal
   verification-level ladder; pin down where each rung sits on the V and how it
   maps to the existing VL-0 / VL-1 / VL-2 / HIL-1 / HIL-2 levels.
4. **How is the methodology made visible inside the implementation** — per-module
   traceability header linking `SYS-` → budget line → the MIL/SIL/HIL level that
   verified it ("mostrar la metodología dentro de la implementación").
5. **HW budget as data, not prose** — parameter files (`.yaml`/`.toml`) +
   derived calculations so the design is "easily editable": energy, attenuation,
   thermal, noise, vendor lock-in as a trade-study axis, limitations/mitigations
   table, measurement conditions.

---

## 8. Scope guardrail (from the week's tasking)

- **No commercial agents.** Concept only; zero commercial tooling.
- v5 is a **methodology** restructuring. Per v4 precedent there is no migration
  command: v5 would need a fresh scaffold/cycle; archived v4 evidence is not
  reclassified as a v5 verdict.

# Failure Triage and Draft Mode — requirements stages (S0 · G0 · G1)

This reference is shared, verbatim, by the S0, G0 and G1 skills. It defines how a
failure is handled in the requirements stages so the human corrects it fast, and how the
fast draft loop works. It changes nothing in S2 or G2.

## 1. Failure triage

Every machine or gate failure in the requirements stages is **translated for the human
before anything else** — never dumped as a raw error. The agent explains the real problem
in plain language and proposes concrete reconciliations; the human chooses; the agent
applies. The agent is the interpreter, never the oracle.

### When it fires

| Stage | Trigger |
|-------|---------|
| G0 | Every ERROR the validator prints (exit `1`), and every entry on S0's missing list. |
| G1 | Every `open` finding. |
| S0 (re-entry) | Every G0 feedback reason being mapped back to the Build Package. |

### For each failure item, present exactly three parts

1. **The real problem** — plain language, no standard/clause jargon. State what is broken
   and *why it matters*: what can no longer be trusted, verified or built because of it.
   One or two sentences. Do not quote the IEEE field name as the explanation.
2. **Reconciliation options** — two to four concrete options, each with its consequence.
   Most Ground-Truth failures fit one of these shapes:
   - **Connect** — the item exists but is unlinked → add the trace/field to an existing block.
   - **Create upstream** — the item is real but has no origin → add the missing block that
     justifies it.
   - **Remove / relax** — the item is not needed, or two items conflict → delete it, or relax
     the bound.
   Name the concrete edit each option makes (file · block · field), not an abstract idea.
3. **Ask which** — one question, the options as choices, free text allowed. Never pick for
   the human, and never invent content a source does not supply (S0's invent-nothing rule
   still holds: an option that needs new content asks the human for it).

### After the choice

Apply the chosen edit to its real owner — the GT block, or the Build Package line when the
Build Package is the source — then re-run the check. In draft mode, loop without writing a
report iteration. In a recorded run, summarise the applied fixes in the iteration's
Description.

### The hard line (P2, P3)

The agent may rank options and recommend one, but the **verdict is never the agent's**: G0
passes only on the validator's exit `0`, Gate H and G1 only on the human's answer. A
plain-language explanation never downgrades, hides or pre-approves an ERROR. The deterministic
validator stays the oracle; this triage only makes its output legible.

## 2. Draft mode — the fast requirements loop

Draft mode lets the human iterate on the Ground Truth (and, at G1, on the open findings)
without the per-edit ceremony: **no report iteration per change, no staleness or digest guard
between edits.** It is scoped to S0, G0 and G1 only; S2 and G2 never run in draft.

### Marker

Draft mode is on for a cycle while the file `.codeanvil/report/<cycle-name>/DRAFT` exists.
It has **no `.md` extension on purpose**, so `codeanvil status` (which reads `*.md` gate
reports) never treats it as a gate. Any requirements-stage skill may offer to enter draft on
the first failure — *"Iterate in draft until green?"* — and on a yes writes the marker with
one line: `Draft opened: <codeanvil now> by <name>`. The human may also ask for it directly.

### While the marker exists

- Run the gate's check on the **current files**: G0 runs the validator on the GT pair as it
  stands; G1 re-derives its findings. Do **not** require the predecessor's recorded PASS — the
  human is editing live, and there are no recorded iterations to be stale against.
- Run the triage above on every failure item, apply the chosen fixes, re-run. Loop.
- Write **no** report iteration. The report stays clean of the intermediate red runs.

### Closing draft (commit)

When the human asks to commit — or when the check is green and the human accepts — **remove
the marker** and run the gate once in the normal recorded way: S0 re-normalises (or accepts
the hand-written pair), G0 writes the one passing iteration plus Gate H, G1 writes its
reviewed iteration. The audit trail records the run that passes, not the path to it.

### Direct GT edits and the Build Package

In draft the human may edit `.codeanvil/GT/StRS.md` / `SyRS.md` directly. That makes the GT
diverge from `.codeanvil/GT/build_package.md`. On commit, that divergence is itself a triage
item, with these options:

- **Regenerate** — rebuild the Build Package narrative from the edited GT.
- **Accept the pair** — keep the GT as a hand-authored input (S0's *"pair supplied as
  normalised input"* path); the Build Package digest for the cycle becomes `none`.
- **Discard** — drop the draft GT edits and re-normalise from the Build Package.

The human chooses; nothing is silently reconciled.

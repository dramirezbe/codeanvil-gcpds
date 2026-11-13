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
   - **Look it up** — when the missing item is a documentary fact that exists in the world (a
     standard clause, a datasheet section or value, a citation) **and the runtime has web access**,
     offer to search the web for it and propose the found value **with its source URL** as a
     candidate. The human confirms before it enters the GT — invent-nothing still holds: a web
     result is a proposal to approve, never an auto-fill, and its source is recorded in the block.
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

### Lead with meaning, never codes

The reader must never have to open a document to learn what an item is about. Describe every
requirement, constraint or obligation by **what it asks or limits, in plain words, first**, and put
its ID in parentheses as a reference only. This holds for the problem statement, every option and
every question — a bare ID with no plain-language description is never acceptable anywhere.

- Not: `NRM-RF-002 has no clause.`
- But: `The rule that the receiver must stay within the HackRF's 1 MHz – 6 GHz tuning range cites the
  datasheet but names no section, so the number cannot be checked against the source (NRM-RF-002).`

When an item links two blocks (a dependency, a trace), name both in plain words, not just the codes:
not `R2 depends on H9`, but `the live-parameter-control requirement depends on a hardware limit that
is not in the table (STK-CTRL-001 → H9)`.

## 2. Draft mode — the fast requirements loop

Draft mode lets the human resolve every open item on the Ground Truth (and, at G1, every open
finding) without the per-edit ceremony: **no report iteration per change, no staleness or digest
guard between edits.** It is scoped to S0, G0 and G1 only; S2 and G2 never run in draft.

### Draft is entered automatically, and is mandatory while items are open

Draft mode is **not optional**. A requirements-stage skill enters it **automatically** the moment
it finds **unresolved items** — any missing-list entry, any format ERROR (G0 exit `1`), or any G1
`open` finding. The skill writes the marker itself; it never asks permission to enter and never
skips straight to a verdict while items are open.

The marker is the file `.codeanvil/report/<cycle-name>/DRAFT`. It has **no `.md` extension on
purpose**, so `codeanvil status` (which reads `*.md` gate reports) never treats it as a gate. The
skill writes it with one line — `Draft opened: <codeanvil now> by <name>` — as soon as it finds an
open item; the human may also create it to iterate deliberately. It is removed only on commit, once
every item has an explicit decision.

### Classify each item: auto-apply or ask

Not every item carries a judgment. Before asking the human anything, sort the items:

- **Auto-apply — do not ask.** Mechanical fixes with one correct resolution that invents nothing:
  - removing blueprint scaffolding the GT should never have carried (an example block, an empty
    `_TERM_` placeholder row, a boilerplate sentence, a template `[TYPE]-[SUB]-[NNN]` row);
  - filling a value stated elsewhere in the GT or the Build Package (a manufacturer named in the
    part, a purpose that restates the existing scope, an overview from the existing headings);
  - removing a broken reference (a dependency on a block that does not exist);
  - linking an obligation to the system block that already realizes it, where the mapping is
    unambiguous.
  Apply these and list them in the iteration as **auto-applied** (what changed and why). Show the
  human the batch so they can **override** any of them, but do **not** ask one question each.

- **Ask — per-item decision.** Anything that carries a trade-off or author authority:
  - dropping or weakening a requirement (marking something out of scope, relaxing a bound);
  - inventing content not derivable from the sources (an acceptance threshold with a real choice);
  - an external fact (a web look-up citation — the human confirms the source);
  - a lifecycle choice (the document status).

When in doubt, **ask** — auto-apply only what is clearly mechanical and invents nothing.

### Decide every ask-tier item before advancing

**No gate advances with an open item left unresolved.** Every item is either **auto-applied and
reported** (above) or carries an **explicit human decision**; the stage must not record a Gate H /
G1 PASS, nor move on, while an ask-tier item is undecided. For each ask-tier item the human chooses
exactly one:

- **Fix** — edit the GT (or the Build Package) to supply what is missing, then re-run the check.
  When the missing value is a documentary fact (a clause, a datasheet number, a citation) and the
  runtime has web access, this may include **looking it up on the web** and proposing the found
  value with its source for the human to confirm before it enters the GT.
- **Ignore / accept** — the gap or finding is acceptable as it stands. This is a real decision: it
  is recorded in the iteration with the decider's name, never a silent skip and never the agent's
  default.
- **Escalate (RFD)** — the item shows the requirements are infeasible on the declared COTS
  platform; raise an RFD.

The agent presents each ask-tier item through the triage of §1, proposes options, and records the
human's choice. It never resolves, defaults or bulk-accepts an **ask-tier** item on its own — a
single blanket PASS over open items is not a decision. (It may, and should, auto-apply the mechanical
tier above without asking, as long as it reports each one.)

**One asymmetry.** A content gap (a missing-list entry at exit `0`) can be *fixed* or *ignored*,
because the document is already structurally valid. A format ERROR (exit `1`) can be *fixed* or
*escalated*, but it cannot be *ignored* into a PASS: the deterministic validator keeps returning
`1` until the structure is corrected (P3). So "ignore" applies to content gaps, not to format errors.

### While the marker exists

- Run the gate's check on the **current files**: G0 runs the validator on the GT pair as it
  stands; G1 re-derives its findings. Do **not** require the predecessor's recorded PASS — the
  human is editing live, and there are no recorded iterations to be stale against.
- Run the triage above on every failure item, apply the chosen fixes, re-run. Loop.
- Write **no** report iteration. The report stays clean of the intermediate red runs.

### Closing draft (commit)

Draft closes only when **every item is resolved** — auto-applied and reported, or given an explicit
decision (fix, ignore/accept, or escalate) — not merely when the human asks. Then **remove the
marker** and run the gate once in the
normal recorded way: S0 re-normalises (or accepts the hand-written pair), G0 writes the one passing
iteration plus Gate H, G1 writes its reviewed iteration. The recorded iteration **lists each item
and the decision it received**, so the audit trail shows what was fixed and what was knowingly
accepted — the run that passes, not the path to it.

### Direct GT edits and the Build Package

In draft the human may edit `.codeanvil/GT/StRS.md` / `SyRS.md` directly. That makes the GT
diverge from `.codeanvil/GT/build_package.md`. On commit, that divergence is itself a triage
item, with these options:

- **Regenerate** — rebuild the Build Package narrative from the edited GT.
- **Accept the pair** — keep the GT as a hand-authored input (S0's *"pair supplied as
  normalised input"* path); the Build Package digest for the cycle becomes `none`.
- **Discard** — drop the draft GT edits and re-normalise from the Build Package.

The human chooses; nothing is silently reconciled.

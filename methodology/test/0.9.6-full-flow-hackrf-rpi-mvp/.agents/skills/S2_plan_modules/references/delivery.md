# S2 delivery and recovery

## Interpret preparation correctly

| Result | Action |
|---|---|
| Backup exits 0: nothing to back up | First delivery has no prior files. Create the scoped plans now. |
| Backup exits 0: already backed up | Preserve that baseline and resume the interrupted work. |
| Backup exits nonzero | Show the failed command/error; stop without a delivered iteration. |
| Classifier prints Kahn rows | Use them to write BACKLOG.md; no plan was written by the script. |
| Plans directory or first-run artifacts absent | Create them; they are S2 outputs. |
| Actual upstream requirement/contract conflict | Complete unaffected work, identify the exact conflict and use the existing design/GT rework route. |
| User explicitly stops or runtime is interrupted | Preserve drafts; report the actual boundary without inventing PASS. |

Do not end with a preparation-only summary while an authorized next action remains. A continue,
run, yes, y or ok reply resumes only an already presented scope, case-insensitively; respect
negations and conditions. Such a reply never means G2 PASS or permission to implement code.

## Close the scoped delivery

1. Preserve the active cycle and passed G1 baseline. Reuse an already successful backup.
2. Create only the admitted scope's artifacts. Slice 0 needs populated BACKLOG.md,
   INFRA-PLAN.md and an empty locked DELTAS.md table. Module slices need one PLAN.md per
   admitted module; system needs INTEGRATION-PLAN.md after the required module-slice verdicts.
3. Use the locked references and copy the required contracts/criteria from SDD/SyRS. For slice 0,
   specify concrete base/kit/stub paths, ordered creation tasks, runner command and expected exit,
   logs/telemetry paths, and the exact placeholder handshake fixture or deterministic generation
   recipe with expected receiver output. Do not abbreviate required arrays or refer vaguely to
   a contract. The fresh implementor must have the exact context and expected outcomes. Keep
   the slice-0 startup/handshake floor separate from final module and PATH acceptance.
4. Check Markdown tables have the declared columns and all Kahn module rows. Retain IDs,
   dependencies, required VL and state from the design/evidence; never mark future work verified.
5. Run `codeanvil custody digest` for SDD, SyRS and every plan written. Copy complete Input lines
   for both required inputs and Output lines for the plans. Change only the prefix for outputs;
   never reconstruct, shorten, combine or hand-compute the digest.
6. Append S2's complete iteration with current G1 Based on, admitted Scope, backup result, tasks,
   risks, outputs and any rework source. PASS means plans delivered, not code or gate approval.
7. Run `codeanvil custody verify --cycle <cycle> --gate S2` and `codeanvil status`. A malformed
   line or absent required input is `invalid-report`, not an ignored optional field. Fix the
   delivery before handing off to G2. Historical G2 staleness does not require altering history.
8. Return scope, plan paths, risks and iteration; hand off to G2 without assuming its verdict.

## Correct an existing report

Read the current report, admitted scope, plans and latest G2 feedback. Preserve all existing
report bytes and take the normal backup before overwriting artifacts. Fix the requested plan
defects within scope; obtain fresh custody lines and append the next complete S2 iteration.
For a metadata-only correction, explicitly state which digests were wrong and that plan content
and unresolved G2 findings are unchanged. Do not reset or delete G2, invent a human answer, or
claim that valid custody proves plan quality. G2 must review the new delivery and resolve its
remaining findings before implementation.

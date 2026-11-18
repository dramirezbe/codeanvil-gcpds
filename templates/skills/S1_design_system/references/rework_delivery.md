# Deliver S1 and reopen G1

Use this procedure for first delivery, interrupted work and bounded rework. Keep authorization
for the requested work active until delivery, a required human choice, an explicit stop or an
evidenced operational/runtime blocker. Finishing edits without the report is unfinished work.

## Baseline and feedback source

S1's upstream prerequisite is the current, passed G0. G1 consumes S1; it is never its upstream
prerequisite, even when G1 requested the rework. Record these separate lines:

```text
Based on: G0 iteration 1
Rework from: G1 iteration 1
Scope: system
```

Use the actual iteration numbers. For another feedback source, name that gate in `Rework from`.
For direct user rework, record the request in prose. This field is provenance, not a freshness
dependency. An old G1 whose input was replaced remains stale until a new review is recorded.

| Condition | Action |
|---|---|
| G0 missing, not PASS or stale; cycle closed; active RFD | Follow the skill's existing prerequisite/RFD boundary. |
| S1 edits exist but no matching delivery report | Resume the missing edits/checks/report; do not send G1 an unrecorded design. |
| G1 FEEDBACK reviews the latest S1 | Complete the requested S1 rework. |
| New valid S1 delivery after the old G1 FEEDBACK | Hand off to G1; old G1 staleness is expected. |
| S1 says `Based on: G1 ...` | Follow corrective delivery below; never delete G1 to break the loop. |

## Close the delivery

1. Confirm the G0 baseline and input custody. Keep the successful pre-edit backup as the old
   baseline; do not back up repeatedly merely because the same work resumed.
2. Complete the requested SDD changes and trace their impact across Meta, runnable command,
   module cards, HAL ladder, telemetry, DAG, runtime graph, contracts and PATHs. Retain stable IDs.
   In `mock-only`, every module has `hw_dependency: false`, no module/path requires VL-2 or a real
   driver, and no hardware enrollment or deployment is needed this cycle. COTS inventory can
   remain future context without active hardware edges or Real HW HAL requirements. Check the
   cards themselves, including Responsibility; a corrected summary alone is insufficient.
   For a listener/origin change, reconcile the root command, client URL, configuration, HTTP
   handling, WebSocket Origin handling and allowed/rejected-origin test recipes.
3. Update both graph DATA blocks from the final design. Equal topology does not mean equal
   profiles: synchronize module levels, hardware edges and labels too. Only theme may differ.
4. Reread the skill's design checks. Write the design change set and downstream impact map for
   rework. Preserve unresolved risks; never widen GT to make the design pass.
5. Obtain final digests only through `codeanvil custody digest`. Append a complete S1 iteration
   with the G0 baseline, separate feedback source, consumed GT Input lines, final SDD Output
   line, backup result and both graph paths. PASS means delivery, not human design approval.
6. Run `codeanvil custody verify --cycle <cycle> --gate S1` and `codeanvil status`. The verifier
   checks the latest recorded S1 outputs as well as inputs. A changed/missing output is
   `undelivered-output`; an incorrect upstream gate is `invalid-baseline`. Diagnose and finish
   the delivery; do not ignore a failure or fabricate a clean result. Historical G1 input
   mismatches are retained and do not require undoing the new S1 design.
7. Return the four artifact paths, iteration and G1 handoff. Do not stop between edits and the
   report while an authorized next action remains. Do not assume G1's human verdict.

## Correct a historical S1 baseline without changing history

Read the latest S1, the actual G0 and the feedback that requested the correction. Verify the
G0 inputs and current artifacts, preserve the existing report bytes and use the normal backup
before any artifact overwrite. Complete any outstanding design or graph fixes. Append the next
S1 iteration with `Based on: G0 iteration N`, `Rework from: G1 iteration M`, current digests and
a change-set entry explaining the metadata correction. If artifacts are already complete,
state that their content is unchanged and cite the previous delivery. Then verify custody and
status. Do not relabel the old iteration, delete feedback, enroll hardware or invent approval.

## G1 review boundary

For a recorded review, require the latest complete S1 with a valid G0 baseline and a matching
SDD Output digest. A newer S1 permits a new G1 review even when the previous G1 is FEEDBACK or
stale. It does not imply the feedback was resolved: review the change set and all findings.
If the feedback still names the current S1, rework has not been delivered yet. RFD is never
cleared by a newer delivery alone. Draft analysis may inspect current working files, but a
recorded verdict still requires delivery integrity and the human's explicit answer.

“Accept the prototype at VL-0/VL-1” sets the requested verification scope. It is not a G1 PASS,
test evidence or a system G3 PASS. Only system G3 PASS produces the Verified Prototype.

# Plan — G0: structural validation + Gate H (small edit)

Feature: `odd/tasks/2026-11-04_1042_vsil_v3_skill_flow.md` · Task T5 · Specs S1, S2, S3, S7 · Contracts C0, C1, C2
Target: `templates/skills/G0_valid_req_and_GT/SKILL.md` (edit, version `3.0` → `3.1`). Paper §4.

G0 is already what the paper asks for: deterministic, stdlib-only and a binary verdict. It validates what S0 normalised and is **the only deterministic gate in the flow (S7)**; Gate H right after it is human. **`g0_validate.py` and `RULES.md` do not change.** Only the agent contract does.

## Edits

| Section | Change |
|---------|--------|
| `## Prerequisite and Cycle` | Replace "no prerequisite / entry point" with the C2 check on `S0.md`: `S0 must pass first. Run the S0 skill.` On G0's own unreworked FEEDBACK: `S0 must rework first. Run the S0 skill.` |
| `## Decision Gates`, exit `0` | Ask the paper's Gate H question verbatim: *Requirements complete, bounded, and verifiable?* Answer `PASS` or `FEEDBACK`. |
| `## Decision Gates`, FEEDBACK | Reasons are collected one per line, each starting with the block ID it concerns, and written verbatim. The route back is S0. Never suggest or complete a reason (L13 of the chat-only feature). |
| `## Execution Steps` | New step on PASS: record Gate H date and authoriser in the Description. |
| `## Report Contract` | Description starts with `Based on: S0 iteration <N>` (C11) and also carries `Gate H` on PASS. |
| `## Activation Contract` | "Do not load" text says later stages are S1 and G1, not "later gates". |
| Hard rule on editing GT | Point fixes back to S0 instead of editing GT inside G0. |

Exit `1` keeps forcing `HITL: FEEDBACK` (P3). Exit `2` keeps writing no iteration.

## RED tests first

`tests/test_create.py::test_g0_skill_writes_an_iterative_report` changes in the same commit as T6, because it asserts `"no prerequisite"` today:

- asserts `S0 must pass first. Run the S0 skill.`;
- asserts `Requirements complete, bounded, and verifiable?`;
- asserts `S0 must rework first. Run the S0 skill.` and `Based on: S0 iteration`.

Previous behaviour stays pinned: `templates/tests/test_g0_validate.py` must pass unchanged.

## Acceptance

1. Exit 0 plus PASS writes a G0 iteration with Gate H recorded; `codeanvil status` shows `G0: PASS`.
2. Exit 1 writes `HITL: FEEDBACK` with the full script report and no question to the human.

## Blueprint text

`templates/GT/G0_StRS.md:32` and `templates/GT/G0_SyRS.md:32` list the companion row `SRS-… | Software design output (G1)`. Change it to the S1 design document: `S1 design … | Software design output (S1)`. `g0_validate.py` has no SRS or companion rule (grep confirmed), so validation is not affected.

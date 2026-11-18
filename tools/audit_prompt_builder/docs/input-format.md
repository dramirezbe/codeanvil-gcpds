# Audit profile JSON format

Start from [templates/default.json](../templates/default.json). Missing fields use
its defaults; list fields replace the whole default list. Keys beginning with `$`
are comments ignored by the loader. Both current profiles include every field.

| Field                 | Type                  | Allowed values / meaning                                                       |
|-----------------------|-----------------------|--------------------------------------------------------------------------------|
| `mode`                | string                | `"Focused"` (default) or `"Detailed"`; Detailed enables extra analysis; both modes return the same compact results |
| `context.title`       | string                | Short name of the idea or project                                              |
| `context.domain`      | string                | Subject area, e.g. `"Methodology and philosophy"`                              |
| `context.problem`     | string                | What goes wrong today, and for whom                                            |
| `context.idea`        | string                | What the review should establish or improve                             |
| `context.constraints` | string                | Applicable principles, requirements, authority, and scope                      |
| `context.assumptions` | string                | Beliefs not yet proven                                                         |
| `context.prior`       | string                | Known prior work and past attempts                                             |
| `stages.<name>`       | `true` / `false`      | `Decomposition`, `Novelty and prior-art check`, `Gap matrix`, `Matrix scoring`, `Failure-mode analysis`, `Recommendation` |
| `scale`               | number                | `3`, `4`, `5` or `10` (top score)                                              |
| `dimensions`          | list of objects       | **Replaces** the whole default list when present                               |
| `dimensions[].name`   | string                | Blank names are left out of the prompt                                         |
| `dimensions[].weight` | number                | `0`–`10`; `0` excludes the dimension from the final percentage                          |
| `dimensions[].definition`, `.low`, `.mid`, `.high` | string | The question it answers and its three anchors; define anchors consistent with the chosen scale |
| `audit.enabled`       | `true` / `false`      | Include the document audit section                                             |
| `audit.checks`        | list of strings       | One audit rule per item; replaces the default list                             |
| `audit.documents`     | string                | Documents to audit, labelled, e.g. `"[SPEC v2.1] ...\n[TEST PLAN r3] ..."`     |
| `rules.two_pass`      | `true` / `false`      | Optional second scoring self-check in Detailed mode                             |
| `rules.evidence`      | `true` / `false`      | Legacy value retained on export; current results always require evidence |
| `rules.disagree`      | string                | Legacy value retained on export: `"report both values and flag for human arbitration"`, `"use the lower score and note the gap"`, `"use the average and report the spread"` |
| `output.format`       | string                | `"Markdown"` or `"JSON"`                                                       |
| `output.language`     | string                | Language of the model's answer                                                 |
| `output.max_words` | positive integer | Target response length; default `350` |
| `output.max_findings` | positive integer | Target findings; default `5`; all critical findings still appear |

Unknown fields, wrong types and values outside the allowed lists are rejected
with a message naming the field (e.g. `scale must be one of: 3, 4, 5, 10.`).

## Result contract

With scoring enabled, output contains only the final percentage, a compact matrix
(dimension, score, weight, brief basis), and findings with evidence and a short
correction. With scoring disabled, only findings and corrections are requested.
Missing evidence yields N/A, excluded from the weighted denominator. If there are
no assessed dimensions with positive weight, the final score is N/A. Coverage
limitations belong on the final score line, not in an extra section.

Markdown and JSON follow the same contract. Scored JSON contains only
`final_score` (object with `percent` or null and `coverage`), `matrix_summary`
(array of objects with `dimension`, `score` or null, `weight`, `basis`), and
`findings` (array of objects with `severity`, `location`, `evidence`, `correction`).
Unscored JSON contains only `findings`.

## Existing profiles

Older JSON remains loadable through upload or by placing it in `profiles/`.
Missing output limits use 350 words and five findings. The original V-SIL v3
paper input is preserved under `archive/profiles/` and is excluded from the picker.
Exporting current inputs includes the new settings, even for a legacy input.

To prepare a profile with an agent, ask it to read this reference and the default
JSON, fill the context, applicable criteria and scoring dimensions, and label the
source texts in `audit.documents`. Keep requirements grounded in the source.
Validate the resulting file with `python -m json.tool profiles/<name>.json`, then
load it in the app for field validation and preview.

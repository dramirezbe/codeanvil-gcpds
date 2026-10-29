# tools/

Standalone helpers for working on CodeAnvil. They are not part of the `codeanvil` package.

## LLM Validation Prompt Builder

`audit_prompt_builder.py` is a Streamlit app that builds a structured review prompt
for an LLM: context, validation stages, a weighted scoring matrix, an optional
document audit, and an output format. You fill it in by hand, by loading a JSON
inputs file (which an agent can write), or both.

| Path                          | What it is                                                       |
|-------------------------------|------------------------------------------------------------------|
| `audit_prompt_builder.py`     | The app                                                          |
| `prompt_inputs.template.json` | Inputs format **and** the app's default content                  |
| `inputs/`                     | Put filled inputs files here; the sidebar lists them             |
| `prompts/`                    | Prompts saved with the "Save prompt to tools/prompts" button     |
| `tools-reqs.txt`              | Python requirements (Streamlit)                                  |

### Setup

From the repo root:

```bash
cd tools
uv venv .venv
source .venv/bin/activate          # fish: source .venv/bin/activate.fish
uv pip install -r tools-reqs.txt
streamlit run audit_prompt_builder.py
```

It opens at http://localhost:8501. Without `uv`, use `python -m venv .venv` and
`pip install -r tools-reqs.txt`.

Optional: `uv pip install -e ..` makes saved-prompt filenames use CodeAnvil's own
timestamp helper (`codeanvil now --machine`). Without it, the app uses a built-in
timestamp in the same `YYYY-MM-DD_HH-MM-SS` format.

### Workflow

1. **Fill the inputs** — either:
   - by hand on the page, or
   - copy `prompt_inputs.template.json` to `inputs/<name>.json` and fill it
     (yourself or with an agent, see below).
2. **Load** — in the sidebar, pick the file under *From tools/inputs/* and click
   **Load selected file**, or upload any JSON file. A summary of errors is shown
   if the file is invalid, and nothing on the page changes.
3. **Adjust** — every field stays editable after loading.
4. **Export** — in section 6:
   - copy the prompt from the code box,
   - **Download prompt (.md)**,
   - **Save prompt to tools/prompts (.txt)** — writes
     `prompts/<title>_<timestamp>.txt` (title made filename-safe; `prompt_` when empty),
   - **Save my inputs (.json)** — downloads the current page in the template format,
     so it can be put back in `inputs/` and loaded again.

**Reset to template defaults** (sidebar) restores the template content.

### Inputs file format

`prompt_inputs.template.json` shows every field with its default value. A filled
file may be **partial**: missing fields keep the template value. Keys starting
with `$` (such as `$help`) are ignored.

| Field                 | Type                  | Allowed values / meaning                                                       |
|-----------------------|-----------------------|--------------------------------------------------------------------------------|
| `context.title`       | string                | Short name of the idea or project                                              |
| `context.domain`      | string                | Engineering field, e.g. `"RF hardware"`                                        |
| `context.problem`     | string                | What goes wrong today, and for whom                                            |
| `context.idea`        | string                | The proposal: components, interfaces, how it works                             |
| `context.constraints` | string                | Budget, schedule, power, size, regulation, team, hardware                      |
| `context.assumptions` | string                | Beliefs not yet proven                                                         |
| `context.prior`       | string                | Known prior work and past attempts                                             |
| `stages.<name>`       | `true` / `false`      | `Decomposition`, `Novelty and prior-art check`, `Gap matrix`, `Matrix scoring`, `Failure-mode analysis`, `Recommendation` |
| `scale`               | number                | `3`, `4`, `5` or `10` (top score)                                              |
| `dimensions`          | list of objects       | **Replaces** the whole default list when present                               |
| `dimensions[].name`   | string                | Blank names are left out of the prompt                                         |
| `dimensions[].weight` | number                | `0`–`10`; `0` keeps the dimension as information only                          |
| `dimensions[].definition`, `.low`, `.mid`, `.high` | string | The question it answers and its three anchors; empty anchors print as `n/a` |
| `audit.enabled`       | `true` / `false`      | Include the document audit section                                             |
| `audit.checks`        | list of strings       | One audit rule per item; replaces the default list                             |
| `audit.documents`     | string                | Documents to audit, labelled, e.g. `"[SPEC v2.1] ...\n[TEST PLAN r3] ..."`     |
| `rules.two_pass`      | `true` / `false`      | Ask for two independent scoring passes                                         |
| `rules.evidence`      | `true` / `false`      | Require evidence (or `ASSUMED`) for every score                                |
| `rules.disagree`      | string                | `"report both values and flag for human arbitration"`, `"use the lower score and note the gap"`, `"use the average and report the spread"` |
| `output.format`       | string                | `"Markdown"` or `"JSON"`                                                       |
| `output.language`     | string                | Language of the model's answer                                                 |

Unknown fields, wrong types and values outside the allowed lists are rejected
with a message naming the field (e.g. `scale must be one of: 3, 4, 5, 10.`).

Minimal example (`inputs/sdr_df.json`):

```json
{
  "context": {
    "title": "Low-cost SDR direction-finding array",
    "domain": "RF hardware",
    "problem": "Commercial DF systems cost more than the lab budget allows.",
    "idea": "Four coherent RTL-SDR receivers sharing one clock, MUSIC on a Raspberry Pi 5."
  },
  "audit": { "enabled": false }
}
```

### Letting an agent fill the inputs

Any coding agent that can read and write files works. Ask it something like:

> Read `tools/README.md` and `tools/prompt_inputs.template.json`. Using
> `<source files, e.g. GT/G0_StRS.md and GT/G0_SyRS.md>`, write
> `tools/inputs/<name>.json` in the template format. Fill `context`, and put the
> documents to audit in `audit.documents`. Keep the other fields unless I asked
> to change them. Do not invent facts: leave a field empty if the sources do not
> cover it. Validate the file with `python -m json.tool tools/inputs/<name>.json`.

Then load the file in the sidebar, review it on the page, and save the prompt.

### Changing the defaults

Edit `prompt_inputs.template.json`; the app reads its starting content from it.
The stage descriptions are prompt text and live in `STAGES` inside
`audit_prompt_builder.py`.

### Notes

- Uploading the **same** file twice in a row does not reload it (the uploader only
  reacts to a new file). Use the `inputs/` picker, or upload it again after removing it.
- Two prompts saved with the same title in the same second overwrite each other.
- Very long documents lower the model's accuracy; split them into sections.

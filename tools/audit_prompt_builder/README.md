# Audit prompt builder

Build a prompt whose response contains only a final score, a compact scoring
matrix, and findings with brief corrections. Defaults target 350 response words
and five findings; all critical findings must still be reported.

## Run

From the repository root:

```bash
uv venv tools/audit_prompt_builder/.venv
uv pip install --python tools/audit_prompt_builder/.venv/bin/python -r tools/audit_prompt_builder/requirements.txt
tools/audit_prompt_builder/.venv/bin/python -m streamlit run tools/audit_prompt_builder/app.py
```

Alternatively, install `requirements.txt` with pip in your preferred environment
and run `python -m streamlit run tools/audit_prompt_builder/app.py`.
Streamlit opens at http://localhost:8501.

## Use

1. Select `conceptual-skill.en.json` or `conceptual-skill.es.json` and click
   **Load selected file**. Replace the document placeholders with the skill,
   applicable philosophy/methodology, and requirements.
2. Review the goal, criteria, and scoring dimensions. Both conceptual profiles
   use four equally weighted dimensions on a 0–5 scale.
3. Copy, download, or **Save prompt to outputs (.txt)**. Use **Save my inputs**
   to download the complete JSON, including your output limits.

Ready-to-fill prompts: [English](outputs/conceptual-skill.en.txt) and
[Spanish](outputs/conceptual-skill.es.txt). They are generated templates, not
completed audits. New saved exports get a title and timestamp.

## Files

| Path | Contents |
|------|----------|
| `app.py` | Streamlit editor, JSON validation, and prompt generation |
| `requirements.txt` | Standalone app dependencies |
| `templates/default.json` | Complete input template and app defaults |
| `profiles/` | Current editable JSON profiles shown in the picker |
| `outputs/` | Current prompts and new exports |
| `archive/` | Historical profiles and superseded exports, excluded from the picker |
| `docs/input-format.md` | Field reference and output contract |

The old `tools/audit_prompt_builder.py`, `tools/inputs/`, `tools/prompts/`,
`tools/prompt_inputs.template.json`, and `tools/tools-reqs.txt` now live here.
Update launch commands to `app.py`; existing JSON remains loadable.

**Focused** performs one review. **Detailed** adds optional analysis stages and
a scoring self-check, but retains the same concise output. **Include scoring
summary** controls the final score and matrix in both modes. Output limits are
editable and stored in JSON. Context and checks are preserved verbatim: keep
instructions concise and include the source material needed to assess them.

The app builds text locally; it does not call an LLM or execute the audit.
Prompt length does not guarantee model latency or review quality.

## Verification and references

With the tool requirements installed, run from the repository root:

```bash
python -m unittest discover -s tests -p test_audit_prompt_builder.py -v
```

The defaults follow clear goals, relevant context, separated source material, and
explicit output expectations from [OpenAI](https://developers.openai.com/api/docs/guides/reasoning-best-practices),
[Anthropic (September 2025)](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents),
and [Google](https://ai.google.dev/gemini-api/docs/prompting-strategies), consulted
on 2026-11-18. Response limits are product defaults; no external model benchmark
is bundled. To roll back this standalone refactor, restore its previous paths
and the matching app/tests/docs together. The CLI and methodology are unaffected.

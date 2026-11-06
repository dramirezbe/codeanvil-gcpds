"""T10 — the generated AGENTS.md follows the full V-SIL v3 flow (S14, S15, S16).

Plan: odd/tasks/2026-11-05_AGENTS_template_full_flow.md
"""

import re

from test_create import _agents_md, db_path  # noqa: F401  (db_path is a fixture)


def _section(text: str, heading: str) -> str:
    """Body of one `## <heading>` section, up to the next `## ` heading.

    `## Iteration <N>` belongs to the report example inside Report Format."""
    match = re.search(rf"^## {re.escape(heading)}\n(.*?)(?=^## (?!Iteration )|\Z)", text, re.S | re.M)
    assert match, f"missing section: ## {heading}"
    return match.group(1)


def test_agents_md_describes_the_full_flow(tmp_path, db_path):  # noqa: F811
    text = _agents_md(tmp_path, db_path)

    for needle in ("S2_artifacts/", "G2_artifacts/", "verified_prototype.md", "vsil-verifier",
                   "fresh session", "Verdict: design defect", "Verdict: module defect",
                   "Not applicable: no lab inputs in the Build Package."):
        assert needle in text, needle
    assert "S0 → G0 → S1 → G1 → S2 → G2" in text
    assert "(S0, G0, S1, G1, S2, G2)" in text


def test_agents_md_drops_the_repository_context_and_software_section(tmp_path, db_path):  # noqa: F811
    text = _agents_md(tmp_path, db_path)

    for banned in ("There is no `src/`", "(and later S2, G2)", "not available in this release",
                   "## Context", "## Software", "CodeAnvil", "templates/", "pyproject.toml",
                   "run.sh"):
        assert banned not in text, banned


def test_agents_md_on_project_open_points_to_status_skills_and_gt(tmp_path, db_path):  # noqa: F811
    section = _section(_agents_md(tmp_path, db_path), "On Project Open")

    for needle in ("codeanvil status", "codeanvil now", ".agents/skills/", "GT/"):
        assert needle in section, needle


def test_agents_md_names_the_verifier_subagent_without_orchestrating(tmp_path, db_path):  # noqa: F811
    text = _agents_md(tmp_path, db_path)
    section = _section(text, "Subagents")

    for folder in (".claude/agents/", ".opencode/agents/", ".codex/agents/"):
        assert folder in section, folder
        assert (tmp_path / "proj" / folder).is_dir(), folder
    assert "G2" in section
    assert "fresh session" in section


def test_agents_md_layout_lists_only_what_scaffold_and_reports_create(tmp_path, db_path):  # noqa: F811
    text = _agents_md(tmp_path, db_path)

    for heading in ("Folder Reference", "Project Layout"):
        section = _section(text, heading)
        for needle in ("S2_artifacts/", "G2_artifacts/", ".claude/agents/"):
            assert needle in section, (heading, needle)
        for banned in ("src/", "verification/", "package.json", "uv.lock", "cmd/", "daemon/"):
            assert banned not in section, (heading, banned)


def test_agents_md_report_format_covers_s2_and_g2(tmp_path, db_path):  # noqa: F811
    section = _section(_agents_md(tmp_path, db_path), "Report Format")

    assert "`S2.md`" in section
    assert "`G2.md`" in section
    assert "Every iteration of G0, S1, G1, S2 and G2" in section

"""The generated AGENTS.md describes the active v4 flow and supported tools.

Plan: odd/tasks/2026-11-05_AGENTS_template_full_flow.md
"""

import argparse
import re

from codeanvil.CLI.parser import build_parser
from codeanvil.config.paths import CONFIG

from test_create import _agents_md, db_path  # noqa: F401  (db_path is a fixture)


def _section(text: str, heading: str) -> str:
    """Body of one `## <heading>` section, up to the next `## ` heading.

    `## Iteration <N>` belongs to the report example inside Report Format."""
    match = re.search(rf"^## {re.escape(heading)}\n(.*?)(?=^## (?!Iteration )|\Z)", text, re.S | re.M)
    assert match, f"missing section: ## {heading}"
    return match.group(1)


def test_agents_md_describes_the_full_flow(tmp_path, db_path):  # noqa: F811
    text = _agents_md(tmp_path, db_path)

    for needle in ("S3_artifacts/", "G3_artifacts/", "verified_prototype.md", "vsil-verifier",
                   "fresh session", "Verdict: design defect", "Verdict: module defect",
                   "Not applicable: no lab inputs in the Build Package."):
        assert needle in text, needle
    assert "S0 → G0 → S1 → G1 → S2 → G2" in text
    assert "(S0, G0, S1, G1, S2, G2, S3, G3)" in text


def test_execution_map_distinguishes_slice_progress_from_system_delivery(tmp_path, db_path):  # noqa: F811
    overview = _section(_agents_md(tmp_path, db_path), "Execution overview")
    diagram = re.search(r"```mermaid\n(.*?)```", overview, re.S).group(1)
    # A general PASS must never imply a prototype after an infrastructure/module slice.
    prototype_edges = [line.strip() for line in diagram.splitlines() if "| VP[" in line]
    assert prototype_edges == ['G3 -->|"system PASS"| VP["Verified Prototype"]']
    assert 'G3 -->|"slice PASS: next scope"| S2' in diagram
    assert set(re.findall(r'(\w+) -\.->\|"infeasible"\| RFD', diagram)) == {"S1", "G1", "G3"}
    assert "new cycle" in diagram
    assert "slice 0" in overview and "verification kit" in overview
    assert "module slices" in overview and "end-to-end paths" in overview


def test_cli_catalog_covers_the_actual_parser_without_inventing_commands(tmp_path, db_path):  # noqa: F811
    catalog = _section(_agents_md(tmp_path, db_path), "CLI capabilities")
    commands = next(a for a in build_parser()._actions if isinstance(a, argparse._SubParsersAction))
    documented = set(re.findall(r"\bcodeanvil ([a-z][a-z-]*)", catalog))
    assert documented == set(commands.choices)
    for family in ("custody", "runtime", "mcp"):
        actions = next(a for a in commands.choices[family]._actions if isinstance(a, argparse._SubParsersAction))
        row = next(line for line in catalog.splitlines() if f"`codeanvil {family} " in line)
        for action in actions.choices:
            assert re.search(rf"\b{re.escape(action)}\b", row), (family, action)
    assert "keeping files by default" in catalog
    assert "v3-only" in catalog and "incompatible with v4" in catalog
    assert "does not run stages or decide gates" in catalog


def test_agents_md_drops_the_repository_context_and_software_section(tmp_path, db_path):  # noqa: F811
    text = _agents_md(tmp_path, db_path)

    for banned in ("There is no `src/`", "(and later S2, G2)", "not available in this release",
                   "## Context", "## Software", "CodeAnvil", "templates/", "pyproject.toml",
                   "run.sh"):
        assert banned not in text, banned


def test_agents_md_on_project_open_points_to_status_skills_and_gt(tmp_path, db_path):  # noqa: F811
    section = _section(_agents_md(tmp_path, db_path), "On Project Open")

    for needle in ("codeanvil status", "codeanvil now", "codeanvil backup <stage>",
                   ".agents/skills/", ".codeanvil/GT/"):
        assert needle in section, needle


def test_agents_md_names_the_verifier_subagent_without_orchestrating(tmp_path, db_path):  # noqa: F811
    text = _agents_md(tmp_path, db_path)
    section = _section(text, "Subagents")

    for folder in (".claude/agents/", ".opencode/agents/", ".codex/agents/"):
        assert folder in section, folder
        assert (tmp_path / "proj" / folder).is_dir(), folder
    assert "G3" in section
    assert "fresh session" in section
    assert "| `vsil-implementor` | S3 |" in section
    assert "| `vsil-verifier` | G3 |" in section
    for runtime, suffix in (("claude", "md"), ("opencode", "md"), ("codex", "toml")):
        assert (tmp_path / "proj" / f".{runtime}/agents/vsil-implementor.{suffix}").is_file()


def test_agents_md_layout_lists_only_what_scaffold_and_reports_create(tmp_path, db_path):  # noqa: F811
    text = _agents_md(tmp_path, db_path)

    for heading in ("Folder Reference", "Project Layout"):
        section = _section(text, heading)
        for needle in ("S3_artifacts/", "G3_artifacts/", ".claude/agents/"):
            assert needle in section, (heading, needle)
        for banned in ("src/", "verification/", "package.json", "uv.lock", "cmd/", "daemon/"):
            assert banned not in section, (heading, banned)


def test_agents_md_report_format_covers_s2_and_g2(tmp_path, db_path):  # noqa: F811
    section = _section(_agents_md(tmp_path, db_path), "Report Format")

    assert "`S2.md`" in section
    assert "`G2.md`" in section
    assert "Every iteration of G0, S1, G1, S2, G2, S3 and G3" in section


def test_admission_summary_preserves_scoped_rework_and_delta_intake(tmp_path, db_path):  # noqa: F811
    text = _agents_md(tmp_path, db_path)
    rules = _section(text, "Rules")
    assert "nominal forward order" in rules
    assert "Rework, delta-intake and delta-sync" in rules
    assert "owning skill's explicit admission" in rules
    assert "latest applicable scoped iteration" in _section(text, "Available Skills")
    assert "even on G3 FEEDBACK" in text
    assert "without a new S2 iteration or a G3 PASS prerequisite" in text


def test_cycle_selection_refreshes_next_and_excludes_closed_cycles(tmp_path, db_path):  # noqa: F811
    cycle = _section(_agents_md(tmp_path, db_path), "Cycle")
    assert "existing **open** cycles" in cycle
    assert "If the user names\n  a closed cycle" in cycle
    assert "do not reopen it or change the active cycle to it" in cycle
    assert cycle.index("Record the selected cycle") < cycle.index("rerun `codeanvil status`")
    assert "never reuse the result from before cycle selection" in cycle
    assert "no `Next:` line, start at S0" in cycle


def test_stage_delivery_semantics_include_all_configured_stages(tmp_path, db_path):  # noqa: F811
    report = _section(_agents_md(tmp_path, db_path), "Report Format")
    match = re.search(r"On a stage\s*\(([^)]+)\), PASS means the output was delivered", report)
    assert match
    assert set(match.group(1).split(", ")) == set(CONFIG["stage_reports"])


def test_hardware_timing_and_gt_authority_do_not_conflict(tmp_path, db_path):  # noqa: F811
    text = _agents_md(tmp_path, db_path)
    assert "Nothing hardware-related is written before G3" not in text
    assert "Creating new target-enrollment" in text
    assert "earlier COTS descriptions, MCP configuration" in text
    assert "GT delta requires explicit acceptance by the Build Package\nauthor" in text
    assert "different reviewer's approval alone is not" in text

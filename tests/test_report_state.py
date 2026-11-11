"""Report baselines must describe the last appended iteration, even mid-write."""

import pytest

from codeanvil.reports import ReportState, parse_report_iterations, report_state, stale_reason


def test_partial_latest_iteration_cannot_inherit_pass(tmp_path):
    path = tmp_path / "G1.md"
    path.write_text("## Iteration 1\n| HITL | PASS |\n## Iteration 2\nBased on: S1 iteration 2\n")
    assert report_state(path) == ReportState(2, None, ("S1", 2))


def test_latest_section_owns_number_and_chain_metadata(tmp_path):
    path = tmp_path / "G1.md"
    path.write_text(
        "## Iteration 7\n| HITL | PASS |\nBased on: S1 iteration 6\n"
        "Superseded by cycle: 02_old\n"
        "## Iteration 3\n| HITL | FEEDBACK |\nBased on: S1 iteration 2\n"
    )
    assert report_state(path) == ReportState(3, "FEEDBACK", ("S1", 2))


def test_placeholder_row_is_not_a_verdict(tmp_path):
    path = tmp_path / "G1.md"
    path.write_text("## Iteration 1\n| HITL | PASS | FEEDBACK |\n")
    assert report_state(path).hitl is None


def test_pre_iteration_report_keeps_its_existing_verdict_behavior(tmp_path):
    path = tmp_path / "G0.md"
    path.write_text("# G0\n| HITL | FEEDBACK |\n")
    assert report_state(path).hitl == "FEEDBACK"


def test_iteration_browser_keeps_file_order_and_partial_sections():
    sections = parse_report_iterations(
        "# G1\n## Iteration 1\n| HITL | PASS |\n"
        "## Iteration 2\nWork in progress\n"
    )
    assert [(section.number, section.hitl) for section in sections] == [(1, "PASS"), (2, None)]
    assert sections[1].content.startswith("## Iteration 2")


def test_staleness_follows_recorded_links_transitively():
    gates = {
        "S0": ReportState(2, "PASS"),
        "G0": ReportState(1, "PASS", ("S0", 1)),
        "S1": ReportState(1, "PASS", ("G0", 1)),
    }
    assert stale_reason("G0", gates) == "based on S0 iteration 1, S0 is at 2"
    assert stale_reason("S1", gates) == "G0 is stale"


def test_missing_future_and_cyclic_baselines_do_not_invent_staleness():
    gates = {
        "S0": ReportState(1, "PASS", ("G0", 1)),
        "G0": ReportState(1, "PASS", ("S0", 2)),
        "S1": ReportState(1, "PASS", ("missing", 1)),
    }
    assert all(stale_reason(stage, gates) is None for stage in gates)


def test_status_uses_the_shared_staleness_function():
    from codeanvil.CLI.commands.status import _stale_reason

    assert _stale_reason is stale_reason


@pytest.mark.parametrize("fence", ["```", "~~~~"])
def test_fenced_examples_cannot_create_iterations_or_state(tmp_path, fence):
    path = tmp_path / "G1.md"
    path.write_text(
        "## Iteration 1\n| HITL | FEEDBACK |\n### Description\n"
        "Based on: S1 iteration 2\n"
        f"{fence}markdown\n## Iteration 99\n| HITL | PASS |\n"
        f"Based on: S1 iteration 99\nSuperseded by cycle: 99_fake\n{fence}\n"
    )
    assert report_state(path) == ReportState(1, "FEEDBACK", ("S1", 2))
    sections = parse_report_iterations(path.read_text())
    assert len(sections) == 1
    assert "## Iteration 99" in sections[0].content
    assert sections[0].hitl == "FEEDBACK"


def test_description_verdict_table_does_not_override_iteration_metadata(tmp_path):
    path = tmp_path / "G1.md"
    path.write_text(
        "## Iteration 1\n| HITL | FEEDBACK |\n### Description\n"
        "Example response table:\n| HITL | PASS |\n"
    )
    assert report_state(path).hitl == "FEEDBACK"
    assert parse_report_iterations(path.read_text())[0].hitl == "FEEDBACK"


@pytest.mark.parametrize("fence", ["```", "~~~"])
def test_fenced_pass_cannot_complete_partial_newest_iteration(tmp_path, fence):
    path = tmp_path / "G1.md"
    path.write_text(
        "## Iteration 1\n| HITL | PASS |\n"
        "## Iteration 2\n### Description\nBased on: S1 iteration 2\n"
        f"{fence}\n## Iteration 99\n| HITL | PASS |\n{fence}\n"
    )
    assert report_state(path) == ReportState(2, None, ("S1", 2))

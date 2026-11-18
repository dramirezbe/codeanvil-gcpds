"""Feedback is persisted before the parent resumes the owning stage skill."""

import pytest

from codeanvil.init.create import scaffold_project


GATES = ["G0_valid_req_and_GT", "G1_design_review", "G2_plan_review", "G3_adaptive_verification"]
STAGES = ["S0_normalise_build_package", "S1_design_system", "S2_plan_modules", "S3_implement_modules"]


@pytest.fixture
def project(tmp_path):
    return scaffold_project("Feedback handoff probe", "probe", tmp_path)


@pytest.mark.parametrize("skill", GATES)
def test_generated_gate_persists_feedback_and_continues_through_owning_skill(project, skill):
    text = " ".join((project / ".agents/skills" / skill / "SKILL.md").read_text().split())
    for required in ("### Description", "reasons", "evidence", "correction suggestions",
                     "same parent agent", "repeat", "human"):
        assert required in text, (skill, required)
    assert "do not stop" in text.lower(), skill
    assert "read" in text.lower() and "loads" in text.lower(), skill


@pytest.mark.parametrize("skill", STAGES)
def test_generated_stage_consumes_feedback_description_without_reasking(project, skill):
    text = " ".join((project / ".agents/skills" / skill / "SKILL.md").read_text().split())
    for required in ("same parent agent", "### Description", "reasons", "evidence",
                     "correction suggestions", "repeat"):
        assert required in text, (skill, required)


def test_reference_keeps_feedback_in_iteration_description_and_fresh_contexts(project):
    text = " ".join((project / "AGENTS.md").read_text().split())
    assert "First publish the completed FEEDBACK iteration" in text
    assert "### Description` is the handoff" in text
    assert "same parent agent then loads the routed stage's skill" in text
    assert "new human verdict" in text
    assert "Keep fresh implementation/verifier contexts" in text
    assert "a route named only in chat is not a complete handoff" in text

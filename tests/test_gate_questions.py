"""Every human gate asks its verdict through the runtime's native question tool."""

import pytest

from test_create import _scaffold_skill, _skill_text, db_path  # noqa: F401
from codeanvil.CLI.commands.create import cmd_create

GATES = {
    "G0_valid_req_and_GT": ("`PASS`", "`FEEDBACK`"),
    "G1_design_review": ("`PASS`", "`FEEDBACK`", "`RFD`"),
    "G2_adaptive_verification": ("`PASS`", "`FEEDBACK`", "`RFD`"),
}


def _question_rule(text: str) -> str:
    start = text.index("**Asking the human.**")
    return text[start:text.index("\n\n", start)]


@pytest.mark.parametrize("skill", GATES)
def test_gate_asks_with_the_native_question_tool(skill):
    rule = _question_rule(_skill_text(skill))

    assert "`AskUserQuestion`" in rule
    assert "native question tool" in rule
    for option in GATES[skill]:
        assert option in rule
    assert "free-text answer" in rule


@pytest.mark.parametrize("skill", GATES)
def test_gate_falls_back_to_chat_and_waits(skill):
    rule = _question_rule(_skill_text(skill))

    assert "no question tool" in rule
    assert "ask the same question in chat and wait for the reply" in rule
    assert "never assume or default an answer" in rule


@pytest.mark.parametrize("skill", GATES)
def test_gate_typed_answer_never_counts_as_pass(skill):
    rule = _question_rule(_skill_text(skill))

    assert "recorded verbatim" in rule
    assert "counts as `FEEDBACK`, never as `PASS`" in rule


def test_g0_keeps_rfd_out_of_gate_h():
    rule = _question_rule(_skill_text("G0_valid_req_and_GT"))

    assert "`RFD`" not in rule


def test_scaffolded_gates_carry_the_question_rule(tmp_path, db_path):
    cmd_create(None, tmp_path, project_name="Proj")

    for skill in GATES:
        text = _scaffold_skill(tmp_path, skill, "SKILL.md").read_text(encoding="utf-8")
        assert "`AskUserQuestion`" in _question_rule(text)


def test_s2_asks_the_pause_schedule_with_the_native_question_tool():
    text = " ".join(_skill_text("S2_implement_services").split())

    assert "`AskUserQuestion`" in text
    assert "Per layer (recommended)" in text
    assert "If the runtime has no question tool" in text

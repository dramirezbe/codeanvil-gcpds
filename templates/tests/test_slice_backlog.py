import runpy
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parents[1] / "skills/S2_plan_modules/scripts/slice_backlog.py"
MODULE = runpy.run_path(str(SCRIPT))
Module = MODULE["Module"]


def mod(name, deps=(), sub="SUB-001"):
    return Module(name, sub, "HAL", list(deps), [], False, "VL-1", ["SYS-001"])


def test_kahn_levels_diamond_are_independent_and_deterministic():
    modules = {"d": mod("d", ["b", "c"]), "c": mod("c", ["a"]), "b": mod("b", ["a"]), "a": mod("a")}
    assert MODULE["levels"](modules) == [["a"], ["b", "c"], ["d"]]
    assert MODULE["levels"](dict(reversed(list(modules.items())))) == [["a"], ["b", "c"], ["d"]]


@pytest.mark.parametrize("modules", [{"a": mod("a", ["a"])}, {"a": mod("a", ["missing"])},
                                      {"a": mod("a", ["b"]), "b": mod("b", ["a"])}])
def test_reject_cycles_and_unknown_dependencies(modules):
    with pytest.raises(ValueError):
        MODULE["levels"](modules)


def card(name, deps="none", traced="SYS-001", sub="SUB-001"):
    values = dict(module_id=name, subsystem_id=sub, layer="HAL", depends_on=deps,
                  provides="INT-001", hw_dependency="false", required_vl="VL-1", traced_reqs=traced)
    return f"#### {sub}/{name}\n" + "".join(f"| {k} | {v} |\n" for k, v in values.items())


def test_parser_cli_exit_and_duplicate_requirements(tmp_path, capsys):
    sdd = tmp_path / "SDD.md"
    sdd.write_text(card("a") + card("b", "SUB-001/a", sub="SUB-002"))
    assert MODULE["main"]([str(sdd)]) == 0
    assert ".codeanvil/plans/SUB-002/b/PLAN.md" in capsys.readouterr().out
    for text in [card("a", "missing"), card("a", "a"), card("a") * 2, card("a", traced="none")]:
        sdd.write_text(text)
        assert MODULE["main"]([str(sdd)]) == 1

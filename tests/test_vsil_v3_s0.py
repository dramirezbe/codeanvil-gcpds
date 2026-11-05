"""T2 (V-SIL v3 full flow) — S0 casts lab inputs into the SyRS as optional content (D9)."""

import re
import shutil
import subprocess
import sys
from pathlib import Path

from codeanvil.CLI.commands.create import cmd_create
from test_create import _scaffold_skill, _skill_text, db_path  # noqa: F401  (db_path is a fixture)

NOT_APPLICABLE = "Not applicable: no lab inputs in the Build Package."
REPO = Path(__file__).resolve().parents[1]
LAB_HEADINGS = (
    "## 4. Correction Chains",
    "## 5. Uncertainty Budgets",
    "## 6. Field Measurement Protocols",
)


def test_s0_skill_routes_lab_inputs_into_the_syrs():
    text = _skill_text("S0_normalise_build_package")

    assert NOT_APPLICABLE in text
    assert "PROTO-NNN" in text
    for section in ("§4", "§5", "§6"):
        assert section in text


def test_scaffolded_syrs_blueprint_marks_lab_sections_optional(tmp_path, db_path):  # noqa: F811
    cmd_create(None, tmp_path, project_name="Proj")

    for skill in ("S0_normalise_build_package", "G0_valid_req_and_GT"):
        text = _scaffold_skill(tmp_path, skill, "templates", "G0_SyRS.md").read_text(encoding="utf-8")
        for heading in LAB_HEADINGS:
            body = text.split(heading, 1)[1].split("\n## ", 1)[0]
            assert NOT_APPLICABLE in body, (skill, heading)


def _blank_lab_sections(syrs: str) -> str:
    """Replace the body of SyRS §4–§6 with the exact not-applicable line."""
    for heading in LAB_HEADINGS:
        pattern = re.compile(re.escape(heading) + r"\n.*?(?=\n## )", re.DOTALL)
        syrs, count = pattern.subn(f"{heading}\n\n{NOT_APPLICABLE}\n", syrs)
        assert count == 1, heading
    return syrs


def test_g0_passes_a_syrs_without_lab_inputs(tmp_path):
    validator = REPO / "templates/skills/G0_valid_req_and_GT/scripts/g0_validate.py"
    t0 = REPO / "methodology/test/T0_ANE-Lap2/just-edge"
    strs, syrs = tmp_path / "StRS.md", tmp_path / "SyRS.md"
    shutil.copy2(t0 / "StRS.md", strs)
    syrs.write_text(_blank_lab_sections((t0 / "SyRS.md").read_text(encoding="utf-8")), encoding="utf-8")
    assert "PROTO-" not in syrs.read_text(encoding="utf-8").split(LAB_HEADINGS[2], 1)[1].split("\n## ", 1)[0]

    result = subprocess.run(
        [sys.executable, str(validator), str(strs), str(syrs)],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr

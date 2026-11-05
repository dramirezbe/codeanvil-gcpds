"""T4: G1 reviews the HAL mode, the verification kit, the toolchain and the telemetry companion."""

from codeanvil.CLI.commands.create import cmd_create
from codeanvil.config.paths import TEMPLATES_DIR
from test_create import _scaffold_skill, _skill_text, db_path  # noqa: F401  (db_path is a fixture)

CHECKLIST = ("G1_design_review", "references", "G1_CHECKLIST.md")


def _checklist_text() -> str:
    return (TEMPLATES_DIR / "skills").joinpath(*CHECKLIST).read_text(encoding="utf-8")


def _g1_text() -> str:
    return _skill_text("G1_design_review") + "\n" + _checklist_text()


def test_g1_checklist_numbering_matches_the_s1_g1_template():
    text = _g1_text()

    assert "G1.11 HAL ladder" in text
    assert "G1.12 Telemetry companion" in text
    assert "G1.13 ML readiness" in text
    assert "G1.11 ML readiness" not in text


def test_g1_reviews_the_hal_mode_and_only_checks_the_real_hw_hal_in_mock_plus_real():
    checklist = _checklist_text()
    hal_row = next(line for line in checklist.splitlines() if "G1.11 HAL ladder" in line)

    assert "HAL mode" in hal_row
    assert "mock-only" in hal_row and "mock+real" in hal_row
    assert "PROTO-*" in hal_row
    assert "Not applicable" in hal_row
    assert "advisory" in hal_row  # Real HW HAL items in mock-only are never open


def test_g1_profile_row_ties_hw_dependency_to_mock_plus_real():
    checklist = _checklist_text()
    profile = next(line for line in checklist.splitlines() if "G1.5 verification profile" in line)

    assert "`hw_dependency: true` means `VL-2`" in profile
    assert "mock+real" in profile


def test_g1_reviews_the_telemetry_companion_outside_src():
    checklist = _checklist_text()
    row = next(line for line in checklist.splitlines() if "G1.12 Telemetry companion" in line)

    assert "§1.7" in row
    assert "verification/telemetry/" in row
    assert "never under `src/`" in row
    assert "appears as a module" in row


def test_g1_reviews_the_kit_and_the_toolchain():
    checklist = _checklist_text()
    row = next(line for line in checklist.splitlines() if line.startswith("| Kit "))

    assert "§1.3.4" in row
    assert "Toolchain" in row
    assert "Python" in row and "uv" in row and "pytest" in row
    assert "TypeScript" in row and "pnpm" in row and "vitest" in row


def test_g1_skill_fills_the_new_rows_and_routes_a_pass_to_s2():
    text = _skill_text("G1_design_review")

    assert "Fill the checklist, including G1.11–G1.13 and the kit row." in text
    assert "G1 passed. Run the S2 skill." in text
    assert "S2 is not available in this release" not in text


def test_g1_ml_readiness_keeps_its_content():
    checklist = _checklist_text()
    row = next(line for line in checklist.splitlines() if "G1.13 ML readiness" in line)

    assert "Only if §1.5 exists" in row
    assert "deterministic fake response" in row
    assert "Supplied metrics are not judged as G2 evidence" in row


def test_scaffolded_g1_checklist_carries_the_new_rows(tmp_path, db_path):  # noqa: F811
    cmd_create(None, tmp_path, project_name="Proj")
    text = _scaffold_skill(tmp_path, *CHECKLIST).read_text(encoding="utf-8")

    assert "G1.11 HAL ladder" in text
    assert "Toolchain" in text

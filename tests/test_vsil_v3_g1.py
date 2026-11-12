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
    assert "functional tests do not universally require an oracle" in hal_row
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

    assert "Fill the checklist, including G1.11–G1.16 and the kit row." in text
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


def test_scaffold_carries_target_design_and_review_contracts(tmp_path, db_path):  # noqa: F811
    """A generated project must keep location, HAL and evidence requirements aligned."""
    cmd_create(None, tmp_path, project_name="Proj")
    design = _scaffold_skill(tmp_path, "S1_design_services", "references", "SDD.md").read_text()
    checklist = _scaffold_skill(tmp_path, *CHECKLIST).read_text()
    hal_row = next(line for line in checklist.splitlines() if "G1.11 HAL ladder" in line)
    telemetry_row = next(line for line in checklist.splitlines() if "G1.12 Telemetry" in line)

    assert "| Target(s)" in design
    assert "No targets: block means local execution" in design
    assert "§1.6 resolve every service, path and level" in hal_row
    assert "A target is undeclared/ambiguous" in hal_row
    assert "PIL is presented as VL-2" in hal_row
    assert "operating envelope per execution target (with COTS basis)" in telemetry_row
    assert "Host readings cannot stand in for a remote target" in telemetry_row


# --- G1 validates by itself, with no script (2026-11-05) --------------------

def test_g1_runs_no_script_at_all():
    text = _skill_text("G1_design_review")

    assert "python -c" not in text
    assert "hashlib" not in text
    assert "sha256sum" in text
    assert "G1 runs no script" in text


def test_g1_spends_tokens_on_a_full_review():
    text = _skill_text("G1_design_review")

    assert "Read the whole design and both GT documents" in text
    assert "re-derive every row yourself" in text
    assert "Never trust the design's own summaries" in text


def test_g1_plans_automatic_target_preparation_without_a_version_equality_gate():
    text = " ".join(_skill_text("G1_design_review").split())
    row = next(line for line in _checklist_text().splitlines() if line.startswith("| G1.14"))

    assert "probe_target" in text and "ssh_exec_cmd" in text
    assert "after the pre-HW review" in text
    assert "Missing installable tools do not block G1" in text
    assert "Version differences alone are not defects" in text
    assert "host observations" in row and "pre-G1 installation deadlock" in row


def test_g1_frontmatter_allows_read_only_remote_observation():
    text = _skill_text("G1_design_review")
    assert "No network access" not in text
    assert "No scripts." in text
    assert "S2/G2 prepare target tools after the pre-HW review" in text


def test_mock_plus_real_needs_metrology_only_when_the_requirement_needs_it():
    row = next(line for line in _checklist_text().splitlines() if "G1.11 HAL ladder" in line)
    assert "when the requirement or conclusion needs them" in row
    assert "functional tests do not universally require an oracle" in row
    assert "capability checks and safe stop" in row


# --- bounded rework: change set, impact map, G1.16 (2026-11-06) --------------

def test_g1_reviews_the_s1_change_set_and_produces_an_impact_map():
    text = " ".join(_skill_text("G1_design_review").split())

    assert "design change set" in text
    assert "impact map" in text
    assert "files S2 must edit" in text
    assert "retest only" in text
    assert "row G1.16" in text


def test_g1_checklist_has_the_change_impact_row():
    checklist = _checklist_text()
    row = next(line for line in checklist.splitlines() if line.startswith("| G1.16"))

    assert "design change set" in row
    assert "impact map" in row
    assert "interface" in row

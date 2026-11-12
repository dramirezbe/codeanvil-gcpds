"""T7: G2 runs the S2 evidence through the verifier subagent and writes the Verified Prototype."""

from codeanvil.CLI.commands.create import cmd_create
from codeanvil.config.paths import TEMPLATES_DIR
from codeanvil.init.create import _parse_skill_frontmatter
from test_create import _scaffold_skill, _skill_text, db_path  # noqa: F401  (db_path is a fixture)

SKILL = "G2_adaptive_verification"
PROTOTYPE = TEMPLATES_DIR / "skills" / SKILL / "references" / "verified_prototype.md"


def _g2_text() -> str:
    return _skill_text(SKILL)


def test_g2_frontmatter_keeps_the_gate_shape():
    meta = _parse_skill_frontmatter(TEMPLATES_DIR / "skills" / SKILL / "SKILL.md")

    assert meta["name"] == "g2-adaptive-verification"
    assert meta["gate"] == "G2"
    assert "Not implemented" not in meta["description"]


def test_g2_prerequisite_messages_match_g1_wording():
    text = _g2_text()

    assert "Cycle closed by RFD. Continue in cycle" in text
    assert "Cycle suspended by RFD. Run the RFD skill." in text
    assert "S2 must pass first. Run the S2 skill." in text
    assert "S2 must rework first. Run the S2 skill." in text
    assert "Outcome: Withdrawn" in text
    assert "Based on: S2 iteration" in text


def test_g2_delegates_runs_to_the_verifier_and_falls_back_to_a_fresh_session():
    text = _g2_text()

    assert "vsil-verifier" in text
    assert "fresh session" in text
    assert "test_run.md" in text
    assert "verification/run.sh vl0" in text and "verification/run.sh vl1" in text


def test_g2_levels_by_mode_and_routes():
    text = _g2_text()

    assert "mock-only" in text and "mock+real" in text
    assert "PROTO-" in text
    assert "Possible infeasibility" in text
    assert "Verdict: module defect" in text
    assert "Verdict: design defect" in text
    assert "Verdict: RFD" in text
    assert "verified_prototype.md" in text
    assert "VALIDATED" in text
    assert "FW-ML-4" in text


def test_verified_prototype_template_has_the_paper_sections():
    text = PROTOTYPE.read_text(encoding="utf-8")

    for section in ("HAL mode", "Toolchain", "Module evidence", "Path evidence",
                    "Telemetry report", "Honesty declaration", "Delivered tree",
                    "Verifier", "RFDs issued", "Future work"):
        assert section in text, section
    assert "VERIFIED" in text and "VALIDATED" in text
    assert "verification/" in text and "src/<service>/" in text


def test_scaffold_ships_the_g2_reference(tmp_path, db_path):
    cmd_create(None, tmp_path, project_name="Proj")

    assert _scaffold_skill(tmp_path, SKILL, "references", "verified_prototype.md").is_file()
    assert "templates/skills/" not in _scaffold_skill(tmp_path, SKILL, "SKILL.md").read_text(encoding="utf-8")


def test_g2_fresh_session_runs_the_steps_itself():
    text = _skill_text("G2_adaptive_verification")

    assert "In a fresh session that did not run S2, G2 runs steps 2–5 itself" in text
    assert "`Verifier` = `fresh session`" in text


def test_g2_skill_backs_up_before_overwriting_the_verified_prototype():
    text = " ".join(_skill_text("G2_adaptive_verification").split())

    assert "codeanvil backup G2" in text
    assert "If it exits nonzero, stop and show its message; write no iteration." in text


# --- rework route split by verdict (2026-11-06) -----------------------------

def test_g2_prerequisite_splits_the_rework_route_by_verdict():
    text = " ".join(_skill_text("G2_adaptive_verification").split())

    assert ("return exactly `S2 must rework first. Run the S2 skill.` for `Verdict: module defect`, "
            "or `S1 must rework first. Run the S1 skill.` for `Verdict: design defect`.") in text


# --- placeholder telemetry is not evidence (2026-11-06, WU-L6) -------------


def test_g2_rejects_placeholder_telemetry_as_measured_evidence():
    text = " ".join(_skill_text("G2_adaptive_verification").split())

    assert "A constant or placeholder telemetry reading is not measured evidence" in text
    assert "Reject a constant or placeholder reading as measured evidence" in text


def test_g2_checks_provenance_without_redeploying_or_substituting_the_host():
    text = " ".join(_g2_text().split())
    prototype = " ".join(PROTOTYPE.read_text(encoding="utf-8").split())

    assert "No declared `targets:` means local execution" in text
    assert "never silently substitute the developer host" in text
    assert "expected digest and clean delivered git revision come from the host" in text
    assert "Recheck deployment identity after the runs" in text
    assert "Never call `code_sync`, `init_codeanvil` or `ssh_exec_cmd_trusted`" in text
    assert "missing/empty/corrupt telemetry" in text
    assert "collector exit 0 alone is insufficient" in text
    assert "Execution targets and provenance" in prototype
    assert "before/after provenance checks" in prototype


def test_scaffolded_g2_and_verifier_keep_the_same_remote_contract(tmp_path, db_path):
    cmd_create(None, tmp_path, project_name="Proj")
    g2 = _scaffold_skill(tmp_path, SKILL, "SKILL.md").read_text(encoding="utf-8")
    verifier = (tmp_path / "proj" / ".claude" / "agents" / "vsil-verifier.md").read_text()

    for text in (g2, verifier):
        assert "verification/check_deployment.py --expected" in text
        assert "fetch_evidence" in text
        assert "evidence gap" in text
        assert "torn final JSONL line" in text
    assert "templates/skills/" not in g2


def test_g2_demands_a_fresh_operator_capture_and_never_promotes_validator_success():
    text = " ".join(_g2_text().split())
    machine = (PROTOTYPE.parent / "machine_evidence.md").read_text(encoding="utf-8")

    for required in ("capture_request.json", "--not-before", "never sets `HITL`",
                     "S2's development capture is not fresh G2 evidence"):
        assert required in text
    assert "scalar measurement" in machine
    assert "Other predicates require an explicitly reviewed schema" in machine
    assert "never calls the trusted tool" in machine
    assert "including records with measured" in machine
    assert "<fetch-local-path>/<run-id>/measurement.json" in machine
    assert "Every fetch returns `local_path`" in machine


def test_scaffold_rewrites_the_machine_validation_command_and_ships_references(tmp_path, db_path):
    cmd_create(None, tmp_path, project_name="Proj")
    machine = _scaffold_skill(tmp_path, SKILL, "references", "machine_evidence.md").read_text()
    s2 = _scaffold_skill(tmp_path, "S2_implement_services", "SKILL.md").read_text()

    assert "templates/skills/" not in machine
    assert ".agents/skills/G2_adaptive_verification/scripts/validate_measurement.py" in machine
    assert ".agents/skills/G2_adaptive_verification/references/machine_evidence.md" in s2
    assert _scaffold_skill(tmp_path, SKILL, "references", "measurement.schema.json").is_file()

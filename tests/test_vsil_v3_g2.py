"""T7: G2 runs the S2 evidence through the verifier subagent and writes the Verified Prototype."""

import json
import shutil
import subprocess
import sys

import pytest

from codeanvil.CLI.commands.create import cmd_create
from codeanvil.config.paths import CONFIG, TEMPLATES_DIR
from codeanvil.init.create import _parse_skill_frontmatter
from test_create import _scaffold_skill, _skill_text, db_path  # noqa: F401  (db_path is a fixture)
from test_hil_measurements import captured  # noqa: F401 (fixture)

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
    assert "verification/" in text and "src/<subsystem>/" in text


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


# --- HIL fixes: operational branch + feedback change list (2026-11-12) ------


def test_g2_classifies_operational_problems_as_a_first_class_branch():
    text = " ".join(_g2_text().split())

    assert "operational-fix" in text
    assert "udev" in text and "plugdev" in text
    assert "must not route to S2 or S1 feedback" in text
    assert "re-run G2" in text
    # last-resort: hand the user the commands rather than mislabel it an S2 defect
    assert "hand the user the exact commands to run by hand on the target" in text
    assert "mislabeling it an S2 defect" in text


def test_g2_module_feedback_carries_the_change_list_in_the_description():
    text = " ".join(_g2_text().split())

    assert "right after the `Based on:` line" in text
    assert "an explicit, enumerated list of the concrete changes S2 must make" in text
    assert "without re-asking the human" in text
    assert "with no AskUser prompt and no redesign" in text


# --- placeholder telemetry is not evidence (2026-11-06, WU-L6) -------------


def test_g2_rejects_placeholder_telemetry_as_measured_evidence():
    text = " ".join(_skill_text("G2_adaptive_verification").split())

    assert "A constant or placeholder telemetry reading is not measured evidence" in text
    assert "Reject a constant or placeholder reading as measured evidence" in text


def test_g2_parent_prepares_but_fresh_verifier_executes_reviewed_hw():
    text = " ".join(_g2_text().split())
    prototype = " ".join(PROTOTYPE.read_text(encoding="utf-8").split())
    assert "No declared `targets:` means local execution" in text
    assert "never silently substitute the developer host" in text
    assert "Stop and wait for explicit `continue`" in text
    assert "clean Git tree and the candidate committed" in text
    assert "parent completes preparation before launching it" in text
    assert "fresh verifier runs the recorded real HW command" in text
    assert "not an exact-SemVer gate" in text
    assert "actual published tool ref" in text
    assert "the next G2 iteration number" in text
    assert "last appended G2 iteration number plus 1" in text
    assert "affected measures or proceed with the supported scope" in text
    assert "Execution equipment and preparation" in prototype
    assert "deployment_manifest.json" not in text
    assert "capture_request.json" not in text


def test_g2_enrolls_hardware_only_when_vl2_is_declared():
    """Credentials/IP/MAC are written at G2, only for a mock+real VL-2 design, and block the HW stage."""
    text = " ".join(_g2_text().split())
    assert "Hardware credentials, IP and MAC appear only here" in text
    assert "codeanvil credential-setup" in text
    assert "blocks the real-HW stage" in text
    assert "`mock-only` designs and designs limited to VL-0/VL-1 never trigger this step" in text
    assert "This version supports exactly one target" in text


def test_scaffolded_g2_and_verifier_keep_parent_pauses_and_causal_feedback(tmp_path, db_path):
    cmd_create(None, tmp_path, project_name="Proj")
    g2 = " ".join(_scaffold_skill(tmp_path, SKILL, "SKILL.md").read_text().split())
    verifier = " ".join((tmp_path / "proj" / ".claude" / "agents" / "vsil-verifier.md").read_text().split())
    for text in (g2, verifier):
        assert "fetch_evidence" in text and "local_path" in text
        assert "monotonic" in text or "synchronizes clocks" in text
        assert "concrete next action" in text
        assert "torn final JSONL line" in text
        assert "module" in text and "S2" in text and "design" in text and "RFD" in text
        assert "check_deployment.py" not in text
    assert "never asks the human" in g2
    assert "Ask the human anything" in verifier
    assert "without editing the DUT" in verifier
    assert "the next G2 iteration number" in verifier
    assert "templates/skills/" not in g2


def test_machine_record_accepts_general_metrics_without_hil_attestation():
    machine = (PROTOTYPE.parent / "machine_evidence.md").read_text(encoding="utf-8")

    assert "number, text or boolean" in machine
    assert "schema_version: 2" in machine
    assert "finite numeric values" in machine
    assert "not a passing test or a gate verdict" in machine
    assert "The agent runs functional or metrological tests" in machine
    assert "No file hash, deployment digest" in machine
    assert "`fetch_evidence` returns `local_path`" in machine


def test_scaffold_rewrites_the_machine_validation_command_and_ships_references(tmp_path, db_path):
    cmd_create(None, tmp_path, project_name="Proj")
    machine = _scaffold_skill(tmp_path, SKILL, "references", "machine_evidence.md").read_text()
    s2 = _scaffold_skill(tmp_path, "S2_implement_subsystems", "SKILL.md").read_text()

    assert "templates/skills/" not in machine
    assert ".agents/skills/G2_adaptive_verification/scripts/validate_measurement.py" in machine
    assert ".agents/skills/S2_implement_subsystems/references/machine_evidence.md" in s2
    assert _scaffold_skill(tmp_path, SKILL, "references", "measurement.schema.json").is_file()


def test_s2_owns_an_executable_copy_of_canonical_measurement_assets(tmp_path, db_path, captured):
    record, _ = captured
    cmd_create(None, tmp_path, project_name="Proj")
    producer = _scaffold_skill(tmp_path, SKILL)
    consumer = _scaffold_skill(tmp_path, "S2_implement_subsystems")
    for relative in ("scripts/validate_measurement.py", "references/measurement.schema.json"):
        assert (consumer / relative).read_bytes() == (producer / relative).read_bytes()
    guide = (consumer / "references/machine_evidence.md").read_text()
    assert ".agents/skills/S2_implement_subsystems/scripts/validate_measurement.py" in guide
    assert ".agents/skills/G2_adaptive_verification/" not in guide

    # Removing the producer from this temporary scaffold proves the consumer is standalone.
    shutil.rmtree(producer)
    script = consumer / "scripts/validate_measurement.py"
    args = [sys.executable, str(script), str(record)]
    result = subprocess.run(args, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["verdict"] == "human review required"


@pytest.mark.parametrize("asset,error", [("references/missing.json", FileNotFoundError),
                                         ("../outside.json", ValueError)])
def test_broken_shared_asset_configuration_fails_explicitly(tmp_path, db_path, monkeypatch, asset, error):
    monkeypatch.setitem(CONFIG, "shared_skill_assets", {SKILL: {"S2_implement_subsystems": [asset]}})
    with pytest.raises(error, match="shared skill asset"):
        cmd_create(None, tmp_path, project_name="Proj")

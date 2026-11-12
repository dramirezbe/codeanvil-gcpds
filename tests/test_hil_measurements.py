"""Synthetic interface tests, never a hardware verdict."""

import json
from pathlib import Path
import runpy
import subprocess
import sys

import pytest

from codeanvil.init.create import scaffold_project

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "templates/skills/G2_adaptive_verification/scripts/validate_measurement.py"
VALIDATOR = runpy.run_path(str(SCRIPT))


@pytest.fixture
def captured(tmp_path):
    record = {
        "schema_version": 2, "cycle": "01_lab", "stage": "G2", "iteration": 1,
        "run_id": "01_lab_1_2026-11-11_20-42-40-123", "target": "synthetic-device",
        "command": "verification/run.sh vl2", "started_at": "2026-11-12T01:42:40Z",
        "finished_at": "2026-11-12T01:42:41Z", "exit_code": 0,
        "measurements": [{"requirement_id": "SYS-ACQ-001", "metric": "sample_rate",
                          "value": 2000000, "unit": "samples/s", "criterion": "2000000 ± 2 %",
                          "result": "pass"}],
    }
    path = tmp_path / "measurement.json"
    path.write_text(json.dumps(record))
    return path, record


def check(path):
    return VALIDATOR["validate"](path)


def test_minimal_functional_record_needs_no_metrology_or_file_artifacts(captured):
    path, record = captured
    assert check(path) == record
    result = subprocess.run([sys.executable, str(SCRIPT), str(path)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["verdict"] == "human review required"


@pytest.mark.parametrize("value,result", [(True, "pass"), ("no packets received", "fail"),
                                          (0.002, "inconclusive"), (10**400, "pass")])
def test_values_and_results_support_functional_and_numeric_tests(captured, value, result):
    path, record = captured
    record["measurements"][0].update(value=value, result=result)
    record["device"] = {"notes": "optional metadata"}
    path.write_text(json.dumps(record))
    assert check(path)["measurements"][0]["result"] == result


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
def test_nonfinite_values_are_rejected_even_in_optional_context(captured, value):
    path, record = captured
    record["environment"] = {"temperature": value}
    path.write_text(json.dumps(record))
    with pytest.raises(ValueError, match="finite"):
        check(path)


@pytest.mark.parametrize("field,value", [("schema_version", 1), ("stage", "G0"),
                                         ("iteration", True), ("iteration", 0),
                                         ("exit_code", "0"), ("measurements", {})])
def test_malformed_structure_is_rejected(captured, field, value):
    path, record = captured
    record[field] = value
    path.write_text(json.dumps(record))
    with pytest.raises(ValueError):
        check(path)


def test_missing_criterion_is_not_a_valid_measurement(captured):
    path, record = captured
    del record["measurements"][0]["criterion"]
    path.write_text(json.dumps(record))
    with pytest.raises(ValueError, match="criterion"):
        check(path)


@pytest.mark.parametrize("field", json.loads((SCRIPT.parents[1] / "references/measurement.schema.json").read_text())["required"])
def test_required_record_fields_are_enforced_by_the_basic_checker(captured, field):
    path, record = captured
    del record[field]
    path.write_text(json.dumps(record))
    with pytest.raises(ValueError):
        check(path)


def test_failed_acquisition_can_record_no_measurements_with_an_explanation(captured):
    path, record = captured
    record.update(measurements=[], exit_code=2, error="device disconnected before acquisition")
    path.write_text(json.dumps(record))
    assert check(path)["error"] == record["error"]
    record["exit_code"] = 0
    path.write_text(json.dumps(record))
    with pytest.raises(ValueError, match="nonzero"):
        check(path)


def test_duplicate_fields_cannot_hide_a_failed_result(captured):
    path, _ = captured
    path.write_text(path.read_text().replace('"result": "pass"', '"result":"fail","result":"pass"'))
    with pytest.raises(ValueError, match="duplicate JSON key"):
        check(path)


def test_scaffolded_checker_accepts_v2_and_leaves_historical_evidence_unchanged(captured, tmp_path):
    path, record = captured
    project = scaffold_project("Measurement fixture", "proj", tmp_path)
    script = project / ".agents/skills/G2_adaptive_verification/scripts/validate_measurement.py"
    args = [sys.executable, str(script), str(path)]
    good = subprocess.run(args, capture_output=True, text=True, cwd=project)
    assert good.returncode == 0, good.stderr
    assert json.loads(good.stdout)["results"] == ["pass"]

    record["schema_version"] = 1
    path.write_text(json.dumps(record))
    historical = path.read_bytes()
    bad = subprocess.run(args, capture_output=True, text=True, cwd=project)
    assert bad.returncode == 2
    assert "historical evidence is not rewritten" in bad.stderr
    assert path.read_bytes() == historical

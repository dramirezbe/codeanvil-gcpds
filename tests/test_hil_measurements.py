"""Synthetic records test the evidence interface, never a hardware verdict."""

import hashlib
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
SHA = "a" * 64
REQUESTED_AT = "2026-11-11T12:00:00Z"


@pytest.fixture
def captured(tmp_path):
    raw = b"synthetic capture for interface testing only"
    (tmp_path / "capture.bin").write_bytes(raw)
    (tmp_path / "telemetry.jsonl").write_text('{"timestamp":"2026-11-11T12:00:00Z","cpu":10}\n')
    record = {
        "schema_version": 1, "run_id": "synthetic-001", "level": "VL-2", "hal_mode": "mock+real",
        "started_at": "2026-11-11T12:00:00Z", "finished_at": "2026-11-11T12:00:01Z",
        "target": {"name": "pi", "os": "linux", "arch": "aarch64", "codeanvil_version": "0.7.5",
                   "device_id": "synthetic-device", "driver": "synthetic"},
        "deployment_sha256": SHA, "protocol_id": "PROTO-001",
        "oracle": {"id": "synthetic", "reference": 1, "unit": "V", "standard_uncertainty": 0.01,
                   "calibration_reference": "synthetic fixture, no real calibration"},
        "captures": [{"path": "capture.bin", "sha256": hashlib.sha256(raw).hexdigest()}],
        "measurements": [{"requirement_id": "SYS-RF-001", "raw": 1, "corrected": 1, "unit": "V",
                          "standard_uncertainty": 0.02, "correction_reference": "SyRS §4 row 1",
                          "tolerance_reference": "SyRS §5 row 1", "lower": 0.9, "upper": 1.1,
                          "result": "pass"}], "telemetry_path": "telemetry.jsonl",
    }
    path = tmp_path / "measurement.json"
    path.write_text(json.dumps(record))
    return path, record


def check(path):
    return VALIDATOR["validate"](path, target="pi", run_id="synthetic-001",
                                 deployment_sha256=SHA, codeanvil_version="0.7.5",
                                 not_before=REQUESTED_AT)


def test_cli_accepts_captured_record_without_setting_a_gate_verdict(captured):
    path, _ = captured
    result = subprocess.run([sys.executable, str(SCRIPT), str(path), "--target", "pi", "--run-id",
                             "synthetic-001", "--deployment-sha256", SHA, "--codeanvil-version", "0.7.5",
                             "--not-before", REQUESTED_AT],
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["verdict"] == "human review required"


@pytest.mark.parametrize("field,value", [("run_id", "old-run"), ("deployment_sha256", "b" * 64),
                                         ("level", "VL-1"), ("hal_mode", "mock-only"),
                                         ("finished_at", "2026-11-11T11:00:00Z")])
def test_refuses_stale_or_wrong_level_evidence(captured, field, value):
    path, record = captured
    record[field] = value
    path.write_text(json.dumps(record))
    with pytest.raises(ValueError):
        check(path)


@pytest.mark.parametrize("value", [float("nan"), float("inf"), True, "1.0"])
def test_refuses_nonmeasured_numeric_values(captured, value):
    path, record = captured
    record["measurements"][0]["corrected"] = value
    path.write_text(json.dumps(record))
    with pytest.raises(ValueError, match="finite number"):
        check(path)


def test_refuses_tampered_or_missing_capture(captured):
    path, _ = captured
    (path.parent / "capture.bin").write_bytes(b"modified")
    with pytest.raises(ValueError, match="digest mismatch"):
        check(path)


@pytest.mark.parametrize("capture_path", ["../outside.bin", "/tmp/outside.bin", "..\\outside.bin"])
def test_refuses_capture_path_escape(captured, capture_path):
    path, record = captured
    record["captures"][0]["path"] = capture_path
    path.write_text(json.dumps(record))
    with pytest.raises(ValueError, match="inside"):
        check(path)


def test_refuses_symlink_escape(captured, tmp_path):
    path, _ = captured
    outside = tmp_path.parent / (tmp_path.name + "-outside.bin")
    outside.write_bytes(b"outside")
    (tmp_path / "capture.bin").unlink()
    (tmp_path / "capture.bin").symlink_to(outside)
    with pytest.raises(ValueError, match="escapes"):
        check(path)


def test_failed_measurements_stay_failed_and_cannot_be_relabeled(captured):
    path, record = captured
    record["measurements"][0].update(corrected=2, result="fail")
    path.write_text(json.dumps(record))
    assert check(path)["measurements"][0]["result"] == "fail"
    record["measurements"][0]["result"] = "pass"
    path.write_text(json.dumps(record))
    with pytest.raises(ValueError, match="inconsistent"):
        check(path)


def test_duplicate_fields_cannot_hide_a_failed_result(captured):
    path, _ = captured
    path.write_text(path.read_text().replace('"result": "pass"', '"result":"fail","result":"pass"'))
    with pytest.raises(ValueError, match="duplicate JSON key"):
        check(path)


def test_old_capture_cannot_be_relabelled_as_a_fresh_g2_run(captured):
    path, record = captured
    record["started_at"] = "2026-11-10T12:00:00Z"
    record["finished_at"] = "2026-11-10T12:00:01Z"
    path.write_text(json.dumps(record))
    with pytest.raises(ValueError, match="predates"):
        check(path)


def test_empty_capture_cannot_establish_measurement_evidence(captured):
    path, record = captured
    (path.parent / "capture.bin").write_bytes(b"")
    record["captures"][0]["sha256"] = hashlib.sha256(b"").hexdigest()
    path.write_text(json.dumps(record))
    with pytest.raises(ValueError, match="nonempty"):
        check(path)


def test_scaffolded_validator_resolves_its_schema_and_rejects_tampering(captured, tmp_path):
    path, _ = captured
    project = scaffold_project("Measurement fixture", "proj", tmp_path)
    script = project / ".agents/skills/G2_adaptive_verification/scripts/validate_measurement.py"
    args = [sys.executable, str(script), str(path), "--target", "pi", "--run-id", "synthetic-001",
            "--deployment-sha256", SHA, "--codeanvil-version", "0.7.5", "--not-before", REQUESTED_AT]
    good = subprocess.run(args, capture_output=True, text=True, cwd=project)
    assert good.returncode == 0, good.stderr
    assert json.loads(good.stdout)["verdict"] == "human review required"

    (path.parent / "capture.bin").write_bytes(b"changed after fetch")
    bad = subprocess.run(args, capture_output=True, text=True, cwd=project)
    assert bad.returncode == 2
    assert "capture digest mismatch" in bad.stderr

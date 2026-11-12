"""`codeanvil telemetry`: the in-process telemetry collector."""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import importlib.util

import pytest



@pytest.fixture
def collector() -> list[str]:
    """The command prefix of the in-process collector: `codeanvil telemetry`."""
    return [sys.executable, "-m", "codeanvil", "telemetry"]


def _run(collector: list[str], output: Path, *extra: str, env_extra: dict | None = None):
    env = {key: value for key, value in os.environ.items() if key != "PYTHONPATH"}
    env.update(env_extra or {})
    return subprocess.run(
        [*collector, "--output", str(output),
         "--interval", "0.02", "--duration", "0.06", *extra],
        capture_output=True, text=True, env=env, timeout=60,
    )


def _needs_psutil():
    if importlib.util.find_spec("psutil") is None:
        pytest.skip("psutil is not installed")


def _lines(output: Path) -> list[dict]:
    return [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]


def test_telemetry_subcommand_exposes_sampling_and_durability_flags():
    from codeanvil.CLI.parser import argparser

    args = argparser(["telemetry", "--pid", "7", "--output", "o.jsonl", "--interval", "0.5",
                      "--duration", "3", "--counters", "c.json", "--fsync"])

    assert args.command == "telemetry"
    assert (args.pid, args.output, args.interval, args.duration, args.counters) == (
        7, Path("o.jsonl"), 0.5, 3.0, Path("c.json"))
    defaults = argparser(["telemetry"])
    assert (defaults.pid, defaults.output, defaults.interval, defaults.duration,
            defaults.counters) == (None, None, 1.0, 0.0, None)
    assert args.fsync is True and defaults.fsync is False


def test_collector_writes_json_lines_with_the_schema(collector, tmp_path):
    output = tmp_path / "run.jsonl"

    result = _run(collector, output)

    assert result.returncode == 0, result.stderr
    assert result.stdout == "" and result.stderr == ""
    lines = _lines(output)
    assert lines
    line = lines[0]
    assert line["collector"] == {"name": "vsil-telemetry", "version": "1.1.0"}
    assert datetime.fromisoformat(line["timestamp"]).tzinfo is not None
    assert isinstance(line["monotonic_s"], (int, float))
    assert line["measurement_source"] == "psutil"
    for key in ("system", "release", "machine", "python", "cpu_count", "device_model"):
        assert key in line["host"]
    assert "process" in line and "system" in line
    assert "temperature_c" in line
    assert "counters" in line


def test_collector_measures_cpu_and_memory_with_psutil(collector, tmp_path):
    if importlib.util.find_spec("psutil") is None:
        pytest.skip("psutil is not installed")
    output = tmp_path / "run.jsonl"

    result = _run(collector, output)

    assert result.returncode == 0, result.stderr
    line = _lines(output)[0]
    assert line["measurement_source"] == "psutil"
    assert isinstance(line["process"]["cpu_percent"], (int, float))
    assert isinstance(line["process"]["rss_bytes"], int)
    assert isinstance(line["system"]["cpu_percent"], (int, float))
    assert isinstance(line["system"]["memory_total_bytes"], int)


def test_collector_refuses_to_run_without_psutil(collector, tmp_path):
    """psutil is the only measurement source: no fallback readings, no file."""
    blocker = tmp_path / "blocker"
    blocker.mkdir()
    (blocker / "psutil.py").write_text('raise ImportError("blocked by the test")\n', encoding="utf-8")
    output = tmp_path / "run.jsonl"

    result = _run(collector, output, env_extra={"PYTHONPATH": str(blocker)})

    assert result.returncode == 2
    assert "psutil is not installed" in result.stderr
    assert "reinstall codeanvil" in result.stderr
    assert not output.exists()


def test_collector_default_output_goes_to_verification_telemetry(collector, tmp_path):
    _needs_psutil()
    env = {key: value for key, value in os.environ.items() if key != "PYTHONPATH"}

    result = subprocess.run(
        [*collector, "--interval", "0.02", "--duration", "0.04"],
        capture_output=True, text=True, env=env, timeout=60, cwd=tmp_path,
    )

    assert result.returncode == 0, result.stderr
    [run] = list((tmp_path / "verification" / "telemetry").glob("telemetry-*.jsonl"))
    assert _lines(run)


def test_collector_never_measures_itself(collector, tmp_path):
    _needs_psutil()
    output = tmp_path / "run.jsonl"

    result = _run(collector, output, "--pid", str(os.getpid()))

    assert result.returncode == 0, result.stderr
    # pytest has no other children here: the collector alone would make it 2.
    assert _lines(output)[0]["process"]["processes"] == 1


def test_collector_copies_application_counters_from_instrumentation(collector, tmp_path):
    counters = tmp_path / "counters.json"
    counters.write_text('{"dropped_buffers": 4, "queue_depth": 0, "scheduling_latency_ms": 1.5}',
                        encoding="utf-8")
    output = tmp_path / "run.jsonl"

    result = _run(collector, output, "--counters", str(counters))

    assert result.returncode == 0, result.stderr
    line = _lines(output)[0]
    assert line["counters"] == {"dropped_buffers": 4, "queue_depth": 0, "scheduling_latency_ms": 1.5}
    assert line["counters_source"] == str(counters)


def test_collector_reports_missing_counters_as_unavailable(collector, tmp_path):
    output = tmp_path / "run.jsonl"

    result = _run(collector, output, "--counters", str(tmp_path / "missing.json"))

    assert result.returncode == 0, result.stderr
    assert "unavailable" in _lines(output)[0]["counters"]


def test_collector_degrades_without_aborting_the_kit_on_unwritable_output(collector, tmp_path):
    target = tmp_path / "not-a-directory"
    target.write_text("", encoding="utf-8")

    result = _run(collector, target / "run.jsonl")

    assert result.returncode == 0
    assert result.stdout == ""
    assert "evidence unavailable" in result.stderr
    assert not (target / "run.jsonl").exists()


def test_collector_never_overwrites_existing_evidence(collector, tmp_path):
    output = tmp_path / "run.jsonl"
    previous = '{"original": true}\n'
    output.write_text(previous, encoding="utf-8")

    result = _run(collector, output)

    assert result.returncode == 0
    assert "evidence unavailable" in result.stderr
    assert output.read_text(encoding="utf-8") == previous


@pytest.mark.parametrize("fsync", [False, True])
def test_collector_syncs_only_when_requested(tmp_path, monkeypatch, fsync):
    from codeanvil.telemetry import collector as impl

    synced = []
    monkeypatch.setattr(impl.os, "fsync", lambda fd: synced.append(fd))
    monkeypatch.setattr(impl.signal, "signal", lambda *args: None)
    output = tmp_path / "run.jsonl"
    args = ["--output", str(output), "--interval", "0.001", "--duration", "0.003"]

    assert impl.main(args + (["--fsync"] if fsync else [])) == 0

    records = _lines(output)
    assert records
    assert len(synced) == (len(records) if fsync else 0)


def test_collector_reports_a_disk_failure_without_losing_prior_samples(tmp_path, monkeypatch, capsys):
    from codeanvil.telemetry import collector as impl

    output = tmp_path / "run.jsonl"
    monkeypatch.setattr(impl.signal, "signal", lambda *args: None)
    count = 0

    def fail_later(fd):
        nonlocal count
        count += 1
        if count == 2:
            raise OSError("No space left on device")

    monkeypatch.setattr(impl.os, "fsync", fail_later)

    assert impl.main(["--output", str(output), "--interval", "0.001", "--duration", "1", "--fsync"]) == 0
    assert len(_lines(output)) == 2
    assert "evidence incomplete" in capsys.readouterr().err


def test_evidence_reader_reports_only_a_torn_tail(tmp_path):
    from codeanvil.telemetry.evidence import read_jsonl

    output = tmp_path / "run.jsonl"
    output.write_bytes(b'{"sample":1}\n{"sample":2}\n{"sample":"\xe2\x82')
    evidence = read_jsonl(output)
    assert evidence.records == [{"sample": 1}, {"sample": 2}]
    assert evidence.truncated_tail is True
    output.write_bytes(b'{"sample":1}')
    assert read_jsonl(output).truncated_tail is False


@pytest.mark.parametrize("payload", [b"", b'{"sample":', b'bad\n{"sample":1}\n',
                                    b'{"sample":1}\nbad\n', b'[]\n', b'{}\n'])
def test_evidence_reader_rejects_empty_or_corrupt_evidence(tmp_path, payload):
    from codeanvil.telemetry.evidence import EvidenceError, read_jsonl

    output = tmp_path / "run.jsonl"
    output.write_bytes(payload)
    with pytest.raises(EvidenceError):
        read_jsonl(output)


def test_evidence_reader_rejects_missing_evidence(tmp_path):
    from codeanvil.telemetry.evidence import EvidenceError, read_jsonl

    with pytest.raises(EvidenceError, match="unavailable"):
        read_jsonl(tmp_path / "missing.jsonl")


def test_collector_rejects_a_nonpositive_interval(collector, tmp_path):
    result = _run(collector, tmp_path / "run.jsonl", "--interval", "0")

    assert result.returncode != 0
    assert "greater than 0" in result.stderr


def test_collector_measures_its_parent_tree_not_itself(collector, tmp_path):
    """Default root is the parent (here: pytest), so the collector's own
    near-idle process is never reported as the verification process."""
    _needs_psutil()
    output = tmp_path / "run.jsonl"

    result = _run(collector, output)

    assert result.returncode == 0, result.stderr
    process = _lines(output)[0]["process"]
    assert process["pid"] == os.getpid()
    assert process["processes"] >= 1


def test_collector_measures_the_tree_under_pid(collector, tmp_path):
    _needs_psutil()
    busy = subprocess.Popen(
        [sys.executable, "-c",
         "import subprocess,sys,time;"
         "c=subprocess.Popen([sys.executable,'-c','import time;time.sleep(30)']);"
         "end=time.time()+30\nwhile time.time()<end: pass"],
    )
    try:
        output = tmp_path / "run.jsonl"
        result = _run(collector, output, "--pid", str(busy.pid),
                      "--interval", "0.3", "--duration", "0.6")
    finally:
        for child in __import__("psutil").Process(busy.pid).children(recursive=True):
            child.kill()
        busy.kill()
        busy.wait()

    assert result.returncode == 0, result.stderr
    first = _lines(output)[0]["process"]
    assert first["pid"] == busy.pid
    assert first["processes"] == 2
    # A busy loop over a real interval is far from the 0.0 a near-zero delta gives.
    assert first["cpu_percent"] > 10


def test_collector_reports_non_utf8_counters_as_unavailable(collector, tmp_path):
    counters = tmp_path / "counters.json"
    counters.write_bytes(b'{"dropped_buffers": "\xff\xfe"}')
    output = tmp_path / "run.jsonl"

    result = _run(collector, output, "--counters", str(counters))

    assert result.returncode == 0, result.stderr
    assert "unavailable" in _lines(output)[0]["counters"]


def test_collector_keeps_the_interval_on_a_fixed_grid(collector, tmp_path):
    """Sampling time (sensor reads) must not stretch the interval."""
    _needs_psutil()
    output = tmp_path / "run.jsonl"

    result = _run(collector, output, "--interval", "0.2", "--duration", "2")

    assert result.returncode == 0, result.stderr
    stamps = [line["monotonic_s"] for line in _lines(output)]
    mean = (stamps[-1] - stamps[0]) / (len(stamps) - 1)
    assert abs(mean - 0.2) < 0.01, f"mean interval {mean:.4f} s"

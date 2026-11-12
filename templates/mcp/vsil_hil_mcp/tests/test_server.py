"""Server dispatch and observation tests; transports never reach hardware."""

import json
import shlex
import subprocess
from pathlib import Path

import pytest
import yaml

from vsil_hil_mcp import config, identity, server, transport


@pytest.fixture
def env(tmp_path, monkeypatch):
    home, root = tmp_path / "home", tmp_path / "project"
    home.mkdir()
    (root / ".codeanvil").mkdir(parents=True)
    (root / ".codeanvil/project.yaml").write_text(yaml.safe_dump({
        "name": "fixture", "targets": [{"name": "pi", "host": "fixture.invalid", "user": "codeanvil-agent",
        "workspace": "/home/codeanvil-agent/workspace", "port": 2222}]}))
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("VSIL_HIL_WORKSPACE", str(root))
    monkeypatch.setenv("VSIL_HIL_CODEANVIL_VERSION", "0.7.5")
    keys = config.ensure_key_dir("pi")
    for kind in ("exec", "deploy"):
        keys[kind].write_text("test-only private key")
    calls = []
    def fake_run(argv, **kwargs):
        calls.append(argv)
        return subprocess.CompletedProcess(argv, 0, stdout="raw á\n", stderr="raw warning\n")
    monkeypatch.setattr(subprocess, "run", fake_run)
    return root, keys, calls


@pytest.mark.parametrize("command", ["sudo apt install driver", "python3 metric.py", "verification/run.sh vl2",
                                     "export VALUE=1 && echo $VALUE"])
def test_normal_lab_operations_execute_without_a_vocabulary_gate(env, command):
    root, keys, calls = env
    result = json.loads(server.ssh_exec_cmd(command))
    assert result == {"stdout": "raw á\n", "stderr": "raw warning\n", "exit_code": 0}
    assert calls[0][-1] == command and str(keys["exec"]) in calls[0]
    assert "IdentityAgent=none" in calls[0]
    assert calls[0][calls[0].index("-p") + 1] == "2222"
    assert json.loads((root / ".codeanvil/hil/audit.log").read_text())["exit"] == 0


@pytest.mark.parametrize("command", ["sudo reboot", "systemctl status app", "rm -rf data", "sqlite3 live.db 'DELETE FROM x'"])
def test_destructive_operations_redirect_without_executing(env, command):
    root, _, calls = env
    result = json.loads(server.ssh_exec_cmd(command))
    assert result["status"] == "use_trusted" and result["command"] == command
    assert not calls
    assert json.loads((root / ".codeanvil/hil/audit.log").read_text())["exit"] is None


def test_trusted_runs_exact_command_and_preserves_failure(env, monkeypatch):
    root, _, calls = env
    raw = {"stdout": "partial\n", "stderr": "failed\n", "exit_code": 23}
    monkeypatch.setattr(transport, "ssh_run", lambda target, key, cmd: calls.append(cmd) or raw)
    assert json.loads(server.ssh_exec_cmd_trusted("sudo reboot")) == raw
    assert calls == ["sudo reboot"]
    assert json.loads((root / ".codeanvil/hil/audit.log").read_text())["exit"] == 23


def test_update_installs_explicit_tool_ref_with_existing_exec_key(env):
    root, keys, calls = env
    result = json.loads(server.init_codeanvil(source_ref="published-tool-commit"))
    assert result["exit_code"] == 0
    command = calls[0][-1]
    assert "codeanvil-gcpds.git@published-tool-commit" in command
    assert "codeanvil telemetry --help" in command and "codeanvil now --machine" in command
    assert str(keys["exec"]) in calls[0] and calls[0][0] == "ssh"
    assert not any(call[0] == "ssh-keygen" for call in calls)
    assert json.loads((root / ".codeanvil/hil/audit.log").read_text())["tool"] == "init_codeanvil"


def test_update_requires_a_tool_source_not_a_guessed_version(env):
    _, _, calls = env
    with pytest.raises(ValueError, match="published"):
        server.init_codeanvil()
    assert not calls


def test_missing_key_names_the_one_time_enrollment(env):
    _, keys, calls = env
    keys["exec"].unlink()
    with pytest.raises(config.ConfigError, match="credential-setup"):
        server.ssh_exec_cmd("uname -a")
    assert not calls


def test_fetch_returns_fresh_snapshots_and_keeps_receiver_paths(env):
    root, _, calls = env
    results = [json.loads(server.fetch_evidence()) for _ in range(2)]
    paths = [Path(result["local_path"]) for result in results]
    assert paths[0] != paths[1]
    for path, argv in zip(paths, calls):
        assert path.parent == root / "verification/telemetry/pi"
        assert argv[-1] == f"{path}/"
        assert argv[-2].endswith(":/home/codeanvil-agent/workspace/verification/telemetry/")


def test_code_sync_uses_deploy_key_and_reports_published_revision(env, monkeypatch):
    root, keys, calls = env
    def push(target, key, directory):
        calls.append((target, key, directory))
        return {"stdout": "deployed", "stderr": "", "exit_code": 0, "revision": "published"}
    monkeypatch.setattr(transport, "rsync_push", push)
    assert json.loads(server.code_sync())["revision"] == "published"
    assert calls[0][1:] == (keys["deploy"], root)


def test_adopted_legacy_keys_resolve_through_mac_identity(env, monkeypatch):
    root, keys, calls = env
    device_id, _ = identity.remember_device(["02:00:00:00:00:01"], "fixture.invalid", 2222, "pi", key_identity="pi")
    path = root / ".codeanvil/project.yaml"
    data = yaml.safe_load(path.read_text())
    data["targets"][0].update(device_id=device_id, mac_addresses=["02:00:00:00:00:01"],
                              deploy_root="/home/codeanvil-agent/projects", workspace="/home/codeanvil-agent/projects/project-uuid")
    path.write_text(yaml.safe_dump(data))
    server.ssh_exec_cmd("uname -a")
    assert str(keys["exec"]) in calls[0]
    assert "UserKnownHostsFile=" + str(keys["known_hosts"]) in calls[0]
    used = []
    monkeypatch.setattr(transport, "rsync_push", lambda target, key, directory: used.append(key) or
                        {"stdout": "", "stderr": "", "exit_code": 0, "revision": "published"})
    server.code_sync()
    assert used == [keys["exec"]]  # old deploy confinement remains usable by old projects


@pytest.mark.parametrize("version,matched", [("codeanvil 0.7.5", True), ("codeanvil 0.8.0.dev1", False), ("", False)])
def test_probe_versions_are_observed_diagnostics_not_a_gate(env, monkeypatch, version, matched):
    text = f"VSIL_OS=Linux\nVSIL_ARCH=aarch64\nVSIL_CODEANVIL={version}\nVSIL_USB_AVAILABLE=yes\nVSIL_USB_BEGIN\nUSB fixture\n"
    raw = {"stdout": text, "stderr": "", "exit_code": 0}
    monkeypatch.setattr(transport, "ssh_run", lambda *args: raw)
    result = json.loads(server.probe_target())
    assert result["stdout"] == text and result["exit_code"] == 0
    assert result["metadata"]["version_match"] is matched
    assert result["metadata"]["codeanvil_version"] == (version.removeprefix("codeanvil ") or None)


def test_probe_works_without_host_version_configuration(env, monkeypatch):
    monkeypatch.delenv("VSIL_HIL_CODEANVIL_VERSION")
    result = json.loads(server.probe_target())
    assert result["metadata"]["expected_version"] is None
    assert result["exit_code"] == 0


@pytest.mark.parametrize("field,value", [("port", 0), ("port", True), ("workspace", "../bad"), ("os", "bare-metal")])
def test_invalid_target_fields_fail_before_ssh(env, field, value):
    root, _, calls = env
    path = root / ".codeanvil/project.yaml"
    data = yaml.safe_load(path.read_text())
    data["targets"][0][field] = value
    path.write_text(yaml.safe_dump(data))
    with pytest.raises(config.ConfigError):
        server.ssh_exec_cmd("uname -a")
    assert not calls


def test_unsupported_windows_target_fails_before_ssh(env):
    root, _, calls = env
    path = root / ".codeanvil/project.yaml"
    data = yaml.safe_load(path.read_text())
    data["targets"][0]["os"] = "windows"
    path.write_text(yaml.safe_dump(data))
    with pytest.raises(config.ConfigError, match="Linux"):
        server.ssh_exec_cmd("uname -a")
    assert not calls

import json
import os
import shlex
import stat
import subprocess

import pytest
import yaml

from vsil_hil_mcp import classifier, config, server, transport

PUB = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAItestkey{n} vsil-hil-{k}-pi"


@pytest.fixture
def env(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    root = tmp_path / "proj"
    (root / ".codeanvil").mkdir(parents=True)
    (root / ".codeanvil" / "project.yaml").write_text(yaml.safe_dump({
        "name": "p",
        "targets": [{"name": "pi", "host": "10.0.0.5", "user": "hil",
                     "workspace": "/home/hil/ws", "device": "rtlsdr"}],
    }))
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("VSIL_HIL_WORKSPACE", str(root))
    monkeypatch.setenv("VSIL_HIL_CODEANVIL_VERSION", "0.7.5")
    calls = []

    def fake_run(argv, **kw):
        calls.append(argv)
        assert isinstance(argv, list) and not kw.get("shell")
        if argv[0] == "ssh-keygen":
            path = argv[argv.index("-f") + 1]
            n = "d" if "deploy" in path else "e"
            open(path, "w").write("PRIVATE")
            open(path + ".pub", "w").write(PUB.format(n=n, k="deploy" if n == "d" else "exec") + "\n")
        return subprocess.CompletedProcess(argv, 0, stdout="out", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    return root, home, calls


def _keys(home, name="pi"):
    d = home / ".codeanvil-config" / "hil" / name
    return d, d / "deploy_ed25519", d / "exec_ed25519"


def test_classifier():
    assert classifier.classify("sudo apt install x") == classifier.PRIVILEGED
    assert classifier.classify("ls -l && sudo reboot") == classifier.PRIVILEGED
    assert classifier.classify("cat /etc/sudoers") == classifier.ALLOW
    assert classifier.classify("uname -a") == classifier.ALLOW


def test_exec_bounces_sudo_without_subprocess(env):
    root, _, calls = env
    out = json.loads(server.ssh_exec_cmd("sudo reboot"))
    assert out["status"] == "use_trusted" and out["command"] == "sudo reboot"
    assert calls == []
    assert '"exit": null' in (root / ".codeanvil/hil/audit.log").read_text()


def test_exec_uses_exec_key_and_audits(env):
    root, home, calls = env
    server.init_codeanvil("pi")
    calls.clear()
    out = json.loads(server.ssh_exec_cmd("uname -a"))
    assert out["exit_code"] == 0
    argv = calls[0]
    assert argv[0] == "ssh" and str(_keys(home)[2]) in argv and argv[-1] == "uname -a"
    assert "hil@10.0.0.5" in argv and "IdentitiesOnly=yes" in argv
    assert "uname -a" in (root / ".codeanvil/hil/audit.log").read_text()


def test_trusted_runs_sudo_with_exec_key(env):
    _, home, calls = env
    server.init_codeanvil("pi")
    calls.clear()
    server.ssh_exec_cmd_trusted("sudo apt-get install -y rtl-sdr")
    assert calls[0][0] == "ssh" and str(_keys(home)[2]) in calls[0]
    assert calls[0][-1] == "sudo apt-get install -y rtl-sdr"


def test_code_sync_separate_excludes_and_deploy_key(env):
    root, home, calls = env
    server.init_codeanvil("pi")
    calls.clear()
    server.code_sync()
    argv = calls[0]
    assert argv[0] == "rsync" and "--delete" in argv
    for e in (".git", "__pycache__", "*.pyc", "verification/telemetry/", ".env", "*.key", "*.pem"):
        assert f"--exclude={e}" in argv
    assert str(_keys(home)[1]) in argv[argv.index("-e") + 1]
    # rrsync -wo roots the deploy key at the workspace, so the dest is the root
    # (empty path), not the absolute workspace path (verified on a real target).
    assert argv[-2] == f"{root}/" and argv[-1] == "hil@10.0.0.5:"


def test_fetch_pulls_only_telemetry(env):
    root, _, calls = env
    server.init_codeanvil("pi")
    calls.clear()
    server.fetch_evidence()
    argv = calls[0]
    assert argv[-2] == "hil@10.0.0.5:/home/hil/ws/verification/telemetry/"
    assert argv[-1] == f"{root}/verification/telemetry/"
    assert not any(a.startswith("--exclude") for a in argv)


def test_init_script_keys_and_perms(env):
    root, home, calls = env
    text = server.init_codeanvil("pi")
    assert "AAAAC3NzaC1lZDI1NTE5AAAAItestkeyd" in text and "AAAAC3NzaC1lZDI1NTE5AAAAItestkeye" in text
    assert 'command=\\"$RRSYNC -wo $HIL_WS\\",restrict' in text
    d, dep, ex = _keys(home)
    assert stat.S_IMODE(d.stat().st_mode) == 0o700
    assert stat.S_IMODE(dep.stat().st_mode) == 0o600 and stat.S_IMODE(ex.stat().st_mode) == 0o600
    kg = [c for c in calls if c[0] == "ssh-keygen"]
    assert kg[0][:7] == ["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-C"]
    assert all(c[0] == "ssh-keygen" for c in calls)  # no ssh during init


def test_init_registers_new_target(env):
    root, *_ = env
    server.init_codeanvil("lab", host="192.168.1.9", device="hackrf")
    names = [t["name"] for t in yaml.safe_load((root / ".codeanvil/project.yaml").read_text())["targets"]]
    assert names == ["pi", "lab"]
    with pytest.raises(config.ConfigError):
        server.ssh_exec_cmd("ls")  # two targets now: must name one


@pytest.mark.parametrize("field,value", [
    ("host", "-oProxyCommand=x"), ("user", "a b"), ("workspace", "/x;rm -rf /"), ("workspace", "rel"),
])
def test_bad_target_fields_refused(env, field, value):
    kw = {"host": "h", "user": "u", "workspace": "/w", field: value}
    with pytest.raises(config.ConfigError):
        server.init_codeanvil("new", **kw)


@pytest.mark.parametrize("policy", ["guarded", "locked"])
def test_non_trusted_policies_not_implemented(env, policy):
    root, *_ = env
    p = root / ".codeanvil/project.yaml"
    data = yaml.safe_load(p.read_text())
    data["targets"][0]["hil_policy"] = policy
    p.write_text(yaml.safe_dump(data))
    for call in (lambda: server.ssh_exec_cmd("ls"), lambda: server.ssh_exec_cmd_trusted("ls"),
                 server.code_sync, server.fetch_evidence, lambda: server.init_codeanvil("pi")):
        with pytest.raises(NotImplementedError, match="guarded/locked"):
            call()


def test_exec_without_keys_fails_clearly(env):
    with pytest.raises(config.ConfigError, match="init_codeanvil"):
        server.ssh_exec_cmd("ls")


def test_port_and_personal_identity_isolation(env):
    root, home, calls = env
    p = root / ".codeanvil/project.yaml"
    data = yaml.safe_load(p.read_text())
    data["targets"][0]["port"] = 2222
    p.write_text(yaml.safe_dump(data))
    server.init_codeanvil("pi")
    calls.clear()
    server.ssh_exec_cmd("uname -a")
    server.code_sync()
    server.fetch_evidence()
    assert config.resolve_target("pi").port == 2222
    for argv in calls:
        ssh = argv if argv[0] == "ssh" else shlex.split(argv[argv.index("-e") + 1])
        assert ssh[ssh.index("-p") + 1] == "2222"
        assert ssh[ssh.index("-F") + 1] == os.devnull
        assert "IdentityAgent=none" in ssh and "IdentitiesOnly=yes" in ssh


@pytest.mark.parametrize("port", [0, 65536, True, "22"])
def test_bad_declared_port_refused(env, port):
    root, _, calls = env
    p = root / ".codeanvil/project.yaml"
    data = yaml.safe_load(p.read_text())
    data["targets"][0]["port"] = port
    p.write_text(yaml.safe_dump(data))
    with pytest.raises(config.ConfigError, match="port"):
        server.init_codeanvil("pi")
    assert not calls


def test_duplicate_target_name_refused(env):
    root, _, calls = env
    p = root / ".codeanvil/project.yaml"
    data = yaml.safe_load(p.read_text())
    data["targets"].append(dict(data["targets"][0], host="other"))
    p.write_text(yaml.safe_dump(data))
    with pytest.raises(config.ConfigError, match="duplicate"):
        server.init_codeanvil("pi")
    assert not calls


def test_windows_execution_refused_and_unknown_os_invalid(env):
    root, _, calls = env
    p = root / ".codeanvil/project.yaml"
    data = yaml.safe_load(p.read_text())
    data["targets"][0]["os"] = "windows"
    p.write_text(yaml.safe_dump(data))
    with pytest.raises(config.ConfigError, match="Linux targets only"):
        server.ssh_exec_cmd("uname -a")
    with pytest.raises(config.ConfigError, match="Linux targets only"):
        server.init_codeanvil("pi")
    assert not calls
    with pytest.raises(config.ConfigError, match="unsupported target OS"):
        server.init_codeanvil("new", host="host", user="agent", os="bare-metal")


def test_provisioning_pins_host_release_and_fixes_new_user(env):
    root, _, _ = env
    script = server.init_codeanvil("new", host="newbox", port=2222)
    assert "CODEANVIL_VERSION=0.7.5" in script
    assert "codeanvil-gcpds.git@v$CODEANVIL_VERSION" in script
    assert "main/install.sh" not in script
    assert 'codeanvil --version)' in script and "CodeAnvil version mismatch" in script
    assert config.resolve_target("new").user == "codeanvil-agent"
    with pytest.raises(config.ConfigError, match="fixed codeanvil-agent"):
        server.init_codeanvil("other", host="otherbox", user="someone")


@pytest.mark.parametrize("value", [None, "0.7.5;reboot", "0.7.5.dev0"])
def test_provisioning_without_a_valid_host_release_never_generates_keys(env, monkeypatch, value):
    root, _, calls = env
    if value is None:
        monkeypatch.delenv("VSIL_HIL_CODEANVIL_VERSION")
    else:
        monkeypatch.setenv("VSIL_HIL_CODEANVIL_VERSION", value)
    with pytest.raises(config.ConfigError, match="version"):
        server.init_codeanvil("new", host="newbox")
    assert not calls
    assert "new" not in config.load_targets(root)


@pytest.mark.parametrize("version,exit_code,matched", [
    ("codeanvil 0.7.5", 0, True), ("codeanvil 0.7.4", 0, False),
    ("", 1, False), ("unknown", 0, False),
])
def test_probe_reports_observed_parity_without_inventing_device_detection(env, monkeypatch, version, exit_code, matched):
    root, _, calls = env
    server.init_codeanvil("pi")
    stdout = f"VSIL_OS=Linux\nVSIL_ARCH=aarch64\nVSIL_CODEANVIL={version}\nVSIL_USB_AVAILABLE=yes\nVSIL_USB_BEGIN\nBus 001 Device 001: controller\n"
    raw = {"stdout": stdout, "stderr": "raw stderr", "exit_code": exit_code}
    monkeypatch.setattr(transport, "ssh_run", lambda *args: raw)
    result = json.loads(server.probe_target("pi"))
    assert all(result[key] == value for key, value in raw.items())
    metadata = result["metadata"]
    assert metadata["version_match"] is matched
    assert metadata["os"] == "Linux" and metadata["arch"] == "aarch64"
    assert metadata["declared_device"] == "rtlsdr"
    assert metadata["usb_devices"] == "Bus 001 Device 001: controller"
    assert '"tool": "probe_target"' in (root / ".codeanvil/hil/audit.log").read_text()


def test_probe_without_usb_or_remote_observations_is_explicit(env, monkeypatch):
    server.init_codeanvil("pi")
    monkeypatch.setattr(transport, "ssh_run", lambda *args: {"stdout": "", "stderr": "SSH failed", "exit_code": 255})
    result = json.loads(server.probe_target())
    assert result["metadata"]["codeanvil_version"] is None
    assert result["metadata"]["os"] is None
    assert result["metadata"]["version_match"] is False
    assert result["metadata"]["usb_probe_available"] is False


def test_pinned_provisioning_script_is_valid_bash(env):
    server.init_codeanvil("pi")
    target = config.resolve_target("pi")
    from vsil_hil_mcp.provision import render_script
    script = render_script(target, PUB.format(n="d", k="deploy"), PUB.format(n="e", k="exec"), "0.7.5")
    # Popen is real: check generated shell syntax without executing the script.
    result = subprocess.Popen(["bash", "-n"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    _, stderr = result.communicate(script.encode(), timeout=5)
    assert result.returncode == 0, stderr.decode()

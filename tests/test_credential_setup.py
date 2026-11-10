"""Tests for `codeanvil credential-setup` — subprocess is always mocked."""

import argparse

import pytest
import yaml

from codeanvil.CLI.commands import credential_setup as mod
from codeanvil.CLI.commands.credential_setup import AGENT_USER, cmd_credential_setup

PASSWORD = "s3cr3t-pw"


@pytest.fixture()
def project_dir(tmp_path, monkeypatch):
    (tmp_path / ".codeanvil").mkdir()
    (tmp_path / ".codeanvil" / "project.yaml").write_text(
        "id: 0193-test\nname: demo\n", encoding="utf-8"
    )
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.chdir(tmp_path)
    return tmp_path


def _capture(monkeypatch, returncode=0):
    calls = []

    def fake_run(cmd, **kw):
        calls.append((cmd, kw))
        return argparse.Namespace(returncode=returncode)

    monkeypatch.setattr(mod.subprocess, "run", fake_run)
    return calls


def _targets(project_dir):
    return yaml.safe_load((project_dir / ".codeanvil" / "project.yaml").read_text())


def test_agent_user_is_fixed():
    assert AGENT_USER == "codeanvil-agent"


def test_rejects_outside_project(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    calls = _capture(monkeypatch)
    with pytest.raises(SystemExit) as exc:
        cmd_credential_setup("u", "10.0.0.5", password=PASSWORD)
    assert exc.value.code == 1
    assert calls == []


def test_rejects_invalid_target_name(project_dir, monkeypatch):
    calls = _capture(monkeypatch)
    with pytest.raises(SystemExit):
        cmd_credential_setup("u", "10.0.0.5", password=PASSWORD, target="bad name!")
    assert calls == []


def test_linux_runs_script_password_via_env_only(project_dir, monkeypatch, caplog):
    calls = _capture(monkeypatch)
    cmd_credential_setup("pepito", "10.0.0.5", password=PASSWORD)
    (cmd, kw), = calls
    assert cmd[0] == "bash"
    assert cmd[1].endswith("setup_credentials_ssh_hil.sh")
    assert cmd[cmd.index("-t") + 1] == "10_0_0_5"
    assert cmd[cmd.index("-u") + 1] == "pepito"
    assert cmd[cmd.index("-a") + 1] == "codeanvil-agent"  # always
    assert not any(PASSWORD in part for part in cmd)
    assert "-p" not in cmd
    assert kw["env"][mod.PASSWORD_ENV] == PASSWORD
    assert kw["env"][mod.SUDO_PASSWORD_ENV] == PASSWORD  # default: reuse
    assert PASSWORD not in caplog.text


def test_registers_target_with_fixed_agent_user(project_dir, monkeypatch):
    _capture(monkeypatch)
    cmd_credential_setup("u", "10.0.0.5", password=PASSWORD)
    data = _targets(project_dir)
    assert data["name"] == "demo"  # rest of the file preserved
    assert data["targets"] == [{
        "name": "10_0_0_5", "host": "10.0.0.5", "user": "codeanvil-agent",
        "workspace": "/home/codeanvil-agent/workspace", "os": "linux", "hil_policy": "trusted",
    }]


def test_idempotent_rerun(project_dir, monkeypatch):
    _capture(monkeypatch)
    cmd_credential_setup("u", "10.0.0.5", password=PASSWORD)
    cmd_credential_setup("u", "10.0.0.5", password=PASSWORD)
    assert len(_targets(project_dir)["targets"]) == 1


def test_script_failure_does_not_register(project_dir, monkeypatch):
    _capture(monkeypatch, returncode=3)
    with pytest.raises(SystemExit) as exc:
        cmd_credential_setup("u", "10.0.0.5", password=PASSWORD)
    assert exc.value.code == 1
    assert "targets" not in _targets(project_dir)


def test_prompts_when_no_password(project_dir, monkeypatch):
    calls = _capture(monkeypatch)
    answers = iter(["login-pw", ""])  # SSH password, then Enter (reuse for sudo)
    monkeypatch.setattr(mod.getpass, "getpass", lambda *a, **k: next(answers))
    cmd_credential_setup("u", "10.0.0.5")
    (_, kw), = calls
    assert kw["env"][mod.PASSWORD_ENV] == "login-pw"
    assert kw["env"][mod.SUDO_PASSWORD_ENV] == "login-pw"


def test_separate_sudo_password(project_dir, monkeypatch):
    calls = _capture(monkeypatch)
    cmd_credential_setup("u", "10.0.0.5", password=PASSWORD, sudo_password="sudo-pw")
    (_, kw), = calls
    assert kw["env"][mod.PASSWORD_ENV] == PASSWORD
    assert kw["env"][mod.SUDO_PASSWORD_ENV] == "sudo-pw"


def test_windows_prints_instructions_and_registers(project_dir, monkeypatch, caplog):
    calls = _capture(monkeypatch)
    caplog.set_level("INFO")
    cmd_credential_setup("u", "win-box", password=PASSWORD, os_="windows")
    assert not any(c[0][0] == "bash" for c in calls)
    assert all(c[0][0] == "ssh-keygen" for c in calls)
    assert "setup_credentials_ssh_hil.ps1" in caplog.text
    assert "deploy_ed25519.pub" in caplog.text
    assert PASSWORD not in caplog.text
    row = _targets(project_dir)["targets"][0]
    assert row["os"] == "windows" and row["user"] == "codeanvil-agent"


def test_parser_optional_password_and_ip_alias():
    from codeanvil.CLI.parser import build_parser

    ns = build_parser().parse_args(["credential-setup", "-u", "p", "-ip", "0.0.0.0"])
    assert ns.ip == "0.0.0.0" and ns.password is None and ns.sudo_password is None
    assert ns.os == "linux" and ns.port == 22
    assert not hasattr(ns, "agent_user")

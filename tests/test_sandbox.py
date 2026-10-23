"""Tests for `codeanvil sandbox` — agent-isolated methodology execution.

The sandbox launches an AI coding agent inside a scaffolded project with
only project-local settings visible. These tests never launch a real agent:
subprocess.run and shutil.which are mocked so only command construction,
strategy dispatch, and temp-dir lifecycle are verified.
"""

import argparse
from pathlib import Path

import pytest

from codeanvil.CLI.commands import sandbox as sandbox_mod
from codeanvil.CLI.commands.sandbox import cmd_sandbox


@pytest.fixture()
def project_dir(tmp_path, monkeypatch):
    """A minimal scaffolded project (manifest present) as cwd."""
    (tmp_path / ".codeanvil").mkdir()
    (tmp_path / ".codeanvil" / "project.yaml").write_text(
        "id: 0193-test\ntest-project\n", encoding="utf-8"
    )
    monkeypatch.chdir(tmp_path)
    return tmp_path


@pytest.fixture()
def fake_home(tmp_path, monkeypatch):
    """HOME pointed at an empty dir so agent-config lookups are isolated."""
    home = tmp_path / "fake-home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    return home


def _fake_run(captured):
    """Replacement for subprocess.run that records the invocation."""

    def fake_run(cmd, **kwargs):
        captured["cmd"] = cmd
        captured["env"] = kwargs.get("env")
        sandbox_dir = (kwargs.get("env") or {}).get("XDG_CONFIG_HOME") or (
            kwargs.get("env") or {}
        ).get("CODEX_HOME")
        if sandbox_dir:
            captured["sandbox_dir_exists_during_run"] = Path(sandbox_dir).is_dir()
        return argparse.Namespace(returncode=0)

    return fake_run


def _patch_agent_launch(monkeypatch, captured):
    monkeypatch.setattr(sandbox_mod.subprocess, "run", _fake_run(captured))
    monkeypatch.setattr(
        sandbox_mod.shutil, "which", lambda name: f"/usr/bin/{name}"
    )


def test_sandbox_rejects_outside_project(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit) as exc:
        cmd_sandbox("claude")
    assert exc.value.code == 1


def test_sandbox_rejects_unknown_agent(project_dir):
    with pytest.raises(SystemExit) as exc:
        cmd_sandbox("foo")
    assert exc.value.code != 0


def test_sandbox_unknown_agent_rejected_by_parser():
    from codeanvil.CLI.parser import build_parser

    with pytest.raises(SystemExit):
        build_parser().parse_args(["sandbox", "foo"])


def test_sandbox_requires_agent_binary(project_dir, monkeypatch):
    monkeypatch.setattr(sandbox_mod.shutil, "which", lambda name: None)
    with pytest.raises(SystemExit) as exc:
        cmd_sandbox("claude")
    assert exc.value.code == 1


def test_sandbox_subcommand_in_help():
    from codeanvil.CLI.parser import build_parser

    help_text = build_parser().format_help()
    assert "sandbox" in help_text


def test_sandbox_claude_uses_native_flags():
    spec = sandbox_mod.SANDBOX_AGENTS["claude"]
    cmd = sandbox_mod._build_command(spec)
    assert cmd[0] == "claude"
    assert "--setting-sources" in cmd
    assert "project" in cmd


def test_sandbox_claude_launches_isolated_command(project_dir, monkeypatch):
    captured = {}
    _patch_agent_launch(monkeypatch, captured)
    with pytest.raises(SystemExit) as exc:
        cmd_sandbox("claude")
    assert exc.value.code == 0
    assert captured["cmd"] == ["claude", "--setting-sources", "project"]
    assert captured["env"] is None  # native strategy passes no env override


def test_sandbox_opencode_creates_temp_dir(project_dir, monkeypatch):
    captured = {}
    _patch_agent_launch(monkeypatch, captured)
    with pytest.raises(SystemExit) as exc:
        cmd_sandbox("opencode")
    assert exc.value.code == 0
    assert captured["cmd"] == ["opencode", "--standalone"]
    assert captured["env"]["XDG_CONFIG_HOME"]
    # temp dir existed during the run and is gone after cleanup
    assert captured["sandbox_dir_exists_during_run"] is True
    assert not Path(captured["env"]["XDG_CONFIG_HOME"]).exists()


def test_sandbox_pi_reenables_required_extension(project_dir, fake_home):
    entry = (
        fake_home / ".pi/agent/npm/node_modules/pi-claude-bridge/src/index.ts"
    )
    entry.parent.mkdir(parents=True)
    entry.write_text("", encoding="utf-8")

    spec = sandbox_mod.SANDBOX_AGENTS["pi"]
    cmd = sandbox_mod._build_command(spec)
    assert "--no-extensions" in cmd
    assert "--no-skills" in cmd
    assert "--no-context-files" not in cmd  # AGENTS.md discovery stays ON
    assert "-e" in cmd
    assert str(entry) in cmd


def test_sandbox_pi_missing_required_extension_errors(project_dir, fake_home):
    spec = sandbox_mod.SANDBOX_AGENTS["pi"]
    with pytest.raises(SystemExit) as exc:
        sandbox_mod._build_command(spec)
    assert exc.value.code == 1


def test_sandbox_codex_copies_auth_files(project_dir, fake_home, monkeypatch):
    codex_dir = fake_home / ".codex"
    codex_dir.mkdir()
    (codex_dir / "installation_id").write_text("inst-123", encoding="utf-8")

    captured = {}
    monkeypatch.setattr(sandbox_mod.subprocess, "run", _fake_run(captured))
    monkeypatch.setattr(
        sandbox_mod.shutil, "which", lambda name: f"/usr/bin/{name}"
    )
    with pytest.raises(SystemExit) as exc:
        cmd_sandbox("codex")
    assert exc.value.code == 0
    assert captured["cmd"] == ["codex", "--no-daemon"]
    assert captured["env"]["CODEX_HOME"]
    sandbox_dir = Path(captured["env"]["CODEX_HOME"])
    assert captured["sandbox_dir_exists_during_run"] is True
    assert not sandbox_dir.exists()  # cleaned up after exit


def test_sandbox_codex_copies_only_auth_files(project_dir, fake_home, monkeypatch):
    codex_dir = fake_home / ".codex"
    codex_dir.mkdir()
    (codex_dir / "installation_id").write_text("inst-123", encoding="utf-8")
    (codex_dir / "config.toml").write_text("model = 'x'", encoding="utf-8")
    (codex_dir / "AGENTS.md").write_text("# global", encoding="utf-8")

    copied = {}

    def fake_run(cmd, **kwargs):
        sandbox_dir = Path(kwargs["env"]["CODEX_HOME"])
        copied["entries"] = sorted(p.name for p in sandbox_dir.iterdir())
        return argparse.Namespace(returncode=0)

    monkeypatch.setattr(sandbox_mod.subprocess, "run", fake_run)
    monkeypatch.setattr(
        sandbox_mod.shutil, "which", lambda name: f"/usr/bin/{name}"
    )
    with pytest.raises(SystemExit):
        cmd_sandbox("codex")
    assert copied["entries"] == ["installation_id"]  # config.toml/AGENTS.md never copied


def test_sandbox_exits_with_agent_exit_code(project_dir, monkeypatch):
    monkeypatch.setattr(sandbox_mod.shutil, "which", lambda name: "/usr/bin/x")
    monkeypatch.setattr(
        sandbox_mod.subprocess,
        "run",
        lambda cmd, **kwargs: argparse.Namespace(returncode=42),
    )
    with pytest.raises(SystemExit) as exc:
        cmd_sandbox("claude")
    assert exc.value.code == 42

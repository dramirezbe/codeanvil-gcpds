"""Sandbox launch recipes shared by the CLI and interactive UI terminal."""

import os
from contextlib import nullcontext
from pathlib import Path

import pytest

from codeanvil import sandbox


@pytest.fixture()
def project(tmp_path, monkeypatch):
    root = tmp_path / "project"
    (root / ".codeanvil").mkdir(parents=True)
    (root / ".codeanvil/project.yaml").write_text("id: fake-project\n")
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setattr(sandbox.shutil, "which", lambda name: f"/bin/{name}")
    return root


def test_native_recipe_preserves_environment_and_project_mcp(project, monkeypatch):
    monkeypatch.setenv("CODEANVIL_TEST_VARIABLE", "unchanged")
    (project / ".mcp.json").write_text("{}")
    before = dict(os.environ)
    with sandbox.prepare_sandbox("claude", project) as launch:
        assert launch["argv"] == [
            "claude", "--setting-sources", "project", "--strict-mcp-config",
            "--mcp-config", str(project / ".mcp.json"),
        ]
        assert launch["env"] == before
        launch["env"]["CODEANVIL_TEST_VARIABLE"] = "child only"
        assert os.environ == before
    assert os.environ == before


@pytest.mark.parametrize("error", [False, True])
def test_redirect_lives_until_context_exit_and_cleans_up(project, error):
    before = dict(os.environ)
    with pytest.raises(RuntimeError) if error else nullcontext():
        with sandbox.prepare_sandbox("opencode", project) as launch:
            directory = Path(launch["env"]["XDG_CONFIG_HOME"])
            assert directory.is_dir()
            assert list(directory.iterdir()) == []
            assert launch["argv"] == ["opencode", "--standalone"]
            assert os.environ == before
            if error:
                raise RuntimeError("process failed")
    assert not directory.exists()
    assert os.environ == before


def test_redirect_seeds_only_recipe_auth_files(project):
    source = Path.home() / ".codex"
    source.mkdir()
    (source / "installation_id").write_text("fake-identity")
    (source / "config.toml").write_text("model = 'global-config'")
    (source / "skills").mkdir()
    with sandbox.prepare_sandbox("codex", project) as launch:
        directory = Path(launch["env"]["CODEX_HOME"])
        assert launch["argv"] == ["codex", "--no-daemon"]
        assert sorted(item.name for item in directory.iterdir()) == ["installation_id"]
        assert (directory / "installation_id").read_text() == "fake-identity"
    assert not directory.exists()
    assert (source / "installation_id").read_text() == "fake-identity"
    assert (source / "config.toml").is_file()


def test_missing_extension_raises_library_error(project):
    with pytest.raises(sandbox.SandboxError, match="required extension"):
        with sandbox.prepare_sandbox("pi", project):
            pytest.fail("must not launch without the required extension")


@pytest.mark.parametrize("agent", ["unknown", "claude"])
def test_invalid_agent_or_missing_binary_raises_library_error(project, monkeypatch, agent):
    monkeypatch.setattr(sandbox.shutil, "which", lambda name: None)
    with pytest.raises(sandbox.SandboxError):
        with sandbox.prepare_sandbox(agent, project):
            pytest.fail("invalid launch must be rejected")


def test_missing_project_rejected(tmp_path):
    with pytest.raises(sandbox.SandboxError, match="project.yaml"):
        with sandbox.prepare_sandbox("claude", tmp_path):
            pytest.fail("project manifest is required")


def test_auth_copy_failure_cleans_temporary_directory(project, monkeypatch):
    created = []
    original = sandbox.tempfile.mkdtemp

    def record_directory(**kwargs):
        directory = original(**kwargs)
        created.append(Path(directory))
        return directory

    def fail_copy(*args):
        raise OSError("cannot read identity file")

    monkeypatch.setattr(sandbox.tempfile, "mkdtemp", record_directory)
    monkeypatch.setattr(sandbox, "_copy_auth_files", fail_copy)
    with pytest.raises(sandbox.SandboxError, match="cannot read identity file"):
        with sandbox.prepare_sandbox("codex", project):
            pytest.fail("failed preparation must not launch")
    assert len(created) == 1
    assert not created[0].exists()

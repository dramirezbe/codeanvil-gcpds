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
    monkeypatch.delenv("CODEX_HOME", raising=False)
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
    (source / "auth.json").write_text('{"tokens": {"access_token": "fake-token"}}')
    (source / "config.toml").write_text("model = 'global-config'")
    (source / "skills").mkdir()
    with sandbox.prepare_sandbox("codex", project) as launch:
        directory = Path(launch["env"]["CODEX_HOME"])
        assert launch["argv"] == ["codex", "--no-daemon"]
        assert sorted(item.name for item in directory.iterdir()) == ["auth.json", "installation_id"]
        assert (directory / "installation_id").read_text() == "fake-identity"
        assert (directory / "auth.json").read_bytes() == (source / "auth.json").read_bytes()
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


def test_codex_auth_uses_inherited_home_without_global_settings(project, tmp_path, monkeypatch):
    original = tmp_path / 'custom-codex'
    original.mkdir()
    (original / 'auth.json').write_text('{"tokens":{"access_token":"fake-custom"}}')
    (original / 'installation_id').write_text('custom-identity')
    (original / 'config.toml').write_text('model = "global-settings"')
    (original / 'AGENTS.md').write_text('global instructions')
    (original / 'sessions').mkdir()
    (original / 'skills').mkdir()
    monkeypatch.setenv('CODEX_HOME', str(original))
    before = dict(os.environ)
    with sandbox.prepare_sandbox('codex', project) as launch:
        temporary = Path(launch['env']['CODEX_HOME'])
        assert temporary != original
        assert sorted(p.name for p in temporary.iterdir()) == ['auth.json', 'installation_id']
        assert (temporary / 'auth.json').read_bytes() == (original / 'auth.json').read_bytes()
        assert (temporary / 'installation_id').read_text() == 'custom-identity'
        assert os.environ == before
    assert not temporary.exists()
    assert os.environ == before


@pytest.mark.skipif(os.name == 'nt', reason='POSIX permission bits')
def test_codex_auth_copy_is_private_even_if_source_is_permissive(project):
    from stat import S_IMODE
    source = Path.home() / '.codex'
    source.mkdir()
    auth = source / 'auth.json'
    auth.write_text('{"tokens":{"access_token":"fake-private"}}')
    auth.chmod(0o644)
    with sandbox.prepare_sandbox('codex', project) as launch:
        temporary = Path(launch['env']['CODEX_HOME'])
        assert S_IMODE(temporary.stat().st_mode) == 0o700
        assert S_IMODE((temporary / 'auth.json').stat().st_mode) == 0o600
    assert S_IMODE(auth.stat().st_mode) == 0o644


def test_codex_auth_snapshot_cleanup_does_not_modify_original(project):
    source = Path.home() / '.codex'
    source.mkdir()
    auth = source / 'auth.json'
    original = '{"tokens":{"access_token":"fake-original"}}'
    auth.write_text(original)
    with pytest.raises(RuntimeError, match='agent exited'):
        with sandbox.prepare_sandbox('codex', project) as launch:
            temporary = Path(launch['env']['CODEX_HOME'])
            (temporary / 'auth.json').write_text('{"tokens":{"access_token":"fake-changed"}}')
            raise RuntimeError('agent exited')
    assert not temporary.exists()
    assert auth.read_text() == original

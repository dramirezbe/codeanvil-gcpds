"""Published-candidate checks use temporary local Git remotes, never hardware."""

from pathlib import Path
import shutil
import subprocess

import pytest

from vsil_hil_mcp import config, transport

GIT = shutil.which('git')
pytestmark = pytest.mark.skipif(GIT is None, reason='requires Git')


def git(root, *args):
    result = subprocess.run([GIT, '-C', str(root), *args], capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


def commit(root, message='candidate'):
    git(root, 'add', '.')
    git(root, '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', message)


@pytest.fixture
def published(tmp_path):
    root, origin = tmp_path / 'project', tmp_path / 'origin.git'
    root.mkdir()
    git(root, 'init', '-q', '-b', 'main')
    (root / 'app.py').write_text('published code', encoding='utf-8')
    (root / '.gitignore').write_text('.env\nignored/\nverification/telemetry/\n', encoding='utf-8')
    commit(root)
    git(root, 'init', '--bare', '-q', str(origin))
    git(root, 'remote', 'add', 'origin', str(origin))
    git(root, 'push', '-qu', 'origin', 'main')
    return root, origin


def target():
    return config.Target('pi', 'fixture.invalid', 'codeanvil-agent', '/home/codeanvil-agent/workspace')


def test_export_deploys_only_committed_files_and_cleans_up(published, tmp_path, monkeypatch):
    root, _ = published
    (root / '.env').write_text('secret', encoding='utf-8')
    (root / 'ignored').mkdir()
    (root / 'ignored/host-only.txt').write_text('must never deploy', encoding='utf-8')
    sources = []

    def fake_rsync(argv):
        source = Path(argv[-2])
        sources.append(source)
        assert source != root
        assert (source / 'app.py').read_text() == 'published code'
        assert not (source / '.env').exists()
        assert not (source / 'ignored').exists()
        assert not (source / '.git').exists()
        return {'stdout': 'sent\n', 'stderr': '', 'exit_code': 0}

    monkeypatch.setattr(transport, '_run', fake_rsync)
    result = transport.rsync_push(target(), tmp_path / 'key', root)
    assert result == {'revision': git(root, 'rev-parse', 'HEAD'), 'stdout': 'sent\n', 'stderr': '', 'exit_code': 0}
    assert len(sources) == 1 and not sources[0].exists()


@pytest.mark.parametrize('state', ['untracked', 'unstaged', 'staged', 'ahead', 'no-upstream', 'detached', 'missing-remote'])
def test_unpublished_or_dirty_candidate_never_reaches_transport(published, tmp_path, monkeypatch, state):
    root, _ = published
    if state == 'untracked':
        (root / 'new.py').write_text('new code', encoding='utf-8')
    elif state in {'unstaged', 'staged', 'ahead'}:
        (root / 'app.py').write_text('unpublished code', encoding='utf-8')
        if state == 'staged':
            git(root, 'add', 'app.py')
        elif state == 'ahead':
            commit(root)
    elif state == 'no-upstream':
        git(root, 'branch', '--unset-upstream')
    elif state == 'detached':
        git(root, 'checkout', '--detach', '-q')
    else:
        git(root, 'remote', 'set-url', 'origin', str(tmp_path / 'not-a-remote'))
    monkeypatch.setattr(transport, '_run', lambda *args: pytest.fail('unapproved candidate reached SSH/rsync'))
    with pytest.raises(config.ConfigError):
        transport.rsync_push(target(), tmp_path / 'key', root)


def test_fetch_detects_a_remote_commit_that_local_tracking_has_not_seen(published, tmp_path, monkeypatch):
    root, origin = published
    other = tmp_path / 'other-client'
    git(root, 'clone', '-q', '--branch', 'main', str(origin), str(other))
    (other / 'app.py').write_text('new remote candidate', encoding='utf-8')
    commit(other)
    git(other, 'push', '-q', 'origin', 'main')
    assert git(root, 'rev-parse', 'HEAD') == git(root, 'rev-parse', '@{upstream}')
    monkeypatch.setattr(transport, '_run', lambda *args: pytest.fail('behind candidate reached SSH/rsync'))
    with pytest.raises(config.ConfigError, match='fetched upstream'):
        transport.rsync_push(target(), tmp_path / 'key', root)
    assert git(root, 'rev-parse', 'HEAD') != git(root, 'rev-parse', '@{upstream}')


def test_project_cannot_export_an_enclosing_repository(published, tmp_path, monkeypatch):
    root, _ = published
    nested = root / 'nested-project'
    nested.mkdir()
    monkeypatch.setattr(transport, '_run', lambda *args: pytest.fail('wrong Git root reached SSH/rsync'))
    with pytest.raises(config.ConfigError, match='repository root'):
        transport.rsync_push(target(), tmp_path / 'key', nested)


def test_escaping_git_symlink_is_rejected_before_transport(published, tmp_path, monkeypatch):
    root, _ = published
    (root / 'external').symlink_to(tmp_path / 'outside')
    commit(root)
    git(root, 'push', '-q', 'origin', 'main')
    monkeypatch.setattr(transport, '_run', lambda *args: pytest.fail('unsafe archive reached SSH/rsync'))
    with pytest.raises(config.ConfigError, match='unsafe or unreadable'):
        transport.rsync_push(target(), tmp_path / 'key', root)


def test_project_relative_and_legacy_destinations(tmp_path, monkeypatch):
    legacy = target()
    canonical = config.Target('mac_aabbccddeeff', 'fixture.invalid', 'codeanvil-agent',
                              '/home/codeanvil-agent/projects/uuid-one', device_id='mac_aabbccddeeff',
                              deploy_root='/home/codeanvil-agent/projects')
    monkeypatch.setattr(config.Target, 'sync_via_exec', property(lambda self: False))
    assert transport.rsync_push_argv(legacy, tmp_path / 'key', tmp_path)[-1].endswith(':')
    assert transport.rsync_push_argv(canonical, tmp_path / 'key', tmp_path)[-1].endswith(':uuid-one')
    monkeypatch.setattr(config.Target, 'sync_via_exec', property(lambda self: True))
    assert transport.rsync_push_argv(canonical, tmp_path / 'key', tmp_path)[-1].endswith(':/home/codeanvil-agent/projects/uuid-one')

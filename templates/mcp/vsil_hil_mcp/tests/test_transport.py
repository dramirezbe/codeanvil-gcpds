"""Local rsync scenarios: exercise receiver protection without connecting SSH."""

from pathlib import Path
import shutil
import subprocess

import pytest

from vsil_hil_mcp import config, transport


@pytest.mark.skipif(shutil.which('rsync') is None, reason='requires the real rsync executable')
def test_code_sync_excludes_preserve_receiver_database_and_declared_state(tmp_path):
    source, destination = tmp_path / 'source', tmp_path / 'destination'
    source.mkdir()
    destination.mkdir()
    target = config.Target('pi', 'fixture.invalid', 'codeanvil-agent', '/home/codeanvil-agent/workspace')
    from dataclasses import replace
    target = replace(target, persistent_paths=('keep/runtime-state',))
    protected = ['live.db', 'live.db-wal', 'live.db-shm', 'live.db-journal',
                 'nested/store.sqlite', 'nested/store.sqlite-wal',
                 'nested/store.sqlite3', 'nested/store.sqlite3-shm',
                 'keep/runtime-state/counter.txt']
    for relative in protected:
        local, remote = source / relative, destination / relative
        local.parent.mkdir(parents=True, exist_ok=True)
        remote.parent.mkdir(parents=True, exist_ok=True)
        local.write_text('must not replace persistent state', encoding='utf-8')
        remote.write_text('existing live state', encoding='utf-8')
    # A DB found only on the receiver must survive --delete as well.
    receiver_only = destination / 'orphan.sqlite-journal'
    receiver_only.write_text('live journal', encoding='utf-8')
    (source / 'app.py').write_text('new published code', encoding='utf-8')
    (destination / 'app.py').write_text('old code', encoding='utf-8')
    stale = destination / 'removed.py'
    stale.write_text('obsolete code', encoding='utf-8')
    argv = transport.rsync_push_argv(target, tmp_path / 'deploy_key', source)
    # Retain the real rsync options and exclusions, replacing only its SSH transport
    # and remote endpoint so this proof runs entirely under tmp_path.
    ssh_option = argv.index('-e')
    local_argv = [arg for index, arg in enumerate(argv) if index not in {ssh_option, ssh_option + 1}]
    local_argv[-1] = f'{destination}/'
    result = subprocess.run(local_argv, capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stderr
    assert (destination / 'app.py').read_text() == 'new published code'
    assert not stale.exists()
    assert receiver_only.read_text() == 'live journal'
    for relative in protected:
        assert (destination / relative).read_text() == 'existing live state'

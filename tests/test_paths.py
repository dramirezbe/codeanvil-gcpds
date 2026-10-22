"""Tests for codeanvil.config.paths — project constants, find_manifest, migration."""

from pathlib import Path

from codeanvil.config.paths import (
    PROJECT_CODEANVIL,
    PROJECT_CUSTODY,
    PROJECT_MANIFEST,
    PROJECT_REPORT,
    _migrate_legacy_workdir,
    find_manifest,
)


def test_project_constants():
    assert PROJECT_CODEANVIL == Path(".codeanvil")
    assert PROJECT_CUSTODY == Path(".codeanvil/custody")
    assert PROJECT_REPORT == Path(".codeanvil/report")
    assert PROJECT_MANIFEST == Path(".codeanvil/project.yaml")


def test_workdir_is_codeanvil_config():
    from codeanvil.config.paths import WORKDIR
    assert WORKDIR.name == ".codeanvil-config"


def _make_manifest(root: Path) -> Path:
    manifest = root / PROJECT_CODEANVIL / "project.yaml"
    manifest.parent.mkdir(parents=True)
    manifest.write_text("id: test\nname: test\n", encoding="utf-8")
    return manifest


def test_find_manifest_in_cwd(tmp_path):
    expected = _make_manifest(tmp_path)
    assert find_manifest(tmp_path) == expected


def test_find_manifest_walks_up(tmp_path):
    expected = _make_manifest(tmp_path)
    nested = tmp_path / "a" / "b" / "c"
    nested.mkdir(parents=True)
    assert find_manifest(nested) == expected


def test_find_manifest_missing(tmp_path):
    dead_end = tmp_path / "no" / "manifest" / "here"
    dead_end.mkdir(parents=True)
    # Walk-up stops at the filesystem root without finding anything (None).
    assert find_manifest(dead_end) is None


def test_migrate_legacy_workdir_moves_dir(tmp_path):
    legacy = tmp_path / ".codeanvil"
    legacy.mkdir()
    (legacy / "db").mkdir()
    target = tmp_path / ".codeanvil-config"
    assert not target.exists()

    _migrate_legacy_workdir(home=tmp_path, workdir=target)

    assert target.is_dir()
    assert (target / "db").is_dir()
    assert not legacy.exists()


def test_migrate_legacy_workdir_noop_when_target_exists(tmp_path):
    legacy = tmp_path / ".codeanvil"
    legacy.mkdir()
    target = tmp_path / ".codeanvil-config"
    target.mkdir()
    (target / "sentinel").write_text("keep", encoding="utf-8")

    _migrate_legacy_workdir(home=tmp_path, workdir=target)

    assert legacy.is_dir()
    assert (target / "sentinel").read_text(encoding="utf-8") == "keep"


def test_migrate_legacy_workdir_noop_without_legacy(tmp_path):
    target = tmp_path / ".codeanvil-config"
    _migrate_legacy_workdir(home=tmp_path, workdir=target)
    assert not target.exists()

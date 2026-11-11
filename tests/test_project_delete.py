"""Deletion exercises disposable registries and trees, never global projects."""

import sqlite3
import stat
from pathlib import Path

import pytest
import yaml

from codeanvil.config import paths
from codeanvil.db.schema import create_schema
from codeanvil.db.utils import connect_db
from codeanvil import project_delete as deletion
from codeanvil.project_delete import ProjectDeleteError, delete_project, resolve_delete_target


@pytest.fixture
def database(tmp_path):
    database = tmp_path / "registry.db"
    conn = connect_db(database)
    create_schema(conn)
    conn.close()
    return database


def project(database, root, identifier="project-1", name="Example"):
    (root / ".codeanvil").mkdir(parents=True, exist_ok=True)
    (root / ".codeanvil/project.yaml").write_text(yaml.safe_dump({"id": identifier, "name": name}))
    (root / "keep.txt").write_text("User code")
    with sqlite3.connect(database) as conn:
        conn.execute("INSERT INTO projects (id,name,path) VALUES (?,?,?)", (identifier, name, str(root)))
    return {"id": identifier, "name": name, "path": str(root)}


def rows(database):
    with sqlite3.connect(database) as conn:
        return conn.execute("SELECT id FROM projects ORDER BY id").fetchall()


def test_unregister_preserves_files_and_other_projects(database, tmp_path):
    selected = project(database, tmp_path / "one")
    project(database, tmp_path / "two", "project-2", "Other")
    assert resolve_delete_target("Example", db_path=database) == selected
    result = delete_project(selected["id"], expected_path=selected["path"], db_path=database)
    assert result == {"project": selected, "removed_files": False}
    assert (tmp_path / "one/keep.txt").read_text() == "User code"
    assert rows(database) == [("project-2",)]


def test_explicit_removal_deletes_only_matching_tree(database, tmp_path):
    selected = project(database, tmp_path / "one")
    project(database, tmp_path / "two", "project-2")
    result = delete_project(selected["id"], expected_path=selected["path"], remove_files=True, db_path=database)
    assert result["removed_files"] is True
    assert not (tmp_path / "one").exists()
    assert (tmp_path / "two/keep.txt").is_file()
    assert rows(database) == [("project-2",)]


def test_removal_operates_in_private_staging_and_cleans_wrapper(database, tmp_path, monkeypatch):
    root = tmp_path / "one"
    selected = project(database, root)
    original = deletion.shutil.rmtree
    observed = []

    def remove(staged):
        observed.append(staged)
        assert staged.name == "project"
        assert staged.parent.parent == root.parent
        assert staged.parent.name.startswith(".codeanvil-delete-")
        if deletion.os.name != "nt":
            assert stat.S_IMODE(staged.parent.stat().st_mode) == 0o700
        original(staged)

    monkeypatch.setattr(deletion.shutil, "rmtree", remove)
    delete_project(selected["id"], expected_path=selected["path"], remove_files=True, db_path=database)
    assert observed
    assert not root.exists()
    assert list(tmp_path.glob(".codeanvil-delete-*")) == []


@pytest.mark.parametrize("replacement_id", ["unrelated-project", "project-1"])
def test_replacement_before_staging_is_never_deleted(database, tmp_path, monkeypatch, replacement_id):
    root = tmp_path / "one"
    selected = project(database, root)
    moved = tmp_path / "original-moved"
    original = deletion.os.rename

    def swap_before_move(source, destination):
        if Path(source) == root:
            original(root, moved)
            (root / ".codeanvil").mkdir(parents=True)
            (root / ".codeanvil/project.yaml").write_text(yaml.safe_dump({"id": replacement_id}))
            (root / "replacement.txt").write_text("Keep the replacement")
        original(source, destination)

    def forbidden(_):
        raise AssertionError("A replacement must never reach rmtree")

    monkeypatch.setattr(deletion.os, "rename", swap_before_move)
    monkeypatch.setattr(deletion.shutil, "rmtree", forbidden)
    with pytest.raises(ProjectDeleteError, match="folder changed before removal"):
        delete_project(selected["id"], expected_path=selected["path"], remove_files=True, db_path=database)
    assert (moved / "keep.txt").read_text() == "User code"
    replacement = root if root.exists() else next(tmp_path.glob(".codeanvil-delete-*/project"))
    assert (replacement / "replacement.txt").read_text() == "Keep the replacement"
    assert rows(database) == [("project-1",)]


def test_manifest_is_rechecked_after_staging(database, tmp_path, monkeypatch):
    root = tmp_path / "one"
    selected = project(database, root)
    original = deletion.os.rename

    def change_identity(source, destination):
        original(source, destination)
        if Path(source) == root:
            (Path(destination) / ".codeanvil/project.yaml").write_text("id: another-project\n")

    def forbidden(_):
        raise AssertionError("A changed manifest must never reach rmtree")

    monkeypatch.setattr(deletion.os, "rename", change_identity)
    monkeypatch.setattr(deletion.shutil, "rmtree", forbidden)
    with pytest.raises(ProjectDeleteError, match="manifest changed before removal"):
        delete_project(selected["id"], expected_path=selected["path"], remove_files=True, db_path=database)
    remaining = root if root.exists() else next(tmp_path.glob(".codeanvil-delete-*/project"))
    assert (remaining / "keep.txt").read_text() == "User code"
    assert rows(database) == [("project-1",)]


def test_staging_failure_keeps_original_tree_and_cleans_empty_wrapper(database, tmp_path, monkeypatch):
    selected = project(database, tmp_path / "one")

    def unavailable(*_):
        raise PermissionError("Cannot move project")

    monkeypatch.setattr(deletion.os, "rename", unavailable)
    with pytest.raises(ProjectDeleteError, match="registry entry was kept"):
        delete_project(selected["id"], expected_path=selected["path"], remove_files=True, db_path=database)
    assert (tmp_path / "one/keep.txt").read_text() == "User code"
    assert list(tmp_path.glob(".codeanvil-delete-*")) == []
    assert rows(database) == [("project-1",)]


def test_failed_removal_preserves_recovery_tree_when_original_path_is_occupied(database, tmp_path, monkeypatch):
    root = tmp_path / "one"
    selected = project(database, root)

    def failed(_):
        root.mkdir()
        (root / "new-occupant.txt").write_text("Do not overwrite")
        raise PermissionError("Folder is in use")

    monkeypatch.setattr(deletion.shutil, "rmtree", failed)
    with pytest.raises(ProjectDeleteError, match="Recover the remaining folder from") as error:
        delete_project(selected["id"], expected_path=selected["path"], remove_files=True, db_path=database)
    staged = next(tmp_path.glob(".codeanvil-delete-*/project"))
    assert str(staged) in str(error.value)
    assert (staged / "keep.txt").read_text() == "User code"
    assert (root / "new-occupant.txt").read_text() == "Do not overwrite"
    assert rows(database) == [("project-1",)]


def test_failed_partial_removal_restores_or_exposes_remaining_files(database, tmp_path, monkeypatch):
    root = tmp_path / "one"
    selected = project(database, root)

    def partial(staged):
        (staged / "keep.txt").unlink()
        raise PermissionError("Interrupted removal")

    monkeypatch.setattr(deletion.shutil, "rmtree", partial)
    with pytest.raises(ProjectDeleteError, match="files may be partially removed"):
        delete_project(selected["id"], expected_path=selected["path"], remove_files=True, db_path=database)
    remaining = root if root.exists() else next(tmp_path.glob(".codeanvil-delete-*/project"))
    assert (remaining / ".codeanvil/project.yaml").is_file()
    assert not (remaining / "keep.txt").exists()
    assert rows(database) == [("project-1",)]


def test_duplicate_names_require_full_id(database, tmp_path):
    project(database, tmp_path / "one")
    second = project(database, tmp_path / "two", "project-2")
    with pytest.raises(ProjectDeleteError, match="ambiguous.*project-1.*project-2"):
        resolve_delete_target("Example", db_path=database)
    assert resolve_delete_target("project-2", db_path=database) == second


def test_current_project_does_not_register_and_requires_current_path(database, tmp_path):
    selected = project(database, tmp_path / "one")
    nested = tmp_path / "one/nested"
    nested.mkdir()
    assert resolve_delete_target(cwd=nested, db_path=database) == selected
    with sqlite3.connect(database) as conn:
        conn.execute("UPDATE projects SET path = ?", (str(tmp_path / "old"),))
    with pytest.raises(ProjectDeleteError, match="sync first"):
        resolve_delete_target(cwd=nested, db_path=database)
    with sqlite3.connect(database) as conn:
        conn.execute("DELETE FROM projects")
    with pytest.raises(ProjectDeleteError, match="not registered"):
        resolve_delete_target(cwd=nested, db_path=database)
    assert rows(database) == []


def test_orphaned_entries_can_be_unregistered_without_files(database, tmp_path):
    selected = project(database, tmp_path / "one")
    (tmp_path / "one/.codeanvil/project.yaml").unlink()
    delete_project(selected["id"], expected_path=selected["path"], db_path=database)
    assert (tmp_path / "one/keep.txt").exists()
    assert rows(database) == []


def test_stale_path_or_missing_row_cannot_delete(database, tmp_path):
    selected = project(database, tmp_path / "one")
    for identifier, path in [(selected["id"], str(tmp_path / "other")), ("missing", selected["path"])]:
        with pytest.raises(ProjectDeleteError):
            delete_project(identifier, expected_path=path, remove_files=True, db_path=database)
    assert rows(database) == [("project-1",)]
    assert (tmp_path / "one/keep.txt").exists()


@pytest.mark.parametrize("manifest", ["id: other\n", "- invalid\n", "[broken"])
def test_removal_requires_matching_root_manifest(database, tmp_path, manifest):
    selected = project(database, tmp_path / "one")
    (tmp_path / "one/.codeanvil/project.yaml").write_text(manifest)
    with pytest.raises(ProjectDeleteError):
        delete_project(selected["id"], expected_path=selected["path"], remove_files=True, db_path=database)
    assert rows(database) == [("project-1",)]
    assert (tmp_path / "one/keep.txt").exists()


@pytest.mark.parametrize("guard", ["home", "config", "registry", "nested", "same_path", "nested_alias", "alias", "manifest_alias"])
def test_removal_refuses_protected_or_shared_trees(database, tmp_path, monkeypatch, guard):
    root = tmp_path / "one"
    selected = project(database, root)
    if guard == "home":
        monkeypatch.setenv("HOME", str(root))
        monkeypatch.setenv("USERPROFILE", str(root))
    elif guard == "config":
        monkeypatch.setattr(paths, "WORKDIR", root / "global-config")
    elif guard == "registry":
        selected["path"] = str(tmp_path)
        with sqlite3.connect(database) as conn:
            conn.execute("UPDATE projects SET path = ?", (str(tmp_path),))
    elif guard == "nested":
        project(database, root / "nested", "project-2", "Other")
    elif guard == "same_path":
        with sqlite3.connect(database) as conn:
            conn.execute("INSERT INTO projects (id,name,path) VALUES (?,?,?)", ("project-2", "Other", str(root)))
    elif guard == "nested_alias":
        outside = tmp_path / "outside"
        outside.mkdir()
        (root / "nested").symlink_to(outside, target_is_directory=True)
        with sqlite3.connect(database) as conn:
            conn.execute("INSERT INTO projects (id,name,path) VALUES (?,?,?)", ("project-2", "Other", str(root / "nested")))
    elif guard == "alias":
        alias = tmp_path / "alias"
        alias.symlink_to(root, target_is_directory=True)
        selected["path"] = str(alias)
        with sqlite3.connect(database) as conn:
            conn.execute("UPDATE projects SET path = ?", (str(alias),))
    else:
        identity = root / ".codeanvil/project.yaml"
        outside = tmp_path / "identity.yaml"
        identity.rename(outside)
        identity.symlink_to(outside)
    with pytest.raises(ProjectDeleteError):
        delete_project(selected["id"], expected_path=selected["path"], remove_files=True, db_path=database)
    assert (root / "keep.txt").exists()
    assert ("project-1",) in rows(database)


def test_filesystem_failure_keeps_registry_entry(database, tmp_path, monkeypatch):
    selected = project(database, tmp_path / "one")
    def failed(_):
        raise PermissionError("Folder is in use")
    monkeypatch.setattr(deletion.shutil, "rmtree", failed)
    with pytest.raises(ProjectDeleteError, match="registry entry was kept"):
        delete_project(selected["id"], expected_path=selected["path"], remove_files=True, db_path=database)
    assert rows(database) == [("project-1",)]


def test_missing_registry_does_not_create_database(tmp_path):
    database = tmp_path / "missing.db"
    with pytest.raises(ProjectDeleteError, match="not initialized"):
        resolve_delete_target("Example", db_path=database)
    assert not database.exists()

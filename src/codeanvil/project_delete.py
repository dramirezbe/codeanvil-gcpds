"""Shared project deletion: unregister by default, remove files only explicitly."""

import os
import shutil
import sqlite3
import stat
import sys
import tempfile
from pathlib import Path

import yaml

from codeanvil.config import paths
from codeanvil.db.utils import connect_db


class ProjectDeleteError(ValueError):
    """A project cannot be selected or safely deleted."""


def _connect(db_path: Path | None):
    database = Path(db_path) if db_path is not None else paths.DB_PATH
    if not database.is_file():
        raise ProjectDeleteError("CodeAnvil is not initialized. Run codeanvil init first.")
    try:
        return connect_db(database), database
    except sqlite3.Error as exc:
        raise ProjectDeleteError(f"Cannot read the project registry: {exc}") from exc


def _identity(manifest: Path) -> dict:
    try:
        data = yaml.safe_load(manifest.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise ProjectDeleteError("Cannot read the project's .codeanvil/project.yaml.") from exc
    if not isinstance(data, dict) or not isinstance(data.get("id"), str) or not data["id"].strip():
        raise ProjectDeleteError("The project manifest must contain a non-empty id.")
    return data


def resolve_delete_target(
    selector: str | None = None, *, cwd: Path | None = None, db_path: Path | None = None,
) -> dict[str, str]:
    """Resolve an exact UUID/name or the registered project owning cwd; never sync."""
    conn, _ = _connect(db_path)
    try:
        current_root = None
        if selector is None:
            manifest = paths.find_manifest(cwd if cwd is not None else Path.cwd())
            if manifest is None:
                raise ProjectDeleteError("No project found. Provide a project name or full UUID.")
            current_root = manifest.parent.parent.resolve()
            selector = _identity(manifest)["id"]
            rows = conn.execute("SELECT id,name,path FROM projects WHERE id = ?", (selector,)).fetchall()
        else:
            if not isinstance(selector, str) or not selector.strip():
                raise ProjectDeleteError("Provide a project name or full UUID.")
            rows = conn.execute("SELECT id,name,path FROM projects WHERE id = ? OR name = ?", (selector, selector)).fetchall()
        if not rows:
            raise ProjectDeleteError("Project is not registered. Use codeanvil list to inspect the registry.")
        if len(rows) != 1:
            ids = ", ".join(row["id"] for row in rows)
            raise ProjectDeleteError(f"Project name is ambiguous. Use a full UUID: {ids}")
        project = dict(rows[0])
        if current_root is not None and Path(project["path"]).resolve() != current_root:
            raise ProjectDeleteError("This project's registered path differs. Run codeanvil sync first.")
        return project
    except (sqlite3.Error, OSError, RuntimeError) as exc:
        raise ProjectDeleteError(f"Cannot resolve the registered project: {exc}") from exc
    finally:
        conn.close()


def _signature(entry: os.stat_result) -> tuple[int, int, int]:
    return entry.st_dev, entry.st_ino, stat.S_IFMT(entry.st_mode)


def _removable_root(project: dict, conn, database: Path) -> tuple[Path, tuple[int, int, int]]:
    raw = Path(project["path"])
    if not raw.is_absolute():
        raise ProjectDeleteError("The registered project path must be absolute.")
    try:
        root = raw.resolve(strict=True)
        entry = root.lstat()
        if root != raw or not stat.S_ISDIR(entry.st_mode) or os.path.ismount(root):
            raise ProjectDeleteError("Refusing to remove an aliased, missing or filesystem-root project folder.")
        home = Path.home().resolve()
        config = paths.WORKDIR.resolve()
        protected = (home, config, database.resolve())
        if any(item == root or item.is_relative_to(root) for item in protected) or root.is_relative_to(config):
            raise ProjectDeleteError("Refusing to remove the home, global configuration, registry, or an ancestor.")
        manifest = root / paths.PROJECT_MANIFEST
        if manifest.is_symlink() or (root / ".codeanvil").is_symlink() or manifest.resolve() != manifest:
            raise ProjectDeleteError("The root project manifest must not be a symlink or alias.")
        if _identity(manifest)["id"] != project["id"]:
            raise ProjectDeleteError("The root project manifest does not match the registered UUID.")
        for other in conn.execute("SELECT id,path FROM projects WHERE id != ?", (project["id"],)):
            other_path = Path(other["path"])
            if not other_path.is_absolute():
                raise ProjectDeleteError("Another registered project has an invalid relative path.")
            if other_path.is_relative_to(root) or other_path.resolve().is_relative_to(root):
                raise ProjectDeleteError(f"Another registered project is inside this folder: {other['id']}.")
    except (OSError, RuntimeError) as exc:
        raise ProjectDeleteError(f"Cannot validate the project folder for removal: {exc}") from exc
    return root, _signature(entry)


def _restore_without_replacing(source: Path, destination: Path) -> bool:
    """Restore atomically without replacing a concurrently created destination.

    Windows rename already refuses an existing destination. Linux exposes the
    same guarantee through renameat2. If unavailable, keep the recovery folder
    rather than approximate this with an unsafe exists()/rename() sequence.
    """
    try:
        if os.name == "nt":
            os.rename(source, destination)
            return True
        if not sys.platform.startswith("linux"):
            return False
        import ctypes

        rename = getattr(ctypes.CDLL(None, use_errno=True), "renameat2", None)
        if rename is None:
            return False
        rename.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
        rename.restype = ctypes.c_int
        # AT_FDCWD=-100; RENAME_NOREPLACE=1. Absolute paths ignore the dir fds.
        return rename(-100, os.fsencode(source), -100, os.fsencode(destination), 1) == 0
    except OSError:
        return False


def _cleanup_wrapper(wrapper: Path) -> None:
    try:
        wrapper.rmdir()  # Never recursively remove unexpected contents.
    except OSError:
        pass


def _recover_staged(staged: Path, root: Path, wrapper: Path) -> str:
    try:
        present = staged.exists() or staged.is_symlink()
    except OSError:
        present = True  # Keep the recovery path even when it cannot be inspected.
    if present:
        if _restore_without_replacing(staged, root):
            recovery = f"The remaining folder was restored to {root}."
        else:
            recovery = f"Recover the remaining folder from {staged}; its original path was not overwritten."
    else:
        recovery = "No staged folder remains."
    _cleanup_wrapper(wrapper)
    return recovery


def _remove_files(project: dict, conn, database: Path) -> None:
    root, expected_identity = _removable_root(project, conn, database)
    wrapper = None
    staged = None
    try:
        wrapper = Path(tempfile.mkdtemp(prefix=".codeanvil-delete-", dir=root.parent))
        os.chmod(wrapper, 0o700)
        staged = wrapper / "project"
        os.rename(root, staged)
        # A replacement at the public path must never inherit the deletion
        # authorization. Recheck the exact directory and manifest after moving.
        if _signature(staged.lstat()) != expected_identity:
            raise ProjectDeleteError("The project folder changed before removal. No folder contents were deleted.")
        manifest = staged / paths.PROJECT_MANIFEST
        if (manifest.resolve() != manifest or (staged / ".codeanvil").is_symlink()
                or _identity(manifest)["id"] != project["id"]):
            raise ProjectDeleteError("The project manifest changed before removal. No folder contents were deleted.")
    except (OSError, ProjectDeleteError) as exc:
        recovery = _recover_staged(staged, root, wrapper) if staged is not None else ""
        if wrapper is not None:
            _cleanup_wrapper(wrapper)
        raise ProjectDeleteError(f"Cannot stage the project folder: {exc}. The registry entry was kept. {recovery}") from exc
    try:
        shutil.rmtree(staged)
    except OSError as exc:
        recovery = _recover_staged(staged, root, wrapper)
        raise ProjectDeleteError(
            f"Cannot remove the project folder: {exc}. The registry entry was kept; files may be partially removed. {recovery}"
        ) from exc
    _cleanup_wrapper(wrapper)


def delete_project(
    project_id: str, *, expected_path: str, remove_files: bool = False, db_path: Path | None = None,
) -> dict:
    """Recheck the selected row while locked, then remove it and optionally its tree.

    Filesystem deletion cannot be transactional with SQLite: a failed rmtree may
    remove some files. Such failures keep the registry row so the project remains
    visible for recovery. A registry failure after removal is reported explicitly.
    """
    conn, database = _connect(db_path)
    removed_files = False
    try:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute("SELECT id,name,path FROM projects WHERE id = ?", (project_id,)).fetchone()
        if row is None:
            raise ProjectDeleteError("Project is no longer registered. Refresh the project list.")
        project = dict(row)
        if project["path"] != expected_path:
            raise ProjectDeleteError("The registered project path changed. Refresh before deleting.")
        if remove_files:
            _remove_files(project, conn, database)
            removed_files = True
        conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
        conn.commit()
        return {"project": project, "removed_files": removed_files}
    except sqlite3.Error as exc:
        conn.rollback()
        detail = " Files were removed; retry without --remove-files." if removed_files else " No files were removed."
        raise ProjectDeleteError(f"Cannot update the project registry: {exc}.{detail}") from exc
    except ProjectDeleteError:
        conn.rollback()
        raise
    finally:
        conn.close()

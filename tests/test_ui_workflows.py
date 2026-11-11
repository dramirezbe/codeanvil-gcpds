"""Project workflows use real temporary registry/scaffold operations, no global writes."""

import importlib
import json
import sqlite3
import subprocess
from pathlib import Path

import pytest
import yaml

pytest.importorskip("fastapi")
from fastapi import HTTPException
from pydantic import ValidationError

from codeanvil.db.schema import create_schema
from codeanvil.db.utils import connect_db
from codeanvil.UI import workflows
from codeanvil.UI.project_context import ProjectManifestError, project_context
from codeanvil.UI.workflows import CreateRequest, FolderRequest, SyncRequest, create_workflows_router


@pytest.fixture
def registry(tmp_path, monkeypatch):
    path = tmp_path / "registry.db"
    conn = connect_db(path)
    create_schema(conn)
    conn.close()
    create_module = importlib.import_module("codeanvil.CLI.commands.create")
    sync_module = importlib.import_module("codeanvil.init.sync")
    monkeypatch.setattr(workflows, "DB_PATH", path)
    monkeypatch.setattr(create_module, "DB_PATH", path)
    monkeypatch.setattr(create_module, "preflight", lambda: True)
    monkeypatch.setattr(sync_module, "DB_PATH", path)
    return path


@pytest.fixture
def endpoints(tmp_path):
    # Direct route calls keep these domain/HTTP-error checks independent of a
    # server's event loop and avoid starting native folder dialogs in tests.
    return {route.path.rsplit("/", 1)[-1]: route.endpoint for route in create_workflows_router(tmp_path).routes}


def manifest(root: Path, **updates):
    root.mkdir(parents=True, exist_ok=True)
    folder = root / ".codeanvil"
    folder.mkdir(exist_ok=True)
    data = {"id": "019f0000-0000-7000-8000-000000000001", "name": "A project", **updates}
    (folder / "project.yaml").write_text(yaml.safe_dump(data), encoding="utf-8")
    return data


def registered(path):
    with sqlite3.connect(path) as conn:
        return conn.execute("SELECT id, name, path FROM projects").fetchall()


def test_create_scaffolds_identity_and_registry_without_changing_cwd(endpoints, registry, tmp_path):
    previous = Path.cwd()
    response = endpoints["create"](CreateRequest(name="My SDR Lab", parent_path=str(tmp_path)))
    project = response["project"]
    root = tmp_path / "my_sdr_lab"
    assert project["path"] == str(root)
    assert project["name"] == "My SDR Lab"
    assert project["cycle"] is None
    assert (root / "AGENTS.md").is_file()
    assert len(list((root / ".agents/skills").glob("*/SKILL.md"))) == 7
    assert yaml.safe_load((root / ".codeanvil/project.yaml").read_text())["id"] == project["id"]
    assert registered(registry) == [(project["id"], "My SDR Lab", str(root))]
    assert not (root / "src").exists()
    assert Path.cwd() == previous


def test_symlink_loops_return_validation_errors(endpoints, registry, tmp_path):
    loop = tmp_path / "loop"
    loop.symlink_to(loop)
    with pytest.raises(ProjectManifestError, match="resolve"):
        project_context(loop)
    with pytest.raises(HTTPException) as caught:
        endpoints["sync"](SyncRequest(path=str(loop)))
    assert caught.value.status_code == 400
    assert registered(registry) == []

    root = tmp_path / "project"
    (root / ".codeanvil").mkdir(parents=True)
    manifest_path = root / ".codeanvil/project.yaml"
    manifest_path.symlink_to(manifest_path)
    with pytest.raises(HTTPException) as caught:
        endpoints["sync"](SyncRequest(path=str(root)))
    assert caught.value.status_code == 400


def test_create_does_not_touch_an_existing_folder(endpoints, registry, tmp_path):
    root = tmp_path / "occupied"
    root.mkdir()
    original = root / "notes.txt"
    original.write_text("Keep this content")
    with pytest.raises(HTTPException) as caught:
        endpoints["create"](CreateRequest(name="Existing", folder="occupied", parent_path=str(tmp_path)))
    assert caught.value.status_code == 409
    assert original.read_text() == "Keep this content"
    assert list(root.iterdir()) == [original]
    assert registered(registry) == []


def test_manual_relative_paths_use_the_ui_root_not_process_cwd(endpoints, registry, tmp_path, monkeypatch):
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)
    response = endpoints["create"](CreateRequest(name="Relative Lab", parent_path="."))
    assert response["project"]["path"] == str(tmp_path / "relative_lab")
    assert not (elsewhere / "relative_lab").exists()


@pytest.mark.parametrize("folder", ["..", ".", "../outside", "nested/path", "nested\\path"])
def test_create_rejects_path_shaped_folder(endpoints, registry, tmp_path, folder):
    with pytest.raises(HTTPException) as caught:
        endpoints["create"](CreateRequest(name="Lab", folder=folder, parent_path=str(tmp_path)))
    assert caught.value.status_code == 400
    assert registered(registry) == []


def test_create_requires_an_existing_parent_and_nonblank_name(endpoints, registry, tmp_path):
    for request in (
        CreateRequest(name="Lab", parent_path=str(tmp_path / "absent")),
        CreateRequest(name="   ", parent_path=str(tmp_path)),
    ):
        with pytest.raises(HTTPException) as caught:
            endpoints["create"](request)
        assert caught.value.status_code == 400
    assert registered(registry) == []


def test_unknown_and_uninstalled_mcp_fail_before_scaffold(endpoints, registry, tmp_path, monkeypatch):
    monkeypatch.setattr(workflows, "is_mcp_installed", lambda name: False)
    for server, expected in (("unknown-server", 400), ("marconi", 409)):
        with pytest.raises(HTTPException) as caught:
            endpoints["create"](CreateRequest(name="Lab", parent_path=str(tmp_path), mcp_servers=[server]))
        assert caught.value.status_code == expected
        assert not (tmp_path / "lab").exists()
    assert registered(registry) == []


def test_create_activates_an_installed_mcp_using_existing_wiring(endpoints, registry, tmp_path, monkeypatch):
    mcp = importlib.import_module("codeanvil.init.mcp")
    installation = tmp_path / "installed-marconi"
    skill = installation / "skills/usage"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text("---\nname: usage\ndescription: Test fixture skill\n---\n\n# Usage\n")
    monkeypatch.setattr(mcp, "get_mcp_install_path", lambda name: installation)
    response = endpoints["create"](CreateRequest(name="MCP Lab", parent_path=str(tmp_path), mcp_servers=["marconi"]))
    root = Path(response["project"]["path"])
    assert (root / ".agents/skills/marconi-usage/SKILL.md").is_file()
    assert "marconi" in yaml.safe_load((root / ".agents/mcp.yaml").read_text())["mcp_servers"]
    assert "marconi" in json.loads((root / ".mcp.json").read_text())["mcpServers"]
    assert (root / "opencode.json").is_file()
    assert len(registered(registry)) == 1


def test_sync_registers_and_moves_by_uuid_without_rescaffolding(endpoints, registry, tmp_path):
    first = tmp_path / "original"
    data = manifest(first)
    report = first / ".codeanvil/report/01_demo/G0.md"
    report.parent.mkdir(parents=True)
    report.write_text("A report to preserve")
    added = endpoints["sync"](SyncRequest(path=str(first)))
    again = endpoints["sync"](SyncRequest(path=str(first)))
    assert added["action"] == "registered"
    assert again["action"] == "already registered"
    assert report.read_text() == "A report to preserve"
    assert not (first / "AGENTS.md").exists()
    moved = tmp_path / "moved"
    manifest(moved, name="Renamed")
    response = endpoints["sync"](SyncRequest(path=str(moved)))
    assert response["action"] == "updated"
    assert registered(registry) == [(data["id"], "Renamed", str(moved))]


def test_sync_accepts_a_nested_project_folder(endpoints, registry, tmp_path):
    root = tmp_path / "project"
    manifest(root, cycle="01_demo")
    nested = root / "nested"
    nested.mkdir()
    response = endpoints["sync"](SyncRequest(path=str(nested)))
    assert response["project"]["path"] == str(root)
    assert response["project"]["cycle"] == "01_demo"


@pytest.mark.parametrize("content", ["[unclosed", "- not a mapping", "id: 7\nname: Lab", "id: abc\nname: ''", "id: abc\nname: Lab\ncycle: ../outside"])
def test_bad_manifest_is_a_field_friendly_error(endpoints, registry, tmp_path, content):
    root = tmp_path / "broken"
    manifest(root)
    (root / ".codeanvil/project.yaml").write_text(content)
    with pytest.raises(HTTPException) as caught:
        endpoints["sync"](SyncRequest(path=str(root)))
    assert caught.value.status_code == 400
    assert isinstance(caught.value.detail, str)
    assert registered(registry) == []


def test_no_manifest_and_missing_registry_are_distinct_errors(endpoints, registry, tmp_path, monkeypatch):
    with pytest.raises(HTTPException) as caught:
        endpoints["sync"](SyncRequest(path=str(tmp_path)))
    assert caught.value.status_code == 400
    root = tmp_path / "project"
    manifest(root)
    monkeypatch.setattr(workflows, "DB_PATH", tmp_path / "absent.db")
    with pytest.raises(HTTPException) as caught:
        endpoints["sync"](SyncRequest(path=str(root)))
    assert caught.value.status_code == 503
    with pytest.raises(HTTPException) as caught:
        endpoints["create"](CreateRequest(name="Lab", parent_path=str(tmp_path)))
    assert caught.value.status_code == 503
    assert not (tmp_path / "lab").exists()


def test_manifest_symlink_cannot_import_identity_from_outside(tmp_path):
    outside = tmp_path / "outside.yaml"
    outside.write_text("id: abc\nname: Outside\n")
    root = tmp_path / "project"
    (root / ".codeanvil").mkdir(parents=True)
    try:
        (root / ".codeanvil/project.yaml").symlink_to(outside)
    except OSError:
        pytest.skip("Symlinks unavailable")
    with pytest.raises(ProjectManifestError, match="inside"):
        project_context(root)


def test_mcp_catalog_reports_configured_state_without_installing(endpoints, monkeypatch):
    monkeypatch.setattr(workflows, "server_rows", lambda: [{"name": "marconi", "installed": False, "source": "git", "ref": "pin", "head": "", "pinned": False}])
    row = endpoints["mcp"]()["servers"][0]
    assert row["name"] == "marconi" and not row["installed"]
    assert row["description"]


@pytest.mark.parametrize("selection", [None, "selected"])
def test_folder_picker_cancellation_and_selection(endpoints, tmp_path, monkeypatch, selection):
    folder = tmp_path / "selected"
    folder.mkdir()
    commands = []

    def picker(argv, **kwargs):
        commands.append((argv, kwargs))
        return subprocess.CompletedProcess(argv, 0, json.dumps({"path": str(folder) if selection else None}), "")

    monkeypatch.setattr(workflows.subprocess, "run", picker)
    result = endpoints["pick-folder"](FolderRequest(initial_path=str(tmp_path)))
    assert result == {"path": str(folder) if selection else None}
    argv, options = commands[0]
    assert argv[1:3] == ["-m", "codeanvil.UI.folder_picker"]
    assert not options.get("shell")


@pytest.mark.parametrize("output,code", [("not json", 0), ('{"error":"headless"}', 1)])
def test_folder_picker_headless_response_offers_manual_fallback(endpoints, monkeypatch, output, code):
    monkeypatch.setattr(workflows.subprocess, "run", lambda argv, **kwargs: subprocess.CompletedProcess(argv, code, output, ""))
    with pytest.raises(HTTPException) as caught:
        endpoints["pick-folder"](FolderRequest())
    assert caught.value.status_code == 409
    assert "Enter the folder path" in caught.value.detail


def test_payload_paths_do_not_accept_non_text_values():
    with pytest.raises(ValidationError):
        SyncRequest(path=123)
    with pytest.raises(ValidationError):
        CreateRequest(name="Lab", parent_path="/tmp", mcp_servers=[7])

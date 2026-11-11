"""Deletion workflows confirm the exact registered identity before shared mutations."""
import asyncio
import sqlite3

import httpx
import pytest
import yaml

from codeanvil.db.schema import create_schema
from codeanvil.db.utils import connect_db
from codeanvil.UI import ui, workflows
from codeanvil.UI.actions import _catalog
from codeanvil.UI.ui import create_app

IDENTITY = "019a0000-0000-7000-8000-000000000001"


@pytest.fixture
def deletion(tmp_path, monkeypatch):
    database = tmp_path / "registry.db"
    project = tmp_path / "project"
    (project / ".codeanvil").mkdir(parents=True)
    (project / ".codeanvil/project.yaml").write_text(yaml.safe_dump({"id": IDENTITY, "name": "Delete preview"}))
    (project / "keep.txt").write_text("Project contents")
    conn = connect_db(database)
    create_schema(conn)
    conn.execute("INSERT INTO projects (id,name,path) VALUES (?,?,?)", (IDENTITY, "Delete preview", str(project)))
    conn.commit()
    conn.close()
    monkeypatch.setattr(workflows, "DB_PATH", database)
    monkeypatch.setattr(ui, "DB_PATH", database)

    def post(**overrides):
        payload = {
            "project_id": IDENTITY, "expected_path": str(project),
            "confirm": True, "confirmation_name": "Delete preview", **overrides,
        }
        async def request():
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=create_app(tmp_path)), base_url="http://localhost") as client:
                result = await client.post("/api/workflows/delete", json=payload)
                projects = (await client.get("/api/projects")).json()
                return result, projects
        return asyncio.run(request())
    return project, database, post


def test_unregister_keeps_files_and_removes_the_project_from_the_ui(deletion):
    project, _, post = deletion
    response, projects = post()
    assert response.status_code == 200
    assert response.json()["removed_files"] is False
    assert projects == []
    assert (project / "keep.txt").read_text() == "Project contents"


def test_explicit_folder_deletion_removes_only_the_selected_project(deletion, tmp_path):
    project, _, post = deletion
    neighbor = tmp_path / "neighbor.txt"
    neighbor.write_text("Keep")
    response, projects = post(remove_files=True)
    assert response.status_code == 200
    assert response.json()["removed_files"] is True
    assert projects == []
    assert not project.exists()
    assert neighbor.read_text() == "Keep"


@pytest.mark.parametrize("override,status", [
    ({"confirm": False}, 428),
    ({"confirmation_name": "Another project"}, 400),
    ({"confirmation_name": ""}, 400),
    ({"expected_path": "/a/stale/path"}, 409),
    ({"project_id": "missing"}, 409),
    ({"remove_files": "true"}, 422),
    ({"confirm": "true"}, 422),
])
def test_rejected_requests_preserve_registry_and_files(deletion, override, status):
    project, database, post = deletion
    response, projects = post(**override)
    assert response.status_code == status
    assert [entry["id"] for entry in projects] == [IDENTITY]
    assert (project / "keep.txt").read_text() == "Project contents"
    with sqlite3.connect(database) as conn:
        assert conn.execute("SELECT COUNT(*) FROM projects").fetchone()[0] == 1


def test_delete_advanced_action_directs_users_to_the_confirmation_workflow():
    action = next(entry for entry in _catalog() if entry["id"] == "delete")
    assert action["available"] is False
    assert "project card" in action["reason"]

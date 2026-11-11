"""HTTP integration for the packaged UI, using an isolated local registry."""

import asyncio
from pathlib import Path

import pytest

pytest.importorskip("fastapi")
httpx = pytest.importorskip("httpx")

from codeanvil.db.schema import create_schema
from codeanvil.db.utils import connect_db
from codeanvil.UI.ui import create_app

EXAMPLES = Path(__file__).resolve().parents[1] / "methodology/test/v0.7.0-example-artifacts"


def test_app_routes_share_project_and_artifact_contract(tmp_path, monkeypatch):
    from codeanvil.UI import ui

    database = tmp_path / "registry.db"
    conn = connect_db(database)
    create_schema(conn)
    conn.close()
    monkeypatch.setattr(ui, "DB_PATH", database)
    project = EXAMPLES / "panel_prototipo"

    async def exercise():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=create_app(tmp_path)), base_url="http://localhost") as client:
            landing = await client.get("/api/ui/bootstrap")
            assert landing.json() == {"mode": "launcher", "project": None, "projects": []}
            query = {"project_path": str(project)}
            bootstrap = await client.get("/api/ui/bootstrap", params=query)
            assert bootstrap.json()["project"]["name"] == "Panel de prototipo"
            overview = await client.get("/api/workspace/overview", params=query)
            assert overview.status_code == 200
            assert overview.json()["synthetic_fixture"] is True
            assert overview.json()["completion"]["passed"] == 6
            prototype = next(item for item in overview.json()["artifacts"] if item["kind"] == "prototype")
            artifact = await client.get("/api/workspace/artifact", params={**query, "path": prototype["path"]})
            assert artifact.status_code == 200
            assert "SYNTHETIC UI FIXTURE" in artifact.json()["content"]
            blocked = await client.get("/api/workspace/artifact", params={**query, "path": ".env"})
            assert blocked.status_code == 400
            catalog = await client.get("/api/workflows/mcp")
            assert catalog.status_code == 200
            assert {row["name"] for row in catalog.json()["servers"]} == {"marconi", "vsil_hil_mcp"}

    asyncio.run(exercise())


def test_app_rejects_foreign_requests_and_malformed_identity(tmp_path):
    project = tmp_path / "broken"
    (project / ".codeanvil").mkdir(parents=True)
    (project / ".codeanvil/project.yaml").write_text("- not\n- an identity\n")

    async def exercise():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=create_app(tmp_path)), base_url="http://localhost") as client:
            assert (await client.get("/api/context", headers={"host": "foreign.example"})).status_code == 400
            assert (await client.get("/api/context", headers={"origin": "https://foreign.example"})).status_code == 403
            broken = await client.get("/api/ui/bootstrap", params={"project_path": str(project)})
            assert broken.status_code == 400
            assert "mapping" in broken.json()["detail"]

    asyncio.run(exercise())

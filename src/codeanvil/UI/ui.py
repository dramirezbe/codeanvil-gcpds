"""Local FastAPI application for the CodeAnvil workspace UI.

The UI is an optional extra so importing the CLI never requires web packages.
"""

from __future__ import annotations

import threading
import webbrowser
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import yaml

from codeanvil.config.paths import DB_PATH, PROJECT_BACKUPS, PROJECT_DESIGN, PROJECT_GT, PROJECT_REPORT, find_manifest
from codeanvil.db.schema import db_exists
from codeanvil.db.utils import connect_db
from codeanvil.db.projects import list_projects
from codeanvil.reports import backup_entries, cycle_reports


def _project_context(cwd: Path) -> tuple[Path, dict[str, Any]] | None:
    manifest = find_manifest(cwd)
    if manifest is None:
        return None
    data = yaml.safe_load(manifest.read_text(encoding="utf-8")) or {}
    return manifest.parent.parent.resolve(), data


def _selected_project(root: Path, project_path: str | None):
    """Resolve a project explicitly selected in the launcher, if supplied."""
    selected = Path(project_path).expanduser().resolve() if project_path else root
    return _project_context(selected)


def _json_safe(value: Any) -> Any:
    if hasattr(value, "items"):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    if isinstance(value, Path):
        return str(value)
    if hasattr(value, "__dict__"):
        return {k: _json_safe(v) for k, v in vars(value).items() if not k.startswith("_")}
    return value


def create_app(cwd: Path | None = None):
    """Build the app; resolving cwd at construction makes tests deterministic."""
    try:
        from fastapi import FastAPI, HTTPException, Request
        from fastapi.responses import FileResponse
        from fastapi.staticfiles import StaticFiles
    except ImportError as exc:  # pragma: no cover - depends on optional extra
        raise RuntimeError("The UI requires the optional dependencies. Install with `uv tool install 'codeanvil[ui]'`.") from exc

    root = (cwd or Path.cwd()).resolve()
    app = FastAPI(title="CodeAnvil", docs_url="/api/docs")
    from codeanvil.UI.actions import create_actions_router
    app.include_router(create_actions_router(root))

    @app.middleware("http")
    async def local_request_guard(request: Request, call_next):
        # Uvicorn is loopback-only. Also reject foreign Host/Origin headers so
        # a hostile site cannot use DNS rebinding to read local project files.
        host = (urlsplit("//" + request.headers.get("host", "")).hostname or "").lower()
        if host not in {"127.0.0.1", "localhost", "::1", "testserver"}:
            from fastapi.responses import PlainTextResponse
            return PlainTextResponse("Invalid Host header", status_code=400)
        origin = request.headers.get("origin")
        if origin:
            origin_host = (urlsplit(origin).hostname or "").lower()
            if origin_host not in {"127.0.0.1", "localhost", "::1"}:
                from fastapi.responses import PlainTextResponse
                return PlainTextResponse("Cross-origin requests are not allowed", status_code=403)
        return await call_next(request)

    @app.get("/api/context")
    def context():
        project = _project_context(root)
        if project is None:
            return {"mode": "launcher", "project": None}
        path, identity = project
        return {"mode": "workspace", "project": {"path": str(path), "id": identity.get("id"), "name": identity.get("name"), "cycle": identity.get("cycle")}}

    @app.get("/api/ui/bootstrap")
    def bootstrap(project_path: str | None = None):
        project = _selected_project(root, project_path)
        if project_path and project is None:
            raise HTTPException(status_code=404, detail="Not a CodeAnvil project")
        current = None
        if project is not None:
            path, identity = project
            current = {"path": str(path), "id": identity.get("id"), "name": identity.get("name"), "cycle": identity.get("cycle")}
        available = []
        if db_exists(DB_PATH):
            conn = connect_db(DB_PATH)
            try:
                available = [_json_safe(dict(row)) for row in list_projects(conn)]
            finally:
                conn.close()
        return {"mode": "workspace" if current else "launcher", "project": current, "projects": available}

    @app.get("/api/projects")
    def projects():
        if not db_exists(DB_PATH):
            return []
        conn = connect_db(DB_PATH)
        try:
            return [_json_safe(dict(row)) for row in list_projects(conn)]
        finally:
            conn.close()

    @app.get("/api/workspace/progress")
    def progress(project_path: str | None = None):
        project = _selected_project(root, project_path)
        if project is None:
            raise HTTPException(status_code=409, detail="Open a CodeAnvil project to view progress")
        path, identity = project
        cycles = cycle_reports(path / PROJECT_REPORT)
        backups = backup_entries(path / PROJECT_BACKUPS)
        active_cycle = identity.get("cycle")
        active_reports = cycles.get(active_cycle, {}) if active_cycle else {}
        return {
            "project": {"path": str(path), "id": identity.get("id"), "name": identity.get("name")},
            "active_cycle": active_cycle,
            "cycles": _json_safe({cycle: {gate: state._asdict() for gate, state in gates.items()} for cycle, gates in cycles.items()}),
            "active_reports": {gate: state._asdict() for gate, state in active_reports.items()},
            "backups": _json_safe(backups),
        }

    @app.get("/api/workspace/documents/{area}/{name}")
    def document(area: str, name: str, project_path: str | None = None):
        project = _selected_project(root, project_path)
        if project is None:
            raise HTTPException(status_code=409, detail="Open a CodeAnvil project to view documents")
        path, _ = project
        areas = {"gt": PROJECT_GT, "design": PROJECT_DESIGN}
        if area not in areas or Path(name).name != name or not name.endswith((".md", ".html")):
            raise HTTPException(status_code=400, detail="Unsupported document")
        target = (path / areas[area] / name).resolve()
        if not target.is_relative_to((path / areas[area]).resolve()) or not target.is_file():
            raise HTTPException(status_code=404, detail="Document not found")
        return {"name": name, "content": target.read_text(encoding="utf-8")}

    @app.get("/api/workspace/reports/{cycle}/{name}")
    def report(cycle: str, name: str, project_path: str | None = None):
        project = _selected_project(root, project_path)
        if project is None:
            raise HTTPException(status_code=409, detail="Open a CodeAnvil project to view reports")
        path, _ = project
        if Path(cycle).name != cycle or Path(name).name != name or not name.endswith(".md"):
            raise HTTPException(status_code=400, detail="Unsupported report")
        folder = (path / PROJECT_REPORT / cycle).resolve()
        target = (folder / name).resolve()
        if not target.is_relative_to(folder) or not target.is_file():
            raise HTTPException(status_code=404, detail="Report not found")
        return {"cycle": cycle, "name": name, "content": target.read_text(encoding="utf-8")}

    dist = Path(__file__).parent / "frontend" / "dist"
    if (dist / "index.html").is_file():
        app.mount("/assets", StaticFiles(directory=dist / "assets"), name="assets")

        @app.get("/")
        def index():
            return FileResponse(dist / "index.html")

    return app


def run_ui(port: int = 8765, *, open_browser: bool = True) -> None:
    """Run the local-only UI server and optionally open the system browser."""
    try:
        import uvicorn
    except ImportError as exc:  # pragma: no cover - depends on optional extra
        raise RuntimeError("The UI requires the optional dependencies. Install with `codeanvil[ui]`.") from exc

    host = "127.0.0.1"
    url = f"http://{host}:{port}/"
    if open_browser:
        threading.Timer(0.8, webbrowser.open, args=(url,)).start()
    uvicorn.run(create_app(), host=host, port=port)

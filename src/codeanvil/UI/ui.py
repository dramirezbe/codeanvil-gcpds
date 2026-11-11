"""Local FastAPI application for the CodeAnvil workspace UI.

The UI is an optional extra so importing the CLI never requires web packages.
"""

from __future__ import annotations

import threading
import webbrowser
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from codeanvil.config.paths import DB_PATH
from codeanvil.db.schema import db_exists
from codeanvil.db.utils import connect_db
from codeanvil.db.projects import list_projects
from codeanvil.UI.project_context import project_context, project_summary


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
    from codeanvil.UI.workflows import create_workflows_router
    from codeanvil.UI.workspace import create_workspace_router
    app.include_router(create_actions_router(root))
    app.include_router(create_workflows_router(root))
    app.include_router(create_workspace_router(root))

    def selected_project(project_path: str | None = None):
        selected = Path(project_path).expanduser() if project_path else root
        if not selected.is_absolute():
            selected = root / selected
        try:
            found = project_context(selected)
        except (ValueError, OSError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        if project_path and found is None:
            raise HTTPException(status_code=404, detail="Not a CodeAnvil project")
        return found

    def registered_projects():
        if not db_exists(DB_PATH):
            return []
        conn = connect_db(DB_PATH)
        try:
            return [_json_safe(dict(row)) for row in list_projects(conn)]
        finally:
            conn.close()

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
        project = selected_project()
        return {"mode": "workspace" if project else "launcher", "project": project_summary(*project) if project else None}

    @app.get("/api/ui/bootstrap")
    def bootstrap(project_path: str | None = None):
        project = selected_project(project_path)
        return {
            "mode": "workspace" if project else "launcher",
            "project": project_summary(*project) if project else None,
            "projects": registered_projects(),
        }

    @app.get("/api/projects")
    def projects():
        return registered_projects()

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

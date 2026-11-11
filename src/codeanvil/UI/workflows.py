"""Purpose-built project workflows over existing CodeAnvil operations."""

import json
import sqlite3
import subprocess
import sys
import threading
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, StrictStr

from codeanvil.CLI.commands.create import CreateInputError, cmd_create, resolve_create_inputs
from codeanvil.config.paths import CONFIG, DB_PATH
from codeanvil.db.schema import db_exists
from codeanvil.init.mcp import is_mcp_installed, server_rows
from codeanvil.init.sync import run_sync
from codeanvil.UI.project_context import ProjectManifestError, project_context, project_summary

_CREATE_LOCK = threading.Lock()
_PICKER_UNAVAILABLE = "Native folder selection is unavailable. Enter the folder path instead."


class FolderRequest(BaseModel):
    initial_path: StrictStr | None = None


class SyncRequest(BaseModel):
    path: StrictStr = Field(min_length=1)


class CreateRequest(BaseModel):
    name: StrictStr = Field(min_length=1)
    parent_path: StrictStr = Field(min_length=1)
    folder: StrictStr | None = None
    mcp_servers: list[StrictStr] = Field(default_factory=list)


def _existing_folder(value: str, base: Path) -> Path:
    if not value.strip():
        raise HTTPException(status_code=400, detail="Choose an existing folder.")
    try:
        path = Path(value).expanduser()
        path = (base / path if not path.is_absolute() else path).resolve()
        exists = path.is_dir()
    except (OSError, RuntimeError, ValueError):
        exists = False
    if not exists:
        raise HTTPException(status_code=400, detail="Choose an existing folder.")
    return path


def _require_registry() -> None:
    if not db_exists(DB_PATH):
        raise HTTPException(status_code=503, detail="CodeAnvil is not initialized. Run codeanvil init first.")


def _context(path: Path):
    try:
        found = project_context(path)
    except ProjectManifestError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if found is None:
        raise HTTPException(status_code=400, detail="No .codeanvil/project.yaml was found in this folder or its parents.")
    return found


def create_workflows_router(root: Path) -> APIRouter:
    root = root.resolve()
    router = APIRouter(prefix="/api/workflows", tags=["workflows"])

    @router.get("/mcp")
    def mcp_catalog():
        rows = server_rows()
        for row in rows:
            row["description"] = CONFIG.get("mcp_servers", {}).get(row["name"], {}).get("description", "")
        return {"servers": rows}

    @router.post("/pick-folder")
    def pick_folder(request: FolderRequest):
        initial = _existing_folder(request.initial_path, root) if request.initial_path else root
        try:
            result = subprocess.run(
                [sys.executable, "-m", "codeanvil.UI.folder_picker", str(initial)],
                capture_output=True, text=True, timeout=120, check=False,
            )
            payload = json.loads(result.stdout)
            if result.returncode != 0 or not isinstance(payload, dict) or payload.get("error"):
                raise ValueError("picker unavailable")
            selected = payload.get("path")
            if selected is None:
                return {"path": None}
            if not isinstance(selected, str):
                raise ValueError("invalid picker result")
            return {"path": str(_existing_folder(selected, root))}
        except (OSError, ValueError, subprocess.SubprocessError) as exc:
            raise HTTPException(status_code=409, detail=_PICKER_UNAVAILABLE) from exc

    @router.post("/sync")
    def add_existing(request: SyncRequest):
        path, identity = _context(_existing_folder(request.path, root))
        _require_registry()
        try:
            action, synced = run_sync(path)
        except (OSError, sqlite3.Error) as exc:
            raise HTTPException(status_code=503, detail="Could not register the project. Check CodeAnvil initialization and folder permissions.") from exc
        return {"action": action, "project": project_summary(path, synced)}

    @router.post("/create")
    def create(request: CreateRequest):
        parent = _existing_folder(request.parent_path, root)
        try:
            label, folder = resolve_create_inputs(None, request.name, request.folder, target=parent)
        except CreateInputError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        servers = list(dict.fromkeys(request.mcp_servers))
        for server in servers:
            if server not in CONFIG.get("mcp_servers", {}):
                raise HTTPException(status_code=400, detail=f"Unknown MCP server: {server}.")
            if not is_mcp_installed(server):
                raise HTTPException(status_code=409, detail=f"Install MCP server {server} globally before activating it for a project.")
        _require_registry()
        target = parent / folder
        # Serialize create requests so a second browser request cannot select
        # the same folder after the first request's preflight has passed.
        with _CREATE_LOCK:
            if target.exists() or target.is_symlink():
                raise HTTPException(status_code=409, detail="That project folder already exists. Choose a new folder or add the existing project.")
            try:
                cmd_create(None, parent, mcp_servers=servers or None, project_name=label, folder=folder)
            except SystemExit as exc:
                raise HTTPException(status_code=503, detail="Project creation failed. Check CodeAnvil initialization and MCP installation.") from exc
            except (OSError, ValueError, sqlite3.Error) as exc:
                raise HTTPException(status_code=503, detail="Project creation failed. Check the parent folder permissions and CodeAnvil initialization.") from exc
        project_path, identity = _context(target)
        return {"project": project_summary(project_path, identity)}

    return router

"""Project-local Build Package uploads and document previews."""

from datetime import datetime, timezone
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
from tempfile import TemporaryDirectory
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import Response
from starlette.concurrency import run_in_threadpool
from starlette.datastructures import UploadFile
from starlette.formparsers import MultiPartException, MultiPartParser

from codeanvil.config.paths import PROJECT_GT
from codeanvil.UI.build_package_archives import documents
from codeanvil.UI.build_package_preview import preview_document, render_pdf_page
from codeanvil.UI.terminal import same_origin
from codeanvil.UI.workspace import _project

_BATCH = re.compile(r"[a-f0-9]{32}\Z")
_UPLOAD_BYTES = 128 * 1024 * 1024
_EXPANDED_BYTES = 256 * 1024 * 1024
_UPLOAD_FILES = 100
_DOCUMENTS = 500
_SOURCE_DIRECTORY = PROJECT_GT / "build_package_uploads"


def _unlinked(path: Path) -> Path:
    try:
        if path.resolve() == path:
            return path
    except (OSError, RuntimeError, ValueError):
        pass
    raise HTTPException(400, "Build Package paths must stay inside the project's original directories.")


def _display_name(value: str) -> str:
    path = PurePosixPath(value.replace("\\", "/"))
    if (not path.parts or path.is_absolute() or ".." in path.parts or PureWindowsPath(value).drive
            or any(ord(char) < 32 for char in value) or len(value) > 1024):
        raise HTTPException(422, "An uploaded file or archive member has an invalid path.")
    return path.as_posix()


def _stored_name(name: str) -> str:
    filename = PurePosixPath(name).name
    sanitized = re.sub(r'[<>:"/\\|?*]', "_", filename).rstrip(" .")
    if PureWindowsPath(sanitized).is_reserved():
        sanitized = f"_{sanitized}"
    if len(sanitized) > 60:
        suffix = PurePosixPath(sanitized).suffix[:12]
        sanitized = sanitized[:60 - len(suffix)] + suffix
    return sanitized or "document"


def _manifest(folder: Path) -> list[dict]:
    path = _unlinked(folder / "manifest.json")
    try:
        with path.open(encoding="utf-8") as stream:
            return json.load(stream)
    except (OSError, ValueError) as exc:
        raise HTTPException(404, "Build Package upload is unavailable.") from exc


def _list(project: Path) -> list[dict]:
    store = _unlinked(project / _SOURCE_DIRECTORY)
    if not store.is_dir():
        return []
    batches = (_manifest(batch) for batch in store.iterdir() if _BATCH.fullmatch(batch.name) and batch.is_dir())
    return sorted((item for batch in batches for item in batch),
                  key=lambda item: (item["uploaded_at"], item["batch"], -item["index"]), reverse=True)


def _file(project: Path, batch: str, index: int) -> Path:
    if not _BATCH.fullmatch(batch) or index < 0:
        raise HTTPException(404, "Document not found.")
    folder = _unlinked(project / _SOURCE_DIRECTORY / batch)
    entries = _manifest(folder)
    if index >= len(entries):
        raise HTTPException(404, "Document not found.")
    file = _unlinked(folder / "files" / str(index) / _stored_name(entries[index]["name"]))
    if not file.is_file():
        raise HTTPException(404, "Document not found.")
    return file


def _save_batch(project: Path, uploads: list[UploadFile]) -> list[dict]:
    store = _unlinked(project / _SOURCE_DIRECTORY)
    batch = uuid4().hex
    uploaded_at = datetime.now(timezone.utc).isoformat(timespec="milliseconds")
    entries: list[dict] = []
    remaining = _EXPANDED_BYTES
    try:
        store.mkdir(parents=True, exist_ok=True)
        with TemporaryDirectory(prefix=".upload-", dir=store) as temporary:
            staged = Path(temporary) / batch
            staged.mkdir()
            for upload in uploads:
                source = _display_name(upload.filename or "")
                before = len(entries)
                # On Python 3.10 a spooled upload lacks seekable() and readinto().
                with os.fdopen(os.dup(upload.file.fileno()), "rb") as source_file:
                    source_file.seek(0)
                    for raw_name, archive, content in documents(source, source_file):
                        if len(entries) == _DOCUMENTS:
                            raise HTTPException(413, f"An upload can contain at most {_DOCUMENTS} documents.")
                        name = _display_name(raw_name)
                        index = len(entries)
                        path = staged / "files" / str(index) / _stored_name(name)
                        path.parent.mkdir(parents=True)
                        with path.open("xb") as stream:
                            for chunk in content:
                                remaining -= len(chunk)
                                if remaining < 0:
                                    raise HTTPException(413, "Extracted documents exceed the 256 MiB upload limit.")
                                stream.write(chunk)
                        entries.append({"batch": batch, "index": index, "name": name,
                                        "archive": archive, "uploaded_at": uploaded_at})
                if len(entries) == before:
                    raise HTTPException(422, f"{source} contains no regular files.")
            (staged / "manifest.json").write_text(json.dumps(entries, ensure_ascii=False), encoding="utf-8")
            staged.rename(store / batch)
    except OSError as exc:
        raise HTTPException(400, "Could not write the project's Build Package upload.") from exc
    return entries


async def _limited_stream(request: Request):
    total = 0
    async for chunk in request.stream():
        total += len(chunk)
        if total > _UPLOAD_BYTES:
            raise HTTPException(413, "A Build Package upload may be at most 128 MiB.")
        yield chunk


def create_build_package_router(root: Path) -> APIRouter:
    router = APIRouter(prefix="/api/workspace/build-package", tags=["build package"])

    @router.get("")
    def files(project_path: str | None = None):
        project, _ = _project(root, project_path)
        return {"files": _list(project)}

    @router.post("", status_code=201)
    async def upload(request: Request, project_path: str | None = None):
        if not same_origin(request.headers):
            raise HTTPException(403, "A same-origin browser request is required.")
        project, _ = _project(root, project_path)
        if request.headers.get("content-type", "").split(";", 1)[0].strip().lower() != "multipart/form-data":
            raise HTTPException(415, "Upload documents as multipart form data.")
        try:
            form = await MultiPartParser(request.headers, _limited_stream(request),
                                         max_files=_UPLOAD_FILES, max_fields=0).parse()
        except MultiPartException as exc:
            raise HTTPException(400, str(exc)) from exc
        try:
            uploads = form.getlist("files")
            if not uploads or len(uploads) != len(form.multi_items()) or not all(
                isinstance(file, UploadFile) for file in uploads
            ):
                raise HTTPException(400, "Select one or more files to upload.")
            return {"files": await run_in_threadpool(_save_batch, project, uploads)}
        finally:
            await form.close()

    @router.get("/{batch}/{index}/preview")
    def preview(batch: str, index: int, sheet: int = Query(0, ge=0), project_path: str | None = None):
        project, _ = _project(root, project_path)
        return preview_document(_file(project, batch, index), sheet)

    @router.get("/{batch}/{index}/pdf-page")
    def pdf_page(batch: str, index: int, page: int = Query(1, ge=1), project_path: str | None = None):
        project, _ = _project(root, project_path)
        image = render_pdf_page(_file(project, batch, index), page)
        return Response(image, media_type="image/png", headers={"X-Content-Type-Options": "nosniff"})

    return router

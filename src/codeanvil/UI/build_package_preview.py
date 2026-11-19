"""Bounded, read-only previews of Build Package source documents."""

from contextlib import closing, contextmanager
import csv
from io import BytesIO, StringIO
from itertools import islice
from math import isfinite
from pathlib import Path
from threading import Lock
from zipfile import BadZipFile, ZipFile

from fastapi import HTTPException
import pypdfium2
from python_calamine import CalamineError, CalamineWorkbook

_TEXT_BYTES = 1024 * 1024
_ROWS = 200
_COLS = 50
_CELL_CHARS = 1000
_EXCEL_BYTES = 64 * 1024 * 1024
_PDF_LOCK = Lock()


def _read_text(path: Path) -> tuple[str, bool]:
    with path.open("rb") as stream:
        data = stream.read(_TEXT_BYTES + 1)
    clipped = len(data) > _TEXT_BYTES
    raw = data[:_TEXT_BYTES]
    if raw.startswith((b"\xff\xfe\x00\x00", b"\x00\x00\xfe\xff")):
        text = raw.decode("utf-32", errors="replace")
    elif raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        text = raw.decode("utf-16", errors="replace")
    else:
        text = raw.decode("utf-8-sig", errors="replace")
    return text.replace("\0", "\ufffd"), clipped


def _table(rows, sheets=(), sheet=0, clipped=False) -> dict:
    visible = list(islice(rows, _ROWS + 1))
    clipped = clipped or len(visible) > _ROWS or any(len(row) > _COLS for row in visible)
    cells = []
    for row in visible[:_ROWS]:
        text_row = [str(value) if value is not None else "" for value in row[:_COLS]]
        clipped = clipped or any(len(value) > _CELL_CHARS for value in text_row)
        cells.append([value[:_CELL_CHARS] for value in text_row])
    return {"format": "table", "rows": cells, "sheets": list(sheets), "sheet": sheet, "clipped": clipped}


def _spreadsheet(path: Path, sheet: int) -> dict:
    try:
        if path.suffix.casefold() == ".xlsx":
            with ZipFile(path) as archive:
                if sum(entry.file_size for entry in archive.infolist()) > _EXCEL_BYTES:
                    raise HTTPException(413, "This workbook is too large to preview.")
        elif path.stat().st_size > _EXCEL_BYTES:
            raise HTTPException(413, "This workbook is too large to preview.")
        with CalamineWorkbook.from_path(path) as workbook:
            sheets = workbook.sheet_names
            if not sheets:
                return _table(())
            if sheet >= len(sheets):
                raise HTTPException(404, "Worksheet not found.")
            return _table(workbook.get_sheet_by_index(sheet).iter_rows(), sheets, sheet)
    except (CalamineError, BadZipFile, OSError) as exc:
        raise HTTPException(422, "Could not open this workbook.") from exc


@contextmanager
def _pdf(path: Path):
    # PDFium calls must be serialized across requests, including object cleanup.
    with _PDF_LOCK:
        try:
            with pypdfium2.PdfDocument(path) as document:
                yield document
        except (pypdfium2.PdfiumError, OSError, ValueError) as exc:
            raise HTTPException(422, "Could not open this PDF. It may be damaged or password protected.") from exc


def preview_document(path: Path, sheet: int) -> dict:
    suffix = path.suffix.casefold()
    if suffix == ".pdf":
        with _pdf(path) as document:
            return {"format": "pdf", "pages": len(document)}
    if suffix in {".xls", ".xlsx"}:
        return _spreadsheet(path, sheet)
    text, clipped = _read_text(path)
    if suffix == ".csv":
        stream = StringIO(text, newline="")
        try:
            dialect = csv.Sniffer().sniff(text[:8192], delimiters=",;\t|")
        except csv.Error:
            dialect = "excel"
        try:
            return _table(csv.reader(stream, dialect), clipped=clipped)
        except csv.Error as exc:
            raise HTTPException(422, "Could not read the CSV preview.") from exc
    return {"format": "markdown" if suffix in {".md", ".markdown"} else "text",
            "content": text, "clipped": clipped}


def render_pdf_page(path: Path, number: int) -> bytes:
    if path.suffix.casefold() != ".pdf":
        raise HTTPException(404, "PDF not found.")
    with _pdf(path) as document:
        if number > len(document):
            raise HTTPException(404, "Page not found.")
        with closing(document[number - 1]) as page:
            width, height = page.get_size()
            if not all(isfinite(size) and size > 0 for size in (width, height)):
                raise HTTPException(422, "The PDF page has invalid dimensions.")
            scale = min(3, 1800 / max(width, height))
            with closing(page.render(scale=scale)) as bitmap, bitmap.to_pil() as image, BytesIO() as output:
                image.save(output, format="PNG")
                return output.getvalue()

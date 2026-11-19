"""Stream archive members without letting an archive write to the filesystem."""

import bz2
from collections.abc import Iterable, Iterator
import gzip
from io import BufferedIOBase
import lzma
from pathlib import PurePosixPath
import stat
import tarfile
from typing import BinaryIO
import zipfile
import zlib

from fastapi import HTTPException

_TAR = (".tar", ".tgz", ".tar.gz", ".tbz", ".tbz2", ".tar.bz2", ".txz", ".tar.xz")
_LIBARCHIVE = (".7z", ".rar", ".zipx", ".cab", ".cpio", ".tar.zst", ".tzst", ".lha", ".lzh", ".xar")
_COMPRESSED = {".gz": gzip.GzipFile, ".bz2": bz2.BZ2File, ".xz": lzma.LZMAFile}
_CHUNK = 256 * 1024


def blocks(stream: BinaryIO | BufferedIOBase) -> Iterator[bytes]:
    while chunk := stream.read(_CHUNK):
        yield chunk


def _extended_members(stream: BinaryIO) -> Iterator[tuple[str, Iterable[bytes]]]:
    try:
        from libarchive import stream_reader
        from libarchive.exception import ArchiveError
    except (ImportError, OSError, AttributeError, TypeError) as exc:
        raise HTTPException(415, "This archive format requires the system libarchive library.") from exc
    try:
        with stream_reader(stream) as archive:
            for entry in archive:
                if entry.isfile and not entry.islnk:
                    name = entry.name
                    yield name.decode("utf-8", errors="replace") if isinstance(name, bytes) else name, entry.get_blocks()
    except ArchiveError as exc:
        raise HTTPException(422, "The archive is corrupt, encrypted, or unsupported.") from exc


def documents(name: str, stream: BinaryIO) -> Iterator[tuple[str, str | None, Iterable[bytes]]]:
    """Yield display path, archive name (when applicable), and file content."""
    lower = name.casefold()
    suffix = PurePosixPath(lower).suffix
    try:
        if suffix == ".zip":
            with zipfile.ZipFile(stream) as archive:
                for entry in archive.infolist():
                    mode = stat.S_IFMT(entry.external_attr >> 16)
                    if not entry.is_dir() and mode in (0, stat.S_IFREG):
                        with archive.open(entry) as member:
                            yield entry.filename, name, blocks(member)
        elif lower.endswith(_TAR):
            with tarfile.open(fileobj=stream, mode="r|*") as archive:
                for entry in archive:
                    if entry.isfile():
                        member = archive.extractfile(entry)
                        if member is not None:
                            with member:
                                yield entry.name, name, blocks(member)
        elif lower.endswith(_LIBARCHIVE):
            for entry_name, content in _extended_members(stream):
                yield entry_name, name, content
        elif suffix in _COMPRESSED:
            opener = _COMPRESSED[suffix]
            kwargs = {"fileobj": stream} if suffix == ".gz" else {"filename": stream}
            with opener(**kwargs) as member:
                yield name[:-len(suffix)], name, blocks(member)
        else:
            yield name, None, blocks(stream)
    except (zipfile.BadZipFile, tarfile.TarError, RuntimeError, EOFError, OSError, lzma.LZMAError, zlib.error) as exc:
        raise HTTPException(422, f"Could not read {name}. The archive may be corrupt or encrypted.") from exc

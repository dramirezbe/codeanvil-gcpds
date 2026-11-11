"""Validate the prebuilt, self-contained frontend without Node or a web server."""

import re
from pathlib import Path
from urllib.parse import unquote, urlsplit


class UIAssetsError(RuntimeError):
    """The installed frontend is missing or depends on an external asset."""


def validate_frontend(dist: Path) -> Path:
    """Check the entry point, linked assets and CSS fonts before serving them."""
    dist = dist.resolve()
    index = dist / "index.html"
    if not index.is_file():
        raise UIAssetsError("CodeAnvil's built UI is missing. Reinstall CodeAnvil from a complete distribution.")

    def local_asset(reference: str, parent: Path) -> Path | None:
        url = urlsplit(reference)
        if url.scheme == "data" or (not url.path and not url.netloc and not url.scheme):
            return None
        if url.scheme or url.netloc:
            raise UIAssetsError(f"The built UI requires an external asset: {reference}")
        path = unquote(url.path)
        asset = ((dist / path.lstrip("/")) if path.startswith("/") else parent / path).resolve()
        if not asset.is_relative_to(dist) or not asset.is_file():
            raise UIAssetsError(f"CodeAnvil's built UI asset is missing: {reference}. Reinstall CodeAnvil.")
        return asset

    try:
        html = index.read_text(encoding="utf-8")
        references = re.findall(r'''(?:src|href)\s*=\s*["']([^"']+)["']''', html, re.IGNORECASE)
        assets = [local_asset(value, dist) for value in references]
        if not any(asset and asset.suffix == ".js" for asset in assets):
            raise UIAssetsError("CodeAnvil's built UI has no JavaScript entry point. Reinstall CodeAnvil.")
        pending = [asset for asset in assets if asset and asset.suffix == ".css"]
        visited = set()
        while pending:
            css = pending.pop()
            if css in visited:
                continue
            visited.add(css)
            text = css.read_text(encoding="utf-8")
            imports = re.findall(r'''@import\s+["']([^"']+)["']''', text, re.IGNORECASE)
            urls = re.findall(r'''url\(\s*["']?([^\s"')]+)["']?\s*\)''', text, re.IGNORECASE)
            for value in [*imports, *urls]:
                asset = local_asset(value, css.parent)
                if asset and asset.suffix == ".css":
                    pending.append(asset)
    except (OSError, UnicodeError, ValueError) as exc:
        raise UIAssetsError(f"Cannot read CodeAnvil's built UI: {exc}") from exc
    return dist

"""Local user context and a stable starting directory for UI folder dialogs."""

import getpass
from pathlib import Path


def local_user() -> dict[str, str]:
    home = Path.home()
    try:
        name = getpass.getuser()
    except (KeyError, OSError):
        name = home.name
    return {"name": name, "home": str(home)}


def default_folder() -> Path:
    """Prefer existing documents folders; never create one or depend on cwd."""
    home = Path.home()
    for name in ("Documents", "Documentos"):
        candidate = home / name
        if candidate.is_dir():
            return candidate
    return home

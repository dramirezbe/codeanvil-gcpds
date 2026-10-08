from pathlib import Path

WORKDIR = Path.home() / ".codeanvil"
DB_DIR = WORKDIR / "db"
DB_PATH = DB_DIR / "codeanvil.db"


def ensure_dirs() -> None:
    DB_DIR.mkdir(parents=True, exist_ok=True)

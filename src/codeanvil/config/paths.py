from importlib import resources
from pathlib import Path

import yaml

from codeanvil.config.logger import get_logger

log = get_logger(__name__)

WORKDIR = Path.home() / ".codeanvil-config"
DB_DIR = WORKDIR / "db"
DB_PATH = DB_DIR / "codeanvil.db"
MCP_DIR = WORKDIR / "mcp"

# Project-local constants — machine-generated methodology artifacts live
# under <project>/.codeanvil/. Human-authored GT stays at the project root.
PROJECT_CODEANVIL = Path(".codeanvil")
PROJECT_CUSTODY = PROJECT_CODEANVIL / "custody"
PROJECT_REPORT = PROJECT_CODEANVIL / "report"
PROJECT_MANIFEST = PROJECT_CODEANVIL / "project.yaml"


def _migrate_legacy_workdir(home: Path | None = None, workdir: Path | None = None) -> None:
    """One-time pre-release migration: ~/.codeanvil/ -> ~/.codeanvil-config/.

    Only moves when the legacy dir exists and the new one doesn't — never
    overwrites anything."""
    home = home if home is not None else Path.home()
    target = workdir if workdir is not None else WORKDIR
    legacy = home / ".codeanvil"
    if legacy.is_dir() and not target.exists():
        legacy.rename(target)
        log.info("migrated global config %s -> %s", legacy, target)


def ensure_dirs() -> None:
    _migrate_legacy_workdir()
    DB_DIR.mkdir(parents=True, exist_ok=True)
    MCP_DIR.mkdir(parents=True, exist_ok=True)


def find_manifest(start: Path) -> Path | None:
    """Walk up from start looking for .codeanvil/project.yaml."""
    current = start.resolve()
    while True:
        candidate = current / PROJECT_CODEANVIL / "project.yaml"
        if candidate.is_file():
            return candidate
        parent = current.parent
        if parent == current:
            return None
        current = parent


def _find_templates_dir() -> Path:
    """Locate the templates directory.
    Works for both editable installs (source tree) and wheel installs
    (templates bundled inside the package via force-include)."""
    # Editable install: templates/ lives 3 levels above this file
    dev_path = Path(__file__).resolve().parents[3] / "templates"
    if dev_path.is_dir():
        return dev_path
    # Wheel install: hatch force-includes templates into codeanvil/templates/
    pkg_path = Path(str(resources.files("codeanvil") / "templates"))
    if pkg_path.is_dir():
        return pkg_path
    raise FileNotFoundError("Cannot locate templates directory")


TEMPLATES_DIR = _find_templates_dir()

# Canonical skill store in the scaffolded project. All agent runtimes
# discover skills through symlinks pointing here.
SKILLS_DIRNAME = Path(".agents") / "skills"


def _load_config() -> dict:
    """Load templates/config.yaml — the single source of truth for the
    scaffold (skills, agent symlinks, pointer files, template paths)."""
    config_path = TEMPLATES_DIR / "config.yaml"
    with config_path.open(encoding="utf-8") as fh:
        config = yaml.safe_load(fh)
    if not isinstance(config, dict):
        raise ValueError(f"invalid scaffold config: {config_path} is empty or not a mapping")
    return config


CONFIG = _load_config()

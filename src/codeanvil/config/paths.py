from importlib import resources
from pathlib import Path

import yaml

WORKDIR = Path.home() / ".codeanvil"
DB_DIR = WORKDIR / "db"
DB_PATH = DB_DIR / "codeanvil.db"


def ensure_dirs() -> None:
    DB_DIR.mkdir(parents=True, exist_ok=True)


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

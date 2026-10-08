import shutil
from pathlib import Path

from codeanvil.config.logger import get_logger

log = get_logger(__name__)

TEMPLATES_DIR = Path(__file__).resolve().parents[3] / "templates"


def scaffold_project(name: str, target: Path) -> Path:
    project_dir = target.resolve() / name
    project_dir.mkdir(parents=True, exist_ok=True)

    gt_dir = project_dir / "GT"
    gt_dir.mkdir(exist_ok=True)
    for template in (TEMPLATES_DIR / "GT").glob("*.md"):
        dest = gt_dir / template.name.replace("placeholder_", "")
        shutil.copy2(template, dest)
        log.debug("copied GT template %s -> %s", template.name, dest)

    skills_src = TEMPLATES_DIR / "skills"
    if skills_src.exists():
        skills_dest = project_dir / "skills"
        shutil.copytree(skills_src, skills_dest, dirs_exist_ok=True)
        log.debug("copied skills to %s", skills_dest)

    log.info("scaffolded project '%s' at %s", name, project_dir)
    return project_dir


def register_project(conn, name: str, path: Path) -> int:
    cur = conn.execute(
        "INSERT INTO projects (name, path) VALUES (?, ?)",
        (name, str(path)),
    )
    conn.commit()
    log.info("registered project '%s' (id=%d)", name, cur.lastrowid)
    return cur.lastrowid

import shutil
from pathlib import Path

from codeanvil.config.logger import get_logger

log = get_logger(__name__)

TEMPLATES_DIR = Path(__file__).resolve().parents[3] / "templates"

# Canonical skill store in the scaffolded project. All agent runtimes
# discover skills through symlinks pointing here.
SKILLS_DIRNAME = Path(".agents") / "skills"

# Agent runtime skill directories (relative to the project root).
# Each is a symlink to `.agents/skills` so every runtime sees the same skills.
AGENT_SKILL_DIRS = [".claude/skills", ".opencode/skills", ".codex/skills"]

# Never copy build artifacts or legacy empty scripts into a project.
COPY_IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc", "valid_structure_SRS.py")

# Repo-root paths inside SKILL.md / RULES.md become project-relative after copy.
# Order matters: apply in dict insertion order.
PATH_REPLACEMENTS = {
    "templates/skills/": ".agents/skills/",
    "templates/GT/G0_SRS.md": ".agents/skills/G0_valid_req_and_GT/templates/G0_SRS.md",
    "templates/GT/G0_HCS.md": ".agents/skills/G0_valid_req_and_GT/templates/G0_HCS.md",
    "(repository-root relative)": "(project-root relative)",
}

# Locked IEEE 29148 reference templates shipped inside the G0 skill.
G0_SKILL_NAME = "G0_valid_req_and_GT"
GT_REFERENCE_TEMPLATES = ("G0_SRS.md", "G0_HCS.md")

GT_README = """# Ground Truth (GT)

Write your project's GT files here:

- `SRS.md` — System Requirements Specification
- `HCS.md` — Hardware Constraints Specification

These are **your** files: edit them freely. The expected structure is defined by the
locked reference templates in `.agents/skills/{skill}/templates/` — do not edit those.

Validate your GT files (deterministic, no AI):

```bash
python .agents/skills/{skill}/scripts/g0_validate.py GT/SRS.md GT/HCS.md
```

Exit code `0` means G0 passes; `1` means structural errors block the gate.
"""


def scaffold_project(name: str, target: Path) -> Path:
    project_dir = target.resolve() / name
    project_dir.mkdir(parents=True, exist_ok=True)

    _copy_skills(project_dir)
    _copy_gt_reference_templates(project_dir)
    _rewrite_skill_paths(project_dir / SKILLS_DIRNAME)
    _create_gt_dir(project_dir)
    _link_agent_skill_dirs(project_dir)

    log.info("scaffolded project '%s' at %s", name, project_dir)
    return project_dir


def _copy_skills(project_dir: Path) -> None:
    skills_src = TEMPLATES_DIR / "skills"
    if not skills_src.exists():
        log.warning("no skills templates found at %s", skills_src)
        return

    skills_dest = project_dir / SKILLS_DIRNAME
    shutil.copytree(skills_src, skills_dest, dirs_exist_ok=True, ignore=COPY_IGNORE)
    log.debug("copied skills to %s", skills_dest)


def _copy_gt_reference_templates(project_dir: Path) -> None:
    """GT templates are locked reference artifacts inside the G0 skill,
    not user-editable project files."""
    dest_dir = project_dir / SKILLS_DIRNAME / G0_SKILL_NAME / "templates"
    dest_dir.mkdir(parents=True, exist_ok=True)
    for template_name in GT_REFERENCE_TEMPLATES:
        src = TEMPLATES_DIR / "GT" / template_name
        if not src.exists():
            log.warning("GT reference template %s not found", src)
            continue
        shutil.copy2(src, dest_dir / template_name)
        log.debug("copied GT reference template %s -> %s", src, dest_dir / template_name)


def _rewrite_skill_paths(skills_root: Path) -> None:
    """Rewrite repo-root paths in copied .md files to project-relative paths."""
    if not skills_root.exists():
        return

    for md_file in skills_root.rglob("*.md"):
        original = md_file.read_text(encoding="utf-8")
        rewritten = original
        for old, new in PATH_REPLACEMENTS.items():
            rewritten = rewritten.replace(old, new)
        if rewritten != original:
            md_file.write_text(rewritten, encoding="utf-8")
            log.debug("rewrote paths in %s", md_file)


def _create_gt_dir(project_dir: Path) -> None:
    """User GT directory: empty except a README. Users write their own GT files."""
    gt_dir = project_dir / "GT"
    gt_dir.mkdir(exist_ok=True)
    readme = gt_dir / "README.md"
    if not readme.exists():
        readme.write_text(GT_README.format(skill=G0_SKILL_NAME), encoding="utf-8")


def _link_agent_skill_dirs(project_dir: Path) -> None:
    """Symlink each known agent runtime's skill dir to `.agents/skills`."""
    target = Path("..") / SKILLS_DIRNAME  # relative to each link's parent
    for agent_dir in AGENT_SKILL_DIRS:
        link = project_dir / agent_dir
        link.parent.mkdir(parents=True, exist_ok=True)

        if link.is_symlink():
            if link.readlink() == target:
                continue
            link.unlink()
        elif link.exists():
            log.warning("%s exists and is not a symlink — skipping", link)
            continue

        link.symlink_to(target)
        log.debug("symlinked %s -> %s", link, target)


def register_project(conn, name: str, path: Path) -> int:
    existing = conn.execute("SELECT id FROM projects WHERE name = ?", (name,)).fetchone()
    if existing:
        log.info("project '%s' already registered (id=%d) — skipping insert", name, existing["id"])
        return existing["id"]

    cur = conn.execute(
        "INSERT INTO projects (name, path) VALUES (?, ?)",
        (name, str(path)),
    )
    conn.commit()
    log.info("registered project '%s' (id=%d)", name, cur.lastrowid)
    return cur.lastrowid

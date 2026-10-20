import re
import shutil
from pathlib import Path

import yaml

from codeanvil.config.logger import get_logger
from codeanvil.config.paths import CONFIG, SKILLS_DIRNAME, TEMPLATES_DIR

log = get_logger(__name__)


def scaffold_project(name: str, target: Path, mcp_servers: list[str] | None = None) -> Path:
    project_dir = target.resolve() / name
    project_dir.mkdir(parents=True, exist_ok=True)

    _copy_skills(project_dir)
    _copy_gt_reference_templates(project_dir)
    _rewrite_skill_paths(project_dir / SKILLS_DIRNAME)
    _create_gt_dir(project_dir)

    if mcp_servers:
        from codeanvil.init.mcp import (
            copy_mcp_skills,
            generate_agent_mcp_configs,
            write_mcp_manifest,
        )
        for server in mcp_servers:
            copy_mcp_skills(server, project_dir)
        write_mcp_manifest(mcp_servers, project_dir)
        generate_agent_mcp_configs(mcp_servers, project_dir)

    _generate_agents_md(project_dir, mcp_servers=mcp_servers)
    _link_agent_skill_dirs(project_dir)
    _link_agent_configs(project_dir)

    log.info("scaffolded project '%s' at %s", name, project_dir)
    return project_dir


def _copy_skills(project_dir: Path) -> None:
    skills_src = TEMPLATES_DIR / "skills"
    if not skills_src.exists():
        log.warning("no skills templates found at %s", skills_src)
        return

    skills_dest = project_dir / SKILLS_DIRNAME
    shutil.copytree(skills_src, skills_dest, dirs_exist_ok=True, ignore=shutil.ignore_patterns(*CONFIG["copy_ignore"]))
    log.debug("copied skills to %s", skills_dest)


def _copy_gt_reference_templates(project_dir: Path) -> None:
    """GT templates are locked reference artifacts inside the G0 skill,
    not user-editable project files."""
    dest_dir = project_dir / SKILLS_DIRNAME / CONFIG["g0_skill"] / "templates"
    dest_dir.mkdir(parents=True, exist_ok=True)
    for template_name in CONFIG["gt_reference_templates"]:
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
        for old, new in CONFIG["path_replacements"].items():
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
        template = (TEMPLATES_DIR / "GT" / "README.md.template").read_text(encoding="utf-8")
        readme.write_text(template.format(skill=CONFIG["g0_skill"]), encoding="utf-8")


def _link_agent_skill_dirs(project_dir: Path) -> None:
    """Symlink each configured agent runtime skill dir to the canonical store."""
    for link_rel, target_str in CONFIG["agent_skill_links"].items():
        link = project_dir / link_rel
        target = Path(target_str)  # relative to the link's parent
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


# Frontmatter block at the very start of a SKILL.md file.
_FRONTMATTER_RE = re.compile(r"\A---[ \t]*\n(.*?)\n---[ \t]*(?:\n|\Z)", re.DOTALL)


def _parse_skill_frontmatter(skill_md: Path) -> dict | None:
    """Extract {name, description, gate} from a SKILL.md YAML frontmatter.

    Returns None when the file has no frontmatter (e.g. an empty
    placeholder SKILL.md) or when parsing fails — never raises."""
    try:
        text = skill_md.read_text(encoding="utf-8")
    except OSError as exc:
        log.warning("cannot read %s: %s", skill_md, exc)
        return None

    match = _FRONTMATTER_RE.match(text)
    if not match:
        return None  # empty file or no frontmatter — not an error

    try:
        metadata = yaml.safe_load(match.group(1))
    except yaml.YAMLError as exc:
        log.warning("cannot parse frontmatter in %s: %s", skill_md, exc)
        return None
    if not isinstance(metadata, dict):
        log.warning("frontmatter in %s is not a mapping — skipping", skill_md)
        return None

    nested = metadata.get("metadata") or {}
    gate = nested.get("gate") if isinstance(nested, dict) else None
    return {
        "name": metadata.get("name") or "",
        "description": metadata.get("description") or "",
        "gate": str(gate) if gate is not None else "",
    }


def _collect_skill_summaries(skills_root: Path) -> list[dict]:
    """Collect frontmatter summaries for every skill under skills_root.

    Skills without frontmatter (empty SKILL.md) are skipped. Each entry
    carries 'dir' — the skill directory name — so the AGENTS.md table can
    show the project-relative load path. Sorted by gate."""
    if not skills_root.is_dir():
        return []

    summaries = []
    for skill_md in sorted(skills_root.glob("*/SKILL.md")):
        summary = _parse_skill_frontmatter(skill_md)
        if summary is None:
            continue
        summary["dir"] = skill_md.parent.name
        summaries.append(summary)

    summaries.sort(key=lambda entry: (entry["gate"], entry["dir"]))
    return summaries


def _skill_table(summaries: list[dict]) -> str:
    """Render skill summaries as a markdown table (or a clear empty note)."""
    if not summaries:
        return (
            "_No skills available: no `SKILL.md` files with YAML frontmatter "
            "were found in `.agents/skills/`._"
        )

    lines = [
        "| Gate | Skill | Description |",
        "|------|-------|-------------|",
    ]
    for summary in summaries:
        # Collapse whitespace so multi-line descriptions stay one table row,
        # and escape pipes so they cannot break the table.
        description = " ".join(str(summary["description"]).split()).replace("|", "\\|")
        gate = summary["gate"] or "-"
        lines.append(f"| {gate} | `{summary['dir']}` | {description} |")
    return "\n".join(lines)


def _mcp_table(mcp_servers: list[str] | None) -> str:
    if not mcp_servers:
        return "_No MCP servers configured._"

    mcp_cfg = CONFIG.get("mcp_servers", {})
    lines = [
        "| Server | Description |",
        "|--------|-------------|",
    ]
    for name in mcp_servers:
        desc = mcp_cfg.get(name, {}).get("description", "")
        lines.append(f"| `{name}` | {desc} |")
    return "\n".join(lines)


def _generate_agents_md(project_dir: Path, mcp_servers: list[str] | None = None) -> None:
    """Generate the canonical AGENTS.md from the configured template,
    with the dynamic skill and MCP tables substituted in. Overwrites any
    existing file — AGENTS.md is generated, not hand-edited."""
    template_path = TEMPLATES_DIR.parent / CONFIG["agents_template"]
    try:
        template = template_path.read_text(encoding="utf-8")
    except OSError as exc:
        log.error("AGENTS template not found at %s: %s", template_path, exc)
        return

    # Collect skills from both CodeAnvil templates and the scaffolded project
    # (which may include MCP-provided skills copied earlier).
    skills_root = project_dir / SKILLS_DIRNAME
    if skills_root.is_dir():
        summaries = _collect_skill_summaries(skills_root)
    else:
        summaries = _collect_skill_summaries(TEMPLATES_DIR / "skills")

    content = template.replace("{skill_table}", _skill_table(summaries))
    content = content.replace("{mcp_table}", _mcp_table(mcp_servers))

    agents_md = project_dir / "AGENTS.md"
    agents_md.write_text(content, encoding="utf-8")
    log.debug("wrote %s (%d skill(s) in table)", agents_md, len(summaries))


def _link_agent_configs(project_dir: Path) -> None:
    """Symlink instruction files and write one-line pointer files, per config.

    Symlinks follow the same robustness rules as _link_agent_skill_dirs:
    a wrong symlink is fixed, a real file occupying the path is left alone
    with a warning. Pointer files are always regular files (a symlink at
    their path is replaced) so additive-reading agents never load the same
    content twice."""
    for link_rel, target_str in CONFIG["agent_config_links"].items():
        link = project_dir / link_rel
        target = Path(target_str)
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

    for file_rel, pointer_text in CONFIG["agent_pointer_files"].items():
        pointer = project_dir / file_rel
        pointer.parent.mkdir(parents=True, exist_ok=True)

        if pointer.is_dir():
            log.warning("%s exists and is a directory — skipping pointer file", pointer)
            continue
        if pointer.is_symlink():
            pointer.unlink()  # replace symlinks: pointer files must be regular files
        pointer.write_text(str(pointer_text).rstrip("\n") + "\n", encoding="utf-8")
        log.debug("wrote pointer file %s", pointer)

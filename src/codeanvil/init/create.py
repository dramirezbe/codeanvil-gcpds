import json
import shutil
import sys
from pathlib import Path

import yaml

from codeanvil.config.logger import get_logger
from codeanvil.skills import FRONTMATTER_RE as _FRONTMATTER_RE  # noqa: F401  (tests)
from codeanvil.skills import parse_skill_frontmatter as _parse_skill_frontmatter
from codeanvil.config.paths import (
    CONFIG,
    PROJECT_BACKUPS,
    PROJECT_CODEANVIL,
    PROJECT_CUSTODY,
    PROJECT_DESIGN,
    PROJECT_GT,
    PROJECT_MANIFEST,
    PROJECT_REPORT,
    SKILLS_DIRNAME,
    TEMPLATES_DIR,
)

log = get_logger(__name__)

_IS_WIN = sys.platform == "win32"


def _is_junction(path: Path) -> bool:
    """Path.is_junction() requires Python 3.12+; fall back for 3.10/3.11."""
    if hasattr(path, "is_junction"):
        return path.is_junction()
    if not _IS_WIN:
        return False
    import ctypes
    attrs = ctypes.windll.kernel32.GetFileAttributesW(str(path))  # type: ignore[attr-defined]
    _REPARSE = 0x400
    return attrs != -1 and bool(attrs & _REPARSE)


def _make_link(link: Path, target: Path) -> None:
    """Create a symlink, falling back on Windows when unprivileged.

    Directory targets fall back to a junction (no special privileges);
    file targets fall back to a copy (junctions only work for directories).
    """
    try:
        link.symlink_to(target)
        return
    except OSError:
        if not _IS_WIN:
            raise
    resolved = (link.parent / target).resolve()
    if resolved.is_dir():
        import _winapi
        _winapi.CreateJunction(str(resolved), str(link))
        log.debug("junction %s -> %s (symlink unavailable)", link, resolved)
    else:
        shutil.copy2(resolved, link)
        log.debug("copied %s -> %s (symlink unavailable)", link, resolved)


def scaffold_project(
    name: str,
    folder_name: str,
    target: Path,
    mcp_servers: list[str] | None = None,
) -> Path:
    """Scaffold a project directory under `target`.

    `name` is the human-readable label (manifest + DB); `folder_name` is the
    directory actually created, so "My SDR Lab" may live in `my_sdr_lab/`.
    """
    parent = target.resolve()
    project_dir = (parent / folder_name).resolve()
    if not project_dir.is_relative_to(parent):
        raise ValueError("project folder must stay inside the selected parent directory")
    project_dir.mkdir(parents=True, exist_ok=True)

    _copy_skills(project_dir)
    _copy_gt_reference_templates(project_dir)
    _rewrite_skill_paths(project_dir / SKILLS_DIRNAME)
    _create_codeanvil_dirs(project_dir)
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
    _write_subagents(project_dir)

    log.info("scaffolded project '%s' at %s", name, project_dir)
    return project_dir


def _copy_skills(project_dir: Path) -> None:
    skills_src = TEMPLATES_DIR / "skills"
    if not skills_src.exists():
        log.warning("no skills templates found at %s", skills_src)
        return

    skills_dest = project_dir / SKILLS_DIRNAME
    shutil.copytree(skills_src, skills_dest, dirs_exist_ok=True, ignore=shutil.ignore_patterns(*CONFIG["copy_ignore"]))
    _copy_shared_skill_assets(skills_src, skills_dest)
    log.debug("copied skills to %s", skills_dest)


def _copy_shared_skill_assets(skills_src: Path, skills_dest: Path) -> None:
    """Copy canonical locked assets into each configured, self-contained consumer.

    Assets are maintained once in the producer skill. Copied Markdown references
    are rebound to the consumer before the usual project-path rewrite.
    """
    def skill_dir(root: Path, name: str) -> Path:
        if not isinstance(name, str) or name in ("", ".", "..") or "/" in name or "\\" in name:
            raise ValueError(f"invalid shared asset skill name: {name!r}")
        path = root / name
        if not (path / "SKILL.md").is_file():
            raise FileNotFoundError(f"shared asset skill not found: {path}")
        return path.resolve()

    for producer, consumers in CONFIG.get("shared_skill_assets", {}).items():
        source_dir = skill_dir(skills_src, producer)
        for consumer, assets in consumers.items():
            destination_dir = skill_dir(skills_dest, consumer)
            for relative in assets:
                path = Path(relative)
                if path.is_absolute() or ".." in path.parts or "\\" in relative:
                    raise ValueError(f"shared skill asset path must be relative: {relative!r}")
                source = (source_dir / path).resolve()
                destination = (destination_dir / path).resolve()
                if not source.is_relative_to(source_dir) or not destination.is_relative_to(destination_dir):
                    raise ValueError(f"shared skill asset escapes its skill: {relative!r}")
                if not source.is_file():
                    raise FileNotFoundError(f"shared skill asset not found: {source}")
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, destination)
                if destination.suffix == ".md":
                    text = destination.read_text(encoding="utf-8")
                    destination.write_text(text.replace(f"templates/skills/{producer}/",
                                                        f"templates/skills/{consumer}/"), encoding="utf-8")
                log.debug("copied shared skill asset %s -> %s", source, destination)


def _copy_gt_reference_templates(project_dir: Path) -> None:
    """GT templates are locked reference artifacts inside their gate skill,
    not user-editable project files."""
    for skill_key in ("s0_skill", "g0_skill"):
        dest_dir = project_dir / SKILLS_DIRNAME / CONFIG[skill_key] / "templates"
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
    """Ground Truth directory under .codeanvil/: a README only. Users write
    their own GT files; S0 writes the pair from the Build Package."""
    gt_dir = project_dir / PROJECT_GT
    gt_dir.mkdir(parents=True, exist_ok=True)
    readme = gt_dir / "README.md"
    if not readme.exists():
        template = (TEMPLATES_DIR / "GT" / "README.md.template").read_text(encoding="utf-8")
        readme.write_text(template.format(skill=CONFIG["g0_skill"]), encoding="utf-8")


def _create_codeanvil_dirs(project_dir: Path) -> None:
    """The methodology tree: identity, GT, design, reports, backups, custody."""
    for path in (
        PROJECT_CODEANVIL,
        PROJECT_GT,
        PROJECT_DESIGN,
        PROJECT_REPORT,
        PROJECT_BACKUPS,
        PROJECT_CUSTODY,
    ):
        (project_dir / path).mkdir(parents=True, exist_ok=True)


def read_manifest_id(project_dir: Path) -> str | None:
    """Return the id from an existing .codeanvil/project.yaml, or None.

    None when the manifest is missing, unparseable, or has no valid id —
    callers fall back to minting a fresh UUID."""
    dest = project_dir / PROJECT_MANIFEST
    if not dest.is_file():
        return None
    try:
        data = yaml.safe_load(dest.read_text(encoding="utf-8"))
    except yaml.YAMLError:
        return None
    if not isinstance(data, dict):
        return None
    pid = data.get("id")
    return pid if isinstance(pid, str) and pid else None


def write_project_manifest(project_dir: Path, project_id: str, name: str) -> None:
    """Write .codeanvil/project.yaml — collaboration-safe project identity.
    Committed to git: UUID + label + relative GT pointers. No absolute path
    (the DB holds that local machine state).

    Skips the write when a manifest with the same id already exists, so
    re-scaffolding never rewrites a committed identity."""
    dest = project_dir / PROJECT_MANIFEST
    if read_manifest_id(project_dir) == project_id:
        log.debug("manifest %s already has id %s — skipping write", dest, project_id)
        return
    manifest = {
        "id": project_id,
        "name": name,
        "gt": {
            "strs": ".codeanvil/GT/StRS.md",
            "syrs": ".codeanvil/GT/SyRS.md",
        },
    }
    dest.parent.mkdir(parents=True, exist_ok=True)
    content = (
        "# Auto-generated by codeanvil. Agents maintain the 'cycle' key; "
        "do not edit other keys.\n\n"
    )
    content += yaml.dump(manifest, default_flow_style=False, sort_keys=False)
    dest.write_text(content, encoding="utf-8")
    log.debug("wrote %s", dest)


def _link_agent_skill_dirs(project_dir: Path) -> None:
    """Link each configured agent runtime skill dir to the canonical store.

    Uses symlinks where possible; falls back to junctions on Windows."""
    for link_rel, target_str in CONFIG["agent_skill_links"].items():
        link = project_dir / link_rel
        target = Path(target_str)  # relative to the link's parent
        link.parent.mkdir(parents=True, exist_ok=True)

        if link.is_symlink() or (_IS_WIN and _is_junction(link)):
            if link.is_symlink() and link.readlink() == target:
                continue
            link.unlink()
        elif link.exists():
            log.warning("%s exists and is not a symlink — skipping", link)
            continue

        _make_link(link, target)
        log.debug("linked %s -> %s", link, target)


# Frontmatter block at the very start of a SKILL.md file.
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


def _configured_skills() -> dict[str, str | None]:
    """Skill directory name -> prerequisite report id, in chain order.

    Declaration order in config.yaml is the gate chain; `None` marks an
    entry point. Skills absent here (for example MCP-provided ones) have no
    prerequisite entry in the generated table."""
    return {
        Path(cfg["project_dir"]).name: cfg.get("prerequisite")
        for cfg in CONFIG.get("skills", {}).values()
    }


def _order_summaries(
    summaries: list[dict], configured: dict[str, str | None]
) -> list[dict]:
    """Configured skills first, in chain order; then any remaining skill."""
    by_dir = {summary["dir"]: summary for summary in summaries}
    ordered = [by_dir.pop(name) for name in configured if name in by_dir]
    ordered.extend(sorted(by_dir.values(), key=lambda entry: (entry["gate"], entry["dir"])))
    return ordered


def _prerequisite_cell(skill_dir: str, prerequisites: dict[str, str | None]) -> str:
    """The prerequisite report a skill checks before it runs."""
    if skill_dir not in prerequisites:
        return "-"
    prerequisite = prerequisites[skill_dir]
    if prerequisite is None:
        return "None (entry point)"
    return f"`{prerequisite}.md` latest iteration `HITL: PASS`"


def _skill_table(
    summaries: list[dict], prerequisites: dict[str, str | None] | None = None
) -> str:
    """Render skill summaries as the chain table (or a clear empty note)."""
    if not summaries:
        return (
            "_No skills available: no `SKILL.md` files with YAML frontmatter "
            "were found in `.agents/skills/`._"
        )

    prerequisites = prerequisites or {}
    lines = [
        "| Gate | Skill | Prerequisite |",
        "|------|-------|--------------|",
    ]
    for summary in summaries:
        gate = summary["gate"] or "-"
        skill_path = f".agents/skills/{summary['dir']}/"
        prerequisite = _prerequisite_cell(summary["dir"], prerequisites)
        lines.append(f"| {gate} | `{skill_path}` | {prerequisite} |")
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

    prerequisites = _configured_skills()
    summaries = _order_summaries(summaries, prerequisites)
    content = template.replace("{skill_table}", _skill_table(summaries, prerequisites))
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

        if link.is_symlink() or (_IS_WIN and _is_junction(link)):
            if link.is_symlink() and link.readlink() == target:
                continue
            link.unlink()
        elif link.exists():
            log.warning("%s exists and is not a symlink — skipping", link)
            continue

        _make_link(link, target)
        log.debug("linked %s -> %s", link, target)

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


def _write_subagents(project_dir: Path) -> None:
    """Write each configured subagent in every runtime's own format.

    One shared body per subagent, one header per runtime: Markdown files get
    a YAML frontmatter, TOML files get flat string fields plus the body as
    `developer_instructions`. Always overwritten — generated, not hand-edited."""
    for name, cfg in CONFIG.get("subagents", {}).items():
        body_path = TEMPLATES_DIR.parent / cfg["body"]
        try:
            body = body_path.read_text(encoding="utf-8")
        except OSError as exc:
            log.error("subagent body for '%s' not found at %s: %s", name, body_path, exc)
            continue

        for runtime, target in cfg["targets"].items():
            dest = project_dir / target["path"]
            if target["format"] == "markdown":
                meta = {**target.get("frontmatter", {}), "description": cfg["description"]}
                header = yaml.safe_dump(meta, sort_keys=False, allow_unicode=True, width=10**6)
                content = f"---\n{header}---\n\n{body}"
            elif target["format"] == "toml":
                fields = {**target.get("fields", {}), "description": cfg["description"]}
                lines = [f"{key} = {json.dumps(str(value), ensure_ascii=False)}" for key, value in fields.items()]
                escaped = body.replace("\\", "\\\\").replace('"""', '""\\"')
                content = "\n".join(lines) + f'\ndeveloper_instructions = """\n{escaped}"""\n'
            else:
                log.warning("unknown subagent format '%s' for %s — skipping", target["format"], runtime)
                continue
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(content, encoding="utf-8")
            log.debug("wrote %s subagent %s", runtime, dest)

"""SKILL.md frontmatter, read once for `create` (AGENTS.md table) and
`python` (the skill's declared runtime packages)."""

import re
from pathlib import Path

import yaml

from codeanvil.config.logger import get_logger

log = get_logger(__name__)

FRONTMATTER_RE = re.compile(r"\A---[ \t]*\n(.*?)\n---[ \t]*(?:\n|\Z)", re.DOTALL)


def parse_skill_frontmatter(skill_md: Path) -> dict | None:
    """Extract {name, description, gate, runtime} from a SKILL.md frontmatter.

    `runtime` is the list under `metadata.runtime`: the packages the skill's
    scripts need in the methodology runtime. Returns None when the file has no
    frontmatter (e.g. an empty placeholder SKILL.md) or when parsing fails —
    never raises."""
    try:
        text = skill_md.read_text(encoding="utf-8")
    except OSError as exc:
        log.warning("cannot read %s: %s", skill_md, exc)
        return None

    match = FRONTMATTER_RE.match(text)
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
    if not isinstance(nested, dict):
        nested = {}
    gate = nested.get("gate")
    runtime = nested.get("runtime") or []
    if not isinstance(runtime, list):
        log.warning("metadata.runtime in %s is not a list — ignoring it", skill_md)
        runtime = []
    return {
        "name": metadata.get("name") or "",
        "description": metadata.get("description") or "",
        "gate": str(gate) if gate is not None else "",
        "runtime": [str(package) for package in runtime],
    }

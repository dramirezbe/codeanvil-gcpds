"""Guard test: enforce D14 custody rule (no hand-computed hashes in skills)."""

import re
from pathlib import Path


def test_no_hand_computed_hashes_in_skills():
    """Fail if any skill contains forbidden hash computation instructions.
    
    Per D14 (plan §3.5): every digest comes only from `codeanvil custody digest`.
    Forbidden patterns: hashlib, python -c sha256, sha256sum, shasum, Get-FileHash.
    """
    templates_dir = Path(__file__).parent.parent / "templates" / "skills"
    
    # Patterns that indicate hand-computed hashes
    forbidden_patterns = [
        r"hashlib",
        r"sha256sum",
        r"shasum",
        r"Get-FileHash",
    ]
    
    findings = []
    for skill_md in templates_dir.rglob("*.md"):
        # Skip backups and no-tools-skills (not scaffolded)
        if "backups" in str(skill_md) or "no-tools-skills" in str(skill_md):
            continue
        
        content = skill_md.read_text(encoding="utf-8")
        for pattern in forbidden_patterns:
            if re.search(pattern, content):
                findings.append(f"{skill_md.relative_to(templates_dir.parent)}: {pattern}")
    
    assert not findings, f"Forbidden hash patterns found (use `codeanvil custody digest`):\n" + "\n".join(findings)


def test_scaffolded_skills_have_no_hand_computed_hashes(tmp_path):
    """Verify that scaffolded projects' `.agents/skills/` have no forbidden patterns."""
    from codeanvil.init.create import scaffold_project
    
    # Scaffold a project to tmp_path
    project_root = tmp_path / "test_proj"
    scaffold_project(
        name="TestProj",
        folder_name="test_proj",
        target=tmp_path,
        mcp_servers=[],
    )
    
    # Check all .md files in .agents/skills/
    skills_dir = project_root / ".agents" / "skills"
    findings = []
    
    forbidden_patterns = [
        r"hashlib",
        r"sha256sum",
        r"shasum",
        r"Get-FileHash",
    ]
    
    for skill_md in skills_dir.rglob("*.md"):
        content = skill_md.read_text(encoding="utf-8")
        for pattern in forbidden_patterns:
            if re.search(pattern, content):
                findings.append(f"{skill_md.relative_to(skills_dir)}: {pattern}")
    
    assert not findings, f"Forbidden patterns in scaffolded skills:\n" + "\n".join(findings)

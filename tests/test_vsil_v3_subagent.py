"""T9: `codeanvil create` ships the read-only `vsil-verifier` subagent per runtime."""

from pathlib import Path

import yaml

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    import tomli as tomllib

from codeanvil.CLI.commands.create import cmd_create
from codeanvil.config.paths import TEMPLATES_DIR
from codeanvil.init.create import _FRONTMATTER_RE, scaffold_project
from test_create import db_path  # noqa: F401  (db_path is a fixture)

BODY = TEMPLATES_DIR / "agents" / "vsil-verifier.md"
CLAUDE = Path(".claude/agents/vsil-verifier.md")
OPENCODE = Path(".opencode/agents/vsil-verifier.md")
CODEX = Path(".codex/agents/vsil-verifier.toml")


def _scaffold(tmp_path) -> Path:
    return scaffold_project("Proj", "proj", tmp_path)


def _split_markdown(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8")
    match = _FRONTMATTER_RE.match(text)
    assert match, f"{path} has no frontmatter"
    return yaml.safe_load(match.group(1)), text[match.end():].lstrip("\n")


def test_scaffold_writes_the_subagent_for_every_runtime(tmp_path):
    project = _scaffold(tmp_path)

    for rel in (CLAUDE, OPENCODE, CODEX):
        assert (project / rel).is_file(), rel


def test_every_runtime_file_carries_the_shared_body_unchanged(tmp_path):
    project = _scaffold(tmp_path)
    body = BODY.read_text(encoding="utf-8")

    for rel in (CLAUDE, OPENCODE):
        meta, text = _split_markdown(project / rel)
        assert text == body
        assert meta["description"]

    codex = tomllib.loads((project / CODEX).read_text(encoding="utf-8"))
    assert codex["name"] == "vsil-verifier"
    assert codex["description"]
    assert codex["developer_instructions"] == body


def test_the_subagent_has_no_edit_or_write_tools(tmp_path):
    project = _scaffold(tmp_path)

    claude, _ = _split_markdown(project / CLAUDE)
    assert claude["name"] == "vsil-verifier"
    tools = [tool.strip() for tool in claude["tools"].split(",")]
    assert "Edit" not in tools and "Write" not in tools
    assert "Bash" in tools

    opencode, _ = _split_markdown(project / OPENCODE)
    assert opencode["mode"] == "subagent"
    assert opencode["permission"]["edit"] == "deny"


def test_verifier_mcp_tools_allow_run_fetch_but_never_deploy_or_setup(tmp_path):
    project = _scaffold(tmp_path)
    claude, _ = _split_markdown(project / CLAUDE)
    claude_tools = {tool.strip() for tool in claude["tools"].split(",")}
    opencode, _ = _split_markdown(project / OPENCODE)
    permissions = opencode["permission"]

    for tool in ("probe_target", "ssh_exec_cmd", "fetch_evidence"):
        assert f"mcp__vsil_hil_mcp__{tool}" in claude_tools
        assert permissions[f"vsil_hil_mcp_{tool}"] == "allow"
    for tool in ("code_sync", "init_codeanvil", "ssh_exec_cmd_trusted"):
        assert f"mcp__vsil_hil_mcp__{tool}" not in claude_tools
        assert permissions[f"vsil_hil_mcp_{tool}"] == "deny"

    body = BODY.read_text(encoding="utf-8")
    assert "Codex inherits its host permissions" in body
    assert "`code_sync`, `init_codeanvil`" in body
    assert "Ask the human anything" in body
    assert "real HW command/scripts yourself" in body


def test_rescaffolding_writes_the_same_bytes(tmp_path):
    project = _scaffold(tmp_path)
    first = {rel: (project / rel).read_bytes() for rel in (CLAUDE, OPENCODE, CODEX)}

    _scaffold(tmp_path)

    assert {rel: (project / rel).read_bytes() for rel in first} == first


def test_body_names_the_run_commands_and_the_never_list():
    body = BODY.read_text(encoding="utf-8")

    assert "test_run.md" in body
    assert "Edit or create source" in body


def test_existing_scaffold_links_and_agents_md_still_hold(tmp_path, db_path):
    cmd_create(None, tmp_path, project_name="Proj")
    project = tmp_path / "proj"

    assert (project / ".claude" / "skills").is_symlink()
    assert (project / ".claude" / "skills").readlink() == Path("../.agents/skills")
    assert (project / ".opencode" / "skills").is_symlink()
    assert (project / ".codex" / "skills").is_symlink()
    assert (project / "CLAUDE.md").readlink() == Path("AGENTS.md")
    assert "{skill_table}" not in (project / "AGENTS.md").read_text(encoding="utf-8")

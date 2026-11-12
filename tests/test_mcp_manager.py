"""MCP manager (WU-M1–M5): pinned installs, probes, launcher, portable configs."""

import json
import os
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest
import yaml

from codeanvil.config.paths import CONFIG
from codeanvil.init import mcp
from codeanvil.init import system_packages as syspkg

LAUNCHER = {"command": "codeanvil", "args": ["mcp", "run", "marconi"], "env": {}}


# --- WU-M1: every server is pinned --------------------------------------------


def test_every_configured_server_pins_a_ref():
    for name, cfg in CONFIG["mcp_servers"].items():
        if cfg.get("source") == "bundled":
            continue  # pinned by the wheel it ships in, not by a git ref
        assert cfg.get("ref"), f"{name} has no pinned ref"
        assert cfg["ref"] not in ("main", "master", "HEAD"), f"{name} pins a branch head"


def _git(*args, cwd):
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True,
                   env={**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
                        "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"})
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=cwd, capture_output=True,
                          text=True).stdout.strip()


def test_checkout_follows_the_pinned_ref_never_the_branch_head(tmp_path):
    upstream = tmp_path / "upstream"
    upstream.mkdir()
    _git("init", "-q", cwd=upstream)
    (upstream / "a").write_text("1")
    _git("add", "a", cwd=upstream)
    first = _git("commit", "-qm", "one", cwd=upstream)
    (upstream / "a").write_text("2")
    _git("commit", "-qam", "two", cwd=upstream)

    dest = tmp_path / "mcp" / "srv"
    mcp._checkout_ref("srv", {"repo": str(upstream), "ref": first}, dest)
    assert mcp._head(dest) == first  # the head of the branch is "two"

    second = _git("rev-parse", "HEAD", cwd=upstream)
    mcp._checkout_ref("srv", {"repo": str(upstream), "ref": second}, dest)
    assert mcp._head(dest) == second


def test_checkout_without_a_ref_is_refused(tmp_path):
    with pytest.raises(mcp.McpError, match="ref is not set"):
        mcp._checkout_ref("srv", {"repo": "x"}, tmp_path / "srv")


def test_failing_commands_raise_with_their_stderr():
    with pytest.raises(mcp.McpError, match="fatal"):
        mcp._run(["git", "-C", "/nonexistent-dir-for-test", "status"], "git status")


# --- WU-M5: probes -------------------------------------------------------------


@pytest.fixture
def fake_package(monkeypatch):
    """A system package `fakepkg` whose probe and location the test controls."""
    spec = {"probe": "print('1.2.3')", "install": {"debian": "sudo apt install fakepkg",
                                                   "arch": "sudo pacman -S fakepkg"}}
    monkeypatch.setitem(CONFIG.setdefault("system_packages", {}), "fakepkg", spec)
    return spec


def _running():
    return "%d.%d" % sys.version_info[:2]


def test_probe_ok_reports_the_version(fake_package, monkeypatch):
    result = syspkg.probe("fakepkg", Path(sys.executable), "the test venv")
    assert result.ok and result.version == "1.2.3"


def test_probe_missing_gives_the_install_instruction(fake_package, monkeypatch):
    fake_package["probe"] = "raise SystemExit(1)"
    monkeypatch.setattr(syspkg, "detect_system_site_packages", lambda pkg: None)
    monkeypatch.setattr(syspkg, "os_family", lambda os_release=None: ["ubuntu", "debian"])

    result = syspkg.probe("fakepkg", Path(sys.executable), "the test venv")

    assert result.status == "missing"
    assert "sudo apt install fakepkg" in result.message


def test_probe_detects_an_abi_mismatch(fake_package, monkeypatch):
    fake_package["probe"] = "raise SystemExit(1)"
    monkeypatch.setattr(syspkg, "detect_system_site_packages",
                        lambda pkg: "/usr/lib/python3.99/site-packages")

    result = syspkg.probe("fakepkg", Path(sys.executable), "the test venv")

    assert result.status == "mismatch"
    assert result.message == f"fakepkg is built for Python 3.99; the test venv runs {_running()}."


def test_probe_reports_a_broken_install_with_its_error(fake_package, monkeypatch):
    fake_package["probe"] = "import sys; sys.exit('ImportError: libgnuradio.so missing')"
    monkeypatch.setattr(syspkg, "detect_system_site_packages",
                        lambda pkg: f"/usr/lib/python{_running()}/site-packages")

    result = syspkg.probe("fakepkg", Path(sys.executable), "the test venv")

    assert result.status == "broken"
    assert "libgnuradio.so missing" in result.message


@pytest.mark.skipif(sys.platform in ("darwin", "win32"), reason="os-release is Linux only")
@pytest.mark.parametrize(("release", "expected"), [
    ({"ID": "ubuntu", "ID_LIKE": "debian"}, "sudo apt install fakepkg"),
    ({"ID": "omarchy", "ID_LIKE": "arch"}, "sudo pacman -S fakepkg"),
    ({"ID": "plan9"}, "debian: sudo apt install fakepkg; arch: sudo pacman -S fakepkg"),
])
def test_install_hint_follows_the_os_family(fake_package, release, expected):
    assert syspkg.install_hint("fakepkg", release) == expected


def test_gnuradio_install_hints_are_runtime_packages_not_dev():
    install = CONFIG["system_packages"]["gnuradio"]["install"]
    assert {"arch", "debian", "fedora", "darwin", "win32"} <= set(install)
    assert not any("-dev" in command for command in install.values())


def test_system_interpreter_is_an_explicit_path(tmp_path):
    prefix = tmp_path / "usr"
    (prefix / "bin").mkdir(parents=True)
    (prefix / "bin" / "python3.14").write_text("")
    site = prefix / "lib" / "python3.14" / "site-packages"
    site.mkdir(parents=True)

    assert syspkg.system_interpreter_for(str(site)) == prefix / "bin" / "python3.14"


def test_cached_probe_skips_the_import_until_the_package_changes(fake_package, monkeypatch, tmp_path):
    site = tmp_path / "site"
    (site / "fakepkg").mkdir(parents=True)
    monkeypatch.setattr(syspkg, "detect_system_site_packages", lambda pkg: str(site))
    calls = []
    real_probe = syspkg.probe
    monkeypatch.setattr(syspkg, "probe", lambda *a: calls.append(1) or real_probe(*a))
    cache = tmp_path / ".probe.json"

    syspkg.cached_probe("fakepkg", Path(sys.executable), "venv", cache)
    syspkg.cached_probe("fakepkg", Path(sys.executable), "venv", cache)
    assert len(calls) == 1

    os.utime(site / "fakepkg", (1, 1))  # the package was reinstalled
    syspkg.cached_probe("fakepkg", Path(sys.executable), "venv", cache)
    assert len(calls) == 2


def test_a_failed_probe_is_never_cached(fake_package, monkeypatch, tmp_path):
    fake_package["probe"] = "raise SystemExit(1)"
    site = tmp_path / "site"
    (site / "fakepkg").mkdir(parents=True)
    monkeypatch.setattr(syspkg, "detect_system_site_packages", lambda pkg: str(site))
    cache = tmp_path / ".probe.json"

    assert not syspkg.cached_probe("fakepkg", Path(sys.executable), "venv", cache).ok
    assert not cache.exists()


# --- WU-M4: portable configs, enable/disable -----------------------------------


def _configs(project: Path) -> dict:
    return {
        "claude": json.loads((project / ".mcp.json").read_text())["mcpServers"],
        "vscode": json.loads((project / ".vscode" / "mcp.json").read_text())["servers"],
        "opencode": json.loads((project / "opencode.json").read_text())["mcp"],
        "codex": json.loads((project / ".codex" / "mcp.json").read_text())["mcp_servers"],
    }


def test_configs_call_the_launcher_and_hold_no_absolute_path(tmp_path):
    first, second = tmp_path / "a" / "proj", tmp_path / "elsewhere" / "deeper" / "proj"
    for project in (first, second):
        project.mkdir(parents=True)
        mcp.generate_agent_mcp_configs(["marconi"], project)
        mcp.write_mcp_manifest(["marconi"], project)

    configs = _configs(first)
    assert configs == _configs(second)  # same bytes wherever the project lives
    assert configs["claude"]["marconi"] == LAUNCHER
    assert configs["opencode"]["marconi"]["command"] == ["codeanvil", "mcp", "run", "marconi"]
    blob = json.dumps(configs) + (first / ".agents" / "mcp.yaml").read_text()
    assert str(tmp_path) not in blob and "PYTHONPATH" not in blob and "/" not in blob.replace("https://", "")


@pytest.fixture
def old_project(tmp_path, monkeypatch):
    """A project scaffolded before the launcher: absolute uv command and env."""
    project = tmp_path / "old"
    (project / ".codeanvil").mkdir(parents=True)
    (project / ".codeanvil" / "project.yaml").write_text("id: x\n")
    (project / ".agents" / "skills").mkdir(parents=True)
    old = {"command": "uv", "args": ["--directory", "/home/u/.codeanvil-config/mcp/marconi", "run"],
           "env": {"MARCONI_WORKSPACE": "/home/u/old", "PYTHONPATH": "/usr/lib/python3.14/site-packages"}}
    (project / ".mcp.json").write_text(json.dumps({"mcpServers": {"marconi": old, "other": {"command": "x"}}}))
    (project / ".agents" / "mcp.yaml").write_text(yaml.safe_dump({"mcp_servers": {"marconi": old}}))
    (project / "AGENTS.md").write_text(
        "# A\n\n## MCP Servers\n\n_No MCP servers configured._\n\nMCP servers provide tool-calling x\n"
    )
    monkeypatch.setattr(mcp, "is_mcp_installed", lambda name: True)
    copied = []
    monkeypatch.setattr(mcp, "copy_mcp_skills", lambda name, project_dir: copied.append(name) or [])
    return project, copied


def test_enable_rewrites_an_old_absolute_config(old_project):
    project, copied = old_project

    servers = mcp.enable_server("marconi", project)

    assert servers == ["marconi"] and copied == ["marconi"]
    configs = _configs(project)
    assert configs["claude"]["marconi"] == LAUNCHER
    assert configs["claude"]["other"] == {"command": "x"}  # other servers are left alone
    assert "/home/u" not in (project / ".agents" / "mcp.yaml").read_text()
    assert "| `marconi` |" in (project / "AGENTS.md").read_text()
    enabled = json.loads((project / ".claude" / "settings.json").read_text())["enabledMcpjsonServers"]
    assert enabled == ["marconi"]


def test_disable_unwires_skills_configs_and_agents_md(old_project):
    project, _ = old_project
    mcp.enable_server("marconi", project)
    skills = project / ".agents" / "skills"
    (skills / "marconi-survey").mkdir()
    (skills / "marconi-LICENSE").write_text("GPL")
    (skills / "S0_keep").mkdir()

    assert mcp.disable_server("marconi", project) == []

    assert not (skills / "marconi-survey").exists() and not (skills / "marconi-LICENSE").exists()
    assert (skills / "S0_keep").is_dir()
    configs = _configs(project)
    assert all("marconi" not in section for section in configs.values())
    enabled = json.loads((project / ".claude" / "settings.json").read_text())["enabledMcpjsonServers"]
    assert enabled == []
    assert "_No MCP servers configured._" in (project / "AGENTS.md").read_text()


# --- WU-M3: launcher -----------------------------------------------------------


@pytest.fixture
def fake_install(tmp_path, monkeypatch):
    monkeypatch.setattr(mcp, "MCP_DIR", tmp_path / "mcp")
    install = tmp_path / "mcp" / "marconi"
    python = mcp.venv_python(install)
    python.parent.mkdir(parents=True)
    python.write_text("")
    monkeypatch.setattr(mcp, "probe_server", lambda name, use_cache=True: [])
    return install


def test_launcher_resolves_the_project_from_a_nested_cwd(fake_install, tmp_path, monkeypatch):
    project = tmp_path / "proj"
    (project / ".codeanvil").mkdir(parents=True)
    (project / ".codeanvil" / "project.yaml").write_text("id: x\n")
    nested = project / "src" / "deep"
    nested.mkdir(parents=True)
    monkeypatch.setenv("PYTHONPATH", "/stale/bridge")

    argv, env = mcp.launch_spec("marconi", nested)

    assert argv == [str(mcp.venv_bin(fake_install) / "marconi-mcp")]
    assert env["MARCONI_WORKSPACE"] == str(project)
    assert "PYTHONPATH" not in env


def test_launcher_refuses_a_failed_probe(fake_install, monkeypatch, tmp_path):
    bad = syspkg.ProbeResult("gnuradio", "mismatch", "gnuradio is built for Python 3.14; the marconi venv runs 3.15. Run codeanvil mcp update marconi.")
    monkeypatch.setattr(mcp, "probe_server", lambda name, use_cache=True: [bad])

    with pytest.raises(mcp.McpError, match="Run codeanvil mcp update marconi"):
        mcp.launch_spec("marconi", tmp_path)


def test_launcher_refuses_a_missing_install(tmp_path, monkeypatch):
    monkeypatch.setattr(mcp, "MCP_DIR", tmp_path / "mcp")
    with pytest.raises(mcp.McpError, match="Run codeanvil mcp add marconi"):
        mcp.launch_spec("marconi", tmp_path)


def test_mcp_run_failure_keeps_stdout_empty(tmp_path):
    """The client reads stdout as protocol: a failure is one stderr line."""
    env = {**os.environ, "HOME": str(tmp_path), "USERPROFILE": str(tmp_path)}
    env.pop("PYTHONPATH", None)

    result = subprocess.run([sys.executable, "-m", "codeanvil", "mcp", "run", "marconi"],
                            capture_output=True, text=True, env=env, cwd=tmp_path, timeout=60)

    assert result.returncode == 1
    assert result.stdout == ""
    assert "Run codeanvil mcp add marconi." in result.stderr


ECHO_SERVER = textwrap.dedent("""
    import sys
    for line in sys.stdin:
        sys.stdout.write(line.upper())
        sys.stdout.flush()
    sys.exit(3)
""")

LAUNCH = textwrap.dedent("""
    import sys
    from pathlib import Path
    from codeanvil.config.paths import CONFIG
    from codeanvil.init import mcp
    mcp.MCP_DIR = Path(sys.argv[1])
    CONFIG["mcp_servers"]["echo"] = {"install_dir": "mcp/echo", "command": sys.executable,
                                     "args": [sys.argv[2]], "env": {}}
    sys.exit(mcp.run_server("echo"))
""")


def test_launcher_stdio_round_trip_and_exit_code(tmp_path):
    """Run by CI on Linux; must also be run by hand on Windows before release."""
    install = tmp_path / "mcp" / "echo"
    python = mcp.venv_python(install)
    python.parent.mkdir(parents=True)
    python.write_text("")
    server = tmp_path / "echo_server.py"
    server.write_text(ECHO_SERVER)

    result = subprocess.run([sys.executable, "-c", LAUNCH, str(tmp_path / "mcp"), str(server)],
                            input='{"jsonrpc": "2.0"}\nping\n', capture_output=True, text=True,
                            timeout=60)

    assert result.stdout == '{"JSONRPC": "2.0"}\nPING\n'  # nothing but the server's bytes
    assert result.returncode == 3


# --- WU-M2: list, doctor, remove ----------------------------------------------


def test_doctor_names_every_problem_of_a_missing_install(tmp_path, monkeypatch):
    monkeypatch.setattr(mcp, "MCP_DIR", tmp_path / "mcp")
    checks = {check: (ok, detail) for check, ok, detail in mcp.doctor("marconi")}

    assert checks["installed"] == (False, "Run codeanvil mcp add marconi.")
    assert "uv on PATH" in checks


def test_list_shows_configured_servers_even_when_not_installed(tmp_path, monkeypatch):
    monkeypatch.setattr(mcp, "MCP_DIR", tmp_path / "mcp")
    [row] = [row for row in mcp.server_rows() if row["name"] == "marconi"]

    assert row["installed"] is False and row["ref"] == CONFIG["mcp_servers"]["marconi"]["ref"]


def test_remove_refuses_while_projects_use_the_server(tmp_path, monkeypatch):
    monkeypatch.setattr(mcp, "MCP_DIR", tmp_path / "mcp")
    (tmp_path / "mcp" / "marconi").mkdir(parents=True)
    monkeypatch.setattr(mcp, "projects_using", lambda name: [("Lab", "/p/lab")])

    with pytest.raises(mcp.McpError, match="1 project"):
        mcp.remove_mcp_server("marconi")
    assert (tmp_path / "mcp" / "marconi").is_dir()

    assert mcp.remove_mcp_server("marconi", force=True) == [("Lab", "/p/lab")]
    assert not (tmp_path / "mcp" / "marconi").exists()


def test_unknown_server_is_a_clear_error():
    with pytest.raises(mcp.McpError, match="unknown MCP server 'nope'"):
        mcp.doctor("nope")


# --- bundled first-party servers (vsil_hil_mcp) ---------------------------------


@pytest.fixture
def stub_install(tmp_path, monkeypatch):
    """Fake `uv` and probes: record `_run` calls, make `uv sync` create the venv."""
    monkeypatch.setattr(mcp, "MCP_DIR", tmp_path / "mcp")
    monkeypatch.setattr(mcp.shutil, "which", lambda tool: f"/usr/bin/{tool}")
    calls = []

    def fake_run(args, what):
        calls.append(args)
        if args[1:2] == ["sync"]:
            python = mcp.venv_python(Path(args[args.index("--directory") + 1]))
            python.parent.mkdir(parents=True, exist_ok=True)
            python.write_text("")
        return ""

    monkeypatch.setattr(mcp, "_run", fake_run)
    return calls


def test_bundled_server_is_configured_without_git_fields():
    cfg = CONFIG["mcp_servers"]["vsil_hil_mcp"]
    assert cfg["source"] == "bundled"
    assert not {"repo", "ref", "system_packages"} & set(cfg)
    assert (mcp.TEMPLATES_DIR / "mcp" / "vsil_hil_mcp" / "uv.lock").is_file()


def test_bundled_install_copies_from_the_wheel_and_builds_a_plain_venv(stub_install, tmp_path):
    dest = mcp.install_mcp_server("vsil_hil_mcp")

    assert dest == (tmp_path / "mcp" / "vsil_hil_mcp").resolve()
    assert (dest / "pyproject.toml").is_file() and (dest / "uv.lock").is_file()
    assert (dest / "vsil_hil_mcp" / "server.py").is_file()
    assert (dest / "skills" / "usage" / "SKILL.md").is_file()
    assert not any(call[0] == "git" for call in stub_install)  # never cloned
    [sync] = [call for call in stub_install if call[1:2] == ["sync"]]
    assert "--python" not in sync  # no system packages -> plain venv
    assert mcp.venv_python(dest).exists()


def test_bundled_install_is_idempotent_and_refreshes_source(stub_install, tmp_path):
    dest = mcp.install_mcp_server("vsil_hil_mcp")
    (dest / "vsil_hil_mcp" / "server.py").write_text("stale")
    mcp.install_mcp_server("vsil_hil_mcp")

    assert "FastMCP" in (dest / "vsil_hil_mcp" / "server.py").read_text()
    assert mcp.venv_python(dest).exists()


def test_bundled_row_has_no_git_head_and_flips_to_installed(stub_install):
    [before] = [r for r in mcp.server_rows() if r["name"] == "vsil_hil_mcp"]
    assert before["installed"] is False and before["source"] == "bundled" and before["pinned"] is False

    mcp.install_mcp_server("vsil_hil_mcp")
    [after] = [r for r in mcp.server_rows() if r["name"] == "vsil_hil_mcp"]
    assert after["installed"] is True and after["pinned"] is True
    assert after["ref"] == "bundled" and after["head"] == ""


def test_bundled_doctor_does_not_ask_for_a_git_pin(stub_install):
    mcp.install_mcp_server("vsil_hil_mcp")
    checks = {check: ok for check, ok, _ in mcp.doctor("vsil_hil_mcp")}

    assert checks["bundled source"] and "pinned ref" not in checks and checks["venv"]


def test_hil_launcher_passes_host_version_and_relocatable_workspace(stub_install, tmp_path, monkeypatch):
    mcp.install_mcp_server("vsil_hil_mcp")
    monkeypatch.setattr(mcp, "__version__", "0.7.5")
    monkeypatch.setenv("VSIL_HIL_CODEANVIL_VERSION", "unrelated-version")
    project = tmp_path / "moved" / "project"
    nested = project / "nested"
    nested.mkdir(parents=True)
    (project / ".codeanvil").mkdir()
    (project / ".codeanvil" / "project.yaml").write_text("name: project\n")

    argv, env = mcp.launch_spec("vsil_hil_mcp", nested)

    assert env["VSIL_HIL_CODEANVIL_VERSION"] == "0.7.5"
    assert env["VSIL_HIL_WORKSPACE"] == str(project)
    assert "vsil-hil-mcp" in argv[0]


def test_bundled_skill_is_copied_with_the_vsil_hil_prefix(stub_install, tmp_path):
    mcp.install_mcp_server("vsil_hil_mcp")
    project = tmp_path / "proj"
    project.mkdir()

    assert mcp.copy_mcp_skills("vsil_hil_mcp", project) == ["vsil-hil-usage"]


def test_git_servers_still_clone_and_pin(monkeypatch, tmp_path):
    """marconi keeps the clone path: _checkout_ref runs, the bundled copy never does."""
    monkeypatch.setattr(mcp, "MCP_DIR", tmp_path / "mcp")
    seen = []
    monkeypatch.setattr(mcp, "_checkout_ref", lambda name, cfg, dest: seen.append(name))
    monkeypatch.setattr(mcp, "_copy_bundled", lambda *a: pytest.fail("bundled path used for git server"))
    monkeypatch.setattr(mcp, "_build_venv", lambda *a: None)
    monkeypatch.setattr(mcp, "_require_probes", lambda name: None)

    mcp.install_mcp_server("marconi")
    assert seen == ["marconi"]
    [row] = [r for r in mcp.server_rows() if r["name"] == "marconi"]
    assert row["source"] == "git" and row["ref"] == CONFIG["mcp_servers"]["marconi"]["ref"]

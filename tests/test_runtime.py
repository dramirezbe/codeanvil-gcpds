"""Global methodology runtime (WU-RT1–RT7): spec, user packages, `codeanvil python`."""

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from codeanvil.config.paths import CONFIG, RUNTIME_SPEC_DIR, TEMPLATES_DIR
from codeanvil.init import runtime

REPO = Path(__file__).resolve().parents[1]


# --- shipped spec ------------------------------------------------------------


def test_shipped_pyproject_is_the_rendered_base():
    """templates/runtime/pyproject.toml is generated from config.yaml runtime.base."""
    shipped = (RUNTIME_SPEC_DIR / "pyproject.toml").read_text(encoding="utf-8")
    assert shipped == runtime.render_pyproject(runtime.base_packages(), [])


def test_shipped_lock_covers_every_base_package():
    lock = (RUNTIME_SPEC_DIR / "uv.lock").read_text(encoding="utf-8")
    for spec in runtime.base_packages():
        assert f'name = "{runtime.requirement_name(spec)}"' in lock


def test_base_includes_psutil_for_the_telemetry_collector():
    assert "psutil" in {runtime.requirement_name(spec) for spec in runtime.base_packages()}


def test_wheel_force_includes_the_runtime_spec():
    text = (REPO / "pyproject.toml").read_text(encoding="utf-8")
    assert '"templates/runtime" = "codeanvil/templates/runtime"' in text


# --- pyproject rendering and user packages -----------------------------------


def test_render_merges_base_and_user_without_duplicates():
    text = runtime.render_pyproject(["psutil", "pyyaml"], ["torch>=2", "PyYAML>=6", "numpy"])

    start = text.index("dependencies = [")
    deps = text[start : text.index("\n]\n", start)]
    assert deps.count("\n    ") == 4  # psutil, pyyaml, torch>=2, numpy
    assert '"torch>=2"' in deps and '"numpy"' in deps
    assert "PyYAML>=6" not in deps  # base pyyaml wins
    assert "package = false" in text


@pytest.mark.parametrize(
    ("spec", "name"),
    [("torch>=2", "torch"), ("PyYAML", "pyyaml"), ("my_pkg[extra]==1", "my-pkg"),
     ("numpy ; python_version>'3.12'", "numpy"), ("zope.interface", "zope-interface")],
)
def test_requirement_name(spec, name):
    assert runtime.requirement_name(spec) == name


@pytest.fixture
def fake_sync(monkeypatch):
    calls = []
    monkeypatch.setattr(runtime, "sync", lambda runtime_dir=None: calls.append(runtime_dir))
    return calls


def test_add_records_user_packages_and_syncs(tmp_path, fake_sync):
    runtime.add(["torch>=2"], tmp_path)
    runtime.add(["torch>=2.1", "numpy"], tmp_path)

    assert runtime.load_user_packages(tmp_path) == ["torch>=2.1", "numpy"]
    assert fake_sync == [tmp_path, tmp_path]


def test_add_skips_base_packages(tmp_path, fake_sync):
    runtime.add(["psutil"], tmp_path)

    assert runtime.load_user_packages(tmp_path) == []


def test_remove_refuses_base_and_unknown_packages(tmp_path, fake_sync):
    runtime.save_user_packages(["torch"], tmp_path)

    with pytest.raises(runtime.RuntimeSetupError, match="base packages"):
        runtime.remove(["psutil"], tmp_path)
    with pytest.raises(runtime.RuntimeSetupError, match="not in the runtime's user packages"):
        runtime.remove(["numpy"], tmp_path)

    runtime.remove(["torch"], tmp_path)
    assert runtime.load_user_packages(tmp_path) == []


def test_sync_keeps_user_packages_and_reports_uv_errors(tmp_path, monkeypatch):
    """A re-sync rewrites pyproject.toml but never user.yaml; a failing uv call
    raises with uv's stderr instead of being swallowed."""
    runtime.save_user_packages(["torch"], tmp_path)
    monkeypatch.setattr(runtime.shutil, "which", lambda name: "/usr/bin/uv")
    calls = []

    def fake_run(args, capture_output, text):
        calls.append(args)
        return subprocess.CompletedProcess(args, 1 if "sync" in args else 0, "", "resolution failed: no torch")

    monkeypatch.setattr(runtime.subprocess, "run", fake_run)

    with pytest.raises(runtime.RuntimeSetupError, match="resolution failed: no torch"):
        runtime.sync(tmp_path)

    assert runtime.load_user_packages(tmp_path) == ["torch"]
    assert '"torch"' in (tmp_path / "pyproject.toml").read_text(encoding="utf-8")
    assert (tmp_path / "uv.lock").is_file()  # seeded from the shipped lock
    assert calls[0][1] == "lock" and calls[1][1] == "sync"
    assert calls[1][-2:] == ["--python", str(CONFIG["runtime"]["python"])]


def test_sync_fails_clearly_without_uv(tmp_path, monkeypatch):
    monkeypatch.setattr(runtime.shutil, "which", lambda name: None)

    with pytest.raises(runtime.RuntimeSetupError, match="uv is not installed"):
        runtime.sync(tmp_path)


# --- venv layout, .pth bridge, installed packages ----------------------------


def _fake_venv(runtime_dir: Path, *dists: str) -> Path:
    """A runtime folder whose interpreter is this test's Python."""
    if sys.platform == "win32":
        bin_dir = runtime_dir / ".venv" / "Scripts"
        site = runtime_dir / ".venv" / "Lib" / "site-packages"
        interpreter = bin_dir / "python.exe"
    else:
        bin_dir = runtime_dir / ".venv" / "bin"
        site = runtime_dir / ".venv" / "lib" / "python3.12" / "site-packages"
        interpreter = bin_dir / "python"
    bin_dir.mkdir(parents=True)
    site.mkdir(parents=True)
    try:
        interpreter.symlink_to(sys.executable)
    except OSError:
        shutil.copy2(sys.executable, interpreter)
    for dist in dists:
        (site / f"{dist}.dist-info").mkdir()
    return site


def test_interpreter_path_per_os(tmp_path, monkeypatch):
    monkeypatch.setattr(runtime, "_IS_WIN", True)
    assert runtime.interpreter_path(tmp_path) == tmp_path / ".venv" / "Scripts" / "python.exe"
    monkeypatch.setattr(runtime, "_IS_WIN", False)
    assert runtime.interpreter_path(tmp_path) == tmp_path / ".venv" / "bin" / "python"


def test_installed_versions_and_missing_packages(tmp_path):
    _fake_venv(tmp_path, "psutil-7.2.2", "PyYAML-6.0.3")

    assert runtime.installed_versions(tmp_path) == {"psutil": "7.2.2", "pyyaml": "6.0.3"}
    assert runtime.missing_packages(["psutil", "torch>=2"], tmp_path) == ["torch>=2"]


def test_system_packages_are_bridged_with_a_pth_file(tmp_path, monkeypatch):
    site = _fake_venv(tmp_path)
    monkeypatch.setitem(CONFIG["runtime"], "system_packages", ["gnuradio"])
    monkeypatch.setattr(runtime, "detect_system_site_packages", lambda pkg: "/usr/lib/python3.12/site-packages")

    pth = runtime.write_system_pth(tmp_path)

    assert pth == site / runtime.PTH_NAME
    assert pth.read_text(encoding="utf-8") == "/usr/lib/python3.12/site-packages\n"


def test_missing_system_package_fails_the_sync(tmp_path, monkeypatch):
    _fake_venv(tmp_path)
    monkeypatch.setitem(CONFIG["runtime"], "system_packages", ["gnuradio"])
    monkeypatch.setattr(runtime, "detect_system_site_packages", lambda pkg: None)

    with pytest.raises(runtime.RuntimeSetupError, match="system package 'gnuradio' not found"):
        runtime.write_system_pth(tmp_path)


def test_no_system_packages_removes_a_stale_pth(tmp_path):
    site = _fake_venv(tmp_path)
    (site / runtime.PTH_NAME).write_text("/old\n", encoding="utf-8")

    assert runtime.write_system_pth(tmp_path) is None
    assert not (site / runtime.PTH_NAME).exists()


# --- codeanvil python ----------------------------------------------------------


def _cli(home: Path, cwd: Path, *args: str) -> subprocess.CompletedProcess:
    env = {key: value for key, value in os.environ.items() if key not in ("PYTHONPATH", "VIRTUAL_ENV")}
    env["HOME"] = str(home)
    env["USERPROFILE"] = str(home)
    return subprocess.run(
        [sys.executable, "-m", "codeanvil", *args],
        capture_output=True, text=True, env=env, cwd=cwd, timeout=60,
    )


@pytest.fixture
def project(tmp_path):
    root = tmp_path / "proj"
    (root / ".codeanvil").mkdir(parents=True)
    (root / ".codeanvil" / "project.yaml").write_text(
        yaml.safe_dump({"id": "x", "name": "Proj"}), encoding="utf-8"
    )
    nested = root / "src" / "deep"
    nested.mkdir(parents=True)
    return root


def _runtime_home(tmp_path: Path, *dists: str) -> Path:
    home = tmp_path / "home"
    _fake_venv(home / ".codeanvil-config" / CONFIG["runtime"]["dir"], *dists)
    return home


def _skill_script(root: Path, skill: str, needs: list[str]) -> Path:
    folder = root / ".agents" / "skills" / skill
    (folder / "scripts").mkdir(parents=True)
    (folder / "SKILL.md").write_text(
        "---\nname: x\ndescription: y\nmetadata:\n  gate: \"S9\"\n"
        f"  runtime: {needs!r}\n---\n# body\n".replace("'", '"'),
        encoding="utf-8",
    )
    script = folder / "scripts" / "probe.py"
    script.write_text(
        "import os, sys\nprint(os.getcwd())\nprint(sys.argv[1:])\nprint(sys.flags.isolated)\n"
        "sys.exit(int(os.environ.get('PROBE_EXIT', '0')))\n",
        encoding="utf-8",
    )
    return script


def test_python_without_runtime_says_how_to_install_it(tmp_path, project):
    home = tmp_path / "home"
    home.mkdir()
    script = project / "x.py"
    script.write_text("print('ran')\n", encoding="utf-8")

    result = _cli(home, project, "python", str(script))

    assert result.returncode == 1
    assert result.stdout == ""
    assert "Runtime not installed. Run codeanvil runtime sync." in result.stderr


def test_python_runs_isolated_from_the_project_root_and_passes_args(tmp_path, project):
    home = _runtime_home(tmp_path, "psutil-7.2.2")
    script = _skill_script(project, "S9_probe", ["psutil"])

    result = _cli(home, project / "src" / "deep", "python", str(script), "--pid", "42", "-h")

    assert result.returncode == 0, result.stderr
    cwd, argv, isolated = result.stdout.splitlines()
    assert Path(cwd).resolve() == project.resolve()
    assert argv == "['--pid', '42', '-h']"
    assert isolated == "1"


def test_python_stops_when_a_skill_package_is_missing(tmp_path, project):
    home = _runtime_home(tmp_path, "psutil-7.2.2")
    script = _skill_script(project, "S9_probe", ["psutil", "torch"])

    result = _cli(home, project, "python", str(script))

    assert result.returncode == 1
    assert result.stdout == ""
    assert "Skill S9_probe needs torch. Run codeanvil runtime add torch." in result.stderr


def test_python_points_to_sync_when_a_base_package_is_missing(tmp_path, project):
    home = _runtime_home(tmp_path)
    script = _skill_script(project, "S9_probe", ["psutil"])

    result = _cli(home, project, "python", str(script))

    assert result.returncode == 1
    assert "Skill S9_probe needs psutil. Run codeanvil runtime sync." in result.stderr


def test_python_forwards_the_exit_code(tmp_path, project, monkeypatch):
    home = _runtime_home(tmp_path)
    script = project / "exit.py"
    script.write_text("import sys\nsys.exit(7)\n", encoding="utf-8")

    result = _cli(home, project, "python", str(script))

    assert result.returncode == 7


def test_scaffolded_skills_declare_their_runtime_packages():
    from codeanvil.skills import parse_skill_frontmatter

    s2 = parse_skill_frontmatter(TEMPLATES_DIR / "skills" / "S2_implement_services" / "SKILL.md")
    g0 = parse_skill_frontmatter(TEMPLATES_DIR / "skills" / "G0_valid_req_and_GT" / "SKILL.md")
    assert s2["runtime"] == ["psutil"]
    assert g0["runtime"] == []
    base = {runtime.requirement_name(spec) for spec in runtime.base_packages()}
    assert set(s2["runtime"]) <= base  # S2 must work right after `runtime sync`


# --- integration: a real uv sync ----------------------------------------------


@pytest.mark.skipif(shutil.which("uv") is None, reason="uv is not installed")
def test_real_sync_builds_a_runtime_that_imports_the_base(tmp_path):
    interpreter = runtime.sync(tmp_path / "runtime")

    result = subprocess.run(
        [str(interpreter), "-I", "-c", "import psutil, yaml; print(psutil.cpu_count() > 0)"],
        capture_output=True, text=True, timeout=60,
    )
    assert result.stdout.strip() == "True", result.stderr

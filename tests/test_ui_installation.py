"""The ordinary global installation includes a Node-free, offline-capable UI."""

import importlib
from pathlib import Path

import pytest
import yaml

from codeanvil.UI.assets import UIAssetsError, validate_frontend
from codeanvil.init import ui as setup

REPO = Path(__file__).resolve().parents[1]


def bundle(root):
    root.mkdir()
    (root / "assets").mkdir()
    (root / "index.html").write_text('<script src="./assets/app.js"></script><link href="./assets/app.css">')
    (root / "assets/app.js").write_text("export {}")
    (root / "assets/app.css").write_text('@font-face {src:url("./font.woff2")}')
    (root / "assets/font.woff2").write_bytes(b"local-font")
    return root


def test_frontend_assets_include_local_fonts_and_need_no_node(tmp_path):
    dist = bundle(tmp_path / "dist")
    assert validate_frontend(dist) == dist
    (dist / "assets/font.woff2").unlink()
    with pytest.raises(UIAssetsError, match="font.woff2"):
        validate_frontend(dist)


@pytest.mark.parametrize("css", [
    '@import url("https://fonts.googleapis.com/css2?family=DM+Sans");',
    '@import "https://fonts.example/font.css";',
    '@font-face {src:url(//fonts.example/font.woff2)}',
    '@font-face {src:url(../../outside.woff2)}',
])
def test_frontend_rejects_external_or_escaping_assets(tmp_path, css):
    dist = bundle(tmp_path / "dist")
    (dist / "assets/app.css").write_text(css)
    with pytest.raises(UIAssetsError):
        validate_frontend(dist)


def test_frontend_reports_missing_entry_point(tmp_path):
    with pytest.raises(UIAssetsError, match="built UI is missing"):
        validate_frontend(tmp_path)


def test_default_package_requires_ui_dependencies():
    try:
        import tomllib
    except ImportError:
        import tomli as tomllib
    project = tomllib.loads((REPO / "pyproject.toml").read_text())["project"]
    required = {item.split(">=")[0] for item in project["dependencies"]}
    assert {"fastapi", "httpx", "uvicorn[standard]", "watchdog"} <= required
    assert "ui" not in project["optional-dependencies"]


def test_prepare_ui_preserves_editable_launcher_settings(tmp_path):
    dist = setup.prepare_ui(tmp_path)
    registry = tmp_path / "launchers.yaml"
    assert dist.is_dir()
    assert "codex" in yaml.safe_load(registry.read_text())["launchers"]
    custom = 'launchers:\n  custom:\n    kind: terminal\n    label: My agent\n'
    registry.write_text(custom)
    assert setup.prepare_ui(tmp_path) == dist
    assert registry.read_text() == custom


def test_prepare_ui_reports_missing_dependency(tmp_path, monkeypatch):
    def missing(_):
        raise ModuleNotFoundError("fastapi")
    monkeypatch.setattr(setup.importlib, "import_module", missing)
    with pytest.raises(setup.UISetupError, match="Reinstall CodeAnvil"):
        setup.prepare_ui(tmp_path)
    assert not (tmp_path / "launchers.yaml").exists()


def test_init_prepares_ui_and_preserves_registered_projects(tmp_path, monkeypatch):
    from codeanvil.config import paths
    from codeanvil.db.utils import connect_db
    from codeanvil.init import runtime

    command = importlib.import_module("codeanvil.CLI.commands.init")
    state = tmp_path / "global"
    database = state / "db/codeanvil.db"
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr(paths, "WORKDIR", state)
    monkeypatch.setattr(paths, "DB_DIR", database.parent)
    monkeypatch.setattr(paths, "MCP_DIR", state / "mcp")
    monkeypatch.setattr(command, "DB_PATH", database)
    syncs = []
    monkeypatch.setattr(runtime, "sync", lambda: syncs.append(True))
    command.cmd_init()
    assert (state / "launchers.yaml").is_file()
    conn = connect_db(database)
    conn.execute("INSERT INTO projects (id,name,path) VALUES (?,?,?)", ("fixture", "Keep", str(tmp_path / "project")))
    conn.commit()
    conn.close()
    command.cmd_init()
    conn = connect_db(database)
    assert conn.execute("SELECT name FROM projects").fetchone()[0] == "Keep"
    conn.close()
    assert syncs == [True, True]


def test_init_cannot_report_success_with_missing_ui(tmp_path, monkeypatch):
    command = importlib.import_module("codeanvil.CLI.commands.init")
    monkeypatch.setattr(command, "DB_PATH", tmp_path / "not-created.db")
    def missing():
        raise setup.UISetupError("Missing UI assets")
    monkeypatch.setattr(command, "prepare_ui", missing)
    with pytest.raises(SystemExit) as error:
        command.cmd_init()
    assert error.value.code == 1
    assert not (tmp_path / "not-created.db").exists()

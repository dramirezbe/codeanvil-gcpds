"""Folder-dialog defaults follow the local user's home, not CodeAnvil's cwd."""

import json
import subprocess

import pytest

from codeanvil.CLI.commands.create import CreateInputError, resolve_create_inputs
from codeanvil.UI import user_context, workflows
from codeanvil.UI.workflows import FolderRequest, create_workflows_router


@pytest.fixture
def home(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    return home


@pytest.mark.parametrize("folders,expected", [([], ""), (["Documentos"], "Documentos"),
                                             (["Documents"], "Documents"),
                                             (["Documents", "Documentos"], "Documents")])
def test_default_folder_is_existing_documents_or_home(home, tmp_path, monkeypatch, folders, expected):
    for name in folders:
        (home / name).mkdir()
    # A file called Documents must not be treated as a usable folder.
    if "Documents" not in folders:
        (home / "Documents").write_text("Not a folder")
    launch = tmp_path / "codeanvil-gcpds"
    launch.mkdir()
    monkeypatch.chdir(launch)
    before = list(home.iterdir())
    endpoints = {route.path.rsplit("/", 1)[-1]: route.endpoint for route in create_workflows_router(launch).routes}
    selected = home / expected
    assert user_context.default_folder() == selected
    assert endpoints["defaults"]() == {"path": str(selected)}
    assert list(home.iterdir()) == before


def test_local_user_uses_username_and_home_with_fallback(home, monkeypatch):
    monkeypatch.setattr(user_context.getpass, "getuser", lambda: "DOMAIN\\localuser")
    assert user_context.local_user() == {"name": "DOMAIN\\localuser", "home": str(home)}

    def unavailable():
        raise OSError("No username database")
    monkeypatch.setattr(user_context.getpass, "getuser", unavailable)
    assert user_context.local_user() == {"name": home.name, "home": str(home)}


def test_picker_starts_at_documents_then_honors_explicit_folder(home, tmp_path, monkeypatch):
    documents = home / "Documentos"
    documents.mkdir()
    commands = []

    def picker(argv, **kwargs):
        commands.append(argv)
        return subprocess.CompletedProcess(argv, 0, json.dumps({"path": None}), "")
    monkeypatch.setattr(workflows.subprocess, "run", picker)
    endpoint = next(route.endpoint for route in create_workflows_router(tmp_path).routes if route.path.endswith("/pick-folder"))
    endpoint(FolderRequest())
    assert commands[-1][-1] == str(documents)
    endpoint(FolderRequest(initial_path=str(tmp_path)))
    assert commands[-1][-1] == str(tmp_path)


@pytest.mark.parametrize("name", ["My SDR Lab", "Señal Ágil 01", "  New--Lab  ", "", "   ", "!!!"])
def test_folder_suggestion_matches_the_cli_contract(tmp_path, name):
    endpoint = next(route.endpoint for route in create_workflows_router(tmp_path).routes if route.path.endswith("/folder-name"))
    try:
        _, folder = resolve_create_inputs(None, name, None)
    except CreateInputError as exc:
        assert endpoint(name) == {"folder": "", "error": str(exc)}
    else:
        assert endpoint(name) == {"folder": folder, "error": None}

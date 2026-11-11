"""Delete CLI confirmation and dispatch use isolated project registrations."""

import importlib
import json
import sqlite3
import subprocess
import sys
from types import SimpleNamespace

import pytest

from codeanvil.CLI.parser import argparser
from codeanvil.db.schema import create_schema
from codeanvil.project_delete import ProjectDeleteError

command = importlib.import_module("codeanvil.CLI.commands.delete")
main = importlib.import_module("codeanvil.CLI.main")


@pytest.fixture
def project(tmp_path, monkeypatch):
    database = tmp_path / "registry.db"
    folder = tmp_path / "project"
    manifest = folder / ".codeanvil/project.yaml"
    manifest.parent.mkdir(parents=True)
    identity = {"id": "019a0000-0000-7000-8000-000000000001", "name": "CLI Lab"}
    manifest.write_text(json.dumps(identity))
    (folder / "notes.txt").write_text("Keep this project content")
    with sqlite3.connect(database) as conn:
        create_schema(conn)
        conn.execute("INSERT INTO projects (id,name,path) VALUES (?,?,?)", (*identity.values(), str(folder)))
    monkeypatch.setattr(command, "DB_PATH", database)
    return database, folder, identity


def registered(database):
    with sqlite3.connect(database) as conn:
        return conn.execute("SELECT id FROM projects").fetchall()


def terminal(monkeypatch, value):
    monkeypatch.setattr(command.sys, "stdin", SimpleNamespace(isatty=lambda: value))


def test_yes_removes_only_registration_by_default(project, capsys):
    database, folder, identity = project
    command.cmd_delete(identity["name"], yes=True)
    assert registered(database) == []
    assert (folder / "notes.txt").read_text() == "Keep this project content"
    output = capsys.readouterr().out
    assert identity["name"] in output and identity["id"] in output and str(folder) in output
    assert "project files kept" in output


def test_yes_remove_files_deletes_explicitly_selected_folder(project, capsys):
    database, folder, identity = project
    command.cmd_delete(identity["id"], remove_files=True, yes=True)
    assert registered(database) == []
    assert not folder.exists()
    assert "Permanently delete" in capsys.readouterr().out


def test_noninteractive_requires_yes_even_with_remove_files(project, monkeypatch, capsys):
    database, folder, identity = project
    terminal(monkeypatch, False)
    with pytest.raises(SystemExit) as error:
        command.cmd_delete(identity["id"], remove_files=True)
    assert error.value.code == 1
    assert "--yes" in capsys.readouterr().err
    assert registered(database) == [(identity["id"],)]
    assert (folder / "notes.txt").is_file()


@pytest.mark.parametrize("answer", ["", "n"])
def test_interactive_confirmation_defaults_to_no(project, monkeypatch, capsys, answer):
    database, folder, identity = project
    terminal(monkeypatch, True)
    monkeypatch.setattr("builtins.input", lambda _: answer)
    command.cmd_delete(identity["id"], remove_files=True)
    assert "Cancelled" in capsys.readouterr().out
    assert registered(database) == [(identity["id"],)]
    assert folder.exists()


def test_interactive_yes_uses_current_project_without_registering_it(project, monkeypatch):
    database, folder, _ = project
    terminal(monkeypatch, True)
    monkeypatch.chdir(folder)
    prompts = []

    def confirm(prompt):
        prompts.append(prompt)
        return "YES"

    monkeypatch.setattr("builtins.input", confirm)
    command.cmd_delete()
    assert prompts == ["Remove project registration? [y/N]: "]
    assert registered(database) == []
    assert folder.exists()


@pytest.mark.parametrize("interruption", [EOFError, KeyboardInterrupt])
def test_interrupted_confirmation_does_not_mutate(project, monkeypatch, interruption):
    database, folder, identity = project
    terminal(monkeypatch, True)

    def cancel(_):
        raise interruption

    monkeypatch.setattr("builtins.input", cancel)
    command.cmd_delete(identity["id"])
    assert registered(database) == [(identity["id"],)]
    assert folder.exists()


def test_domain_failure_is_a_cli_error_and_keeps_registration(project, monkeypatch, capsys):
    database, folder, identity = project

    def fail(*args, **kwargs):
        assert args == (identity["id"],)
        assert kwargs["expected_path"] == str(folder)
        raise ProjectDeleteError("Project changed since confirmation")

    monkeypatch.setattr(command, "delete_project", fail)
    with pytest.raises(SystemExit) as error:
        command.cmd_delete(identity["id"], yes=True)
    assert error.value.code == 1
    assert "Project changed since confirmation" in capsys.readouterr().err
    assert registered(database) == [(identity["id"],)]


def test_unknown_project_has_no_mutation(project, capsys):
    database, folder, identity = project
    with pytest.raises(SystemExit) as error:
        command.cmd_delete("missing", yes=True)
    assert error.value.code == 1
    assert capsys.readouterr().err.startswith("Error:")
    assert registered(database) == [(identity["id"],)]
    assert folder.exists()


@pytest.mark.parametrize("argv,expected", [
    (["delete"], (None, False, False)),
    (["delete", "CLI Lab", "--remove-files", "-y"], ("CLI Lab", True, True)),
])
def test_parser_and_dispatch_pass_delete_options(monkeypatch, argv, expected):
    calls = []
    monkeypatch.setattr(main, "cmd_delete", lambda project, *, remove_files, yes: calls.append((project, remove_files, yes)))
    main.choose_option(argparser(argv))
    assert calls == [expected]


def test_delete_help_exposes_modes_on_the_module_entrypoint():
    result = subprocess.run([sys.executable, "-I", "-m", "codeanvil", "delete", "--help"], capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stderr
    assert "--remove-files" in result.stdout and "--yes" in result.stdout
    assert "kept unless" in " ".join(result.stdout.split())

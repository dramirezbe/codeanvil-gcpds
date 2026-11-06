"""Guard test: installed CLI must expose all expected subcommands and flags.

Catches stale installs — if you change the argparser in source but forget
to reinstall, these tests fail when run against the installed binary."""

import subprocess
import sys

import pytest

EXPECTED_SUBCOMMANDS = {"init", "create", "list", "sync", "status", "now", "backup", "runtime", "python", "sandbox", "upgrade"}


def _run_cli(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-I", "-m", "codeanvil", *args],
        capture_output=True, text=True, timeout=10,
    )


def test_all_subcommands_present():
    result = _run_cli("--help")
    assert result.returncode == 0, result.stderr
    for cmd in EXPECTED_SUBCOMMANDS:
        assert cmd in result.stdout, f"subcommand '{cmd}' missing from --help"


def test_sync_subcommand_exists():
    result = _run_cli("sync", "--help")
    assert result.returncode == 0, f"sync not recognized: {result.stderr}"


def test_now_machine_flag_exists():
    result = _run_cli("now", "--help")
    assert result.returncode == 0, result.stderr
    assert "--machine" in result.stdout, "--machine flag missing from 'now --help'"


def test_now_tz_flag_exists():
    result = _run_cli("now", "--help")
    assert "--tz" in result.stdout, "--tz flag missing from 'now --help'"


def test_status_name_is_optional():
    result = _run_cli("status", "--help")
    assert result.returncode == 0, result.stderr
    help_text = result.stdout.lower()
    assert "name" in help_text, "status should accept optional name argument"


def test_create_has_mcp_flag():
    result = _run_cli("create", "--help")
    assert result.returncode == 0, result.stderr
    assert "--mcp" in result.stdout, "--mcp flag missing from 'create --help'"


def test_init_has_mcp_flag():
    result = _run_cli("init", "--help")
    assert result.returncode == 0, result.stderr
    assert "--mcp" in result.stdout, "--mcp flag missing from 'init --help'"


def test_backup_subcommand_exists():
    result = _run_cli("backup", "--help")
    assert result.returncode == 0, f"backup not recognized: {result.stderr}"
    for stage in ("S0", "S1", "S2", "G2"):
        assert stage in result.stdout, f"stage '{stage}' missing from 'backup --help'"


def test_upgrade_subcommand_exists():
    result = _run_cli("upgrade", "--help")
    assert result.returncode == 0, f"upgrade not recognized: {result.stderr}"
    assert "uv" in result.stdout.lower() or "reinstall" in result.stdout.lower(), (
        "upgrade help should mention reinstalling via uv"
    )


def test_version_flag():
    result = _run_cli("--version")
    assert result.returncode == 0, result.stderr
    assert "codeanvil" in result.stdout


def test_version_short_flag():
    result = _run_cli("-v")
    assert result.returncode == 0, result.stderr
    assert "codeanvil" in result.stdout


def test_runtime_subcommand_exposes_its_actions():
    result = _run_cli("runtime", "--help")
    assert result.returncode == 0, f"runtime not recognized: {result.stderr}"
    for action in ("sync", "add", "remove", "list", "path"):
        assert action in result.stdout, f"action '{action}' missing from 'runtime --help'"


def test_python_subcommand_exists():
    result = _run_cli("python", "--help")
    assert result.returncode == 0, f"python not recognized: {result.stderr}"
    assert "script" in result.stdout

"""Guard test: installed CLI must expose all expected subcommands and flags.

Catches stale installs — if you change the argparser in source but forget
to reinstall, these tests fail when run against the installed binary."""

import subprocess
import sys

import pytest

EXPECTED_SUBCOMMANDS = {"init", "create", "list", "sync", "status", "now"}


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


def test_version_flag():
    result = _run_cli("--version")
    assert result.returncode == 0, result.stderr
    assert "codeanvil" in result.stdout


def test_version_short_flag():
    result = _run_cli("-v")
    assert result.returncode == 0, result.stderr
    assert "codeanvil" in result.stdout

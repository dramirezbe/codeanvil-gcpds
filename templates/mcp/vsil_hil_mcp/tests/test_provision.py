"""Run the actual update command with fake user tools, without installing anything."""

from pathlib import Path
import subprocess

import pytest

from vsil_hil_mcp.provision import render_update_command


@pytest.mark.parametrize("failed_capability", [False, True])
def test_user_update_uses_published_tool_source_and_checks_capabilities(tmp_path, failed_capability):
    binaries = tmp_path / ".local/bin"
    binaries.mkdir(parents=True)
    log = tmp_path / "calls"
    for name in ("uv", "codeanvil"):
        script = binaries / name
        script.write_text("#!/bin/sh\nprintf '%s %s\\n' " + name + ' "$*" >> "$CALL_LOG"\n' +
                          ('[ "$1 $2" != "telemetry --help" ] || exit 17\n' if failed_capability and name == "codeanvil" else 'exit 0\n'))
        script.chmod(0o755)
    command = render_update_command("published-tool-ref")
    result = subprocess.run(["/bin/bash", "-c", command], env={"HOME": str(tmp_path), "PATH": "/usr/bin:/bin",
                                                            "CALL_LOG": str(log)}, capture_output=True, text=True)
    assert result.returncode == (17 if failed_capability else 0), result.stderr
    lines = log.read_text().splitlines()
    assert lines[:4] == ["uv tool install --force git+https://github.com/dramirezbe/codeanvil-gcpds.git@published-tool-ref",
                         "codeanvil init", "codeanvil runtime sync", "codeanvil telemetry --help"]
    assert ("codeanvil now --machine" in lines) is not failed_capability
    assert not any("ssh-keygen" in line for line in lines)


def test_source_reference_is_quoted_as_one_install_argument(tmp_path):
    command = render_update_command("branch;touch-marker")
    syntax = subprocess.run(["/bin/bash", "-n"], input=command, capture_output=True, text=True)
    assert syntax.returncode == 0
    assert "'git+https://github.com/dramirezbe/codeanvil-gcpds.git@branch;touch-marker'" in command


@pytest.mark.parametrize("ref", ["", " branch", "branch name"])
def test_missing_or_ambiguous_source_is_not_guessed(ref):
    with pytest.raises(ValueError, match="published"):
        render_update_command(ref)

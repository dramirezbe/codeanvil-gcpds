"""Execute only the generated prerequisite block against temporary executables."""

import os
from pathlib import Path
import shutil
import subprocess

import pytest

from vsil_hil_mcp.config import Target
from vsil_hil_mcp.provision import render_script

PUBLIC_KEY = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAItest vsil-test"


def _prerequisites():
    script = render_script(Target("pi", "host", "codeanvil-agent", "/home/codeanvil-agent/ws"),
                           PUBLIC_KEY, PUBLIC_KEY, "0.7.5")
    # Run the actual generated helper/checks; never execute user/key/install stages.
    start = script.index("install_pkg() {")
    end = script.index("# 1. unprivileged user")
    return "set -euo pipefail\n" + script[start:end]


def _executable(path: Path, body: str):
    path.write_text("#!/bin/bash\n" + body)
    path.chmod(0o755)


def _run(tmp_path, manager=None, mode="install"):
    binaries = tmp_path / "bin"
    binaries.mkdir(exist_ok=True)
    log = tmp_path / "packages.log"
    if manager:
        body = '''printf '%s\\n' "$*" >> "$PACKAGE_LOG"
'''
        if mode == "fail":
            body += "exit 17\n"
        elif mode == "install":
            body += '''package="${@: -1}"
printf '#!/bin/sh\\nexit 0\\n' > "$FAKE_BIN/$package"
/bin/chmod 755 "$FAKE_BIN/$package"
'''
        _executable(binaries / manager, body)
    env = {"PATH": str(binaries), "PACKAGE_LOG": str(log), "FAKE_BIN": str(binaries)}
    result = subprocess.run([shutil.which("bash"), "-c", _prerequisites()],
                            env=env, capture_output=True, text=True, timeout=5)
    return result, log, binaries


@pytest.mark.parametrize("manager,prefix", [
    ("apt-get", "install -y"), ("dnf", "install -y"), ("pacman", "-S --noconfirm"),
])
def test_missing_git_and_curl_installed_in_order_before_bootstrap(tmp_path, manager, prefix):
    result, log, binaries = _run(tmp_path, manager)
    assert result.returncode == 0, result.stderr
    assert log.read_text().splitlines() == [f"{prefix} git", f"{prefix} curl"]
    assert os.access(binaries / "git", os.X_OK) and os.access(binaries / "curl", os.X_OK)


def test_available_tools_do_not_call_package_manager(tmp_path):
    binaries = tmp_path / "bin"
    binaries.mkdir()
    for tool in ("git", "curl"):
        _executable(binaries / tool, "exit 0\n")
    result, log, _ = _run(tmp_path, "apt-get", mode="fail")
    assert result.returncode == 0, result.stderr
    assert not log.exists()


@pytest.mark.parametrize("mode,expected", [("fail", 17), ("noop", 1)])
def test_failed_or_ineffective_install_stops_before_next_tool(tmp_path, mode, expected):
    result, log, _ = _run(tmp_path, "apt-get", mode=mode)
    assert result.returncode == expected
    assert log.read_text().splitlines() == ["install -y git"]
    if mode == "noop":
        assert "git is still unavailable" in result.stderr


def test_unknown_package_manager_reports_manual_prerequisite(tmp_path):
    result, log, _ = _run(tmp_path)
    assert result.returncode == 1
    assert "install git manually" in result.stderr
    assert not log.exists()

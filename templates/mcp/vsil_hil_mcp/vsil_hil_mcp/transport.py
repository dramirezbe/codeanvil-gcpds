"""ssh / rsync / ssh-keygen through subprocess, argv lists only (never a shell)."""

from __future__ import annotations

import os
import shlex
import subprocess
from pathlib import Path

from .config import Target, key_paths

EXCLUDES = (
    ".git", "__pycache__", "*.pyc", "verification/telemetry/",
    ".env", "*.key", "*.pem", ".venv", ".codeanvil/hil/",
)
TELEMETRY_REL = "verification/telemetry/"
TIMEOUT_S = 600

# Fixed read-only diagnostic; the target receives no agent-authored shell here.
PROBE_CMD = r'''vsil_probe_status=0
printf 'VSIL_OS='; uname -s || vsil_probe_status=1
printf 'VSIL_ARCH='; uname -m || vsil_probe_status=1
printf 'VSIL_CODEANVIL='
if command -v codeanvil >/dev/null 2>&1; then codeanvil --version || vsil_probe_status=1
else "$HOME/.local/bin/codeanvil" --version || vsil_probe_status=1; fi
if command -v lsusb >/dev/null 2>&1; then
  printf 'VSIL_USB_AVAILABLE=yes\nVSIL_USB_BEGIN\n'
  lsusb || vsil_probe_status=1
else printf 'VSIL_USB_AVAILABLE=no\nVSIL_USB_BEGIN\n'; fi
exit "$vsil_probe_status"'''


def _ssh_opts(target: Target, key: Path) -> list[str]:
    return [
        "-F", os.devnull,
        "-i", str(key),
        "-p", str(target.port),
        "-o", "IdentitiesOnly=yes",
        "-o", "IdentityAgent=none",
        "-o", "StrictHostKeyChecking=accept-new",
        "-o", f"UserKnownHostsFile={key_paths(target.name)['known_hosts']}",
        "-o", "BatchMode=yes",
        "-o", "ConnectTimeout=15",
    ]


def _run(argv: list[str]) -> dict:
    try:
        p = subprocess.run(argv, capture_output=True, text=True, timeout=TIMEOUT_S)
        return {"stdout": p.stdout, "stderr": p.stderr, "exit_code": p.returncode}
    except subprocess.TimeoutExpired:
        return {"stdout": "", "stderr": f"timeout after {TIMEOUT_S}s", "exit_code": 124}
    except FileNotFoundError as exc:
        return {"stdout": "", "stderr": f"binary not found: {exc.filename}", "exit_code": 127}


def ssh_argv(target: Target, key: Path, remote_cmd: str) -> list[str]:
    # The remote command is ONE argv element; ssh hands it to the remote login shell.
    return ["ssh", *_ssh_opts(target, key), f"{target.user}@{target.host}", remote_cmd]


def ssh_run(target: Target, key_path: Path, remote_cmd: str) -> dict:
    return _run(ssh_argv(target, key_path, remote_cmd))


def _rsync_e(target: Target, key: Path) -> str:
    return shlex.join(["ssh", *_ssh_opts(target, key)])


def _rsync_host(target: Target) -> str:
    # rsync uses ':' to separate host and path; literal IPv6 needs brackets.
    host = f"[{target.host}]" if ":" in target.host else target.host
    return f"{target.user}@{host}"


def rsync_push_argv(target: Target, deploy_key: Path, local_workspace: Path) -> list[str]:
    return [
        "rsync", "-az", "--delete",
        "-e", _rsync_e(target, deploy_key),
        *[f"--exclude={e}" for e in EXCLUDES],
        f"{local_workspace}/",
        # The deploy key is forced to `rrsync -wo <workspace>`, which roots every
        # client path at the workspace. So the destination is that root (empty
        # path), NOT the absolute workspace path — otherwise rrsync nests it as
        # <workspace>/<workspace>/ and fails (verified against a real target).
        f"{_rsync_host(target)}:",
    ]


def rsync_push(target: Target, deploy_key: Path, local_workspace: Path) -> dict:
    return _run(rsync_push_argv(target, deploy_key, local_workspace))


def rsync_pull_argv(target: Target, key: Path, local_workspace: Path) -> list[str]:
    return [
        "rsync", "-az",
        "-e", _rsync_e(target, key),
        f"{_rsync_host(target)}:{target.workspace}/{TELEMETRY_REL}",
        f"{local_workspace}/{TELEMETRY_REL}",
    ]


def rsync_pull(target: Target, key: Path, local_workspace: Path) -> dict:
    (local_workspace / TELEMETRY_REL).mkdir(parents=True, exist_ok=True)
    return _run(rsync_pull_argv(target, key, local_workspace))


def keygen(path: Path, comment: str) -> dict:
    return _run(["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-C", comment, "-f", str(path)])

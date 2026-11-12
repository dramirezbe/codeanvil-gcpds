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
        f"{target.user}@{target.host}:",
    ]


def rsync_push(target: Target, deploy_key: Path, local_workspace: Path) -> dict:
    return _run(rsync_push_argv(target, deploy_key, local_workspace))


def rsync_pull_argv(target: Target, key: Path, local_workspace: Path) -> list[str]:
    return [
        "rsync", "-az",
        "-e", _rsync_e(target, key),
        f"{target.user}@{target.host}:{target.workspace}/{TELEMETRY_REL}",
        f"{local_workspace}/{TELEMETRY_REL}",
    ]


def rsync_pull(target: Target, key: Path, local_workspace: Path) -> dict:
    (local_workspace / TELEMETRY_REL).mkdir(parents=True, exist_ok=True)
    return _run(rsync_pull_argv(target, key, local_workspace))


def keygen(path: Path, comment: str) -> dict:
    return _run(["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-C", comment, "-f", str(path)])

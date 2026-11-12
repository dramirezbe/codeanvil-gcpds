"""ssh / rsync / ssh-keygen through subprocess, argv lists only (never a shell)."""

from __future__ import annotations

import os
import shlex
import subprocess
import tarfile
import tempfile
from pathlib import Path

from .config import ConfigError, Target, key_paths

EXCLUDES = (
    ".git", "__pycache__", "*.pyc", "verification/telemetry/",
    ".env", "*.key", "*.pem", ".venv", ".codeanvil/hil/",
    "*.db", "*.db-*", "*.db3", "*.db3-*", "*.sqlite", "*.sqlite-*",
    "*.sqlite3", "*.sqlite3-*", "*.duckdb", "*.mdb", "*.rdb",
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
        "-o", f"UserKnownHostsFile={key_paths(target.key_identity)['known_hosts']}",
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
    # Default rsync exclusions are symmetric: hide sender files AND protect
    # existing receiver files from --delete. Never add --delete-excluded here.
    excludes = (*EXCLUDES, *(f"/{path}" for path in getattr(target, "persistent_paths", ())))
    if target.sync_via_exec:
        # An adopted legacy client keeps its old restricted deploy key intact.
        # Its existing exec identity can reach the new project workspace directly.
        remote_path = target.workspace
    elif target.deploy_root:
        remote_path = str(Path(target.workspace).relative_to(target.deploy_root))
    else:
        remote_path = ""  # legacy forced command already roots at the workspace
    return [
        "rsync", "-az", "--delete",
        "-e", _rsync_e(target, deploy_key),
        *[f"--exclude={e}" for e in excludes],
        f"{local_workspace}/",
        f"{_rsync_host(target)}:{remote_path}",
    ]


def _git(root: Path, *args: str) -> str:
    try:
        result = subprocess.run(["git", "-C", str(root), *args], capture_output=True,
                                text=True, timeout=TIMEOUT_S)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ConfigError(f"cannot prepare published candidate: {exc}") from exc
    if result.returncode:
        raise ConfigError(f"cannot prepare published candidate: git {args[0]} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def _git_config(root: Path, key: str) -> str:
    """`git config --get`, returning '' when the key is unset instead of raising
    (unlike `_git`, which treats git's exit 1 for a missing key as a failure)."""
    try:
        result = subprocess.run(["git", "-C", str(root), "config", "--get", key],
                                capture_output=True, text=True, timeout=TIMEOUT_S)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ConfigError(f"cannot prepare published candidate: {exc}") from exc
    return result.stdout.strip() if result.returncode == 0 else ""


def _has_commit(root: Path) -> bool:
    """True when HEAD resolves to a real commit (a fresh repo has none)."""
    try:
        result = subprocess.run(["git", "-C", str(root), "rev-parse", "--verify", "--quiet", "HEAD"],
                                capture_output=True, text=True, timeout=TIMEOUT_S)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ConfigError(f"cannot prepare published candidate: {exc}") from exc
    return result.returncode == 0 and bool(result.stdout.strip())


def _deploy_revision(root: Path) -> tuple[str, bool]:
    """Resolve the committed revision to deploy and whether it is published.

    The floor is always a clean tree and a real commit: the deploy is
    `git archive <revision>`, so the deployed bytes equal a named commit and the
    HIL evidence pins to it. When the branch tracks a remote upstream the commit
    must be pushed there (returns published=True), so third parties can reproduce
    it. A branch with no upstream deploys its local commit and is flagged
    unpublished (published=False) — reproducible from this machine's repository
    only. The local path needs only a `git commit`: no remote, no push, no GitHub.
    """
    if Path(_git(root, "rev-parse", "--show-toplevel")).resolve() != root.resolve():
        raise ConfigError("deployment requires the project root to be the Git repository root")
    branch = _git(root, "symbolic-ref", "--quiet", "--short", "HEAD")
    if not _has_commit(root):
        raise ConfigError("deployment requires at least one commit; commit the source and kit changes")
    if _git(root, "status", "--porcelain", "--untracked-files=all"):
        raise ConfigError("deployment requires a clean Git tree; commit all source and kit changes")
    revision = _git(root, "rev-parse", "HEAD")
    remote = _git_config(root, f"branch.{branch}.remote")
    if not remote or remote == ".":
        return revision, False  # local-only candidate: no remote upstream, no push required
    upstream_ref = _git_config(root, f"branch.{branch}.merge")
    # Fetch the actual upstream branch, rather than relying on a possibly stale
    # tracking ref or a remote fetch refspec that excludes this branch.
    _git(root, "fetch", "--quiet", "--no-tags", "--", remote, upstream_ref)
    if revision != _git(root, "rev-parse", "FETCH_HEAD") or revision != _git(root, "rev-parse", "@{upstream}"):
        raise ConfigError("deployment requires HEAD to match the fetched upstream; push or update the candidate")
    return revision, True


def rsync_push(target: Target, deploy_key: Path, local_workspace: Path) -> dict:
    """Deploy only a clean, committed Git export; ignored host files never enter it.

    The result carries `published`: True when the deployed commit is pushed to the
    branch's remote upstream, False for a local-only commit (no remote required)."""
    root = local_workspace.resolve()
    revision, published = _deploy_revision(root)
    with tempfile.TemporaryDirectory(prefix="codeanvil-deploy-") as directory:
        temporary = Path(directory)
        archive_path = temporary / "candidate.tar"
        with archive_path.open("wb") as archive_output:
            try:
                archived = subprocess.run(["git", "-C", str(root), "archive", revision],
                                          stdout=archive_output, stderr=subprocess.PIPE,
                                          timeout=TIMEOUT_S)
            except (OSError, subprocess.TimeoutExpired) as exc:
                raise ConfigError(f"cannot export published candidate: {exc}") from exc
        if archived.returncode:
            raise ConfigError(f"cannot export published candidate: {archived.stderr.decode(errors='replace').strip()}")
        source = temporary / "source"
        source.mkdir()
        try:
            with tarfile.open(archive_path) as archive:
                # The server requires Python 3.12+: the stdlib data filter refuses
                # escaping paths/links and special-device members during extraction.
                archive.extractall(source, filter="data")
        except (OSError, tarfile.TarError) as exc:
            raise ConfigError(f"unsafe or unreadable Git archive: {exc}") from exc
        if _git(root, "rev-parse", "HEAD") != revision or _git(root, "status", "--porcelain", "--untracked-files=all"):
            raise ConfigError("candidate changed during export; review and publish it before deployment")
        return {"revision": revision, "published": published,
                **_run(rsync_push_argv(target, deploy_key, source))}


def rsync_pull_argv(
    target: Target, key: Path, local_workspace: Path, destination: Path | None = None,
) -> list[str]:
    destination = destination or local_workspace / TELEMETRY_REL / target.name
    return [
        "rsync", "-az",
        "-e", _rsync_e(target, key),
        f"{_rsync_host(target)}:{target.workspace}/{TELEMETRY_REL}",
        f"{destination}/",
    ]


def rsync_pull(target: Target, key: Path, local_workspace: Path) -> dict:
    target_dir = local_workspace / TELEMETRY_REL / target.name
    target_dir.mkdir(parents=True, exist_ok=True)
    # Each transfer owns a new directory. Another target or a later fetch can
    # never replace evidence whose path and digest were already recorded by G2.
    destination = Path(tempfile.mkdtemp(prefix="fetch-", dir=target_dir))
    result = _run(rsync_pull_argv(target, key, local_workspace, destination))
    return {"local_path": str(destination), **result}


def keygen(path: Path, comment: str) -> dict:
    return _run(["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-C", comment, "-f", str(path)])

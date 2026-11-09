"""Upgrade codeanvil to the latest version from GitHub."""

import platform
import shutil
import subprocess
import sys

from codeanvil.config.logger import get_logger

log = get_logger(__name__)

REPO = "git+https://github.com/dramirezbe/codeanvil-gcpds.git"
PYTHON_VERSION = "3.12"


def cmd_upgrade() -> None:
    uv = shutil.which("uv")
    if uv is None:
        log.error("uv is not installed — install it first (https://docs.astral.sh/uv/)")
        raise SystemExit(1)

    cmd = [uv, "tool", "install", "--force-reinstall", "--python", PYTHON_VERSION, REPO]

    os_name = platform.system()
    if os_name == "Windows":
        log.info("Windows detected — upgrading via uv")
    elif os_name in ("Linux", "Darwin"):
        log.info("%s detected — upgrading via uv", os_name)
    else:
        log.warning("Unknown OS %r — attempting upgrade anyway", os_name)

    log.info("Running: %s", " ".join(cmd))
    result = subprocess.run(cmd)
    if result.returncode != 0:
        log.error("Upgrade failed (exit %d)", result.returncode)
        raise SystemExit(result.returncode)
    log.info("codeanvil upgraded successfully")

    # The new binary owns the new shipped runtime spec: run *its* sync, not
    # this process's, so a changed lock takes effect at once.
    new_binary = shutil.which("codeanvil")
    if new_binary is None:
        log.warning("codeanvil is not on PATH — run 'codeanvil runtime sync' once it is")
        return
    sync = subprocess.run([new_binary, "runtime", "sync"])
    if sync.returncode != 0:
        log.error("runtime sync failed after the upgrade (exit %d) — rerun 'codeanvil runtime sync'",
                  sync.returncode)
        raise SystemExit(sync.returncode)

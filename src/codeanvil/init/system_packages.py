"""OS-installed Python packages (e.g. gnuradio) that uv venvs cannot install.

Shared by the methodology runtime (bridged with a .pth file) and the MCP
servers (bridged with PYTHONPATH)."""

import glob
import subprocess


def detect_system_site_packages(package: str) -> str | None:
    """Find the system site-packages directory containing a Python package.

    GNU Radio and similar packages are installed by the system package manager
    (pacman, apt, dnf) and aren't pip-installable. uv's isolated venvs can't
    see them unless PYTHONPATH bridges the gap. This finds where they live."""
    # Try gnuradio-config-info first (most reliable for GNU Radio)
    if package == "gnuradio":
        try:
            prefix = subprocess.check_output(
                ["gnuradio-config-info", "--prefix"],
                text=True, stderr=subprocess.DEVNULL,
            ).strip().rstrip("/")
            hits = glob.glob(f"{prefix}/lib/python*/site-packages/{package}/__init__.py")
            if hits:
                return hits[0].rsplit(f"/{package}/", 1)[0]
        except (FileNotFoundError, subprocess.CalledProcessError):
            pass

    # Fallback: scan common system locations (Arch, Debian/Ubuntu, Fedora, local builds)
    for pattern in [
        f"/usr/lib/python*/site-packages/{package}/__init__.py",
        f"/usr/lib/python*/dist-packages/{package}/__init__.py",
        f"/usr/local/lib/python*/site-packages/{package}/__init__.py",
        f"/usr/local/lib/python*/dist-packages/{package}/__init__.py",
    ]:
        hits = sorted(glob.glob(pattern), reverse=True)  # newest python first
        if hits:
            return hits[0].rsplit(f"/{package}/", 1)[0]

    return None

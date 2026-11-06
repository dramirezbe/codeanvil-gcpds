"""OS-installed Python packages (e.g. gnuradio) that uv venvs cannot install.

A system package is compiled for one system Python. The only reliable check is
a real import in the target interpreter (`probe`), never "the folder exists":
a folder built for 3.14 is found by a 3.15 venv and still fails to import.
`probe()` reports exactly one outcome — ok, missing, ABI mismatch or broken —
with a message that says what to do. Install instructions are data, keyed by
OS family, in config.yaml `system_packages`.
"""

import glob
import json
import os
import platform
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from codeanvil.config.paths import CONFIG

_PYVER_RE = re.compile(r"python(\d+\.\d+)")


def detect_system_site_packages(package: str) -> str | None:
    """Find the system site-packages directory containing a Python package.

    GNU Radio and similar packages are installed by the system package manager
    (pacman, apt, dnf) and aren't pip-installable. This finds where they live."""
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


def built_for_python(site_dir: str) -> str | None:
    """`3.14` from `/usr/lib/python3.14/site-packages`."""
    match = _PYVER_RE.search(site_dir)
    return match.group(1) if match else None


def system_interpreter_for(site_dir: str) -> Path | None:
    """The system interpreter a site-packages folder belongs to, by explicit
    path (`/usr/bin/python3.14` for `/usr/lib/python3.14/...`), never a
    version shim that can silently move to another minor version."""
    version = built_for_python(site_dir)
    if version is None:
        return None
    prefix = Path(site_dir).parents[2]  # <prefix>/lib/pythonX.Y/site-packages
    candidate = prefix / "bin" / f"python{version}"
    if candidate.is_file():
        return candidate
    found = shutil.which(f"python{version}")
    return Path(found) if found else None


def os_family(os_release: dict | None = None) -> list[str]:
    """Candidate keys of the install table, most specific first."""
    if sys.platform == "darwin":
        return ["darwin"]
    if sys.platform == "win32":
        return ["win32"]
    if os_release is None:
        try:
            os_release = platform.freedesktop_os_release()
        except OSError:
            os_release = {}
    keys = [os_release.get("ID", "")] + os_release.get("ID_LIKE", "").split()
    return [key for key in keys if key]


def install_hint(package: str, os_release: dict | None = None) -> str:
    table = CONFIG.get("system_packages", {}).get(package, {}).get("install", {})
    for key in os_family(os_release):
        if key in table:
            return table[key]
    if table:
        return "; ".join(f"{family}: {command}" for family, command in table.items())
    return f"install {package} with your OS package manager"


@dataclass(frozen=True)
class ProbeResult:
    package: str
    status: str  # "ok" | "missing" | "mismatch" | "broken"
    message: str
    version: str = ""

    @property
    def ok(self) -> bool:
        return self.status == "ok"


def interpreter_version(interpreter: Path) -> str | None:
    """The interpreter's real `X.Y` (it can differ from pyvenv.cfg when the
    venv's base is a symlink that moved)."""
    try:
        result = subprocess.run(
            [str(interpreter), "-c", "import sys; print('%d.%d' % sys.version_info[:2])"],
            capture_output=True, text=True, timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    return result.stdout.strip() if result.returncode == 0 else None


def probe(package: str, interpreter: Path, owner: str) -> ProbeResult:
    """Import `package` in `interpreter`. `owner` names the environment in
    messages (e.g. "the marconi venv") and the fix command (`fix`)."""
    spec = CONFIG.get("system_packages", {}).get(package, {})
    code = spec.get("probe", f"import {package}")
    env = {key: value for key, value in os.environ.items() if key != "PYTHONPATH"}
    try:
        result = subprocess.run(
            [str(interpreter), "-c", code], capture_output=True, text=True, env=env, timeout=60,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return ProbeResult(package, "broken", f"cannot run {interpreter}: {exc}")
    if result.returncode == 0:
        lines = result.stdout.strip().splitlines()
        return ProbeResult(package, "ok", f"{package} {lines[-1] if lines else ''}".strip(),
                           lines[-1] if lines else "")

    site = detect_system_site_packages(package)
    if site is None:
        return ProbeResult(
            package, "missing", f"{package} is not installed. Install it: {install_hint(package)}"
        )
    built = built_for_python(site)
    running = interpreter_version(interpreter)
    if built and running and built != running:
        return ProbeResult(
            package, "mismatch",
            f"{package} is built for Python {built}; {owner} runs {running}.",
        )
    detail = (result.stderr.strip().splitlines() or ["no error output"])[-1]
    return ProbeResult(package, "broken", f"{package} fails to import in {owner}: {detail}")


def _cache_key(package: str, interpreter: Path) -> dict | None:
    site = detect_system_site_packages(package)
    if site is None:
        return None
    try:
        folder_mtime = os.stat(Path(site) / package).st_mtime
    except OSError:
        return None
    return {
        "interpreter": os.path.realpath(interpreter),  # a moved symlink busts the cache
        "folder": site,
        "folder_mtime": folder_mtime,
    }


def cached_probe(package: str, interpreter: Path, owner: str, cache_file: Path) -> ProbeResult:
    """`probe()`, skipping the import when an `ok` for the same real
    interpreter and the same package folder mtime is cached."""
    key = _cache_key(package, interpreter)
    try:
        cache = json.loads(cache_file.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        cache = {}
    entry = cache.get(package) if isinstance(cache, dict) else None
    if key is not None and isinstance(entry, dict) and entry.get("key") == key:
        return ProbeResult(package, "ok", f"{package} {entry.get('version', '')}".strip(),
                           entry.get("version", ""))

    result = probe(package, interpreter, owner)
    if result.ok and key is not None:
        cache = cache if isinstance(cache, dict) else {}
        cache[package] = {"key": key, "version": result.version}
        try:
            cache_file.write_text(json.dumps(cache, indent=2) + "\n", encoding="utf-8")
        except OSError:
            pass  # a cache that cannot be written only costs the next import
    return result

"""`codeanvil python <script> [args...]` — run a script on the methodology runtime.

The script runs with `python -I` from the project root. A script inside
`.agents/skills/<skill>/` is checked first against that skill's
`metadata.runtime` packages. stdout belongs to the script: this command logs
to stderr only. On POSIX the launcher is replaced by the interpreter
(`os.execv`), so the script's parent is the caller; on Windows the launcher
stays as the parent and forwards the exit code.
"""

import os
import subprocess
import sys
from pathlib import Path

from codeanvil.config.logger import get_logger
from codeanvil.config.paths import SKILLS_DIRNAME, find_manifest
from codeanvil.init import runtime
from codeanvil.skills import parse_skill_frontmatter

log = get_logger(__name__)


def _skill_dir(script: Path, root: Path) -> Path | None:
    """`<root>/.agents/skills/<skill>/` when the script lives inside one."""
    skills = (root / SKILLS_DIRNAME).resolve()
    try:
        relative = script.relative_to(skills)
    except ValueError:
        return None
    return skills / relative.parts[0] if len(relative.parts) > 1 else None


def _check_skill_runtime(skill_dir: Path) -> None:
    meta = parse_skill_frontmatter(skill_dir / "SKILL.md") or {}
    needed = meta.get("runtime", [])
    missing = runtime.missing_packages(needed)
    if not missing:
        return
    base = {runtime.requirement_name(spec) for spec in runtime.base_packages()}
    names = " ".join(missing)
    if all(runtime.requirement_name(name) in base for name in missing):
        hint = "Run codeanvil runtime sync."
    else:
        hint = f"Run codeanvil runtime add {names}."
    raise runtime.RuntimeSetupError(f"Skill {skill_dir.name} needs {names}. {hint}")


def cmd_python(script: str, args: list[str] | None = None) -> None:
    args = list(args or [])
    interpreter = runtime.interpreter_path()
    try:
        if not interpreter.is_file():
            raise runtime.RuntimeSetupError("Runtime not installed. Run codeanvil runtime sync.")
        manifest = find_manifest(Path.cwd())
        root = manifest.parent.parent if manifest else Path.cwd().resolve()
        script_path = Path(script).resolve()
        if not script_path.is_file():
            raise runtime.RuntimeSetupError(f"script not found: {script}")
        skill_dir = _skill_dir(script_path, root)
        if skill_dir is not None:
            _check_skill_runtime(skill_dir)
    except runtime.RuntimeSetupError as exc:
        log.error("%s", exc)
        sys.exit(1)

    argv = [str(interpreter), "-I", str(script_path), *args]
    if sys.platform == "win32":
        sys.exit(subprocess.run(argv, cwd=root).returncode)
    os.chdir(root)
    sys.stdout.flush()
    sys.stderr.flush()
    os.execv(argv[0], argv)

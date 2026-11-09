"""`codeanvil runtime <sync|add|remove|list|path>` — the global methodology runtime."""

import sys

from codeanvil.config.logger import get_logger
from codeanvil.init import runtime

log = get_logger(__name__)


def cmd_runtime(action: str, packages: list[str] | None = None) -> None:
    packages = packages or []
    try:
        if action == "sync":
            runtime.sync()
        elif action == "add":
            runtime.add(packages)
        elif action == "remove":
            runtime.remove(packages)
        elif action == "list":
            rows = runtime.listing()
            width = max((len(spec) for spec, _, _ in rows), default=0)
            for spec, source, version in rows:
                print(f"{spec:<{width}}  {source:<4}  {version}")
        elif action == "path":
            interpreter = runtime.interpreter_path()
            if not interpreter.is_file():
                raise runtime.RuntimeSetupError("Runtime not installed. Run codeanvil runtime sync.")
            print(interpreter)
    except runtime.RuntimeSetupError as exc:
        log.error("%s", exc)
        sys.exit(1)

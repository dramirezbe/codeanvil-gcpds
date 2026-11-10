"""Best-effort append-only audit log: <project>/.codeanvil/hil/audit.log (JSON per line)."""

import json
from datetime import datetime
from pathlib import Path


def audit(root: Path, target: str, tool: str, command: str, exit_code: int | None) -> None:
    """One line per action; `exit_code` None = refused / not executed. Never raises."""
    try:
        d = Path(root) / ".codeanvil" / "hil"
        d.mkdir(parents=True, exist_ok=True)
        line = json.dumps(
            {
                "ts": datetime.now().astimezone().isoformat(timespec="seconds"),
                "target": target,
                "tool": tool,
                "command": command,
                "exit": exit_code,
            },
            ensure_ascii=False,
        )
        with open(d / "audit.log", "a", encoding="utf-8") as fh:
            fh.write(line + "\n")
    except Exception:
        pass

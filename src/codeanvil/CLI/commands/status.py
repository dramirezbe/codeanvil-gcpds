"""`codeanvil status` — project identity and latest gate report per gate."""

import re
import sys
from pathlib import Path

import yaml

from codeanvil.config.logger import get_logger
from codeanvil.config.paths import DB_PATH, PROJECT_REPORT, find_manifest
from codeanvil.db.projects import get_project_by_id, get_project_by_name, sync_project
from codeanvil.db.schema import db_exists
from codeanvil.db.utils import connect_db

log = get_logger(__name__)

# Gate report filenames: <gate>_<machine-timestamp>.md (e.g. G0_2026-10-21_16-23-45-123.md)
_REPORT_RE = re.compile(r"^(?P<gate>.+)_(?P<ts>\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}-\d{3})\.md$")


def _latest_reports(report_dir: Path) -> dict[str, str]:
    """Latest report filename per gate, ordered by the machine timestamp."""
    latest: dict[str, str] = {}
    latest_ts: dict[str, str] = {}
    if not report_dir.is_dir():
        return latest
    for path in report_dir.glob("*.md"):
        match = _REPORT_RE.match(path.name)
        if not match:
            continue
        gate = match.group("gate")
        ts = match.group("ts")
        if gate not in latest_ts or ts > latest_ts[gate]:
            latest_ts[gate] = ts
            latest[gate] = path.name
    return latest


def cmd_status(name: str | None = None) -> None:
    if not db_exists(DB_PATH):
        log.error("not initialized — run 'codeanvil init' first")
        sys.exit(1)

    conn = connect_db(DB_PATH)
    try:
        project_dir: Path | None = None
        identity: dict | None = None

        if name is not None:
            # Lookup by human label (projects.name), not by folder name.
            project = get_project_by_name(conn, name)
            if not project:
                log.error("project '%s' not found", name)
                sys.exit(1)
            project_dir = Path(project["path"])
            identity = {"id": project["id"], "name": project["name"]}
            manifest = find_manifest(project_dir)
            # find_manifest walks up — a parent dir's manifest must not
            # hijack identity when the recorded project path is stale.
            if manifest is not None and manifest.parent.parent.resolve() == project_dir.resolve():
                try:
                    identity = yaml.safe_load(manifest.read_text(encoding="utf-8"))
                except yaml.YAMLError:
                    log.warning("cannot parse %s — using DB identity", manifest)
        else:
            manifest = find_manifest(Path.cwd())
            if manifest is None:
                log.error("no .codeanvil/project.yaml found (searched up from cwd) and no project name given")
                sys.exit(1)
            project_dir = manifest.parent.parent
            try:
                identity = yaml.safe_load(manifest.read_text(encoding="utf-8"))
            except yaml.YAMLError:
                log.error("cannot parse %s", manifest)
                sys.exit(1)
            if not isinstance(identity, dict) or "id" not in identity or "name" not in identity:
                log.error("%s is not a valid project manifest (missing id/name)", manifest)
                sys.exit(1)
            # Agents run status constantly — auto-register a manifest that
            # isn't in the DB yet instead of demanding a separate sync.
            existing = get_project_by_id(conn, identity["id"])
            if existing is None:
                sync_project(conn, identity["id"], identity["name"], project_dir.resolve())

        if not project_dir or not identity:
            log.error("could not resolve project")
            sys.exit(1)

        print(f"Project: {identity['name']} ({identity['id']})")
        print(f"Path:    {project_dir.resolve()}")

        latest = _latest_reports(project_dir / PROJECT_REPORT)
        if not latest:
            print("Reports: none yet (.codeanvil/report/ is empty)")
            return
        print("Reports (latest per gate):")
        for gate in sorted(latest):
            print(f"  {gate}: {latest[gate]}")
    finally:
        conn.close()

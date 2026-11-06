"""`codeanvil backup <stage>` — save a stage's working artifacts before overwrite.

The command copies and hashes files; it never decides or advances a gate. Each
overwriting skill runs it immediately before the step that rewrites the
artifact, and cites the printed backup path in its iteration.
"""

import hashlib
import shutil
import sys
from pathlib import Path

import yaml

from codeanvil.config.logger import get_logger
from codeanvil.config.paths import CONFIG, PROJECT_BACKUPS, PROJECT_REPORT, find_manifest
from codeanvil.config.time import format_timestamp, format_timestamp_machine
from codeanvil.reports import ReportState, cycle_reports

log = get_logger(__name__)

BACKUP_STAGES = ("S0", "S1", "S2", "G2")


class BackupError(Exception):
    """A precondition failed; the message tells the agent what to fix."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _producer(
    cycles: dict[str, dict[str, ReportState]], active: str | None, stage: str
) -> tuple[str, int] | None:
    """Cycle and iteration that last wrote the stage's artifacts, or None.

    The active cycle wins. In a new cycle the fixed-path artifacts still belong
    to the cycle whose RFD superseded it, so that cycle's latest iteration is
    the baseline; cycles are never guessed from their names alone."""
    if active is not None:
        state = cycles.get(active, {}).get(stage)
        if state is not None and state.iteration is not None:
            return active, state.iteration
    for cycle in reversed(sorted(cycles)):
        if cycle == active:
            continue
        rfd = cycles[cycle].get("RFD")
        if rfd is None or rfd.superseded_by != active:
            continue
        state = cycles[cycle].get(stage)
        if state is not None and state.iteration is not None:
            return cycle, state.iteration
    return None


def _targets(stage: str, active: str | None) -> list[Path]:
    """Project-relative target paths for a stage, `{cycle}` expanded."""
    templates = CONFIG.get("backup_targets", {}).get(stage)
    if not templates:
        raise BackupError(f"no backup targets configured for {stage} in templates/config.yaml")
    targets: list[Path] = []
    for template in templates:
        if "{cycle}" in template:
            if not active:
                raise BackupError(
                    f"no active cycle in .codeanvil/project.yaml — set 'cycle:' before backing up {stage}"
                )
            template = template.format(cycle=active)
        targets.append(Path(template))
    return targets


def _relative(folder: Path, project_dir: Path) -> str:
    return f"{folder.relative_to(project_dir).as_posix()}/"


def _manifest_digests(folder: Path) -> dict[str, str]:
    """source -> sha256 from an existing MANIFEST.yaml, or raise BackupError."""
    manifest = folder / "MANIFEST.yaml"
    try:
        data = yaml.safe_load(manifest.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise BackupError(
            f"backup exists without a readable MANIFEST.yaml: {folder} — inspect it before continuing"
        ) from exc
    files = data.get("files") if isinstance(data, dict) else None
    if not isinstance(files, list):
        raise BackupError(
            f"backup exists without a readable MANIFEST.yaml: {folder} — inspect it before continuing"
        )
    return {
        str(entry.get("source")): str(entry.get("sha256"))
        for entry in files
        if isinstance(entry, dict)
    }


def _write_backup(
    folder: Path, project_dir: Path, sources: list[Path], manifest: dict
) -> None:
    """Copy into a staging folder, then rename: no half-written backup is ever
    mistaken for an existing one."""
    staging = folder.with_name(f"{folder.name}.tmp")
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)
    for source in sources:
        shutil.copy2(project_dir / source, staging / source.name)
    (staging / "MANIFEST.yaml").write_text(
        yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8"
    )
    staging.rename(folder)


def _run(stage: str) -> None:
    manifest_path = find_manifest(Path.cwd())
    if manifest_path is None:
        raise BackupError("no .codeanvil/project.yaml found (searched up from cwd)")
    try:
        identity = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise BackupError(f"cannot read {manifest_path}: {exc}") from exc
    if not isinstance(identity, dict):
        raise BackupError(f"{manifest_path} is not a valid project manifest")
    project_dir = manifest_path.parent.parent
    active = identity.get("cycle")
    active = active if isinstance(active, str) and active else None

    targets = _targets(stage, active)
    sources = [target for target in targets if (project_dir / target).is_file()]
    if not sources:
        print("nothing to back up")
        return

    cycles = cycle_reports(project_dir / PROJECT_REPORT)
    producer = _producer(cycles, active, stage)
    backups_dir = project_dir / PROJECT_BACKUPS
    if producer is None:
        folder = backups_dir / "unknown" / f"{stage}_{format_timestamp_machine()}"
    else:
        folder = backups_dir / producer[0] / f"{stage}_iter{producer[1]}"

    files = [
        {"source": source.as_posix(), "sha256": _sha256(project_dir / source)}
        for source in sources
    ]

    if folder.exists():
        if _manifest_digests(folder) == {entry["source"]: entry["sha256"] for entry in files}:
            print(f"already backed up: {_relative(folder, project_dir)}")
            return
        raise BackupError(
            f"backup already exists with different content: {_relative(folder, project_dir)}"
            " — a file was edited outside the flow; stop and show this to the human"
        )

    manifest = {
        "created": format_timestamp(),
        "active_cycle": active,
        "producer": {
            "cycle": producer[0] if producer else "unknown",
            "stage": stage,
            "iteration": producer[1] if producer else "unknown",
        },
        "files": files,
    }
    try:
        _write_backup(folder, project_dir, sources, manifest)
    except OSError as exc:
        raise BackupError(f"cannot write {_relative(folder, project_dir)}: {exc}") from exc

    label = f"{stage} iteration {producer[1]}" if producer else stage
    print(f"Backed up {label} → {_relative(folder, project_dir)}")


def cmd_backup(stage: str) -> None:
    """Entry point for `codeanvil backup <stage>`."""
    try:
        _run(stage)
    except BackupError as exc:
        log.error("%s", exc)
        sys.exit(1)

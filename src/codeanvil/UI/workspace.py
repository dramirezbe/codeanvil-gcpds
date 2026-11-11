"""Read-only views of the artifacts and report chain of a 0.7.0 project."""

from pathlib import Path, PurePosixPath
import re

from fastapi import APIRouter, HTTPException

from codeanvil.config.paths import CONFIG
from codeanvil.reports import (
    backup_entries, gate_order, parse_report_iterations, report_header,
    report_state, stale_reason, unfenced_text,
)
from codeanvil.UI.project_context import project_context, project_summary

_CYCLE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]*\Z")
_DEVIATION = re.compile(r"RFD-\d{3}\.md\Z")
_REPORTS = tuple(CONFIG["report_order"])
_GT = {"build_package.md": "Build Package", "StRS.md": "Stakeholder requirements", "SyRS.md": "System requirements"}
_GRAPH_THEMES = {"dependency_graph.html": "dark", "dependency_graph_light.html": "light"}
_DESIGN = {"SDD.md": "Service design", "dependency_graph.html": "Dependency graph",
           "dependency_graph_light.html": "Dependency graph · light"}


def _project(root: Path, selected: str | None) -> tuple[Path, dict]:
    try:
        root = root.resolve()
        start = Path(selected).expanduser() if selected else root
        if not start.is_absolute():
            start = root / start
        context = project_context(start)
    except (ValueError, OSError, RuntimeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if context is None:
        raise HTTPException(status_code=409, detail="Open a CodeAnvil project first")
    return context


def _contained(root: Path, relative: str) -> Path:
    """Resolve every ancestor, rejecting root and nested symlink escapes alike."""
    parts = PurePosixPath(relative).parts
    if not parts or relative.startswith("/") or "\\" in relative or ".." in parts:
        raise HTTPException(status_code=400, detail="Invalid artifact path")
    try:
        target = (root / relative).resolve()
        owner = root.resolve()
    except (OSError, RuntimeError) as exc:
        raise HTTPException(status_code=400, detail="Artifact path cannot be resolved") from exc
    if not target.is_relative_to(owner):
        raise HTTPException(status_code=400, detail="Artifact resolves outside the project")
    return target


def _allowed(relative: str) -> bool:
    parts = PurePosixPath(relative).parts
    if len(parts) == 3 and parts[:2] == (".codeanvil", "GT"):
        return parts[-1] in _GT
    if len(parts) == 3 and parts[:2] == (".codeanvil", "design"):
        return parts[-1] in _DESIGN
    if len(parts) not in (4, 5) or parts[:2] != (".codeanvil", "report"):
        return False
    if not _CYCLE.fullmatch(parts[2]):
        return False
    if len(parts) == 4:
        return parts[3] in {f"{stage}.md" for stage in (*_REPORTS, "RFD")}
    return (
        parts[3:] in (("S2_artifacts", "test_run.md"), ("G2_artifacts", "verified_prototype.md"))
        or (parts[3] == "RFD_artifacts" and bool(_DEVIATION.fullmatch(parts[4])))
    )


def _read(root: Path, relative: str) -> str:
    if not _allowed(relative):
        raise HTTPException(status_code=400, detail="Unsupported artifact")
    path = _contained(root, relative)
    if not _allowed(path.relative_to(root.resolve()).as_posix()):
        raise HTTPException(status_code=400, detail="Artifact link targets an unsupported file")
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Artifact not found")
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise HTTPException(status_code=400, detail="Artifact is not readable UTF-8 text") from exc


def _latest(text: str) -> str:
    sections = parse_report_iterations(text)
    return unfenced_text(sections[-1].content if sections else text)


def _field(text: str, name: str) -> str | None:
    match = re.search(rf"^{re.escape(name)}:\s*(.+?)\s*$", _latest(text), re.MULTILINE)
    return match.group(1) if match else None


def _cycle_state(root: Path, cycle: str, active: str | None) -> tuple[dict, dict, dict]:
    base = f".codeanvil/report/{cycle}"
    gates, texts = {}, {}
    for stage in (*_REPORTS, "RFD"):
        relative = f"{base}/{stage}.md"
        file = _contained(root, relative)
        if file.is_file():
            texts[stage] = _read(root, relative)
            gates[stage] = report_state(file)
    rfd = gates.get("RFD")
    withdrawn = _field(texts.get("RFD", ""), "Outcome") == "Withdrawn"
    suspended = not withdrawn and (
        (rfd is not None and rfd.hitl == "FEEDBACK")
        or any(_field(texts.get(stage, ""), "Verdict") == "RFD" for stage in ("S1", "G1", "G2"))
    )
    superseded = rfd.superseded_by if rfd else None
    state = {
        "name": cycle,
        "active": cycle == active,
        "closed": bool(superseded),
        "superseded_by": superseded,
        "draft": _contained(root, f"{base}/DRAFT").is_file(),
        "suspended": bool(suspended and not superseded),
    }
    return state, gates, texts


def _artifact(root: Path, path: str, label: str, kind: str, cycle: str | None = None, working: bool = False) -> dict:
    item = {"path": path, "label": label, "kind": kind, "exists": _contained(root, path).is_file()}
    if cycle:
        item["cycle"] = cycle
    if working:
        item["working_copy"] = True
    return item


def _inventory(root: Path, cycle: str | None) -> list[dict]:
    artifacts = [
        _artifact(root, f".codeanvil/GT/{name}", label, "gt", working=True)
        for name, label in _GT.items()
    ]
    for name, label in _DESIGN.items():
        item = _artifact(root, f".codeanvil/design/{name}", label, "design", working=True)
        if name in _GRAPH_THEMES:
            item["graph_theme"] = _GRAPH_THEMES[name]
        artifacts.append(item)
    if cycle is None:
        return artifacts
    base = f".codeanvil/report/{cycle}"
    artifacts.extend(_artifact(root, f"{base}/{stage}.md", stage, "report", cycle) for stage in _REPORTS)
    if _contained(root, f"{base}/RFD.md").is_file():
        artifacts.append(_artifact(root, f"{base}/RFD.md", "Deviation report", "report", cycle))
    artifacts.extend([
        _artifact(root, f"{base}/S2_artifacts/test_run.md", "S2 test run", "test_run", cycle),
        _artifact(root, f"{base}/G2_artifacts/verified_prototype.md", "Verified Prototype", "prototype", cycle),
    ])
    deviations = _contained(root, f"{base}/RFD_artifacts")
    if deviations.is_dir():
        for path in sorted(deviations.iterdir()):
            if _DEVIATION.fullmatch(path.name):
                artifacts.append(_artifact(root, f"{base}/RFD_artifacts/{path.name}", path.stem, "deviation", cycle))
    return artifacts


def _prototype_baseline(root: Path, cycle: str, gates: dict) -> tuple[bool, str]:
    text = unfenced_text(_read(root, f".codeanvil/report/{cycle}/G2_artifacts/verified_prototype.md"))
    section = re.search(r"^## 1\. Cycle\s*$(.*?)(?=^## |\Z)", text, re.MULTILINE | re.DOTALL)
    row = re.search(r"^\|\s*Based on\s*\|\s*([^|]+)\|\s*$", section.group(1), re.MULTILINE) if section else None
    baseline = re.fullmatch(r"S2 iteration (\d+),\s*G2 iteration (\d+)", row.group(1).strip().strip("`")) if row else None
    if baseline is None:
        return False, "Verified Prototype baseline is missing or malformed"
    declared = tuple(int(value) for value in baseline.groups())
    current = tuple(gates[stage].iteration if stage in gates else None for stage in ("S2", "G2"))
    if declared != current:
        return False, f"Verified Prototype is stale: based on S2 iteration {declared[0]}, G2 iteration {declared[1]}"
    return True, "G2 passed with a current Verified Prototype"


def read_overview(root: Path, project_path: str | None = None, cycle: str | None = None) -> dict:
    project, identity = _project(root, project_path)
    active = identity.get("cycle")
    report_dir = _contained(project, ".codeanvil/report")
    names = {
        path.name for path in report_dir.iterdir()
        if path.is_dir() and _CYCLE.fullmatch(path.name)
    } if report_dir.is_dir() else set()
    if active:
        names.add(active)
    if cycle is not None and (not _CYCLE.fullmatch(cycle) or cycle not in names):
        raise HTTPException(status_code=404, detail="Cycle not found")
    selected = cycle or active or (sorted(names)[-1] if names else None)
    cycles, states = [], {}
    for name in sorted(names):
        status, gates, texts = _cycle_state(project, name, active)
        cycles.append(status)
        states[name] = (status, gates, texts)
    status, gates, texts = states[selected] if selected else ({}, {}, {})
    stages = set(CONFIG["stage_reports"])
    reports = []
    for stage in sorted({*_REPORTS, *gates}, key=gate_order):
        state = gates.get(stage)
        hitl = state.hitl if state else None
        reports.append({
            "id": stage,
            "iteration": state.iteration if state else None,
            "hitl": hitl,
            "based_on": state.based_on if state else None,
            "stale_reason": stale_reason(stage, gates),
            "state": "missing" if state is None else "delivered" if stage in stages and hitl == "PASS" else hitl or "UNKNOWN",
            "verdict": _field(texts.get(stage, ""), "Verdict"),
        })
    artifacts = _inventory(project, selected)
    passed = sum(row["id"] in _REPORTS and row["hitl"] == "PASS" and not row["stale_reason"] for row in reports)
    prototype = any(item["kind"] == "prototype" and item["exists"] for item in artifacts)
    prototype_current, prototype_reason = _prototype_baseline(project, selected, gates) if prototype else (False, "G2 output is missing")
    if status.get("closed"):
        reason = f"Cycle closed; superseded by {status['superseded_by']}"
    elif status.get("draft"):
        reason = "Draft has unresolved review items"
    elif status.get("suspended"):
        reason = "Cycle suspended by RFD"
    elif passed != len(_REPORTS):
        reason = "Waiting for current stage deliveries and human gate verdicts"
    else:
        reason = prototype_reason
    complete = passed == len(_REPORTS) and prototype_current and not any(status.get(key) for key in ("closed", "draft", "suspended"))
    return {
        "project": project_summary(project, identity),
        "active_cycle": active,
        "selected_cycle": selected,
        "cycles": cycles,
        "reports": reports,
        "completion": {"passed": passed, "total": len(_REPORTS), "complete": complete, "reason": reason},
        "synthetic_fixture": _contained(project, "UI_FIXTURE.md").is_file(),
        "artifacts": artifacts,
    }


def read_artifact(root: Path, project_path: str | None, path: str, iteration: int | None = None) -> dict:
    project, _ = _project(root, project_path)
    content = _read(project, path)
    sections = parse_report_iterations(content) if PurePosixPath(path).parent.parent == PurePosixPath(".codeanvil/report") else []
    if iteration is not None:
        chosen = next((section for section in sections if section.number == iteration), None)
        if chosen is None:
            raise HTTPException(status_code=404, detail="Report iteration not found")
        header = report_header(content)
        content = header + chosen.content + "\n"
    format_ = "html" if path.endswith(".html") else "markdown" if path.endswith(".md") else "text"
    if path in {f".codeanvil/design/{name}" for name in _GRAPH_THEMES}:
        library_path = ".agents/skills/S1_design_services/assets/vis-network.min.js"
        library = _contained(project, library_path)
        if library != project / library_path:
            raise HTTPException(status_code=400, detail="Graph library must use the copied project asset")
        if library.is_file():
            script = library.read_text(encoding="utf-8").replace("</script", "<\\/script")
            content = re.sub(
                r'<script\b[^>]*\bsrc=([\"\'])[^\"\']*vis-network(?:\.min)?\.js\1[^>]*>\s*</script>',
                lambda _: f"<script>{script}</script>", content, flags=re.IGNORECASE,
            )
    result = {
        "path": path, "name": PurePosixPath(path).name, "content": content, "format": format_,
        "iterations": [{"number": section.number, "hitl": section.hitl} for section in sections],
    }
    if iteration is not None:
        result["selected_iteration"] = iteration
    return result


def read_backups(root: Path, project_path: str | None = None) -> dict:
    project, _ = _project(root, project_path)
    base = _contained(project, ".codeanvil/backups")
    if base.is_dir():
        for cycle in base.iterdir():
            cycle_path = _contained(project, f".codeanvil/backups/{cycle.name}")
            if cycle_path.is_dir():
                for folder in cycle_path.iterdir():
                    _contained(project, f".codeanvil/backups/{cycle.name}/{folder.name}")
    return {"backups": backup_entries(base)}


def create_workspace_router(root: Path) -> APIRouter:
    router = APIRouter(prefix="/api/workspace", tags=["workspace"])

    @router.get("/overview")
    def overview(project_path: str | None = None, cycle: str | None = None):
        return read_overview(root, project_path, cycle)

    @router.get("/artifact")
    def artifact(path: str, project_path: str | None = None, iteration: int | None = None):
        return read_artifact(root, project_path, path, iteration)

    @router.get("/backups")
    def backups(project_path: str | None = None):
        return read_backups(root, project_path)

    return router

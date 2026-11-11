"""Exercise read-only artifact/state views against 0.7.0 fixtures and live edits."""

import asyncio
import hashlib
from pathlib import Path

import pytest
import yaml

pytest.importorskip("fastapi")
httpx = pytest.importorskip("httpx")
from fastapi import FastAPI, HTTPException

from codeanvil.UI.workspace import create_workspace_router, read_artifact, read_backups, read_overview


EXAMPLES = Path(__file__).resolve().parents[1] / "methodology/test/v0.7.0-example-artifacts"
ORDER = ["S0", "G0", "S1", "G1", "S2", "G2"]


def project(tmp_path, cycle="01_demo"):
    root = tmp_path / "project"
    (root / ".codeanvil").mkdir(parents=True)
    (root / ".codeanvil/project.yaml").write_text(yaml.safe_dump({
        "id": "019f0000-0000-7000-8000-000000000001", "name": "UI test", "cycle": cycle,
    }))
    return root


def report(root, stage, text=None):
    path = root / f".codeanvil/report/01_demo/{stage}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    before = "" if stage in ("S0", "RFD") else f"Based on: {ORDER[ORDER.index(stage) - 1]} iteration 1\n"
    path.write_text(text or f"# {stage}\n\n## Iteration 1\n| HITL | PASS |\n{before}")
    return path


@pytest.mark.parametrize("directory,passed,complete", [
    ("laboratorio_espectro_rf", 0, False),
    ("monitor_ocupacion_fm", 2, False),
    ("banco_telemetria_cots", 4, False),
    ("api_procesamiento_senales", 5, False),
    ("panel_prototipo", 6, True),
])
def test_all_five_archived_states(directory, passed, complete):
    result = read_overview(EXAMPLES / directory)
    assert result["completion"]["passed"] == passed
    assert result["completion"]["complete"] is complete
    assert len(result["reports"]) == 6
    assert result["synthetic_fixture"] is (passed > 0)
    assert result["selected_cycle"] == ("01_ui_demo" if passed else None)


def test_active_cycle_exists_before_its_first_report(tmp_path):
    root = project(tmp_path)
    result = read_overview(root)
    assert result["cycles"] == [{
        "name": "01_demo", "active": True, "closed": False,
        "superseded_by": None, "draft": False, "suspended": False,
    }]
    assert all(row["state"] == "missing" for row in result["reports"])


def test_partial_latest_iteration_blocks_completion(tmp_path):
    root = project(tmp_path)
    for stage in ORDER:
        report(root, stage)
    report(root, "G2", "## Iteration 1\n| HITL | PASS |\n## Iteration 2\nBased on: S2 iteration 1\n")
    artifact = root / ".codeanvil/report/01_demo/G2_artifacts/verified_prototype.md"
    artifact.parent.mkdir()
    artifact.write_text("# Previous prototype")
    result = read_overview(root)
    assert result["reports"][-1]["state"] == "UNKNOWN"
    assert result["completion"]["passed"] == 5
    assert not result["completion"]["complete"]


def test_stale_status_is_transitive_and_stage_pass_means_delivered(tmp_path):
    root = project(tmp_path)
    report(root, "S0", "## Iteration 2\n| HITL | PASS |\n")
    report(root, "G0")
    report(root, "S1")
    rows = {row["id"]: row for row in read_overview(root)["reports"]}
    assert rows["S0"]["state"] == "delivered"
    assert rows["G0"]["state"] == "PASS"
    assert rows["S1"]["stale_reason"] == "G0 is stale"
    assert read_overview(root)["completion"]["passed"] == 1


def test_draft_rfd_withdrawal_and_cycle_closure(tmp_path):
    root = project(tmp_path)
    report(root, "G1", "## Iteration 1\n| HITL | FEEDBACK |\nVerdict: RFD\n")
    rfd = report(root, "RFD", "## Iteration 1\n| HITL | FEEDBACK |\n")
    assert read_overview(root)["cycles"][0]["suspended"]
    rfd.write_text(rfd.read_text() + "## Iteration 2\n| HITL | PASS |\nOutcome: Withdrawn\n")
    assert not read_overview(root)["cycles"][0]["suspended"]
    draft = root / ".codeanvil/report/02_draft/DRAFT"
    draft.parent.mkdir()
    draft.write_text("Draft opened for review")
    assert read_overview(root, cycle="02_draft")["cycles"][1]["draft"]
    rfd.write_text("## Iteration 3\n| HITL | PASS |\nSuperseded by cycle: 02_draft\n")
    result = read_overview(root, cycle="01_demo")
    assert result["cycles"][0]["closed"]
    assert not result["cycles"][0]["suspended"]
    assert result["completion"]["reason"].startswith("Cycle closed")


def test_selecting_another_cycle_does_not_change_active_identity(tmp_path):
    root = project(tmp_path)
    report(root, "S0")
    other = root / ".codeanvil/report/02_other"
    other.mkdir()
    before = (root / ".codeanvil/project.yaml").read_bytes()
    result = read_overview(root, cycle="02_other")
    assert result["active_cycle"] == "01_demo"
    assert result["selected_cycle"] == "02_other"
    assert (root / ".codeanvil/project.yaml").read_bytes() == before


@pytest.mark.parametrize("blocker", ["draft", "suspended", "closed"])
def test_full_pass_chain_cannot_override_cycle_blockers(tmp_path, blocker):
    root = project(tmp_path)
    for stage in ORDER:
        report(root, stage)
    prototype = root / ".codeanvil/report/01_demo/G2_artifacts/verified_prototype.md"
    prototype.parent.mkdir()
    prototype.write_text("# Prior prototype")
    if blocker == "draft":
        (prototype.parent.parent / "DRAFT").write_text("Review pending")
    elif blocker == "suspended":
        report(root, "RFD", "## Iteration 1\n| HITL | FEEDBACK |\n")
    else:
        report(root, "RFD", "## Iteration 1\n| HITL | PASS |\nSuperseded by cycle: 02_new\n")
    result = read_overview(root)
    assert result["completion"]["passed"] == 6
    assert result["cycles"][0][blocker]
    assert not result["completion"]["complete"]


def test_prototype_baseline_must_match_current_s2_and_g2_iterations(tmp_path):
    root = project(tmp_path)
    for stage in ORDER:
        report(root, stage)
    prototype = root / ".codeanvil/report/01_demo/G2_artifacts/verified_prototype.md"
    prototype.parent.mkdir()
    prototype.write_text("# Prototype\n## 1. Cycle\n| Based on | S2 iteration 1, G2 iteration 1 |\n")
    assert read_overview(root)["completion"]["complete"]
    g2 = root / ".codeanvil/report/01_demo/G2.md"
    g2.write_text(g2.read_text() + "## Iteration 2\n| HITL | PASS |\nBased on: S2 iteration 1\n")
    result = read_overview(root)
    assert result["completion"]["passed"] == 6
    assert not result["completion"]["complete"]
    assert "Prototype is stale" in result["completion"]["reason"]
    assert next(item for item in result["artifacts"] if item["kind"] == "prototype")["exists"]
    prototype.write_text("# Prototype\n## 1. Cycle\n| Based on | S2 iteration 1, G2 iteration 2 |\n")
    assert read_overview(root)["completion"]["complete"]


@pytest.mark.parametrize("content", [
    "# Prototype without baseline",
    "## 1. Cycle\n| Based on | Unknown |\n",
    "## 1. Cycle\n~~~markdown\n| Based on | S2 iteration 1, G2 iteration 1 |\n~~~\n",
])
def test_unknown_or_fenced_prototype_baseline_is_not_current(tmp_path, content):
    root = project(tmp_path)
    for stage in ORDER:
        report(root, stage)
    prototype = root / ".codeanvil/report/01_demo/G2_artifacts/verified_prototype.md"
    prototype.parent.mkdir()
    prototype.write_text(content)
    result = read_overview(root)
    assert not result["completion"]["complete"]
    assert "baseline is missing or malformed" in result["completion"]["reason"]


def test_fenced_rfd_instruction_does_not_suspend_cycle(tmp_path):
    root = project(tmp_path)
    report(root, "G1", "## Iteration 1\n| HITL | PASS |\n### Description\n~~~text\nVerdict: RFD\n~~~\n")
    assert not read_overview(root)["cycles"][0]["suspended"]


def test_nested_artifacts_and_graph_are_readable_without_writes():
    root = EXAMPLES / "panel_prototipo"
    source = root / ".codeanvil/design/dependency_graph.html"
    before = hashlib.sha256(source.read_bytes()).hexdigest()
    result = read_artifact(root, None, ".codeanvil/design/dependency_graph.html")
    assert result["format"] == "html"
    assert '<script src="../../.agents/' not in result["content"]
    assert hashlib.sha256(source.read_bytes()).hexdigest() == before
    for path in ("S2_artifacts/test_run.md", "G2_artifacts/verified_prototype.md"):
        result = read_artifact(root, None, f".codeanvil/report/01_ui_demo/{path}")
        assert result["format"] == "markdown"
        assert "SYNTHETIC UI FIXTURE" in result["content"]
    artifacts = read_overview(root)["artifacts"]
    assert all(item.get("working_copy") for item in artifacts if item["kind"] in {"gt", "design"})


def test_select_report_iteration_keeps_header_and_hides_other_iteration(tmp_path):
    root = project(tmp_path)
    report(root, "S0", "# S0 header\n## Iteration 1\n| HITL | FEEDBACK |\nFirst\n## Iteration 2\n| HITL | PASS |\nSecond\n")
    result = read_artifact(root, None, ".codeanvil/report/01_demo/S0.md", 1)
    assert result["content"].startswith("# S0 header")
    assert "First" in result["content"] and "Second" not in result["content"]
    assert result["iterations"] == [{"number": 1, "hitl": "FEEDBACK"}, {"number": 2, "hitl": "PASS"}]


def test_iteration_selection_keeps_fenced_header_and_raw_quoted_content(tmp_path):
    root = project(tmp_path)
    header = "# Report\n```markdown\n## Iteration 1\n| HITL | PASS |\n```\nHeader ends here.\n"
    report(root, "G1", header + "## Iteration 1\n| HITL | FEEDBACK |\n### Description\n~~~text\n## Iteration 99\n~~~\n")
    result = read_artifact(root, None, ".codeanvil/report/01_demo/G1.md", 1)
    assert result["content"].startswith(header)
    assert "## Iteration 99" in result["content"]
    assert result["iterations"] == [{"number": 1, "hitl": "FEEDBACK"}]


@pytest.mark.parametrize("path", ["../.env", "/etc/passwd", ".codeanvil/project.yaml", ".codeanvil/report/01_demo/../S0.md"])
def test_unapproved_paths_are_rejected(tmp_path, path):
    with pytest.raises(HTTPException) as error:
        read_artifact(project(tmp_path), None, path)
    assert error.value.status_code == 400


@pytest.mark.parametrize("ancestor", [".codeanvil/GT", ".codeanvil/report"])
def test_methodology_directory_symlink_escape_is_rejected(tmp_path, ancestor):
    root = project(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "StRS.md").write_text("Do not read")
    (root / ancestor).symlink_to(outside, target_is_directory=True)
    with pytest.raises(HTTPException) as error:
        read_overview(root)
    assert error.value.status_code == 400


def test_nested_artifact_symlink_escape_is_rejected(tmp_path):
    root = project(tmp_path)
    outside = tmp_path / "private.md"
    outside.write_text("Private")
    path = root / ".codeanvil/report/01_demo/S2_artifacts/test_run.md"
    path.parent.mkdir(parents=True)
    path.symlink_to(outside)
    with pytest.raises(HTTPException) as error:
        read_artifact(root, None, ".codeanvil/report/01_demo/S2_artifacts/test_run.md")
    assert error.value.status_code == 400


def test_known_artifact_cannot_link_to_an_unapproved_file_inside_project(tmp_path):
    root = project(tmp_path)
    (root / ".env").write_text("LOCAL_SECRET=do-not-render")
    gt = root / ".codeanvil/GT"
    gt.mkdir()
    (gt / "StRS.md").symlink_to(root / ".env")
    with pytest.raises(HTTPException) as error:
        read_artifact(root, None, ".codeanvil/GT/StRS.md")
    assert error.value.status_code == 400


def test_symlink_loop_returns_a_structured_client_error(tmp_path):
    root = project(tmp_path)
    gt = root / ".codeanvil/GT"
    gt.mkdir()
    (gt / "StRS.md").symlink_to("StRS.md")
    for read in (lambda: read_artifact(root, None, ".codeanvil/GT/StRS.md"), lambda: read_overview(root)):
        with pytest.raises(HTTPException) as error:
            read()
        assert error.value.status_code == 400
        assert error.value.detail == "Artifact path cannot be resolved"


def test_relative_project_selection_is_anchored_to_ui_root(tmp_path, monkeypatch):
    root = project(tmp_path)
    monkeypatch.chdir(tmp_path.parent)
    assert read_overview(tmp_path, "project")["project"]["path"] == str(root)


def test_malformed_manifest_has_a_useful_error(tmp_path):
    root = project(tmp_path)
    (root / ".codeanvil/project.yaml").write_text("[not, a, mapping]")
    with pytest.raises(HTTPException) as error:
        read_overview(root)
    assert error.value.status_code == 400


def test_backup_view_preserves_latest_per_stage_mapping(tmp_path):
    root = project(tmp_path)
    base = root / ".codeanvil/backups/01_demo"
    for folder in ("S1_iter1", "S1_iter2", "S2_iter1"):
        (base / folder).mkdir(parents=True)
    assert read_backups(root) == {"backups": {"01_demo": [
        ("S1", 2, "01_demo/S1_iter2"), ("S2", 1, "01_demo/S2_iter1"),
    ]}}


def test_backup_directory_escape_is_rejected(tmp_path):
    root = project(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    (root / ".codeanvil/backups").symlink_to(outside, target_is_directory=True)
    with pytest.raises(HTTPException) as error:
        read_backups(root)
    assert error.value.status_code == 400


def test_router_http_contract(tmp_path):
    root = project(tmp_path)
    report(root, "S0")
    app = FastAPI()
    app.include_router(create_workspace_router(root))

    async def requests():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver") as client:
            overview = await client.get("/api/workspace/overview")
            assert overview.status_code == 200
            assert overview.json()["reports"][0]["state"] == "delivered"
            artifact = await client.get("/api/workspace/artifact", params={"path": ".codeanvil/report/01_demo/S0.md", "iteration": 1})
            assert artifact.status_code == 200
            assert artifact.json()["selected_iteration"] == 1
            bad = await client.get("/api/workspace/artifact", params={"path": "../private.md"})
            assert bad.status_code == 400

    asyncio.run(asyncio.wait_for(requests(), timeout=10))

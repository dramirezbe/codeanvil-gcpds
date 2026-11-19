"""Exercise read-only workspace views for the current V-SIL v4 project format."""

import asyncio
import hashlib
import json
from pathlib import Path

import pytest
import yaml

pytest.importorskip("fastapi")
httpx = pytest.importorskip("httpx")
from fastapi import FastAPI, HTTPException

from codeanvil.UI.workspace import create_workspace_router, read_artifact, read_backups, read_evidence, read_overview


FULL_FLOW = Path(__file__).resolve().parents[1] / "methodology/test/0.9.6-full-flow-hackrf-rpi-mvp"
ORDER = ["S0", "G0", "S1", "G1", "S2", "G2", "S3", "G3"]


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


def test_saved_096_full_flow_uses_current_eight_report_chain():
    result = read_overview(FULL_FLOW)
    assert [row["id"] for row in result["reports"]] == ORDER
    assert result["selected_cycle"] == "01_fm_hackrf_rpi5_mvp"
    assert result["completion"]["total"] == 8
    assert next(row for row in result["reports"] if row["id"] == "G3")["hitl"] == "PASS"
    prototype = next(item for item in result["artifacts"] if item["kind"] == "prototype")
    test_run = next(item for item in result["artifacts"] if item["kind"] == "test_run")
    assert prototype["exists"] and prototype["path"].endswith("G3_artifacts/verified_prototype.md")
    assert test_run["exists"] and test_run["path"].endswith("S3_artifacts/test_run.md")


def test_saved_full_flow_preserves_evidence_limits():
    evidence = read_evidence(FULL_FLOW)
    assert evidence["telemetry"] == []
    assert evidence["measurements"] == []
    assert {log["label"] for log in evidence["test_logs"]} == {
        "pytest_vl0.txt", "pytest_vl1.txt", "vitest_vl0.txt", "vitest_vl1.txt",
    }
    vl2 = evidence["vl2"]
    assert vl2["prototype_current"]
    assert vl2["statement"].startswith("VL-2: NO EVIDENCE.")
    assert vl2["manual_telemetry"]
    assert any(row["id"] == "PATH-006" and row["result"].startswith("BLOCKED") for row in vl2["items"])


def test_evidence_uses_selected_cycle_and_current_g3_format(tmp_path):
    root = project(tmp_path)
    prototype = root / ".codeanvil/report/01_demo/G3_artifacts/verified_prototype.md"
    prototype.parent.mkdir(parents=True)
    prototype.write_text(
        "## 5. Path evidence\n"
        "| Path | `required_vl` | Declared level | Result |\n"
        "|------|---------------|----------------|--------|\n"
        "| PATH-001 | VL-2 | VL-1 | BLOCKED |\n\n"
        "## 7. Honesty declaration\n"
        "- VALIDATED (VL-2, `mock+real`, actual Real HW HAL tests): none.\n"
    )
    for cycle in ("01_demo", "01_demo_retry"):
        run = f"{cycle}_1_2026-11-19_09-30-10-125"
        folder = root / "verification/telemetry/remote/fetch-abc" / run
        folder.mkdir(parents=True)
        (folder / f"{run}.jsonl").write_text('{"process":{"cpu_percent":1}}\n')
        (folder / "pytest_vl1.txt").write_text(cycle)
        (folder / "measurement.json").write_text(json.dumps({
            "schema_version": 2, "cycle": cycle, "stage": "G3", "iteration": 1,
            "run_id": run, "target": "local", "command": "verification/run.sh vl1",
            "started_at": "2026-11-19T09:30:10Z", "finished_at": "2026-11-19T09:30:11Z",
            "exit_code": 0, "measurements": [{
                "requirement_id": "SYS-001", "metric": "latency", "value": 4, "unit": "ms",
                "criterion": "at most 3 ms", "result": "fail",
            }],
        }))

    evidence = read_evidence(root)
    assert evidence["vl2"]["statement"].endswith("actual Real HW HAL tests): none.")
    assert [(row["id"], row["result"]) for row in evidence["vl2"]["items"]] == [("PATH-001", "BLOCKED")]
    for cycle in ("01_demo", "01_demo_retry"):
        evidence = read_evidence(root, cycle=cycle)
        sample, = evidence["telemetry"]
        assert sample["run_id"].startswith(f"{cycle}_1_")
        assert sample["sample_count"] == 1
        log, = evidence["test_logs"]
        assert read_artifact(root, None, log["path"])["content"] == cycle
        measurement, = evidence["measurements"]
        assert measurement["record"]["cycle"] == cycle
        assert measurement["record"]["measurements"][0]["result"] == "fail"


def test_active_cycle_exists_before_its_first_report(tmp_path):
    root = project(tmp_path)
    result = read_overview(root)
    assert result["cycles"] == [{
        "name": "01_demo", "active": True, "closed": False,
        "superseded_by": None, "draft": False, "suspended": False,
    }]
    assert all(row["state"] == "missing" for row in result["reports"])


def test_evidence_limits_apply_after_cycle_selection(tmp_path, monkeypatch):
    root = project(tmp_path)
    report(root, "S0")
    base = root / "verification/telemetry"
    other = base / "01_demo_retry_1_2026-11-19_09-30-10-125"
    other.mkdir(parents=True)
    for number in range(200):
        (other / f"{number}.jsonl").write_text("{}\n")
    selected = base / "01_demo_1_2026-11-19_09-30-10-125"
    selected.mkdir()
    log = selected / "pytest_vl1.txt"
    log.write_text("selected")
    original = Path.rglob

    def ordered_rglob(path, pattern):
        return iter(sorted(original(path, pattern), key=lambda item: item.parent != other))

    monkeypatch.setattr(Path, "rglob", ordered_rglob)
    assert [entry["path"] for entry in read_evidence(root)["test_logs"]] == [log.relative_to(root).as_posix()]


def test_direct_telemetry_artifact_read_has_same_file_limit(tmp_path):
    root = project(tmp_path)
    path = root / "verification/telemetry/01_demo_1_2026-11-19_09-30-10-125/pytest_vl1.txt"
    path.parent.mkdir(parents=True)
    with path.open("wb") as stream:
        stream.truncate(5 * 1024 * 1024 + 1)
    assert not read_evidence(root)["test_logs"]
    with pytest.raises(HTTPException) as error:
        read_artifact(root, None, path.relative_to(root).as_posix())
    assert error.value.status_code == 413


def test_partial_latest_iteration_blocks_completion(tmp_path):
    root = project(tmp_path)
    for stage in ORDER:
        report(root, stage)
    report(root, "G3", "## Iteration 1\n| HITL | PASS |\n## Iteration 2\nBased on: S3 iteration 1\n")
    artifact = root / ".codeanvil/report/01_demo/G3_artifacts/verified_prototype.md"
    artifact.parent.mkdir()
    artifact.write_text("# Previous prototype")
    result = read_overview(root)
    assert result["reports"][-1]["state"] == "UNKNOWN"
    assert result["completion"]["passed"] == 7
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
    prototype = root / ".codeanvil/report/01_demo/G3_artifacts/verified_prototype.md"
    prototype.parent.mkdir()
    prototype.write_text("# Prior prototype")
    if blocker == "draft":
        (prototype.parent.parent / "DRAFT").write_text("Review pending")
    elif blocker == "suspended":
        report(root, "RFD", "## Iteration 1\n| HITL | FEEDBACK |\n")
    else:
        report(root, "RFD", "## Iteration 1\n| HITL | PASS |\nSuperseded by cycle: 02_new\n")
    result = read_overview(root)
    assert result["completion"]["passed"] == 8
    assert result["cycles"][0][blocker]
    assert not result["completion"]["complete"]


def test_prototype_baseline_must_match_current_s3_and_g3_iterations(tmp_path):
    root = project(tmp_path)
    for stage in ORDER:
        report(root, stage)
    prototype = root / ".codeanvil/report/01_demo/G3_artifacts/verified_prototype.md"
    prototype.parent.mkdir()
    prototype.write_text("# Prototype\n## 1. Cycle\n| Based on | S3 iteration 1, G3 iteration 1 |\n")
    assert read_overview(root)["completion"]["complete"]
    g3 = root / ".codeanvil/report/01_demo/G3.md"
    g3.write_text(g3.read_text() + "## Iteration 2\n| HITL | PASS |\nBased on: S3 iteration 1\n")
    result = read_overview(root)
    assert result["completion"]["passed"] == 8
    assert not result["completion"]["complete"]
    assert "Verified Prototype is stale" in result["completion"]["reason"]
    assert next(item for item in result["artifacts"] if item["kind"] == "prototype")["exists"]
    prototype.write_text("# Prototype\n## 1. Cycle\n| Based on | S3 iteration 1, G3 iteration 2 |\n")
    assert read_overview(root)["completion"]["complete"]


@pytest.mark.parametrize("content", [
    "# Prototype without baseline",
    "## 1. Cycle\n| Based on | Unknown |\n",
    "## 1. Cycle\n~~~markdown\n| Based on | S3 iteration 1, G3 iteration 1 |\n~~~\n",
])
def test_unknown_or_fenced_prototype_baseline_is_not_current(tmp_path, content):
    root = project(tmp_path)
    for stage in ORDER:
        report(root, stage)
    prototype = root / ".codeanvil/report/01_demo/G3_artifacts/verified_prototype.md"
    prototype.parent.mkdir()
    prototype.write_text(content)
    result = read_overview(root)
    assert not result["completion"]["complete"]
    assert "baseline is missing or malformed" in result["completion"]["reason"]


def test_fenced_rfd_instruction_does_not_suspend_cycle(tmp_path):
    root = project(tmp_path)
    report(root, "G1", "## Iteration 1\n| HITL | PASS |\n### Description\n~~~text\nVerdict: RFD\n~~~\n")
    assert not read_overview(root)["cycles"][0]["suspended"]


def test_both_graph_variants_use_the_local_library_and_report_actual_presence(tmp_path):
    root = project(tmp_path)
    design = root / ".codeanvil/design"
    design.mkdir()
    library = root / ".agents/skills/S1_design_system/assets/vis-network.min.js"
    library.parent.mkdir(parents=True)
    library.write_text("window.graphLibrary = true;")
    graphs = ("dependency_graph.html", "dependency_graph_light.html")
    (design / graphs[0]).write_text('<script src="../../.agents/skills/S1_design_system/assets/vis-network.min.js"></script>')
    inventory = {item["graph_theme"]: item for item in read_overview(root)["artifacts"] if "graph_theme" in item}
    assert inventory["dark"]["exists"]
    assert not inventory["light"]["exists"]
    (design / graphs[1]).write_text((design / graphs[0]).read_text())
    for name in graphs:
        result = read_artifact(root, None, f".codeanvil/design/{name}")
        assert result["format"] == "html"
        assert "<script>window.graphLibrary = true;</script>" in result["content"]
        assert '<script src=' not in result["content"]
    inventory = [item for item in read_overview(root)["artifacts"] if "graph_theme" in item]
    assert all(item["exists"] for item in inventory)


def test_light_graph_cannot_escape_through_a_symlink(tmp_path):
    root = project(tmp_path)
    design = root / ".codeanvil/design"
    design.mkdir()
    outside = tmp_path / "outside.html"
    outside.write_text("Outside the project")
    (design / "dependency_graph_light.html").symlink_to(outside)
    with pytest.raises(HTTPException) as error:
        read_artifact(root, None, ".codeanvil/design/dependency_graph_light.html")
    assert error.value.status_code == 400


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


@pytest.mark.parametrize("path", ["../.env", "/etc/passwd", ".codeanvil/project.yaml", ".codeanvil/report/01_demo/../S0.md",
                                 ".codeanvil/report/01_demo/S2_artifacts/test_run.md",
                                 ".codeanvil/report/01_demo/G2_artifacts/verified_prototype.md",
                                 ".codeanvil/design/custom.html", ".codeanvil/design/dependency_graph_dark.html"])
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
    path = root / ".codeanvil/report/01_demo/S3_artifacts/test_run.md"
    path.parent.mkdir(parents=True)
    path.symlink_to(outside)
    with pytest.raises(HTTPException) as error:
        read_artifact(root, None, ".codeanvil/report/01_demo/S3_artifacts/test_run.md")
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

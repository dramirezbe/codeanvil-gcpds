"""`codeanvil backup <stage>` — producer resolution, idempotency, MANIFEST."""

import hashlib

import pytest
import yaml

from codeanvil.CLI.commands.backup import cmd_backup
from codeanvil.config.paths import PROJECT_BACKUPS, PROJECT_MANIFEST


def _make_project(tmp_path, cycle="01_run"):
    project = tmp_path / "proj"
    manifest = project / PROJECT_MANIFEST
    manifest.parent.mkdir(parents=True)
    data = {"id": "0199a000-0000-7000-8000-000000000000", "name": "Proj"}
    if cycle is not None:
        data["cycle"] = cycle
    manifest.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return project


def _write_report(project, cycle, gate, iterations):
    """Each iteration is (number, hitl) or (number, hitl, description)."""
    report_dir = project / ".codeanvil" / "report" / cycle
    report_dir.mkdir(parents=True, exist_ok=True)
    sections = []
    for number, hitl, *rest in iterations:
        description = rest[0] if rest else "N/A"
        sections.append(
            f"## Iteration {number}\n\n"
            "| Field       | Value |\n"
            "|-------------|-------|\n"
            f"| Iteration   | {number} |\n"
            f"| HITL        | {hitl} |\n\n"
            f"### Description\n\n{description}\n"
        )
    (report_dir / f"{gate}.md").write_text(
        f"# {gate}\n\n" + "\n---\n\n".join(sections), encoding="utf-8"
    )


def _design(project):
    design = project / ".codeanvil" / "design"
    design.mkdir(parents=True)
    (design / "SDD.md").write_text("# SDD\n", encoding="utf-8")
    (design / "dependency_graph.html").write_text("<html></html>\n", encoding="utf-8")
    return design


def _manifest(folder):
    return yaml.safe_load((folder / "MANIFEST.yaml").read_text(encoding="utf-8"))


class _ErrorLog:
    """Stands in for the module logger so tests read the diagnostic verbatim."""

    def __init__(self):
        self.errors = []

    def error(self, message, *args):
        self.errors.append(message % args)


def _capture_errors(monkeypatch):
    log = _ErrorLog()
    monkeypatch.setattr("codeanvil.CLI.commands.backup.log", log)
    return log


def test_backup_uses_the_active_cycle_and_writes_the_manifest(tmp_path, monkeypatch, capsys):
    project = _make_project(tmp_path)
    monkeypatch.chdir(project)
    _write_report(project, "01_run", "S1", [(1, "PASS"), (2, "PASS")])
    _design(project)

    cmd_backup("S1")

    folder = project / PROJECT_BACKUPS / "01_run" / "S1_iter2"
    assert capsys.readouterr().out.strip() == (
        "Backed up S1 iteration 2 → .codeanvil/backups/01_run/S1_iter2/"
    )
    assert sorted(path.name for path in folder.iterdir()) == [
        "MANIFEST.yaml", "SDD.md", "dependency_graph.html",
    ]
    data = _manifest(folder)
    assert data["producer"] == {"cycle": "01_run", "stage": "S1", "iteration": 2}
    assert data["active_cycle"] == "01_run"
    assert data["created"]
    digests = {entry["source"]: entry["sha256"] for entry in data["files"]}
    assert digests == {
        ".codeanvil/design/SDD.md": hashlib.sha256(
            (project / ".codeanvil/design/SDD.md").read_bytes()
        ).hexdigest(),
        ".codeanvil/design/dependency_graph.html": hashlib.sha256(
            (project / ".codeanvil/design/dependency_graph.html").read_bytes()
        ).hexdigest(),
    }


def test_backup_follows_the_rfd_supersede_chain(tmp_path, monkeypatch, capsys):
    """A new cycle overwrites the design of the cycle its RFD superseded."""
    project = _make_project(tmp_path, cycle="02_new")
    monkeypatch.chdir(project)
    _write_report(project, "01_old", "S1", [(1, "PASS")])
    _write_report(project, "01_old", "RFD", [(1, "PASS", "Superseded by cycle: 02_new")])
    _design(project)

    cmd_backup("S1")

    assert "01_old/S1_iter1" in capsys.readouterr().out
    assert (project / PROJECT_BACKUPS / "01_old" / "S1_iter1" / "SDD.md").is_file()


def test_backup_falls_back_to_unknown_without_a_producer(tmp_path, monkeypatch, capsys):
    project = _make_project(tmp_path)
    monkeypatch.chdir(project)
    _design(project)

    cmd_backup("S1")

    [folder] = list((project / PROJECT_BACKUPS / "unknown").iterdir())
    assert folder.name.startswith("S1_")
    assert f".codeanvil/backups/unknown/{folder.name}/" in capsys.readouterr().out
    assert _manifest(folder)["producer"] == {
        "cycle": "unknown", "stage": "S1", "iteration": "unknown",
    }


def test_backup_is_idempotent_for_unchanged_files(tmp_path, monkeypatch, capsys):
    project = _make_project(tmp_path)
    monkeypatch.chdir(project)
    _write_report(project, "01_run", "S1", [(1, "PASS")])
    _design(project)
    cmd_backup("S1")
    capsys.readouterr()

    cmd_backup("S1")

    assert capsys.readouterr().out.strip() == (
        "already backed up: .codeanvil/backups/01_run/S1_iter1/"
    )
    assert len(list((project / PROJECT_BACKUPS / "01_run").iterdir())) == 1


def test_backup_prints_nothing_to_back_up_when_no_target_exists(tmp_path, monkeypatch, capsys):
    project = _make_project(tmp_path)
    monkeypatch.chdir(project)
    _write_report(project, "01_run", "S1", [(1, "PASS")])

    cmd_backup("S1")

    assert capsys.readouterr().out.strip() == "nothing to back up"
    assert not (project / PROJECT_BACKUPS).exists()


def test_backup_keeps_the_folder_when_an_interrupted_pass_resumes(
    tmp_path, monkeypatch, capsys
):
    """A pass that backed up, rewrote the design and died before its iteration
    re-runs with the same producer: the folder already holds that iteration's
    files, so the command keeps it, never overwrites it, and lets the pass go on."""
    project = _make_project(tmp_path)
    monkeypatch.chdir(project)
    _write_report(project, "01_run", "S1", [(1, "PASS")])
    design = _design(project)
    cmd_backup("S1")
    (design / "SDD.md").write_text("# SDD half rewritten by the interrupted pass\n", encoding="utf-8")
    capsys.readouterr()

    cmd_backup("S1")

    out = capsys.readouterr().out
    assert "already backed up: .codeanvil/backups/01_run/S1_iter1/" in out
    assert "resuming an interrupted pass" in out
    assert (project / PROJECT_BACKUPS / "01_run" / "S1_iter1" / "SDD.md").read_text(
        encoding="utf-8"
    ) == "# SDD\n"


def test_backup_refuses_a_cycle_named_like_the_unknown_bucket(tmp_path, monkeypatch):
    log = _capture_errors(monkeypatch)
    project = _make_project(tmp_path, cycle="unknown")
    monkeypatch.chdir(project)
    _design(project)

    with pytest.raises(SystemExit) as exc:
        cmd_backup("S1")

    assert exc.value.code == 1
    assert "reserved" in log.errors[0]
    assert not (project / PROJECT_BACKUPS).exists()


def test_backup_expands_the_active_cycle_for_s2(tmp_path, monkeypatch, capsys):
    project = _make_project(tmp_path, cycle="01_run")
    monkeypatch.chdir(project)
    _write_report(project, "01_run", "S2", [(1, "PASS")])
    artifact = project / ".codeanvil/report/01_run/S2_artifacts/test_run.md"
    artifact.parent.mkdir(parents=True)
    artifact.write_text("# run\n", encoding="utf-8")

    cmd_backup("S2")

    folder = project / PROJECT_BACKUPS / "01_run" / "S2_iter1"
    assert (folder / "test_run.md").read_text(encoding="utf-8") == "# run\n"
    assert "S2_iter1" in capsys.readouterr().out


def test_backup_requires_an_active_cycle_for_s2(tmp_path, monkeypatch):
    log = _capture_errors(monkeypatch)
    project = _make_project(tmp_path, cycle=None)
    monkeypatch.chdir(project)

    with pytest.raises(SystemExit) as exc:
        cmd_backup("S2")

    assert exc.value.code == 1
    assert "no active cycle" in log.errors[0]


def test_backup_requires_a_project_manifest(tmp_path, monkeypatch):
    log = _capture_errors(monkeypatch)
    monkeypatch.chdir(tmp_path)

    with pytest.raises(SystemExit) as exc:
        cmd_backup("S1")

    assert exc.value.code == 1
    assert "no .codeanvil/project.yaml" in log.errors[0]


def test_backup_entries_never_mix_iteration_and_timestamp_orders(tmp_path):
    """An `unknown/` bucket that also holds an `_iter` folder (a cycle once named
    `unknown`) must not crash `status` with an int-versus-str comparison."""
    from codeanvil.reports import backup_entries

    unknown = tmp_path / "unknown"
    (unknown / "S1_iter1").mkdir(parents=True)
    (unknown / "S1_2026-11-06_14-10-00-123").mkdir()
    (tmp_path / "01_run" / "S1_iter2").mkdir(parents=True)

    entries = backup_entries(tmp_path)

    assert entries["unknown"] == [("S1", None, "unknown/S1_2026-11-06_14-10-00-123")]
    assert entries["01_run"] == [("S1", 2, "01_run/S1_iter2")]

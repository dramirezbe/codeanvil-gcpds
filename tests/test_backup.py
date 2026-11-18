"""`codeanvil backup <stage>` — producer resolution, idempotency, MANIFEST."""

import hashlib
import subprocess
import sys

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


def test_s1_backup_preserves_both_graph_themes_and_their_digests(tmp_path, monkeypatch):
    project = _make_project(tmp_path)
    monkeypatch.chdir(project)
    _write_report(project, "01_run", "S1", [(1, "PASS")])
    design = _design(project)
    (design / "dependency_graph.html").write_text("<html>Dark graph</html>\n", encoding="utf-8")
    (design / "dependency_graph_light.html").write_text("<html>Light graph</html>\n", encoding="utf-8")

    cmd_backup("S1")

    folder = project / PROJECT_BACKUPS / "01_run" / "S1_iter1"
    digests = {entry["source"]: entry["sha256"] for entry in _manifest(folder)["files"]}
    for name in ("dependency_graph.html", "dependency_graph_light.html"):
        original = (design / name).read_bytes()
        assert (folder / name).read_bytes() == original
        assert digests[f".codeanvil/design/{name}"] == hashlib.sha256(original).hexdigest()


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


def test_backup_expands_the_active_cycle_for_s3(tmp_path, monkeypatch, capsys):
    project = _make_project(tmp_path, cycle="01_run")
    monkeypatch.chdir(project)
    _write_report(project, "01_run", "S3", [(1, "PASS")])
    artifact = project / ".codeanvil/report/01_run/S3_artifacts/test_run.md"
    artifact.parent.mkdir(parents=True)
    artifact.write_text("# run\n", encoding="utf-8")

    cmd_backup("S3")

    folder = project / PROJECT_BACKUPS / "01_run" / "S3_iter1"
    assert (folder / "test_run.md").read_text(encoding="utf-8") == "# run\n"
    assert "S3_iter1" in capsys.readouterr().out


def test_backup_requires_an_active_cycle_for_s3(tmp_path, monkeypatch):
    log = _capture_errors(monkeypatch)
    project = _make_project(tmp_path, cycle=None)
    monkeypatch.chdir(project)

    with pytest.raises(SystemExit) as exc:
        cmd_backup("S3")

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


def test_s2_backups_preserve_distinct_nested_plan_paths(tmp_path, monkeypatch, capsys):
    project = _make_project(tmp_path)
    monkeypatch.chdir(project)
    _write_report(project, '01_run', 'S2', [(6, 'PASS')])
    contents = {
        '.codeanvil/plans/BACKLOG.md': 'backlog',
        '.codeanvil/plans/INFRA-PLAN.md': 'infra',
        '.codeanvil/plans/DELTAS.md': 'deltas',
        '.codeanvil/plans/SUB-001/capture/PLAN.md': 'capture plan',
        '.codeanvil/plans/SUB-002/receive/PLAN.md': 'receive plan',
    }
    for name, content in contents.items():
        path = project / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
    cmd_backup('S2')
    assert 'Backed up S2 iteration 6' in capsys.readouterr().out
    folder = project / PROJECT_BACKUPS / '01_run/S2_iter6'
    manifest = _manifest(folder)
    assert {entry['source'] for entry in manifest['files']} == set(contents)
    for entry in manifest['files']:
        assert entry['backup_path'] == entry['source']
        saved = folder / entry['backup_path']
        assert saved.read_text() == contents[entry['source']]
        assert entry['sha256'] == hashlib.sha256(saved.read_bytes()).hexdigest()
    original = {p.relative_to(folder): p.read_bytes() for p in folder.rglob('*') if p.is_file()}
    (project / '.codeanvil/plans/SUB-001/capture/PLAN.md').write_text('partial rework')
    cmd_backup('S2')
    assert 'resuming an interrupted pass' in capsys.readouterr().out
    assert original == {p.relative_to(folder): p.read_bytes() for p in folder.rglob('*') if p.is_file()}


@pytest.mark.parametrize('exists', [False, True])
def test_missing_or_empty_s2_plan_directory_is_success(tmp_path, monkeypatch, capsys, exists):
    project = _make_project(tmp_path)
    monkeypatch.chdir(project)
    if exists:
        (project / '.codeanvil/plans').mkdir()
    cmd_backup('S2')
    assert capsys.readouterr().out.strip() == 'nothing to back up'
    assert not (project / PROJECT_BACKUPS).exists()


def test_failed_directory_copy_never_publishes_a_completed_backup(tmp_path, monkeypatch):
    project = _make_project(tmp_path)
    monkeypatch.chdir(project)
    _write_report(project, '01_run', 'S2', [(1, 'PASS')])
    path = project / '.codeanvil/plans/SUB-001/a/PLAN.md'
    path.parent.mkdir(parents=True)
    path.write_text('original')
    def fail(*args, **kwargs):
        raise OSError('simulated full disk')
    monkeypatch.setattr('codeanvil.CLI.commands.backup.shutil.copy2', fail)
    with pytest.raises(SystemExit) as exc:
        cmd_backup('S2')
    assert exc.value.code == 1
    assert not (project / PROJECT_BACKUPS / '01_run/S2_iter1').exists()
    assert path.read_text() == 'original'


def test_backup_cli_copies_the_s2_directory_tree(tmp_path):
    project = _make_project(tmp_path)
    _write_report(project, '01_run', 'S2', [(1, 'PASS')])
    for module in ['a', 'b']:
        plan = project / f'.codeanvil/plans/SUB-001/{module}/PLAN.md'
        plan.parent.mkdir(parents=True)
        plan.write_text(module)
    result = subprocess.run(
        [sys.executable, '-c', 'from codeanvil.CLI.main import main; main()', 'backup', 'S2'],
        cwd=project, capture_output=True, text=True,
    )
    assert result.returncode == 0
    assert 'Backed up S2 iteration 1' in result.stdout
    folder = project / PROJECT_BACKUPS / '01_run/S2_iter1'
    for module in ['a', 'b']:
        assert (folder / f'.codeanvil/plans/SUB-001/{module}/PLAN.md').read_text() == module

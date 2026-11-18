from pathlib import Path
import subprocess

import pytest

from codeanvil.custody import file_sha256, tree_sha256, verify, verify_manifest
from codeanvil.reports import ReportState, authorized_advance, next_step, stale_reason


def delta(before, after, **kwargs):
    return {"Document": "GT.md", "Before sha256": before, "After sha256": after,
            "Status": "applied", "Interface impact": "none", "Authority": "author",
            "Applied in": "S0 iteration 2", **kwargs}


def test_authorized_chains_and_rejected_changes():
    a, b, c = (n * 64 for n in "abc")
    assert authorized_advance("GT.md", a, c, [delta(b, c), delta(a, b)])
    assert not authorized_advance("GT.md", a, c, [delta(b, c)])
    for field, value in [("Status", "accepted"), ("Interface impact", "contract.v2"),
                         ("Authority", ""), ("Applied in", "")]:
        assert not authorized_advance("GT.md", a, b, [delta(a, b, **{field: value})])


def test_latest_inputs_only_and_delta_sync(tmp_path):
    (tmp_path / "GT.md").write_text("before")
    before = file_sha256(tmp_path / "GT.md")
    reports = tmp_path / ".codeanvil/report/c"
    reports.mkdir(parents=True)
    (tmp_path / ".codeanvil/project.yaml").write_text("cycle: c\n")
    (reports / "S0.md").write_text(f"## Iteration 1\n| HITL | PASS |\n### Description\nInput: GT.md sha256:{before}\n")
    assert verify(tmp_path) == []
    (tmp_path / "GT.md").write_text("after")
    after = file_sha256(tmp_path / "GT.md")
    assert verify(tmp_path)[0].kind == "stale-report"
    plans = tmp_path / ".codeanvil/plans"
    plans.mkdir()
    (plans / "DELTAS.md").write_text(
        "| Document | Before sha256 | After sha256 | Status | Interface impact | Authority | Applied in |\n"
        "|---|---|---|---|---|---|---|\n"
        f"| GT.md | {before} | {after} | applied | none | author | S0 iteration 2 |\n")
    assert verify(tmp_path) == []
    gates = {"S0": ReportState(2, "PASS", scope="delta-sync"),
             "G0": ReportState(1, "PASS", ("S0", 1), inputs=(("GT.md", before),))}
    assert stale_reason("G0", gates, project_root=tmp_path) is None
    (tmp_path / "GT.md").write_text("unapproved")
    assert "stale-report" in stale_reason("G0", gates, project_root=tmp_path)


def test_entry_stage_input_staleness_without_based_on(tmp_path):
    gates = {"S0": ReportState(1, "PASS", inputs=(("missing", "a" * 64),))}
    assert "missing" in stale_reason("S0", gates, project_root=tmp_path)


def test_tree_tracks_ignored_files_and_modifications(tmp_path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    (tmp_path / ".gitignore").write_text("ignored/\n")
    source = tmp_path / "src"
    source.mkdir()
    (source / "a.py").write_text("first")
    before = tree_sha256(source)
    (tmp_path / "ignored").mkdir()
    (tmp_path / "ignored/log").write_text("noise")
    assert tree_sha256(source) == before
    (source / "a.py").write_text("changed")
    assert tree_sha256(source) != before


def test_manifest_missing_tampered_unlisted_and_duplicate(tmp_path):
    manifest = tmp_path / "manifest.md"
    assert verify_manifest(manifest)
    vector = tmp_path / "v.bin"
    vector.write_bytes(b"vector")
    row = f"| V1 | {file_sha256(vector)} | v.bin |\n"
    header = "| Vector ID | SHA-256 | File |\n|---|---|---|\n"
    manifest.write_text(header + row)
    assert verify_manifest(manifest) == []
    vector.write_bytes(b"tamper")
    assert verify_manifest(manifest)
    manifest.write_text(header + row + row)
    assert any(f.current == "unsafe or duplicate path" for f in verify_manifest(manifest))
    manifest.write_text(header)
    assert any(f.current == "unlisted" for f in verify_manifest(manifest))


def test_new_slice_next_gate_does_not_reuse_old_gate():
    gates = {g: ReportState(1, "PASS", (p, 1) if p else None, scope="slice 0")
             for p, g in zip([None, "S0", "G0", "S1", "G1", "S2", "G2", "S3"],
                             ["S0", "G0", "S1", "G1", "S2", "G2", "S3", "G3"])}
    assert next_step(gates).startswith("S2 slice 1")
    gates["S2"] = ReportState(2, "PASS", ("G1", 1), scope="slice 1")
    assert next_step(gates) == "G2 slice 1"


def test_custody_cli_propagates_failure_exit_code(tmp_path):
    import sys
    result = subprocess.run([sys.executable, '-c',
                             'from codeanvil.CLI.main import main; main()',
                             'custody', 'verify-manifest', str(tmp_path / 'missing.md')],
                            capture_output=True, text=True)
    assert result.returncode == 1
    assert 'manifest-mismatch' in result.stdout


def test_routing_and_pending_sync(tmp_path):
    assert next_step({'S0': ReportState(1, 'FEEDBACK', verdict='GT defect')}) == 'S0'
    plans = tmp_path / '.codeanvil/plans'
    plans.mkdir(parents=True)
    (plans / 'DELTAS.md').write_text('| Document | Before sha256 | Type | Status |\n'
                                    '|---|---|---|---|\n| GT.md | abc | design-sync | accepted |\n')
    assert next_step({'S0': ReportState(1, 'PASS')}, project_root=tmp_path) == 'S1 delta-sync'

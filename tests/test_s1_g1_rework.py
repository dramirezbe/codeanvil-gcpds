"""Synthetic rework evidence: no human verdicts or user-project files are changed."""
import subprocess
import sys

import pytest

from codeanvil.custody import path_sha256, verify
from codeanvil.reports import cycle_reports, next_step, report_state, stale_reason


@pytest.fixture
def rework(tmp_path):
    reports = tmp_path / '.codeanvil/report/c'
    reports.mkdir(parents=True)
    (tmp_path / '.codeanvil/project.yaml').write_text('cycle: c\n')
    gt = tmp_path / 'GT.md'
    gt.write_text('mock-only, maximum VL-1')
    design = tmp_path / '.codeanvil/design/SDD.md'
    design.parent.mkdir()
    design.write_text('initial design')

    def append(gate, n, predecessor=None, verdict='PASS', extra=''):
        text = f'## Iteration {n}\n| HITL | {verdict} |\n### Description\n'
        if predecessor:
            text += f'Based on: {predecessor}\n'
        if gate in {'G0', 'S1', 'G1'}:
            text += f'Input: GT.md sha256:{path_sha256(gt)}\n'
        if gate == 'S1':
            text += f'Output: .codeanvil/design/SDD.md sha256:{path_sha256(design)}\n'
        if gate == 'G1':
            text += f'Input: .codeanvil/design/SDD.md sha256:{path_sha256(design)}\n'
        with (reports / f'{gate}.md').open('a') as stream:
            stream.write(text + extra)

    append('S0', 1)
    append('G0', 1, 'S0 iteration 1')
    append('S1', 1, 'G0 iteration 1')
    append('G1', 1, 'S1 iteration 1', 'FEEDBACK')
    return tmp_path, reports, design, append


def states(root):
    return cycle_reports(root / '.codeanvil/report')['c']


def test_feedback_rework_reopens_review_and_preserves_history(rework):
    root, reports, design, append = rework
    assert next_step(states(root), root) == 'S1'
    history = (reports / 'G1.md').read_bytes()
    for n in (2, 3):
        design.write_text(f'reworked design {n}')
        append('S1', n, 'G0 iteration 1', extra=f'Rework from: G1 iteration {n-1}\n')
        gates = states(root)
        assert stale_reason('S1', gates, project_root=root) is None
        assert stale_reason('G1', gates, project_root=root)
        assert gates['S1'].rework_from == ('G1', n-1)
        assert next_step(gates, root) == 'G1'
        append('G1', n, f'S1 iteration {n}', 'FEEDBACK' if n == 2 else 'PASS')
    assert (reports / 'G1.md').read_bytes().startswith(history)
    assert next_step(states(root), root) == 'S2 slice 0'


def test_invalid_s1_feedback_baseline_is_diagnosed_not_followed(rework):
    root, _, _, append = rework
    append('S1', 2, 'G1 iteration 1')
    reason = stale_reason('S1', states(root), project_root=root)
    assert reason == 'invalid-baseline: S1 must be based on G0, found G1'
    assert next_step(states(root), root) == 'S1'
    assert verify(root, 'c', 'S1')[0].kind == 'invalid-baseline'


def test_rework_source_is_metadata_not_an_upstream_dependency(rework):
    root, reports, design, append = rework
    design.write_text('fixed')
    append('S1', 2, 'G0 iteration 1', extra='Rework from: G1 iteration 1\n')
    state = report_state(reports / 'S1.md')
    assert state.based_on == ('G0', 1)
    assert state.rework_from == ('G1', 1)
    assert stale_reason('S1', states(root), project_root=root) is None
    assert next_step(states(root), root) == 'G1'


@pytest.mark.parametrize('boundary', ['GT drift', 'RFD', 'partial delivery'])
def test_new_delivery_does_not_bypass_real_blockers(rework, boundary):
    root, reports, design, append = rework
    design.write_text('fixed')
    append('S1', 2, 'G0 iteration 1')
    if boundary == 'GT drift':
        (root / 'GT.md').write_text('unreviewed GT change')
        expected = 'G0'
    elif boundary == 'RFD':
        append('G1', 2, 'S1 iteration 1', 'FEEDBACK', 'Verdict: RFD\n')
        expected = 'RFD'
    else:
        with (reports / 'S1.md').open('a') as stream:
            stream.write('## Iteration 3\nWork in progress\n')
        expected = 'S1'
    assert next_step(states(root), root) == expected


def test_rework_source_ignores_fenced_examples(rework):
    _, reports, _, append = rework
    append('S1', 2, 'G0 iteration 1', extra='```\nRework from: G1 iteration 99\n```\n')
    assert report_state(reports / 'S1.md').rework_from is None


@pytest.mark.parametrize('change', ['edit', 'delete'])
def test_working_design_is_not_delivered_until_s1_report_matches(rework, change):
    root, _, design, append = rework
    if change == 'edit':
        design.write_text('unfinished rework')
    else:
        design.unlink()
    finding, = verify(root, 'c', 'S1')
    assert finding.kind == 'undelivered-output'
    assert finding.path == '.codeanvil/design/SDD.md'
    assert 'undelivered-output' in stale_reason('S1', states(root), project_root=root)
    assert next_step(states(root), root) == 'S1'
    result = subprocess.run(
        [sys.executable, '-c', 'from codeanvil.CLI.main import main; main()',
         'custody', 'verify', '--cycle', 'c', '--gate', 'S1'],
        cwd=root, capture_output=True, text=True,
    )
    assert result.returncode == 1
    assert 'undelivered-output: .codeanvil/design/SDD.md' in result.stdout
    design.write_text('complete rework')
    append('S1', 2, 'G0 iteration 1', extra='Rework from: G1 iteration 1\n')
    assert verify(root, 'c', 'S1') == []
    assert next_step(states(root), root) == 'G1'


def test_latest_s1_outputs_only_and_no_global_s3_output_checks(rework):
    root, reports, design, append = rework
    design.write_text('new complete delivery')
    append('S1', 2, 'G0 iteration 1')
    # An overwritten historical S1 output and an old implementation tree are legitimate.
    append('S3', 1, extra=f'Output: src/ sha256:{"0" * 64}\n')
    with (reports / 'S1.md').open('a') as stream:
        stream.write(f'```\nOutput: absent.md sha256:{"0" * 64}\n```\n')
    assert verify(root, 'c', 'S1') == []
    assert verify(root, 'c', 'S3') == []
    # The old G1 still records its actual consumed design and remains stale.
    assert {f.kind for f in verify(root, 'c', 'G1')} == {'stale-report'}


def test_status_exposes_pending_delivery_then_routes_to_new_review(rework, monkeypatch, capsys):
    from codeanvil.CLI.commands.status import cmd_status
    from codeanvil.db.projects import register_project
    from codeanvil.db.schema import create_schema
    from codeanvil.db.utils import connect_db

    root, _, design, append = rework
    (root / '.codeanvil/project.yaml').write_text('id: test-rework\nname: Rework\ncycle: c\n')
    database = root / 'isolated.db'
    connection = connect_db(database)
    create_schema(connection)
    register_project(connection, 'test-rework', 'Rework', root)
    connection.close()
    monkeypatch.setattr('codeanvil.CLI.commands.status.DB_PATH', database)
    design.write_text('unfinished rework')
    cmd_status('Rework')
    output = capsys.readouterr().out
    assert 'undelivered-output: .codeanvil/design/SDD.md' in output
    assert 'Next: S1' in output
    append('S1', 2, 'G0 iteration 1')
    cmd_status('Rework')
    output = capsys.readouterr().out
    assert 'S1: delivered (iteration 2)' in output
    assert 'Next: G1' in output

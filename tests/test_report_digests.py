"""Fail closed on malformed digest declarations in the latest report iteration."""
import subprocess
import sys

import pytest

from codeanvil.custody import path_sha256, verify
from codeanvil.reports import ReportState, next_step, report_state, scoped_report_state, stale_reason


@pytest.fixture
def delivery(tmp_path):
    report = tmp_path / '.codeanvil/report/c/S2.md'
    report.parent.mkdir(parents=True)
    (tmp_path / '.codeanvil/project.yaml').write_text('cycle: c\n')
    inputs = []
    for name in ['.codeanvil/design/SDD.md', '.codeanvil/GT/SyRS.md']:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(name)
        inputs.append(f'Input: {name} sha256:{path_sha256(path)}\n')
    text = ('## Iteration 1\n| HITL | PASS |\n### Description\n'
            'Based on: G1 iteration 1\nScope: slice 0\n' + ''.join(inputs))
    report.write_text(text)
    return tmp_path, report, text


def gates(report):
    return {'S0': ReportState(1, 'PASS'), 'G0': ReportState(1, 'PASS', ('S0', 1)),
            'S1': ReportState(1, 'PASS', ('G0', 1)), 'G1': ReportState(1, 'PASS', ('S1', 1)),
            'S2': report_state(report)}


@pytest.mark.parametrize('kind', ['Input', 'Output'])
@pytest.mark.parametrize('digest', ['a' * 62, 'a' * 65, 'g' * 64, 'A' * 64, '', '<hash>'])
def test_invalid_declared_digest_is_not_silently_dropped(delivery, kind, digest):
    root, report, text = delivery
    report.write_text(text + f'{kind}: bad.md sha256:{digest}\n')
    assert any(f.kind == 'invalid-report' for f in verify(root, 'c', 'S2'))
    assert f'malformed-{kind.lower()}' in stale_reason('S2', gates(report), project_root=root)
    assert next_step(gates(report), root) == 'S2'
    assert report_state(report).hitl == 'PASS'  # retain the actual recorded verdict


@pytest.mark.parametrize('missing', ['SDD.md', 'SyRS.md', 'both'])
def test_scoped_s2_requires_both_inputs(delivery, missing):
    root, report, text = delivery
    lines = [line for line in text.splitlines() if not
             (line.startswith('Input:') and (missing == 'both' or missing in line))]
    report.write_text('\n'.join(lines) + '\n')
    assert any('missing-input' in f.current for f in verify(root, 'c', 'S2'))
    assert next_step(gates(report), root) == 'S2'


def test_actual_62_character_regression_fails_at_cli_boundary(delivery):
    root, report, text = delivery
    line = next(line for line in text.splitlines() if line.startswith('Input: .codeanvil/design/'))
    report.write_text(text.replace(line, line[:-2]))
    result = subprocess.run(
        [sys.executable, '-c', 'from codeanvil.CLI.main import main; main()',
         'custody', 'verify', '--cycle', 'c', '--gate', 'S2'],
        cwd=root, capture_output=True, text=True,
    )
    assert result.returncode == 1
    assert 'invalid-report' in result.stdout and 'malformed-input' in result.stdout


def test_corrective_append_preserves_bad_history_and_reopens_g2(delivery):
    root, report, text = delivery
    bad = text + 'Output: bad.md sha256:short\n'
    report.write_text(bad)
    with report.open('a') as stream:
        stream.write(text.replace('Iteration 1', 'Iteration 2'))
    assert report.read_text().startswith(bad)
    assert verify(root, 'c', 'S2') == []
    assert next_step(gates(report), root) == 'G2 slice 0'
    assert not scoped_report_state(report, 'slice 0').format_errors


def test_fenced_examples_and_unscoped_legacy_are_not_required_inputs(delivery):
    root, report, text = delivery
    report.write_text(text + '~~~\nInput: example sha256:short\n~~~\n')
    assert verify(root, 'c', 'S2') == []
    report.write_text('## Iteration 1\n| HITL | PASS |\n')
    assert verify(root, 'c', 'S2') == []


def test_valid_wrong_digest_remains_a_stale_input_and_duplicates_block(delivery):
    root, report, text = delivery
    line = next(line for line in text.splitlines() if line.startswith('Input: .codeanvil/design/'))
    report.write_text(text.replace(line, line.split('sha256:')[0] + 'sha256:' + '0' * 64))
    assert verify(root, 'c', 'S2')[0].kind == 'stale-report'
    report.write_text(text + line + '\n')
    assert 'duplicate-input' in report_state(report).format_errors[0]
    assert next_step(gates(report), root) == 'S2'


def test_malformed_digest_in_other_gate_is_also_rejected(delivery):
    root, report, _ = delivery
    other = report.with_name('G2.md')
    other.write_text('## Iteration 1\n| HITL | PASS |\nInput: SDD.md sha256:short\n')
    assert verify(root, 'c', 'G2')[0].kind == 'invalid-report'


@pytest.mark.parametrize('prefix,separator', [('./', '/'), ('', '\\')])
def test_required_input_paths_accept_native_windows_and_relative_spelling(delivery, prefix, separator):
    _, report, text = delivery
    for path in ['.codeanvil/design/SDD.md', '.codeanvil/GT/SyRS.md']:
        text = text.replace(path, prefix + path.replace('/', separator))
    report.write_text(text)
    assert report_state(report).format_errors == ()

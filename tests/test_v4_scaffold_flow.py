"""Synthetic plumbing probe; these fixture PASS rows are never human acceptance evidence."""
import subprocess
import sys
from pathlib import Path

from codeanvil.config.paths import CONFIG
from codeanvil.custody import file_sha256, verify
from codeanvil.init.create import scaffold_project
from codeanvil.reports import cycle_reports, next_step


def test_generated_eight_node_flow_and_scoped_inputs(tmp_path):
    project = scaffold_project('V4 probe', 'probe', tmp_path)
    (project / '.codeanvil/project.yaml').write_text('cycle: probe\n')
    order = [s for s in CONFIG['report_order'] if s != 'RFD']
    assert order == ['S0', 'G0', 'S1', 'G1', 'S2', 'G2', 'S3', 'G3']
    for runtime, suffix in [('claude', 'md'), ('opencode', 'md'), ('codex', 'toml')]:
        for agent in ['vsil-verifier', 'vsil-implementor']:
            assert (project / f'.{runtime}/agents/{agent}.{suffix}').is_file()
    assert not (project / '.codeanvil/custody').exists()
    for name in ['PLAN.md', 'INFRA-PLAN.md', 'INTEGRATION-PLAN.md', 'DELTAS.md']:
        assert (project / '.agents/skills/S2_plan_modules/references' / name).is_file()
    source = project / 'baseline.txt'
    source.write_text('test fixture input')
    digest = file_sha256(source)
    reports = project / '.codeanvil/report/probe'
    reports.mkdir()
    for index, gate in enumerate(order):
        baseline = f'Based on: {order[index-1]} iteration 1\n' if index else ''
        scope = 'Scope: slice 0\n' if gate in order[4:] else ''
        (reports / f'{gate}.md').write_text(
            f'# Synthetic fixture {gate}\n## Iteration 1\n| HITL | PASS |\n### Description\n'
            f'{baseline}{scope}Input: baseline.txt sha256:{digest}\n')
        assert verify(project, 'probe') == []
    assert next_step(cycle_reports(project / '.codeanvil/report')['probe']).startswith('S2 slice 1')
    source.write_text('unapproved edit')
    assert len(verify(project, 'probe')) == 8
    # Exercise the installed console boundary, not only function calls.
    result = subprocess.run([sys.executable, '-c', 'from codeanvil.CLI.main import main; main()',
                             'custody', 'verify', '--cycle', 'probe'], cwd=project,
                            capture_output=True, text=True)
    assert result.returncode == 1
    assert 'stale-report' in result.stdout

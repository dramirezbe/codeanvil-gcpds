"""Synthetic contract transitions; no methodology, hardware or human gates are executed."""
from dataclasses import dataclass
from pathlib import Path

import pytest

from codeanvil.custody import path_sha256, verify
from codeanvil.reports import cycle_reports, next_step, report_state, scoped_report_state, stale_reason


@dataclass
class Fixture:
    root: Path

    def write(self, relative, text):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        return path

    def digest_lines(self, prefix, paths):
        return ''.join(f'{prefix}: {p} sha256:{path_sha256(self.root / p)}\n' for p in paths)

    def report(self, gate, n=1, pred=None, scope=None, hitl='PASS', inputs=(), outputs=(), extra=''):
        path = self.root / f'.codeanvil/report/c/{gate}.md'
        path.parent.mkdir(parents=True, exist_ok=True)
        text = f'## Iteration {n}\n| HITL | {hitl} |\n### Description\n'
        if pred:
            text += f'Based on: {pred[0]} iteration {pred[1]}\n'
        if scope:
            text += f'Scope: {scope}\n'
        text += self.digest_lines('Input', inputs) + self.digest_lines('Output', outputs) + extra
        with path.open('a') as stream:
            stream.write(text)

    def gates(self):
        return cycle_reports(self.root / '.codeanvil/report')['c']

    def next(self):
        return next_step(self.gates(), project_root=self.root)


@pytest.fixture
def flow(tmp_path):
    f = Fixture(tmp_path)
    f.write('.codeanvil/project.yaml', 'cycle: c\n')
    f.write('.codeanvil/GT/SyRS.md', 'GT baseline')
    f.write('.codeanvil/design/SDD.md', 'SDD baseline')
    f.report('S0', outputs=('.codeanvil/GT/SyRS.md',))
    f.report('G0', pred=('S0', 1), inputs=('.codeanvil/GT/SyRS.md',))
    f.report('S1', pred=('G0', 1), scope='system', inputs=('.codeanvil/GT/SyRS.md',), outputs=('.codeanvil/design/SDD.md',))
    f.report('G1', pred=('S1', 1), scope='system', inputs=('.codeanvil/GT/SyRS.md', '.codeanvil/design/SDD.md'))
    return f


def deliver_slice(f, n, scope, finish=True):
    plan = f'.codeanvil/plans/{scope.replace(" ", "-")}/PLAN.md'
    f.write(plan, f'Immutable approved {scope} plan')
    f.report('S2', n, ('G1', 1), scope, inputs=('.codeanvil/design/SDD.md', '.codeanvil/GT/SyRS.md'), outputs=(plan,))
    f.report('G2', n, ('S2', n), scope, inputs=(plan, '.codeanvil/design/SDD.md'))
    f.write('src/app.py', f'built through {scope}')
    f.write('verification/test_app.py', f'tests through {scope}')
    run = '.codeanvil/report/c/S3_artifacts/test_run.md'
    f.write(run, f'Scope: {scope}\nrecorded command for this scope')
    f.report('S3', n, ('G2', n), scope, inputs=(plan,), outputs=('src/', 'verification/', run),
             extra='Implementation notes: returned by the module implementor\n')
    if finish:
        f.report('G3', n, ('S3', n), scope, inputs=(plan, 'src/', 'verification/', run, '.codeanvil/design/SDD.md', '.codeanvil/GT/SyRS.md'))
    return plan


def test_first_delivery_does_not_inherit_s1_system_scope(flow):
    assert flow.next() == 'S2 slice 0'


def test_cadence_keeps_historical_g3_differences_out_of_current_prerequisite(flow):
    deliver_slice(flow, 1, 'slice 0')
    assert verify(flow.root, 'c') == []
    assert flow.next().startswith('S2 slice 1')
    plan = deliver_slice(flow, 2, 'slice 1', finish=False)
    assert flow.next() == 'G3 slice 1'
    # The previous G3's input tree really changed: diagnostics must retain this evidence.
    assert {v.path for v in verify(flow.root, 'c')} >= {'src/', 'verification/'}
    assert verify(flow.root, 'c', 'G2') == []
    assert verify(flow.root, 'c', 'S3') == []
    assert stale_reason('S3', flow.gates(), project_root=flow.root) is None
    # Notes in S3.md don't change the approved plan; a manual plan edit still blocks.
    assert 'Immutable approved' in (flow.root / plan).read_text()
    (flow.root / plan).write_text('unauthorized plan edit')
    assert verify(flow.root, 'c', 'G2')[0].path == plan
    assert verify(flow.root, 'c', 'S3')[0].path == plan


def test_scoped_history_never_reuses_pass_after_same_scope_feedback(flow):
    deliver_slice(flow, 1, 'slice 0')
    deliver_slice(flow, 2, 'slice 1')
    flow.report('G3', 3, ('S3', 2), 'slice 1', hitl='FEEDBACK',
                extra='Verdict: plan defect\nModules: SUB-001/a\n')
    path = flow.root / '.codeanvil/report/c/G3.md'
    assert scoped_report_state(path, 'slice 0').hitl == 'PASS'
    assert scoped_report_state(path, 'slice 1').hitl == 'FEEDBACK'
    assert scoped_report_state(path, 'slice 2').iteration is None
    assert flow.next() == 'S2'
    # Rework of the failed scope advances to G2 without requiring that scope's G3 PASS.
    flow.report('S2', 3, ('G1', 1), 'slice 1', inputs=('.codeanvil/design/SDD.md', '.codeanvil/GT/SyRS.md'))
    assert flow.next() == 'G2 slice 1'


def delta_table(f, status, before, after=''):
    return f.write('.codeanvil/plans/DELTAS.md',
                   '| ID | Type | Document | Status | Before sha256 | After sha256 | Interface impact | Authority | Applied in |\n'
                   '|---|---|---|---|---|---|---|---|---|\n'
                   f'| D-001 | design-sync | .codeanvil/design/SDD.md | {status} | {before} | {after} | none | reviewer | '
                   f'{"S1 iteration 2" if status == "applied" else ""} |\n')


def test_system_sync_feedback_closes_intake_apply_review_replan_loop(flow):
    plan = deliver_slice(flow, 1, 'system', finish=False)
    flow.report('G3', 1, ('S3', 1), 'system', hitl='FEEDBACK', inputs=(plan,),
                extra='Verdict: design defect\nSync-only: yes\nDelta accepted: D-001\n')
    assert flow.next() == 'S2 delta-intake'
    before = path_sha256(flow.root / '.codeanvil/design/SDD.md')
    # An existing proposed row is not yet a materialized human acceptance.
    delta_table(flow, 'proposed', before)
    assert flow.next() == 'S2 delta-intake'
    delta_table(flow, 'accepted', before)
    assert flow.next() == 'S1 delta-sync'
    flow.write('.codeanvil/design/SDD.md', 'authorized minor design change')
    after = path_sha256(flow.root / '.codeanvil/design/SDD.md')
    delta_table(flow, 'applied', before, after)
    flow.report('S1', 2, ('G0', 1), 'delta-sync', inputs=('.codeanvil/GT/SyRS.md',), outputs=('.codeanvil/design/SDD.md',))
    # Applied is not reviewed: a fresh G1 human verdict is still mandatory.
    assert flow.next() == 'G1'
    flow.report('G1', 2, ('S1', 2), 'delta-sync', inputs=('.codeanvil/design/SDD.md', '.codeanvil/GT/SyRS.md'))
    assert flow.next() == 'S2 system'
    flow.report('S2', 2, ('G1', 2), 'system', inputs=('.codeanvil/design/SDD.md', '.codeanvil/GT/SyRS.md'), outputs=(plan,))
    assert flow.next() == 'G2 system'
    flow.report('G2', 2, ('S2', 2), 'system', inputs=(plan, '.codeanvil/design/SDD.md'))
    assert flow.next() == 'S3 system'
    flow.report('S3', 2, ('G2', 2), 'system', inputs=(plan,))
    assert flow.next() == 'G3 system'
    flow.report('G3', 2, ('S3', 2), 'system', inputs=(plan, '.codeanvil/design/SDD.md'))
    assert flow.next() is None


def test_gt_delta_also_requires_fresh_gate_h(flow):
    old = path_sha256(flow.root / '.codeanvil/GT/SyRS.md')
    flow.write('.codeanvil/GT/SyRS.md', 'authorized rename')
    new = path_sha256(flow.root / '.codeanvil/GT/SyRS.md')
    flow.write('.codeanvil/plans/DELTAS.md',
               '| ID | Type | Document | Status | Before sha256 | After sha256 | Interface impact | Authority | Applied in |\n'
               '|---|---|---|---|---|---|---|---|---|\n'
               f'| D-002 | RENAMED | .codeanvil/GT/SyRS.md | applied | {old} | {new} | none | author | S0 iteration 2 |\n')
    flow.report('S0', 2, scope='delta-sync', outputs=('.codeanvil/GT/SyRS.md',))
    assert flow.next() == 'G0'
    flow.report('G0', 2, ('S0', 2), 'delta-sync', inputs=('.codeanvil/GT/SyRS.md',))
    assert stale_reason('S1', flow.gates(), project_root=flow.root) is None
    assert flow.next() == 'S2 slice 0'


def test_acceptance_parser_ignores_examples_and_partial_verdicts(flow):
    flow.report('G3', scope='system', hitl='FEEDBACK',
                extra='Sync-only: yes\nDelta accepted: D-001\n```\nDelta accepted: D-FAKE\n```\n')
    state = report_state(flow.root / '.codeanvil/report/c/G3.md')
    assert state.accepted_deltas == ('D-001',)
    assert state.sync_only



@pytest.mark.parametrize('gate,predecessor', [('S3', 'G2'), ('G3', 'S3')])
def test_same_iteration_with_different_scope_cannot_reuse_approval(flow, gate, predecessor):
    deliver_slice(flow, 1, 'slice 0')
    flow.report(gate, 2, (predecessor, 1), 'system')
    assert flow.next() == f'{gate} slice 0'


def test_mixed_sync_waits_for_gate_h_before_applying_design(flow):
    before = path_sha256(flow.root / '.codeanvil/GT/SyRS.md')
    flow.write('.codeanvil/GT/SyRS.md', 'accepted GT rename')
    after = path_sha256(flow.root / '.codeanvil/GT/SyRS.md')
    flow.write('.codeanvil/plans/DELTAS.md',
               '| ID | Type | Document | Status | Before sha256 | After sha256 | Interface impact | Authority | Applied in |\n'
               '|---|---|---|---|---|---|---|---|---|\n'
               f'| D-002 | RENAMED | .codeanvil/GT/SyRS.md | applied | {before} | {after} | none | author | S0 iteration 2 |\n'
               '| D-003 | design-sync | .codeanvil/design/SDD.md | accepted | | | none | reviewer | |\n')
    flow.report('S0', 2, scope='delta-sync', outputs=('.codeanvil/GT/SyRS.md',))
    assert flow.next() == 'G0'
    flow.report('G0', 2, ('S0', 2), 'delta-sync', hitl='FEEDBACK', inputs=('.codeanvil/GT/SyRS.md',))
    assert flow.next() == 'S0'
    flow.report('S0', 3, scope='delta-sync', outputs=('.codeanvil/GT/SyRS.md',))
    flow.report('G0', 3, ('S0', 3), 'delta-sync', inputs=('.codeanvil/GT/SyRS.md',))
    assert flow.next() == 'S1 delta-sync'


def test_unreviewed_design_delta_never_reuses_g1_pass(flow):
    before = path_sha256(flow.root / '.codeanvil/design/SDD.md')
    flow.write('.codeanvil/design/SDD.md', 'authorized design sync')
    after = path_sha256(flow.root / '.codeanvil/design/SDD.md')
    delta_table(flow, 'applied', before, after)
    flow.report('S1', 2, ('G0', 1), 'delta-sync', inputs=('.codeanvil/GT/SyRS.md',), outputs=('.codeanvil/design/SDD.md',))
    assert flow.next() == 'G1'
    flow.report('G1', 2, ('S1', 2), 'delta-sync', hitl='FEEDBACK', inputs=('.codeanvil/design/SDD.md',))
    assert flow.next() == 'S1'


def test_later_reviewed_delta_delivery_can_close_original_sync_feedback(flow):
    plan = deliver_slice(flow, 1, 'system', finish=False)
    flow.report('G3', 1, ('S3', 1), 'system', hitl='FEEDBACK', inputs=(plan,),
                extra='Verdict: design defect\nSync-only: yes\nDelta accepted: D-001\n')
    before = path_sha256(flow.root / '.codeanvil/design/SDD.md')
    flow.write('.codeanvil/design/SDD.md', 'accepted minor change')
    delta_table(flow, 'applied', before, path_sha256(flow.root / '.codeanvil/design/SDD.md'))
    # A later bounded delivery can preserve the applied row's original iteration identity.
    flow.report('S1', 3, ('G0', 1), 'delta-sync', inputs=('.codeanvil/GT/SyRS.md',), outputs=('.codeanvil/design/SDD.md',))
    flow.report('G1', 3, ('S1', 3), 'delta-sync', inputs=('.codeanvil/design/SDD.md', '.codeanvil/GT/SyRS.md'))
    assert flow.next() == 'S2 system'

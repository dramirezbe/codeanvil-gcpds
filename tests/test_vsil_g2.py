from test_create import _skill_text
from codeanvil.config.paths import TEMPLATES_DIR


def test_microgate_paper_checks_and_routes():
    skill = _skill_text('G2_plan_review')
    checklist = (TEMPLATES_DIR / 'skills/G2_plan_review/references/G2_CHECKLIST.md').read_text()
    for text in (skill, checklist):
        for check in ('Completeness', 'Traceability', 'Contract consistency', 'Task ordering',
                      'Verification feasibility', 'Fresh-context sufficiency'):
            assert check in text
        for route in ('plan defect', 'design defect', 'GT defect'):
            assert route in text
        assert 'never offers RFD' in text or 'Never offer RFD' in text
    assert 'S2 must rework first.' in skill
    assert 'Decided by:' in skill


def test_tutor_corrections_preserve_v4_gt_feedback():
    s0 = _skill_text('S0_normalise_build_package')
    for expected in ('Exiting draft mode', 'full inventory', 'G2 GT-defect feedback',
                     'Verdict: GT defect', 'Scope: delta-sync', 'MINOR', 'PATCH'):
        assert expected in s0
    assert 'python -c' not in s0

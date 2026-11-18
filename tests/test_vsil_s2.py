from test_create import _skill_text


def test_planning_cadence_and_per_module_context():
    text = _skill_text('S2_plan_modules')
    for expected in ('S2(k) → G2(k) → S3(k) → G3(k)', 'Scope: slice', 'Scope: system',
                     '<SUB-xxx>/<module_id>/PLAN.md', 'contracts verbatim', 'GT version',
                     'INFRA-PLAN.md', 'INTEGRATION-PLAN.md', 'empty locked table',
                     'Apply accepted deltas first', 'Modules:', 'codeanvil custody digest'):
        assert expected in text
    assert 'One PLAN.md per slice' not in text


def test_implementor_receives_only_context_set():
    from codeanvil.config.paths import TEMPLATES_DIR
    text = (TEMPLATES_DIR / 'agents/vsil-implementor.md').read_text()
    for expected in ('one', 'Context set', 'Never edit plans', 'golden manifests',
                     'Never ask the human', 'plan defect', 'design defect'):
        assert expected.lower() in text.lower()
    assert 'Deferred to Phase F' not in text

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


def test_s2_first_delivery_continues_through_plan_and_report_creation():
    text = ' '.join(_skill_text('S2_plan_modules').split())
    for rule in ('same turn', 'Missing first-run plans are outputs to create',
                 'nonzero exit code', 'Exit 0 with `nothing to back up`',
                 'it does not write plans', 'Only DELTAS.md starts with the empty locked table',
                 'codeanvil custody verify --cycle <cycle> --gate S2',
                 'only the human decides G2', 'never rewriting historical bytes'):
        assert rule in text


def test_generated_s2_carries_continuity_and_recovery_reference(tmp_path):
    from codeanvil.init.create import scaffold_project
    project = scaffold_project('S2 delivery probe', 's2', tmp_path)
    skill = project / '.agents/skills/S2_plan_modules'
    text = (skill / 'SKILL.md').read_text()
    assert 'version: "1.1"' in text
    assert 'references/delivery.md' in text
    assert '.agents/skills/S2_plan_modules/scripts/slice_backlog.py' in text
    reference = (skill / 'references/delivery.md').read_text()
    assert 'metadata-only correction' in reference
    assert 'unresolved G2 findings are unchanged' in reference
    assert 'templates/skills/' not in text
    assert not list((project / '.codeanvil/report').glob('**/S2.md'))

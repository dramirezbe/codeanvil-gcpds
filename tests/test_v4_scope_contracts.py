"""Cross-skill scope and artifact contracts, reviewed without executing the methodology."""


def test_scope_specific_skill_obligations_and_immutable_plan_notes():
    from codeanvil.config.paths import TEMPLATES_DIR
    skill = lambda name: (TEMPLATES_DIR / 'skills' / name / 'SKILL.md').read_text()
    s3 = skill('S3_implement_modules')
    scope = s3.split('## Scope execution\n', 1)[1].split('## Steps\n', 1)[0]
    assert "Within step 3 also write and exercise the current module's VL-1 tests" in scope
    assert 'Do not defer these to system scope' in scope
    assert 'parent writes returned implementation\n  notes in S3.md' in scope
    assert 'may fill the PLAN' not in s3
    assert 'Before and after this delivery run `codeanvil custody verify --cycle <cycle> --gate G2`' in s3
    g3 = skill('G3_adaptive_verification')
    assert 'Only `system` must smoke the actual §0.5 root command' in g3
    assert 'A declared VL-1 module or path with no VL-1 test is a **plan defect**' not in g3
    assert 'Sync-only: yes' in g3 and 'zero unrecorded acceptances or pending accepted deltas' in g3
    assert 'test_run.md`, and' in g3
    verifier = (TEMPLATES_DIR / 'agents/vsil-verifier.md').read_text()
    assert 'Only system scope requires the real §0.5 entry-point smoke test' in verifier
    plan = (TEMPLATES_DIR / 'skills/S2_plan_modules/references/PLAN.md').read_text()
    assert 'immutable after G2 approval' in plan
    assert 'S3 parent fills' not in plan
    s1, g1 = skill('S1_design_system'), skill('G1_design_review')
    assert '"G0 approved" row' not in s1
    assert 'files S2 must edit' not in g1
    s2 = skill('S2_plan_modules')
    assert 'Only **advance** requires a preceding-slice G3 PASS' in s2
    assert 'Include acceptances on FEEDBACK' in s2
    assert 'Do not edit plans/BACKLOG or write S2.md' in s2

"""T3 — S1 declares the HAL mode, the toolchain and the verification kit (D1–D9)."""

from test_create import TEMPLATES_DIR, _skill_text


def _design_template() -> str:
    path = TEMPLATES_DIR / "skills" / "S1_design_system" / "references" / "SDD.md"
    return path.read_text(encoding="utf-8")


def test_s1_skill_declares_the_hal_mode():
    text = _skill_text("S1_design_system")

    assert "HAL mode" in text
    assert "mock-only" in text
    assert "mock+real" in text
    assert "PROTO-" in text  # mock+real cites the SyRS lab procedures (D9)


def test_s1_skill_declares_the_toolchain_per_service():
    text = _skill_text("S1_design_system")

    assert "Toolchain" in text
    assert "uv · pytest" in text
    assert "pnpm · vitest" in text
    assert "src/<package>/" in text


def test_s1_skill_designs_the_telemetry_companion_in_the_kit():
    text = _skill_text("S1_design_system")

    assert "Telemetry companion" in text
    assert "verification/" in text


def test_s1_separates_execution_targets_from_hal_and_levels():
    """Local VL-0/VL-1 (Mock HAL) must not be presented as VL-2; targets are design intent."""
    text = " ".join(_skill_text("S1_design_system").split())
    design = _design_template()

    assert "design intent" in text
    assert "deduced from the `HWC-*` blocks" in text
    assert "never pick the first silently" in text
    assert "VL-0 and VL-1 run **locally with no hardware**" in text
    assert "Remote PIL at S3 is out of scope" in text
    assert "run locally and remain **VERIFIED**" in text
    assert "| Target(s)" in design
    assert "**Where each level runs:**" in design
    assert "operating envelope (repeat per execution target)" in design
    assert "Host readings cannot stand in for a" in design


def test_s1_skill_accepts_design_defect_rework():
    text = _skill_text("S1_design_system")

    assert "Verdict: design defect" in text


def test_s1_skill_keeps_the_ml_training_source_rule():
    """FW-ML-1 — the ML rule stays exactly as written."""
    text = _skill_text("S1_design_system")

    assert ("training source: Mock HAL (a software signal generator behind the HAL port) data plus labelling or,\n"
            "  failing that, real-hardware HAL data plus labelling.") in text


def test_s1_design_template_has_toolchain_hal_ladder_and_telemetry():
    text = _design_template()

    assert "| Toolchain" in text
    assert "| HAL mode" in text
    assert "#### 1.3.4 Verification kit" in text
    assert "### 1.6 HAL substitution ladder" in text
    assert "### 1.7 Telemetry companion" in text
    assert text.index("### 1.5 Supplied ML model") < text.index("### 1.6 HAL") \
        < text.index("### 1.7 Telemetry") < text.index("## 2. Dependency view")


def test_s1_skill_backs_up_before_overwriting_the_design():
    text = " ".join(_skill_text("S1_design_system").split())

    assert "codeanvil backup S1" in text
    assert "If it exits nonzero, stop and show its message; write no iteration." in text


# --- bounded rework: design change set and SDD digest (2026-11-06) ----------

def test_s1_skill_writes_a_bounded_design_change_set_on_rework():
    text = " ".join(_skill_text("S1_design_system").split())

    assert "design change set" in text
    assert "old decision, the new decision, the reason" in text
    assert "no code impact" in text
    assert "Keep the IDs of unchanged elements stable" in text
    assert "SHA-256 of the final `SDD.md`" in text


def _continuity(text):
    return ' '.join(text.split('## Execution Continuity\n', 1)[1].split('## Steps (one pass)\n', 1)[0].split())


def test_s1_must_execute_past_preparation_and_deliver_all_artifacts():
    section = _continuity(_skill_text('S1_design_system'))
    for expected in ('**in the same turn**', 'S1 has no scheduled internal human checkpoint',
                     'preparation, not a completed stage', 'Write the design incrementally',
                     'Do not return only a reading summary', 'an assumed turn budget is not a blocker'):
        assert expected in section
    for path in ('.codeanvil/design/SDD.md', '.codeanvil/design/dependency_graph.html',
                 '.codeanvil/design/dependency_graph_light.html', '.codeanvil/report/<cycle-name>/S1.md'):
        assert path in section
    assert 'Record PASS only after the design and both graphs are complete' in section
    assert "Never assume G1's human verdict" in section


def test_s1_resumes_without_restarting_or_bypassing_real_stop_conditions():
    section = _continuity(_skill_text('S1_design_system'))
    for expected in ('Resume, do not restart', 'Preserve valid sections and stable IDs',
                     'Do not repeat an already successful backup', '`nothing to back up` result is not a blocker',
                     'complete unaffected work first', 'failed command/error',
                     'Explicit human stop or actual runtime interruption', 'write no fabricated completed iteration'):
        assert expected in section
    for response in ('`continue`', '`run`', '`y`', '`yes`', '`ok`', '`RUN`', '`do not run`'):
        assert response in section
    assert 'never waive a prerequisite, expand scope or decide G1' in section


def test_scaffolded_s1_retains_continuity_and_local_reference_paths(tmp_path):
    from codeanvil.init.create import scaffold_project
    project = scaffold_project('S1 continuity probe', 's1-continuity', tmp_path)
    generated = project / '.agents/skills/S1_design_system/SKILL.md'
    text = generated.read_text(encoding='utf-8')
    assert _continuity(text) == _continuity(_skill_text('S1_design_system'))
    assert '.agents/skills/S1_design_system/references/SDD.md' in text
    assert 'templates/skills/' not in text
    assert 'version: "1.2"' in text
    assert not list((project / '.codeanvil/design').iterdir())
    assert not list((project / '.codeanvil/report').glob('**/S1.md'))


def test_s1_delivery_procedure_keeps_upstream_baseline_and_checks_all_profiles():
    text = _skill_text('S1_design_system')
    reference = (TEMPLATES_DIR / 'skills/S1_design_system/references/rework_delivery.md').read_text()
    assert 'references/rework_delivery.md' in text
    assert 'never write `Based on: G1 ...`' in text
    assert 'Rework from: G1 iteration <N>' in text
    for rule in ('no module/path requires VL-2', 'synchronize module levels, hardware edges and labels',
                 'Responsibility', 'Append the next', 'never rewriting history'):
        assert rule in reference or rule in text
    assert 'codeanvil custody verify --cycle <cycle> --gate S1' in text


def test_generated_s1_g1_ship_the_delivery_reference_and_recovery_route(tmp_path):
    from codeanvil.init.create import scaffold_project
    project = scaffold_project('Rework instructions', 'rework', tmp_path)
    skills = project / '.agents/skills'
    reference = skills / 'S1_design_system/references/rework_delivery.md'
    assert reference.is_file()
    g1 = (skills / 'G1_design_review/SKILL.md').read_text()
    assert '../S1_design_system/references/rework_delivery.md' in g1
    agents = (project / 'AGENTS.md').read_text()
    assert 'resume the `Next:` step' in agents
    assert 'Rework from: G1 iteration <N>' in agents
    assert 'templates/skills/' not in reference.read_text()

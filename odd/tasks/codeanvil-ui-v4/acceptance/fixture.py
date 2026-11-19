from pathlib import Path
import json
import sys
import yaml

root = Path(sys.argv[1])
base = root / '.codeanvil'
base.mkdir(parents=True, exist_ok=True)
cycle = '02_pump'
retry = cycle + '_retry'
(base / 'project.yaml').write_text(yaml.safe_dump({'id': '019f0000-0000-7000-8000-000000000002', 'name': 'Pump fixture', 'cycle': cycle}))
(root / 'UI_FIXTURE.md').write_text('Synthetic evidence for the workspace UI.')
order = yaml.safe_load(Path('templates/config.yaml').read_text())['report_order']
prototype = Path('templates/skills/G3_adaptive_verification/references/verified_prototype.md').read_text()
for name in (cycle, retry):
    report = base / 'report' / name
    for folder in ('S3_artifacts', 'G3_artifacts'):
        (report / folder).mkdir(parents=True, exist_ok=True)
    for index, stage in enumerate(order if name == cycle else order[:1]):
        predecessor = f'Based on: {order[index-1]} iteration 1\n' if index else ''
        (report / f'{stage}.md').write_text(f'# {stage}\n\n## Iteration 1\n{predecessor}| HITL | PASS |\n')
    if name == cycle:
        (report / 'S3_artifacts/test_run.md').write_text('# Pump verification\n\n`verification/run.sh vl1`')
        (report / 'G3_artifacts/verified_prototype.md').write_text(
            prototype.replace('<cycle-name>', name).replace('S3 iteration <N>, G3 iteration <M>', 'S3 iteration 1, G3 iteration 1')
            .replace('| MOD-xxx | <k> | <plan path> | <iteration> | <VL-n> | <VL-n> | <Mock HAL / Real HW HAL> | <verification/run.sh vl0 / vl1 / PROTO-*> | <pass> | <in envelope> |',
                     '| pump_guard | 2 | .codeanvil/plans/pump_guard/PLAN.md | 1 | VL-2 | VL-2 | Real HW HAL | PROTO-010 | INCONCLUSIVE | MISSING |')
            .replace('| PATH-xxx | <VL-n> | <VL-n> | <Mock HAL / Real HW HAL> | <command> | <pass> | <in envelope> |',
                     '| PATH-010 | VL-2 | VL-1 | Mock HAL | verification/run.sh vl1 | VL-1 PASS; VL-2 BLOCKED | MISSING |')
            .replace('<supported modules/paths or "none">', 'none'))
    run_id = f'{name}_1_2026-11-19_12-00-00-000'
    folder = root / 'verification/telemetry' / run_id
    folder.mkdir(parents=True, exist_ok=True)
    with (folder / f'{run_id}.jsonl').open('w') as out:
        for i in range(10):
            value = i * 4 + (10 if name == cycle else 50)
            cpu = {'unavailable': 'fixture gap'} if i == 4 else value
            sample = {'process': {'cpu_percent': cpu}}
            if name == cycle:
                sample['timestamp'] = f'2026-11-19T12:00:0{i}.000Z'
            out.write(json.dumps(sample) + '\n')
    (folder / 'pytest_vl1.txt').write_text(f'{name} captured result')
    record = dict(schema_version=2, cycle=name, stage='G3', iteration=1, run_id=run_id,
                  target='fixture', command='verification/run.sh vl1',
                  started_at='2026-11-19T12:00:00Z', finished_at='2026-11-19T12:00:10Z',
                  exit_code=0, measurements=[dict(requirement_id='SYS-013', metric='pressure', value=12 if name == cycle else 19, unit='kPa',
                                              criterion='at most 15 kPa', result='inconclusive' if name == cycle else 'fail')])
    (folder / 'measurement.json').write_text(json.dumps(record))

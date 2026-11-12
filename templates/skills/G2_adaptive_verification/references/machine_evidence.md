# Laboratory measurements, version 2

The agent runs functional or metrological tests appropriate to the GT and records what actually
happened. `measurement.json` captures results; it does not decide the human G2 verdict. A real
hardware test does not universally require a calibrated source or formal oracle: justify why
the method and resolution support the requested tolerance. Satisfy calibration/correction
requirements when the GT or the conclusion requires them, or report `inconclusive`.

## Before touching hardware

The parent agent presents the published code/kit, target/device and planned update/deploy/test
operations, then **stops and waits for explicit `continue`**. This checkpoint applies to remote
updates/deployment and local hardware tests, even with full host access. It is the existing
narrative `Checkpoint:` line in the completed stage report, not a new gate or state. A fresh G2
verifier never asks the human: the G2 parent owns the pause, preparation and trusted operations.

Code and kit must be clean and pushed. After the review, the agent updates tool/application and
dependencies from their respective published references, synchronizes clocks before measuring
and diagnoses failures. Neither tool version equality nor a deployment manifest is required.
Normal tests run through the authorized runtime; clearly destructive operations go to trusted.

## Capture and read the record

Use `<cycle>_<iteration>_<codeanvil now --machine>` as the run ID. `iteration` is the existing S2
or G2 iteration being performed; no HIL counter is added. A retry uses a new timestamp. Keep
telemetry and script outputs together under `verification/telemetry/<run_id>/`, including
`<cycle>_<iteration>_<timestamp>.jsonl` and `measurement.json`. Create new outputs without
overwriting an earlier attempt. Old v1 records and historic reports remain unchanged.

The required record fields are `schema_version: 2`, `cycle`, `stage` (`S2` or `G2`), `iteration`,
`run_id`, `target`, `command`, `started_at`, `finished_at`, `exit_code` and `measurements`.
Each measurement gives `requirement_id`, `metric`, `value` (number, text or boolean), `criterion`
and `result` (`pass`, `fail`, `inconclusive`); add `unit` where relevant. A failure before any
measurement may use an empty list with a nonzero exit code and an `error` explanation. Versions,
device settings, telemetry status, artifact paths and metrological context are optional. Extra
fields are allowed. No file hash, deployment digest, formal capture request or host time bound
is required.

For remote evidence, `fetch_evidence` returns `local_path`, a new host snapshot. Select this
run's files within that path; snapshots can also contain older remote logs. Read local evidence
directly from its run directory. Record the actual target, command, times and results in the
existing report; do not relabel an old S2 measurement as a fresh G2 test.

Run the copied structural checker locally through the methodology runtime:

```sh
codeanvil python templates/skills/G2_adaptive_verification/scripts/validate_measurement.py \
  <record-path>/measurement.json
```

Exit 2 means malformed/incomplete record. Exit 0 means **valid record**, including measurements
recorded as failed or inconclusive, not a passing test or a gate verdict. The checker validates
basic fields and finite numeric values; the agent assesses the actual criteria against GT.
It does not calculate expectations, impose a scalar interval or require calibration metadata
for every functional test. Missing telemetry prompts notice and investigation of collector,
process, disk or sensors. Decide whether to repeat or continue with unaffected evidence, record
the cause and scope, and never replace missing readings with zeros. A collector exit 0 does not
prove complete coverage.

G2 feedback identifies command/target, observed and expected result, relevant evidence, technical
cause or unconfirmed hypothesis, affected requirement/module/path, next action and the existing
rework route. Operational faults are diagnosed as such, not invented product defects. Only the
human's final G2 answer sets `HITL`.

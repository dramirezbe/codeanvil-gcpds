# Machine-captured VL-2 evidence

VL-2 uses a fresh capture from the Real HW HAL against the oracle already declared in SyRS §6.
The capture is machine-produced; G2's verdict remains human. A transport connection, valid JSON
or a successful validator exit does not establish calibration, correct uncertainty or VALIDATED.

## Before requesting a capture

All of these must be resolved in the approved SDD and GT:

- `mock+real`, a named execution target and the actual device/driver capabilities it requires;
- a SyRS §6 `PROTO-*`, a declared oracle/reference and its calibration provenance;
- SyRS §4 correction chains and §5 uncertainty/tolerance budgets, with units and decision rule;
- the Real HW HAL's non-transmitting probe, its capability guard and safe shutdown;
- the S2 deployment identity, CodeAnvil version parity and target telemetry envelope.

Identity applies to local HIL as well: with no remote `targets:`, use target name `local`, the
observed host CodeAnvil version and a locally generated deployment manifest/checker. Perform
pre/post checks on that manifest without SSH, sync or MCP. Local VL-0/VL-1 alone need no manifest.

If any is missing, **do not run VL-2**. Record the specific gap and return it to S1/GT author or
S2 as appropriate. Never choose a reference signal, infer calibration or substitute synthetic
data. The bundled schema supports one scalar measurement per row with a closed interval
`lower <= corrected <= upper`. It records standard uncertainty but does not apply guard bands
or another uncertainty decision rule. Other predicates require an explicitly reviewed schema
extension; do not encode them as unsupported passing claims.

## Fresh G2 capture request

1. G2 chooses a new run ID and records the host UTC request time **before** the capture. Write
   `.codeanvil/report/<cycle>/G2_artifacts/capture_request.json` with target name, `run_id`,
   `not_before`, expected deployment manifest SHA-256, expected CodeAnvil version, `PROTO-*`,
   exact S2 capture command and the human's authorization/operator reference. These expectations
   come from the approved design and S2 record, never from a returned measurement.
2. Present the exact capture command, target, device and RF/TX consequences to the human. A
   human or authorized operator executes it after explicit authorization and reports the exit
   code. For a remote target the authorized call uses `ssh_exec_cmd_trusted`; the auto door
   refuses `verification/run.sh vl2`. The fresh verifier never calls the trusted tool and never
   bypasses it with Python, direct SSH or another shell. A full-access host may suppress prompts;
   record the authorization explicitly rather than treating the tool name as consent.
3. The S2-created command is `verification/run.sh vl2 --run-id <id>` plus the protocol-specific
   arguments recorded in `test_run.md`. It refuses an existing run directory, probes the device,
   checks capabilities before configuration, checks deployment identity before and after, starts
   telemetry, executes only the declared `PROTO-*` and stops cleanly. Its per-run directory is
   `verification/telemetry/<run-id>/`, containing `measurement.json`, telemetry and captures.
   Files are created exclusively and never overwritten. Failed or partial runs remain separate
   failed evidence; a retry needs a new run ID.
4. Request a new capture for every G2 VL-2 evaluation. S2's development measurements and old
   cycle files are not a fresh G2 run. If clocks disagree, resolve the discrepancy; never weaken
   the host `not_before` bound to accept stale evidence.

## Record and validate

`measurement.json` follows this skill's `references/measurement.schema.json`. It records actual
start/end timestamps, target OS/architecture/CodeAnvil version, device identity and driver,
deployment digest, protocol, oracle/reference/calibration, raw and corrected scalar values,
units, standard uncertainty, correction/tolerance references, bounds and the measured outcome.
Capture files, including the actual device probe output, have SHA-256 digests. Paths are relative
to the run directory; escaping symlinks or paths, missing/empty captures and altered bytes fail.

After the operator finishes, the fresh verifier fetches remote evidence with `fetch_evidence`
(or reads the local run directory). Every fetch returns `local_path`, a new host snapshot under
`verification/telemetry/<target>/fetch-<unique>/`; use that returned path and select
`<run-id>/measurement.json` inside it. The snapshot may also contain older remote runs: only the
requested run ID with timestamps after `not_before` is eligible. Local paths remain
`verification/telemetry/<run-id>/measurement.json`. Per-run relative capture paths stay the same.
Run this recorded host command through the methodology runtime, using the returned remote
snapshot path shown below or its local equivalent:

```sh
codeanvil python templates/skills/G2_adaptive_verification/scripts/validate_measurement.py \
  <fetch-local-path>/<run-id>/measurement.json \
  --target <expected-target> --run-id <expected-run-id> \
  --deployment-sha256 <expected-manifest-SHA256> \
  --codeanvil-version <expected-version> --not-before <host-request-UTC>
```

The scaffold rewrites the skill path above. S2 records the exact resolved validator command in
`test_run.md`; the fresh verifier substitutes the returned fetch path and values from the host
capture request, never expected provenance from the record itself.
Exit 2 means invalid evidence. Exit 0 means **valid record**, including records with measured
`fail` outcomes; the output always says `human review required`. Read each measurement result.
Validate the telemetry separately with the JSONL evidence reader and that target's §1.7 envelope.

The verifier compares observed device/OS/architecture and protocol references with SDD and the
request, checks correction and uncertainty references against GT, reports gaps and returns the
result table. It does not calculate missing expected values, repair records or judge calibration.
G2 presents the capture, validator output, failed outcomes and evidence gaps to the human. Only
their answer sets `HITL`; a missing oracle or invalid record cannot support a VALIDATED claim.

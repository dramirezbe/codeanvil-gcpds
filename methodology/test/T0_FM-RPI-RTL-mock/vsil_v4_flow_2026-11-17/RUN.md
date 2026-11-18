# V-SIL v4 acceptance preparation — 2026-11-17

Status: automated tooling/scaffold probes executed; full T0 methodology run pending human gates.
This directory is not a Verified Prototype and supplies no new G0 Gate H/G1/G2/G3 verdict.
The archived first_full_flow_2026-11-05 remains historical v3 evidence, unchanged.

## Executed checks

`.venv/bin/python -m pytest -q`: final run 730 passed, 40 skipped (12.81 s).
After report-wording corrections: 52 relevant skill/custody tests passed (0.66 s).
This final run includes implementor generation in all three runtimes.

`tests/test_v4_scaffold_flow.py` creates an isolated v4 scaffold, checks all eight report IDs,
both agents in Claude/OpenCode/Codex formats, planning templates, absent custody folder,
slice continuation, and altered input rejection through the actual console boundary.
Its synthetic PASS rows are test fixtures; they are not human decisions.

| Probe | Automated evidence | Remaining acceptance |
|-------|--------------------|----------------------|
| G2 plan defect → S2 | test_vsil_g2.py, report routing tests | Actual human plan verdict and module-only rework in T0 |
| G2 GT defect → S0 | test_vsil_g2.py, S0 triage contract | Actual conflicting requirement and human resolution |
| G3 plan defect → S2 | G3 skill/route tests | Actual G3 feedback iteration |
| Unchanged-module failure → S1 | G3 self-diagnosis contract | Actual injected dependency failure and fresh verifier |
| Accepted/applied delta advance | test_v4_integrity.py | Author acceptance and GT revision in T0 |
| Structural change stale cascade | test_v4_integrity.py, test_report_state.py | Actual contract version bump in T0 |
| Runtime without subagents | Fresh-session handoff contract and generated agents | Run a module in a separate Pi/Copilot session |
| UI non-chain operation | Existing unskipped UI backend tests | Interactive UI startup on the acceptance project |

## Full T0 acceptance procedure

1. Create a fresh project with the candidate 0.9.0 tool. Copy the T0 Build Package only;
   do not copy old reports as v4 approval. Select a new cycle.
2. Execute S0/G0 and obtain Gate H, then S1/G1 and obtain the design verdict.
3. Execute S2/G2/S3/G3 for slice 0, each module slice and system. Record each real human
   gate answer and implementor/verifier context. S3 cannot self-approve G2/G3.
4. Exercise the eight probes above with real report iterations, preserving candidate digests.
5. On actual system G3 PASS, archive the project and Verified Prototype here, plus exact root
   command, URL, observed smoke result, clean shutdown and telemetry/evidence paths.

Release/tag and final PR wait for the owner's review. Do not mark Phase K accepted from unit
or scaffold tests alone.

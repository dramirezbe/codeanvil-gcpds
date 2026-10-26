# Custody Chain

| Field     | Value |
|-----------|-------|
| Gate      | CC |
| Cycle     | 01_smoke_test |
| Document  | GT/G0_StRS.md, GT/G0_SyRS.md |
| Created   | 2026-10-26 09:46:13.556 |

---

## Iteration 1

| Field       | Value |
|-------------|-------|
| Date        | 2026-10-26 09:46:13.556 |
| Timestamp   | 2026-10-26_09-46-13-788 |
| Iteration   | 1 |
| Cycle       | 01_smoke_test |
| HITL        | PASS |

### Description

Prerequisite verified: `.codeanvil/report/01_smoke_test/G0.md` latest iteration is `HITL: PASS`.

```
PROVENANCE REPORT  (2026-10-26T14:46:13Z)
Overall: INCOMPLETE
1. Controls   : SKIPPED (no controls registry configured)
2. Ports      : SKIPPED (no ports bindings configured)
3. Source     : PASS (3 files, 122556 bytes, manifest 6027d645781a)
4. Custody    : PASS (1 entry, head 1ef472f6ff0a)
Findings: none
Limitations: this scaffolded project has no controls.json or ports.json, so
ControlRegistry and Port binding checks were not applicable. The CC report's
own creation entry is recorded after this report and verified separately.
```

Observed exit codes:

| Step | Command | Exit |
|------|---------|------|
| Controls | `control_registry.py --registry <controls.json>` | not run (no registry) |
| Ports | `port_check.py --root . --bindings ports.json` | not run (no bindings) |
| Seal | `source_snapshot.py snapshot --root . --include 'GT/**' --out .codeanvil/custody/snapshot.json` | `0` |
| Source verify | `source_snapshot.py verify --root . --snapshot .codeanvil/custody/snapshot.json --strict` | `0` |
| Custody record | `custody_ledger.py record --doc .codeanvil/report/01_smoke_test/G0.md --action accessed` | `0` |
| Custody verify | `custody_ledger.py verify --ledger .codeanvil/custody/custody.jsonl --root .` | `0` |

Source snapshot details:

- Files: 3 (`GT/G0_StRS.md`, `GT/G0_SyRS.md`, `GT/README.md`)
- Total bytes: 122556
- Manifest digest: `6027d645781a27d12a174b51bc91da37ab373e159689dc297ee061c51139ca9f`
- Verify result: PASS, 0 findings, 3 files checked

Custody ledger details:

- Entry 1: `G0.md` accessed by `opencode-agent` (V-SIL gate agent)
- Document SHA-256: `cbc5b2b808a688814863967bf2fd91575eec3b9fceaa8ace736653981bb6a10f`
- Entry hash: `1ef472f6ff0a7cd1ab7a3633b31e7ba19f153adb9665edf504988c973a0296cf`
- Verify result: PASS, 0 findings

User decision: PASS — accepted with source and custody checks passing, and
controls/ports skipped as not applicable. No feedback.

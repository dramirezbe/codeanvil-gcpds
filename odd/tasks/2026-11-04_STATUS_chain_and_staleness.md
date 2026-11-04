# Plan — STATUS: chain order, stale reports and closed cycles

Feature: `odd/tasks/2026-11-04_1042_vsil_v3_skill_flow.md` · Task T10 · Specs S4, S11 · Contracts C2, C4, C11
Target: `src/codeanvil/CLI/commands/status.py`, `templates/config.yaml`, tests. S11: "yes, add it to the plans. You can refactor also \"status\". But mantain sync, and now". `sync.py` and `now` do not change.

## Goal

`codeanvil status` keeps reading only reports, and also shows what the reports imply: flow order, stages that delivered, a PASS that went stale, and a cycle an RFD closed. It still advances nothing and stores nothing: reports stay the only state, and each skill still runs its own prerequisite check (C2).

## Output

Reports with no `Based on` line and no chain id print exactly as today.

```text
Cycles:
  01_fm (closed: superseded by 02_fm_relaxed)
    S0: delivered (iteration 1)
    G0: PASS (iteration 1)
    S1: delivered (iteration 1)
    G1: FEEDBACK (iteration 1)
    RFD: PASS (iteration 2)
  02_fm_relaxed (active)
    S0: delivered (iteration 2)
    G0: PASS (iteration 1) [stale: based on S0 iteration 1, S0 is at 2]
    S1: delivered (iteration 1) [stale: G0 is stale]
```

## Changes

| Part | Change |
|------|--------|
| `templates/config.yaml` | Add `report_order: ["S0", "G0", "S1", "G1", "S2", "G2"]` and `stage_reports: ["S0", "S1", "S2"]` |
| `_report_state` | Also return `based_on` and `superseded_by`, read only from the text after the last `## Iteration` heading. The HITL and iteration logic stays as it is |
| New `_stale_reason(gate, gates)` | Stale when the report's `based_on` iteration is older than that predecessor's latest iteration, or when the predecessor is itself stale. A visited set stops a malformed `Based on` loop |
| `_cycle_reports` | Order gates by `report_order`; any other id follows alphabetically, so `RFD` and old ids like `CC` still print |
| `cmd_status` | Print `delivered` for a passing id in `stage_reports`, the `[stale: ...]` suffix, and `(closed: superseded by <cycle>)` on the cycle line |

```python
_BASED_ON_RE = re.compile(r"^Based on: (\S+) iteration (\d+)\s*$", re.MULTILINE)
_SUPERSEDED_RE = re.compile(r"^Superseded by cycle: (\S+)\s*$", re.MULTILINE)
```

Missing `based_on` means "not stale", and a `Based on` naming a report absent from the cycle also means "not stale", so old cycles and partial reports never produce a false warning.

## RED tests first (`tests/test_create.py`)

One test per rule, through `cmd_status` and `capsys`, using `_write_report` extended with an optional `based_on`:

1. Gates print in `report_order`, with unknown ids after them: `S0`, `G0`, `S1`, then `CC`, `RFD`.
2. A passing `S1` prints `S1: delivered (iteration 1)`. A failing one prints `S1: FEEDBACK (iteration 1)`.
3. `G1` based on `S1` iteration 1 while `S1` is at 2 prints `[stale: based on S1 iteration 1, S1 is at 2]`.
4. Staleness propagates: `S2` based on the latest `G1`, with `G1` stale, prints `[stale: G1 is stale]`.
5. `G1` based on the latest `S1` prints no suffix.
6. A `Based on` line in an earlier iteration only is ignored.
7. `Superseded by cycle: 02_x` in the latest `RFD` iteration prints `(closed: superseded by 02_x)`, and a line in an earlier iteration does not.
8. A `Based on` loop between two reports ends without error.

Existing behaviour stays pinned and these tests must pass unchanged: `test_status_reads_cycle_scoped_reports`, `test_status_lists_every_cycle`, `test_status_ignores_the_ambiguous_schema_row`, `test_status_reads_legacy_reports_when_no_cycles_exist`, `test_status_reports_latest_hitl_not_first`. The `CC` fixture stays on purpose, because it now pins that old report ids are still listed.

## Differential check

Compare stdout, stderr and exit code against a base-commit copy in a `mktemp -d` folder:

- `codeanvil now` and `codeanvil sync`: identical.
- `codeanvil status` on a project with only `G0.md`, plus a project with legacy reports: identical.

Do not run these against the real `~/.codeanvil-config` database: use the `db_path` fixture pattern or a scratch `HOME`, because `status` auto-registers projects.

## Risk

Item 3: agents read this output, and `AGENTS.md` makes it the first action on project open. The existing line format is kept and only suffixes are added. Commit separately from the chain switch.

## Acceptance

All tests pass, the differential check shows no unrequested difference, and `git diff` shows no change to `src/codeanvil/init/sync.py`, the `now` command or `config/time.py`.

## Reuse

`_ITERATION_RE`, `_HITL_RE`, legacy report handling and the manifest and DB lookups stay as they are.

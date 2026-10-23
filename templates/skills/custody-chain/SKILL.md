---
name: custody-chain
description: "Trigger: provenance, custody, integrity, hash, seal, snapshot, tamper, audit trail, evidence, lineage. Verify source immutability and track chain of custody of generated audit documents across all V-SIL gates."
license: Apache-2.0
compatibility: "Requires Python 3.9+ (stdlib only). No network access. Writes only to .codeanvil/custody/ and .codeanvil/report/<cycle-name>/CC.md."
metadata:
  author: "gcpds"
  version: "2.0"
  gate: "CC"
  pipeline: "V-SIL"
---

# Custody Chain — Data Provenance & Integrity Verification

## Prerequisite and Cycle

G0 must have passed on both Ground Truth documents.

Before running anything:

1. Resolve the active cycle from `.codeanvil/project.yaml` (the `cycle:` key).
   If the key is missing, stop and ask the user for a cycle name (see
   `AGENTS.md`, `## Cycle`).
2. Read `.codeanvil/report/<cycle-name>/G0.md`. If the file does not exist, or
   its **latest** iteration is not `HITL: PASS`, stop and return exactly:

   > G0 must pass first. Run the G0 skill.

   Write no report iteration and run no custody script in that case.

## Report Contract

Write exactly one file: `.codeanvil/report/<cycle-name>/CC.md`.

- First run: write the header and `## Iteration 1`.
- Later runs: append `## Iteration <N>`, where `N` is the number of existing
  iterations plus one.
- Header fields: `Gate` = `CC`, `Cycle` = the active cycle, `Document` = the
  GT files sealed by the snapshot, `Created` = `codeanvil now`.
- Iteration fields: `Date` = `codeanvil now`, `Timestamp` = `codeanvil now --machine`,
  `Iteration` = `N`, `Cycle` = the active cycle, `HITL` = `PASS` or `FEEDBACK`.
- `Description` carries the provenance report (the same text returned in the
  Output Contract), the observed exit codes, and the user's feedback when there
  is any.

Never edit a previous iteration. Iterations are append-only; the latest
iteration is the gate state.

## Activation Contract

Load this skill when **any** V-SIL gate needs to prove that (1) original source data
was not altered and (2) generated audit documents have a complete, tamper-evident chain
of custody.

This is a **chain link** after G0 and a **cross-cutting** check — it runs once as the
CC gate, and it also applies before and after operations that create, modify, or
export audit documents.

Do **not** load it to judge data correctness or quality, perform column/row-level lineage,
access databases or APIs, enforce access control, or draw legal conclusions — those are
out of scope (see Scope & Boundaries below).

## Hard Rules

- **Run the scripts.** Never re-implement checks in prose (all paths
  repository-root relative):
  - `python templates/skills/custody-chain/scripts/source_snapshot.py snapshot|verify [opts]`
  - `python templates/skills/custody-chain/scripts/custody_ledger.py record|verify|history [opts]`
  - `python templates/skills/custody-chain/scripts/control_registry.py --registry <controls.json>`
  - `python templates/skills/custody-chain/scripts/port_check.py --root . --bindings <ports.json>`
- **Originals are read-only.** Never write to, rename, or regenerate a sealed source file.
  If a mismatch is found, report it; do not repair it.
- **Evidence over assertion.** Every PASS must cite a tool run (digest, byte length,
  ledger head hash). Never write "verified" from memory or inference.
- **Fail closed.** Missing file, unreadable file, unset signing key, or ambiguous result
  = FAIL or UNVERIFIED, never PASS.
- **Append-only custody.** Ledger entries are never edited or deleted. Corrections are
  new entries.
- **Project-relative paths only.** Reject absolute paths, `..` traversal, backslashes,
  drive letters, and symlinks that leave the project root.
- **No secrets in output.** Never print, log, store, or echo the HMAC key.
- **Exit codes are verdicts.** `0` = PASS, `1` = FAIL, `2` = usage/IO error. Never
  record a PASS on exit `1` or `2`.
- **One report file, append-only.** Never write a second `CC` file and never edit
  an earlier iteration.

## Scope & Boundaries

### In scope

- **Source integrity:** project-relative paths, byte lengths, SHA-256 digests, sealed manifests.
- **Chain of custody:** who created, accessed, modified, extracted, signed, verified, or
  exported an audit document, with UTC timestamps and document hashes.
- **Audit-rule hygiene:** ControlRegistry validation (unique IDs, typed params, no executable expressions).
- **Wiring checks:** confirming runtime ports have bound, conforming implementations.

### Out of scope (say so and stop)

- Data correctness or quality (hash match ≠ data is right).
- Column/row/transformation-level lineage.
- Databases, APIs, cloud object stores, streams.
- Access control, encryption, key management.
- Forensics, attribution, legal conclusions.
- Remediation (do not restore, re-hash, or regenerate failures).

### What a PASS proves vs. does not prove

| PASS proves | PASS does not prove |
|---|---|
| Sealed files match recorded paths, byte lengths, and digests | Files were correct when sealed |
| Custody ledger is unbroken, signed, and time-ordered | Every real-world access was recorded |
| Latest document hashes match disk | Recorded actor identity is authentic |
| Controls are declarative and typed; required ports are bound | Controls are sufficient; ports behave correctly |

## Decision Gates

| Situation | Action |
|-----------|--------|
| All scripts exit `0` | Present the provenance report to the user and ask **PASS** or **FEEDBACK**. Write the iteration with that `HITL` value. `PASS` completes CC. |
| Any script exits `1` | `HITL` is forced to **FEEDBACK**. Write the iteration with the report verbatim so each finding is actionable. |
| Any script exits `2` | Script error (bad args, unreadable file). Fix the invocation, re-run. Write **no** iteration. |
| `PROVENANCE_HMAC_KEY` not set | FAIL. Tell the user; do not generate a key silently. Write a `FEEDBACK` iteration naming the missing key. |
| Hash mismatch on sealed source | FAIL. Report the expected vs. actual digest. Never explain it away (line endings, encoding). |
| Re-sealing requested | Requires explicit user authorization. Record the re-seal as a ledger entry with the reason. |
| Ambiguous include patterns or zero matched files | Ask the human before proceeding. |

## Execution Steps

Follow in order. Stop and report on the first critical failure unless the user asks
to continue.

### 1. Preflight

- Confirm the prerequisite report check passed (see Prerequisite and Cycle).
- Identify the project root and the provenance directory (default `.codeanvil/custody/`).
- Confirm `PROVENANCE_HMAC_KEY` is set in the environment.

### 2. Validate controls (ControlRegistry)

```
python templates/skills/custody-chain/scripts/control_registry.py --registry <controls.json>
```

### 3. Verify ports (Port Implementation Injections)

```
python templates/skills/custody-chain/scripts/port_check.py --root . --bindings ports.json
```
Static by default. Use `--import` only with user consent (it runs project code).

### 4. Seal or verify GT sources (SourceSnapshot)

After G0 passes, seal the Ground Truth files so any later modification is detected:
```
python templates/skills/custody-chain/scripts/source_snapshot.py snapshot \
  --root . --include 'GT/**' --out .codeanvil/custody/snapshot.json
```
Every later check (before any gate that reads GT):
```
python templates/skills/custody-chain/scripts/source_snapshot.py verify \
  --root . --snapshot .codeanvil/custody/snapshot.json --strict
```
For strong guarantees, ask the user to store `manifest_digest` outside the repo and pass
`--expect-digest`; otherwise someone who edits both GT and snapshot goes undetected.

### 5. Record custody of every audit document touched

```
python templates/skills/custody-chain/scripts/custody_ledger.py record \
  --ledger .codeanvil/custody/custody.jsonl \
  --doc <path> --action <action> --actor "<who>" --role "<role>" --detail "<why>"
```
Actions: `created`, `accessed`, `modified`, `extracted`, `signed`, `verified`, `exported`.

### 6. Verify custody

```
python templates/skills/custody-chain/scripts/custody_ledger.py verify \
  --ledger .codeanvil/custody/custody.jsonl --root .
```

## Output Contract

Return all of:

1. **Verdict** — `CUSTODY: PASS` or `CUSTODY: FAIL` or `CUSTODY: INCOMPLETE`.
2. **The provenance report** in this format:
   ```
   PROVENANCE REPORT  (<UTC timestamp>)
   Overall: PASS | FAIL | INCOMPLETE
   1. Controls   : <status> (<n> controls)
   2. Ports      : <status> (<bound>/<total> bound; unverified: <list>)
   3. Source     : <status> (<files> files, <bytes> bytes, manifest <first 12 hex>)
   4. Custody    : <status> (<entries> entries, head <first 12 hex>)
   Findings: <code, path/id, expected vs actual>  (critical first)
   Limitations: <what was NOT verified and why>
   ```
3. **Finding list** — when there are failures, one entry per finding: code, path/id,
   expected vs. actual.
4. **The observed exit codes** of each script invocation.
5. **The report path** — `.codeanvil/report/<cycle-name>/CC.md` and the iteration number.

`INCOMPLETE` = no failures but something was UNVERIFIED or skipped.

## References

- [references/schemas.md](references/schemas.md) — file format specs for snapshot.json,
  ports.json, controls.json, and custody.jsonl.
- [assets/controls.example.json](assets/controls.example.json) — example control registry.
- `templates/skills/custody-chain/scripts/_common.py` — shared helpers (safe paths, SHA-256, canonical JSON).
- `templates/skills/custody-chain/scripts/source_snapshot.py` — seal and verify source file integrity.
- `templates/skills/custody-chain/scripts/custody_ledger.py` — hash-chained, HMAC-signed custody log.
- `templates/skills/custody-chain/scripts/control_registry.py` — declarative control validation.
- `templates/skills/custody-chain/scripts/port_check.py` — port/interface binding verification.

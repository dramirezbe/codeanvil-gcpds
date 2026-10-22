---
name: custody-chain
description: "Trigger: provenance, custody, integrity, hash, seal, snapshot, tamper, audit trail, evidence, lineage. Verify source immutability and track chain of custody of generated audit documents across all V-SIL gates."
license: Apache-2.0
compatibility: "Requires Python 3.9+ (stdlib only). No network access. Writes only to .codeanvil/custody/ directory."
metadata:
  author: "gcpds"
  version: "1.0"
  gate: "*"
  pipeline: "V-SIL"
---

# Custody Chain — Data Provenance & Integrity Verification

## Activation Contract

Load this skill when **any** V-SIL gate needs to prove that (1) original source data
was not altered and (2) generated audit documents have a complete, tamper-evident chain
of custody.

This is a **cross-cutting skill** — it runs alongside any gate, not as a gate itself.
Invoke it before and after operations that create, modify, or export audit documents.

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
| All scripts exit `0` | Record custody status as PASS. Proceed. |
| Any script exits `1` | Record FAIL. Return the report verbatim so each finding is actionable. Do not proceed to the next gate until resolved. |
| Any script exits `2` | Script error (bad args, unreadable file). Fix the invocation, re-run. Record **no** verdict. |
| `PROVENANCE_HMAC_KEY` not set | FAIL. Tell the user; do not generate a key silently. |
| Hash mismatch on sealed source | FAIL. Report the expected vs. actual digest. Never explain it away (line endings, encoding). |
| Re-sealing requested | Requires explicit user authorization. Record the re-seal as a ledger entry with the reason. |
| Ambiguous include patterns or zero matched files | Ask the human before proceeding. |

## Execution Steps

Follow in order. Stop and report on the first critical failure unless the user asks
to continue.

### 1. Preflight

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

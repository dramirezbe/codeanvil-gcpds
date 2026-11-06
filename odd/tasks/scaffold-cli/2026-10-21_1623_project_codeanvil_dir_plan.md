# Plan: `.codeanvil/` directory inside scaffolded projects

## Context

Methodology outputs are scattered across the scaffolded project root: `GT/` for user-authored ground truth, `.provenance/` for custody chain artifacts, and gate reports exist only as TEXT blobs in the DB's `gate_results` table. GT reference templates are buried inside `.agents/skills/G0_.../templates/` with no visible separation from skill code.

This plan consolidates machine-generated/internal methodology artifacts under `<project>/.codeanvil/`, keeps human-authored GT prominent at project root, and renames the global config to avoid namespace collision.

## Design decisions

1. **GT/ stays at project root.** It's the primary human-authored input — the contract. Burying it in a dot-directory two levels deep adds friction for the one thing users must find and edit. Only machine-generated/internal stuff goes under `.codeanvil/`.

2. **GT templates stay inside the skill only.** No second copy in `.codeanvil/`. The skill owns its reference templates at `.agents/skills/G0_.../templates/` — one location, no drift risk.

3. **Namespace split: `~/.codeanvil-config/` (global) vs `<project>/.codeanvil/` (local).** Same name at two scopes is a collision waiting to happen. The global config dir becomes `~/.codeanvil-config/` (db, mcp installs). The project-local dir is `.codeanvil/` (custody, reports, manifest).

4. **`project.yaml` is collaboration-safe.** UUIDv7 for ID (time-sortable, unique across machines). Name is a human label, not unique. No absolute path (not portable). GT file pointers are relative paths.

5. **`codeanvil sync` for cloned repos.** When someone clones a repo with `.codeanvil/` in it, `codeanvil sync` reads `project.yaml` and registers the project in the local DB. No re-scaffold needed.

## Current state

```
~/.codeanvil/                        ← global config (namespace collision risk)
├── db/codeanvil.db
└── mcp/

<project>/
├── GT/                              ← user-authored GT files + README
├── .provenance/                     ← custody chain (snapshot.json, custody.jsonl)
├── .agents/skills/G0_.../templates/ ← locked GT reference templates
└── (gate reports only in DB)
```

## Target state

```
~/.codeanvil-config/                 ← RENAMED: global config
├── db/codeanvil.db
└── mcp/

<project>/
├── GT/                              ← STAYS: user-authored GT (prominent, visible)
│   ├── README.md
│   ├── G0_SRS.md
│   └── G0_HCS.md
├── .codeanvil/                      ← NEW: machine-generated methodology artifacts
│   ├── project.yaml                 ← project identity (DB projection)
│   ├── custody/                     ← was .provenance/
│   │   ├── snapshot.json
│   │   └── custody.jsonl
│   └── report/                      ← NEW: timestamped gate reports
│       └── (empty at scaffold time)
├── .agents/skills/                  ← unchanged
│   └── G0_.../templates/            ← GT reference templates stay here
├── AGENTS.md                        ← updated paths (.provenance → .codeanvil/custody)
└── ...
```

## What changes

### 1. Rename global config: `~/.codeanvil/` → `~/.codeanvil-config/`

**`src/codeanvil/config/paths.py`**:
```python
WORKDIR = Path.home() / ".codeanvil-config"   # was ".codeanvil"
DB_DIR  = WORKDIR / "db"
DB_PATH = DB_DIR / "codeanvil.db"
MCP_DIR = WORKDIR / "mcp"
```

**`src/codeanvil/init/check.py`** — no code change, reads `WORKDIR` from paths.

**`install.sh`** — if it references `~/.codeanvil/`, update to `~/.codeanvil-config/`.

**Migration**: first run after rename, if `~/.codeanvil/` exists and `~/.codeanvil-config/` doesn't, move it. One-time in `ensure_dirs()`.

### 2. New project-local constants

**`src/codeanvil/config/paths.py`** — add project-relative path constants:
```python
PROJECT_CODEANVIL = Path(".codeanvil")
PROJECT_CUSTODY   = PROJECT_CODEANVIL / "custody"
PROJECT_REPORT    = PROJECT_CODEANVIL / "report"
PROJECT_MANIFEST  = PROJECT_CODEANVIL / "project.yaml"
```

### 3. `src/codeanvil/init/create.py` — scaffold restructure

**`_create_gt_dir()`** — unchanged. GT/ stays at project root with README.

**New `_create_codeanvil_dirs(project_dir)`**:
- Create `.codeanvil/`, `.codeanvil/custody/`, `.codeanvil/report/`.
- Does NOT create `.codeanvil/GT/` (GT stays at root).

**`_copy_gt_reference_templates()`** — unchanged. Templates stay inside the skill at `.agents/skills/G0_.../templates/`.

**`scaffold_project()`** — add call to `_create_codeanvil_dirs()`.

**New `write_project_manifest(project_dir, project_id, name, created_at)`**:
```python
def write_project_manifest(project_dir: Path, project_id: str, name: str, created_at: str) -> None:
    manifest = {
        "id": project_id,
        "name": name,
        "gt": {
            "srs": "GT/G0_SRS.md",
            "hcs": "GT/G0_HCS.md",
        },
    }
    dest = project_dir / PROJECT_MANIFEST
    dest.parent.mkdir(parents=True, exist_ok=True)
    content = "# Auto-generated — do not edit.\n\n"
    content += yaml.dump(manifest, default_flow_style=False, sort_keys=False)
    dest.write_text(content, encoding="utf-8")
```

### 4. Project identity — UUIDv7

**`src/codeanvil/config/identity.py`** (NEW):
- `generate_uuidv7()` — stdlib-only (~10 lines, `time.time_ns()` + `uuid.uuid4()` random bits). ID generation is a format choice, not a DB concern.

**`src/codeanvil/db/projects.py`**:
- `register_project()` stores the UUID as the primary key (TEXT), not autoincrement INTEGER.
- Add `get_project_by_id(conn, uuid)` returning full row.

**`src/codeanvil/db/schema.py`** — update `projects` table:
```sql
CREATE TABLE IF NOT EXISTS projects (
    id          TEXT PRIMARY KEY,       -- UUIDv7
    name        TEXT NOT NULL,          -- human label, NOT UNIQUE
    path        TEXT NOT NULL,          -- absolute path on THIS machine (local, not shared)
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
```

`path` is local machine state — lives in the DB only, never in `project.yaml`. Discovered at `create` time, updated by `sync` when the project moves.

**`project.yaml`** (committed/shared — no path, no machine-specific data):
```yaml
# Auto-generated — do not edit.

id: 019296a0-7b1c-7d4e-8a3f-1c2d3e4f5a6b
name: ane-lap2
gt:
  srs: GT/G0_SRS.md
  hcs: GT/G0_HCS.md
```

### 5. `codeanvil sync` — the collaboration flow

The real new piece. When someone clones a repo that already has `.codeanvil/project.yaml`:

```bash
cd /path/to/cloned-project
codeanvil sync
```

Flow:
1. Find `.codeanvil/project.yaml` in CWD (or walk up to find it).
2. Read `id` + `name`.
3. Resolve absolute path of the directory containing `.codeanvil/`.
4. Check DB:
   - **id not in DB** → `INSERT (id, name, path)` — “Registered”
   - **id in DB, same path** → no-op — “Already registered”
   - **id in DB, different path** → `UPDATE path` — “Project moved”
5. Print: `Synced: ane-lap2 (019293a4) → /home/bob/dev/ane-lap2`

**`src/codeanvil/db/projects.py`** — new `sync_project(conn, id, name, path)`:
```python
def sync_project(conn, project_id: str, name: str, path: Path) -> str:
    """Register or update a project from its manifest. Returns action taken."""
    existing = conn.execute(
        "SELECT path FROM projects WHERE id = ?", (project_id,)
    ).fetchone()
    
    if existing is None:
        conn.execute(
            "INSERT INTO projects (id, name, path) VALUES (?, ?, ?)",
            (project_id, name, str(path)),
        )
        conn.commit()
        return "registered"
    
    if existing["path"] == str(path):
        return "already registered"
    
    conn.execute(
        "UPDATE projects SET path = ? WHERE id = ?",
        (str(path), project_id),
    )
    conn.commit()
    return "moved"
```

**`src/codeanvil/init/sync.py`** (NEW) — orchestrates the sync flow:
```python
def run_sync(project_dir: Path) -> tuple[str, dict]:
    """Full sync: read manifest, migrate .provenance if needed, upsert DB.
    Returns (action, manifest_data)."""
    manifest = find_manifest(project_dir)
    data = yaml.safe_load(manifest.read_text(encoding="utf-8"))
    _migrate_provenance(project_dir)
    conn = connect_db(DB_PATH)
    action = sync_project(conn, data["id"], data["name"], project_dir.resolve())
    conn.close()
    return action, data

def _migrate_provenance(project_dir: Path) -> None:
    """Pre-release migration: .provenance/ -> .codeanvil/custody/."""
    old = project_dir / ".provenance"
    new = project_dir / ".codeanvil" / "custody"
    if old.is_dir() and not new.exists():
        new.parent.mkdir(parents=True, exist_ok=True)
        old.rename(new)
        log.info("migrated .provenance/ -> .codeanvil/custody/")
```

**`src/codeanvil/CLI/cli.py`** — new `cmd_sync()` (thin dispatch):
```python
def cmd_sync() -> None:
    from codeanvil.config.paths import find_manifest
    from codeanvil.init.sync import run_sync
    manifest = find_manifest(Path.cwd())
    if manifest is None:
        log.error("no .codeanvil/project.yaml found (searched up from cwd)")
        sys.exit(1)
    project_dir = manifest.parent.parent
    action, data = run_sync(project_dir)
    short_id = data["id"][:8]
    print(f"Synced: {data['name']} ({short_id}) → {project_dir.resolve()}  [{action}]")
```

**`find_manifest(start)`** lives in **`src/codeanvil/config/paths.py`** (not cli.py) — `cmd_status`, `cmd_sync`, and future MCP tools all need it:
```python
def find_manifest(start: Path) -> Path | None:
    """Walk up from start looking for .codeanvil/project.yaml."""
    current = start.resolve()
    while True:
        candidate = current / ".codeanvil" / "project.yaml"
        if candidate.is_file():
            return candidate
        parent = current.parent
        if parent == current:
            return None
        current = parent
```

**Argparser** — add `sync` subcommand:
```
codeanvil sync    Register or update a cloned project in the local DB
```

**Use cases**:
- Clone a teammate's repo → `codeanvil sync` → project appears in `codeanvil list`
- Move a project folder → `cd new/location && codeanvil sync` → DB path updated
- Re-scaffold on a new machine → same UUID, `sync` registers it locally

### 6. `codeanvil list` — shows path from DB

The DB stores the local path (set by `create` or `sync`), so `list` can show it:

```
  [019296a0] ane-lap2  —  /home/bob/dev/ane-lap2  (2026-10-21 16:23:45)
```

Short UUID prefix (first 8 chars) for display. Full UUID available via `codeanvil status`.

### 7. `codeanvil now --machine` — filename-safe timestamp

The tool owns the timestamp format. Agents call `codeanvil now` for human-readable text and `codeanvil now --machine` for filenames.

```bash
codeanvil now              # 2026-10-21 16:23:45.123  (human, for report content)
codeanvil now --machine    # 2026-10-21_16-23-45-123  (filename-safe, for file creation)
```

**`src/codeanvil/config/time.py`** — new `format_timestamp_machine()`:
```python
def format_timestamp_machine(dt: datetime | None = None, tz_name: str | None = None) -> str:
    """Filename-safe timestamp: colons and spaces replaced."""
    human = format_timestamp(dt, tz_name)
    return human.replace(" ", "_").replace(":", "-")
```

**`src/codeanvil/CLI/cli.py`** — update `cmd_now`:
```python
def cmd_now(tz: str | None = None, machine: bool = False) -> None:
    from codeanvil.config.time import format_timestamp, format_timestamp_machine
    if machine:
        print(format_timestamp_machine(tz_name=tz))
    else:
        print(format_timestamp(tz_name=tz))
```

**Argparser** — add `--machine` flag to `now`:
```python
now_parser.add_argument(
    "--machine",
    action="store_true",
    help="Filename-safe format (no colons or spaces)",
)
```

**Report filename convention** (agent-side):
```
.codeanvil/report/<gate>_$(codeanvil now --machine).md
```
Example: `G0_2026-10-21_16-23-45-123.md`

### 8. `codeanvil create` flow — updated

```python
def cmd_create(name, path, mcp_servers=None):
    ...
    project_dir = scaffold_project(name, path, mcp_servers=...)
    project_id = generate_uuidv7()
    register_project(conn, project_id, name, project_dir)  # path stored in DB
    write_project_manifest(project_dir, project_id, name)  # path NOT in manifest
```

The manifest is committed to git. The DB row is local. Same UUID everywhere.

### 9. `.provenance/` → `.codeanvil/custody/`

**`templates/skills/custody-chain/SKILL.md`**:
- `.provenance/` → `.codeanvil/custody/` in all examples and instructions.
- `GT/**` include patterns stay as `GT/**` (GT is still at root).

**`templates/skills/custody-chain/scripts/source_snapshot.py`**:
- `DEFAULT_EXCLUDE` — change `.provenance/` to `.codeanvil/`.
- Default `--out` path in docstring: `.provenance/snapshot.json` → `.codeanvil/custody/snapshot.json`.

**`templates/skills/custody-chain/scripts/custody_ledger.py`**:
- Default `--ledger` path: `.provenance/custody.jsonl` → `.codeanvil/custody/custody.jsonl`.

**`templates/skills/custody-chain/assets/controls.example.json`**:
- `.provenance/snapshot.json` → `.codeanvil/custody/snapshot.json`.

### 10. DB — slim down to registry only

**Drop `sessions` and `gate_results` tables.** Nothing populates them. Gate progress moves to `.codeanvil/report/` as markdown files.

**Keep `projects` table** — minimal registry (id, name, created_at).

**`src/codeanvil/db/schema.py`** — remove `sessions` and `gate_results` from `_SCHEMA`.

**`src/codeanvil/db/sessions.py`** — **delete** (dead code).

### 11. Report format — timestamped markdown

Reports in `.codeanvil/report/` use the `codeanvil now` timestamp format.

**Filename convention**:
```
.codeanvil/report/<gate>_<timestamp>.md
```
Examples:
```
G0_2026-10-21_16-23-45-123.md
custody_2026-10-21_16-24-01-456.md
G1_2026-10-21_17-00-00-789.md
```

**Content**: gate name, result (PASS/FAIL), findings, iteration number. Human-readable markdown. Must include `codeanvil now` timestamp at the top.

**Filename**: `<gate>_$(codeanvil now --machine).md`. The agent calls the CLI to get the timestamp — never generates it independently.

**Stage tracking**: latest report file per gate = current project stage. `codeanvil status` reads these files.

### 12. `codeanvil status` — read from report dir (with auto-sync)

**`src/codeanvil/CLI/cli.py`** — `cmd_status`:
- Two modes:
  - `codeanvil status` (no args) — reads from CWD's `.codeanvil/report/`.
  - `codeanvil status <name>` — looks up path in DB, reads from `<path>/.codeanvil/report/`.
- **Auto-sync**: if `find_manifest()` finds a `project.yaml` and the ID isn't in the DB, call `sync_project()` silently before printing. Agents run `status` constantly; requiring a separate `sync` first is friction that'll generate bugs.
- List markdown report files sorted by timestamp, show latest per gate.
- Also show project identity from `project.yaml` (id, name).

### 13. TEMPLATE_AGENT.md — timestamp mandate

The generated `AGENTS.md` must instruct agents to use `codeanvil now` for all timestamps:

```markdown
## Timestamps

- For report **content** (human-readable text): `codeanvil now`
- For **filenames** and machine identifiers: `codeanvil now --machine`
- Do NOT generate timestamps any other way. The tool owns the format.

## Report creation

After each gate run, write a report to `.codeanvil/report/`:

    GATE=$(gate name, e.g. G0)
    TIMESTAMP=$(codeanvil now --machine)
    # Write to: .codeanvil/report/${GATE}_${TIMESTAMP}.md

Report content must include a human-readable timestamp from `codeanvil now`
at the top of the file.
```

**`templates/AGENTS/TEMPLATE_AGENT.md`** — add this section to the orchestration block.

### 14. Templates and docs — update paths

**`templates/AGENTS/TEMPLATE_AGENT.md`**:
- `.provenance/` → `.codeanvil/custody/`.
- GT/ references stay as-is (GT still at root).
- Update directory tree diagram.

**`templates/GT/README.md.template`** — no change needed (GT stays at root).

**`AGENTS.md` (repo root)** — update scaffolded project structure diagram.

**`templates/config.yaml`** — update `path_replacements`:
```yaml
path_replacements:
  "templates/skills/": ".agents/skills/"
  "templates/GT/G0_SRS.md": ".agents/skills/G0_valid_req_and_GT/templates/G0_SRS.md"
  "templates/GT/G0_HCS.md": ".agents/skills/G0_valid_req_and_GT/templates/G0_HCS.md"
  "(repository-root relative)": "(project-root relative)"
  ".provenance/": ".codeanvil/custody/"
```

## What does NOT change

- **GT/ at project root** — stays visible, prominent, user-authored.
- **`.agents/skills/G0_.../templates/`** — GT reference templates stay inside the skill only.
- **`.agents/skills/`** — canonical skill store, symlinks. Untouched.
- **g0_validate.py** — path-agnostic (CLI args). No change.
- **MCP wiring** — unchanged (just lives under `~/.codeanvil-config/mcp/` now).

## Files to modify

| File | Change |
|------|--------|
| `src/codeanvil/config/paths.py` | `WORKDIR` → `~/.codeanvil-config/`; add `PROJECT_CODEANVIL`, `PROJECT_CUSTODY`, `PROJECT_REPORT`, `PROJECT_MANIFEST`; add `find_manifest()` (walk-up search) |
| `src/codeanvil/init/create.py` | Add `_create_codeanvil_dirs()`; add `write_project_manifest()`; update `scaffold_project()` |
| `src/codeanvil/db/schema.py` | Drop `sessions`/`gate_results`; update `projects` table (TEXT id, no path, name not unique) |
| `src/codeanvil/db/sessions.py` | **Delete** |
| `src/codeanvil/config/identity.py` | **New**: `generate_uuidv7()` (stdlib-only) |
| `src/codeanvil/init/sync.py` | **New**: `run_sync()` orchestration + `_migrate_provenance()` auto-migration |
| `src/codeanvil/db/projects.py` | Update `register_project()` signature; add `get_project_by_id()`, `sync_project()` (DB upsert) |
| `src/codeanvil/CLI/cli.py` | Add `cmd_sync` (thin); update `cmd_create` flow; update `cmd_status` (auto-sync + report dir); update `cmd_list`; remove sessions import |
| `src/codeanvil/config/time.py` | New `format_timestamp_machine()` |
| `install.sh` | Update `~/.codeanvil` references to `~/.codeanvil-config` |
| `templates/config.yaml` | Add `.provenance/` → `.codeanvil/custody/` replacement |
| `templates/AGENTS/TEMPLATE_AGENT.md` | `.provenance/` → `.codeanvil/custody/`; update tree diagram |
| `templates/skills/custody-chain/SKILL.md` | `.provenance/` → `.codeanvil/custody/` |
| `templates/skills/custody-chain/scripts/source_snapshot.py` | `DEFAULT_EXCLUDE`, docstring paths |
| `templates/skills/custody-chain/scripts/custody_ledger.py` | Docstring default paths |
| `templates/skills/custody-chain/assets/controls.example.json` | `.provenance/` → `.codeanvil/custody/` |
| `AGENTS.md` (repo root) | Scaffolded project structure diagram; update `~/.codeanvil/` → `~/.codeanvil-config/`, `.provenance/` → `.codeanvil/custody/`, drop `sessions.py` references |

## Verification

```bash
# Verify global config rename
codeanvil init
ls ~/.codeanvil-config/db/codeanvil.db

# Clean scaffold
codeanvil create testproj -p /tmp

# Verify GT/ at project root (NOT moved)
ls /tmp/testproj/GT/
# README.md

# Verify .codeanvil/ structure
ls -R /tmp/testproj/.codeanvil/
# project.yaml  custody/  report/

# Verify NO .codeanvil/GT/ (GT stays at root)
test -d /tmp/testproj/.codeanvil/GT && echo "FAIL" || echo "PASS"

# Verify project.yaml has UUIDv7, no path
cat /tmp/testproj/.codeanvil/project.yaml
# id: 019296a0-...
# name: testproj
# gt:
#   srs: GT/G0_SRS.md
#   hcs: GT/G0_HCS.md

# Verify .provenance/ does NOT exist
test -d /tmp/testproj/.provenance && echo "FAIL" || echo "PASS"

# Verify GT templates still inside skill only
ls /tmp/testproj/.agents/skills/G0_valid_req_and_GT/templates/
# G0_SRS.md  G0_HCS.md

# Test sync flow (simulates cloning)
cp -r /tmp/testproj /tmp/cloned-proj
cd /tmp/cloned-proj
codeanvil sync
# Should print: Synced: testproj (019296a0) → /tmp/cloned-proj  [registered]
codeanvil list
# Local DB, one machine — same UUID = project moved, path updated.

# Test project-moved flow
mv /tmp/testproj /tmp/testproj-moved
cd /tmp/testproj-moved
codeanvil sync
# Should print: Synced: testproj (019296a0) → /tmp/testproj-moved  [moved]

# Copy real GT and run G0
cp methodology/test/T0_ANE-Lap2/just-edge/SRS.md /tmp/testproj/GT/G0_SRS.md
cp methodology/test/T0_ANE-Lap2/just-edge/HCS.md /tmp/testproj/GT/G0_HCS.md
cd /tmp/testproj
python .agents/skills/G0_valid_req_and_GT/scripts/g0_validate.py GT/G0_SRS.md GT/G0_HCS.md
# Should PASS

# Verify no stale paths
grep -rn "\.provenance" /tmp/testproj/AGENTS.md && echo "FAIL" || echo "PASS"
```

## Migration notes

- **Global config rename**: `ensure_dirs()` checks if `~/.codeanvil/` exists and `~/.codeanvil-config/` doesn't → moves it automatically. One-time migration.
- **DB schema**: existing `sessions`/`gate_results` tables are empty. `projects` table changes schema (TEXT id, no path, name not unique). Since this is pre-release, drop and recreate is acceptable. For safety, `codeanvil init` can detect old schema and re-create.
- **Existing scaffolded projects**: still have `GT/` at root (good), still have `.provenance/` (stale). Pre-release — `codeanvil sync` auto-migrates: if `.provenance/` exists and `.codeanvil/custody/` doesn't, rename it and print one line. No ambiguity.

## Module layout after refactor

```
src/codeanvil/
├── CLI/cli.py              ← dispatch only (thin)
├── config/
│   ├── paths.py            ← + find_manifest(), PROJECT_* constants
│   ├── time.py             ← + format_timestamp_machine()
│   ├── identity.py         ← NEW: generate_uuidv7()
│   └── logger.py           ← unchanged
├── db/
│   ├── projects.py         ← + sync_project() (DB upsert only)
│   ├── schema.py           ← slimmed (drop sessions/gate_results)
│   └── utils.py            ← unchanged
├── init/
│   ├── create.py           ← + _create_codeanvil_dirs(), write_project_manifest()
│   ├── sync.py             ← NEW: run_sync() + _migrate_provenance()
│   ├── check.py            ← unchanged
│   └── mcp.py              ← unchanged
└── UI/                     ← unchanged
```

`db/sessions.py` deleted. New files: `config/identity.py`, `init/sync.py`.

## Dependencies

- **UUIDv7**: Python 3.12 has no native UUIDv7. Stdlib-only implementation in `config/identity.py`: combine `time.time_ns()` with `uuid.uuid4()` random bits — ~10 lines, zero deps.

# Plan: Project Scaffold CLI — Full Flow

## Context

G0 skill is implemented and tested. The next step is making it work **in user projects** — not just from the CodeAnvil repo root. The test with `claude --safe-mode` proved the skill works when copied to `.claude/skills/`, but the current `scaffold_project()` copies to `project_dir/skills/` (wrong), SKILL.md has hardcoded repo-root paths, and there's no `pyproject.toml` to install the CLI.

The full flow: author skills in `templates/` → `codeanvil create` scaffolds a project anywhere → GT templates + skills copied with correct paths → DB tracks the project → user runs an AI agent that discovers the skills natively.

## What exists and works

| Component | File | Status |
|-----------|------|--------|
| CLI (init, create, list, status) | `src/codeanvil/CLI/cli.py` | Functional, 4 subcommands |
| `scaffold_project()` | `src/codeanvil/init/create.py` | Works but copies to wrong dirs, copies `__pycache__`, no path rewriting |
| `register_project()` | `src/codeanvil/init/create.py` | Works |
| DB schema (projects, sessions, gate_results) | `src/codeanvil/db/schema.py` | Works |
| Session CRUD | `src/codeanvil/db/sessions.py` | Works, but nothing calls `create_session()` yet |
| Preflight checks | `src/codeanvil/init/check.py` | Works |
| Logger | `src/codeanvil/config/logger.py` | Works |
| Paths config | `src/codeanvil/config/paths.py` | Works (`~/.codeanvil/`) |
| g0_validate.py | `templates/skills/G0_valid_req_and_GT/scripts/` | Works, path-agnostic (takes CLI args) |
| SKILL.md (G0) | `templates/skills/G0_valid_req_and_GT/SKILL.md` | Works but has hardcoded repo-root paths |

## What's missing

1. **`pyproject.toml`** — package can't be installed, `codeanvil` command doesn't exist
2. **Skill directory convention** — scaffold copies to `project_dir/skills/`, should be `.agents/skills/` with symlinks for `.claude/skills/`, `.opencode/skills/`, `.codex/skills/`
3. **Path rewriting in SKILL.md** — repo-root paths need to become project-relative during copy
4. **`__pycache__` exclusion** — `shutil.copytree` copies `.pyc` files
5. **GT templates in wrong place** — scaffold copies GT templates to `project_dir/GT/` as user-editable files; they should be locked reference templates inside the skill at `.agents/skills/G0_.../templates/`

## Implementation

### 1. Create `pyproject.toml`

Minimal PEP 621 config at repo root:

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "codeanvil"
version = "0.1.0"
requires-python = ">=3.10"

[project.scripts]
codeanvil = "codeanvil.CLI.cli:main"
```

Add a `main()` function to `cli.py` that calls `choose_option(argparser())` — entry point for the console script.

**File**: new `pyproject.toml` at repo root.  
**File**: edit `src/codeanvil/CLI/cli.py` — add `main()`.

### 2. Fix `scaffold_project()` — skill directory + symlinks + GT inside skills

Rewrite `src/codeanvil/init/create.py`:

**GT templates are NOT user files.** They are locked reference artifacts that belong inside each skill. The user never edits them — the validator and the agent read them to know the expected structure.

**Skills copy** — destination is `.agents/skills/`, exclude `__pycache__` and `valid_structure_SRS.py` (legacy empty):
```
templates/skills/G0_valid_req_and_GT/  →  project_dir/.agents/skills/G0_valid_req_and_GT/
templates/skills/G1_start_design/      →  project_dir/.agents/skills/G1_start_design/
```

Use `shutil.copytree` with `ignore=shutil.ignore_patterns('__pycache__', '*.pyc', 'valid_structure_SRS.py')`.

**GT templates inside the skill** — copy the IEEE 29148 templates into the G0 skill:
```
templates/GT/G0_SRS.md  →  project_dir/.agents/skills/G0_valid_req_and_GT/templates/G0_SRS.md
templates/GT/G0_HCS.md  →  project_dir/.agents/skills/G0_valid_req_and_GT/templates/G0_HCS.md
```

These are reference-only. The user writes their own GT files (SRS.md, HCS.md) at the project root or wherever they choose, then points the validator at them.

**User GT directory** — create an empty `GT/` with a short README explaining what goes here:
```
project_dir/GT/           ← user writes SRS.md, HCS.md here
project_dir/GT/README.md  ← "Write your GT files here. See .agents/skills/G0_.../templates/ for the expected structure."
```

**Agent symlinks** — after copying skills, create symlinks for each known agent runtime:
```python
AGENT_SKILL_DIRS = [".claude/skills", ".opencode/skills", ".codex/skills"]

for agent_dir in AGENT_SKILL_DIRS:
    link = project_dir / agent_dir
    link.parent.mkdir(parents=True, exist_ok=True)
    link.symlink_to(project_dir / ".agents" / "skills")
```

Each symlink points to the canonical `.agents/skills/` so all runtimes discover the same skills.

**File**: edit `src/codeanvil/init/create.py`.

### 3. Path rewriting in SKILL.md

SKILL.md currently references repo-root paths. After copy, rewrite to project-relative paths:

| Repo path | Project path |
|-----------|--------------|
| `python templates/skills/G0_.../scripts/g0_validate.py` | `python .agents/skills/G0_.../scripts/g0_validate.py` |
| `templates/GT/G0_SRS.md` | `.agents/skills/G0_valid_req_and_GT/templates/G0_SRS.md` |
| `templates/GT/G0_HCS.md` | `.agents/skills/G0_valid_req_and_GT/templates/G0_HCS.md` |

Also `references/RULES.md` has the same patterns.

**Approach**: after `copytree`, do text replacement on every `.md` file in the copied skill tree:

```python
PATH_REPLACEMENTS = {
    "templates/skills/": ".agents/skills/",
    "templates/GT/G0_SRS.md": ".agents/skills/G0_valid_req_and_GT/templates/G0_SRS.md",
    "templates/GT/G0_HCS.md": ".agents/skills/G0_valid_req_and_GT/templates/G0_HCS.md",
}
```

**File**: edit `src/codeanvil/init/create.py` — add `_rewrite_skill_paths()`.

### 4. Scaffold output structure

After `codeanvil create myproj`, the directory looks like:

```
myproj/
├── GT/
│   └── README.md               ← instructions: write SRS.md, HCS.md here
├── .agents/
│   └── skills/
│       ├── G0_valid_req_and_GT/
│       │   ├── SKILL.md              ← paths rewritten to project-relative
│       │   ├── templates/            ← locked IEEE 29148 reference templates
│       │   │   ├── G0_SRS.md
│       │   │   └── G0_HCS.md
│       │   ├── references/
│       │   │   └── RULES.md          ← paths rewritten
│       │   └── scripts/
│       │       └── g0_validate.py
│       └── G1_start_design/
│           ├── SKILL.md
│           └── scripts/
├── .claude/
│   └── skills -> ../.agents/skills
├── .opencode/
│   └── skills -> ../.agents/skills
└── .codex/
    └── skills -> ../.agents/skills
```

### 5. No `codeanvil run` in this phase

The user asked for: skill authoring → CLI scaffold → DB persistence → skill copy logic. Gate execution (`codeanvil run`) is a separate phase — it needs the orchestrator described in AGENTS.md. Sessions CRUD already exists in `db/sessions.py` and is ready when that phase comes.

## Files to modify

1. **New**: `pyproject.toml` (repo root)
2. **Edit**: `src/codeanvil/CLI/cli.py` — add `main()` entry point
3. **Edit**: `src/codeanvil/init/create.py` — rewrite `scaffold_project()` with correct dirs, `__pycache__` exclusion, path rewriting, symlinks

## Verification

```bash
# Install
uv pip install -e .

# Init
codeanvil init

# Scaffold
codeanvil create testproj -p /tmp

# Verify structure
find /tmp/testproj -type f -o -type l | sort

# Verify symlinks resolve correctly
ls -la /tmp/testproj/.claude/skills
ls -la /tmp/testproj/.opencode/skills
ls -la /tmp/testproj/.codex/skills

# Verify GT templates are inside the skill (locked, not in GT/)
ls /tmp/testproj/.agents/skills/G0_valid_req_and_GT/templates/
# Should show G0_SRS.md, G0_HCS.md

# Verify GT/ has only README (user writes their own files here)
ls /tmp/testproj/GT/
# Should show only README.md

# Verify path rewriting — no repo-root paths left
grep -rn "templates/skills/" /tmp/testproj/.agents/skills/G0_valid_req_and_GT/SKILL.md
# Should return nothing
grep -rn "templates/GT/" /tmp/testproj/.agents/skills/G0_valid_req_and_GT/SKILL.md
# Should return nothing

# Verify no __pycache__
find /tmp/testproj -name __pycache__
# Should return nothing

# Copy real GT files and run G0
cp methodology/test/T0_ANE-Lap2/just-edge/SRS.md /tmp/testproj/GT/
cp methodology/test/T0_ANE-Lap2/just-edge/HCS.md /tmp/testproj/GT/
cd /tmp/testproj
python .agents/skills/G0_valid_req_and_GT/scripts/g0_validate.py GT/SRS.md GT/HCS.md
# Should exit 0 (PASS)

# Verify DB registration
codeanvil list
# Should show testproj

# Test with Claude (agent discovers skill via symlink)
cd /tmp/testproj && claude --safe-mode
# Prompt: "Read .claude/skills/G0_valid_req_and_GT/SKILL.md and execute G0 on GT/SRS.md and GT/HCS.md"
```

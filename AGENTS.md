# CodeAnvil — Agent Architecture

## Overview

CodeAnvil implements the V-SIL pipeline as a chain of gates — G0 is deterministic, G1+ are AI coding agents. The harness is **agent-agnostic**: it works with any coding agent runtime (Claude, Codex, OpenCode, Pi, etc.). `src/` scaffolds and tracks state.

**Scope**: software development, testing, and validation on COTS hardware (not necessarily OOTB). Does not design hardware — assumes commercial off-the-shelf devices, validates software against GT constraints.

```
codeanvil init ────► ~/.codeanvil/ (config + SQLite DB only)
codeanvil create ──► scaffold project anywhere (GT templates + skills)
codeanvil run ─────► orchestrator
                       │
                       ├─ G0 (deterministic — no agent)
                       │    ├─ reads: 3 GT .md files
                       │    ├─ script: valid_structure.py
                       │    ├─ checks: required sections, format, fields
                       │    └─ output: pass/fail (hard gate)
                       │
                       ├─ G1 Agent (start design)
                       │    ├─ reads: validated GT + G0 report
                       │    ├─ skill: SKILL.md
                       │    └─ output: design artifacts
                       │
                       ├─ G2 Agent (...)
                       └─ ...
```

## Test GT cases (V-SIL system inputs)

`methodology/test/T<n>_<name>/` — numbered test cases containing real-world project materials (proposals, papers, design docs) from which the 3 GT files are derived. They are the methodology's integration tests: each T# exercises the full pipeline from raw inputs through G0 validation and into agent-driven gates.

| Test | Domain | Contents |
|------|--------|----------|
| **T1_FM-monitoring** | SDR-based FM broadcast compliance monitoring | LaTeX specification (RAG-informed from FCC Part 73, ANE Res. 105, ITU-R BS.412/450/SM.2152, ISO/IEC 17025), DSP pipeline design, compliance measurands, uncertainty budgets |
| **T2_IoT-Indoor** | Indoor IoT radio environment mapping, 2.4 GHz ISM (Proyecto Hermes / GCPDS) | Hermes proposal, radio environment mapping literature, variable adaptation design doc |

## Gate details

### G0 — Validate GT Structure (deterministic, no agent)

Pure Python script. No LLM, no AI agent — just `valid_structure.py`.

- **Purpose**: hard gate ensuring each GT `.md` file has the required structure before any agent gate runs.
- **Script**: `templates/skills/G0_valid_req_and_GT/scripts/valid_structure.py`
- **Spec**: `SKILL.md` documents the expected structure for each GT file.
- **Inputs** (3 pre-processed `.md` files, human-authored):
  1. **Requirements** — functional and non-functional requirements
  2. **HW Restrictions** — COTS hardware constraints (embedded, server, DAQ/SDR)
  3. **Normativity** — applicable standards (ITU, ICNIRP, IEEE, etc.)
- **Output**: pass/fail with exact listing of missing/malformed sections.
- **Property**: deterministic — same input, same result. No interpretation.

### G1 — Start Design (agent-driven)

- **Purpose**: initiate design phase once GT is validated.
- **Skill**: `templates/skills/G1_start_design/SKILL.md`
- **Inputs**: validated GT + G0 pass report
- **Output**: initial design artifacts (architecture, interfaces, GT-derived constraints)

## Orchestrator (planned)

- Loads session from DB (`db/sessions.py`)
- Determines next gate from `sessions.current_gate`
- G0: runs `valid_structure.py` directly
- G1+: spawns AI coding agent with `SKILL.md` + GT context (any supported runtime)
- Records result via `record_gate_result()`
- Advances gate via `update_gate()` on pass

## Agent contract

Each gate agent (G1+), regardless of runtime:

1. Receives `SKILL.md` as instructions
2. Receives the project's GT documents as context
3. Executes validation, generation, or review per the skill
4. Returns structured output (pass/fail, findings, artifacts)

Agents are **stateless** and **runtime-agnostic** — all persistence is in the DB and GT files. Any coding agent that reads markdown and executes scripts can run a gate. Re-runnable without side effects.

## MCP servers (planned)

- **Project DB** — query sessions, gate results, project metadata
- **GT access** — read/write GT documents with schema validation
- **CI bridge** — trigger and read SIL regression results

## Adding a new gate

1. Create `templates/skills/G<n>_<name>/SKILL.md`
2. Add validation scripts under `scripts/` if needed
3. Register the gate in the orchestrator's sequence
4. Update DB schema if the gate produces new artifact types

## Principles

- **GT is pre-processed input**: 3 human-authored `.md` files, not raw PDFs.
- **G0 is deterministic**: no AI, no interpretation. Valid or not.
- **Gates are sequential**: G(n+1) requires G(n) pass.
- **Skills are the methodology**: not in `SKILL.md` (or G0 script) → not in V-SIL.
- **GT is the contract**: agents validate against GT, never assumptions.
- **Agents are stateless**: re-runnable, same GT → same result.
- **`src/` serves `templates/`**: the tool delivers the methodology, not the other way around.

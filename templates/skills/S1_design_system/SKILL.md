---
name: s1-design-system
description: "Trigger: S1, design subsystems, architecture, subsystem topology, contracts, stubs, dependency graph. From a passed G0 pair, write the S1 design document (layered subsystems, contracts with stubs, traceability, decisions, risks) and its dependency graph."
license: Apache-2.0
compatibility: "No network access, no scripts. Reads .codeanvil/GT/StRS.md, .codeanvil/GT/SyRS.md and .codeanvil/project.yaml. Writes .codeanvil/design/SDD.md, .codeanvil/design/dependency_graph.html (dark), .codeanvil/design/dependency_graph_light.html and .codeanvil/report/<cycle-name>/S1.md."
metadata:
  author: "gcpds"
  version: "1.0"
  gate: "S1"
  pipeline: "V-SIL"
---

# S1 — Design of a System of Layered Subsystems

Produce one design document that resolves every implementation-critical decision: subsystem
topology, a layered base and modules per subsystem, contracts with stubs, traceability and system
paths. One subsystem is a valid special case. A human reviews the result at G1.

## Prerequisite and Cycle

Resolve the active cycle from `.codeanvil/project.yaml` (`cycle:`); if missing, ask the user.
If the latest iteration of `.codeanvil/report/<cycle-name>/RFD.md` holds a line
`Superseded by cycle: <name>`, this cycle is **closed** by an RFD and read-only: return exactly
`Cycle closed by RFD. Continue in cycle <name>.` and write nothing. Otherwise check, in this order,
writing **no iteration** when you stop:

1. `.codeanvil/report/<cycle-name>/G0.md` is missing or its latest iteration is not
   `HITL: PASS`: return exactly `G0 must pass first. Run the G0 skill.`
2. `codeanvil status` marks `G0` or any earlier report of the cycle `stale`: return the same
   line, naming the earliest stale report.
3. S1's own latest iteration is `FEEDBACK` with `Verdict: RFD`: return exactly
   `Cycle suspended by RFD. Run the RFD skill.`, unless the latest `RFD.md` iteration states
   `Outcome: Withdrawn`, in which case continue.

When S1 already delivered and nothing asks for rework, say so and point to the G1 skill. Rework
is requested by a `G1.md` iteration with `FEEDBACK` (named sections to rework), by an `S2.md` or
`G2.md` iteration with `FEEDBACK` and the line `Verdict: design defect` naming the sections to
rework, or by the user.

## Inputs and Outputs

| | Path | Notes |
|---|------|-------|
| Input | `.codeanvil/GT/StRS.md`, `.codeanvil/GT/SyRS.md` | Read-only |
| Input | `.codeanvil/project.yaml` | Read-only; its keys are copied as text into the graph |
| Input (optional) | Supplied ML package | Only if the design uses ML or the GT requires it |
| Input (rework) | Latest `G1.md` FEEDBACK, or `S2.md` / `G2.md` FEEDBACK with `Verdict: design defect` | Named sections to rework |
| Template | `templates/skills/S1_design_system/references/SDD.md` | This skill's locked template |
| Output | `.codeanvil/design/SDD.md` | Overwritten on rework |
| Output | `.codeanvil/design/dependency_graph.html` | Dark dependency graph; overwritten on rework |
| Output | `.codeanvil/design/dependency_graph_light.html` | Light dependency graph; same design data; overwritten on rework |
| Output | `.codeanvil/report/<cycle-name>/S1.md` | Iterative report: the only state of this stage |

Working files live in `.codeanvil/design/`, outside the cycle report folder.

## Hard Rules

- **Never edit GT.** A GT gap goes to design §6 as a risk, or follows the RFD route.
- Modules talk only through their subsystem's base. No cross-subsystem call bypasses a versioned contract.
- Split subsystems only when they deploy or restart independently, communicate over a network, or
  have distinct failure domains.
- `hw_dependency: true` means `required_vl: VL-2`. Running on a computer does not count as a
  hardware dependency.
- **HAL mode** (Meta) is `mock-only` unless the GT or the user requires real hardware this cycle.
  In `mock-only`, no module has `hw_dependency: true`, so the highest `required_vl` is VL-1, there
  is no Real HW HAL, and SyRS §4–§6 are not read.
- In `mock+real`, design Real HW HAL tests against the actual `SYS-*` criteria, with a method
  and resolution justified for each tolerance. Cite SyRS `PROTO-*`, corrections, calibration and
  uncertainty when the requirement or conclusion needs them; functional tests need no formal
  oracle by default. Do not invent missing calibration or widen tolerances. A required lab input
  absent from GT is a risk to resolve, not a reason to block unrelated functional measurements.
  Design device identity/driver/capability observation, a guard rejecting unsupported settings
  before configuration, and safe stop/disconnect. Record the agent's measurement scripts in the
  kit contract; real hardware runs require the pre-HW review checkpoint in S2/G2.
- The Mock HAL (§1.6) and the Telemetry companion (§1.7) are always designed. The Telemetry
  companion lives in `verification/telemetry/`: it is never a module and never under `src/`.
- **Target(s)** (Meta) is **design intent**: it maps every subsystem and verification path to
  `local` or to the intended device, **deduced from the `HWC-*` blocks** of the StRS. It is not a
  `.codeanvil/project.yaml` `targets:` entry. When several devices could apply, resolve the
  selection from GT or ask the user; never pick the first silently. S1 never enrolls a target and
  never writes or asks for credentials, IP or MAC: the concrete `project.yaml` target entry is
  created later, at G2, by `credential-setup`, and only if the design requires VL-2. In §1.6 name
  where each level runs and in §1.7 give an operating envelope per target, sourced from its COTS
  constraints. Missing target intent or limits are design risks to resolve, never guessed values.
- Verification ladder: VL-0 and VL-1 run **locally with no hardware** (Mock HAL, and in `mock+real`
  the Real HW HAL against a fake device API). VL-2 is real SIL/HIL on the actual hardware at G2.
  Remote PIL at S2 is out of scope: do not design a remote deployment for VL-0/VL-1. Do not ask
  the user to invent a target alias or put local private key paths in shared project metadata.
- Execution location and HAL mode are separate axes. VL-0/VL-1 with Mock HAL inputs run locally
  and remain **VERIFIED**; they do not establish VL-2 or real-RF validation. Real-hardware
  execution happens at G2 through `vsil_hil_mcp`; local execution uses the runtime's normal tools.
- **Toolchain** (Meta) names, per subsystem, `SUB-xxx: <package> · <language> · <package manager> ·
  <test runner>`, using only `Python · uv · pytest` or `TypeScript · pnpm · vitest`. `<package>`
  is a valid identifier and names `src/<package>/`. Derive it from §1.3.1 and the deployment
  target; ask the user only when the GT and the orchestration mechanism leave it open.
- Keep the implementation DAG and the runtime interaction graph separate. A cross-subsystem
  contract is defined before both subsystems and is never drawn as a mutual dependency.
- Every contract is complete enough to write a deterministic stub without asking the designer.
- Omit design §1.5 entirely when no ML is used. Never train or select a model. When used, record its
  training source: Mock HAL (a software signal generator behind the HAL port) data plus labelling or,
  failing that, real-hardware HAL data plus labelling.
- Ask the user only when a choice cannot be derived from the GT.

## Steps (one pass)

1. **Back up before overwriting.** Run `codeanvil backup S1` from the project root. If it exits
   nonzero, stop and show its message; write no iteration. Cite the printed backup path in the
   iteration's Description. Backups never cover `src/` or `verification/`: code recovery relies
   on git.
2. Copy the template to `.codeanvil/design/SDD.md`. Record the GT digests in the Meta
   "G0 approved" row (information only, never a block), computed with:
   `python -c "import hashlib,sys;[print(hashlib.sha256(open(p,'rb').read()).hexdigest(),p) for p in sys.argv[1:]]" .codeanvil/GT/StRS.md .codeanvil/GT/SyRS.md`
3. Allocate `SYS-*` to subsystems and paths: §0.4, §1.1, §4.1.
4. Fill the COTS envelope from the `HWC-*` blocks: §0.1–0.3. In §0.5, define
   one project-root command that starts the complete runnable system, its HAL
   mode, processes, URL, visible result and clean shutdown.
5. For each subsystem: its base (§1.3) and module cards (§1.4), each with the full verification profile.
   Set `Target(s)`, `HAL mode` and `Toolchain` in the Meta, then fill the verification kit (§1.3.4), the HAL
   substitution ladder (§1.6) and the Telemetry companion (§1.7).
6. Draw the implementation DAG and topological order (§2.1–2.2) and the runtime graph (§2.3).
7. Write the contracts with stub or fake-peer recipes and vectors (§3).
8. Complete traces and `PATH-*` (§4).
9. Record decisions with real alternatives (§5; DEC-001 is the partitioning decision) and risks (§6).
10. Reread the design against this short list and fix what you find: no `{{` left, every `SYS-*`
    traced, every contract with a recipe, `hw_dependency: true` at `VL-2`, no cycle in the build
    order, `HAL mode` set, `Toolchain` and `Target(s)` set for every subsystem, kit table complete,
    §1.6 execution targets resolved and §1.7 present for every target.
    This is a courtesy to the reviewer, not a gate.
11. Build both dependency graph versions (next section).
12. Write the iteration with the row `| HITL | PASS |` and both graph paths in the Description.
    Return the design path and `S1 complete. Run the G1 skill.`

## Rework (bounded)

On rework, the old baseline is the folder printed by `codeanvil backup S1` and cited in the
iteration's Description. Change only what the feedback names, and record the change so G1 can
review its impact instead of re-reading the whole design:

1. Write a **design change set** in the iteration's Description: one row per changed `SYS-*`,
   contract, subsystem, module or `PATH-*` ID, with the old decision, the new decision, the reason
   and whether the interface changed. A graph-only change is marked `no code impact`.
2. Keep the IDs of unchanged elements stable. Renumbering hides the impact from G1.
3. Record the SHA-256 of the final `SDD.md`:
   `python -c "import hashlib,sys;print(hashlib.sha256(open(sys.argv[1],'rb').read()).hexdigest())" .codeanvil/design/SDD.md`

## Infeasibility

If the design shows that no partitioning can meet a requirement on the declared COTS platform
(for example, pipeline latency exceeds the requirement under any partitioning on this hardware),
do not hide it: run the RFD skill with `ANALYSIS (no VL)` evidence, and write the iteration with
`| HITL | FEEDBACK |` and the Description line `Verdict: RFD` naming the RFD. A rework after G1
passed makes `codeanvil status` mark G1 stale, so the design is reviewed again before S2.

## Dependency Graph

The graph is a reading aid: **a full dependency graph, each subsystem drawn as a spider** (its
base at the center, its modules on the spokes), delivered as dark and light HTML files using
vis-network, with the manifest as text to tell designs apart. Their palette follows CodeAnvil's
forge UI: ember accents, steel surfaces, cyan and green functional layers.

Copy `templates/skills/S1_design_system/references/dependency_graph_template.html` to
`.codeanvil/design/dependency_graph.html` with `const theme = 'dark'` and to
`.codeanvil/design/dependency_graph_light.html` with `const theme = 'light'`.
Change **only the `DATA` block at the top**. Both copies must have identical manifest,
subsystems, hardware and subsystemContracts data; only `theme` differs. Never edit below it and
never write the pages by hand: the fixed rendering code makes
every agent runtime draw the same graph. It loads `assets/vis-network.min.js` from this skill's
own folder by relative path, so it needs no network, but it must stay inside the project.

| `DATA` field | Source |
|--------------|--------|
| `theme` | `'dark'` for `dependency_graph.html`, `'light'` for `dependency_graph_light.html`; do not change other data between versions |
| `manifest` | `.codeanvil/project.yaml`: `id`, `name`, `gt`, `cycle`, copied as they are |
| `subsystems` | §1.1 per subsystem, §1.3 for its base, §1.4 cards for its modules; module label is `module_id` and `required_vl` |
| `hardware` | §0.1 devices; `to` lists the `SUB-xxx/module_id` of the `hw_dependency: true` modules that use the device; `phys` lists other hardware items it connects to physically (signal chain, power, cooling) — leave `[]` for spatial items with no physical connection (e.g. enclosure) |
| `subsystemContracts` | §3.4, producers in `from` and consumers in `to` |

Rules:

- Every subsystem, module, hardware device and subsystem contract of the design appears, and nothing
  appears that the design lacks.
- Spiders have no module-to-module edge. Build order, internal contracts and `PATH-*` stay in the
  design document.
- One color per functional layer, in the template's declared order; reuse its color identifiers
  in both copies. The renderer adapts those colors for contrast in each theme. Bases, hardware
  and contracts use the renderer's reserved accents and shapes, not functional-layer colors.
- A contract with several producers or consumers is one entry with arrays in `from` and `to`.
- Keep `layout.randomSeed` fixed. One subsystem means one spider and no subsystem contracts.
- `S1.md` is the only state: G1 and `codeanvil status` never read the HTML. A graph problem
  blocks nothing; if it exposes a design error, fix the design and rewrite both graph versions.

## Report Contract

Write exactly one file: `.codeanvil/report/<cycle-name>/S1.md`, append-only.

- First run: header plus `## Iteration 1`; later runs append `## Iteration <N>`.
- Header: a `| Field | Value |` table with `Gate` = `S1`, `Cycle`, `Document` (the design path)
  and `Created` = `codeanvil now`.
- Iteration: a `| Field | Value |` table with `Date` = `codeanvil now`, `Timestamp` =
  `codeanvil now --machine`, `Iteration`, `Cycle`, and exactly one row written as
  `| HITL | PASS |` or `| HITL | FEEDBACK |` (never both in one row, which `codeanvil status`
  reads as `UNKNOWN`). Then `### Description`.
- The Description starts with the exact line `Based on: G0 iteration <N>`, where `N` is the latest
  G0 iteration when the work starts, followed by the design and both graph paths and the SHA-256 of
  `.codeanvil/design/SDD.md` (command in `## Rework (bounded)`). On rework it also carries the
  design change set.
- S1 is a **stage**: `PASS` means "output delivered". The human verdict belongs to G1.

## Output Contract

Return the design path, both graph paths, the report path with the iteration number, and the
next step (`S1 complete. Run the G1 skill.`).

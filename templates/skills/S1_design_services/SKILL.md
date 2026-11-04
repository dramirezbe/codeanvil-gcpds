---
name: s1-design-services
description: "Trigger: S1, design services, architecture, service topology, contracts, stubs, dependency graph. From a passed G0 pair, write the S1 design document (layered services, contracts with stubs, traceability, decisions, risks) and its dependency graph."
license: Apache-2.0
compatibility: "No network access, no scripts. Reads GT/G0_StRS.md, GT/G0_SyRS.md and .codeanvil/project.yaml. Writes .codeanvil/report/<cycle-name>/S1.md and S1_artifacts/."
metadata:
  author: "gcpds"
  version: "1.0"
  gate: "S1"
  pipeline: "V-SIL"
---

# S1 — Design of a System of Layered Services

Produce one design document that resolves every implementation-critical decision: service
topology, a layered base and modules per service, contracts with stubs, traceability and system
paths. One service is a valid special case. A human reviews the result at G1.

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
is requested by a `G1.md` iteration with `FEEDBACK` (named sections to rework) or by the user.

## Inputs and Outputs

| | Path | Notes |
|---|------|-------|
| Input | `GT/G0_StRS.md`, `GT/G0_SyRS.md` | Read-only |
| Input | `.codeanvil/project.yaml` | Read-only; its keys are copied as text into the graph |
| Input (optional) | Supplied ML package | Only if the design uses ML or the GT requires it |
| Input (rework) | Latest `G1.md` FEEDBACK | Named sections to rework |
| Template | `templates/skills/S1_design_services/references/S1_design.md` | This skill's locked template |
| Output | `.codeanvil/report/<cycle-name>/S1_artifacts/S1_design.md` | Overwritten on rework |
| Output | `.codeanvil/report/<cycle-name>/S1_artifacts/S1_graph.html` | Dependency graph; overwritten on rework |
| Output | `.codeanvil/report/<cycle-name>/S1.md` | Iterative report: the only state of this stage |

Working files live in `S1_artifacts/`, never directly in the cycle folder.

## Hard Rules

- **Never edit GT.** A GT gap goes to design §6 as a risk, or follows the RFD route.
- Modules talk only through their service's base. No cross-service call bypasses a versioned contract.
- Split services only when they deploy or restart independently, communicate over a network, or
  have distinct failure domains.
- `hw_dependency: true` means `required_vl: VL-2`. Running on a computer does not count as a
  hardware dependency.
- Keep the implementation DAG and the runtime interaction graph separate. A cross-service
  contract is defined before both services and is never drawn as a mutual dependency.
- Every contract is complete enough to write a deterministic stub without asking the designer.
- Omit design §1.5 entirely when no ML is used. Never train or select a model.
- Ask the user only when a choice cannot be derived from the GT.

## Steps (one pass)

1. Copy the template to `S1_artifacts/S1_design.md`. Record the GT digests in the Meta
   "G0 approved" row (information only, never a block), computed with:
   `python -c "import hashlib,sys;[print(hashlib.sha256(open(p,'rb').read()).hexdigest(),p) for p in sys.argv[1:]]" GT/G0_StRS.md GT/G0_SyRS.md`
2. Allocate `SYS-*` to services and paths: §0.4, §1.1, §4.1.
3. Fill the COTS envelope from the `HWC-*` blocks: §0.1–0.3.
4. For each service: its base (§1.3) and module cards (§1.4), each with the full verification profile.
5. Draw the implementation DAG and topological order (§2.1–2.2) and the runtime graph (§2.3).
6. Write the contracts with stub or fake-peer recipes and vectors (§3).
7. Complete traces and `PATH-*` (§4).
8. Record decisions with real alternatives (§5; DEC-001 is the partitioning decision) and risks (§6).
9. Reread the design against this short list and fix what you find: no `{{` left, every `SYS-*`
   traced, every contract with a recipe, `hw_dependency: true` at `VL-2`, no cycle in the build
   order. This is a courtesy to the reviewer, not a gate.
10. Build the dependency graph (next section).
11. Write the iteration with the row `| HITL | PASS |` and the graph's path in the Description.
    Return the design path and `S1 complete. Run the G1 skill.`

## Infeasibility

If the design shows that no partitioning can meet a requirement on the declared COTS platform
(for example, pipeline latency exceeds the requirement under any partitioning on this hardware),
do not hide it: run the RFD skill with `ANALYSIS (no VL)` evidence, and write the iteration with
`| HITL | FEEDBACK |` and the Description line `Verdict: RFD` naming the RFD. A rework after G1
passed makes `codeanvil status` mark G1 stale, so the design is reviewed again before S2.

## Dependency Graph

The graph is a reading aid: **a full dependency graph, each service drawn as a spider** (its
base at the center, its modules on the spokes), delivered as one HTML file using vis-network, with
the manifest as text to tell designs apart.

Copy `templates/skills/S1_design_services/references/S1_graph_template.html` to
`.codeanvil/report/<cycle-name>/S1_artifacts/S1_graph.html` and change **only the `DATA` block at
the top**. Never edit below it and never write the page by hand: the fixed rendering code makes
every agent runtime draw the same graph. It loads `assets/vis-network.min.js` from this skill's
own folder by relative path, so it needs no network, but it must stay inside the project.

| `DATA` field | Source |
|--------------|--------|
| `manifest` | `.codeanvil/project.yaml`: `id`, `name`, `gt`, `cycle`, copied as they are |
| `services` | §1.1 per service, §1.3 for its base, §1.4 cards for its modules; module label is `module_id` and `required_vl` |
| `hardware` | §0.1 devices; `to` lists the `SVC-xxx/module_id` of the `hw_dependency: true` modules that use the device |
| `serviceContracts` | §3.4, producers in `from` and consumers in `to` |

Rules:

- Every service, module, hardware device and service contract of the design appears, and nothing
  appears that the design lacks.
- Spiders have no module-to-module edge. Build order, internal contracts and `PATH-*` stay in the
  design document.
- One color per functional layer, in template order. Purple and red are reserved for bases,
  hardware and contracts.
- A contract with several producers or consumers is one entry with arrays in `from` and `to`.
- Keep `layout.randomSeed` fixed. One service means one spider and no service contracts.
- `S1.md` is the only state: G1 and `codeanvil status` never read the HTML. A graph problem
  blocks nothing; if it exposes a design error, fix the design and rewrite both.

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
  G0 iteration when the work starts, followed by the design and graph paths.
- S1 is a **stage**: `PASS` means "output delivered". The human verdict belongs to G1.

## Output Contract

Return the design path, the graph path, the report path with the iteration number, and the
next step (`S1 complete. Run the G1 skill.`).

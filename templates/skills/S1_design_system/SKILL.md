---
name: s1-design-system
description: "Trigger: S1, design subsystems, architecture, subsystem topology, contracts, stubs, dependency graph. From a passed G0 pair, write the S1 design document (layered subsystems, contracts with stubs, traceability, decisions, risks) and its dependency graph."
license: Apache-2.0
compatibility: "No network access, no scripts. Reads .codeanvil/GT/StRS.md, .codeanvil/GT/SyRS.md, .codeanvil/project.yaml, and .codeanvil/design/SDD.md (from G1 rework). Writes .codeanvil/design/SDD.md, .codeanvil/design/dependency_graph.html (dark), dependency_graph_light.html, and .codeanvil/report/<cycle-name>/S1.md. Report includes Scope: system and Input: sha256 lines for all read GT files."
metadata:
  author: "gcpds"
  version: "1.2"
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

On every rework, keep G0 as the upstream baseline. Record the feedback source separately as
`Rework from: <gate> iteration <N>`. Follow [Delivery and rework](references/rework_delivery.md)
through report publication; an old G1 becoming stale is expected and does not invalidate S1.

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
  kit contract; real hardware runs require the pre-HW review checkpoint in S3/G3.
- The Mock HAL (§1.6) and the Telemetry companion (§1.7) are always designed. The Telemetry
  companion lives in `verification/telemetry/`: it is never a module and never under `src/`.
- **Target(s)** (Meta) is **design intent**: it maps every subsystem and verification path to
  `local` or to the intended device, **deduced from the `HWC-*` blocks** of the StRS. It is not a
  `.codeanvil/project.yaml` `targets:` entry. When several devices could apply, resolve the
  selection from GT or ask the user; never pick the first silently. S1 never enrolls a target and
  never writes or asks for credentials, IP or MAC: the concrete `project.yaml` target entry is
  created later, at G3, by `credential-setup`, and only if the design requires VL-2. In §1.6 name
  where each level runs and in §1.7 give an operating envelope per target, sourced from its COTS
  constraints. Missing target intent or limits are design risks to resolve, never guessed values.
- Verification ladder: VL-0 and VL-1 run **locally with no hardware** (Mock HAL, and in `mock+real`
  the Real HW HAL against a fake device API). VL-2 is real SIL/HIL on the actual hardware at G3.
  Remote PIL at S3 is out of scope: do not design a remote deployment for VL-0/VL-1. Do not ask
  the user to invent a target alias or put local private key paths in shared project metadata.
- Execution location and HAL mode are separate axes. VL-0/VL-1 with Mock HAL inputs run locally
  and remain **VERIFIED**; they do not establish VL-2 or real-RF validation. Real-hardware
  execution happens at G3 through `vsil_hil_mcp`; local execution uses the runtime's normal tools.
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

## Execution Continuity

Once the user requests S1 and its prerequisites pass, execute the authorized design work
**in the same turn** until the output is delivered or a concrete blocker requires a stop.
S1 has no scheduled internal human checkpoint. Reading the templates, checking G0, taking
a backup or collecting timestamps/digests is preparation, not a completed stage. Progress
updates and status questions do not end the authorized work.

- **Resume, do not restart.** Continue the same in-progress iteration from any existing SDD
  and graphs. Preserve valid sections and stable IDs; finish missing work and apply the bounded
  rework rules where needed. Do not repeat an already successful backup or ask again for
  unchanged authorization. An exit-0 `nothing to back up` result is not a blocker.
- Derive package identifiers, toolchain and the root command from GT and the design rules;
  document the rationale for G1. Ask only for a required choice that cannot be derived.
  Write the design incrementally instead of postponing every artifact until all reasoning
  is finished. Never invent requirements or edit GT to avoid a question.
- Do not return only a reading summary, a promise, `S1 is still pending` or
  `I cannot complete S1 in this turn` while an authorized next action remains. The estimated
  size of the design or an assumed turn budget is not a blocker. For an actual runtime or
  context interruption, preserve existing work and name the actual limit/boundary reached.
- Completion requires all four outputs: `.codeanvil/design/SDD.md`,
  `.codeanvil/design/dependency_graph.html`, `.codeanvil/design/dependency_graph_light.html`
  and `.codeanvil/report/<cycle-name>/S1.md`. Record PASS only after the design and both
  graphs are complete and the prescribed reread and digest/report checks succeed;
  templates, placeholders and promises are not delivery evidence. S1 PASS means
  delivered, never G1 approval. Do not invent a PASS to make the chain advance.

| Boundary | Required action |
|----------|-----------------|
| S1 delivered | Finish the design, both graphs and the completed iteration; return `S1 complete. Run the G1 skill.` Never assume G1's human verdict. |
| Missing required input or unresolved GT choice | Name the exact file, section, field or choice, affected deliverables and the specific question needed; complete unaffected work first. Preserve drafts and write no completed iteration. |
| Permission, tool, custody or backup failure | Show the failed command/error and affected scope; resolve within existing authorization or request the specific missing permission. Resume after resolution; preserve the predecessor/backup stop rules. |
| Demonstrated infeasibility | Follow the existing Infeasibility/RFD contract with concrete evidence; do not substitute a generic inability-to-finish message. |
| Explicit human stop or actual runtime interruption | Preserve partial artifacts, identify completed/pending scope and the concrete resume action; write no fabricated completed iteration. |

### Continuation responses

After trimming whitespace, the whole replies `continue`, `run`, `y`, `yes` and `ok`
(case-insensitive, including `RUN`) resume the already authorized S1 scope. Do not ask for
another continuation or treat resumption as a new iteration. These replies never waive a
prerequisite, expand scope or decide G1. Respect negations and conditions such as `do not run`
or `yes, but stop before the report`; clarify only when the requested scope remains ambiguous.

## Steps (one pass)

1. **Back up before overwriting.** Run `codeanvil backup S1` from the project root. If it exits
   nonzero, stop and show its message; write no iteration. Cite the printed backup path in the
   iteration's Description. Backups never cover `src/` or `verification/`: code recovery relies
   on git.
2. On first delivery copy the template to `.codeanvil/design/SDD.md`; on rework resume the existing
   design and preserve valid sections. Obtain GT digests using
   `codeanvil custody digest .codeanvil/GT/StRS.md .codeanvil/GT/SyRS.md` and record the
   returned Input lines in S1.md. Do not add retired approval fields to the SDD Meta.
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
12. Finish the [delivery checks](references/rework_delivery.md), then write the iteration with
    the row `| HITL | PASS |`, the final SDD Output digest and both graph paths in the Description.
    Run `codeanvil custody verify --cycle <cycle> --gate S1` and `codeanvil status`.
    Resolve a failed delivery check before claiming completion. An obsolete previous G1 is the
    reason for a new review, never a reason to restart a complete S1 delivery.
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
   Run `codeanvil custody digest .codeanvil/design/SDD.md --raw`

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
- Keep that G0 line on rework too. Use `Rework from: G1 iteration <N>` (or the actual feedback
  gate) as separate provenance; never write `Based on: G1 ...` in S1. A malformed historical
  baseline is recovered by appending a checked corrective delivery, never rewriting history.
- S1 is a **stage**: `PASS` means "output delivered". The human verdict belongs to G1.

## Output Contract

Return the design path, both graph paths, the report path with the iteration number, and the
next step (`S1 complete. Run the G1 skill.`).

**Report structure:**

The report includes:
- `Scope: system` — this design covers the whole system
- `Input: .codeanvil/GT/StRS.md sha256:‹hash›` — hash of the input StRS (use `codeanvil custody digest`)
- `Input: .codeanvil/GT/SyRS.md sha256:‹hash›` — hash of the input SyRS
- `Output: .codeanvil/design/SDD.md sha256:‹hash›` — delivered design digest from custody; do not record the overwritten previous SDD as an Input against the same path.

## Delta-sync

For accepted `design-sync` rows in `.codeanvil/plans/DELTAS.md`, run `codeanvil backup S1`,
verify Before digests using `codeanvil custody digest` and apply only the named minor design edits.
Never bump a contract version or change stubs in this mode; structural changes use normal S1/G1
rework with the full stale cascade. Record before/after digests, Status applied and Applied in
with this S1 iteration. Append `Scope: delta-sync` with delta IDs and an explicit empty interface
impact map, new SDD Output digest and G0 baseline. G1 bounded rework must confirm that map.
Rework may also originate from S2/G2/S3/G3 `Verdict: design defect`; preserve unaffected modules.

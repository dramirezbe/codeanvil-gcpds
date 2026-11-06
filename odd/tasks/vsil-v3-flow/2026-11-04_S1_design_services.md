# Plan — S1: system of layered services

Feature: `odd/tasks/2026-11-04_1042_vsil_v3_skill_flow.md` · Task T2 · Specs S1, S2, S3, S8, S9 · Contracts C0–C7
Target: `templates/skills/S1_design_services/SKILL.md` (about 150 lines) + `references/S1_design.md` (template, about 350 lines) + `references/S1_graph_template.html` (about 85 lines) + `assets/vis-network.min.js` (477 KB, version 9.1.9) and its license. All of it stays inside the skill folder (C10). Paper §5, `S1_G1_template.md` Meta and §0–§6.

## Goal

Produce one design document that resolves every implementation-critical decision: service topology, a layered base and modules per service, contracts with stubs, traceability and system paths. One service is a valid special case.

## Inputs and outputs

| | Path | Notes |
|---|------|-------|
| Input | `GT/G0_StRS.md`, `GT/G0_SyRS.md` | Read-only |
| Input | `.codeanvil/project.yaml` | Read-only; its keys are copied as text into the graph |
| Input (optional) | Supplied ML package | Only if the design uses ML or the GT requires it (paper §5.4) |
| Input (rework) | Latest `G1.md` FEEDBACK or a G2 design defect | Named sections to rework |
| Output | `.codeanvil/report/<cycle>/S1_artifacts/S1_design.md` | Overwritten on rework (C3) |
| Output | `.codeanvil/report/<cycle>/S1_artifacts/S1_graph.html` | Dependency graph; overwritten on rework (C3) |
| Output | `.codeanvil/report/<cycle>/S1.md` | Iterative report and the only state of this stage |

## Template (`references/S1_design.md`)

English translation of `S1_G1_template.md` through §6 (A3). Same section numbers, so paper and template references hold. Long guidance comments shrink to one or two lines, because the skill carries the rules. It lives inside the skill folder, so **no scaffold code or config is needed to ship it**.

The Meta "G0 approved" row holds the GT digests (C5). No script parses this document (S7), so section wording may change as long as the numbering holds.

## Skill sections

Frontmatter: `name: s1-design-services`, `metadata.gate: "S1"`.

1. **Prerequisite.** C2 on `G0.md`. Record the GT digests in Meta (C5). The iteration's Description starts with `Based on: G0 iteration <N>` (C11).
2. **Hard rules.**
   - Never edit GT. A GT gap goes to §6 as a risk or follows the RFD route.
   - Modules talk only through their service's base. No cross-service call bypasses a versioned contract (paper §5.2).
   - Split services only when they deploy or restart independently, communicate over a network, or have distinct failure domains (paper §5).
   - `hw_dependency: true` means `required_vl: VL-2`. Running on a computer does not count as a hardware dependency.
   - Keep the implementation DAG and the runtime interaction graph separate. A cross-service contract is defined before both services and is never drawn as a mutual dependency; runtime loops are reviewed as protocol.
   - Every contract is complete enough to write a deterministic stub without asking the designer.
   - Omit §1.5 entirely when no ML is used. Do not train or select a model.
3. **Steps (one pass; ask only when a choice cannot be derived from the GT).**
   1. Allocate `SYS-*` to services and paths: §0.4, §1.1, §4.1.
   2. Fill the COTS envelope: §0.1–0.3 from `HWC-*`.
   3. For each service: base (§1.3) and module cards (§1.4).
   4. Draw the implementation DAG and topological order (§2.1–2.2) and the runtime graph (§2.3).
   5. Write contracts with stub or fake-peer recipes and vectors (§3).
   6. Complete traces and `PATH-*` (§4).
   7. Record decisions with real alternatives (§5; DEC-001 is the partitioning decision, A4) and risks (§6).
   8. Reread the design against this skill's own short list and fix what you find: no `{{` left, every `SYS-*` traced, every contract with a recipe, `hw_dependency: true` at `VL-2`, no cycle in the build order. This is a courtesy to the reviewer, not a gate.
   9. Copy `templates/skills/S1_design_services/references/S1_graph_template.html` to `S1_artifacts/S1_graph.html` and fill its `DATA` block from the design (see `## Dependency graph`).
   10. Write `HITL: PASS` (C4), with the graph's path in the Description. Return the path and `S1 complete. Run the G1 skill.`
4. **Infeasibility.** "Pipeline latency exceeds requirement under any partitioning on this HW" (paper §9.2) → run the RFD skill with `ANALYSIS (no VL)` evidence. Write `HITL: FEEDBACK` with `Verdict: RFD` in the Description, naming the RFD. Reworking after G1 already passed makes `codeanvil status` mark G1 stale, so the design is reviewed again before S2 (C2).

## Dependency graph

S8 and S9: a full dependency graph, each service drawn as a spider, delivered as an HTML file using vis-network, with the manifest as text "to difference designs". A "spider" is the service star of paper §5.2 and `V-SIL_v3-diagrams.html` §5.1: the service's base at the center and its modules on the spokes.

The user's style reference is `methodology/V-SIL-v3/spider-vis-network.html`. `odd/tasks/2026-11-04_S1_graph_examples/S1_graph_template.html` extends it to several services, and five filled examples sit beside it. All six rendered in headless Chromium with no console errors, and two renders of each were byte-identical. The user approved this look (L13). T2 copies the template to `references/S1_graph_template.html`, changing only the script source to `../../../../.agents/skills/S1_design_services/assets/vis-network.min.js` and the load-failure message. The previews in that folder keep the CDN link only because they sit outside a project.

**How the agent produces it.** Copy the template to `S1_artifacts/S1_graph.html` and change only the `DATA` block at the top, as in the user's example. The rendering code stays fixed, so every agent runtime draws the same graph: never edit below the `DATA` block, and never write the page by hand. It is a plain file, so no runtime-specific artifact feature is involved.

| `DATA` field | Source |
|--------------|--------|
| `manifest` | `.codeanvil/project.yaml`: `id`, `name`, `gt`, `cycle`, copied as they are |
| `services` | §1.1 for each service, §1.3 for its base, §1.4 cards for its modules. Each module label is `module_id` and `required_vl` |
| `hardware` | §0.1 devices. `to` lists the `SVC-xxx/module_id` of the modules with `hw_dependency: true` that use the device |
| `serviceContracts` | §3.4, with producers in `from` and consumers in `to` |

The graph is rewritten whenever the design changes, in the same run, so the two never drift apart.

**What the page shows.**

| Part | Content |
|------|---------|
| Text panel | `id`, `name`, `cycle` and `gt` from `.codeanvil/project.yaml`, copied as they are, to tell designs apart. Nothing else is added |
| Spiders | One spider per service, physics layout as in the example. Hardware attaches with a dashed arrow. Service contracts sit between the bases, so runtime loops are visible |

**Rules.**

- Derive the data from the design (§0.1, §1.1, §1.4, §2.3, §3.4). Every service, module, hardware device and service contract appears, and nothing appears that the design lacks.
- Spiders have no module-to-module edge, because modules talk only through their base. Build order, internal contracts and `PATH-*` stay in the design document (§2.1–2.2, §3.1–3.3, §4.4).
- Module colors: one color per functional layer, taken in order from the palette in the template. Purple and red stay reserved for bases, hardware and contracts.
- Two services may reuse a module name, because the page prefixes module ids by service. `hardware.to` uses the full `SVC-xxx/module_id`.
- A contract with several producers or consumers is one entry with arrays in `from` and `to`, so it draws as one box.
- `layout.randomSeed` stays fixed, so the same data always gives the same picture.
- One service is valid: one spider and no service contracts.
- Rework overwrites the file (C3), so the page always shows the latest design of its cycle.

**Orchestration stays report-driven.** The HTML is a reading aid, never state:

- `S1.md` remains the only state of this stage. G1's prerequisite reads `S1.md`, never the HTML.
- `S1.md`'s Description names the graph's path. The iteration history lives in the report, not in the page.
- `codeanvil status` ignores the file, because it sits in a subfolder (C3) and is not `.md`.
- A graph problem blocks nothing. If it exposes a design error, S1 fixes the design and rewrites both.

**Offline by design.** The page loads vis-network 9.1.9, the version in the user's example, from this skill's `assets/` by relative path, so it needs no network. Tested in a mock project with all network access blocked: it rendered byte-identical to the CDN version. Each design adds no copy of the library, but the page needs the project's `.agents/` folder beside it: sent alone, it shows the load-failure message.

**Known limits.** The page shows runtime structure only, so it cannot be used to check the implementation DAG; G1.1 reviews that in the design document. With about 30 nodes the first view shrinks labels until they need zooming with the mouse wheel. Colors have no legend on the page.

## RED tests first

- `tests/test_create.py` through `_skill_text`: names `S1_artifacts/S1_design.md`, and `G0 must pass first. Run the G0 skill.`, and `Based on: G0 iteration`, and does not contain `g1_check` (S7) or `G1_CHECKLIST` (C10).
- Same test: names `S1_artifacts/S1_graph.html`, `S1_graph_template.html`, `spider` and `.codeanvil/project.yaml` (S8, S9).
- `tests/test_create.py`: a scaffold contains `.agents/skills/S1_design_services/references/S1_graph_template.html`, with the `DATA` block markers and no `https://` script source in it, and `.agents/skills/S1_design_services/assets/vis-network.min.js`.

## Acceptance

1. A design from the FM test inputs reaches the human at G1 with the checklist filled and no `{{` placeholder left (T7). One service or several are both valid.
2. `S1_artifacts/` does not appear as a gate in `codeanvil status` (C3).
3. Each §1.4 card carries the full verification profile from paper §5.3.
4. `S1_graph.html` opens with the spiders and the manifest text, with every service, module, hardware device and service contract of the design present (T7).
5. Deleting `S1_graph.html` does not change `codeanvil status` or G1's prerequisite result (T7).

## Reuse

`scaffold` copies `references/` and `assets/` with the skill, and the wheel's `force-include` of `templates/skills` ships them. The `.md` path rewrite turns `templates/skills/` into `.agents/skills/` in the skill text.

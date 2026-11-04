# V-SIL v3 skill flow — simplest full flow in `templates/skills/`

Objective: replace the v2-era gate chain (G0 → CC → G1 with SRS) by the V-SIL v3 flow (S0 → G0 → S1 → G1 → S2 → G2, RFD from any stage) using the simplest skill for each step, with `codeanvil status` as the only CLI refactor (S11).
Branch: `feat/vsil-v3-skill-flow` · Delivery: `ask-on-risk` with chain strategy `feature-branch-chain` (chosen 2026-11-04) · Test runner: `pytest` (`uv run --extra dev pytest`).
Status: **S0–G1, RFD, the chain switch and `status` are implemented (252 tests pass). The agent-driven end-to-end run (T7) is NOT run. S2 and G2 are HELD for the user (S5).**

## Specs

- **S1** — "Read methodology V-SIL-v3. Plan in odd/tasks all the reafactors needed to implement all the methodology flow."
- **S2** — "Take the simplest version possible of each skill and implement a full flow ready to use."
- **S3** — "plan each skill or step as a different file of plan."
- **S4** — "Remeber reuse the current tools already implemented, like \"codeanvil status, now, sync, create, init, etc ,etc...\" to not refactor all, just skills."
- **S5** — "If you have a question ask directly to me. Stop when planning implementation stage, because i dont know how to do it." Assumption: "implementation stage" is V-SIL S2, so planning stops before S2 and G2 and continues with the user.
- **S6** — "move the skill outside for now in templates/backups/ please. Do not custody chain for now"
- **S7** — "No deterministic gates. The only determniistic gate is the S0 normalization. The rest are all HITL. Or in stage validation the interface contracts, but is not deterministic, is validation agent driven with harness of interfaces contraact and sandwich tests". Assumption: "the S0 normalization" gate is the existing `g0_validate.py` check of what S0 produced, followed by human Gate H. G1 and G2 have no scripts or exit-code verdicts; S2's interface-contract and sandwich validation is agent-driven inside the stage and is not a gate.
- **S8** — "Add to S1 skill a part where describes full graph of dependencies in ascii here in chat. remember as spider each service, etc". Assumption: "spider" is the paper's service star, with the base at the center and modules on the spokes. Delivery format replaced by S9.
- **S9** — "Change that ascii diagrams to an html artifact using vis. Just add as text inside html the metadata of .codeanvil/project.yaml to difference designs" · "Remember to mantain agent orchestration based in reports" · "See an example if what i like @methodology/V-SIL-v3/spider-vis-network.html". Assumption: "html artifact" is a plain HTML file in `S1_artifacts/`, not a runtime-specific feature, because skills stay agent-agnostic. Amended by L10: spiders only, "delete build order. The rest is ok".
- **S10** — "Remember autocontained skill. Im refering for example. The templates, scripts and other tools used for the skill in the same .agents/skills/<folder-skill>"
- **S11** — "yes, add it to the plans. You can refactor also \"status\". But mantain sync, and now". Refines S4: `status` may change; `sync` and `now` stay as they are.

## Tasks

Plans are the specification of each task. Status and commits are observed outcomes.

| ID | Specs | Plan file | Route | Status | Commit |
|----|-------|-----------|-------|--------|--------|
| T1 | S1, S2, S3, S7, S9 | `2026-11-04_G1_design_review.md` (HITL review skill, no script) | inline | done | 647cf3d |
| T2 | S1, S2, S3, S8, S9, S10 | `2026-11-04_S1_design_services.md` + `2026-11-04_S1_graph_examples/` | inline | done | c9b76e7 |
| T3 | S1, S2, S3, S10 | `2026-11-04_S0_normalise_build_package.md` | inline | done | f45db10 |
| T4 | S1, S2, S3 | `2026-11-04_RFD_request_for_deviation.md` | inline | done | f45db10 |
| T5 | S1, S2, S3 | `2026-11-04_G0_gate_h_update.md` | inline | done | c383301 |
| T6 | S4, S6, S10 | `2026-11-04_CHAIN_scaffold_switch.md` | inline | done (docs 26bbba4) | c383301 |
| T7 | S2 | `2026-11-04_E2E_flow_through_g1.md` | inline | procedure written; **agent run not performed** | 26bbba4 |
| T10 | S4, S11 | `2026-11-04_STATUS_chain_and_staleness.md` | inline | done | 3b35444 |
| T8 | S1, S5, S7 | S2 skill plan (in-stage, agent-driven contract and sandwich validation, C9) | — | **HELD: needs the user** | — |
| T9 | S1, S5, S7 | G2 skill plan (HITL) + Verified Prototype output | — | **HELD: depends on T8** | — |

Order rationale: T1–T4 only add new skill directories, so the suite stays green. T10 comes next, in its own commit, because skills rely on its stale markers and old report ids keep printing. T5 and T6 flip the chain together in one commit, because `tests/test_create.py` pins the old chain. Route evidence: the skills share one document contract (S1's template is G1's input), so they are not independent units, and no Writer trigger fires.

## Target flow

| Step | Skill dir (`templates/skills/`) | `metadata.gate` | `prerequisite` | Report | Writes |
|------|---------------------------------|-----------------|----------------|--------|--------|
| S0 | `S0_normalise_build_package` (new) | `S0` | `null` | `S0.md` | `GT/G0_StRS.md`, `GT/G0_SyRS.md` |
| G0 + Gate H | `G0_valid_req_and_GT` (edited) | `G0` | `S0` | `G0.md` | — |
| S1 | `S1_design_services` (new) | `S1` | `G0` | `S1.md` | `S1_artifacts/S1_design.md` |
| G1 | `G1_design_review` (new) | `G1` | `S1` | `G1.md` | — |
| S2 | HELD | `S2` | `G1` | `S2.md` | HELD |
| G2 | HELD | `G2` | `S2` | `G2.md` | HELD |
| RFD | `RFD_request_for_deviation` (new) | `RFD` | not in chain | `RFD.md` | `RFD_artifacts/RFD-NNN.md` |

Paper routes only (L8 of the v3 chat-only feature, carried over as C0 below):

```
Build Package → S0 → G0 ─ PASS + Gate H → S1 → G1 ─ PASS → S2 → G2 ─ PASS → Verified Prototype
                ▲    └ FEEDBACK → S0      ▲    └ FEEDBACK → S1 ▲    ├ design → S1
                │                                              └────┴ module → S2
                └── new cycle ◄ updated Build Package ◄ RFD ◄ infeasible (S1, G1, G2)
```

## Shared contracts (every plan references these)

- **C0 No deviation.** Stages, gates, routes and outcomes come from `methodology/V-SIL-v3/V-SIL_v3.md` and `S1_G1_template.md`. Plans may add only mechanics (paths, report fields). The paper and template were aligned with S7 (L7).
- **C1 Reuse the report contract unchanged.** One file `.codeanvil/report/<cycle>/<id>.md`, append-only `## Iteration N`, row `| HITL | PASS |` or `| HITL | FEEDBACK |`, timestamps from `codeanvil now` and `codeanvil now --machine`, active cycle from `.codeanvil/project.yaml`. Same wording as `G0_valid_req_and_GT/SKILL.md`, `## Report Contract`.
- **C2 Prerequisite check.** In this order, writing no iteration when stopping. RFD is exempt: it can be raised from any stage.
  1. The predecessor report is missing or its latest iteration is not `HITL: PASS`: return exactly `<X> must pass first. Run the <X> skill.`
  2. `codeanvil status` marks the predecessor or any earlier report in the active cycle `stale`: return the same line, naming the earliest stale report. This is how a design reworked after its review is caught, including further down the chain.
  3. The skill's own latest iteration is `HITL: FEEDBACK`. With `Verdict: RFD`, return exactly `Cycle suspended by RFD. Run the RFD skill.` Otherwise, if its `Based on` matches the predecessor's latest iteration, nothing has been reworked yet, so return exactly `<X> must rework first. Run the <X> skill.`
- **C3 Artifacts sit in a subfolder.** `cmd_status` globs `<cycle>/*.md`, so a design file directly in the cycle folder would show as a gate with `UNKNOWN`. Working files go to `<cycle>/<ID>_artifacts/`, overwritten on rework, exactly like the old `G1_artifacts/`.
- **C4 Stage vs gate.** S0 and S1 are stages: they finish in one pass and write `HITL: PASS` meaning "output delivered". The human judgement belongs to Gate H, G1 and G2 (S7). `codeanvil status` prints a stage's PASS as `delivered`, so it never reads as a human approval.
- **C5 GT digests are information only (S6, S7).** S1 records the SHA-256 of both GT files in the design's Meta table (the template's "G0 approved" row), computed with this stdlib one-liner:
  `python -c "import hashlib,sys;[print(hashlib.sha256(open(p,'rb').read()).hexdigest(),p) for p in sys.argv[1:]]" GT/G0_StRS.md GT/G0_SyRS.md`
  G1 recomputes them and shows the human whether they match. They never block. Edits made between G0's PASS and S1 are not detected, and this is not tamper evidence.
- **C6 Principles (S7).** P1: Gate H, G1 and G2 verdicts are human. P2: the model never approves its own work, because the human is the oracle at every gate after S0, so no separate reviewer session is required. P3 applies only to `g0_validate.py`: exit `1` forces `HITL: FEEDBACK`. P4: every claim names its verification level and environment; S1-time evidence is `ANALYSIS (no VL)`.
- **C7 Simplest version.** Skills are short agent contracts that read their locked template instead of embedding it. The chat-only v3 skills are a source of rules, not of text: they embed blueprints for tool-less chats (S0-1 is 761 lines) and predate the services model (0 mentions of `SVC-`, `service_id`, `PATH-` or cross-service in `templates/no-tools-skills/v3/`).
- **C8 Skill test pattern.** Assertions on skill text through `_skill_text()` in `tests/test_create.py`, plus the existing `templates/tests/test_g0_validate.py`. No new gate script means no new script test.
- **C9 In-stage validation in S2 (S7, input for T8).** S2 validates interface contracts and sandwich integration inside the stage. The agent drives it, using a harness built from the G1-approved contracts: stubs, fake peers, drivers and reference vectors. It informs the agent's work and the evidence shown to the human; it is not a gate and has no pass or fail verdict of its own.
- **C10 Self-contained skills (S10).** Every template, script and tool a skill uses lives in its own `.agents/skills/<skill>/` folder. A skill may read its inputs (GT files, the predecessor's report and artifacts) and may name the next skill as a route, but it never reads another skill's folder. Skill text states its rules inline and never points at `methodology/`, which scaffolded projects do not have; the "paper §" citations in these plans are traceability for the author only.
- **C11 `Based on` line.** Every iteration of G0, S1, G1, and later S2 and G2, starts its Description with the exact line `Based on: <predecessor id> iteration <N>`, where `N` is the predecessor's latest iteration when the work starts. S0 has no predecessor and RFD is outside the chain, so neither writes one. This one line is what lets reports express rework and staleness; reports stay the only state.

## Tools reused with no change (S4)

| Tool | Why no change is needed |
|------|-------------------------|
| `codeanvil now`, `sync`, `list`, `init`, `sandbox` | Independent of skill names. S11 explicitly keeps `sync` and `now` as they are. |
| `codeanvil create` | `_copy_skills` copies the whole `templates/skills/`. `_skill_table`, `_order_summaries` and `_prerequisite_cell` are driven by `config.yaml` and frontmatter. A skill missing from `config.yaml` renders `-`, which is what RFD needs. Only one hardcoded line changes (see T6). |
| `g0_validate.py` | Unchanged. It passes on the test inputs: 0 errors and 0 warnings, observed 2026-11-04. |
| `.codeanvil/custody/` dir, `_migrate_provenance` | Left in place. An empty folder is harmless and `tests/test_sync.py` and `tests/test_paths.py` pin them. |

## Assumptions to confirm

- **A1** — A project with a ready GT pair and no Build Package (T0_ANE-Lap2) passes through S0 as a no-op iteration, so the chain stays strict and T0 stays usable.
- **A2** — `G1_start_design/` and `templates/GT/G1_SRS.md` also move to `templates/backups/`. S6 only names custody, but v3 has no SRS (paper §5, §6), and moving is reversible.
- **A3** — The S1 and G1 templates shipped to projects are English translations of the Spanish `S1_G1_template.md`, because generated artifacts default to English. The Spanish file stays canonical in `methodology/`.
- **A4** — v2's mandatory multi-hypothesis + ATAM is dropped. The paper does not require it, and DEC-001's "alternatives considered" carries the partitioning choice.
- **A5** — An RFD re-enters through a **new cycle**, because an updated Build Package is a new GT baseline (`AGENTS.md`, `## Cycle`). The old cycle stays read-only.

## Log

- **L1** (2026-11-04, user, verbatim): "Read methodology V-SIL-v3. Plan in odd/tasks all the reafactors needed to implement all the methodology flow. What is the idea. Take the simplest version possible of each skill and implement a full flow ready to use. plan each skill or step as a different file of plan. Remeber reuse the current tools already implemented, like \"codeanvil status, now, sync, create, init, etc ,etc...\" to not refactor all, just skills. If you have a question ask directly to me. Stop when planning implementation stage, because i dont know how to do it."
- **L2** (2026-11-04, user, verbatim answer on custody-chain): "move the skill outside for now in templates/backups/ please. Do not custody chain for now" → S6, C5, T6. The move is planned, not executed: `tests/test_create.py:332,391,413` and `config.yaml` pin the skill until T6.
- **L3** Evidence: read the paper, `S1_G1_template.md`, the G0/G1/CC skills, `status.py`, `create.py`, the chat-only v3 README and plans. Observed `g0_validate.py` exit 0 on `templates/no-tools-skills/v3/test-inputs/`. Not run: any new skill, because none exists yet.
- **L4** Next step: the user decides how S2 works (T8). G2 follows from it (T9).
- **L5** (2026-11-04, user, verbatim): "Change this. No deterministic gates. The only determniistic gate is the S0 normalization. The rest are all HITL. Or in stage validation the interface contracts, but is not deterministic, is validation agent driven with harness of interfaces contraact and sandwich tests" → S7, C0, C4, C5, C6, C9. Removed `g1_check.py`, its tests and the digest stop; removed G1's separate-session rule because the human is now the oracle. T1, T2, T5 and T7 plans revised; S0, RFD and CHAIN unaffected.
- **L6** Open: `methodology/V-SIL-v3/` still states P3 and marks G1 checks as mechanically verifiable. Not edited, because the request was about the plans. Closed by L7.
- **L7** (2026-11-04, user, verbatim): "Update inconsistencies in V-SIL-v3 about G1 not deterministic + current incsistence of RFD" → paper, Spanish mirror, template and diagrams updated: P3 scoped to G0, G1 is a human review, RFD route and §9.2 row added for G1, "any stage" replaced by S1, G1 or any G2 sub-gate. G1 plan gained the RFD recommendation.
- **L8** (2026-11-04, user, verbatim): "Add to S1 skill a part where describes full graph of dependencies in ascii here in chat. remember as spider each service, etc" → S8. The skill does not exist yet, so T2's plan and T7's expected output changed. The map is also stored in `S1.md` so a later G1 session can read it; no section was added to the paper's template. Replaced by L9.
- **L9** (2026-11-04, user, verbatim): "Change that ascii diagrams to an html artifact using vis. Just add as text inside html the metadata of .codeanvil/project.yaml to difference designs\nRemember to mantain agent orchestration based in reports" and "See an example if what i like @methodology/V-SIL-v3/spider-vis-network.html" → S9. Prototype in `odd/tasks/2026-11-04_S1_graph_prototype.html`, on vis-network 9.1.9 from the user's example; both views rendered in headless Chromium with no console errors. `S1.md` stays the only state; G1 and `codeanvil status` never read the HTML. T2, T1 and T7 plans revised.
- **L10** (2026-11-04, user, verbatim, after opening the prototype): "delete build order. The rest is ok" → prototype reduced to the spiders view plus manifest text; internal contracts and `PATH-*` removed from its data block. Build order stays in the design document only. T2 and T7 plans revised.
- **L11** (2026-11-04, user, verbatim, on the manifest panel): "Add to this item shading to difference bolck toiagram" → panel shaded with a grey background, border and shadow, and moved above the diagram because the floating panel covered a node.
- **L12** (2026-11-04, user, verbatim): "Give me an example of template and various examples of  different services to see if I like it" → `odd/tasks/2026-11-04_S1_graph_examples/`: the blank template and five illustrative designs, from one service without hardware to six services. It replaces `2026-11-04_S1_graph_prototype.html`, which was removed. Added module ids prefixed by service, array `from`/`to` on contracts and on hardware, a color palette, and `layout.randomSeed`. Two renders of each page were byte-identical. Pending: the user's verdict on the look.
- **L13** (2026-11-04, user, verbatim): "I like it. So modify S1 and G1 knowing that now tool" → template approved as the fixed tool. Assumption: "S1 and G1" means their plans, because neither skill exists yet. S1 plan gained the `DATA` field mapping and the rule never to write the page by hand; G1 plan gained the Graph checklist row and the rule that the graph never decides. The paper and `S1_G1_template.md` are unchanged, because the graph is a reading aid and not a methodology step.
- **L14** (2026-11-04, user, verbatim): "Remember autocontained skill. Im refering for example. The templates, scripts and other tools used for the skill in the same .agents/skills/<folder-skill>" → S10, C10. Audit found three breaks, now fixed in the plans: S1 read G1's checklist; S0 read blueprints inside the G0 skill; S1's graph loaded vis-network from a CDN. S1 now vendors vis-network in its `assets/`. Evidence: in a mock project with all network access blocked, the page loaded the vendored 9.1.9 by relative path and rendered byte-identical to the CDN version.
- **L15** (2026-11-04, user, verbatim): "Now see if your plans uses the current report-orchestration artifacts" → read-only audit. Sample reports in the planned format parsed correctly through `_cycle_reports`, and artifact subfolders stayed out of it. Found: rework routed to the wrong skill, a PASS going stale, stage PASS undefined, a closed cycle looking open.
- **L16** (2026-11-04, user, verbatim): "yes, add it to the plans. You can refactor also \"status\". But mantain sync, and now" → S11, C2, C4, C11, T10. Skills route rework from reports, and `status` adds chain order, `delivered`, stale markers and closed cycles. The earlier idea of renaming the `CC` test fixture was dropped, because it now pins that old report ids are still listed.
- **L17** (2026-11-04, user, verbatim): "Perfect. Now verify logic of all plans. Validation dimensions: \"Zero death code, try to use all modules cunrrently implemented if are not touched to plan\", \"full flow of planned skills have logic?\", \"report-based agent orchestration is used?, all trazable?\"" → two independent read-only reviews; all dimensions PASS WITH FIXES. **Open blockers, not applied to these plans:**
  1. A refused `Verdict: RFD` deadlocks the cycle under C2 step 3. Fix: the human's RFD answer is binding, and a `Withdrawn` outcome returns to ordinary FEEDBACK.
  2. RFD re-entry hits S0's hand-written-pair prompt, because `S0.md` is cycle-scoped. Fix: "hand-written" means no `S0.md` in any cycle.
  3. After RFD switches cycle, `status` shows no active cycle, because `_cycle_reports` drops empty folders. Fix (T10): always print the manifest's active cycle.
  4. The resume rule misses a fully stale chain. Fix: resume at the first report that is missing, not at PASS, or stale.
  5. The report schema is not inline in the skills, and `HITL: PASS` as written parses as `UNKNOWN`. Fix: each skill states the exact `| HITL | PASS |` row, and tests assert it.
  6. Blueprint placeholders in block bodies pass G0 (exit 0 reproduced). Fix: G0 shows S0's missing list before Gate H; correct the S0 plan's "G0 rejects it".
  7. Verdicts cannot be traced to content or decider. Fix: information-only digest lines and `Decided by: <name>`.
  8. T3's scaffold assertion fails until T6. Fix: move it to the T5/T6 commit.

  Dead code the plans cause or keep: the `.provenance/` path replacement, the `.codeanvil/custody/` mkdir and `PROJECT_CUSTODY`, the `template_dir` keys, and stale docs in `parser.py:31,45`, `README.md:164-166,173`, `templates/GT/README.md` and `methodology/test/README.md:22,92,96`. Pre-existing: `valid_structure_SRS.py`, `check_project_path`, `marconi.requires`. Advisories: an open RFD does not suspend S0, G0 and S1; G1 PASS needs a "S2 not available yet" return; RFD has no mode table and its write order is unset; T7 and the CHAIN differential need a scratch `HOME`; `TEMPLATE_AGENT.md:101,112,170` contradict S0 correcting GT; the FAIL to FEEDBACK mapping is unstated; `status` exiting 1 without a DB is undefined for C2 step 2.
- **L18** (2026-11-04, user, verbatim): "Ok. noproblem for now. apporved plans. commit ans push plans. await instructions to start implementing" → plans approved and committed as they stand, with L17's blockers still open. Assumption: "noproblem for now" defers those fixes, so they are not applied. Do not start implementing until the user says so; resolve L17 and T8 (S2 shape) first.
- **L19** (2026-11-04, user, verbatim): "Start implementing @odd/tasks/2026-11-04_1042_vsil_v3_skill_flow.md" → implementation of T10, T3, T4, T2, T1, T5+T6 and the docs of T7, inline (no Writer trigger). Chain strategy asked once and answered `feature-branch-chain`.
- **L20** Evidence. Suite: 234 → 252 passed (`uv run --extra dev pytest`); `templates/tests` 93 passed unchanged; `g0_validate.py` and `RULES.md` unchanged. RED observed for T10 (7 failed first) and for the chain switch (5 failed first); the skill-text tests were written after the skills, so they have no RED. Differential `status` vs base commit in a scratch HOME: the only difference is the requested chain ordering. A wheel built in scratch ships the five skills and `vis-network.min.js`, and no `templates/backups/`. Scaffold smoke test: five skills, the four-row chain table, `g0_validate.py` exit 0 on the FM pair. vis-network 9.1.9 vendored byte-identical to the cdnjs file (sha256 f6ee3a65…).
- **L21** L17 blockers, as implemented: (1) RFD answer binding and `Outcome: Withdrawn` returns to FEEDBACK (RFD, S1, G1, G0 skills); (2) S0's hand-written-pair row means no `S0.md` in any cycle; (3) `status` always prints the active cycle; (4) resume rule in AGENTS template covers missing, not-PASS and stale; (5) each skill states the exact `| HITL | PASS |` row and tests assert it; (6) G0 shows S0's missing list before Gate H; (7) GT digest lines and `Decided by:` added; (8) the scaffold assertions are in the T5/T6 commit. Dead code removed: the `template_dir` keys, the `.provenance/` replacement and the stale text in `parser.py`, READMEs and docs. Kept on purpose: `PROJECT_CUSTODY` and its mkdir (pinned by `tests/test_sync.py` and `tests/test_paths.py`) and the pre-existing `valid_structure_SRS.py`, `check_project_path` and `marconi.requires`.
- **L22** Not run: the agent-driven procedure of T7 (`methodology/test/README.md`, prompts 1-6 and the failure table), which needs a sandboxed agent runtime. The flow is NOT ready to use end to end until that run, T8 and T9. The advisories of L17 not listed in L21 (an open RFD does not suspend S0, G0 and S1; the FAIL to FEEDBACK mapping; `status` exit 1 without a DB) stay open.
- **L23** (2026-11-04, user, verbatim): "Validate plan vs implemention befire pushing" → read-only audit, then two doc fixes (README quickstart, `status` help text). Result: every task of the plans is implemented as specified except the deviations below. Differential vs the merge-base in a scratch HOME: `init`, `create`, `list`, `now`, `sync`, `status` (empty and legacy reports) are identical apart from a timestamp, and `--help` differs only in the requested epilog. `S1_artifacts/` and `RFD_artifacts/` do not appear in `status`. The graph template, filled with an example design and served from a mock project, rendered a canvas in headless Chromium with no network. **Deviations from the plans:** (a) `template_dir` keys and the `.provenance/` path replacement were removed instead of kept (L17 flagged them as dead code); (b) G1_CHECKLIST.md is 44 lines against the plan's ~130 because it is one table plus the filled form; (c) the G0 skill's "Do not load" text says "do not use it for the design: that is S1 and G1" instead of the planned wording. **Still open:** the T7 agent-driven run; an open RFD does not stop S0.
- **L24** (2026-11-04, user, verbatim): "Implement this logic. When RFD is triggered, the project needs a new cycle, son expect a new name and redo all the flow" → assumption: "triggered" means an RFD decided with a deviation accepted (a raised RFD still suspends the old cycle, and `Outcome: Withdrawn` keeps it). The RFD skill requires a new unique cycle name and records the Build Package digest; S0, G0, S1 and G1 refuse to run in the closed cycle; S0 refuses an unchanged Build Package in the new cycle. Tests: 252 → 255. Text contracts only, so the behaviour still needs the T7 agent run.


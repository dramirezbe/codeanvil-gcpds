# No-tools skills v3 — V-SIL v3 chat-only skill set

Objective: chat-only (no tools) skill set in `templates/no-tools-skills/v3/` covering the full V-SIL v3 flow (Build Package → S0/G0 → S1/G1 → S2/G2 → Verified Prototype | RFD), plus FM-spectrogram test inputs.
Branch: `feat/no-tools-skills-v3` · Delivery: `ask-on-risk` · Test runner: none (passive Markdown; structural readback + manual G0 dry-run of test inputs).

## Specs

- **S1** — "Toma @templates/no-tools-skills/v2/ y dame v3/ leyendo el refactor de @methodology/V-SIL-v3/ y leyendo el estilo de skill (solo chat, sin tools)". Output dir: `templates/no-tools-skills/v3/`.
- **S2** — "Genera un conjunto de skills (solo chat, sin tools) que cubran **todo el flujo V-SIL v3**, desde la captura de requisitos hasta el software verificado y validado." Each skill: "Seguir la **estructura y estilo de v2**", "Implementar la **metodología definida en V-SIL-v3** (no la de v2)", "Representar una fase o artefacto concreto del flujo v3", "Ser autocontenida: incluir inputs esperados, outputs generados, y criterios de aceptación."
- **S3** — Naming: "Usa un prefijo `S#` secuencial (S1, S2, S3…) alineado con el orden del flujo V-SIL-v3." combined with the first request "a qué S# pertenece y luego el # de skill". Assumption: prefix `S<stage>-<n>` where `<stage>` is the V-SIL v3 stage (S0, S1, S2) the skill belongs to (its gate included) and `<n>` the skill number inside it; the cross-stage RFD skill uses `SX-1`.
- **S4** — Test inputs in `templates/no-tools-skills/v3/test-inputs/`: "**Proyecto de prueba:** Espectrograma FM en tiempo real con HackRF One. Entrada RF: banda FM comercial (~88–108 MHz). Salida: visualización de espectrograma en pantalla. Stack: Python + GNU Radio o acceso directo vía libhackrf." At least "**StSR** (Stakeholder Requirements Specification)" and "**SySR** (System Requirements Specification)", "lo suficientemente sencillos para probar el flujo completo de las skills pero técnicamente correctos."
- **S5** — ODD planning in `odd/tasks/`: "recuerda usar la fecha de hoy como nombre de archivo luego a qué S# pertenece y luego el # de skill". Each plan file includes: "**Objetivo**", "**Inputs**", "**Outputs**", "**Prompt template** resumido", "**Criterios de aceptación**", "**Dependencias**", "**Mapeo V-SIL-v3**". "Planea **todas** las skills con lujo de detalle antes de empezar a escribirlas."
- **S6** — Constraints: "Las skills son **solo chat** (sin tools, sin acceso a archivos, sin ejecución de código)." "No asumas herramientas externas en las skills; el LLM guía al usuario paso a paso."

## Tasks

| ID | Specs | Deliverable | Route | Status | Commit |
|----|-------|-------------|-------|--------|--------|
| T1 | S3, S5 | Feature doc + 8 per-skill plan files `odd/tasks/2026-11-01_S<stage>-<n>_<slug>.md` | inline | done | `469773e` |
| T2 | S4 | `test-inputs/` — Build Package, G0_StRS, G0_SyRS, README | inline | done (g0_validate.py: 0 errors / 0 warnings) | `7458e12` |
| T1v | S5 | Independent logic verification of the plans (skill-creator + skill-improver lens) | delegated (fresh agent) | done — 2 BLOCKER, 10 MAJOR, 10 MINOR (L6) | — |
| T1f | S5 | Apply T1v findings to the plans (C1–C12 + per-plan fixes, L7) | inline | done | see Log |
| T2b | S4 | FAIL-path fixtures in `test-inputs/fixtures/`: `F1_G0_fail_StRS.md` (seeded errors: missing §2.7, bad SemVer, STK without Verification, HWC orphan component, duplicate ID) + `F1_expected.md`; `F2_S1_design_defective.md` (cycle in DAG, contract without stub recipe, HW module at VL-1, module touching HW outside HAL) + `F2_expected.md`; `F3_pastes.md` (green/red pytest outputs, a skipped-test output for C4, SIL metric table, 30-min soak log with 7 overflows at 20 MS/s plus a 16 MS/s run with 0 overflows but 90–106 MHz coverage → SX-1 RFD, a module bug paste → module defect, an unchanged-module failure → self-diagnosis) | inline | planned (on hold with T3–T6) | — |
| T3 | S1, S2, S6 | S0-1 normalisation + S0-2 G0/Gate H skills | inline | on hold (L5) | — |
| T4 | S1, S2, S6 | S1-1 layered architecture + S1-2 G1 review skills | inline | on hold (L5) | — |
| T5 | S1, S2, S6 | S2-1 base layer, S2-2 modules, S2-3 G2 skills | inline | on hold (L5) | — |
| T6 | S1, S2, S6 | SX-1 RFD skill + v3 README index (lookup table skill → stage/gate → plan, record formats C3, flow diagram) | inline | on hold (L5) | — |

Route evidence: units share one output contract chain (S1-1's document format is S1-2's and S2-x's input), so they are not independent → no Writer trigger; all inline.

## Shared contracts (C0–C12) — every plan references these

- **C0 No deviation from the methodology (L8).** Every stage, gate, route, outcome and
  record in the plans must be grounded in `methodology/V-SIL-v3/V-SIL_v3.md` (or its
  `S1_G1_template.md` for S1/G1 detail). Plans may add chat mechanics only (pauses, paste
  formats, answer domains) — never a new route, outcome, actor or decision rule. The
  only routes are the paper's: G0 FAIL → S0 · G0 PASS + Gate H → S1 · G1 PASS → S2 ·
  G1 FAIL → S1 · G2 PASS → Verified Prototype · G2 design → S1 · G2 module → S2 ·
  S1/G2 (any stage) infeasible → RFD → updated Build Package → S0.

- **C1 Skill skeleton (v2 structure).** Every skill has, in order: title + "V-SIL v3 | <Stage/Gate> | No-Tools Variant"; Definitions table (v3 terms; the v2 "SRS produced at G1" entry is replaced by "S1 design document"); **Activation Contract** (Load when / Do NOT load when); Preconditions; Decision Gates table; numbered Steps; output formats; Ground rules.
- **C2 Closed answer domains.** Every human prompt lists its allowed answers `[a/b/c]` with a default. A question about the prompt is answered, then the prompt is shown again. Ambiguous input or "go ahead" / "continue" in place of an answer → re-ask. Applies to: Gate H `[y/N]`, S1-1 Job 0 `[y/N/x]`, S1-2 independence `[y/n]`, S2-2 out-of-order `[k/o/x]`, S2-3 VL declaration (per-module `VL-0|VL-1|VL-2` or scenario `fast|dsp|pre|full`, paper §8.2).
- **C3 Records (copy-paste handoff blocks).** Every handoff between skills is a fenced text block the user pastes into the next chat:
  - `G0 RECORD` — StRS/SyRS ID+version, G0 verdict, Gate H outcome/date/authoriser, **block inventory** (every NRM/HWC/STK/SYS ID with its Status). S1-1 compares the pasted GT against it.
  - `G1 RECORD` — S1 design version, reviewer, verdict, **contract list** `contract_id@schema_version`, module list `module@required_vl`.
  - `MODULE LEDGER` — `| cycle | step | module | g1_version | unit | bottom-up | regression | evidence_ref | state |`, state ∈ `VALID | VOID(reason)`.
  - `DESIGN DEFECT NOTE` — raised by S1-2/S2-1/S2-2/S2-3: affected S1 section(s), contract/module IDs, evidence (with VL), S1-1 jobs to re-run.
  - `RFD SEED` — stage, requirement IDs, evidence with VL or `ANALYSIS (no VL)`.
- **C4 Evidence rule (P2/P4).** A test step counts as passed only when the user pastes: the exact command line the skill emitted, and runner output whose test count and test names equal the list of tests the skill wrote. Missing, skipped, renamed or extra tests → `NOT EVIDENCED`. Measurements the user describes in words (HIL photos, scope readings) are labelled `USER-ATTESTED`. The LLM never invents, simulates or rounds a measurement.
- **C5 Independence (P2).** Reviewer skills (S1-2, S2-3) start with a check that they did not author what they review: refuse if the artefact is this conversation's own earlier output, or if the user answers `y` to "was it produced in this chat?". Expected values in tests (S2-1/S2-2) are copied verbatim from the G1-approved §3 reference vectors and the SyRS acceptance criteria — never authored by the implementer.
- **C6 Non-determinism disclaimer.** S0-2, S1-2 and S2-3 carry the v2 disclaimer: the "mechanical" checks are LLM-executed, so P3 (mechanical rejection beats LLM approval) is only approximated in chat; a deterministic tool overrides the chat verdict where one exists.
- **C7 Context pack + new chat.** Each skill states its minimal paste set and whether it must start in a new chat: S0-1 (BP) · S0-2 new chat (StRS+SyRS) · S1-1 (StRS+SyRS+G0 RECORD) · S1-2 **new chat** (S1 design + SyRS + StRS §3) · S2-1 (S1 design §1–§3 + G1 RECORD) · S2-2 (module's §1.3 card + its §3 contracts + base-layer contract types + LEDGER) · S2-3 **new chat** (S1 §1.3 profiles + §3 vectors + SyRS acceptance criteria + LEDGER + fresh suite run) · SX-1 (RFD SEED + cited blocks).
- **C8 HAL ownership (paper §5.1 vs §5.2).** The base layer owns the **HAL port** (abstract interface + its deterministic stub) — written by S2-1. The concrete **device adapter** (e.g. `hackrf_source`) is a module in layer `HAL` with `hw_dependency: true ⇒ required_vl: VL-2` — declared by S1-1, implemented by S2-2 (first in topological order). No other module touches hardware.
- **C9 Evidence invalidation.** (a) A new G1 RECORD voids every LEDGER row whose module consumes/provides a contract whose `schema_version` changed, plus the S2-1 base evidence if a base-layer contract changed. (b) Reworking module k voids k's row and the regression column of every row after k. (c) VOID rows must be re-run before S2-3.
- **C10 Cycles.** A cycle id is set at S1-1 Job 0 and carried in every record. A new cycle (e.g. `fast_01` → `pre_release_01`) re-enters at S2-3 if the code is unchanged; if code changed, the affected modules go through S2-2 rework first. G2.0 is always a fresh full-suite run tagged with the current cycle id (paper §8.2 "every cycle").
- **C11 Integration.** The last S2-2 run is the **integration run** (paper §5.1 "Integration"): all modules real, no stubs except the HAL stub at VL-0; full suite pasted.
- **C12 Defect vs infeasibility (paper §9, verbatim criteria).** "A **defect** means V-SIL can fix it internally. The implementation or the design is wrong, but the requirements are achievable" → design defect → S1, module defect → S2 (§9.1, incl. self-diagnosis). "An **RFD** means the Build Package requirements are **infeasible on the declared COTS platform**" (§9.2) — shown by evidence, as in RFD-001, that the conflicting requirements are not met simultaneously by the configurations evaluated. Trade-off options may include design changes that require S1 rework, exactly like RFD-001 option C ("Dual-mode … both met, adds complexity" → "new module, new interface contract, S1 rework"); the Build Package author chooses (§9.2: "V-SIL **suspends** until the Build Package is updated and re-enters at S0"). No extra criterion is added.
- **C8 grounding note.** C8 restates the paper, it does not extend it: §5.1 puts the HAL in the base layer and §5.2 models `iq_acquisition` as a HAL-layer module with `hw_dependency` = yes and VL-2.

## Skill map (V-SIL v3 → skill)

| Skill | V-SIL v3 | Plan file |
|-------|----------|-----------|
| `S0-1` Build Package normalisation | §3 S0 | `2026-11-01_S0-1_normalise_build_package.md` |
| `S0-2` G0 structural validation + Gate H | §4 G0 | `2026-11-01_S0-2_g0_structural_validation.md` |
| `S1-1` Layered architecture design | §5 S1 + S1_G1_template §0–§6 | `2026-11-01_S1-1_layered_architecture_design.md` |
| `S1-2` G1 design review | §6 G1 + S1_G1_template G1.1–G1.8 | `2026-11-01_S1-2_g1_design_review.md` |
| `S2-1` Base layer + stubs + top-down integration | §7 S2 Step 1 | `2026-11-01_S2-1_base_layer_and_stubs.md` |
| `S2-2` Module implementation (DAG order) | §7 S2 Step 2 | `2026-11-01_S2-2_module_implementation.md` |
| `S2-3` G2 adaptive verification + Verified Prototype | §8 G2, §9.1, §10 | `2026-11-01_S2-3_g2_adaptive_verification.md` |
| `SX-1` Request for Deviation | §9.2–§9.4 | `2026-11-01_SX-1_request_for_deviation.md` |

## Log

- **L1** (2026-11-01, user, verbatim first request): "Toma @templates/no-tools-skills/v2/ y dame v3/ leyendo el refactor de @methodology/V-SIL-v3/ y leyendo el estilo de skill (solo chat, sin tools), haz las skills vagamente que representen todo el flujo de v2 hasta el software completo. Dame un ejemplo de StSR y SySR para probar estas skills. Active odd y en odd/tasks planea todas las skills recuerda usar la fecha de hoy como ombre de archivo luego a qué S# pertenece y luego el # de skill. Planea todas las skills con lujo de detalle. Recuerda seguir @templates/no-tools-skills/v2/ pero para la metodología definida en V-SIL-v3"
- **L2** (2026-11-01, user refinement): structured prompt — Contexto / Tarea principal / Nomenclatura `S#` / Test inputs FM HackRF / Planificación ODD (Objetivo, Inputs, Outputs, Prompt template, Criterios de aceptación, Dependencias, Mapeo V-SIL-v3) / Restricciones solo-chat. Quoted in S2–S6.
- **L3** Decisions: (a) v3 drops the G1 SRS (v2) — S1 now produces the layered-architecture design document of `methodology/V-SIL-v3/S1_G1_template.md`; v2's multi-hypothesis + QA scoring survives inside S1-1 as the partitioning decision DEC-001. (b) G0 rules are unchanged from v2 (paper §4: same deterministic gate) plus human Gate H. (c) Skills are English (Language Domain Contract); test inputs English so G0 heading rules apply verbatim. (d) Chat-only implementation skills (S2-x) emit code in chat; the user runs it and pastes output — no pass claim without pasted evidence (P2/P3/P4).
- **L5** (2026-11-01, user, verbatim): "Do nnit implement, up a subagent with no memory to verify the plans with skill skill-creator and skill-improver. But what is the idea, just logic verification, no .claude/skills/ and yaml header." → skill writing (T3–T6) on hold; T1v launched (read-only, logic only, out of scope: install paths and YAML frontmatter).
- **L6** T1v verdict: SX-1 UNSOUND; other 7 SOUND WITH FIXES. BLOCKERs: B1 SX-1 defect-vs-RFD test contradicts its own FM case (dual-tune sweep on same COTS ⇒ defect, not RFD; paper RFD-001 option C has the same tension) → RFD needs "violates another BP constraint" clause; B2 S0-1 no-invention rule vs test SyRS design parameters (N=2048, K=16, 5-bin DC) → user-confirmed derivations. MAJORs: M1 no P2 independence in S2-3; M2 G2.0 must be a fresh full-suite run per cycle; M3 HAL vs device-adapter ownership; M4 S2-2 rework mode; M5 shared Design Defect Note + evidence invalidation; M6 GT-gap path (missing SyRS threshold ≠ S1 defect); M7 G1.x blocking/advisory table; M8 evidence must match emitted test list; M9 FAIL-path fixtures; M10 Activation/Definitions sections. Minors m1–m10 incl. naming confirmation.
- **L7** (2026-11-01, user, verbatim): "Fix" → T1f: shared contracts C1–C12 added above; every plan edited (B1→C12 in SX-1; B2 user-confirmed derivations in S0-1; M1/m4→C5; M2/C10 in S2-3; M3→C8; M4 rework mode S2-2; M5→C3 Design Defect Note + C9; M6→C3 GT Gap Note; M7 blocking table S1-2; M8→C4; M9→T2b; M10→C1; m1–m9 per plan). m10: naming unchanged (user did not change it); README lookup table added to T6. Skills still not written.
- **L8** (2026-11-01, user, verbatim): "NO deviation for @methodology/V-SIL-v3/V-SIL_v3.md" → C0 added; removed every addition not grounded in the paper: GT GAP NOTE route to S0 (a SyRS gap now goes through the paper's routes: S1 risk §6 / G1.8 → RFD, or design defect → S1), the extra RFD criterion in C12 (now paper §9 verbatim; RFD-001 option C-style design options are valid RFD options), S0-1 SyRS proposals (S0 "normalises only"; missing BP content → placeholder → G0 FAIL → S0, so the test Build Package now carries the system-level technical annex), the Gate H `r` (RFD) answer, SX-1 outcomes `MORE EVIDENCE` / `REJECT` and the "≥ 1 option changes COTS" rule. Reviewer findings B1/B2/M6 are thus resolved by the paper's own rules.
- **L9** (2026-11-01, user, verbatim): "Perfect. Now start a mode step-by-step. Im gonna call another subagent, not in claude code to di the code skill by skill. You are just gonnna verify and then see if plan approaches skill. Do not test it, just read it and see plan." → T3–T6 route: written by an external agent, one skill at a time; this session only reads each skill and checks it against its plan, C0–C12 and the paper (no tests, no edits).
- **L10** S0-1 review (rev 0, 783 lines): MATCHES WITH GAPS — plan outputs, steps, Step R, acceptance 1–5 covered; 4 corrections sent, all "normalise only" (paper §3): Compliance/Status inferred instead of BP-copied (→ PENDING / PROPOSED markers), STK Standard(s) inherited from NRM dependencies, §5.x filled by vocabulary heuristic. Agent open points 1, 2, 4 accepted; 3 answered by correction 2.
- **L11** (2026-11-01, user, verbatim): "next skill, pass. await" → S0-1 passed by the user; build_package.md left unchanged (verify-only mode). Awaiting S0-2.
- **L12** S0-2 review (rev 0, 504 lines): MATCHES WITH GAPS — all v2 G0 rules, verdict rules, disclaimer (C6), P2/new chat (C7), Gate H `[y/N]`, G0 RECORD with block inventory (C3) and routes (C0) match the plan. 1 correction: on `N` the skill tells the human to carry reasons to S0-1 instead of collecting them (plan Output 5) — S0-1 Step R expects S0-2 to hand back numbered reasons tagged with block IDs.
- **L13** (2026-11-01, user, verbatim correction for S0-2 rev 1; applied to `templates/no-tools-skills/v3/S0-2_SKILL.md` Step 7 only):

  ````
  Correction for S0-2 (Revision 1). Apply only this; everything else is approved.

  Step 7 "On `N` — not authorised" contradicts the plan (Output 5) and breaks the handoff to
  S0-1 Step R, which expects "numbered reasons, each tagged with its block ID(s)" handed back
  by S0-2. Replace the "Do not ask for the reasons inside this run" paragraph with:

  1. After `GATE H: NOT AUTHORISED`, ask (instruction line, not a choice prompt):
     "List your reasons, one per line, each starting with the block ID(s) it concerns
     (e.g. `STK-SPEC-002: latency bound not verifiable`). Type `done` when finished."
  2. Check each tagged ID against the Phase 3 block inventory; an unknown ID → ask the user to
     correct that line (never drop or rewrite a reason).
  3. Emit the handoff block, verbatim reasons, no G0 RECORD:
     ```
     GATE H RETURN
     =====================================================================
     StRS: <ID> v<X.Y.Z> · SyRS: <ID> v<X.Y.Z> · G0 verdict: PASS
     Gate H: NOT AUTHORISED — <YYYY-MM-DD> — <authoriser>
     | # | Block ID(s) | Reason (verbatim) |
     |---|-------------|-------------------|
     =====================================================================
     → S0 (S0-1), new chat: paste this block together with the Build Package.
     ```
  The skill never suggests, words or completes the reasons for the user.
  ````
- **L14** (2026-11-01, user, verbatim): "Verify. After verify, yourself implement the rest of skills please" → S0-2 rev 1 verified: PASS (Step 7 `N` path collects tagged reasons, checks IDs against the inventory, emits `GATE H RETURN`). T4–T6 route changed: written inline by this session from the plans (S1-1, S1-2, S2-1, S2-2, S2-3, SX-1 + v3 README), following the conventions of the approved S0-1/S0-2.
- **L4** Pre-existing user working-tree changes (v2 move, `.atl/` registry) left unstaged and untouched.

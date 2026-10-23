---
name: g1-start-design
description: "Trigger: G1, start design, design synthesis, architecture, SRS, trade study, ATAM. Multi-hypothesis software architecture design from G0-validated StRS + SyRS; produces and validates the SRS (IEEE 29148 §9.6)."
license: Apache-2.0
compatibility: "Works in any agent runtime with file read/write. No network required."
metadata:
  author: "gcpds"
  version: "2.0"
  gate: "G1"
  pipeline: "V-SIL"
---

# G1 — Design Synthesis from Ground Truth

## Prerequisite and Cycle

The custody chain must have passed.

Before starting:

1. Resolve the active cycle from `.codeanvil/project.yaml` (the `cycle:` key).
   If the key is missing, stop and ask the user for a cycle name (see
   `AGENTS.md`, `## Cycle`).
2. Read `.codeanvil/report/<cycle-name>/CC.md`. If the file does not exist, or
   its **latest** iteration is not `HITL: PASS`, stop and return exactly:

   > Custody chain must pass first. Run the custody-chain skill.

   Write no report iteration and run no G1 job in that case.

## Report Contract

Write exactly one iterative report file: `.codeanvil/report/<cycle-name>/G1.md`.
The design artifacts of the jobs below are separate working files (see
`## Artifacts`) — they are not report iterations.

- First run: write the header and `## Iteration 1`.
- Later runs: append `## Iteration <N>`, where `N` is the number of existing
  iterations plus one.
- Header fields: `Gate` = `G1`, `Cycle` = the active cycle, `Document` = the GT
  files plus `GT/G1_SRS.md`, `Created` = `codeanvil now`.
- Iteration fields: `Date` = `codeanvil now`, `Timestamp` = `codeanvil now --machine`,
  `Iteration` = `N`, `Cycle` = the active cycle, `HITL` = `PASS` or `FEEDBACK`.
- A `FEEDBACK` iteration records the user's comments and the jobs to rework; the
  rework appends the next iteration. The final approved iteration is `HITL: PASS`.

Never edit a previous iteration. Iterations are append-only; the latest
iteration is the gate state.

## Artifacts

Each job writes its design output to its own file under
`.codeanvil/report/<cycle-name>/G1_artifacts/`, next to the `G1.md` report:

```
.codeanvil/report/<cycle-name>/
├── G0.md
├── CC.md
├── G1.md                 # HITL report — iterations and verdicts only
└── G1_artifacts/         # design working files
    ├── ASR.md
    ├── Arch_01.md … Arch_NN.md
    ├── QA_matrix.md
    ├── ATAM.md
    ├── ADD.md
    └── review_package.md
```

| Job | File | Content |
|---|---|---|
| 1 | `ASR.md` | Extracted ASRs and their Condition Groups |
| 3 | `Arch_01.md` … `Arch_NN.md` | One file per architecture candidate, in generation order |
| 4 | `QA_matrix.md` | QA × Architecture scores |
| 5 | `ATAM.md` | Trade study: sensitivity points, tradeoff points, risks, verdict |
| 6 | `ADD.md` | Attribute-Driven Design decomposition and the component dependency graph |
| 9 | `review_package.md` | Consolidated review package |

Rules:

- `Arch_NN.md` uses zero-padded two-digit numbers matching generation order
  (`Arch_01.md`, `Arch_02.md`, …).
- Create `G1_artifacts/` on the first write (Job 1).
- On rework, **overwrite** the artifact file — never append. The artifact always
  holds the latest version; `G1.md` is what tracks iterations.
- Artifacts are working material — auditable but not GT. `GT/G1_SRS.md` stays the
  only GT-level deliverable (Job 7).

## Activation Contract

Load this skill when the Ground Truth pair has **passed G0 and the custody chain (CC)**
and software design must begin: architecture synthesis, the multi-hypothesis trade
study, SRS authoring, or a G1 review package.

Do **not** load it for GT validation (that is G0) or implementation (that is G2+).

## Hard Rules

- **The prerequisite chain must have passed.** `CC.md`'s latest iteration must be
  `HITL: PASS` (which in turn required G0 to pass) before starting.
- **The GT is locked by CC.** The custody-chain seal is the lock — never edit
  `GT/G0_StRS.md` or `GT/G0_SyRS.md` during G1. Gaps go in the SRS Gap List,
  not into silent GT edits.
- **Multi-hypothesis is mandatory.** Generate and score multiple candidate
  architectures (minimum 3); a single-candidate design is not a G1 output.
  The user chooses how many candidates before Job 2.
- **Every REQ- traces to a SYS-.** No software requirement may exist without upstream
  justification in the approved SyRS.
- **The SRS is the G1 deliverable.** Author it at `GT/G1_SRS.md` following the
  `G1_SRS.md` template (in the CodeAnvil repo: `templates/GT/G1_SRS.md`; request a
  copy if your project does not have one yet). Validate it structurally before the
  review package.

## Inputs and Outputs

| | Path | Notes |
|---|---|---|
| Input | `GT/G0_StRS.md` | G0-validated Stakeholder Requirements Specification |
| Input | `GT/G0_SyRS.md` | G0-validated System Requirements Specification |
| Output | `GT/G1_SRS.md` | Software Requirements Specification (REQ- blocks) |
| Output | `.codeanvil/report/<cycle-name>/G1.md` | Iterative review package + G1 validation report |
| Output | `.codeanvil/report/<cycle-name>/G1_artifacts/` | Per-job design artifacts (`ASR.md`, `Arch_NN.md`, `QA_matrix.md`, `ATAM.md`, `ADD.md`, `review_package.md`) |

## Execution Flow

Work the nine jobs **in order**, pausing after each for the user. After every
job ask **PASS** or **FEEDBACK**:

- **PASS** moves on to the next job.
- **FEEDBACK** appends one report iteration with the user's comments, then
  redoes the named jobs and their downstream jobs.
- The final job's PASS appends the closing iteration with `HITL: PASS`.

0. **GT Integrity Check** — run `source_snapshot.py verify --strict` against the
   CC snapshot. If PASS, the GT is confirmed intact since sealing — proceed to
   Job 1. If FAIL, stop: the GT was tampered after CC sealed it; a new cycle
   starting at G0 is required. No interactive approval — CC already locked the GT.
1. **Extract ASRs** from STK-/HWC-/NRM- (StRS) and SYS- (SyRS) blocks. Priority from
   the block; HWC Impact maps HARD→MUST, SOFT→SHOULD, INFORMATIONAL→COULD; SYS
   priority is inherited from its traced STKs (highest wins), else SHOULD.
   Group into Condition Groups. Write `G1_artifacts/ASR.md`.
2. **Ask the user how many architecture candidates** to generate (minimum 3,
   default 4). Use the runtime's native question mechanism. Record the answer —
   it drives Job 3 and the trade study scope.
3. **Generate N architecture candidates** (where N is the user's answer), each
   addressing every Condition Group. Write each to its own
   `G1_artifacts/Arch_NN.md` in generation order.
4. **Score the QA × Architecture matrix** (ISO 25010 rows, 0–5 cells, weights 3/2/1,
   highest-priority aggregation per row). Write `G1_artifacts/QA_matrix.md`.
5. **ATAM-style trade study** on the top 2: sensitivity points, tradeoff points,
   Condition Group satisfaction, risks, verdict. Write `G1_artifacts/ATAM.md`.
6. **Select and decompose** via iterative Attribute-Driven Design (3–5 iterations);
   produce the complete component dependency graph. Write `G1_artifacts/ADD.md`.
7. **Author the SRS** at `GT/G1_SRS.md` per the template: metadata + companion rows,
   §2 design (libraries with rationale), §3 REQ- blocks
   (`REQ-[A-Z]{2,4}-NNN`, SHALL descriptions, acceptance criteria, `Traces to` SYS-),
   §4–§6 algorithms/schemas/interfaces/error behavior, §7 test cases (≥1 per REQ-),
   §8 traceability (REQ → SYS → STK/NRM/HWC).
8. **Validate the SRS structurally** (the template's G1 Validation Rules):
   metadata placeholders; required sections; REQ- ID format + uniqueness; every
   `Traces to` resolves in the SyRS; testable SHALL + criteria + §7 case; §2.2
   rationale non-empty; Dependencies acyclic and resolvable; §8 lists every REQ-.
   Fix your own drafting errors; report upstream gaps to the user.
9. **Produce the review package** (project, GT basis, ASR catalog, candidates with
   scores, selection rationale, accepted tradeoffs, risks, modules, SRS Gap List)
   at `G1_artifacts/review_package.md` and ask **PASS** or **FEEDBACK** (naming
   the jobs to rework).

### Rework

FEEDBACK re-runs the named jobs and every downstream job that consumed their output
(Job 1 rework ⇒ Jobs 2–9; Job 7 rework ⇒ Jobs 8–9). Each feedback round appends one
report iteration; the package is re-issued as `Rev N`. Every reworked job
**overwrites** its artifact file with the new version. The GT stays sealed — a
GT-changing defect means a new cycle that starts at G0.

## Verdicts

| Verdict | Meaning |
|---------|---------|
| `G1: PASS` | Review package issued, SRS validation PASS, final iteration `HITL: PASS` |
| `G1: FEEDBACK` | Defects or open comments in the named jobs; rework in progress |

## References

- `templates/GT/G1_SRS.md` — the SRS template and its structural validation rules.
- `templates/GT/G0_StRS.md`, `templates/GT/G0_SyRS.md` — the upstream contract.
- IEEE/ISO/IEC 29148:2018 §9.6 — software requirements specification.

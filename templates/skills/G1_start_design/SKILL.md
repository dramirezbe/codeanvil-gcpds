---
name: g1-start-design
description: "Trigger: G1, start design, design synthesis, architecture, SRS, trade study, ATAM. Multi-hypothesis software architecture design from G0-validated StRS + SyRS; produces and validates the SRS (IEEE 29148 §9.6)."
license: Apache-2.0
compatibility: "Works in any agent runtime with file read/write. No network required."
metadata:
  author: "gcpds"
  version: "1.0"
  gate: "G1"
  pipeline: "V-SIL"
---

# G1 — Design Synthesis from Ground Truth

## Activation Contract

Load this skill when the Ground Truth pair has **passed G0** and software design must
begin: architecture synthesis, the multi-hypothesis trade study, SRS authoring, or a
G1 review package.

Do **not** load it for GT validation (that is G0) or implementation (that is G2+).

## Hard Rules

- **G0 must have passed on both documents.** Confirm the G0 reports exist under
  `.codeanvil/report/` (or the user states the result) before starting.
- **The GT is locked at approval.** Never edit `GT/G0_StRS.md` or `GT/G0_SyRS.md`
  during G1. Gaps go in the SRS Gap List, not into silent GT edits.
- **Multi-hypothesis is mandatory.** Generate and score 3–4 candidate architectures;
  a single-candidate design is not a G1 output.
- **Every REQ- traces to a SYS-.** No software requirement may exist without upstream
  justification in the approved SyRS.
- **The SRS is the G1 deliverable.** Author it at `GT/G1_SRS.md` following
  `templates/GT/G1_SRS.md` (template store: the G1_SRS template shipped with this
  project). Validate it structurally before the review package.

## Inputs and Outputs

| | Path | Notes |
|---|---|---|
| Input | `GT/G0_StRS.md` | G0-validated Stakeholder Requirements Specification |
| Input | `GT/G0_SyRS.md` | G0-validated System Requirements Specification |
| Output | `GT/G1_SRS.md` | Software Requirements Specification (REQ- blocks) |
| Output | `.codeanvil/report/G1_<timestamp>.md` | Review package + G1 validation report |

## Execution Flow

Work the eight jobs **in order**, pausing after each for the user:

0. **GT Approval Gate** — present the approval prompt (StRS + SyRS IDs and versions,
   `y`/`N`/`x`). No `y` means no Job 1. The GT is then LOCKED.
1. **Extract ASRs** from STK-/HWC-/NRM- (StRS) and SYS- (SyRS) blocks. Priority from
   the block; HWC Impact maps HARD→MUST, SOFT→SHOULD, INFORMATIONAL→COULD; SYS
   priority is inherited from its traced STKs (highest wins), else SHOULD.
   Group into Condition Groups.
2. **Generate 3–4 architecture candidates**, each addressing every Condition Group.
3. **Score the QA × Architecture matrix** (ISO 25010 rows, 0–5 cells, weights 3/2/1,
   highest-priority aggregation per row).
4. **ATAM-style trade study** on the top 2: sensitivity points, tradeoff points,
   Condition Group satisfaction, risks, verdict.
5. **Select and decompose** via iterative Attribute-Driven Design (3–5 iterations);
   produce the complete component dependency graph.
6. **Author the SRS** at `GT/G1_SRS.md` per the template: metadata + companion rows,
   §2 design (libraries with rationale), §3 REQ- blocks
   (`REQ-[A-Z]{2,4}-NNN`, SHALL descriptions, acceptance criteria, `Traces to` SYS-),
   §4–§6 algorithms/schemas/interfaces/error behavior, §7 test cases (≥1 per REQ-),
   §8 traceability (REQ → SYS → STK/NRM/HWC).
7. **Validate the SRS structurally** (the template's G1 Validation Rules):
   metadata placeholders; required sections; REQ- ID format + uniqueness; every
   `Traces to` resolves in the SyRS; testable SHALL + criteria + §7 case; §2.2
   rationale non-empty; Dependencies acyclic and resolvable; §8 lists every REQ-.
   Fix your own drafting errors; report upstream gaps to the user.
8. **Produce the review package** (project, GT basis, ASR catalog, candidates with
   scores, selection rationale, accepted tradeoffs, risks, modules, SRS Gap List)
   and present APPROVE / RETURN [jobs] / REJECT.

### Rework

A RETURN re-runs the named jobs and every downstream job that consumed their output
(Job 1 rework ⇒ Jobs 2–8; Job 6 rework ⇒ Jobs 7–8). The package is re-issued as
`Rev N`. The GT stays locked — GT-changing defects mean REJECT, not RETURN.

## Verdicts

| Verdict | Meaning |
|---------|---------|
| `G1: PASS` | Review package issued, SRS validation PASS, human approved |
| `G1: RETURN` | Defects in named jobs; rework in progress |
| `G1: REJECT` | GT or constraints must change; restart at G0 |

## References

- `templates/GT/G1_SRS.md` — the SRS template and its structural validation rules.
- `templates/GT/G0_StRS.md`, `templates/GT/G0_SyRS.md` — the upstream contract.
- IEEE/ISO/IEC 29148:2018 §9.6 — software requirements specification.

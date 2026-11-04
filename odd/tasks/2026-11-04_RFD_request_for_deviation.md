# Plan — RFD: Request for Deviation

Feature: `odd/tasks/2026-11-04_1042_vsil_v3_skill_flow.md` · Task T4 · Specs S1, S2, S3 · Contracts C0, C1, C2, C3, C6
Target: `templates/skills/RFD_request_for_deviation/SKILL.md` (new, about 90 lines). Paper §9.

## Goal

When Build Package requirements are infeasible on the declared COTS platform, suspend the flow with a decision document for the Build Package author. Paper: "V-SIL **suspends** until the Build Package is updated and re-enters at S0."

## Inputs and outputs

| | Path | Notes |
|---|------|-------|
| Input | Raising stage's evidence | `S1_design.md` §6 today; G2 reports later |
| Input | Cited blocks in `GT/` | Read-only |
| Output | `.codeanvil/report/<cycle>/RFD_artifacts/RFD-NNN.md` | One per deviation |
| Output | `.codeanvil/report/<cycle>/RFD.md` | Iterative report: list and decisions |

## Skill sections

Frontmatter: `name: rfd-request-for-deviation`, `metadata.gate: "RFD"`. **Not in `config.yaml` `skills`**, so `_prerequisite_cell` renders `-`. That is correct for a cross-stage skill.

1. **Prerequisite.** None by design (C2 exemption). Requires a raising stage and evidence; otherwise stop.
2. **Defect test first (paper §9, verbatim).**
   - "A **defect** means V-SIL can fix it internally. The implementation or the design is wrong, but the requirements are achievable." → Do not raise. Route to S1 or S2.
   - "An **RFD** means the Build Package requirements are **infeasible on the declared COTS platform**."
   - Self-diagnosis also from the paper: a failure in an unchanged module means an undeclared dependency, which is a design defect routed to S1.
3. **Document.** The fields of paper §9.3, in order: conflicting requirements with sources; evidence with stage and VL (`ANALYSIS (no VL)` at S1, P4); trade-off options; impact of each; recommendation. Options may include design changes that need S1 rework, like option C in RFD-001.
4. **Rules.** Never invent or round a measurement. Never edit GT or the Build Package. The author decides; the agent only recommends.
5. **Report.**
   - Raised: `HITL: FEEDBACK`, Description links `RFD-NNN.md`. This blocks nothing extra, because the raising stage also wrote FEEDBACK with `Verdict: RFD`.
   - Decided: `HITL: PASS` only once every RFD in this cycle is decided, with each author's choice verbatim. Until then the iteration stays FEEDBACK and its Description lists which RFDs are open, because one report holds one verdict.
6. **Re-entry (A5).** On the decided iteration, ask the author for the new cycle's name, apply the cycle naming rules stated in this skill, set `cycle:` in `.codeanvil/project.yaml` (only that key), and add the exact line `Superseded by cycle: <name>` to the Description. Return: "Update `GT/build_package.md`, then run the S0 skill." `codeanvil status` then shows the old cycle as closed, and it stays read-only.

## RED tests first

`tests/test_create.py`:

- through `_skill_text`: names `RFD.md`, `RFD_artifacts/RFD-NNN.md`, `infeasible on the declared COTS platform`, `ANALYSIS (no VL)`, `Superseded by cycle:`;
- a scaffold's AGENTS.md table renders the RFD row with `-`, placed after the configured chain.

## Acceptance

1. The section order matches paper §9.3.
2. A defect case is routed away with no `RFD-NNN.md` written (T7, dry run).
3. `codeanvil status` lists `RFD` and, once decided, shows the old cycle as closed (T10).

## Not covered until T8/T9

G2.0, G2.1 and G2.2 as raising stages are supported by the contract, but cannot be exercised until G2 exists.

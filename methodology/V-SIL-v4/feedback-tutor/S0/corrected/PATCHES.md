# S0 — Tutor Corrected Version (Patches)

Raw output from tutor's correction tool.

---

## Artifact A: Diff-Based Patch

**Patch ID:** P-01
**Finding ID(s):** F-01
**Operation Index:** 1
**Old Snippet:** `compatibility:  "No network access, no scripts. Writes .codeanvil/GT/StRS.md, .codeanvil/GT/SyRS.md and .codeanvil/report/ <cycle-name >/S0.md. "`
**New Snippet:** `compatibility:  "No network access. Writes .codeanvil/GT/StRS.md, .codeanvil/GT/SyRS.md and .codeanvil/report/ <cycle-name >/S0.md. "`
**Superseded Patch ID:** None
**Rationale:** Removes contradictory "no scripts" constraint to permit the explicit Python execution required later in the document.

**Patch ID:** P-02
**Finding ID(s):** F-01
**Operation Index:** 2
**Old Snippet:** `runtime:  "codeanvil CLI MUST be installed and on PATH (codeanvil backup, codeanvil now, codeanvil status). "`
**New Snippet:** `runtime:  "codeanvil CLI MUST be installed and on PATH (codeanvil backup, codeanvil now, codeanvil status). Python 3 MUST be installed and on PATH. "`
**Superseded Patch ID:** None
**Rationale:** Explicitly declares the Python 3 dependency required for the SHA-256 computation script.

**Patch ID:** P-03
**Finding ID(s):** F-02
**Operation Index:** 3
**Old Snippet:** `this is the re-entry cycle and the whole flow is redone from here. Compute the SHA-256`
**New Snippet:** `this is the re-entry cycle. Before re-normalising, evaluate if the Build Package has changed. Compute the SHA-256`
**Superseded Patch ID:** None
**Rationale:** Resolves procedural contradiction by clarifying that the flow is conditionally evaluated before re-normalisation, rather than unconditionally "redone".

**Patch ID:** P-04
**Finding ID(s):** F-03
**Operation Index:** 4
**Old Snippet:** `| templates/skills/S0_normalise_build_package/templates/StRS.md ,  .../SyRS.md|This skill's locked blueprints. Never edit them|`
**New Snippet:** `| .agents/skills/S0_normalise_build_package/templates/StRS.md ,  .../SyRS.md|This skill's locked blueprints. Never edit them|`
**Superseded Patch ID:** None
**Rationale:** Corrects broken dependency path to match the standard `.agents/skills/` directory structure.

**Patch ID:** P-05
**Finding ID(s):** F-04
**Operation Index:** 5
**Old Snippet:** `Exiting draft mode. When the human says "commit the draft" or deletes the`
**New Snippet:** `Exiting draft mode. Re-evaluate the Decision Table to determine the correct action (e.g., ask before overwriting a hand-written pair). When the human says "commit the draft" or deletes the`
**Superseded Patch ID:** None
**Rationale:** Adds missing procedural step to re-evaluate overwrite protections upon exiting draft mode, preventing silent bypass of the Decision Table.

**Patch ID:** P-06
**Finding ID(s):** F-05
**Operation Index:** 6
**Old Snippet:** `Delete exactly these guidance patterns — they are not requirements:`
**New Snippet:** `Delete the following guidance patterns — they are not requirements, including any empty blueprint placeholder row or instruction sentence:`
**Superseded Patch ID:** None
**Rationale:** Restores the catch-all deletion rule for empty placeholders to ensure all scaffolding is removed, fulfilling the "Emit spec" core rule.

**Patch ID:** P-07
**Finding ID(s):** F-06
**Operation Index:** 7
**Old Snippet:** `| Build Package present, GT pair present, an  S0.md  exists in  any  cycle|Re-normalise, applying the latest G0 feedback (an RFD re-entry lands here)|`
**New Snippet:** `| Build Package present, GT pair present, an  S0.md  exists in  any  cycle|Re-normalise: execute the ## Re-entry procedure to apply the latest G0 feedback before filling the blueprints.|`
**Superseded Patch ID:** None
**Rationale:** Integrates the orphaned Re-entry logic into the Decision Table's action definition.

**Patch ID:** P-08
**Finding ID(s):** F-06
**Operation Index:** 8
**Old Snippet:**
```
Steps
Inventory every statement of the Build Package as `STK | HWC | NRM | SYS | not mapped`.
```
**New Snippet:**
```
Steps
If the Decision Table routes to Re-normalise via G0 FEEDBACK, execute the ## Re-entry procedure first. Otherwise, Inventory every statement of the Build Package as `STK | HWC | NRM | SYS | not mapped`.
```
**Superseded Patch ID:** None
**Rationale:** Integrates the Re-entry execution branch into the main linear Steps sequence to prevent it from being bypassed during re-normalisation.

---

## Artifact E: Updated Resolution Ledger

| Finding ID | Category | Severity | Contextual Importance | Affected Location | Patch ID | Resolution State | Notes |
|:---|:---|:---|:---|:---|:---|:---|:---|
| F-01 | 1. Core Purpose, Scope, and Internal Consistency | 9 | High | `compatibility` and `runtime` fields | P-01, P-02 | RESOLVED | Removed "no scripts" constraint; added Python 3 to runtime. |
| F-02 | 2. Architecture, Methodology, and System-Level Logic | 6 | High | `Prerequisite and Cycle` -> re-entry flow | P-03 | RESOLVED | Clarified conditional evaluation before re-normalisation. |
| F-03 | 3. Interfaces, Dependencies, and Cross-Section Contracts | 7 | High | `Inputs` table -> template path | P-04 | RESOLVED | Corrected path to `.agents/skills/...`. |
| F-04 | 4. Procedural and Operational Completeness | 8 | High | `Exiting draft mode` | P-05 | RESOLVED | Added Decision Table re-evaluation to prevent overwrite bypass. |
| F-05 | 4. Procedural and Operational Completeness | 7 | High | `Hard Rules` -> `Emit spec...` | P-06 | RESOLVED | Restored catch-all deletion rule for empty placeholders. |
| F-06 | 6. Evidence, Validation, Acceptance, and Decision Logic | 9 | High | `Decision Table` and `Steps` | P-07, P-08 | RESOLVED | Integrated Re-entry procedure into Decision Table action and main Steps sequence. |

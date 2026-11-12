# Refactor plan — rename "service" → "subsystem" (full) + HIL methodology fixes

**Date:** 2026-11-12
**Status:** RENAME EXECUTED (2026-11-12) on branch `refactor/service-to-subsystem` — steps 1–8
done, suites green. The **HIL methodology fixes (HIL-1, HIL-2)** below are **NOT yet executed**.
**Decided word:** `Subsystem` / `SUB-` for the software architectural unit (replaces
`service` / `SVC-`). `component` is reserved for hardware; `block` is left to GNU Radio.
**Option:** A (full) — rename the concept, the skill folders, config keys, frontmatter,
data fields, tests, AND the methodology paper. Maximum consistency.

## Why this word

Domain collisions in an SDR + HIL tool whose users work with GNU Radio:
- `service` → ITU radiocommunication service / spectrum band (the original problem).
- `component` → a hardware component (ADC/FPGA/HackRF) in RF/embedded/HIL.
- `block` → a GNU Radio flowgraph block (the delivered `.grc` has a `blocks:` section;
  the SDD template already says "e.g. GNU Radio top block").
- `package` → an IC package.

`subsystem` (ISO/IEC/IEEE 15288) collides with none, and V-SIL already has the parent
"system" level it implies. So the SW unit becomes a **subsystem**, and `component` is
freed to mean a **COTS hardware** piece — its natural reading here.

## Taxonomy (locked)

```
Prototype (HW+SW)                  = the G2 Verified Prototype (whole verified thing)
├── SW: System                     = §0.5 complete system, one runnable entry point
│        └── Subsystem  (SUB-nnn)  = top-level SW architectural unit  (was service / SVC-)
│              └── Module          = internal code unit  (SUB-nnn/module_id)
└── HW: COTS
         └── Component             = a COTS hardware piece (HackRF, RPi, ADC…),
                                     described by the StRS `HWC-` blocks (UNCHANGED)
```

## Decisions (locked by the author 2026-11-12)

1. **GT formats:** change the **minimum necessary** — in practice **nothing**: the GT
   templates (`StRS.md`, `SyRS.md`) have zero "service"/`SVC-`. Leave them as-is.
2. **Full rename across `templates/` AND `methodology/V-SIL-v3/`** (the methodology
   paper, markdown): `V-SIL_v3.md` (~46), `V-SIL_v3-spa.md` (Spanish, ~3),
   `S1_G1_template.md` (~19), `V-SIL_v3-diagrams.html` (~59). ~127 hits total.
3. **Skill folder names:** `S1_design_services` → **`S1_design_system`** (S1 delivers
   the whole design = the system); `S2_implement_services` → **`S2_implement_subsystems`**
   (S2 builds the units). Frontmatter: `s1-design-system`, `s2-implement-subsystems`.
4. **`service_id` → `subsystem_id`:** included (part of the full rename).
5. **HW branch intact:** keep `HWC-` as the only hardware id; NO new `component`
   id/prefix. "component" is the conceptual reading of the COTS hardware, nothing more.
6. **Legacy note for agents:** do NOT migrate archived/existing projects
   (`methodology/test/T0_*`, `T1_*`, the live `hackrf_fm_peaks_v*`). Instead add a short
   **legacy-terminology note** an agent will read (in `templates/AGENTS/TEMPLATE_AGENT.md`,
   and/or a NOTES line), stating: in pre-rename artifacts, `service`/`SVC-` is the legacy
   name of `subsystem`/`SUB-`; treat them as equivalent, do not "fix" old snapshots.
7. **Execution vehicle:** done **by hand** (no subagents) given the folder/config/path
   interdependence — "por si acaso".

## Scope boundaries

**NOT touched:** GT templates (zero hits); G0 validator/rules (`STK-/HWC-/SYS-/NRM-`
only); pipeline STAGE ids `S0 S1 S2 G0 G1 G2`; the `module` sub-unit; the HW branch
(`HWC-`, "component"); any incidental/correct use of "service" (systemd/web),
"component" (hardware), "block" (GNU Radio), "package" (IC) — context-aware replacement
only, never a blind sed; archived/live existing projects (legacy, per decision 6).

**Touched:** SW design/impl methodology in `templates/`, the `SVC-` convention, the two
skill folders, `config.yaml`, frontmatter, the `src/` references, the `V-SIL-v3/` paper,
and tests.

## Naming map

| Old | New |
|-----|-----|
| service (SW unit) | subsystem |
| services | subsystems |
| `SVC-` (`SVC-001`) | `SUB-` (`SUB-001`) |
| `src/<service>/` | `src/<subsystem>/` |
| "a system of layered services" | "a system of layered subsystems" |
| "service contract" | "subsystem contract" |
| `service_id` | `subsystem_id` |
| folder `S1_design_services/` | `S1_design_system/` |
| folder `S2_implement_services/` | `S2_implement_subsystems/` |
| `name: s1-design-services` | `name: s1-design-system` |
| `name: s2-implement-services` | `name: s2-implement-subsystems` |

## SDD definitions (to add)

> **Subsystem** (`SUB-nnn`): a top-level unit of the software architecture; has a
> contract from the design stage, implemented under `src/SUB-nnn/`, containing one or
> more **modules**. **System**: the complete software, one runnable entry point (§0.5),
> i.e. the set of subsystems. **Component**: a COTS hardware piece (HackRF, RPi…),
> described by the `HWC-` blocks; never software. **Prototype**: the G2-verified
> realization of the system on its COTS hardware (HW+SW).

## Work breakdown (by risk — structural first, text last; executed by hand)

1. **Folder renames (git mv):** `S1_design_services` → `S1_design_system`;
   `S2_implement_services` → `S2_implement_subsystems`. Scaffold copies the whole dir
   from disk, so new projects follow — fix every hardcoded path string (steps 2–3).
2. **`templates/config.yaml`:** `skills:` keys + `project_dir` (~18–19, 24–25);
   `shared_skill_assets:` `S2_implement_services` key (~154). `path_replacements` needs
   no change; no `s1_skill`/`s2_skill` constants exist.
3. **`src/codeanvil/`:** `UI/workspace.py:245` vis-network path; grep for any other old
   folder literal and design-concept "service" in CLI/help (exclude incidental).
4. **Frontmatter `name:`** of the two skills.
5. **Concept-text sweep** (service→subsystem, SVC-→SUB-, service_id→subsystem_id),
   context-aware: `S1_design_system/` (SKILL, SDD ~58, dependency_graph_template.html),
   `S2_implement_subsystems/` (SKILL, project_layout, machine_evidence incl. scaffolded
   `.agents/skills/S2_...` paths), `G1_design_review/`, `G2_adaptive_verification/`,
   `templates/AGENTS/TEMPLATE_AGENT.md` (+ the legacy note, decision 6). Add the SDD
   definitions above; name the "System" level explicitly where it helps.
6. **Data field** `service_id` → `subsystem_id`: `SDD.md`, `machine_evidence.md`,
   `measurement.schema.json`, `validate_measurement.py` (+ its S2 copy via shared assets).
7. **Methodology paper** `methodology/V-SIL-v3/`: `V-SIL_v3.md`, `V-SIL_v3-spa.md`
   (Spanish — translate the term consistently), `S1_G1_template.md`,
   `V-SIL_v3-diagrams.html` (watch the SVG label widths).
8. **Tests:** the ~8 files asserting folder names / `name:` slugs / "service" / `SVC-`
   (`test_vsil_v3_s1/s2/g1/g2`, `test_create`, shared-asset/scaffold path asserts).

## Verification
- `uv run pytest` (full) + the vsil_hil_mcp suite — green.
- `grep -rniE '\\bservices?\\b|SVC-' templates/skills src/codeanvil methodology/V-SIL-v3`
  returns only reviewed incidental hits.
- Scaffold a fresh project: `.agents/skills/` has `S1_design_system` /
  `S2_implement_subsystems`, AGENTS.md renders, S1→G2 dry read coherent.
- Migration of ids is a validated map (`SVC-nnn` ↔ `SUB-nnn`, one-to-one), not raw sed.

---

# Add-on: HIL methodology fixes (fold into the S2/G2 skills while renaming them)

Independent of the rename, but discovered in HIL testing and to be applied in the same
pass on `S2_implement_subsystems` and `G2_adaptive_verification`.

## HIL-1 — G2 → S2 feedback carried in the report's Description (no intermediate software)
Today a G2 FEEDBACK sends S2 back to rework, and S2 may re-interrogate the human
(AskUser) to decide what to change. Change it so the handoff rides the **existing gate
report** — no new channel, data structure or communication software between gates:
- On FEEDBACK (`Verdict: module defect`), G2 writes the **concrete changes to make**
  directly into its iteration report's **`### Description`** section (right after the
  `Based on: S2 iteration <N>` line) — a plain, explicit list of what S2 must edit.
  The report is already the gate-to-stage medium (report-driven gates), so this adds
  no plumbing.
- S2's rework route **reads that G2 Description and edits ONLY what is listed**, with
  **no AskUser prompt**. State this in both skills: G2 says "write the change list in
  the Description"; S2 says "on a G2 module-defect FEEDBACK, apply exactly the listed
  changes from the G2 report Description; do not ask the human or redesign."
- Goal: faster, bounded correction loop. Keep it consistent with the existing bounded-
  rework / impact-map wording.

## HIL-2 — G2 must say explicitly what to do on a HARDWARE/environment problem
In the test, the `codeanvil-agent` user lacked permission to use the HackRF (USB /
group / udev), and the agent wrongly suggested S2 feedback instead of fixing the target.
Add a G2 section that **distinguishes operational HW/environment problems from software
defects**:
- Permission/driver/group/udev/device-visibility problems on the target are
  **operational** → recommend the fix on the DUT (e.g. add `codeanvil-agent` to the
  device group / udev rule / plugdev; verify with `probe_target` / `lsusb`), re-run.
  They are NOT a module or design defect and must NOT route to S2/S1 feedback.
- Only a genuine behavioral failure of the delivered code is a `module`/`design` defect.
- Make this a first-class branch in the G2 verdict logic (operational-fix vs
  module-defect vs design-defect vs RFD), with the HW-permission case as the worked
  example.
- **If the runtime/tool blocks the remediation command** (e.g. the permission classifier
  refuses `ssh_exec_cmd_trusted`, or the sandbox blocks the fix), G2 **hands the user the
  exact commands to run by hand on the target** as a LAST resort, rather than giving up
  or mislabeling it an S2 defect. State the concrete commands (e.g. the group/udev fix)
  so the human can apply them directly, then re-run G2.

## Pending additions (OPEN — author to extend)
> Keep open; add items below; do not execute until marked APPROVED.

- …

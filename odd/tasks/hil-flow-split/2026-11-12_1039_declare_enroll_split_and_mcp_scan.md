# Plan — HW enrollment at pre-G2, and GT/design-driven MCP provisioning at pre-S2

Objective: fix a verified flow loose end so that **hardware credentials/IP/MAC only appear
when G2 needs them** (and only if the design requires VL-2), and make **MCP provisioning
driven by the design** instead of coupling the general methodology to any domain MCP.

Status: **PLAN — all decisions final (2026-11-12). Ready to implement; not started.**
Await go-ahead + branch name.

Related:
- Builds on the HIL harness in [`../hil-mcp/2026-11-11_2042_hil_relaxed_refactor.md`](../hil-mcp/2026-11-11_2042_hil_relaxed_refactor.md) (v0.8.0).
- Loose end found building the `hackrf_fm_peaks` HIL test project (the manual `rpi_lab`
  placeholder was the workaround that exposed it).

---

## Specs

User requests quoted verbatim (Spanish). Interpretations are marked **Assumption**.

- **S1** — *"Cuando llegue a G2, le pregunta al usuario configure el hardware, antes no
  debería. (Solo si el GT pide vl2, sino ni lo pregunta)."*
- **S2** — *"La descripción del hw usado debe de ir incluso en la entrada de la metodología,
  pero las credenciales, la ip, la MAC, solo cuando se vaya a empezar G2."*
- **S3 (Q1 decision)** — *"El comando credential-setup edita y hace un append a project.yaml
  para que el agente no lo edite a mano. No es necesario flag --target. Se diferencian los
  dispositivos por macs de interfaces de red + ip actual (más débil). El que de verdad sirve
  es las macs. Todo esto como un pre-G2 dentro de la skill de G2 se pide al humano hacer el
  comando (bloqueante si el usuario no lo hace para GT con vl2), antes de G2 no es necesario.
  Si se necesita varios dispositivos, el identificador debe de ser las macs de interfaz
  (fuera de alcance esta versión)."*
- **S4 (Q2 decision)** — *"pre-G2 va dentro de la skill G2. Todo va contenido en su misma
  skill. Se hace un análisis pre-S2 de los mcp, se hace una vez, y se reinicia a mano por el
  usuario. esto no genera error por el comportamiento de codeanvil status. ojo marconi no se
  usa en S1, se usa en S2 para implementar los flujos de RF, se entrega su .grc y su .py y
  luego se adecua al código general (gnu radio se usa para generar el código de DSP/RF con
  pocos tokens)."*

Decision taken earlier: **do not default `marconi`** (domain-specific; defaulting couples
the general methodology to RF). Provisioning is design-driven and authorized per add.

---

## Decisions locked

**Q1 — enrollment writer and timing.**
- `credential-setup` stays the **sole writer** of `targets:` in `project.yaml` (appends), so
  the agent never hand-edits it. **No new `codeanvil target add`. No `--target` flag.**
- It runs as a **pre-G2 step inside the G2 skill**: when the design requires VL-2, the G2
  skill asks the human to run `credential-setup`. This is **blocking** — G2 cannot run the
  real-HW stage until it is done. **Before G2 nothing hardware-related is written.**
- Devices are identified by **network-interface MACs** (current IP is a weaker secondary
  signal). **Multiple devices / MAC-keyed selection is OUT OF SCOPE this version** — exactly
  one target is expected.

**Q2 — MCP provisioning.**
- A **pre-S2 MCP analysis**, contained in the **S2 skill** (preamble), runs **once**: it
  reads the approved design (SDD) and provisions the MCP(s) it needs, each via
  `codeanvil mcp add <name>` with user authorization. The **user restarts the agent
  manually** to load the tools. Re-running S2 after restart finds the MCP present and
  proceeds. `codeanvil status` is report-driven/stateless, so the restart causes no error.
- **`marconi` is used in S2** (not S1): GNU Radio generates the RF/DSP flow cheaply — deliver
  `.grc` + `.py`, then adapt it into the general `src/` code.
- `vsil_hil_mcp` is provisioned in the same pre-S2 analysis (methodology-owned; needed at G2).
- The MCP engine and `config.yaml mcp_servers` registry stay; **no static default list**.

---

## What this simplifies (gotchas from the earlier draft are now moot)

Because there is **no design-time target declaration** (the target only exists after
enrollment at G2):
- **No `--target` matching problem.** `credential-setup` appends the single target; a bare
  `resolve_target("")` returns the only one.
- **No host-optional config change.** `project.yaml` simply has **no `targets:`** until G2;
  `resolve_target` already raises *"no remote target declared … run codeanvil
  credential-setup"*, which is exactly the pre-G2 blocking message.

---

## Design

Four concerns, now cleanly separated by owner and time:

| Concern | Owner | When |
|--------|-------|------|
| HW **description** (device, limits) | GT `StRS.md` `HWC-*` | methodology entry (already correct) |
| **MCP provisioning** (marconi/hil tools) | S2 skill preamble (once, manual restart) | pre-S2 |
| **Code** incl. Real HW HAL + fake device API | S2 | S2 (no hardware needed; fake API at VL-0) |
| **Enrollment** (IP/MAC/credentials) | `credential-setup` (append) | pre-G2 inside the G2 skill, if VL-2 |

### Change A — enrollment at pre-G2 (inside the G2 skill)

- The G2 skill gains a **pre-G2 hardware step**: if the SDD declares VL-2 (real device) and
  no target is enrolled, it tells the human to run `codeanvil credential-setup …` and
  **blocks** the real-HW stage until done. For mock-only / local designs it never asks.
- `credential-setup` appends the enrolled target (host, `mac_addresses`, `device_id`,
  `bootstrap_user`, workspace) to `project.yaml`. MAC is the identity; IP is secondary.
- S1 no longer needs a `project.yaml targets:` entry. `SDD.md` Meta `Target(s)` names the
  **intended device/target as design intent**, which the agent **deduces from the `HWC-*`
  blocks** (or `local`); the concrete `project.yaml` entry is created at G2.
- **Verification ladder:** VL-0/VL-1 run **locally, no hardware** (Mock HAL + fake device
  API); **VL-2 is real SIL/HIL on the actual hardware at G2**. Remote PIL at S2 is dropped on
  purpose — you can write and validate code up to VL-1 without any hardware.
- **Single target, replace not stack:** this version supports exactly one target. Re-enrolling
  the same device updates it in place; enrolling a *different* device is **rejected** with a
  "multi-device out of scope" message — `credential-setup` never silently appends a second.

### Change B — pre-S2 MCP analysis (inside the S2 skill)

- At S2 start, read the approved SDD and decide:
  - **RF / DSP / SDR** design (measurands, methods, GNU Radio flow) → `marconi`, used to
    generate `.grc` + `.py` and adapt into `src/`.
  - **VL-2 + embedded-Linux `HWC-*`** → `vsil_hil_mcp` (used at G2).
- For each needed, missing MCP: propose `codeanvil mcp add <name>`, get authorization, add it,
  then ask the user to **restart the agent** and re-run S2. Idempotent: present MCPs are
  skipped (projects created with `--mcp` already have them).
- **Missing system dependency ⇒ help install, don't degrade.** If an MCP needs a system
  package (gnuradio for marconi) that is absent, the agent researches how to install it and
  gives the user the exact commands; it does **not** silently fall back. Writing the RF/DSP
  code by hand without GNU Radio is only *suggested*, and only done if the user asks.

**Strength of pre-S2 vs the earlier pre-S1 idea:** by S2 the **SDD already exists**, so the
analysis reads a concrete design (HAL mode, VL-2, device themes) instead of guessing from the
raw GT.

---

## Touch points

- `templates/skills/G2_adaptive_verification/SKILL.md` — add the pre-G2 hardware step
  (VL-2-gated, blocking, `credential-setup` instruction); silence for mock-only/local.
- `templates/skills/S2_implement_services/SKILL.md` — add the pre-S2 MCP analysis preamble
  (read SDD → propose `codeanvil mcp add` → manual restart → re-entrant); document marconi's
  `.grc`/`.py` → `src/` adaptation.
- `templates/skills/S1_design_services/SKILL.md` + `references/SDD.md` — relax `Target(s)` to
  design intent (device/`local`), not a `project.yaml` entry; the entry is created at G2.
- `templates/skills/G1_design_review/references/G1_CHECKLIST.md` — G1.8 reviews the target
  **intent**, not an enrolled `project.yaml` row.
- `src/codeanvil/CLI/commands/credential_setup.py` — confirm append semantics are clean for a
  from-empty `targets:` (no pre-declared row); no `--target`.
- `templates/AGENTS/TEMPLATE_AGENT.md` — document: HW description at entry, MCP analysis at
  S2, enrollment at G2; the manual-restart step.

---

## Resolved decisions (final, 2026-11-12)

- **R1/R5/R6 — `Target(s)` relaxed, deduced from HWC.** S1's `Target(s)` is design intent
  (not a `project.yaml` entry); the agent deduces it from the `HWC-*` blocks when a
  remote/VL-2 target is needed, and defines it. The pre-G2 block condition is precise: SDD
  `mock+real` **AND** a VL-2 claim **AND** no enrolled target ⇒ block and ask the human to run
  `credential-setup`; anything else ⇒ never ask. The S2 MCP preamble runs before any code work
  and is idempotent (post-restart re-run continues cleanly).
- **R2 — Remote PIL at S2 dropped on purpose.** VL-0/VL-1 local (no hardware); VL-2 = real
  SIL/HIL at G2. See the verification ladder in Change A.
- **R3 — One target, replace not stack.** Guard added; a second distinct device is rejected
  (multi-device out of scope).
- **R4 — Help install the system dependency, don't degrade.** See Change B.

## Non-goals

- No implementation in this plan; no change to the enrollment security model (SSH keys,
  `codeanvil-agent`, policies).
- Multi-device MAC-keyed selection, remote PIL at S2, Windows targets, and hot-loading MCP
  tools mid-session stay out of scope.

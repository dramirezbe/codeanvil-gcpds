# Handoff — V-SIL v3 full flow (2026-11-05)

Where we stopped, and how to pick up on another machine. The full history (specs, tasks,
verbatim requests L1–L16) is in `odd/tasks/2026-11-05_1421_vsil_v3_full_flow.md`.

Branch: `feat/vsil-v3-full-flow` (pushed, not merged to `main`). Suite: 320 passed.
Version in `pyproject.toml`: still `0.3.0`.

## Done

| What | Commits |
|------|---------|
| S2 and G2 wired into the chain (T5) | `c0e915e` |
| S0 casts lab inputs into SyRS §4–§6, or the "Not applicable" line (T2) | `b2549c0` |
| S1 declares `HAL mode`, `Toolchain`, verification kit §1.3.4, HAL ladder §1.6, telemetry §1.7 (T3) | `84f06f7` |
| G1 checks HAL mode, telemetry, kit, toolchain (T4) | `728b8cd` |
| `vsil-verifier` subagent shipped for Claude Code, OpenCode, Codex; `templates/agents/` in the wheel (T9) | `75e871c` |
| G2 adaptive verification + Verified Prototype template (T7) | `7ee8c78` |
| Paper EN/ES, template, diagrams: Real HW HAL and lab optional, telemetry mandatory (T1) | `34f89f6` |
| S2 skill: project layout (Python uv / TS pnpm), self-contained loggers (T6) | `fdbc68a` |
| Generated `AGENTS.md` follows S0 → G2, names only the `codeanvil` CLI (T10) | `d0015b4` |
| Gates G0, G1, G2 ask PASS / FEEDBACK (/ RFD) with `AskUserQuestion`, chat fallback | `36da67e` |
| Manual review fixes: kit imports `verification.<package>…` (pythonpath collision), G2 fresh-session path, tsconfig types | `8ac41b9` |
| G1 runs no script; re-derives every row; G1.14 checks the toolchain with `--version` and installs only after a yes | `19ce74a`, `7221e0e` |
| T3 fixture v2: spectrum + waterfall + detection, DSP + UI, author-owned oracle (B.2 Mock HAL model, B.3 scenes SC-1–SC-6, B.4 golden vectors GV-1–GV-5) | `87dfd96` |

## Pending

1. **T8 end-to-end run** (needs a human at the gates). Procedure: `methodology/test/README.md`
   §5b. A first Claude run was started on the old fixture and must restart with the v2 fixture.
   Record each step's result and the runtime used in the feature document's Log.
2. **Live check** that `/agents` (Claude Code) and OpenCode list `vsil-verifier`.
3. **Merge** `feat/vsil-v3-full-flow` into `main` after T8 (PR is the user's call).
4. **T11 release** after the merge: bump `0.3.0` → `0.4.0`, `uv lock`, tag `v0.4.0`; push the
   tag only after the user confirms. Plan: `odd/tasks/2026-11-05_RELEASE_v0_4_0.md`.

## Findings to remember

- Codex ignores `sandbox_mode` in `.codex/agents/*.toml` since openai/codex PR #39299; the
  verifier is read-only there only by its instructions. Real enforcement needs
  `codex exec --sandbox read-only`. Optional hardening: a `git status` before/after check in G2.
- T3 oracle: a median noise floor fails when more than half the slice is on air; the fixture
  uses the 10th percentile (checked with a numpy simulation, ≥ 4 dB clearance per label).
- "Labelling" for ML training is future work (FW-ML); labelled scenes as a test oracle are not ML.
- Paper §6 G1 list still has no explicit kit row; the G1 skill checks it.
- The AGENTS template is filled with `str.replace`, not Jinja (CLAUDE.md still says "Jinja").

## Resume on another machine

```bash
cd ~/GIT/UNAL                       # git identity dramirezbe applies only under ~/GIT/UNAL/
git clone git@github.com-unal:dramirezbe/codeanvil-gcpds.git   # or git pull if already cloned
cd codeanvil-gcpds && git checkout feat/vsil-v3-full-flow
uv run --extra dev pytest -q        # expect 320 passed
uv tool install --force-reinstall --python 3.12 .   # codeanvil from this branch
codeanvil init
npm i -g typescript                 # tsc, only to type-check the TS logger
```

Then run the T8 sandbox test, with the project inside `~/GIT/UNAL/` so commits get an identity:

```bash
mkdir -p ~/GIT/UNAL/sandbox-vsil && cd ~/GIT/UNAL/sandbox-vsil
codeanvil create --name "FM Occupancy Mock" && cd fm_occupancy_mock
cp ~/GIT/UNAL/codeanvil-gcpds/methodology/test/T3_FM-mock/build_package.md GT/build_package.md
git init -q && git add -A && git commit -qm "scaffold"
codeanvil sandbox claude            # then: start → Run S0, then G0 → S1 → G1 → S2 → G2
```

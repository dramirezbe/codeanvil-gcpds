# Plan — T1: paper, template and diagrams follow the HAL mode

Feature: `odd/tasks/2026-11-05_1421_vsil_v3_full_flow.md` · Task T1 · Specs S1, S2, S3, S7, S10 · Contracts C0, D1–D5
Targets: `methodology/V-SIL-v3/V-SIL_v3.md`, `V-SIL_v3-spa.md`, `S1_G1_template.md`, `V-SIL_v3-diagrams.html`.

## Goal

C0 makes the paper the source of every skill, so it changes first. Today the paper says S1 designs **both** HALs and G1 checks both. After S1: the Real HW HAL and the lab inputs are optional, the Mock HAL and the telemetry companion are mandatory.

## Changes

| Where | Change |
|-------|--------|
| Paper §5.5 | S1 declares `HAL mode: mock-only` or `mock+real` (D1). The Mock HAL is always designed. The Real HW HAL and its lab procedures, calibration and tolerances appear only in `mock+real`. |
| Paper §5.5 | The telemetry companion is mandatory, verification infrastructure only, never shipped (S2, D3). |
| Paper §5.5 | The verification kit (D2 list) is built in the initial layer of S2, before any module (S3). |
| Paper §6, check 7 | "Mock HAL exposes the base-layer interface; golden vectors carry digest, parameters and expected outputs. In `mock+real`, the Real HW HAL exposes the same interface and references the Build Package lab inputs." |
| Paper §7 | Step 1 becomes "Initial layer: base + verification kit". The data-sources table notes that VL-2 needs `mock+real`. |
| Paper §8.2 | Add D5: `mock-only` caps claims at VL-1. Keep S7: in `mock+real` the Real HW HAL may be declared at VL-0 for a cycle. |
| Paper §5.4 | Done before T1 (L5 of the feature document): status "uncertain", S2 and G2 ML paragraphs marked future work, FW-005 origin updated. No further change. |
| Paper §10 | The Verified Prototype lists the delivered tree (`app/`) apart from the kit (`verification/`) (A3). |
| Template §1.6 | Add the `HAL mode` row; mark the Real HW HAL table "only in `mock+real`". |
| Template G1.11 | Real HW HAL rows only in `mock+real`. |
| Diagrams §5.5 | The VL-2 button notes "only in `mock+real`"; the caption states that the telemetry companion is mandatory and not shipped. |

Spanish file: same changes, same section numbers.

## Checks

- No test reads the paper. Structural readback: headings and numbering unchanged, `grep -c 'mock-only'` > 0 in both papers and the template, and the diagrams page opens with no JS error in headless Chromium.
- Passive documentation: no RED test applies.

## Acceptance

1. A reader of §5.5 alone knows which HAL pieces are mandatory and which are optional.
2. Nothing in the paper still says S1 always designs the Real HW HAL.
3. EN and ES say the same thing in the same sections.

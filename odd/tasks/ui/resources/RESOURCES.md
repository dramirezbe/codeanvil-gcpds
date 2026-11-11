# UI launcher icons — brand assets

Real brand icons for the agent/editor launcher buttons (feature `feat/ui`,
spec S8). Used **nominatively** to identify each tool in its launch button —
standard launcher practice. All marks are trademarks of their respective
owners; CodeAnvil claims no affiliation or endorsement. Kept as the real
downloaded assets — not redrawn.

## Source & license

The set is now the **colored official marks**, downloaded by the author, except
one monochrome fallback:

- `claude.svg`, `openai-codex.svg`, `vscode.svg`, `jetbrains.svg`, `pi.svg` —
  colored official marks (author-provided; `pi.svg` from pi.dev). Each is its
  owner's trademark.
- `opencode-light.svg` / `opencode-dark.svg` — OpenCode's official **monochrome**
  mark, which has no single colored form, so it ships as **two theme variants**:
  `-light` (dark ink `#1F1F1F`, for light backgrounds) and `-dark` (light ink
  `#EEEEEE`, for dark backgrounds). The only icon with explicit light/dark files.
- `anthropic.svg` — the only **Simple Icons** mark left (monochrome, single
  path, **CC0 1.0**), kept as a mono alternate for Claude.

The colored marks carry fixed `fill` brand colors (and gradients), so they do
**not** take `currentColor`. OpenCode is handled by picking the variant per
theme; `anthropic.svg` tints freely via `currentColor`.

## Inventory

| File                | Brand / tool        | Launcher group (S8)      | Color | viewBox    |
|---------------------|---------------------|--------------------------|-------|------------|
| `claude.svg`        | Claude              | both (desktop + CLI)     | color | 0 0 24 24  |
| `anthropic.svg`     | Anthropic (alt)     | mono alternate           | mono  | 0 0 24 24  |
| `openai-codex.svg`  | OpenAI / Codex      | both (desktop + CLI)     | color | 0 0 250 250|
| `opencode-light.svg`| OpenCode (light bg) | both (desktop + CLI)     | mono  | 0 0 240 300|
| `opencode-dark.svg` | OpenCode (dark bg)  | both (desktop + CLI)     | mono  | 0 0 240 300|
| `vscode.svg`        | Visual Studio Code  | no-terminal (editor)     | color | 0 0 100 100|
| `jetbrains.svg`     | JetBrains           | no-terminal (editor)     | color | 0 0 512 512|
| `pi.svg`            | Pi                  | terminal (CLI)           | color | 0 0 470 470|

## Normalized set — `normalized/`

Produced by `scratchpad/normalize_icons.py` (lossless, vector-only: each source
drawing is wrapped in a single `<g transform="translate scale">`, so no raster
and no resolution loss — SVGs scale infinitely). Originals at the folder root
are kept untouched as provenance.

Each normalized file is a common **`viewBox="0 0 24 24"`**, `width/height=24`,
`role="img"` + `<title>`, with the mark fitted and centered into the 24 box with
`PAD = 1.5` units of optical padding. OpenCode's `viewBox` (240×300, non-square)
is honored and the mark centered; both `opencode-light` and `opencode-dark` are
normalized.

- `normalized/<brand>.svg` — the usable, consistent icon.
- `normalized/<brand>-off.svg` — the **faded/disabled** variant (same mark,
  `opacity="0.25"` on the wrapper group — a stronger, clearly-distinct fade).

Equivalent to a CSS `opacity:.4` at runtime, so the `-off` files are optional
convenience; prefer CSS fade when the icon is inlined.

### Caveats for wiring (T6/T8)

- `vscode.svg`/`jetbrains.svg` use `<mask>`/gradient `id`s (e.g. `mask0`). As
  separate files they are fine; if several are **inlined into one DOM**,
  namespace or suffix those ids per icon to avoid collisions.
- `PAD` (1.5) is a tweakable optical choice; bump per-icon only if one looks
  visually larger/smaller than the rest at button size.
- Re-run: `python3 -I normalize_icons.py <resources-dir>` after adding an icon.

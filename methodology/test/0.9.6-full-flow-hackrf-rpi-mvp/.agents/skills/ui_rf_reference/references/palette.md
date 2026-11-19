# RF Palette — Color Tokens

Dark-first palette grounded in the visual language of spectrum analysers and SDR consoles.
Every token is a CSS custom property defined on `:root`.

## Token definitions

```css
:root {
  /* Surface */
  --rf-bg:            #0a1620;   /* deep navy — instrument background */
  --rf-bg-panel:      #0e1e2c;   /* slightly lighter panel surface */
  --rf-bg-elevated:   #142838;   /* popover, tooltip, elevated card */
  --rf-border:        #1e3a52;   /* panel dividers, grid lines */
  --rf-border-subtle: #152a3c;   /* secondary grid, faint separators */

  /* Text */
  --rf-fg:            #d4dfe8;   /* primary text */
  --rf-fg-muted:      #7e97aa;   /* secondary labels, axis ticks */
  --rf-fg-dim:        #4a6478;   /* disabled, placeholder */

  /* Signal — the spectrum trace and active data */
  --rf-signal:        #72d8ff;   /* primary trace, cyan phosphor */
  --rf-signal-glow:   rgba(114, 216, 255, 0.15);  /* CRT glow behind trace */

  /* State — semantic, not decorative */
  --rf-occupied:      #174735;   /* occupied channel background */
  --rf-occupied-fg:   #8bf0ac;   /* occupied channel text/marker */
  --rf-clear:         #bbcbd8;   /* clear channel marker */
  --rf-threshold:     #f0c040;   /* near-threshold warning */
  --rf-error:         #e05454;   /* error, disconnected */
  --rf-connected:     #4ade80;   /* connection OK */

  /* Waterfall colourmap endpoints (interpolate between) */
  --rf-wf-cold:       #142838;   /* noise floor colour */
  --rf-wf-warm:       #72d8ff;   /* mid-intensity */
  --rf-wf-hot:        #ffffff;   /* peak intensity */

  /* Accent — used sparingly for interactive elements */
  --rf-accent:        #3b8eea;   /* buttons, links, focus rings */
  --rf-accent-hover:  #5aa3f0;
}
```

## Light theme variant

The light variant inverts the contrast model: dark traces on a light field, like a
printed spectrum plot. It is NOT a simple inversion of the dark tokens.

```css
@media (prefers-color-scheme: light) {
  :root:not([data-theme="dark"]) {
    --rf-bg:            #f4f6f8;
    --rf-bg-panel:      #ffffff;
    --rf-bg-elevated:   #ffffff;
    --rf-border:        #d0d8e0;
    --rf-border-subtle: #e4e9ee;

    --rf-fg:            #1a2a3a;
    --rf-fg-muted:      #5a6a7a;
    --rf-fg-dim:        #98a8b4;

    --rf-signal:        #0066aa;   /* dark blue trace on light */
    --rf-signal-glow:   rgba(0, 102, 170, 0.08);

    --rf-occupied:      #d6f5e0;
    --rf-occupied-fg:   #0d6832;
    --rf-clear:         #5a6a7a;
    --rf-threshold:     #b8860b;
    --rf-error:         #c03030;
    --rf-connected:     #22804a;

    --rf-wf-cold:       #e8ecf0;
    --rf-wf-warm:       #0066aa;
    --rf-wf-hot:        #001833;

    --rf-accent:        #2070c0;
    --rf-accent-hover:  #1860a8;

    color-scheme: light;
  }
}
:root[data-theme="light"] {
  /* same light values as above */
  --rf-bg:            #f4f6f8;
  --rf-bg-panel:      #ffffff;
  --rf-bg-elevated:   #ffffff;
  --rf-border:        #d0d8e0;
  --rf-border-subtle: #e4e9ee;
  --rf-fg:            #1a2a3a;
  --rf-fg-muted:      #5a6a7a;
  --rf-fg-dim:        #98a8b4;
  --rf-signal:        #0066aa;
  --rf-signal-glow:   rgba(0, 102, 170, 0.08);
  --rf-occupied:      #d6f5e0;
  --rf-occupied-fg:   #0d6832;
  --rf-clear:         #5a6a7a;
  --rf-threshold:     #b8860b;
  --rf-error:         #c03030;
  --rf-connected:     #22804a;
  --rf-wf-cold:       #e8ecf0;
  --rf-wf-warm:       #0066aa;
  --rf-wf-hot:        #001833;
  --rf-accent:        #2070c0;
  --rf-accent-hover:  #1860a8;
  color-scheme: light;
}
```

## Usage rules

- Never use literal hex in component CSS — always go through the token
- `--rf-signal` is for the data trace and active measurements ONLY, not for headings or accents
- Semantic colours (`--rf-occupied`, `--rf-error`, etc.) are separate from `--rf-accent`
- The waterfall colourmap is a continuous gradient, not three steps — interpolate in the shader or canvas code
- The glow token is for a 1–2px box-shadow or filter behind the trace, not a background

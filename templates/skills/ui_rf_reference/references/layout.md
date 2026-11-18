# RF Dashboard Layouts

Responsive panel layouts for signal-processing browser UIs. The views are instruments
in a rack — they share edges, align on the frequency axis, and use the full width.

## Principles

- **Spectrum and waterfall share a frequency axis** — they MUST be the same width and
  vertically stacked so bin N in the spectrum is directly above bin N in the waterfall
- **Data first**: no hero, no spacer — the first visible thing is the spectrum trace
- **Full bleed on canvas**: the spectrum and waterfall backgrounds extend to the panel
  edges; padding goes around labels, not around the canvas
- **Status bar is minimal**: connection indicator + centre frequency + sample rate,
  one line, top of page

## Layout A: Single-column stack (1–3 views)

The default. Works at every width. Best when views update together at the same rate.

```
┌──────────────────────────────────────────┐
│ ● Connected   98.0 MHz   2.4 MS/s       │  status bar
├──────────────────────────────────────────┤
│                                          │
│  ~~~~~~~~~~~~spectrum trace~~~~~~~~~~~~  │  spectrum (220px)
│                                          │
├──────────────────────────────────────────┤
│ ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓ │
│ ▓▓▓▓▓▓▓▓▓▓ waterfall ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓ │  waterfall (120px)
│ ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓ │
├──────────────────────────────────────────┤
│  97.1  97.3  97.5  97.7  97.9  ...      │
│  Clear  OCC  Clear Clear  OCC  ...       │  channel table
│  ...                                     │
└──────────────────────────────────────────┘
```

```css
.rf-dashboard {
  display: flex;
  flex-direction: column;
  gap: 0;                        /* panels share edges */
  min-height: 0;
  background: var(--rf-bg);
  color: var(--rf-fg);
}
.rf-status {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.5rem 1rem;
  font-size: 0.8125rem;
  font-family: var(--rf-font-mono);
  color: var(--rf-fg-muted);
  border-bottom: 1px solid var(--rf-border);
}
.rf-panel {
  position: relative;
  border-bottom: 1px solid var(--rf-border);
}
.rf-panel canvas {
  display: block;
  width: 100%;
  height: auto;
  background: var(--rf-bg-panel);
}
.rf-panel figcaption {
  position: absolute;
  top: 0.375rem;
  left: 0.75rem;
  font-size: 0.6875rem;
  color: var(--rf-fg-dim);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  pointer-events: none;
}
```

## Layout B: Side panel (spectrum + waterfall left, table right)

For wider screens (≥768px). The table sits beside the views instead of below, keeping
all information visible without scrolling.

```
┌──────────────────────────────┬───────────┐
│ ● Connected   98.0 MHz      │  Channels │
├──────────────────────────────┤           │
│  ~~~~~~~~spectrum~~~~~~~~    │  97.1 Clr │
│                              │  97.3 OCC │
├──────────────────────────────┤  97.5 Clr │
│ ▓▓▓▓▓▓▓▓ waterfall ▓▓▓▓▓▓▓ │  97.7 Clr │
│ ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓ │  97.9 OCC │
│ ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓ │  ...      │
└──────────────────────────────┴───────────┘
```

```css
@media (min-width: 768px) {
  .rf-dashboard {
    display: grid;
    grid-template-columns: 1fr 240px;
    grid-template-rows: auto 1fr;
  }
  .rf-status { grid-column: 1 / -1; }
  .rf-views { grid-column: 1; }
  .rf-sidebar {
    grid-column: 2;
    grid-row: 2;
    border-left: 1px solid var(--rf-border);
    overflow-y: auto;
  }
}
```

## Layout C: Fullscreen instrument (fills viewport)

For dedicated monitoring. The spectrum and waterfall divide the viewport height
proportionally; the table overlays as a compact strip.

```css
.rf-dashboard--fullscreen {
  height: 100%;
  display: grid;
  grid-template-rows: auto 2fr 1fr auto;
}
```

Use `height: 100%` on `html` and `body`, not `100vh`, to stay inside safe-area insets.

## Aligning spectrum + waterfall + overlays

When the spectrum uses a chart library (uPlot) and the waterfall is a raw canvas,
their pixel grids don't match by default — the chart has internal margins for axis
labels that the canvas doesn't. Overlays (channel bands, occupied highlights) also
need to land on the exact same frequency columns in both views. Three mechanisms
solve this:

### 1. Waterfall tracks the chart's plot area

uPlot exposes `chart.bbox` — the actual drawing rectangle in canvas pixels (not CSS
pixels). Convert to CSS pixels and apply to the waterfall canvas:

```typescript
function alignWaterfall(chart: uPlot, canvas: HTMLCanvasElement): void {
  const plotLeft = chart.bbox.left / devicePixelRatio;
  const plotWidth = chart.bbox.width / devicePixelRatio;
  canvas.style.marginLeft = `${plotLeft}px`;
  canvas.style.width = `${plotWidth}px`;
  canvas.width = Math.round(plotWidth);
}
```

Call this after the first `setData` and on resize. The waterfall canvas backing
store (`canvas.width`) must match the CSS width to avoid interpolation blur.

### 2. Spectrum overlays use `valToPos`, not manual math

uPlot's `valToPos(value, scaleKey, canvasPixels)` converts a data value to a pixel
position that respects the current zoom, pan, and axis layout. Manual math against
`bbox` drifts when the axis label width changes (wider numbers → more margin).

```typescript
// Inside a uPlot draw hook:
const xLo = u.valToPos(loHz, "x", true);   // canvas pixels
const xHi = u.valToPos(hiHz, "x", true);
ctx.fillRect(xLo, u.bbox.top, xHi - xLo, u.bbox.height);
```

The third argument (`true`) returns canvas pixels, which is what `ctx.fillRect`
expects. Without it you get CSS pixels and the overlay appears at half-scale on
HiDPI screens.

### 3. No overlays on the waterfall

The waterfall is a heatmap — colour IS the data. Overlaying occupation bands on it
adds visual noise without information. Channel bands belong on the spectrum trace
only, where they help read which peaks correspond to which channels. The waterfall's
vertical alignment with the spectrum already shows the same correspondence.

### Why this matters

The frequency axis is the shared coordinate between spectrum and waterfall. If bin N
in the spectrum is not directly above bin N in the waterfall, the user reads false
correlations. Getting this wrong is the most common visual bug in RF dashboards:

- **Wrong**: both canvases at `width: 100%` but different internal margins
- **Wrong**: chart library uses padding for labels, waterfall canvas starts at x=0
- **Wrong**: overlay positions calculated with manual `(hz - min) / range * width`
  while the chart uses its own layout engine — they drift on resize and zoom
- **Right**: one source of truth for the plot area (the chart's `bbox`), waterfall
  and overlays both derive from it

## Mobile (< 480px)

Always Layout A. Reduce spectrum height to 160px. Hide the occupancy percentage column
in the channel table. Use `font-size: 0.75rem` on the table.

```css
@media (max-width: 479px) {
  .rf-panel canvas { height: 160px; }
  .rf-channels td:nth-child(4),
  .rf-channels th:nth-child(4) { display: none; }
}
```

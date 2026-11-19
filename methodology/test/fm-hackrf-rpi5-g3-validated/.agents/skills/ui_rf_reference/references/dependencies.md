# Recommended Libraries

Libraries evaluated for real-time RF visualization in a browser. S3 picks based on the
project's actual needs — favour ready tools that save code over hand-rolling for purity.

## Decision tree

```
Spectrum trace (power vs frequency):
  └── uPlot (default) — 45 KB buys grid, axes, cursor, zoom, resize, multi-series
      └── Canvas 2D only when: no interaction at all AND the trace is decorative

Waterfall (scrolling heatmap):
  ├── ≤ 200 rows AND ≤ 2048 bins → Canvas 2D ImageData (simplest, no dependency)
  └── > 200 rows OR > 2048 bins  → regl (GPU texture scrolling)

Channel table:
  └── HTML table (always) — tabular data with accessible semantics
```

The bias is toward less code, not fewer dependencies. 45 KB for a chart library that
handles grid, resize and interaction is not bloat — it's what libraries are for.

## Recommended

### uPlot — spectrum trace (default)

| Field | Value |
|-------|-------|
| Package | `uplot` |
| Size | ~45 KB min |
| License | MIT |
| Maintained | Yes (last release 2025) |
| CDN | `https://cdn.jsdelivr.net/npm/uplot@1.6.31/dist/uPlot.iife.min.js` |
| CSS | `https://cdn.jsdelivr.net/npm/uplot@1.6.31/dist/uPlot.min.css` |

**What it does well:** Line charts at extreme speed — 150k points cold-rendered in 90ms.
Streaming updates. Minimal API. Tiny footprint. Responsive. Grid, axis labels, crosshair
cursor, zoom/pan, multi-series — all out of the box.

**What it doesn't do:** Heatmaps, waterfall, 2D grids. It's a 1D chart library. The
waterfall needs a separate renderer.

**Use it for:** Every spectrum trace. The 45 KB pays for itself immediately in code you
don't write: axis formatting with engineering units, responsive resize, cursor readout,
grid lines at proper intervals. Writing these by hand costs 50+ lines for a worse result.

**Skip it only when:** The trace has zero interaction and is purely a background visual —
then Canvas 2D `drawSpectrum` from `canvas_patterns.md` is fine.

**Quick wiring:**
```typescript
import uPlot from "uPlot";

const opts: uPlot.Options = {
  width: container.clientWidth,
  height: 220,
  scales: { y: { range: [MIN_DBFS, MAX_DBFS] } },
  axes: [
    { font: "11px 'JetBrains Mono', monospace", stroke: "#7e97aa", grid: { stroke: "#1e3a52" } },
    { font: "11px 'JetBrains Mono', monospace", stroke: "#7e97aa", grid: { stroke: "#1e3a52" },
      values: (_, ticks) => ticks.map(v => `${v} dBFS`) },
  ],
  series: [
    {},
    { stroke: "#72d8ff", width: 1.5, label: "Power" },
  ],
};
const chart = new uPlot(opts, [freqAxis, spectrumBins], container);

// On each frame:
chart.setData([freqAxis, newBins]);
```

### regl — WebGL waterfall renderer

| Field | Value |
|-------|-------|
| Package | `regl` |
| Size | ~73 KB min |
| License | MIT |
| Maintained | Yes |
| CDN | `https://cdn.jsdelivr.net/npm/regl@2.1.0/dist/regl.min.js` |

**What it does well:** Thin WebGL wrapper. GPU texture scrolling — the waterfall never
copies pixel data, just advances a row pointer and re-renders. Handles 4096×512
waterfalls at 60fps without breaking a sweat.

**What it doesn't do:** No chart primitives. Axes, labels, grids are all DIY. It's a
rendering layer, not a charting library.

**When to use:** When Canvas 2D `putImageData` drops below the frame rate. Usually
>200 rows or >2048 bins, or when you need smooth colourmap interpolation.

**When NOT to use:** When Canvas 2D keeps up. Adding WebGL for a 120×853 waterfall
is premature optimisation — the waterfall's ImageData path is simple enough to hand-roll.

## Evaluated and rejected

### SigPlot

The only RF-native browser library (spectrum + raster). Built by LGS Innovations for
SIGINT. Apache-2.0.

**Rejected because:** Last updated January 2023. ~39 GitHub stars. No active maintainer.
Canvas 2D only, no WebGL path. Imperative API, not component-friendly. Using it means
adopting an abandoned dependency.

### spectrogram-js / spectrodrom

Lightweight waterfall components inspired by bastibe's WebGL-Spectrogram.

**Rejected because:** Low adoption, minimal documentation, uncertain maintenance. The
regl approach gives the same performance with a maintained dependency.

### Plotly

Feature-rich charting library with heatmap support.

**Rejected because:** ~3.5 MB bundle. Designed for dashboards, not real-time streaming.
Redraws the entire chart on every update. The overhead is unacceptable at 2 Hz with
853 bins.

### D3

The standard for data visualization.

**Rejected because:** SVG-based rendering doesn't scale to real-time streaming of
hundreds of elements per frame. Canvas renderers exist in the D3 ecosystem but add
complexity without benefit over direct Canvas 2D.

## CSS — no framework needed

No RF-themed CSS framework exists on npm. OpenWebRX, SDR++, CubicSDR, and every
well-regarded SDR console hand-rolls its dark theme with plain CSS. The palette in
`palette.md` is the starting point; the layout in `layout.md` is the structure.
Google Fonts for typography (see `design_principles.md`). That's it.

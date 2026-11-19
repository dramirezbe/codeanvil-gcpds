# Canvas Patterns for RF Visualization

Starter patterns for the core RF views. Adapt to the project's actual data shape —
these are reference implementations, not locked templates.

## 1. Spectrum Trace (uPlot — default)

uPlot is the default for spectrum traces. 45 KB buys grid, axes, cursor, zoom, resize
and multi-series — writing these by hand costs more code for a worse result.

```typescript
import uPlot from "uPlot";

function createSpectrum(
  container: HTMLElement,
  freqAxis: number[],
  minDbfs: number,
  maxDbfs: number,
): uPlot {
  const opts: uPlot.Options = {
    width: container.clientWidth,
    height: 220,
    cursor: { show: true, x: true, y: true },
    scales: {
      x: { time: false },
      y: { range: [minDbfs, maxDbfs] },
    },
    axes: [
      {
        font: "11px 'JetBrains Mono', monospace",
        stroke: "#7e97aa",
        grid: { stroke: "#1e3a52", width: 1 },
        values: (_, ticks) => ticks.map(v => `${(v / 1e6).toFixed(1)}`),
        label: "MHz",
      },
      {
        font: "11px 'JetBrains Mono', monospace",
        stroke: "#7e97aa",
        grid: { stroke: "#1e3a52", width: 1 },
        values: (_, ticks) => ticks.map(v => `${v}`),
        label: "dBFS",
      },
    ],
    series: [
      {},
      {
        stroke: "#72d8ff",
        width: 1.5,
        label: "Power",
        points: { show: false },
      },
    ],
  };
  return new uPlot(opts, [freqAxis, new Float64Array(freqAxis.length)], container);
}

// On each frame:
// chart.setData([freqAxis, spectrumBins]);
```

**Key decisions:**
- uPlot handles grid, axes, resize, cursor — no hand-rolled drawing code
- `scales.x.time: false` — frequency axis, not time
- `points.show: false` — 853 bins, points would overlap
- Axis formatters show engineering units (MHz, dBFS)
- Responsive: `new ResizeObserver` → `chart.setSize()`

## 1b. Spectrum Trace (Canvas 2D — fallback)

Use only when the trace has zero interaction and is purely a background visual.

```typescript
function drawSpectrum(
  ctx: CanvasRenderingContext2D,
  bins: number[],
  width: number,
  height: number,
  minDbfs: number,
  maxDbfs: number,
): void {
  const range = maxDbfs - minDbfs;
  ctx.clearRect(0, 0, width, height);
  ctx.beginPath();
  for (let i = 0; i < bins.length; i++) {
    const level = Math.max(minDbfs, Math.min(maxDbfs, bins[i]));
    const y = height * (1 - (level - minDbfs) / range);
    if (i === 0) ctx.moveTo(i, y);
    else ctx.lineTo(i, y);
  }
  ctx.strokeStyle = "#72d8ff";
  ctx.lineWidth = 1.5;
  ctx.stroke();
}
```

**Key decisions:**
- No grid, no axes, no cursor — if you need any of these, use uPlot
- Read palette tokens once at init via `getComputedStyle`, not per frame

## 1c. Channel Overlay (uPlot draw plugin)

Occupied-channel bands and frequency labels drawn directly on the spectrum chart.
This is a uPlot plugin — it fires after the series renders, so the bands appear
behind the trace but above the grid.

```typescript
interface ChannelOverlay {
  channels: { f_mhz: number; occupied: boolean }[];
}

function channelPlugin(state: ChannelOverlay): uPlot.Plugin {
  const CHANNEL_BW_HZ = 200_000;
  return {
    hooks: {
      draw: [(u: uPlot) => {
        const ctx = u.ctx;
        const dpr = devicePixelRatio;
        const plotTop = u.bbox.top;
        const plotHeight = u.bbox.height;

        for (const ch of state.channels) {
          const centerHz = ch.f_mhz * 1e6;
          const xLo = u.valToPos(centerHz - CHANNEL_BW_HZ / 2, "x", true);
          const xHi = u.valToPos(centerHz + CHANNEL_BW_HZ / 2, "x", true);
          const xCenter = u.valToPos(centerHz, "x", true);

          if (ch.occupied) {
            ctx.fillStyle = "rgba(23, 71, 53, 0.5)";
            ctx.fillRect(xLo, plotTop, xHi - xLo, plotHeight);
          }

          ctx.strokeStyle = ch.occupied
            ? "rgba(139, 240, 172, 0.3)"
            : "rgba(187, 203, 216, 0.12)";
          ctx.lineWidth = dpr;
          ctx.beginPath();
          ctx.moveTo(xCenter, plotTop + 14 * dpr);
          ctx.lineTo(xCenter, plotTop + plotHeight);
          ctx.stroke();

          ctx.fillStyle = ch.occupied ? "#8bf0ac" : "#4a6478";
          ctx.font = `${Math.round(9 * dpr)}px 'JetBrains Mono', monospace`;
          ctx.textAlign = "center";
          ctx.textBaseline = "top";
          ctx.fillText(ch.f_mhz.toFixed(1), xCenter, plotTop + 2 * dpr);
        }
      }],
    },
  };
}

// Wire it:
// const overlayState: ChannelOverlay = { channels: [] };
// const chart = new uPlot({ ..., plugins: [channelPlugin(overlayState)] }, data, el);
// On each frame: overlayState.channels = frame.channels; chart.setData(...);
```

**Key decisions:**
- `valToPos(hz, "x", true)` returns canvas pixels — the only correct coordinate
  for `ctx.fillRect`. Without `true` you get CSS pixels and the overlay scales
  wrong on HiDPI.
- The state object is shared by reference — mutate it before `setData` and the
  draw hook reads the current channels.
- No overlay on the waterfall — the heatmap colour IS the data; overlaying bands
  on it adds noise without information.

## 2. Waterfall / Spectrogram (Canvas 2D with ImageData)

A scrolling heatmap: each row is one spectrum frame, newest on top, colour-mapped
from noise floor to peak.

```typescript
const HISTORY = 120;  // rows = 60 seconds at 2 Hz

function drawWaterfall(
  ctx: CanvasRenderingContext2D,
  history: number[][],     // most recent first, each row = bins
  minDbfs: number,
  maxDbfs: number,
): void {
  const width = history[0]?.length ?? 0;
  const image = ctx.createImageData(width, HISTORY);
  const range = maxDbfs - minDbfs;

  for (let y = 0; y < history.length; y++) {
    const row = history[y];
    if (!row) continue;
    for (let x = 0; x < width; x++) {
      const t = Math.max(0, Math.min(1, (row[x] - minDbfs) / range));
      const offset = 4 * (y * width + x);
      // Three-stop colourmap: cold → warm → hot
      if (t < 0.5) {
        const s = t * 2;
        image.data[offset]     = 20 + 94 * s;    // R
        image.data[offset + 1] = 40 + 176 * s;   // G
        image.data[offset + 2] = 56 + 199 * s;   // B
      } else {
        const s = (t - 0.5) * 2;
        image.data[offset]     = 114 + 141 * s;
        image.data[offset + 1] = 216 - 216 * s * 0.3;
        image.data[offset + 2] = 255;
      }
      image.data[offset + 3] = 255;
    }
  }
  ctx.putImageData(image, 0, 0);
}
```

**When to upgrade to WebGL (regl):**
- More than ~200 rows or >2048 bins — ImageData starts dropping frames
- Need smooth colourmap interpolation in the shader
- Want GPU-side texture scrolling instead of rewriting every pixel

## 3. WebGL Waterfall with regl (high-performance path)

For projects where Canvas 2D waterfall drops below the update rate.

```typescript
// Requires: npm install regl
import createREGL from "regl";

function createWaterfallRenderer(canvas: HTMLCanvasElement, bins: number, rows: number) {
  const regl = createREGL({ canvas, attributes: { antialias: false } });

  const texture = regl.texture({
    width: bins, height: rows,
    format: "luminance", type: "float",
    mag: "nearest", min: "nearest",
    wrap: "clamp",
  });

  const draw = regl({
    vert: `
      precision mediump float;
      attribute vec2 position;
      varying vec2 uv;
      uniform float scroll;
      void main() {
        uv = position * 0.5 + 0.5;
        uv.y = fract(uv.y + scroll);
        gl_Position = vec4(position, 0, 1);
      }
    `,
    frag: `
      precision mediump float;
      varying vec2 uv;
      uniform sampler2D spectrum;
      uniform vec3 cold, warm, hot;
      void main() {
        float t = texture2D(spectrum, uv).r;
        vec3 color = t < 0.5
          ? mix(cold, warm, t * 2.0)
          : mix(warm, hot, (t - 0.5) * 2.0);
        gl_FragColor = vec4(color, 1.0);
      }
    `,
    attributes: { position: [[-1,-1],[1,-1],[-1,1],[1,1]] },
    uniforms: {
      spectrum: texture,
      scroll: regl.prop("scroll"),
      cold: [0.08, 0.16, 0.22],   // --rf-wf-cold normalised
      warm: [0.45, 0.85, 1.0],    // --rf-wf-warm
      hot:  [1.0, 1.0, 1.0],      // --rf-wf-hot
    },
    primitive: "triangle strip",
    count: 4,
  });

  let rowIndex = 0;

  return {
    pushRow(data: Float32Array) {
      // Normalise data to 0–1 range before uploading
      texture.subimage({ data, width: bins, height: 1 }, 0, rowIndex % rows);
      rowIndex++;
    },
    render() {
      draw({ scroll: (rowIndex % rows) / rows });
    },
  };
}
```

**Key decisions:**
- Luminance float texture: one channel, the dBFS value normalised to 0–1
- Colourmap in the fragment shader: change `cold/warm/hot` uniforms from palette tokens
- Scroll by advancing the texture row pointer — no data copy
- `mag: "nearest"` preserves bin boundaries; switch to `"linear"` for smooth interpolation

## 4. Channel Table (DOM, not canvas)

The channel table is better as HTML than canvas — it's tabular data with accessible
semantics and state-dependent styling.

```typescript
function renderChannelTable(
  container: HTMLElement,
  channels: { f_mhz: number; power_dbfs: number; occupied: boolean; occupancy: number }[],
): void {
  // Build once, update per frame
  let tbody = container.querySelector("tbody");
  if (!tbody) {
    container.innerHTML = `
      <table class="rf-channels">
        <thead><tr>
          <th scope="col">Frequency</th>
          <th scope="col">Power</th>
          <th scope="col">Status</th>
          <th scope="col">Occupancy</th>
        </tr></thead>
        <tbody></tbody>
      </table>`;
    tbody = container.querySelector("tbody")!;
  }

  // Reuse rows instead of rebuilding DOM each frame
  while (tbody.children.length < channels.length) {
    const tr = document.createElement("tr");
    for (let i = 0; i < 4; i++) tr.insertCell();
    tbody.appendChild(tr);
  }

  for (let i = 0; i < channels.length; i++) {
    const ch = channels[i];
    const tr = tbody.children[i] as HTMLTableRowElement;
    tr.dataset.occupied = String(ch.occupied);
    tr.cells[0].textContent = `${ch.f_mhz.toFixed(1)} MHz`;
    tr.cells[1].textContent = `${ch.power_dbfs.toFixed(1)} dBFS`;
    tr.cells[2].textContent = ch.occupied ? "Occupied" : "Clear";
    tr.cells[3].textContent = `${(ch.occupancy * 100).toFixed(1)}%`;
  }
}
```

**Styling:**
```css
.rf-channels {
  width: 100%;
  border-collapse: collapse;
  font-variant-numeric: tabular-nums;
  font-family: var(--rf-font-mono);
  font-size: 0.8125rem;
}
.rf-channels th {
  text-align: left;
  color: var(--rf-fg-muted);
  font-weight: 500;
  padding: 0.375rem 0.75rem;
  border-bottom: 1px solid var(--rf-border);
}
.rf-channels td {
  padding: 0.375rem 0.75rem;
  border-bottom: 1px solid var(--rf-border-subtle);
}
.rf-channels tr[data-occupied="true"] {
  background: var(--rf-occupied);
  color: var(--rf-occupied-fg);
}
```

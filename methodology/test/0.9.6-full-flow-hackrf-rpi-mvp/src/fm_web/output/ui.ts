/** RF instrument panel: live spectrum, waterfall and channel readout. */
export function buildDashboardHtml(_activeRoute = "/spectrum"): string {
  return `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<meta name="theme-color" content="#0a1620"/>
<title>FM Monitor · COL-001</title>
<link rel="stylesheet" href="/assets/uplot.css"/>
<style>
:root {
  color-scheme: dark;
  --rf-bg: #0a1620;
  --rf-bg-panel: #0e1e2c;
  --rf-bg-elevated: #142838;
  --rf-border: #1e3a52;
  --rf-border-subtle: #152a3c;
  --rf-fg: #d4dfe8;
  --rf-fg-muted: #7e97aa;
  --rf-fg-dim: #4a6478;
  --rf-signal: #72d8ff;
  --rf-signal-glow: rgba(114, 216, 255, .15);
  --rf-occupied: #174735;
  --rf-occupied-fg: #8bf0ac;
  --rf-clear: #bbcbd8;
  --rf-threshold: #f0c040;
  --rf-error: #e05454;
  --rf-connected: #4ade80;
  --rf-wf-cold: #142838;
  --rf-wf-warm: #72d8ff;
  --rf-wf-hot: #ffffff;
  --rf-accent: #3b8eea;
  --rf-accent-hover: #5aa3f0;
  --rf-font-mono: ui-monospace, "SFMono-Regular", Consolas, monospace;
}
* { box-sizing: border-box; }
html, body { min-height: 100%; }
body {
  margin: 0;
  background: var(--rf-bg);
  color: var(--rf-fg);
  font: 14px/1.45 Inter, ui-sans-serif, system-ui, sans-serif;
}
button, a { font: inherit; }
a { color: inherit; text-decoration: none; }
.instrument { min-height: 100vh; display: flex; flex-direction: column; }
.masthead {
  display: flex; align-items: center; gap: 16px; min-height: 54px;
  padding: 0 22px; border-bottom: 1px solid var(--rf-border); background: var(--rf-bg-panel);
}
.brand { display: inline-flex; align-items: baseline; gap: 8px; font-weight: 700; letter-spacing: .02em; white-space: nowrap; }
.brand-mark { color: var(--rf-signal); font: 700 18px/1 var(--rf-font-mono); }
.brand-name { font-size: 13px; }
.device-name { color: var(--rf-fg-muted); font-size: 12px; border-left: 1px solid var(--rf-border); padding-left: 16px; }
.head-status { margin-left: auto; display: flex; align-items: center; gap: 18px; color: var(--rf-fg-muted); font: 11px var(--rf-font-mono); text-transform: uppercase; letter-spacing: .04em; }
.status-item { display: inline-flex; align-items: center; gap: 7px; white-space: nowrap; }
.led { width: 7px; height: 7px; border-radius: 50%; background: var(--rf-fg-dim); }
.led.live { background: var(--rf-connected); box-shadow: 0 0 7px rgba(74, 222, 128, .35); }
.led.warn { background: var(--rf-threshold); }
.led.error { background: var(--rf-error); }
.masthead strong { color: var(--rf-fg); font-weight: 600; }
.bandline {
  min-height: 40px; display: flex; align-items: center; gap: 15px; padding: 0 22px;
  border-bottom: 1px solid var(--rf-border-subtle); color: var(--rf-fg-muted);
  font: 11px var(--rf-font-mono); letter-spacing: .04em;
}
.bandline .band-title { color: var(--rf-fg); }
.bandline .band-range { color: var(--rf-signal); }
.evidence { margin-left: auto; color: var(--rf-fg-dim); letter-spacing: 0; text-transform: none; }
main { width: 100%; max-width: 1600px; margin: 0 auto; padding: 18px 22px 30px; }
.notice {
  display: flex; align-items: center; gap: 10px; min-height: 34px; margin-bottom: 12px;
  padding: 7px 10px; border: 1px solid var(--rf-border); background: var(--rf-bg-panel);
  color: var(--rf-fg-muted); font-size: 12px;
}
.notice-mark { color: var(--rf-threshold); font: 700 12px var(--rf-font-mono); }
.readouts { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); border: 1px solid var(--rf-border); background: var(--rf-bg-panel); margin-bottom: 12px; }
.readout { min-height: 68px; padding: 10px 14px; border-right: 1px solid var(--rf-border); }
.readout:last-child { border-right: 0; }
.readout-label { color: var(--rf-fg-dim); font: 10px var(--rf-font-mono); letter-spacing: .07em; text-transform: uppercase; }
.readout-value { margin-top: 5px; color: var(--rf-fg); font: 600 18px/1.15 var(--rf-font-mono); font-variant-numeric: tabular-nums; }
.readout-value.small { font-size: 14px; }
.panel { border: 1px solid var(--rf-border); background: var(--rf-bg-panel); margin-bottom: 12px; }
.panel-head { min-height: 39px; display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 0 13px; border-bottom: 1px solid var(--rf-border); }
.panel-title { margin: 0; color: var(--rf-fg-muted); font: 10px var(--rf-font-mono); letter-spacing: .08em; text-transform: uppercase; }
.panel-meta { color: var(--rf-fg-dim); font: 10px var(--rf-font-mono); font-variant-numeric: tabular-nums; }
.spectrum-body { padding: 5px 10px 2px; }
#spectrum-chart { width: 100%; height: 300px; }
.u-legend { display: none; }
.u-wrap { background: transparent; }
.uplot { background: transparent; }
.u-axis { color: var(--rf-fg-muted); }
.u-over { cursor: crosshair; }
.chart-foot { min-height: 28px; display: flex; align-items: center; gap: 16px; padding: 0 13px 8px; color: var(--rf-fg-dim); font: 10px var(--rf-font-mono); }
.chart-foot { flex-wrap: wrap; padding-top: 6px; }
.chart-controls { display: flex; flex-wrap: wrap; gap: 12px; }
.chart-controls label { display: inline-flex; align-items: center; gap: 6px; color: var(--rf-fg); }
.chart-controls select { font: inherit; color: var(--rf-fg); background: var(--rf-bg-elevated); border: 1px solid var(--rf-border); border-radius: 3px; padding: 4px; }
#cursor-readout { color: var(--rf-fg); background: var(--rf-bg-elevated); border: 1px solid var(--rf-border); padding: 5px 8px; font-size: 12px; }
#refresh-state { color: var(--rf-fg-muted); }
[hidden] { display: none !important; }
.legend-key { display: inline-flex; align-items: center; gap: 6px; }
.legend-line { width: 17px; height: 2px; background: var(--rf-signal); box-shadow: 0 0 5px var(--rf-signal-glow); }
.legend-band { width: 10px; height: 10px; background: var(--rf-occupied); border: 1px solid var(--rf-occupied-fg); }
.waterfall-wrap { padding: 0; background: var(--rf-bg); }
#waterfall { display: block; width: 100%; height: 148px; image-rendering: pixelated; }
.waterfall-axis { display: flex; justify-content: space-between; padding: 5px 12px 8px; color: var(--rf-fg-dim); font: 10px var(--rf-font-mono); }
.channels-panel { overflow: hidden; }
.table-scroll { max-height: 360px; overflow: auto; }
.channels { width: 100%; border-collapse: collapse; font: 11px var(--rf-font-mono); font-variant-numeric: tabular-nums; }
.channels th { position: sticky; top: 0; z-index: 1; padding: 8px 12px; background: var(--rf-bg-panel); color: var(--rf-fg-dim); font-weight: 500; text-align: left; border-bottom: 1px solid var(--rf-border); }
.channels td { padding: 6px 12px; border-bottom: 1px solid var(--rf-border-subtle); color: var(--rf-fg-muted); }
.channels tr:last-child td { border-bottom: 0; }
.channels .free-run td { color: var(--rf-fg-muted); font-size: 10px; }
.channels .frequency, .channels .power { color: var(--rf-fg); }
.channels tr[data-state="Occupied"] { background: var(--rf-occupied); }
.channels tr[data-state="Occupied"] .state { color: var(--rf-occupied-fg); }
.state { letter-spacing: .04em; }
.empty { padding: 28px 14px; color: var(--rf-fg-dim); text-align: center; font: 12px var(--rf-font-mono); }
.footnote { display: flex; justify-content: space-between; gap: 16px; color: var(--rf-fg-dim); font-size: 11px; }
.footnote span:last-child { font-family: var(--rf-font-mono); }
@media (prefers-color-scheme: light) {
  :root:not([data-theme="dark"]) {
    color-scheme: light;
    --rf-bg: #f4f6f8; --rf-bg-panel: #fff; --rf-bg-elevated: #fff;
    --rf-border: #d0d8e0; --rf-border-subtle: #e4e9ee;
    --rf-fg: #1a2a3a; --rf-fg-muted: #5a6a7a; --rf-fg-dim: #98a8b4;
    --rf-signal: #0066aa; --rf-signal-glow: rgba(0, 102, 170, .08);
    --rf-occupied: #d6f5e0; --rf-occupied-fg: #0d6832; --rf-clear: #5a6a7a;
    --rf-threshold: #b8860b; --rf-error: #c03030; --rf-connected: #22804a;
    --rf-wf-cold: #e8ecf0; --rf-wf-warm: #0066aa; --rf-wf-hot: #001833;
    --rf-accent: #2070c0; --rf-accent-hover: #1860a8;
  }
}
@media (max-width: 740px) {
  .masthead { padding: 0 13px; gap: 10px; }
  .device-name { display: none; }
  .head-status { gap: 10px; font-size: 9px; }
  .head-status .status-item:nth-child(3) { display: none; }
  .bandline { padding: 0 13px; }
  .evidence { display: none; }
  main { padding: 12px 10px 22px; }
  .readouts { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .readout:nth-child(2) { border-right: 0; }
  .readout:nth-child(-n+2) { border-bottom: 1px solid var(--rf-border); }
  #spectrum-chart { height: 245px; }
  #waterfall { height: 112px; }
  .panel-meta { font-size: 9px; }
}
</style>
</head>
<body>
<div class="instrument">
  <header class="masthead">
    <a class="brand" href="/spectrum" aria-label="FM Monitor spectrum">
      <span class="brand-mark">FM</span><span class="brand-name">MONITOR / COL-001</span>
    </a>
    <span class="device-name">HackRF One · Raspberry Pi 5</span>
    <div class="head-status" aria-live="polite">
      <span class="status-item"><i class="led" id="rx-led"></i><strong id="rx-state">WAITING</strong></span>
      <span class="status-item">CLOCK <strong id="sync-state">UNSYNCED</strong></span>
      <span class="status-item">SOURCE <strong id="hal-state">—</strong></span>
    </div>
  </header>
  <div class="bandline">
    <span class="band-title">LIVE SPECTRUM</span>
    <span class="band-range">87.5–107.6 MHz · 20.1 MHz span</span>
    <span>100 kHz CHANNEL GRID</span>
    <span class="evidence">Screening evidence only · not a compliance determination</span>
  </div>
  <main>
    <div class="notice" id="calibration-notice">
      <span class="notice-mark">!</span>
      <span>Raw receiver level in dBFS. No valid K(f) calibration. Occupancy is relative receiver-level screening only.</span>
    </div>
    <section class="readouts" aria-label="Current sweep">
      <div class="readout"><div class="readout-label">Last sweep</div><div class="readout-value" id="scan-age">—</div></div>
      <div class="readout"><div class="readout-label">Sweep number</div><div class="readout-value" id="scan-number">—</div></div>
      <div class="readout"><div class="readout-label">Acquisition</div><div class="readout-value small">3 × 10 MS/s</div></div>
      <div class="readout"><div class="readout-label">Receiver level</div><div class="readout-value small">dBFS · 8 bit I/Q</div></div>
    </section>
    <section class="panel" aria-labelledby="spectrum-heading">
      <div class="panel-head">
        <h1 class="panel-title" id="spectrum-heading">Frequency / amplitude</h1>
        <span class="panel-meta" id="scan-time">AWAITING FIRST SWEEP</span>
      </div>
      <div class="spectrum-body"><div id="spectrum-chart" role="img" aria-label="Live FM spectrum in dBFS"></div></div>
      <div class="chart-foot">
        <span class="legend-key"><i class="legend-line"></i>RX power</span>
        <span class="legend-key" id="occupied-legend" hidden><i class="legend-band"></i>Screened occupied</span>
        <output id="cursor-readout">Cursor · hover over spectrum</output>
        <div class="chart-controls">
          <label>Vertical range <select id="vertical-range"><option value="auto">Auto</option><option value="full">Full (−120 to 0 dBFS)</option></select></label>
          <label>Refresh interval <select id="refresh-interval"><option value="500" selected>0.5 s</option><option value="1000">1 s</option><option value="2000">2 s</option><option value="6000">6 s</option><option value="10000">10 s</option></select></label>
        </div>
        <span id="refresh-state" role="status" hidden></span>
      </div>
    </section>
    <section class="panel" aria-labelledby="waterfall-heading">
      <div class="panel-head"><h2 class="panel-title" id="waterfall-heading">Recent sweeps</h2><span class="panel-meta"><span id="sweep-count">0 / 120</span> SWEEPS · NEWEST AT TOP</span></div>
      <div class="waterfall-wrap"><canvas id="waterfall" aria-label="Waterfall of recent FM spectrum sweeps"></canvas></div>
      <div class="waterfall-axis"><span>87.5 MHz</span><span>97.55 MHz</span><span>107.6 MHz</span></div>
    </section>
    <section class="panel channels-panel" aria-labelledby="channels-heading">
      <div class="panel-head"><h2 class="panel-title" id="channels-heading">Channel grid</h2><span class="panel-meta"><span id="occupancy-threshold">Awaiting screening threshold</span></span></div>
      <div class="table-scroll" id="channel-table"><div class="empty">Waiting for I/Q samples from the receiver.</div></div>
    </section>
    <footer class="footnote"><span>Occupancy is receiver-level screening, not a calibrated measurement or compliance verdict.</span><span id="updated-at">—</span></footer>
  </main>
</div>
<script src="/assets/uplot.js"></script>
<script>
const MIN_HZ = 87_500_000;
const MAX_HZ = 107_600_000;
const MIN_DBFS = -120;
const MAX_DBFS = 0;
const HISTORY_ROWS = 120;
const WATERFALL_BINS = 1600;
const HISTORY = [];
let chart = null;
let lastScanId = null;
let lastSweepTime = null;
let lastRenderedScanId = null;
let lastRenderedThreshold = null;
let refreshTimer = null;
let refreshing = false;

function el(id) { return document.getElementById(id); }
function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, function (ch) {
    if (ch === "&") return "&amp;";
    if (ch === "<") return "&lt;";
    if (ch === ">") return "&gt;";
    if (ch.charCodeAt(0) === 34) return "&quot;";
    return "&#39;";
  });
}
function css(name) { return getComputedStyle(document.documentElement).getPropertyValue(name).trim(); }
function parseColor(value) {
  const hex = value.match(/^#([0-9a-f]{6})$/i);
  if (hex) return [parseInt(hex[1].slice(0, 2), 16), parseInt(hex[1].slice(2, 4), 16), parseInt(hex[1].slice(4, 6), 16)];
  const rgb = value.match(/[0-9.]+/g);
  return rgb ? rgb.slice(0, 3).map(Number) : [0, 0, 0];
}
function interpolate(a, b, t) { return Math.round(a + (b - a) * t); }
function colourAt(t, cold, warm, hot) {
  const lo = t < 0.62 ? cold : warm;
  const hi = t < 0.62 ? warm : hot;
  const local = t < 0.62 ? t / 0.62 : (t - 0.62) / 0.38;
  return [interpolate(lo[0], hi[0], local), interpolate(lo[1], hi[1], local), interpolate(lo[2], hi[2], local)];
}
function statusLed(kind, text) {
  el("rx-led").className = "led " + kind;
  el("rx-state").textContent = text;
}
function binsForBand(data, count) {
  const values = new Float32Array(count);
  values.fill(Number.NaN);
  for (const step of data.raw_steps || []) {
    const bins = step.points_dbfs || [];
    for (let i = 0; i < bins.length; i++) {
      const value = bins[i];
      if (value === null || !Number.isFinite(value)) continue;
      const frequency = step.first_frequency_hz + i * step.point_spacing_hz;
      if (frequency < MIN_HZ || frequency > MAX_HZ) continue;
      const index = Math.max(0, Math.min(count - 1, Math.round((frequency - MIN_HZ) / (MAX_HZ - MIN_HZ) * (count - 1))));
      values[index] = Number.isFinite(values[index]) ? Math.max(values[index], value) : value;
    }
  }
  return values;
}
function chartData(data) {
  const grouped = new Map();
  for (const step of data.raw_steps || []) {
    for (let i = 0; i < (step.points_dbfs || []).length; i++) {
      const value = step.points_dbfs[i];
      const frequency = step.first_frequency_hz + i * step.point_spacing_hz;
      if (value === null || !Number.isFinite(value) || frequency < MIN_HZ || frequency > MAX_HZ) continue;
      const key = Math.round(frequency / 10) * 10;
      const group = grouped.get(key) || [];
      group.push(value);
      grouped.set(key, group);
    }
  }
  const frequencies = Array.from(grouped.keys()).sort((a, b) => a - b);
  const levels = frequencies.map((f) => {
    const values = grouped.get(f);
    return values.reduce((sum, value) => sum + value, 0) / values.length;
  });
  return [frequencies, levels];
}
function isClassified(point) {
  return point && (!point.withheld_reason || point.withheld_reason === "none");
}
function occupiedPlugin(state) {
  return { hooks: { draw: [function (u) {
    const channels = state.channels.filter((channel) => isClassified(channel) && channel.occupancy === "Occupied");
    const ctx = u.ctx;
    const top = u.bbox.top;
    const height = u.bbox.height;
    const dpr = devicePixelRatio || 1;
    for (const channel of channels) {
      const left = u.valToPos(channel.freq_hz - 50_000, "x", true);
      const right = u.valToPos(channel.freq_hz + 50_000, "x", true);
      ctx.fillStyle = css("--rf-occupied");
      ctx.globalAlpha = 0.18;
      ctx.fillRect(left, top, right - left, height);
      ctx.globalAlpha = 1;
      ctx.strokeStyle = css("--rf-occupied-fg");
      ctx.lineWidth = dpr;
      ctx.beginPath();
      ctx.moveTo(u.valToPos(channel.freq_hz, "x", true), top);
      ctx.lineTo(u.valToPos(channel.freq_hz, "x", true), top + height);
      ctx.stroke();
    }
  }] } };
}
function verticalRange(_chart, min, max) {
  if (el("vertical-range").value === "full" || !Number.isFinite(min) || !Number.isFinite(max)) {
    return [MIN_DBFS, MAX_DBFS];
  }
  const low = Math.min(MAX_DBFS - 20, Math.max(MIN_DBFS, Math.floor((min - 5) / 5) * 5));
  const high = Math.min(MAX_DBFS, Math.max(low + 20, Math.ceil((max + 5) / 5) * 5));
  return [low, high];
}
function updateCursor(u) {
  const frequency = u.data[0][u.cursor.idx];
  const level = u.data[1][u.cursor.idx];
  el("cursor-readout").textContent = Number.isFinite(frequency) && Number.isFinite(level)
    ? "Cursor · " + (frequency / 1e6).toFixed(4) + " MHz / " + level.toFixed(1) + " dBFS"
    : "Cursor · hover over spectrum";
}
function ensureChart(data, values) {
  const mount = el("spectrum-chart");
  if (chart || !window.uPlot || !mount.clientWidth) return;
  const state = { channels: Number.isFinite(data.occupancy_rule?.threshold_dbfs) ? data.points || [] : [] };
  const colors = getComputedStyle(document.documentElement);
  chart = new window.uPlot({
    width: mount.clientWidth,
    height: mount.clientHeight || 300,
    cursor: { show: true, x: true, y: true, drag: { setScale: false } },
    scales: {
      x: { time: false, range: [MIN_HZ, MAX_HZ] },
      y: { range: verticalRange },
    },
    axes: [
      {
        label: "Frequency · MHz",
        labelFont: "12px ui-monospace, monospace",
        font: "12px ui-monospace, monospace",
        stroke: colors.getPropertyValue("--rf-fg").trim(),
        grid: { stroke: colors.getPropertyValue("--rf-border").trim(), width: 1 },
        ticks: { stroke: colors.getPropertyValue("--rf-border").trim(), width: 1 },
        values: function (_u, ticks) { return ticks.map((value) => (value / 1e6).toFixed(1)); },
      },
      {
        label: "Level · dBFS",
        labelFont: "12px ui-monospace, monospace",
        font: "12px ui-monospace, monospace",
        stroke: colors.getPropertyValue("--rf-fg").trim(),
        grid: { stroke: colors.getPropertyValue("--rf-border").trim(), width: 1 },
        ticks: { stroke: colors.getPropertyValue("--rf-border").trim(), width: 1 },
        values: function (_u, ticks) { return ticks.map((value) => value.toFixed(0)); },
      },
    ],
    series: [
      {},
      {
        label: "RF power",
        stroke: colors.getPropertyValue("--rf-signal").trim(),
        width: 2,
        points: { show: false },
        spanGaps: false,
      },
    ],
    plugins: [occupiedPlugin(state)],
    hooks: {
      setCursor: [updateCursor],
      setData: [updateCursor],
    },
  }, values, mount);
  chart._rfState = state;
  const observer = new ResizeObserver(function () {
    const width = mount.clientWidth;
    const height = mount.clientHeight || 300;
    if (width && (width !== chart.width || height !== chart.height)) chart.setSize({ width, height });
  });
  observer.observe(mount);
}
function updateChart(data) {
  const values = chartData(data);
  if (!chart) {
    ensureChart(data, values);
    return;
  }
  chart._rfState.channels = Number.isFinite(data.occupancy_rule?.threshold_dbfs) ? data.points || [] : [];
  chart.setData(values);
}
function drawWaterfall() {
  const canvas = el("waterfall");
  if (!canvas) return;
  const width = WATERFALL_BINS;
  const height = HISTORY_ROWS;
  if (canvas.width !== width || canvas.height !== height) { canvas.width = width; canvas.height = height; }
  const ctx = canvas.getContext("2d", { alpha: false });
  const image = ctx.createImageData(width, height);
  const cold = parseColor(css("--rf-wf-cold"));
  const warm = parseColor(css("--rf-wf-warm"));
  const hot = parseColor(css("--rf-wf-hot"));
  for (let y = 0; y < height; y++) {
    const row = HISTORY[y];
    for (let x = 0; x < width; x++) {
      const level = row?.[x];
      const color = Number.isFinite(level)
        ? colourAt(Math.max(0, Math.min(1, (level + 65) / 55)), cold, warm, hot)
        : cold;
      const offset = 4 * (y * width + x);
      image.data[offset] = color[0];
      image.data[offset + 1] = color[1];
      image.data[offset + 2] = color[2];
      image.data[offset + 3] = 255;
    }
  }
  ctx.putImageData(image, 0, 0);
}
function recordSweep(data) {
  const id = data.scan_id;
  if (!Number.isSafeInteger(id) || id < 0 || (lastScanId !== null && id <= lastScanId)) return;
  const time = Date.parse(data.scan_ts_iso);
  if (Number.isFinite(time) && lastSweepTime !== null && time < lastSweepTime) return;
  const row = binsForBand(data, WATERFALL_BINS);
  if (!row.some(Number.isFinite)) return;
  lastScanId = id;
  if (Number.isFinite(time)) lastSweepTime = time;
  HISTORY.unshift(row);
  if (HISTORY.length > HISTORY_ROWS) HISTORY.pop();
  el("sweep-count").textContent = HISTORY.length + " / " + HISTORY_ROWS;
  drawWaterfall();
}
function renderChannels(data) {
  const rows = [];
  const points = new Map((data.points || []).map((point) => [point.channel, point]));
  let freeRows = [];
  function flushFreeRows() {
    if (freeRows.length <= 5) rows.push(...freeRows);
    else rows.push('<tr class="free-run"><td colspan="4">' + freeRows.length + ' consecutive Free channels hidden</td></tr>');
    freeRows = [];
  }
  for (let channel = 1; channel <= 199; channel++) {
    const frequency = 87_600_000 + (channel - 1) * 100_000;
    const point = points.get(channel);
    const level = point?.power_dbfs;
    const state = Number.isFinite(level) && isClassified(point) && point.occupancy !== "Uncertain"
      ? point.occupancy : "Unclassified";
    const row = "<tr data-state=\\"" + escapeHtml(state) + "\\"><td>" + String(channel).padStart(3, "0") + "</td><td class=\\"frequency\\">" + (frequency / 1e6).toFixed(1) + " MHz</td><td class=\\"power\\">" + (!Number.isFinite(level) ? "—" : level.toFixed(1) + " dBFS") + "</td><td class=\\"state\\">" + escapeHtml(state) + "</td></tr>";
    if (state === "Free") freeRows.push(row);
    else {
      flushFreeRows();
      rows.push(row);
    }
  }
  flushFreeRows();
  el("channel-table").innerHTML = "<table class=\\"channels\\"><thead><tr><th scope=\\"col\\">CH</th><th scope=\\"col\\">FREQUENCY</th><th scope=\\"col\\">CHANNEL LEVEL</th><th scope=\\"col\\">INTERPRETATION</th></tr></thead><tbody>" + rows.join("") + "</tbody></table>";
}
function formatAge(iso) {
  if (!iso) return "—";
  const seconds = Math.max(0, (Date.now() - Date.parse(iso)) / 1000);
  return seconds < 10 ? seconds.toFixed(1) + " s" : Math.floor(seconds) + " s";
}
function updateHeader(data) {
  const age = data.scan_ts_iso ? (Date.now() - Date.parse(data.scan_ts_iso)) / 1000 : Number.POSITIVE_INFINITY;
  if (data.data_state === "ok" && age < 15) statusLed("live", data.hal === "real" ? "HACKRF LIVE" : "MOCK SIGNAL");
  else if (data.data_state === "partial") statusLed("warn", "PARTIAL SWEEP");
  else statusLed("error", data.data_state === "no_data" ? "NO I/Q DATA" : "WAITING");
  el("hal-state").textContent = data.hal === "real" ? "HACKRF" : String(data.hal || "UNKNOWN").toUpperCase();
  el("sync-state").textContent = String(data.sync_state || "unsynced").toUpperCase();
  el("scan-age").textContent = formatAge(data.scan_ts_iso);
  el("scan-number").textContent = data.scan_id == null ? "—" : "#" + data.scan_id;
  el("scan-time").textContent = data.scan_ts_iso ? new Date(data.scan_ts_iso).toLocaleString() : "AWAITING FIRST SWEEP";
  el("updated-at").textContent = "UPDATED " + new Date().toLocaleTimeString();
  el("calibration-notice").hidden = data.calibration_state === "valid";
  const rule = data.occupancy_rule;
  const hasThreshold = Number.isFinite(rule?.threshold_dbfs);
  el("occupied-legend").hidden = !hasThreshold;
  el("occupancy-threshold").textContent = hasThreshold
    ? "Occupied ≥ " + rule.threshold_dbfs.toFixed(1) + " dBFS · sweep median + " + rule.margin_db + " dB"
    : "Awaiting screening threshold";
}
function scheduleRefresh() {
  clearTimeout(refreshTimer);
  if (refreshing) return;
  const interval = Number(el("refresh-interval").value) || 500;
  refreshTimer = setTimeout(refreshSpectrum, Math.max(500, interval));
}
async function refreshSpectrum() {
  refreshing = true;
  try {
    const response = await fetch("/api/spectrum", {
      cache: "no-store",
      signal: AbortSignal.timeout(10000),
    });
    if (!response.ok) throw new Error("HTTP " + response.status);
    const data = await response.json();
    const threshold = data.occupancy_rule?.threshold_dbfs ?? null;
    updateHeader(data);
    if (!chart || data.scan_id == null || data.scan_id !== lastRenderedScanId || threshold !== lastRenderedThreshold) {
      updateChart(data);
      if (data.raw_steps?.length) renderChannels(data);
      else el("channel-table").innerHTML = '<div class="empty">Waiting for I/Q samples from the receiver.</div>';
      lastRenderedScanId = data.scan_id;
      lastRenderedThreshold = threshold;
    }
    recordSweep(data);
    el("refresh-state").hidden = true;
  } catch (error) {
    console.error(error);
    statusLed("error", "SPECTRUM UNAVAILABLE");
    el("refresh-state").textContent = "Retrying at the selected interval";
    el("refresh-state").hidden = false;
  } finally {
    refreshing = false;
    scheduleRefresh();
  }
}
el("refresh-interval").addEventListener("change", scheduleRefresh);
el("vertical-range").addEventListener("change", function () {
  if (chart) chart.setData(chart.data);
});
drawWaterfall();
refreshSpectrum();
</script>
</body>
</html>`;
}

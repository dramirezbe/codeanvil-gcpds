import { getLogger } from "../config/logger.ts";
import type { UpdateMessage } from "../output/client.ts";

const log = getLogger("dashboard.views");

const DB_MIN = -80;
const DB_MAX = -20;

function dbToColor(db: number): string {
  const t = Math.max(0, Math.min(1, (db - DB_MIN) / (DB_MAX - DB_MIN)));
  const r = Math.round(t * 255);
  const b = Math.round((1 - t) * 255);
  return `rgb(${r},0,${b})`;
}

function dbToY(db: number, height: number): number {
  const t = Math.max(0, Math.min(1, (db - DB_MIN) / (DB_MAX - DB_MIN)));
  return height * (1 - t);
}

export class Renderer {
  private spectrumCtx: CanvasRenderingContext2D;
  private waterfallCtx: CanvasRenderingContext2D;
  private channelBody: HTMLTableSectionElement;
  private statusEl: HTMLElement;

  constructor() {
    const specCanvas = document.getElementById("spectrum-canvas") as HTMLCanvasElement;
    const wfCanvas = document.getElementById("waterfall-canvas") as HTMLCanvasElement;
    this.channelBody = document.getElementById("channel-body") as HTMLTableSectionElement;
    this.statusEl = document.getElementById("status") as HTMLElement;

    // Set canvas resolution
    const dpr = window.devicePixelRatio || 1;
    for (const c of [specCanvas, wfCanvas]) {
      const rect = c.getBoundingClientRect();
      c.width = rect.width * dpr;
      c.height = rect.height * dpr;
      const ctx = c.getContext("2d")!;
      ctx.scale(dpr, dpr);
    }

    this.spectrumCtx = specCanvas.getContext("2d")!;
    this.waterfallCtx = wfCanvas.getContext("2d")!;
    log.info("Renderer initialized");
  }

  renderSpectrum(msg: UpdateMessage): void {
    const ctx = this.spectrumCtx;
    const canvas = ctx.canvas;
    const w = canvas.width / (window.devicePixelRatio || 1);
    const h = canvas.height / (window.devicePixelRatio || 1);
    
    ctx.clearRect(0, 0, w, h);
    ctx.fillStyle = "#0f3460";
    ctx.fillRect(0, 0, w, h);

    // Draw grid
    ctx.strokeStyle = "#1a4a7a";
    ctx.lineWidth = 0.5;
    for (let db = DB_MIN; db <= DB_MAX; db += 10) {
      const y = dbToY(db, h);
      ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(w, y); ctx.stroke();
    }

    // Draw channel centres
    const bins = msg.spectrum_dbfs.length; // 853
    for (const ch of msg.channels) {
      const binIdx = Math.round(((ch.f_mhz * 1e6) - (msg.fc_hz - 1e6)) / msg.bin_hz);
      const x = (binIdx / bins) * w;
      ctx.strokeStyle = ch.occupied ? "#4ecca3" : "#2a4a5a";
      ctx.lineWidth = 1;
      ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, h); ctx.stroke();
    }

    // Draw spectrum line
    ctx.strokeStyle = "#e8d44d";
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    for (let i = 0; i < bins; i++) {
      const x = (i / bins) * w;
      const y = dbToY(msg.spectrum_dbfs[i], h);
      if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
    }
    ctx.stroke();

    // Y-axis labels
    ctx.fillStyle = "#7b8794";
    ctx.font = "10px system-ui";
    for (let db = DB_MIN; db <= DB_MAX; db += 20) {
      ctx.fillText(`${db}`, 2, dbToY(db, h) - 2);
    }
  }

  renderWaterfall(waterfallRows: readonly number[][]): void {
    const ctx = this.waterfallCtx;
    const canvas = ctx.canvas;
    const w = canvas.width / (window.devicePixelRatio || 1);
    const h = canvas.height / (window.devicePixelRatio || 1);
    
    ctx.clearRect(0, 0, w, h);
    
    const rowHeight = h / 120;
    for (let r = 0; r < waterfallRows.length; r++) {
      const row = waterfallRows[r];
      const bins = row.length;
      for (let i = 0; i < bins; i++) {
        const x = (i / bins) * w;
        const colW = w / bins + 1;
        ctx.fillStyle = dbToColor(row[i]);
        ctx.fillRect(x, r * rowHeight, colW, rowHeight + 1);
      }
    }
  }

  renderChannels(msg: UpdateMessage): void {
    this.channelBody.innerHTML = "";
    for (let n = 0; n < msg.channels.length; n++) {
      const ch = msg.channels[n];
      const row = document.createElement("tr");
      const statusClass = ch.occupied ? "occupied" : "free";
      const statusText = ch.occupied ? "ON" : "OFF";
      row.innerHTML = `
        <td>${n}</td>
        <td>${ch.f_mhz.toFixed(1)}</td>
        <td class="${statusClass}">${statusText}</td>
        <td>${(ch.occupancy * 100).toFixed(1)}%</td>
      `;
      this.channelBody.appendChild(row);
    }
  }

  setStatus(status: string): void {
    this.statusEl.textContent = status;
  }
}

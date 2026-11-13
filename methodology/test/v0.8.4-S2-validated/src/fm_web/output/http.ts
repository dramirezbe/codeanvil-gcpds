/**
 * HTTP layer — GET/HEAD only, port 8080, four views + alerts + reports.
 * Max 8 concurrent, 64 queued 30 s, then 503 Retry-After:10 (SDD §1.4).
 */
import * as http from "node:http";
import type { DataPort } from "../hal/port.ts";
import {
  buildAlertBarView, buildCatalogView, buildPowerView,
  buildSpectrumView, buildStationsView, buildStatusView,
} from "./views.ts";
import { buildDashboardHtml } from "./ui.ts";
import { MAX_CONCURRENT, MAX_QUEUED, QUEUE_TIMEOUT_S } from "../config/runtime.ts";
import { getLogger } from "../config/logger.ts";

const log = getLogger("fm_web.output.http");
const EVIDENCE_HEADER = "X-Evidence-Label";
const EVIDENCE_VALUE  = "Screening evidence only: not a compliance determination";

export function createServer(port: DataPort): http.Server {
  let active = 0;
  let queued = 0;

  const handle = async (req: http.IncomingMessage, res: http.ServerResponse): Promise<void> => {
    const raw   = req.url ?? "/";
    const url   = raw.split("?")[0];
    const query = Object.fromEntries(new URLSearchParams(raw.includes("?") ? raw.split("?")[1] : ""));

    if (req.method !== "GET" && req.method !== "HEAD") {
      res.writeHead(405, { Allow: "GET, HEAD" }); res.end(); return;
    }

    if (active >= MAX_CONCURRENT) {
      if (queued >= MAX_QUEUED) {
        res.writeHead(503, { "Retry-After": "10", "Content-Type": "application/json" });
        res.end(JSON.stringify({ error: "overloaded" })); return;
      }
      queued++;
      await new Promise<void>((r) => setTimeout(r, QUEUE_TIMEOUT_S * 1000));
      queued--;
    }

    active++;
    res.setHeader(EVIDENCE_HEADER, EVIDENCE_VALUE);

    try {
      // ── UI HTML routes ────────────────────────────────────────────────────
      if (url === "/" || url === "/ui") {
        redirect(res, "/power"); return;
      }
      if (["/power", "/spectrum", "/stations", "/status", "/alerts", "/reports"].includes(url)) {
        res.setHeader("Content-Type", "text/html; charset=utf-8");
        res.writeHead(200);
        if (req.method !== "HEAD") res.write(buildDashboardHtml(url));
        res.end(); return;
      }

      // ── JSON API routes ───────────────────────────────────────────────────
      res.setHeader("Content-Type", "application/json; charset=utf-8");

      if (url === "/api/power" || url === "/api/power-map") {
        const span_h = Number(query["span_h"] ?? "1");
        res.writeHead(200);
        if (req.method !== "HEAD") res.write(JSON.stringify(buildPowerView(await port.getHistory(span_h))));
        res.end(); return;
      }
      if (url === "/api/spectrum" || url === "/api/latest-scan") {
        res.writeHead(200);
        if (req.method !== "HEAD") res.write(JSON.stringify(buildSpectrumView(await port.getSpectrum())));
        res.end(); return;
      }
      if (url === "/api/stations") {
        const span_h = Number(query["span_h"] ?? "24");
        const chs = query["channels"] ? query["channels"].split(",").map(Number).filter(n => n > 0 && n <= 199) : [];
        res.writeHead(200);
        if (req.method !== "HEAD") res.write(JSON.stringify(buildStationsView(await port.getStations(chs, span_h))));
        res.end(); return;
      }
      if (url === "/api/status") {
        res.writeHead(200);
        if (req.method !== "HEAD") res.write(JSON.stringify(buildStatusView(await port.getStatus())));
        res.end(); return;
      }
      if (url === "/api/alerts") {
        res.writeHead(200);
        if (req.method !== "HEAD") res.write(JSON.stringify(buildAlertBarView(await port.getAlerts())));
        res.end(); return;
      }
      if (url === "/api/reports") {
        res.writeHead(200);
        if (req.method !== "HEAD") res.write(JSON.stringify(buildCatalogView(await port.getReportCatalog())));
        res.end(); return;
      }

      // ── Report file download ──────────────────────────────────────────────
      if (url.startsWith("/reports/")) {
        const filePath = url.slice("/reports/".length);
        const data = await port.readReportFile(filePath);
        res.setHeader("Content-Type", "text/csv; charset=utf-8");
        res.setHeader("Content-Disposition", `attachment; filename="${filePath.split("/").pop()}"`);
        res.writeHead(200);
        if (req.method !== "HEAD") res.write(data);
        res.end(); return;
      }

      res.writeHead(404); res.end(JSON.stringify({ error: "not found" }));
    } catch (err) {
      log.error(`handler error: ${err}`);
      res.writeHead(500); res.end(JSON.stringify({ error: "internal" }));
    } finally {
      active--;
    }
  };

  return http.createServer((req, res) => { handle(req, res).catch(() => {}); });
}

function redirect(res: http.ServerResponse, to: string): void {
  res.writeHead(302, { Location: to }); res.end();
}

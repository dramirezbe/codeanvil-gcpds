/** Real DataPort — Unix sockets to other subsystems (VL-2 only). */
import * as net from "node:net";
import * as fs from "node:fs";
import * as path from "node:path";
import type {
  AlertsResponse, CatalogResponse, DataPort,
  HistoryResponse, SpectrumResponse, StationsResponse, StatusResponse,
} from "./port.ts";
import { SOCKET_DIR, REPORT_DIR } from "../config/runtime.ts";
import { getLogger } from "../config/logger.ts";

const log = getLogger("fm_web.hal.real");
const MAX_MSG = 16 * 1024 * 1024;

function unixRequest(sockPath: string, msg: unknown): Promise<unknown> {
  return new Promise((resolve, reject) => {
    const sock = net.createConnection(sockPath);
    sock.setTimeout(5000);
    sock.once("connect", () => {
      const body = Buffer.from(JSON.stringify(msg));
      const hdr = Buffer.alloc(4);
      hdr.writeUInt32BE(body.length, 0);
      sock.write(Buffer.concat([hdr, body]));
    });
    sock.once("data", (chunk: Buffer) => {
      if (chunk.length < 4) { reject(new Error("short header")); sock.destroy(); return; }
      const len = chunk.readUInt32BE(0);
      if (len > MAX_MSG) { reject(new Error("message too large")); sock.destroy(); return; }
      resolve(JSON.parse(chunk.slice(4, 4 + len).toString("utf8")));
      sock.destroy();
    });
    sock.once("error", reject);
    sock.once("timeout", () => { reject(new Error("timeout")); sock.destroy(); });
  });
}

export class RealDataPort implements DataPort {
  async getHistory(span_h = 1): Promise<HistoryResponse> {
    return unixRequest(path.join(SOCKET_DIR, "history.sock"), { query: "history", span_h }) as Promise<HistoryResponse>;
  }
  async getSpectrum(): Promise<SpectrumResponse> {
    return unixRequest(path.join(SOCKET_DIR, "history.sock"), { query: "spectrum" }) as Promise<SpectrumResponse>;
  }
  async getStations(channels: number[] = [], span_h = 24): Promise<StationsResponse> {
    return unixRequest(path.join(SOCKET_DIR, "history.sock"), { query: "stations", channels, span_h }) as Promise<StationsResponse>;
  }
  async getAlerts(): Promise<AlertsResponse> {
    return unixRequest(path.join(SOCKET_DIR, "alerts.sock"), { query: "alerts" }) as Promise<AlertsResponse>;
  }
  async getStatus(): Promise<StatusResponse> {
    return unixRequest(path.join(SOCKET_DIR, "supervisor.sock"), { query: "status" }) as Promise<StatusResponse>;
  }
  async getReportCatalog(): Promise<CatalogResponse> {
    return unixRequest(path.join(SOCKET_DIR, "catalog.sock"), { query: "catalog" }) as Promise<CatalogResponse>;
  }
  async readReportFile(filePath: string): Promise<Buffer> {
    const safe = path.resolve(REPORT_DIR, filePath);
    if (!safe.startsWith(path.resolve(REPORT_DIR))) throw new Error("path traversal");
    return fs.promises.readFile(safe);
  }
  close(): void { log.info("RealDataPort closed"); }
}

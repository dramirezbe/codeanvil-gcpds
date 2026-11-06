import { getLogger } from "../config/logger.ts";

const log = getLogger("dashboard.client");

export interface ChannelMessage {
  f_mhz: number;
  power_dbfs: number;
  occupied: boolean;
  occupancy: number;
}

export interface UpdateMessage {
  v: 1;
  t_capture_end: string;
  fc_hz: number;
  bin_hz: number;
  spectrum_dbfs: number[];
  floor_dbfs: number;
  channels: ChannelMessage[];
}

export type MessageHandler = (msg: UpdateMessage) => void;
export type StatusHandler = (status: string) => void;

export function validateMessage(data: unknown): UpdateMessage | null {
  if (typeof data !== "object" || data === null) return null;
  const obj = data as Record<string, unknown>;
  if (obj.v !== 1) {
    log.warn(`Rejected message: v=${String(obj.v)} !== 1`);
    return null;
  }
  if (typeof obj.t_capture_end !== "string") return null;
  if (typeof obj.fc_hz !== "number") return null;
  if (typeof obj.bin_hz !== "number") return null;
  if (!Array.isArray(obj.spectrum_dbfs) || obj.spectrum_dbfs.length !== 853) return null;
  if (typeof obj.floor_dbfs !== "number") return null;
  if (!Array.isArray(obj.channels) || obj.channels.length !== 10) return null;
  for (const ch of obj.channels) {
    if (typeof ch !== "object" || ch === null) return null;
    const c = ch as Record<string, unknown>;
    if (typeof c.f_mhz !== "number" || typeof c.power_dbfs !== "number" ||
        typeof c.occupied !== "boolean" || typeof c.occupancy !== "number") return null;
  }
  return data as UpdateMessage;
}

export class UpdateClient {
  private ws: WebSocket | null = null;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private handlers: MessageHandler[] = [];
  private statusHandlers: StatusHandler[] = [];

  constructor(private readonly url: string) {}

  onMessage(handler: MessageHandler): void { this.handlers.push(handler); }
  onStatus(handler: StatusHandler): void { this.statusHandlers.push(handler); }

  private setStatus(status: string): void {
    for (const h of this.statusHandlers) h(status);
  }

  connect(): void {
    if (this.ws) return;
    log.info(`Connecting to ${this.url}`);
    this.setStatus("Connecting...");
    
    this.ws = new WebSocket(this.url);
    
    this.ws.onopen = () => {
      log.info("Connected");
      this.setStatus("Connected");
    };
    
    this.ws.onmessage = (event: MessageEvent) => {
      try {
        const parsed: unknown = JSON.parse(event.data as string);
        const msg = validateMessage(parsed);
        if (msg) {
          for (const h of this.handlers) h(msg);
        } else {
          log.warn("Rejected invalid message");
        }
      } catch (e) {
        log.error(`Parse error: ${String(e)}`);
      }
    };
    
    this.ws.onclose = () => {
      log.info("Disconnected, reconnecting in 2s");
      this.setStatus("Disconnected — reconnecting...");
      this.ws = null;
      this.reconnectTimer = setTimeout(() => this.connect(), 2000);
    };
    
    this.ws.onerror = () => {
      log.error("WebSocket error");
      this.ws?.close();
    };
  }

  disconnect(): void {
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
    this.ws?.close();
    this.ws = null;
  }
}

import { getLogger } from "../config/logger.ts";

const log = getLogger("dashboard.waterfall");

const MAX_ROWS = 120;

export class WaterfallBuffer {
  private buffer: number[][] = [];

  push(spectrum: number[]): void {
    this.buffer.unshift(spectrum);
    if (this.buffer.length > MAX_ROWS) {
      this.buffer.length = MAX_ROWS;
    }
  }

  get rows(): readonly number[][] { return this.buffer; }
  get length(): number { return this.buffer.length; }

  clear(): void {
    this.buffer = [];
    log.info("Waterfall buffer cleared");
  }
}

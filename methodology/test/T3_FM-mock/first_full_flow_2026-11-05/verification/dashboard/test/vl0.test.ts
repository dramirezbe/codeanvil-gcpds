/**
 * GV-5 consumer side plus the waterfall ring-buffer check (VL-0).
 */

import { describe, expect, it } from "vitest";

import { validateMessage } from "../../../src/dashboard/output/client.ts";
import { gv5Message } from "./fixtures.ts";
import { WaterfallBuffer } from "../../../src/dashboard/dsp/waterfall.ts";

describe("GV-5 message validation", () => {
  it("accepts the fixed message with n1 and n4 occupied", () => {
    const msg = validateMessage(JSON.parse(JSON.stringify(gv5Message())));
    expect(msg).not.toBeNull();
    expect(msg?.channels).toHaveLength(10);
    expect(msg?.channels[1].occupied).toBe(true);
    expect(msg?.channels[4].occupied).toBe(true);
    expect(msg?.channels[0].occupied).toBe(false);
  });

  it("rejects a copy with v = 2", () => {
    const bad = { ...gv5Message(), v: 2 };
    expect(validateMessage(bad)).toBeNull();
  });

  it("rejects a message missing a field", () => {
    const bad: Record<string, unknown> = { ...gv5Message() };
    delete bad.floor_dbfs;
    expect(validateMessage(bad)).toBeNull();
  });

  it("rejects a wrong spectrum length", () => {
    const bad = { ...gv5Message(), spectrum_dbfs: new Array<number>(10).fill(-60) };
    expect(validateMessage(bad)).toBeNull();
  });
});

describe("waterfall ring buffer", () => {
  it("keeps exactly the last 120 rows, newest first", () => {
    const buf = new WaterfallBuffer();
    for (let i = 0; i < 130; i += 1) {
      buf.push(new Array<number>(853).fill(-80 + i / 10));
    }
    expect(buf.length).toBe(120);
    expect(buf.rows).toHaveLength(120);
    expect(buf.rows[0][0]).toBeCloseTo(-80 + 129 / 10, 5);
    expect(buf.rows[119][0]).toBeCloseTo(-80 + 10 / 10, 5);
  });

  it("holds fewer than 120 rows during the first minute", () => {
    const buf = new WaterfallBuffer();
    buf.push(new Array<number>(853).fill(-60));
    buf.push(new Array<number>(853).fill(-60));
    expect(buf.length).toBe(2);
  });
});

/**
 * VL-1 rendering tests for SVC-002 dashboard.
 *
 * The renderer is exercised against a jsdom DOM with the fixed GV-5 message.
 * VL-1 evidence is claimed at G2, not here.
 */

import { beforeEach, describe, expect, it, vi } from "vitest";

import { Renderer } from "../../../src/dashboard/views/renderer.ts";
import { gv5Message } from "./fixtures.ts";

/** Minimal 2D context: jsdom has no canvas implementation. */
function fakeContext(): CanvasRenderingContext2D {
  return {
    canvas: document.createElement("canvas"),
    clearRect: vi.fn(),
    fillRect: vi.fn(),
    beginPath: vi.fn(),
    moveTo: vi.fn(),
    lineTo: vi.fn(),
    stroke: vi.fn(),
    fillText: vi.fn(),
    scale: vi.fn(),
    set fillStyle(_v: string) {},
    set strokeStyle(_v: string) {},
    set lineWidth(_v: number) {},
    set font(_v: string) {},
  } as unknown as CanvasRenderingContext2D;
}

function buildDom(): void {
  document.body.innerHTML = `
    <canvas id="spectrum-canvas"></canvas>
    <canvas id="waterfall-canvas"></canvas>
    <table><tbody id="channel-body"></tbody></table>
    <div id="status"></div>
  `;
  vi.spyOn(HTMLCanvasElement.prototype, "getContext").mockImplementation(
    () => fakeContext(),
  );
}

describe("UI views", () => {
  beforeEach(() => {
    buildDom();
  });

  it("renders 10 channel rows and marks n1 and n4 occupied", () => {
    const renderer = new Renderer();
    const msg = gv5Message();
    renderer.renderChannels(msg);

    const rows = document.querySelectorAll("#channel-body tr");
    expect(rows).toHaveLength(10);

    const row1 = rows[1] as HTMLTableRowElement;
    const row4 = rows[4] as HTMLTableRowElement;
    const row0 = rows[0] as HTMLTableRowElement;

    expect(row1.textContent).toContain("ON");
    expect(row4.textContent).toContain("ON");
    expect(row0.textContent).toContain("OFF");
  });

  it("shows the occupancy as a percentage", () => {
    const renderer = new Renderer();
    renderer.renderChannels(gv5Message());
    const row1 = document.querySelectorAll("#channel-body tr")[1] as HTMLTableRowElement;
    expect(row1.textContent).toContain("100.0%");
  });

  it("renders the spectrum and waterfall without throwing", () => {
    const renderer = new Renderer();
    const msg = gv5Message();
    expect(() => {
      renderer.renderSpectrum(msg);
      renderer.renderWaterfall([msg.spectrum_dbfs, msg.spectrum_dbfs]);
    }).not.toThrow();
  });

  it("updates the status line", () => {
    const renderer = new Renderer();
    renderer.setStatus("Connected");
    expect(document.getElementById("status")?.textContent).toBe("Connected");
  });
});

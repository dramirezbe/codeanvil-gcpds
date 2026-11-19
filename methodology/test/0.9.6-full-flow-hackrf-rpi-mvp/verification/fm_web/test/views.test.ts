/** VL-0 floor tests for fm_web views layer. */
import { describe, it, expect } from "vitest";
import { buildAlertBarView, buildPowerView, buildStatusView } from "../../../src/fm_web/output/views.ts";
import type { AlertsResponse, HistoryResponse, StatusResponse } from "../../../src/fm_web/hal/port.ts";

const BASE_HISTORY: HistoryResponse = {
  schema: "history.v1",
  data_state: "ok",
  sync_state: "synced",
  history_start_utc_us: 0,
  channels: [],
};

describe("buildPowerView", () => {
  it("returns null power when no bins", () => {
    const history: HistoryResponse = {
      ...BASE_HISTORY,
      channels: [{ channel: 100, freq_hz: 98_000_000, bins: [] }],
    };
    const view = buildPowerView(history);
    // channel with no bins has no latest bin — bins array is empty
    expect(view.channels[0].bins).toHaveLength(0);
  });

  it("returns power and colour when bin present", () => {
    const history: HistoryResponse = {
      ...BASE_HISTORY,
      channels: [{
        channel: 100, freq_hz: 98_000_000,
        bins: [{ ts_iso: "2026-01-01T00:00:00Z", power_dbm: -60.0, withheld_reason: null, occupancy: "Free" }],
      }],
    };
    const view = buildPowerView(history);
    expect(view.channels[0].bins[0].power_dbm).toBe(-60.0);
    expect(view.channels[0].bins[0].colour).toBe("green");
  });

  it("withheld bin gets grey colour", () => {
    const history: HistoryResponse = {
      ...BASE_HISTORY,
      channels: [{
        channel: 1, freq_hz: 87_600_000,
        bins: [{ ts_iso: "2026-01-01T00:00:00Z", power_dbm: null, withheld_reason: "clipped", occupancy: "Uncertain" }],
      }],
    };
    const view = buildPowerView(history);
    expect(view.channels[0].bins[0].colour).toBe("grey");
    expect(view.channels[0].bins[0].power_dbm).toBeNull();
  });

  it("includes evidence label and screening_evidence", () => {
    const view = buildPowerView(BASE_HISTORY);
    expect(view.label).toContain("Screening evidence only");
    expect(view.screening_evidence).toBe(true);
  });

  it("propagates data_state", () => {
    const view = buildPowerView({ ...BASE_HISTORY, data_state: "insufficient_history" });
    expect(view.data_state).toBe("insufficient_history");
  });
});

describe("buildStatusView", () => {
  const BASE_STATUS: StatusResponse = {
    schema: "supervisor_status.v1",
    data_state: "ok",
    sync_state: "synced",
    online: true,
    last_scan_age_s: 2.1,
    noise_floor_drift_db: 0.5,
    overflow_count: 0,
    dropped_frame_count: 0,
    hal: "mock",
    temp_c: 42.0,
    thermal_ok: true,
    tick: 7,
  };

  it("maps all five mandated STK-REQ-044 fields", () => {
    const view = buildStatusView(BASE_STATUS);
    expect(view.online).toBe(true);
    expect(view.last_scan_age_s).toBe(2.1);
    expect(view.noise_floor_drift_db).toBe(0.5);
    expect(view.overflow_count).toBe(0);
    expect(view.dropped_frame_count).toBe(0);
  });

  it("carries screening_evidence", () => {
    expect(buildStatusView(BASE_STATUS).screening_evidence).toBe(true);
  });
});

describe("buildAlertBarView", () => {
  it("counts active alerts and carries screening_evidence", () => {
    const alerts: AlertsResponse = {
      schema: "alerts.v1",
      data_state: "ok",
      sync_state: "synced",
      active: [{ rule: "channel_silent", channels: [100], since_iso: "2026-01-01T00:00:00Z", reason: "silent" }],
      scan_index: 10,
    };
    const view = buildAlertBarView(alerts);
    expect(view.active_count).toBe(1);
    expect(view.alerts[0].rule).toBe("channel_silent");
    expect(view.screening_evidence).toBe(true);
  });
});

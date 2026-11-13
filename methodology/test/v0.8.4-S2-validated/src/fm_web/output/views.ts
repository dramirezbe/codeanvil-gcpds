/**
 * View layer — shapes responses from released values only (SDD §1.4 SUB-004/views).
 *
 * Release rule (STK-REQ-045): only released values are shown.
 * Withheld → null + withheld_reason + flags. Never 0, never the last value.
 * Fixed colour encoding: Occupied=red, Free=green, Uncertain=yellow.
 * Every response carries screening_evidence:true and the evidence label (STK-REQ-032).
 */
import type {
  AlertsResponse, CatalogResponse, HistoryResponse,
  SpectrumResponse, StationsResponse, StatusResponse,
} from "../hal/port.ts";

const LABEL = "Screening evidence only: not a compliance determination";

function base() {
  return { screening_evidence: true as const, label: LABEL };
}

// ── /power ───────────────────────────────────────────────────────────────────

export interface PowerChannelBin {
  ts_iso: string;
  power_dbm: number | null;
  withheld_reason: string | null;
  occupancy: string | null;
  colour: "red" | "green" | "yellow" | "grey";
}

export interface PowerChannel {
  channel: number;
  freq_hz: number;
  bins: PowerChannelBin[];
}

export interface PowerView {
  label: string;
  screening_evidence: true;
  data_state: string;
  sync_state: string;
  history_start_utc_us: number | null;
  channels: PowerChannel[];
}

export function buildPowerView(r: HistoryResponse): PowerView {
  return {
    ...base(),
    data_state: r.data_state,
    sync_state: r.sync_state,
    history_start_utc_us: r.history_start_utc_us,
    channels: r.channels.map((ch) => ({
      channel: ch.channel,
      freq_hz: ch.freq_hz,
      bins: ch.bins.map((b) => ({
        ts_iso: b.ts_iso,
        power_dbm: b.power_dbm,
        withheld_reason: b.withheld_reason,
        occupancy: b.occupancy,
        colour: occColour(b.occupancy, b.withheld_reason),
      })),
    })),
  };
}

// ── /spectrum ─────────────────────────────────────────────────────────────────

export interface SpectrumPointView {
  channel: number;
  freq_hz: number;
  power_dbm: number | null;
  withheld_reason: string | null;
  occupancy: string;
  dc_adjacent: boolean;
  colour: "red" | "green" | "yellow" | "grey";
}

export interface SpectrumView {
  label: string;
  screening_evidence: true;
  data_state: string;
  sync_state: string;
  scan_id: number | null;
  scan_ts_iso: string | null;
  raw_steps: import("../hal/port.ts").SpectrumStep[];
  points: SpectrumPointView[];
}

export function buildSpectrumView(r: SpectrumResponse): SpectrumView {
  return {
    ...base(),
    data_state: r.data_state,
    sync_state: r.sync_state,
    scan_id: r.scan_id,
    scan_ts_iso: r.scan_ts_iso,
    raw_steps: r.raw_steps,
    points: r.points.map((p) => ({
      channel: p.channel,
      freq_hz: p.freq_hz,
      power_dbm: p.power_dbm,
      withheld_reason: p.withheld_reason,
      occupancy: p.occupancy,
      dc_adjacent: p.dc_adjacent,
      colour: occColour(p.occupancy, p.withheld_reason),
    })),
  };
}

// ── /stations ─────────────────────────────────────────────────────────────────

export interface StationBinView {
  interval_start_iso: string;
  duty_cycle_pct: number | null;
  uncertain_pct: number | null;
}

export interface StationView {
  channel: number;
  freq_hz: number;
  callsign: string | null;
  latest_power_dbm: number | null;
  bins: StationBinView[];
}

export interface StationsView {
  label: string;
  screening_evidence: true;
  data_state: string;
  sync_state: string;
  span_h: number;
  stations: StationView[];
}

export function buildStationsView(r: StationsResponse): StationsView {
  return {
    ...base(),
    data_state: r.data_state,
    sync_state: r.sync_state,
    span_h: r.span_h,
    stations: r.stations.map((s) => ({
      channel: s.channel,
      freq_hz: s.freq_hz,
      callsign: s.callsign,
      latest_power_dbm: s.latest_power_dbm,
      bins: s.bins.map((b) => ({
        interval_start_iso: b.interval_start_iso,
        duty_cycle_pct: b.duty_cycle_pct,
        uncertain_pct: b.uncertain_pct,
      })),
    })),
  };
}

// ── /status ───────────────────────────────────────────────────────────────────

export interface StatusView {
  label: string;
  screening_evidence: true;
  data_state: string;
  sync_state: string;
  /** STK-REQ-044 §1 */ online: boolean;
  /** STK-REQ-044 §2 */ last_scan_age_s: number | null;
  /** STK-REQ-044 §3 */ noise_floor_drift_db: number | null;
  /** STK-REQ-044 §4 */ overflow_count: number;
  /** STK-REQ-044 §5 */ dropped_frame_count: number;
  hal: string;
  temp_c: number | null;
  thermal_ok: boolean;
  tick: number;
}

export function buildStatusView(r: StatusResponse): StatusView {
  return {
    ...base(),
    data_state: r.data_state,
    sync_state: r.sync_state,
    online: r.online,
    last_scan_age_s: r.last_scan_age_s,
    noise_floor_drift_db: r.noise_floor_drift_db,
    overflow_count: r.overflow_count,
    dropped_frame_count: r.dropped_frame_count,
    hal: r.hal,
    temp_c: r.temp_c,
    thermal_ok: r.thermal_ok,
    tick: r.tick,
  };
}

// ── /alerts ───────────────────────────────────────────────────────────────────

export interface AlertBarView {
  label: string;
  screening_evidence: true;
  data_state: string;
  sync_state: string;
  active_count: number;
  alerts: { rule: string; channels: number[]; since_iso: string; reason: string }[];
}

export function buildAlertBarView(r: AlertsResponse): AlertBarView {
  return {
    ...base(),
    data_state: r.data_state,
    sync_state: r.sync_state,
    active_count: r.active.length,
    alerts: r.active.map((a) => ({ rule: a.rule, channels: a.channels, since_iso: a.since_iso, reason: a.reason })),
  };
}

// ── /reports ──────────────────────────────────────────────────────────────────

export interface CatalogView {
  label: string;
  screening_evidence: true;
  data_state: string;
  runs: { run_id: string; started_iso: string; segments: number; interrupted: boolean; size_mb: number | null }[];
}

export function buildCatalogView(r: CatalogResponse): CatalogView {
  return { ...base(), data_state: r.data_state, runs: r.runs };
}

// ── helpers ───────────────────────────────────────────────────────────────────

function occColour(occ: string | null, withheld: string | null): "red" | "green" | "yellow" | "grey" {
  if (withheld && withheld !== "none") return "grey";
  if (occ === "Occupied") return "red";
  if (occ === "Free") return "green";
  return "yellow"; // Uncertain or null
}

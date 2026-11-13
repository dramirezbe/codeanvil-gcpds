/** HAL port interfaces for fm_web (SDD §1.4 SUB-004). */

export interface BinRecord {
  ts_iso: string;
  power_dbm: number | null;
  withheld_reason: string | null;
  occupancy: "Occupied" | "Free" | "Uncertain" | null;
}

export interface ChannelHistory {
  channel: number;
  freq_hz: number;
  bins: BinRecord[];
}

export interface HistoryResponse {
  schema: "history.v1";
  data_state: "ok" | "no_data" | "insufficient_history" | "unavailable";
  sync_state: "synced" | "unsynced" | "stepped";
  history_start_utc_us: number | null;
  channels: ChannelHistory[];
}

export interface SpectrumPoint {
  channel: number;
  freq_hz: number;
  power_dbm: number | null;
  withheld_reason: string | null;
  occupancy: "Occupied" | "Free" | "Uncertain";
  dc_adjacent: boolean;
}

/** One step of the raw 819-point FFT spectrum (SDD §3.2 spectrum_snapshot). */
export interface SpectrumStep {
  step: number;
  first_frequency_hz: number;
  point_spacing_hz: number;
  points_dbm: (number | null)[];  // 819 values; null when withheld
  withheld_reason: string | null;
}

export interface SpectrumResponse {
  schema: "spectrum.v1";
  data_state: "ok" | "no_data" | "unavailable";
  sync_state: "synced" | "unsynced" | "stepped";
  scan_id: number | null;
  scan_ts_iso: string | null;
  /** 199-channel summary for occupancy markers */
  points: SpectrumPoint[];
  /** 3 × 819 raw FFT points (SDD spectrum_snapshot) */
  raw_steps: SpectrumStep[];
}

export interface DutyCycleBin {
  interval_start_iso: string;
  duty_cycle_pct: number | null;
  uncertain_pct: number | null;
}

export interface StationHistory {
  channel: number;
  freq_hz: number;
  callsign: string | null;
  bins: DutyCycleBin[];
  latest_power_dbm: number | null;
}

export interface StationsResponse {
  schema: "stations.v1";
  data_state: "ok" | "no_data" | "insufficient_history" | "unavailable";
  sync_state: "synced" | "unsynced" | "stepped";
  span_h: number;
  stations: StationHistory[];
}

export interface ActiveAlert {
  rule: string;
  channels: number[];
  since_iso: string;
  reason: string;
}

export interface AlertsResponse {
  schema: "alerts.v1";
  data_state: "ok" | "unavailable";
  sync_state: "synced" | "unsynced" | "stepped";
  active: ActiveAlert[];
  scan_index: number;
}

/** Exactly the five fields mandated by STK-REQ-044 / SYS-WEB-001. */
export interface StatusResponse {
  schema: "supervisor_status.v1";
  data_state: "ok" | "unavailable";
  sync_state: "synced" | "unsynced" | "stepped";
  /** STK-REQ-044 field 1: online state */
  online: boolean;
  /** STK-REQ-044 field 2: age of last scan in seconds */
  last_scan_age_s: number | null;
  /** STK-REQ-044 field 3: noise-floor drift in dB over 24 h */
  noise_floor_drift_db: number | null;
  /** STK-REQ-044 field 4: overflow count */
  overflow_count: number;
  /** STK-REQ-044 field 5: dropped-frame count */
  dropped_frame_count: number;
  /** Extra context fields (not mandated but useful) */
  hal: string;
  temp_c: number | null;
  thermal_ok: boolean;
  tick: number;
}

export interface RunEntry {
  run_id: string;
  started_iso: string;
  segments: number;
  interrupted: boolean;
  size_mb: number | null;
}

export interface CatalogResponse {
  schema: "report_catalog.v1";
  data_state: "ok" | "unavailable";
  runs: RunEntry[];
}

export interface DataPort {
  getHistory(span_h?: number): Promise<HistoryResponse>;
  getSpectrum(): Promise<SpectrumResponse>;
  getStations(channels?: number[], span_h?: number): Promise<StationsResponse>;
  getAlerts(): Promise<AlertsResponse>;
  getStatus(): Promise<StatusResponse>;
  getReportCatalog(): Promise<CatalogResponse>;
  readReportFile(path: string): Promise<Buffer>;
  close(): void;
}

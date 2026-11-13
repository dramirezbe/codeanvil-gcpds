/** Mock DataPort — synthesises all data in memory, no sockets needed. */
import type {
  AlertsResponse, CatalogResponse, DataPort,
  HistoryResponse, SpectrumResponse, StationsResponse, StatusResponse,
} from "./port.ts";
import { getLogger } from "../config/logger.ts";

const log = getLogger("fm_web.hal.mock");

// 199 FM channels: 87.6–107.5 MHz, 100 kHz spacing
const CH_COUNT = 199;
const BASE_HZ = 87_600_000;

// Simulated stations (channel → callsign, typical Colombian FM)
const STATIONS: Record<number, string> = {
  15: "HJxx 88.9", 25: "HJCK 89.9", 40: "UN Radio 91.9",
  55: "RCN Bogotá 93.9", 70: "Olímpica 95.9", 85: "Blu Radio 96.9",
  100: "La FM 98.9", 115: "Caracol 100.4", 130: "W Radio 102.9",
  145: "La X 104.4", 160: "Oxígeno 105.9", 175: "Vibra 107.3", 190: "Tropicana 107.3",
};

function freqHz(ch: number): number {
  return BASE_HZ + (ch - 1) * 100_000;
}

function stationPower(ch: number, t: number): number {
  // Occupied channel: −55 to −65 dBm with slow oscillation
  return -60 + Math.sin(t * 0.001 + ch * 0.7) * 5;
}

function noisePower(ch: number, t: number): number {
  // Noise floor: −105 to −110 dBm
  return -107 + Math.sin(t * 0.0005 + ch * 0.3) * 2;
}

function isoNow(): string { return new Date().toISOString(); }

function binTs(offsetMinutes: number): string {
  return new Date(Date.now() - offsetMinutes * 60_000).toISOString();
}

export class MockDataPort implements DataPort {
  private _tick = 0;
  private _startMs = Date.now();

  async getHistory(_span_h = 1): Promise<HistoryResponse> {
    const now = Date.now();
    const BINS = 10; // 10 one-minute bins
    const channels = Array.from({ length: CH_COUNT }, (_, i) => {
      const ch = i + 1;
      const isStation = ch in STATIONS;
      const bins = Array.from({ length: BINS }, (_, b) => {
        const t = now - (BINS - b) * 60_000;
        const power = isStation ? stationPower(ch, t) : noisePower(ch, t);
        const occ: "Occupied" | "Free" = isStation ? "Occupied" : "Free";
        return { ts_iso: new Date(t).toISOString(), power_dbm: power, withheld_reason: null, occupancy: occ };
      });
      return { channel: ch, freq_hz: freqHz(ch), bins };
    });
    return { schema: "history.v1", data_state: "ok", sync_state: "synced", history_start_utc_us: (now - BINS * 60_000) * 1000, channels };
  }

  async getSpectrum(): Promise<SpectrumResponse> {
    const now = Date.now();
    const points = Array.from({ length: CH_COUNT }, (_, i) => {
      const ch = i + 1;
      const isStation = ch in STATIONS;
      const power = isStation ? stationPower(ch, now) : noisePower(ch, now);
      return {
        channel: ch, freq_hz: freqHz(ch), power_dbm: power, withheld_reason: null,
        occupancy: (isStation ? "Occupied" : "Free") as "Occupied" | "Free" | "Uncertain",
        dc_adjacent: ch === 67 || ch === 133,
      };
    });

    // 3 steps × 819 raw FFT points at 9765.625 Hz spacing (SDD spectrum_snapshot)
    // Step centres: 90.25, 97.75, 105.25 MHz; first_freq = centre - 819/2 * spacing
    const SPACING = 9_765.625;
    const STEP_CENTRES = [90_250_000, 97_750_000, 105_250_000];
    const raw_steps = STEP_CENTRES.map((centre, si) => {
      const first = centre - Math.floor(819 / 2) * SPACING;
      const pts = Array.from({ length: 819 }, (_, bi) => {
        const f = first + bi * SPACING;
        // Find nearest station channel
        const nearestCh = Math.round((f - BASE_HZ) / 100_000) + 1;
        let pwr = noisePower(nearestCh, now);
        // Add station peaks as Gaussian bumps
        for (const [ch, _] of Object.entries(STATIONS)) {
          const stCh = Number(ch);
          const stF = freqHz(stCh);
          const dist = (f - stF) / 100_000; // in channel widths
          // FM signal: wider bump (~0.5 channel wide at −3dB)
          const bump = stationPower(stCh, now) + 10 * Math.log10(Math.exp(-dist * dist * 8));
          if (bump > pwr) pwr = bump;
        }
        // DC bin suppression at step centre
        const dcDist = Math.abs(f - centre);
        if (dcDist < SPACING * 2) pwr = Math.max(pwr - 20, -130);
        return Math.max(-130, Math.min(-20, pwr));
      });
      return { step: si + 1, first_frequency_hz: first, point_spacing_hz: SPACING, points_dbm: pts, withheld_reason: null };
    });

    return { schema: "spectrum.v1", data_state: "ok", sync_state: "synced", scan_id: this._tick, scan_ts_iso: isoNow(), points, raw_steps };
  }

  async getStations(channels?: number[], span_h = 24): Promise<StationsResponse> {
    const selected = channels?.length ? channels : Object.keys(STATIONS).map(Number).slice(0, 5);
    const BINS = Math.min(span_h * 6, 60); // one bin per 10 min, max 60
    const now = Date.now();
    const stations = selected.map((ch) => {
      const isStation = ch in STATIONS;
      const bins = Array.from({ length: BINS }, (_, b) => {
        const t = now - (BINS - b) * 10 * 60_000;
        const dc = isStation ? 85 + Math.sin(t * 0.0003 + ch) * 10 : 2 + Math.random() * 3;
        return { interval_start_iso: new Date(t).toISOString(), duty_cycle_pct: parseFloat(dc.toFixed(1)), uncertain_pct: 2.0 };
      });
      return { channel: ch, freq_hz: freqHz(ch), callsign: STATIONS[ch] ?? null, bins, latest_power_dbm: isStation ? stationPower(ch, now) : noisePower(ch, now) };
    });
    return { schema: "stations.v1", data_state: "ok", sync_state: "synced", span_h, stations };
  }

  async getAlerts(): Promise<AlertsResponse> {
    this._tick++;
    return {
      schema: "alerts.v1", data_state: "ok", sync_state: "synced", scan_index: this._tick,
      active: [
        { rule: "channel_silent", channels: [160], since_iso: new Date(Date.now() - 3600_000).toISOString(), reason: "channel 160 silent for 10 scans" },
        { rule: "calibration_expiring", channels: [], since_iso: new Date(Date.now() - 7200_000).toISOString(), reason: "calibration expiring within margin" },
      ],
    };
  }

  async getStatus(): Promise<StatusResponse> {
    const uptimeS = (Date.now() - this._startMs) / 1000;
    return {
      schema: "supervisor_status.v1", data_state: "ok", sync_state: "synced",
      online: true,
      last_scan_age_s: (uptimeS % 6).toFixed(1) as unknown as number,
      noise_floor_drift_db: 1.3,
      overflow_count: 0,
      dropped_frame_count: 0,
      hal: "mock", temp_c: 42.5, thermal_ok: true, tick: this._tick,
    };
  }

  async getReportCatalog(): Promise<CatalogResponse> {
    return {
      schema: "report_catalog.v1", data_state: "ok",
      runs: [
        { run_id: "RUN-20261113-001", started_iso: "2026-11-13T00:00:00Z", segments: 24, interrupted: false, size_mb: 599 },
        { run_id: "RUN-20261112-001", started_iso: "2026-11-12T00:00:00Z", segments: 24, interrupted: false, size_mb: 597 },
      ],
    };
  }

  async readReportFile(_path: string): Promise<Buffer> { return Buffer.alloc(0); }
  close(): void { log.info("MockDataPort closed"); }
}

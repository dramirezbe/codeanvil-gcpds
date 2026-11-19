export type Project = { name: string; path: string; id?: string }

export type Cycle = {
  name: string
  active: boolean
  closed: boolean
  superseded_by?: string | null
  draft: boolean
  suspended: boolean
}

export type Report = {
  id: string
  iteration: number | null
  hitl: string | null
  based_on?: [string, number] | null
  stale_reason?: string | null
  state: string
  verdict?: string | null
}

export type Artifact = {
  path: string
  label: string
  kind: 'report' | 'gt' | 'design' | 'test_run' | 'prototype' | 'deviation' | 'test_log'
  cycle?: string
  exists: boolean
  working_copy?: boolean
  graph_theme?: 'dark' | 'light'
}

export type TelemetrySample = {
  timestamp?: string
  monotonic_s?: number
  process?: Record<string, unknown>
  system?: Record<string, unknown>
  temperature_c?: unknown
  counters?: Record<string, unknown>
}

export type TelemetryStream = {
  path: string
  run_id: string
  samples: TelemetrySample[]
  unavailable_signals: { signal: string; reasons: string[] }[]
  sample_count: number
  truncated_tail: boolean
  truncated_count: boolean
  error: string | null
}

export type MachineMeasurement = {
  path: string
  valid_v2: boolean
  error?: string
  record: {
    schema_version?: number
    cycle?: string
    stage?: 'S3' | 'G3'
    iteration?: number
    run_id?: string
    target?: string
    command?: string
    started_at?: string
    finished_at?: string
    exit_code?: number
    error?: string
    measurements?: {
      requirement_id?: string
      metric?: string
      value?: number | string | boolean
      unit?: string
      criterion?: string
      result?: 'pass' | 'fail' | 'inconclusive'
    }[]
  }
}

export type WorkspaceEvidence = {
  cycle: string | null
  telemetry: TelemetryStream[]
  measurements: MachineMeasurement[]
  test_logs: { path: string; label: string; size_bytes: number }[]
  vl2: {
    statement: string
    prototype_current: boolean
    freshness: string
    items: { scope: string; id: string; level: string; environment: string; command: string; result: string; telemetry: string }[]
    manual_telemetry: Record<string, string>[]
  }
}

export type Overview = {
  project: Project
  active_cycle: string | null
  selected_cycle: string | null
  cycles: Cycle[]
  reports: Report[]
  completion: { passed: number; total: number; complete: boolean; reason: string }
  synthetic_fixture: boolean
  artifacts: Artifact[]
}

export type ArtifactDocument = {
  path: string
  name: string
  content: string
  format: 'markdown' | 'html' | 'text' | 'json'
  iterations: { number: number; hitl: string | null }[]
  selected_iteration?: number | null
}

export async function request<T>(url: string, signal?: AbortSignal): Promise<T> {
  const response = await fetch(url, { signal })
  const body = await response.json()
  if (!response.ok) {
    throw new Error(typeof body.detail === 'string' ? body.detail : `Request failed (${response.status})`)
  }
  return body as T
}

export function workspaceUrl(endpoint: string, projectPath: string, extra: Record<string, string> = {}) {
  const query = new URLSearchParams({ project_path: projectPath, ...extra })
  return `/api/workspace/${endpoint}?${query}`
}

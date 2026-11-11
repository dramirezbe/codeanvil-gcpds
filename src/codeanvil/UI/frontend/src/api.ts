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
  kind: 'report' | 'gt' | 'design' | 'test_run' | 'prototype' | 'deviation'
  cycle?: string
  exists: boolean
  working_copy?: boolean
  graph_theme?: 'dark' | 'light'
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

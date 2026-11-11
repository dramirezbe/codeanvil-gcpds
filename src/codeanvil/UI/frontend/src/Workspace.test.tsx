import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { ArtifactViewer } from './ArtifactViewer'
import { Workspace } from './Workspace'
import { type Artifact, type ArtifactDocument, type Overview } from './api'

const project = { id: 'sample', name: 'Sample project', path: '/projects/sample' }
const reportPath = '.codeanvil/report/01_demo/S0.md'
const reportArtifact: Artifact = { path: reportPath, label: 'S0 report', kind: 'report', cycle: '01_demo', exists: true }
const overview: Overview = {
  project, active_cycle: '01_demo', selected_cycle: '01_demo',
  cycles: [{ name: '01_demo', active: true, closed: false, draft: false, suspended: false }],
  reports: [
    { id: 'S0', iteration: 1, hitl: 'PASS', state: 'delivered' },
    { id: 'G0', iteration: 1, hitl: 'PASS', state: 'PASS', based_on: ['S0', 1] },
    ...['S1', 'G1', 'S2', 'G2'].map(id => ({ id, iteration: null, hitl: null, state: 'missing' })),
  ],
  completion: { passed: 2, total: 6, complete: false, reason: 'G2 must pass before completion.' },
  synthetic_fixture: true,
  artifacts: [reportArtifact],
}

function response(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } })
}

describe('Workspace', () => {
  it('uses server state and keeps synthetic progress distinct from human approval', async () => {
    const state: Overview = {
      ...overview,
      cycles: [{ ...overview.cycles[0], draft: true, suspended: true }],
      reports: [{ ...overview.reports[0], stale_reason: 'G0 was reworked' }, ...overview.reports.slice(1)],
    }
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(response(state)))
    render(<Workspace project={project} active="Overview" onSetActive={vi.fn()} />)
    expect(await screen.findByText('Synthetic UI fixture')).toBeInTheDocument()
    expect(screen.getByText('DRAFT')).toBeInTheDocument()
    expect(screen.getByText('Suspended by RFD')).toBeInTheDocument()
    expect(screen.getAllByText('STALE')).toHaveLength(2)
    expect(screen.getByText('G2 must pass before completion.')).toBeInTheDocument()
    expect(screen.getAllByText('Not started')).toHaveLength(8)
  })

  it('changes cycles without changing active-cycle identity or retaining the previous document', async () => {
    const user = userEvent.setup()
    const fetcher = vi.fn(async (url: string) => {
      const query = new URL(url, 'http://localhost').searchParams
      const second = query.get('cycle') === '02_next' || query.get('path')?.includes('02_next')
      if (url.includes('/overview?')) return response({
        ...overview,
        selected_cycle: second ? '02_next' : '01_demo',
        cycles: [...overview.cycles, { name: '02_next', active: false, closed: false, draft: false, suspended: false }],
        artifacts: [{ ...reportArtifact, path: second ? reportPath.replace('01_demo', '02_next') : reportPath }],
      })
      return response({ path: query.get('path'), name: 'S0.md', format: 'markdown', iterations: [], content: second ? '# Second cycle document' : '# First cycle document' })
    })
    vi.stubGlobal('fetch', fetcher)
    render(<Workspace project={project} active="Reports" onSetActive={vi.fn()} />)
    expect(await screen.findByRole('heading', { name: 'First cycle document' })).toBeInTheDocument()
    await user.selectOptions(screen.getByRole('combobox', { name: 'Cycle' }), '02_next')
    expect(await screen.findByRole('heading', { name: 'Second cycle document' })).toBeInTheDocument()
    expect(screen.queryByRole('heading', { name: 'First cycle document' })).not.toBeInTheDocument()
    expect(screen.getByRole('option', { name: '01_demo · active' })).toBeInTheDocument()
    expect(fetcher.mock.calls.some(([url]) => url.includes('cycle=02_next'))).toBe(true)
  })

  it('shows missing artifacts and load failures as separate states', async () => {
    const missing: Overview = { ...overview, artifacts: [{ path: '.codeanvil/design/SDD.md', label: 'Software design', kind: 'design', exists: false, working_copy: true }] }
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(response(missing)))
    const view = render(<Workspace project={project} active="Design" onSetActive={vi.fn()} />)
    expect(await screen.findByRole('heading', { name: 'Not produced yet' })).toBeInTheDocument()
    expect(screen.getByText('Working copy · shared across cycles')).toBeInTheDocument()
    view.unmount()
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(response({ detail: 'Manifest is malformed' }, 400)))
    render(<Workspace project={project} active="Overview" onSetActive={vi.fn()} />)
    expect(await screen.findByRole('alert')).toHaveTextContent('Manifest is malformed')
  })
})

describe('ArtifactViewer', () => {
  it('renders GFM without executing HTML or loading external images', async () => {
    const document: ArtifactDocument = {
      path: reportPath, name: 'S0.md', format: 'markdown', iterations: [],
      content: '# Requirements\n\n| Field | Value |\n|---|---|\n| HITL | PASS |\n\n[Unsafe](javascript:alert%281%29)\n\n<script>window.compromised=true</script>\n\n![tracking](https://example.com/pixel.png)',
    }
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(response(document)))
    const { container } = render(<ArtifactViewer artifact={reportArtifact} projectPath={project.path} />)
    expect(await screen.findByRole('heading', { name: 'Requirements' })).toBeInTheDocument()
    expect(screen.getByRole('table')).toHaveTextContent('HITLPASS')
    expect(container.querySelector('script')).toBeNull()
    expect(container.querySelector('img')).toBeNull()
    expect(screen.getByText('Unsafe').getAttribute('href') || '').not.toMatch(/^javascript:/)
    expect(screen.getByText(/external images are not loaded automatically/)).toBeInTheDocument()
  })

  it('requests a chosen report iteration and renders its returned content', async () => {
    const user = userEvent.setup()
    const fetcher = vi.fn(async (url: string) => response({
      path: reportPath, name: 'S0.md', format: 'markdown',
      iterations: [{ number: 1, hitl: 'FEEDBACK' }, { number: 2, hitl: 'PASS' }],
      content: url.includes('iteration=1') ? '# Selected first iteration' : '# Complete report',
    }))
    vi.stubGlobal('fetch', fetcher)
    render(<ArtifactViewer artifact={reportArtifact} projectPath={project.path} />)
    expect(await screen.findByRole('heading', { name: 'Complete report' })).toBeInTheDocument()
    await user.selectOptions(screen.getByRole('combobox', { name: 'Report iteration' }), '1')
    expect(await screen.findByRole('heading', { name: 'Selected first iteration' })).toBeInTheDocument()
    expect(screen.queryByRole('heading', { name: 'Complete report' })).not.toBeInTheDocument()
    expect(fetcher.mock.calls.at(-1)?.[0]).toContain('iteration=1')
  })

  it('confines interactive graph HTML to a sandbox without same-origin permission', async () => {
    const artifact: Artifact = { path: '.codeanvil/design/dependency_graph.html', label: 'Dependency graph', kind: 'design', exists: true }
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(response({ name: 'dependency_graph.html', path: artifact.path, format: 'html', content: '<h1>Graph</h1><script>draw()</script>', iterations: [] })))
    render(<ArtifactViewer artifact={artifact} projectPath={project.path} />)
    await waitFor(() => expect(screen.getByTitle('Dependency graph')).toHaveAttribute('sandbox', 'allow-scripts'))
    expect(screen.getByTitle('Dependency graph')).toHaveAttribute('srcdoc', '<h1>Graph</h1><script>draw()</script>')
  })

  it('does not replace a new artifact with a late previous response', async () => {
    let resolveOld!: (value: Response) => void
    const pending = new Promise<Response>(resolve => { resolveOld = resolve })
    vi.stubGlobal('fetch', vi.fn((url: string) => url.includes('S0.md') ? pending : Promise.resolve(response({ path: 'new.md', name: 'new.md', content: '# Current artifact', format: 'markdown', iterations: [] }))))
    const view = render(<ArtifactViewer artifact={reportArtifact} projectPath={project.path} />)
    view.rerender(<ArtifactViewer artifact={{ ...reportArtifact, path: '.codeanvil/report/01_demo/G0.md' }} projectPath={project.path} />)
    expect(await screen.findByRole('heading', { name: 'Current artifact' })).toBeInTheDocument()
    resolveOld(response({ path: reportPath, name: 'S0.md', content: '# Old artifact', format: 'markdown', iterations: [] }))
    await waitFor(() => expect(screen.queryByRole('heading', { name: 'Old artifact' })).not.toBeInTheDocument())
  })
})

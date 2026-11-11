import { useEffect, useState } from 'react'
import { ArrowUpRight, FileText, RefreshCw, ShieldCheck } from 'lucide-react'
import { ArtifactViewer } from './ArtifactViewer'
import { type Artifact, type Overview, type Project, type Report, request, workspaceUrl } from './api'

const stages = [
  ['S0', 'Normalize'], ['G0', 'GT Gate'], ['S1', 'Design'],
  ['G1', 'Review'], ['S2', 'Implement'], ['G2', 'Verify'],
]

export function ReportBadge({ report }: { report: Report }) {
  const label = report.stale_reason ? 'STALE' : report.state
  const complete = label === 'PASS' || label === 'delivered'
  return <span className={`tag ${complete ? 'tag-pass' : label === 'FEEDBACK' || label === 'STALE' ? 'tag-warning' : 'tag-muted'}`}
    title={report.stale_reason || undefined}>{label === 'missing' ? 'Not started' : label}</span>
}

export function Workspace({ project, active, onSetActive, revision = 0 }: {
  project: Project
  active: string
  onSetActive: (view: string) => void
  revision?: number
}) {
  const [overview, setOverview] = useState<Overview | null>(null)
  const [cycle, setCycle] = useState<string | undefined>()
  const [refresh, setRefresh] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [selection, setSelection] = useState<{ path: string; view: string } | null>(null)

  useEffect(() => {
    const controller = new AbortController()
    setOverview(null)
    setLoading(true)
    setError('')
    request<Overview>(workspaceUrl('overview', project.path, cycle ? { cycle } : {}), controller.signal)
      .then(value => { if (!controller.signal.aborted) setOverview(value) })
      .catch(reason => { if (!controller.signal.aborted) setError(reason.message) })
      .finally(() => { if (!controller.signal.aborted) setLoading(false) })
    return () => controller.abort()
  }, [project.path, cycle, refresh, revision])

  const currentCycle = overview?.cycles.find(item => item.name === overview.selected_cycle)
  const artifacts = overview?.artifacts.filter(artifact => {
    if (active === 'Ground truth') return artifact.kind === 'gt'
    if (active === 'Design') return artifact.kind === 'design'
    if (active === 'Reports') return artifact.kind === 'report' || artifact.kind === 'deviation'
    if (active === 'Verification') return artifact.kind === 'test_run' || artifact.kind === 'prototype'
    return false
  }) || []
  const selectedArtifact = artifacts.find(item => selection?.view === active && item.path === selection.path)
    || artifacts.find(item => item.exists) || artifacts[0] || null

  function openArtifact(artifact: Artifact) {
    const view = artifact.kind === 'test_run' || artifact.kind === 'prototype' ? 'Verification' : 'Reports'
    setSelection({ path: artifact.path, view })
    onSetActive(view)
  }

  return <div className="workspace workspace-canvas">
    <div className="page-head">
      <div className="page-title">
        <div className="eyebrow"><span className="eyebrow-line" /> V-SIL METHOD</div>
        <h1>{active === 'Overview' ? 'Project overview' : active}</h1>
        <p className="lede" title={project.path}>{project.name} · {project.path}</p>
      </div>
      <div className="workspace-controls">
        <label className="cycle-control"><span>Cycle</span>
          <select aria-label="Cycle" value={overview?.selected_cycle || ''} disabled={!overview?.cycles.length || loading}
            onChange={event => { setSelection(null); setCycle(event.target.value) }}>
            {!overview?.cycles.length && <option value="">No cycle yet</option>}
            {overview?.cycles.map(item => <option key={item.name} value={item.name}>
              {item.name}{item.active ? ' · active' : ''}{item.closed ? ' · closed' : ''}
            </option>)}
          </select>
        </label>
        <button className="secondary-button" onClick={() => setRefresh(value => value + 1)} disabled={loading}>
          <RefreshCw size={14} /> Refresh
        </button>
      </div>
    </div>

    {overview?.synthetic_fixture && <div className="fixture-banner" role="note">
      <strong>Synthetic UI fixture</strong><span>Progress and human decisions are simulated; this is not a genuine gate approval.</span>
    </div>}
    {currentCycle && (currentCycle.draft || currentCycle.suspended || currentCycle.closed) && <div className="cycle-notice" role="status">
      {currentCycle.draft && <span><b>DRAFT</b> · Open items are being resolved without new report iterations.</span>}
      {currentCycle.suspended && <span><b>Suspended by RFD</b> · The deviation needs an author decision.</span>}
      {currentCycle.closed && <span><b>Closed cycle</b> · Continue in {currentCycle.superseded_by || 'its successor cycle'}.</span>}
    </div>}

    {loading ? <div className="workspace-message" role="status">Loading project…</div>
      : error ? <div className="workspace-message error-state" role="alert"><h2>Could not load project</h2><p>{error}</p></div>
      : overview && <>
        {active === 'Overview' ? <div className="overview-panels">
          <section className="flow-panel">
            <div className="panel-head"><div><span className="eyebrow">{overview.selected_cycle || 'EMPTY PROJECT'}</span><h2>V-SIL progress</h2></div>
              <span className="progress-total">{overview.completion.passed}<small>/{overview.completion.total}</small></span>
            </div>
            <div className="flow-line">{stages.map(([id, label], index) => {
              const report = overview.reports.find(item => item.id === id)
              const done = !!report && !report.stale_reason && (report.state === 'PASS' || report.state === 'delivered')
              return <div key={id} className={`flow-stage ${done ? 'done' : ''}`}>
                <div className="stage-node">{done ? <ShieldCheck size={16} /> : id}</div>
                <span className="stage-id">{id}</span><span className="stage-name">{label}</span>
                {report && <ReportBadge report={report} />}
                {index < stages.length - 1 && <div className="stage-connector" />}
              </div>
            })}</div>
            <p className={`completion-note ${overview.completion.complete ? 'completion-ready' : ''}`}>{overview.completion.reason}</p>
            {!overview.selected_cycle && <p className="muted-copy">This project is scaffolded. Its agent selects a cycle before stage work begins.</p>}
          </section>

          <div className="overview-lower">
            <section className="content-panel report-summary"><h2>Stage and gate reports</h2>
              {overview.reports.map(report => {
                const artifact = overview.artifacts.find(item => item.kind === 'report' && item.path.endsWith(`/${report.id}.md`))
                return <button className="report-row report-button" key={report.id} disabled={!artifact?.exists}
                  onClick={() => artifact && openArtifact(artifact)}>
                  <span className="report-id">{report.id}</span><span className="report-name"><b>{report.iteration ? `Iteration ${report.iteration}` : 'No report yet'}</b>
                    {report.stale_reason && <small>{report.stale_reason}</small>}
                    {!report.stale_reason && report.based_on && <small>Based on {report.based_on[0]} iteration {report.based_on[1]}</small>}
                  </span><ReportBadge report={report} />{artifact?.exists && <ArrowUpRight size={14} />}
                </button>
              })}
            </section>
            <section className="content-panel evidence-summary"><h2>Verification artifacts</h2><p className="muted-copy">Run instructions and evidence belong to the selected cycle.</p>
              {overview.artifacts.filter(item => item.kind === 'test_run' || item.kind === 'prototype').map(artifact =>
                <button key={artifact.path} className="artifact-shortcut" disabled={!artifact.exists} onClick={() => openArtifact(artifact)}>
                  <FileText size={18} /><span><b>{artifact.label}</b><small>{artifact.exists ? 'Open artifact' : 'Not produced yet'}</small></span><ArrowUpRight size={14} />
                </button>)}
              {!overview.selected_cycle && <p className="muted-copy">No cycle artifacts yet.</p>}
            </section>
          </div>
        </div> : <div className="artifact-layout">
          <nav className="artifact-list" aria-label={`${active} artifacts`}>
            {artifacts.map(artifact => <button key={artifact.path}
              className={`artifact-option ${selectedArtifact?.path === artifact.path ? 'selected' : ''}`}
              aria-pressed={selectedArtifact?.path === artifact.path}
              onClick={() => setSelection({ path: artifact.path, view: active })}>
              <FileText size={16} /><span><b>{artifact.label}</b><small>{artifact.exists ? artifact.kind === 'report' ? 'Iterative report' : artifact.working_copy ? 'Working copy' : 'Cycle artifact' : 'Not produced yet'}</small></span>
            </button>)}
            {!artifacts.length && <p className="muted-copy">No {active.toLowerCase()} artifacts for this cycle.</p>}
          </nav>
          <ArtifactViewer key={`${project.path}:${selectedArtifact?.path || ''}`} artifact={selectedArtifact}
            projectPath={project.path} revision={refresh + revision} />
        </div>}
      </>}
  </div>
}

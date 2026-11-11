import { useEffect, useState } from 'react'
import {
  Anvil, Archive, ArrowDownRight, ArrowUpRight, BookOpen, ChevronDown,
  Command, FileText, FolderOpen, HardDrive, LayoutDashboard, Menu, Moon,
  ShieldCheck, Sun, Terminal,
} from 'lucide-react'
import { ActionsPanel } from './ActionsPanel'
import { BackupsView } from './BackupsView'
import { ProjectWorkflows } from './ProjectWorkflows'
import { Workspace } from './Workspace'
import { type Project, request } from './api'

type Bootstrap = { mode: 'launcher' | 'workspace'; project: Project | null; projects: Project[] }

function useBootstrap(projectPath: string | undefined, revision: number) {
  const [data, setData] = useState<Bootstrap>({ mode: 'launcher', project: null, projects: [] })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  useEffect(() => {
    const controller = new AbortController()
    setLoading(true)
    setError('')
    const query = projectPath ? `?${new URLSearchParams({ project_path: projectPath })}` : ''
    request<Bootstrap>(`/api/ui/bootstrap${query}`, controller.signal)
      .then(value => { if (!controller.signal.aborted) setData(value) })
      .catch(reason => { if (!controller.signal.aborted) setError(reason.message) })
      .finally(() => { if (!controller.signal.aborted) setLoading(false) })
    return () => controller.abort()
  }, [projectPath, revision])
  return { data, error, loading }
}

const navigation = [
  [LayoutDashboard, 'Overview'], [FileText, 'Reports'], [FolderOpen, 'Ground truth'],
  [BookOpen, 'Design'], [ShieldCheck, 'Verification'], [Archive, 'Backups'], [Terminal, 'CLI actions'],
] as const

export default function App() {
  const [active, setActive] = useState('Overview')
  const [dark, setDark] = useState(true)
  const [mobile, setMobile] = useState(false)
  const [selected, setSelected] = useState<Project | null>(null)
  const [forceLauncher, setForceLauncher] = useState(false)
  const [revision, setRevision] = useState(0)
  const { data, error, loading } = useBootstrap(selected?.path, revision)
  const [uiZoom, setUiZoom] = useState(() => {
    const saved = Number(localStorage.getItem('codeanvil-ui-zoom'))
    return Number.isFinite(saved) && saved >= 0.8 && saved <= 1.3 ? saved : 1
  })
  useEffect(() => {
    const onWheel = (event: WheelEvent) => {
      if (!event.ctrlKey) return
      event.preventDefault()
      setUiZoom(current => {
        const next = Math.min(1.3, Math.max(0.8, Math.round((current + (event.deltaY < 0 ? 0.05 : -0.05)) * 100) / 100))
        localStorage.setItem('codeanvil-ui-zoom', String(next))
        return next
      })
    }
    window.addEventListener('wheel', onWheel, { passive: false })
    return () => window.removeEventListener('wheel', onWheel)
  }, [])

  const project = forceLauncher ? null : selected || data.project
  const showWorkspace = !forceLauncher && project !== null
  const openProject = (value: Project) => {
    setSelected(value)
    setForceLauncher(false)
    setActive('Overview')
    setRevision(current => current + 1)
  }

  return <div className={dark ? 'app' : 'app light'} style={{ zoom: uiZoom }}>
    <header className="topbar">
      <button className="icon-btn mobile-menu" onClick={() => setMobile(!mobile)} aria-label="Toggle navigation"><Menu size={18} /></button>
      <div className="brand"><span className="brand-mark"><Anvil size={19} /></span><span>CODE<span className="ember">ANVIL</span></span><span className="brand-tag">FORGE</span></div>
      <div className="top-separator" />
      <button className="project-switch" onClick={() => { setSelected(null); setForceLauncher(true); setActive('Overview') }}>
        <span className="project-dot" /><span>{project?.name || 'Project launcher'}</span><ChevronDown size={14} />
      </button>
      <div className="top-spacer" />
      <div className="status-pill"><span className="pulse" /> LOCAL ENGINE <span className="status-sep" /> {error ? 'UNAVAILABLE' : loading ? 'LOADING' : 'READY'}</div>
      <button className="icon-btn" onClick={() => setDark(!dark)} aria-label="Toggle theme">{dark ? <Sun size={17} /> : <Moon size={17} />}</button>
    </header>

    <div className="shell">
      <nav className={`rail ${mobile ? 'rail-open' : ''}`} aria-label="Workspace navigation">
        <div className="rail-group"><span className="rail-label">WORKSPACE</span>
          {navigation.map(([Icon, label]) => <button key={label} className={`rail-item ${active === label ? 'selected' : ''}`}
            aria-label={label} aria-current={active === label ? 'page' : undefined} onClick={() => { setActive(label); setMobile(false) }}>
            <Icon size={17} /><span>{label}</span>
          </button>)}
        </div>
        <div className="rail-bottom"><span className="rail-footnote">PROJECTS · ARTIFACTS · EVIDENCE</span></div>
      </nav>
      <main className="main-area">
        {active === 'CLI actions' ? <ActionsPanel projectPath={project?.path} onComplete={() => setRevision(value => value + 1)} />
          : showWorkspace && project ? active === 'Backups' ? <BackupsView key={project.path} projectPath={project.path} />
            : <Workspace key={project.path} project={project} active={active} onSetActive={setActive} revision={revision} />
          : <Launcher projects={data.projects} loading={loading} error={error} onSelect={openProject} />}
      </main>
    </div>
    <footer className="statusbar"><span><span className="online-dot" /> CODEANVIL 0.7.0</span><span className="status-path">{project?.path || 'No project selected'}</span>
      <span className="footer-right">{Math.round(uiZoom * 100)}% · CTRL+SCROLL <span className="status-sep" /> LOCAL</span>
    </footer>
  </div>
}

function Launcher({ projects, loading, error, onSelect }: {
  projects: Project[]; loading: boolean; error: string; onSelect: (project: Project) => void
}) {
  return <div className="launcher launcher-canvas">
    <div className="launcher-heading"><div className="eyebrow"><span className="eyebrow-line" /> PROJECT DESK</div>
      <h1>Choose your <span>workpiece.</span></h1><p className="lede">Your projects, gates, and tools in one place.</p>
      <ProjectWorkflows onComplete={onSelect} />
    </div>
    <div className="section-heading"><div><span className="eyebrow">RECENT PROJECTS</span><h2>Projects in CodeAnvil</h2></div></div>
    <div className="project-grid">
      {error ? <div className="empty-projects" role="alert"><HardDrive size={21} /><div><b>Could not load projects</b><span>{error}</span></div></div>
        : loading ? <div className="empty-projects" role="status">Loading registered projects…</div>
        : projects.length ? projects.map(project => <button className="project-card" key={project.id || project.path} onClick={() => onSelect(project)}>
          <div className="card-top"><span className="project-icon"><Anvil size={18} /></span></div><strong>{project.name}</strong>
          <span className="project-path" title={project.path}>{project.path}</span><div className="card-foot"><span><FolderOpen size={13} /> Open workspace</span><ArrowUpRight size={15} /></div>
        </button>) : <div className="empty-projects"><div className="empty-icon"><HardDrive size={21} /></div><div><b>No registered projects</b><span>Create a project or add an existing folder to get started.</span></div></div>}
    </div>
    <details className="upcoming-features"><summary>Coming next</summary><p>Live agent terminal, automatic file updates, hardware gallery, telemetry charts and native desktop packaging.</p></details>
    <div className="launcher-footer"><span><Command size={13} /> CODEANVIL TOOLCHAIN</span><span>LOCAL WORKSPACE <ArrowDownRight size={12} /></span></div>
  </div>
}

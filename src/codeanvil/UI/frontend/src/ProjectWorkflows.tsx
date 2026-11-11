import { useEffect, useRef, useState } from 'react'
import type { FormEvent, KeyboardEvent } from 'react'
import { FolderOpen, Plus, X } from 'lucide-react'

type Project = { id?: string; name: string; path: string; cycle?: string | null }
type Server = { name: string; description?: string; installed: boolean }
type Mode = 'sync' | 'create'

async function request<T>(path: string, body?: object, signal?: AbortSignal): Promise<T> {
  const response = await fetch(`/api/workflows/${path}`, body === undefined
    ? { signal }
    : { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body), signal })
  let payload
  try {
    payload = await response.json()
  } catch {
    throw new Error(`The local server returned an unreadable response (${response.status}).`)
  }
  if (!response.ok) {
    throw new Error(typeof payload.detail === 'string' ? payload.detail : `Request failed (${response.status}).`)
  }
  return payload as T
}

function WorkflowDialog({ mode, onClose, onComplete }: {
  mode: Mode
  onClose: () => void
  onComplete: (project: Project) => void
}) {
  const [path, setPath] = useState('')
  const [name, setName] = useState('')
  const [folder, setFolder] = useState('')
  const [servers, setServers] = useState<Server[]>([])
  const [selectedServers, setSelectedServers] = useState<string[]>([])
  const [catalogLoading, setCatalogLoading] = useState(mode === 'create')
  const [catalogError, setCatalogError] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [picking, setPicking] = useState(false)
  const [pickerNotice, setPickerNotice] = useState('')
  const dialog = useRef<HTMLDivElement>(null)
  const firstInput = useRef<HTMLInputElement>(null)
  const creating = mode === 'create'

  useEffect(() => { firstInput.current?.focus() }, [])
  useEffect(() => {
    if (!creating) return
    const controller = new AbortController()
    request<{ servers: Server[] }>('mcp', undefined, controller.signal)
      .then(data => { if (!controller.signal.aborted) setServers(data.servers) })
      .catch(reason => { if (!controller.signal.aborted) setCatalogError(reason.message) })
      .finally(() => { if (!controller.signal.aborted) setCatalogLoading(false) })
    return () => controller.abort()
  }, [creating])

  const keyDown = (event: KeyboardEvent<HTMLDivElement>) => {
    if (event.key === 'Escape' && !busy && !picking) {
      event.stopPropagation()
      onClose()
    }
    if (event.key !== 'Tab') return
    const controls = Array.from(dialog.current?.querySelectorAll<HTMLElement>(
      'button:not(:disabled), input:not(:disabled), select:not(:disabled), a[href]',
    ) || [])
    const first = controls[0]
    const last = controls[controls.length - 1]
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault()
      last?.focus()
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault()
      first?.focus()
    }
  }

  const pickFolder = async () => {
    setPicking(true)
    setPickerNotice('')
    try {
      const result = await request<{ path: string | null }>('pick-folder', { initial_path: path || undefined })
      if (result.path !== null) setPath(result.path)
    } catch (reason) {
      const detail = reason instanceof Error ? reason.message : 'Folder selection is unavailable.'
      setPickerNotice(`${detail} You can enter the folder path below.`)
    } finally {
      setPicking(false)
    }
  }

  const submit = async (event: FormEvent) => {
    event.preventDefault()
    setError('')
    if (!path.trim() || (creating && !name.trim())) {
      setError(creating ? 'Enter a project name and parent folder.' : 'Enter the project folder.')
      return
    }
    setBusy(true)
    try {
      const body = creating
        ? { name: name.trim(), parent_path: path.trim(), folder: folder.trim() || undefined, mcp_servers: selectedServers }
        : { path: path.trim() }
      const result = await request<{ project: Project }>(creating ? 'create' : 'sync', body)
      if (typeof result.project?.path !== 'string' || typeof result.project?.name !== 'string') {
        throw new Error('The local server did not return a valid project.')
      }
      onComplete(result.project)
      onClose()
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'The project operation failed.')
    } finally {
      setBusy(false)
    }
  }

  return <div className="dialog-backdrop">
    <div className="dialog-surface" role="dialog" aria-modal="true" aria-labelledby="workflow-title"
      ref={dialog} onKeyDown={keyDown}>
      <div className="panel-head">
        <h2 id="workflow-title">{creating ? 'Create project' : 'Add existing project'}</h2>
        <button type="button" className="icon-btn" aria-label="Close project dialog" disabled={busy || picking} onClick={onClose}>
          <X size={18}/>
        </button>
      </div>
      <p className="workflow-help">{creating
        ? 'Choose where your new workspace will live and which installed tools to activate.'
        : 'Choose an existing CodeAnvil project to add it to your local project list.'}</p>
      <form onSubmit={submit} aria-busy={busy}>
        <fieldset className="workflow-fields" disabled={busy || picking}>
          {creating && <label className="action-field">
            <b>Project name</b>
            <input ref={firstInput} value={name} onChange={event => setName(event.target.value)} required autoComplete="off"/>
          </label>}
          <label className="action-field">
            <b>{creating ? 'Parent folder' : 'Project folder'}</b>
            <input ref={creating ? undefined : firstInput} value={path} onChange={event => setPath(event.target.value)}
              required autoComplete="off" spellCheck={false}/>
            <small>{creating ? 'The project folder will be created inside this directory.' : 'The folder must contain .codeanvil/project.yaml.'}</small>
          </label>
          <button type="button" className="secondary-button" onClick={pickFolder}>
            <FolderOpen size={15}/>{picking ? 'Choosing folder…' : 'Browse folders'}
          </button>
          {pickerNotice && <p className="workflow-help" role="status">{pickerNotice}</p>}
          {creating && <>
            <label className="action-field">
              <b>Folder name (optional)</b>
              <input value={folder} onChange={event => setFolder(event.target.value)} autoComplete="off" spellCheck={false}/>
              <small>Leave blank to derive a folder name from the project name.</small>
            </label>
            <div className="workflow-catalog">
              <h3>Project tools</h3>
              <p className="workflow-help">Activate servers already installed on this machine. This does not install global software.</p>
              {catalogLoading && <p role="status">Loading installed tools…</p>}
              {catalogError && <p className="workflow-help" role="status">{catalogError} You can create the project without MCP tools.</p>}
              {!catalogLoading && !catalogError && servers.length === 0 && <p className="workflow-help">No MCP servers are configured.</p>}
              {servers.map(server => <label className="confirm-action" key={server.name}>
                <input type="checkbox" disabled={!server.installed} checked={selectedServers.includes(server.name)}
                  onChange={event => setSelectedServers(current => event.target.checked
                    ? [...current, server.name] : current.filter(value => value !== server.name))}/>
                <span><b>{server.name}</b>{server.installed ? '' : ' — not installed'}
                  {server.description && <small className="workflow-help"> {server.description}</small>}</span>
              </label>)}
            </div>
          </>}
        </fieldset>
        {error && <p className="workflow-error" role="alert">{error}</p>}
        <div className="workflow-actions">
          <button type="button" className="secondary-button" onClick={onClose} disabled={busy || picking}>Cancel</button>
          <button type="submit" className="primary-button" disabled={busy || picking}>
            {busy ? (creating ? 'Creating…' : 'Adding…') : (creating ? 'Create project' : 'Add project')}
          </button>
        </div>
      </form>
    </div>
  </div>
}

export function ProjectWorkflows({ onComplete }: { onComplete: (project: Project) => void }) {
  const [mode, setMode] = useState<Mode | null>(null)
  const opener = useRef<HTMLButtonElement | null>(null)
  const close = () => { setMode(null); opener.current?.focus() }

  return <section className="workflow-panel" aria-label="Project actions">
    <div className="workflow-actions">
      <button className="primary-button" onClick={event => { opener.current = event.currentTarget; setMode('create') }}>
        <Plus size={16}/>Create project
      </button>
      <button className="secondary-button" onClick={event => { opener.current = event.currentTarget; setMode('sync') }}>
        <FolderOpen size={16}/>Add existing project
      </button>
    </div>
    {mode && <WorkflowDialog mode={mode} onClose={close} onComplete={onComplete}/>}
  </section>
}

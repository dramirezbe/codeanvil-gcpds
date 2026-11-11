import { useEffect, useRef, useState } from 'react'
import { Play, Square, Terminal as TerminalIcon } from 'lucide-react'
import { Terminal } from '@xterm/xterm'
import { FitAddon } from '@xterm/addon-fit'
import { type Project, request } from './api'
import '@xterm/xterm/css/xterm.css'
import './styles/terminal.css'

type Launcher = {
  id: string; label: string; installed: boolean; available: boolean
  kind: 'terminal'; sandbox_supported: boolean
}
type Session = {
  id: string; pid: number; project_path: string; launcher_id: string; sandbox: boolean
  state: 'running' | 'exited'; exit_code: number | null; clients: number
}
type Launchers = { supported: boolean; platform: string; launchers: Launcher[] }
type Props = { project: Project; theme: 'dark' | 'light' }

function terminalSize(emulator: Terminal | null) {
  return {
    cols: Math.max(2, Math.min(500, emulator?.cols ?? 80)),
    rows: Math.max(2, Math.min(200, emulator?.rows ?? 24)),
  }
}

function terminalTheme(theme: Props['theme']) {
  return theme === 'dark' ? {
    background: '#111417', foreground: '#e5e8e9', cursor: '#f0783c', selectionBackground: '#653b2a',
    black: '#171b1f', red: '#ec7777', green: '#83c99b', yellow: '#e4bf7a',
    blue: '#82aee5', magenta: '#c99bdd', cyan: '#72c7ca', white: '#e5e8e9',
  } : {
    background: '#ffffff', foreground: '#1d2528', cursor: '#bb4b1d', selectionBackground: '#f3d4c4',
    black: '#1d2528', red: '#af3636', green: '#35744b', yellow: '#87611a',
    blue: '#316aa5', magenta: '#8552a0', cyan: '#21777a', white: '#f7f8f7',
  }
}

async function postSession(url: string, body?: object): Promise<Session> {
  const response = await fetch(url, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    ...(body ? { body: JSON.stringify(body) } : {}),
  })
  const value = await response.json()
  if (!response.ok) throw new Error(typeof value.detail === 'string' ? value.detail : `Terminal request failed (${response.status}).`)
  return value
}

export function TerminalPanel({ project, theme }: Props) {
  const container = useRef<HTMLDivElement>(null)
  const terminal = useRef<Terminal | null>(null)
  const fit = useRef<FitAddon | null>(null)
  const socket = useRef<WebSocket | null>(null)
  const themeRef = useRef(theme)
  const generation = useRef(0)
  const sessionRef = useRef<Session | null>(null)
  const [catalog, setCatalog] = useState<Launchers | null>(null)
  const [launcherId, setLauncherId] = useState('')
  const [sandbox, setSandbox] = useState(false)
  const [session, setSession] = useState<Session | null>(null)
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)
  const [connected, setConnected] = useState(false)
  const [connectionAttempt, setConnectionAttempt] = useState(0)
  const [error, setError] = useState('')
  const running = session?.state === 'running'
  const selected = catalog?.launchers.find(value => value.id === launcherId)
  const ready = !loading && catalog?.supported && selected?.installed && selected.available
  themeRef.current = theme

  const acceptSession = (value: Session | null) => {
    sessionRef.current = value
    setSession(value)
  }

  const sendSize = () => {
    fit.current?.fit()
    if (sessionRef.current?.state === 'running' && socket.current?.readyState === WebSocket.OPEN) {
      socket.current.send(JSON.stringify({ type: 'resize', ...terminalSize(terminal.current) }))
    }
  }

  useEffect(() => {
    if (!container.current) return
    const emulator = new Terminal({
      cursorBlink: true, fontFamily: "'DM Mono', monospace", fontSize: 13,
      scrollback: 5000, theme: terminalTheme(themeRef.current),
    })
    const sizing = new FitAddon()
    terminal.current = emulator
    fit.current = sizing
    emulator.loadAddon(sizing)
    emulator.open(container.current)
    sizing.fit()
    const input = emulator.onData(data => {
      if (sessionRef.current?.state === 'running' && socket.current?.readyState === WebSocket.OPEN) {
        socket.current.send(JSON.stringify({ type: 'input', data }))
      }
    })
    const observer = new ResizeObserver(sendSize)
    observer.observe(container.current)
    return () => {
      observer.disconnect()
      input.dispose()
      emulator.dispose()
      terminal.current = null
      fit.current = null
    }
  }, [project.path])

  useEffect(() => {
    if (terminal.current) terminal.current.options.theme = terminalTheme(theme)
  }, [theme])

  useEffect(() => {
    const controller = new AbortController()
    generation.current += 1
    setLoading(true)
    setBusy(false)
    setConnected(false)
    setError('')
    setCatalog(null)
    acceptSession(null)
    setLauncherId('')
    setSandbox(false)
    const query = new URLSearchParams({ project_path: project.path })
    Promise.all([
      request<Launchers>('/api/terminal/launchers', controller.signal),
      request<{ sessions: Session[] }>(`/api/terminal/sessions?${query}`, controller.signal),
    ]).then(([launchers, result]) => {
      if (controller.signal.aborted) return
      setCatalog(launchers)
      const existing = result.sessions.find(value => value.state === 'running' && value.project_path === project.path)
      const available = launchers.launchers.filter(value => value.installed && value.available)
      setLauncherId(existing?.launcher_id ?? available.find(value => value.id === 'claude')?.id ?? available[0]?.id ?? '')
      setSandbox(existing?.sandbox ?? false)
      acceptSession(existing ?? null)
    }).catch(reason => {
      if (!controller.signal.aborted) setError(reason.message)
    }).finally(() => {
      if (!controller.signal.aborted) setLoading(false)
    })
    return () => {
      controller.abort()
      generation.current += 1
    }
  }, [project.path])

  useEffect(() => {
    if (!session?.id || session.project_path !== project.path) return
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    terminal.current?.reset()
    const connection = new WebSocket(`${protocol}//${window.location.host}/api/terminal/sessions/${encodeURIComponent(session.id)}/stream`)
    connection.binaryType = 'arraybuffer'
    socket.current = connection
    setConnected(false)
    let exited = session.state === 'exited'
    connection.onopen = () => {
      setConnected(true)
      setError('')
      sendSize()
      terminal.current?.focus()
    }
    connection.onmessage = event => {
      if (event.data instanceof ArrayBuffer) {
        terminal.current?.write(new Uint8Array(event.data))
        return
      }
      try {
        const message = JSON.parse(event.data)
        if (message.type === 'ready') {
          exited = message.session.state === 'exited'
          acceptSession(message.session)
        } else if (message.type === 'exit') {
          exited = true
          if (sessionRef.current) acceptSession({ ...sessionRef.current, state: 'exited', exit_code: message.code })
        } else if (message.type === 'error') setError(message.message)
      } catch {
        setError('The terminal received an invalid server message.')
      }
    }
    connection.onerror = () => {
      if (sessionRef.current?.state === 'running') setError('Could not connect to the local terminal. Check that CodeAnvil is still running.')
    }
    connection.onclose = () => {
      setConnected(false)
      if (!exited && sessionRef.current?.state === 'running') setError(current => current || 'Terminal connection closed. Reconnect to the running process.')
    }
    return () => {
      connection.onopen = null
      connection.onmessage = null
      connection.onerror = null
      connection.onclose = null
      connection.close()
      if (socket.current === connection) socket.current = null
    }
  }, [session?.id, connectionAttempt, project.path])

  const start = async () => {
    if (!ready || running || busy) return
    const expectedGeneration = generation.current
    setBusy(true)
    setError('')
    try {
      fit.current?.fit()
      const created = await postSession('/api/terminal/sessions', {
        project_path: project.path, launcher_id: launcherId, sandbox,
        ...terminalSize(terminal.current),
      })
      if (generation.current === expectedGeneration) acceptSession(created)
    } catch (reason) {
      if (generation.current === expectedGeneration) setError(reason instanceof Error ? reason.message : 'Could not start the local CLI.')
    } finally { if (generation.current === expectedGeneration) setBusy(false) }
  }

  const stop = async () => {
    if (!session || !running || busy) return
    const expectedGeneration = generation.current
    setBusy(true)
    setError('')
    try {
      const stopped = await postSession(`/api/terminal/sessions/${encodeURIComponent(session.id)}/stop`)
      if (generation.current === expectedGeneration) acceptSession(stopped)
    } catch (reason) {
      if (generation.current === expectedGeneration) setError(reason instanceof Error ? reason.message : 'Could not stop the local CLI.')
    } finally { if (generation.current === expectedGeneration) setBusy(false) }
  }

  const stateLabel = running ? (connected ? 'Running' : 'Connecting…')
    : session ? `Exited (${session.exit_code ?? 'unknown'})` : loading ? 'Loading…' : 'Ready to start'

  return <section className="terminal-workspace" aria-label="Project terminal">
    <header className="terminal-heading">
      <div><span className="eyebrow"><TerminalIcon size={14} /> LOCAL PROCESS</span><h1>Interactive terminal</h1>
        <p>Run your installed coding CLI in <strong>{project.name}</strong>.</p></div>
      <div className="terminal-process" role="status"><span>{stateLabel}</span>{session && <code>PID {session.pid}</code>}</div>
    </header>
    <div className="terminal-controls">
      <label className="terminal-cli">Local CLI<select value={launcherId} disabled={loading || busy || running || !catalog?.supported}
        onChange={event => {
          setLauncherId(event.target.value)
          if (!catalog?.launchers.find(value => value.id === event.target.value)?.sandbox_supported) setSandbox(false)
        }}>
        {!launcherId && <option value="">Select a local CLI</option>}
        {catalog?.launchers.map(value => <option key={value.id} value={value.id} disabled={!value.installed || !value.available}>
          {value.label}{!value.installed ? ' (not installed)' : !value.available ? ' (unavailable)' : ''}
        </option>)}
      </select></label>
      <label className="terminal-sandbox"><input type="checkbox" checked={sandbox} disabled={loading || busy || running || !catalog?.supported || !selected?.sandbox_supported}
        onChange={event => setSandbox(event.target.checked)} />Sandbox mode</label>
      <div className="terminal-buttons">
        <button className="primary-button" disabled={!ready || running || busy} onClick={start}><Play size={14} />Start terminal</button>
        <button className="secondary-button" disabled={!running || busy} onClick={stop}><Square size={13} />Stop terminal</button>
      </div>
    </div>
    <p className="terminal-mode-help">Sandbox mode uses CodeAnvil project-only settings and CLI isolation. Normal mode uses your usual local CLI settings. Choose before starting.</p>
    {!loading && catalog && !catalog.supported && <p className="terminal-notice">Interactive terminals are not supported on this platform. Use Linux or WSL.</p>}
    {!loading && catalog?.supported && !catalog.launchers.some(value => value.installed && value.available) && <p className="terminal-notice">Install a supported local CLI, then reopen this view.</p>}
    {!loading && selected && !selected.sandbox_supported && <p className="terminal-notice">Sandbox mode is not available for this CLI.</p>}
    {error && <div className="terminal-error" role="alert"><span>{error}</span>{running && !connected && <button className="secondary-button"
      onClick={() => setConnectionAttempt(value => value + 1)}>Reconnect</button>}</div>}
    <div ref={container} className="terminal-screen" aria-label="Interactive CLI terminal" />
    <p className="terminal-footnote">{project.path} <span>Switching views keeps the process running. Use Stop terminal to end it.</span></p>
  </section>
}

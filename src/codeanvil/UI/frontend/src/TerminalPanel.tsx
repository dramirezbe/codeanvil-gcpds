import { useEffect, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import { Square, Terminal as TerminalIcon } from 'lucide-react'
import { Terminal } from '@xterm/xterm'
import { FitAddon } from '@xterm/addon-fit'
import { type Project, request } from './api'
import { type Launcher, LauncherIcon, LauncherSidebar } from './LauncherSidebar'
import '@xterm/xterm/css/xterm.css'
import './styles/terminal.css'

type Session = {
  id: string; pid: number; project_path: string; launcher_id: string; sandbox: boolean
  state: 'running' | 'exited'; exit_code: number | null; clients: number
}
type Launchers = { supported: boolean; platform: string; launchers: Launcher[] }
type Props = {
  project: Project
  theme: 'dark' | 'light'
  visible?: boolean
  launcherSlot?: HTMLElement | null
  onOpenTerminal?: () => void
}

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

export function TerminalPanel({ project, theme, visible = true, launcherSlot, onOpenTerminal }: Props) {
  const container = useRef<HTMLDivElement>(null)
  const terminal = useRef<Terminal | null>(null)
  const fit = useRef<FitAddon | null>(null)
  const socket = useRef<WebSocket | null>(null)
  const themeRef = useRef(theme)
  const generation = useRef(0)
  const sessionRef = useRef<Session | null>(null)
  const [catalog, setCatalog] = useState<Launchers | null>(null)
  const [launcherId, setLauncherId] = useState('')
  const [modes, setModes] = useState<Record<string, boolean>>({})
  const [session, setSession] = useState<Session | null>(null)
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)
  const [connected, setConnected] = useState(false)
  const [connectionAttempt, setConnectionAttempt] = useState(0)
  const [error, setError] = useState('')
  const running = session?.state === 'running'
  const selected = catalog?.launchers.find(value => value.id === launcherId)
  const ready = Boolean(!loading && catalog?.supported && selected?.installed && selected.available)
  const displayed = catalog?.launchers.find(value => value.id === session?.launcher_id) || selected
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
  }, [project.path, visible])

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
    setModes({})
    const query = new URLSearchParams({ project_path: project.path })
    Promise.all([
      request<Launchers>('/api/launchers', controller.signal),
      request<{ sessions: Session[] }>(`/api/terminal/sessions?${query}`, controller.signal),
    ]).then(([launchers, result]) => {
      if (controller.signal.aborted) return
      setCatalog(launchers)
      const existing = result.sessions.find(value => value.state === 'running' && value.project_path === project.path)
      const available = launchers.launchers.filter(value => value.kind === 'terminal' && value.installed && value.available)
      setLauncherId(existing?.launcher_id ?? available.find(value => value.id === 'claude')?.id ?? available[0]?.id ?? '')
      if (existing) setModes({ [existing.launcher_id]: existing.sandbox })
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
    if (!session?.id || session.project_path !== project.path || (!visible && session.state === 'exited')) return
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    if (visible) terminal.current?.reset()
    const connection = new WebSocket(`${protocol}//${window.location.host}/api/terminal/sessions/${encodeURIComponent(session.id)}/stream`)
    connection.binaryType = 'arraybuffer'
    socket.current = connection
    setConnected(false)
    let exited = session.state === 'exited'
    connection.onopen = () => {
      setConnected(true)
      setError('')
      if (visible) {
        sendSize()
        terminal.current?.focus()
      }
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
  }, [session?.id, connectionAttempt, project.path, visible])

  const start = async (launcher: Launcher | undefined = selected) => {
    if (!launcher?.installed || !launcher.available || !catalog?.supported || busy) return
    const current = sessionRef.current
    if (current?.state === 'running' && current.launcher_id === launcher.id) return
    const expectedGeneration = generation.current
    setBusy(true)
    setError('')
    onOpenTerminal?.()
    try {
      if (current?.state === 'running') {
        const stopped = await postSession(`/api/terminal/sessions/${encodeURIComponent(current.id)}/stop`)
        if (generation.current !== expectedGeneration) return
        acceptSession(stopped)
        if (stopped.state !== 'exited') throw new Error('The current terminal is still running.')
      }
      setLauncherId(launcher.id)
      fit.current?.fit()
      const created = await postSession('/api/terminal/sessions', {
        project_path: project.path, launcher_id: launcher.id, sandbox: launcher.sandbox_supported && !!modes[launcher.id],
        ...terminalSize(terminal.current),
      })
      if (generation.current === expectedGeneration) acceptSession(created)
    } catch (reason) {
      if (generation.current === expectedGeneration) setError(reason instanceof Error ? reason.message : 'Could not start the local CLI.')
    } finally { if (generation.current === expectedGeneration) setBusy(false) }
  }

  const selectLauncher = (launcher: Launcher) => {
    if (busy) return
    if (running) {
      if (session.launcher_id === launcher.id) onOpenTerminal?.()
      else void start(launcher)
    } else setLauncherId(launcher.id)
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

  const controls = <>
    <LauncherSidebar items={catalog?.launchers ?? []} projectPath={project.path} theme={theme}
      supported={!!catalog?.supported} selected={launcherId} running={running ? session.launcher_id : undefined}
      modes={modes} busy={busy} ready={ready} onSelect={selectLauncher} onStart={() => void start()}
      onSandbox={(id, checked) => setModes(current => ({ ...current, [id]: checked }))} />
    {!visible && !catalog && error && <p className="launcher-error" role="alert">{error}</p>}
  </>

  return <>
    {launcherSlot ? createPortal(controls, launcherSlot) : launcherSlot === undefined ? controls : null}
    {visible && <section className="terminal-workspace" aria-label="Project terminal">
      <header className="terminal-heading">
        <div className="terminal-title">{displayed ? <LauncherIcon launcher={displayed} theme={theme} /> : <TerminalIcon size={20} />}
          <h1>{displayed?.label ?? 'Interactive terminal'}</h1>
        </div>
        <div className="terminal-buttons">
          <div className="terminal-process" role="status"><span>{stateLabel}</span>{session && <code>PID {session.pid}</code>}</div>
          <button className="secondary-button" disabled={!running || busy} onClick={stop}><Square size={13} />Stop terminal</button>
        </div>
      </header>
      {!loading && catalog && !catalog.supported && <p className="terminal-notice">Interactive terminals are not supported on this platform. Use Linux or WSL.</p>}
      {!loading && catalog?.supported && !ready && !running && <p className="terminal-notice">Install a supported local CLI to start a terminal from the sidebar.</p>}
      {ready && !session && !error && <p className="terminal-notice">Select an agent and start its terminal from the sidebar.</p>}
      {error && <div className="terminal-error" role="alert"><span>{error}</span>{running && !connected && <button className="secondary-button"
        onClick={() => setConnectionAttempt(value => value + 1)}>Reconnect</button>}</div>}
      <div ref={container} className="terminal-screen" aria-label="Interactive CLI terminal" />
    </section>}
  </>
}

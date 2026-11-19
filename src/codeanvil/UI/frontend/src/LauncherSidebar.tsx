import { useEffect, useRef, useState } from 'react'
import { Monitor, Play, Shield, Terminal } from 'lucide-react'
import claude from './assets/icons/claude.svg'
import codex from './assets/icons/openai-codex.svg'
import jetbrains from './assets/icons/jetbrains.svg'
import opencodeDark from './assets/icons/opencode-dark.svg'
import opencodeLight from './assets/icons/opencode-light.svg'
import pi from './assets/icons/pi.svg'
import vscode from './assets/icons/vscode.svg'
import './styles/launcher-sidebar.css'

export type Launcher = {
  id: string
  label: string
  icon?: string | null
  kind: 'gui' | 'terminal'
  installed: boolean
  available: boolean
  sandbox_supported: boolean
}

const icons = new Map([
  ['claude', claude], ['openai-codex', codex], ['jetbrains', jetbrains], ['pi', pi], ['vscode', vscode],
])

export function LauncherIcon({ launcher, theme }: { launcher: Launcher; theme: 'dark' | 'light' }) {
  const asset = launcher.icon?.startsWith('opencode')
    ? theme === 'dark' ? opencodeDark : opencodeLight
    : icons.get(launcher.icon ?? '')
  const Fallback = launcher.kind === 'gui' ? Monitor : Terminal
  return asset ? <img className="launcher-icon" src={asset} alt="" />
    : <Fallback className="launcher-icon" size={20} aria-hidden="true" />
}

type Props = {
  items: Launcher[]
  projectPath: string
  theme: 'dark' | 'light'
  supported: boolean
  selected: string
  running?: string
  modes: Record<string, boolean>
  busy: boolean
  ready: boolean
  onSelect: (launcher: Launcher) => void
  onSandbox: (id: string, checked: boolean) => void
  onStart: () => void
}

export function LauncherSidebar({
  items, projectPath, theme, supported, selected, running, modes, busy, ready,
  onSelect, onSandbox, onStart,
}: Props) {
  const timers = useRef(new Map<string, ReturnType<typeof setTimeout>>()).current
  const launchRequest = useRef<AbortController | null>(null)
  const [pending, setPending] = useState<string | null>(null)
  const [recent, setRecent] = useState<string[]>([])
  const [error, setError] = useState('')
  useEffect(() => () => {
    launchRequest.current?.abort()
    for (const timer of timers.values()) clearTimeout(timer)
    timers.clear()
  }, [timers])

  async function openDesktop(launcher: Launcher) {
    if (launchRequest.current) return
    const controller = new AbortController()
    launchRequest.current = controller
    setPending(launcher.id)
    setError('')
    try {
      const response = await fetch(`/api/launchers/${encodeURIComponent(launcher.id)}/launch`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ project_path: projectPath }),
        signal: controller.signal,
      })
      const result = await response.json()
      if (controller.signal.aborted) return
      if (!response.ok) throw new Error(typeof result.detail === 'string' ? result.detail : 'Could not open the desktop app.')
      clearTimeout(timers.get(launcher.id))
      setRecent(current => current.includes(launcher.id) ? current : [...current, launcher.id])
      timers.set(launcher.id, setTimeout(() => {
        setRecent(current => current.filter(id => id !== launcher.id))
        timers.delete(launcher.id)
      }, 15_000))
    } catch (reason) {
      if (!controller.signal.aborted) setError(reason instanceof Error ? reason.message : 'Could not open the desktop app.')
    } finally {
      launchRequest.current = null
      if (!controller.signal.aborted) setPending(null)
    }
  }

  function row(launcher: Launcher) {
    const cli = launcher.kind === 'terminal'
    const usable = launcher.installed && launcher.available && (!cli || supported)
    const chosen = cli && launcher.id === selected
    const live = cli && launcher.id === running
    const launched = !cli && recent.includes(launcher.id)
    const status = live ? 'Running' : launched ? 'Recently opened' : pending === launcher.id ? 'Opening…'
      : !launcher.available || (cli && !supported) ? 'Unavailable' : !launcher.installed ? 'Not installed'
        : chosen ? 'Selected' : 'Ready'
    const state = live || launched ? 'active' : !usable ? 'unavailable' : chosen ? 'selected' : 'idle'
    return <div className="launcher-row" data-state={state} key={launcher.id}>
      <button className="launcher-choice" aria-label={launcher.label}
        aria-pressed={cli ? chosen : undefined} aria-describedby={`launcher-status-${launcher.id}`}
        title={`${launcher.label} · ${status}`} disabled={!usable || (cli ? busy : pending !== null)}
        onClick={() => { if (cli) onSelect(launcher); else void openDesktop(launcher) }}>
        <LauncherIcon launcher={launcher} theme={theme} />
        <span className="launcher-label">{launcher.label}</span>
        <span className="launcher-status" id={`launcher-status-${launcher.id}`}>{status}</span>
      </button>
      {cli && launcher.sandbox_supported && <label className="launcher-sandbox" title={`Sandbox mode for ${launcher.label}`}>
        <input type="checkbox" aria-label={`Sandbox mode for ${launcher.label}`} checked={!!modes[launcher.id]}
          disabled={!usable || busy || live} onChange={event => onSandbox(launcher.id, event.target.checked)} />
        <Shield size={13} aria-hidden="true" />
      </label>}
    </div>
  }

  const desktop = items.filter(item => item.kind === 'gui')
  const terminal = items.filter(item => item.kind === 'terminal')
  return <section className="launcher-dock" aria-label="Project launchers">
    <span className="rail-label">AGENTS &amp; IDES</span>
    {desktop.map(row)}
    {desktop.length > 0 && terminal.length > 0 && <hr />}
    {terminal.map(row)}
    <button className="secondary-button launcher-start" aria-label="Start terminal" title="Start terminal"
      disabled={!ready || !!running || busy} onClick={onStart}>
      <Play size={14} /><span>Start terminal</span>
    </button>
    {error && <p className="launcher-error" role="alert">{error}</p>}
  </section>
}

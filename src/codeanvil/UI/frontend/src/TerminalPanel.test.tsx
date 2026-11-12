import { act, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { TerminalPanel } from './TerminalPanel'

const emulator = vi.hoisted(() => ({
  instances: [] as Array<{
    cols: number; rows: number; options: Record<string, unknown>; write: ReturnType<typeof vi.fn>
    dispose: ReturnType<typeof vi.fn>; focus: ReturnType<typeof vi.fn>; reset: ReturnType<typeof vi.fn>
    data?: (data: string) => void
  }>,
  fits: [] as Array<ReturnType<typeof vi.fn>>,
  observers: [] as Array<{ callback: () => void; disconnect: ReturnType<typeof vi.fn> }>,
}))

vi.mock('@xterm/xterm', () => ({ Terminal: class {
  cols = 100
  rows = 30
  options: Record<string, unknown>
  write = vi.fn()
  dispose = vi.fn()
  focus = vi.fn()
  reset = vi.fn()
  data?: (data: string) => void
  constructor(options: Record<string, unknown>) { this.options = options; emulator.instances.push(this) }
  loadAddon() {}
  open(element: HTMLElement) { element.setAttribute('data-emulator', 'open') }
  onData(callback: (data: string) => void) { this.data = callback; return { dispose: vi.fn() } }
} }))
vi.mock('@xterm/addon-fit', () => ({ FitAddon: class {
  fit = vi.fn()
  constructor() { emulator.fits.push(this.fit) }
} }))

class Socket {
  static OPEN = 1
  static instances: Socket[] = []
  readyState = 0
  binaryType = ''
  onopen: (() => void) | null = null
  onmessage: ((event: { data: string | ArrayBuffer }) => void) | null = null
  onclose: (() => void) | null = null
  onerror: (() => void) | null = null
  send = vi.fn()
  close = vi.fn(() => { this.readyState = 3 })
  constructor(readonly url: string) { Socket.instances.push(this) }
  open() { this.readyState = 1; this.onopen?.() }
  message(data: object | ArrayBuffer) {
    this.onmessage?.({ data: data instanceof ArrayBuffer ? data : JSON.stringify(data) })
  }
}

const project = { name: 'Sample', path: '/home/alice/Documents/sample' }
const launcher = { id: 'claude', label: 'Claude Code', installed: true, available: true, kind: 'terminal', sandbox_supported: true }
const session = { id: 'session-1', pid: 2345, project_path: project.path, launcher_id: 'claude', sandbox: false,
  state: 'running', exit_code: null, clients: 0 }

function backend(options: { supported?: boolean; launchers?: object[]; sessions?: object[]; startError?: string } = {}) {
  const fetch = vi.fn(async (url: string, init?: RequestInit) => {
    if (url === '/api/terminal/launchers') return Response.json({ supported: options.supported ?? true, platform: 'linux', launchers: options.launchers ?? [launcher] })
    if (url.startsWith('/api/terminal/sessions?')) {
      const path = new URL(url, 'http://localhost').searchParams.get('project_path')
      return Response.json({ sessions: (options.sessions ?? []).filter(value => (value as typeof session).project_path === path) })
    }
    if (url.endsWith('/stop')) return Response.json({ ...session, state: 'exited', exit_code: -15 })
    if (url === '/api/terminal/sessions' && init?.method === 'POST') {
      if (options.startError) return Response.json({ detail: options.startError }, { status: 409 })
      const body = JSON.parse(init.body as string)
      return Response.json({ ...session, sandbox: body.sandbox })
    }
    throw new Error(`Unexpected request: ${url}`)
  })
  vi.stubGlobal('fetch', fetch)
  return fetch
}

beforeEach(() => {
  Socket.instances = []
  emulator.instances = []
  emulator.fits = []
  emulator.observers = []
  vi.stubGlobal('WebSocket', Socket)
  vi.stubGlobal('ResizeObserver', class {
    disconnect = vi.fn()
    constructor(callback: () => void) { emulator.observers.push({ callback, disconnect: this.disconnect }) }
    observe() {}
  })
})

describe('Interactive local terminal', () => {
  it('waits for an explicit start, defaults to Claude and launches normal mode', async () => {
    const user = userEvent.setup()
    const fetch = backend({ launchers: [{ ...launcher, id: 'codex', label: 'Codex' }, launcher] })
    render(<TerminalPanel project={project} theme="dark" />)
    const start = await screen.findByRole('button', { name: 'Start terminal' })
    await waitFor(() => expect(start).toBeEnabled())
    expect(screen.getByRole('combobox', { name: 'Local CLI' })).toHaveValue('claude')
    expect(screen.getByRole('checkbox', { name: 'Sandbox mode' })).not.toBeChecked()
    expect(Socket.instances).toHaveLength(0)
    expect(fetch.mock.calls.every(([, init]) => init?.method !== 'POST')).toBe(true)
    await user.click(start)
    await waitFor(() => expect(Socket.instances).toHaveLength(1))
    expect(fetch).toHaveBeenCalledWith('/api/terminal/sessions', expect.objectContaining({
      method: 'POST', body: JSON.stringify({ project_path: project.path, launcher_id: 'claude', sandbox: false, cols: 100, rows: 30 }),
    }))
    expect(screen.getByText('PID 2345')).toBeInTheDocument()
    expect(screen.getByRole('checkbox', { name: 'Sandbox mode' })).toBeDisabled()
    expect(screen.getByRole('combobox', { name: 'Local CLI' })).toBeDisabled()
  })

  it('sends the selected sandbox setting only when starting a new process', async () => {
    const user = userEvent.setup()
    const fetch = backend()
    render(<TerminalPanel project={project} theme="dark" />)
    await waitFor(() => expect(screen.getByRole('button', { name: 'Start terminal' })).toBeEnabled())
    await user.click(screen.getByRole('checkbox', { name: 'Sandbox mode' }))
    await user.click(screen.getByRole('button', { name: 'Start terminal' }))
    await waitFor(() => expect(Socket.instances).toHaveLength(1))
    const request = fetch.mock.calls.find(([url, init]) => url === '/api/terminal/sessions' && init?.method === 'POST')
    expect(JSON.parse(request![1]!.body as string).sandbox).toBe(true)
    expect(screen.getByText(/project-only settings/i)).toBeInTheDocument()
  })

  it('forwards raw keyboard input and binary output, resizes and follows the theme', async () => {
    backend({ sessions: [session] })
    const view = render(<TerminalPanel project={project} theme="dark" />)
    await waitFor(() => expect(Socket.instances).toHaveLength(1))
    const socket = Socket.instances[0]
    const terminal = emulator.instances[0]
    expect(socket.binaryType).toBe('arraybuffer')
    expect(socket.url).toContain('/api/terminal/sessions/session-1/stream')
    act(() => { socket.open(); socket.message({ type: 'ready', session }) })
    expect(terminal.focus).toHaveBeenCalled()
    act(() => terminal.data?.('\u001b[AHi\r'))
    expect(socket.send).toHaveBeenCalledWith(JSON.stringify({ type: 'input', data: '\u001b[AHi\r' }))
    const bytes = new Uint8Array([27, 91, 51, 49, 109, 72, 105])
    act(() => socket.message(bytes.buffer))
    expect(terminal.write).toHaveBeenCalledWith(bytes)
    terminal.cols = 120
    terminal.rows = 42
    act(() => emulator.observers[0].callback())
    expect(socket.send).toHaveBeenCalledWith(JSON.stringify({ type: 'resize', cols: 120, rows: 42 }))
    view.rerender(<TerminalPanel project={project} theme="light" />)
    expect((terminal.options.theme as { background: string }).background).toBe('#ffffff')
    expect(Socket.instances).toHaveLength(1)
    act(() => socket.message({ type: 'exit', code: 0 }))
    expect(screen.getByText('Exited (0)')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Start terminal' })).toBeEnabled()
    socket.send.mockClear()
    act(() => { terminal.data?.('ignored'); emulator.observers[0].callback() })
    expect(socket.send).not.toHaveBeenCalled()
  })

  it('reattaches on reopening without spawning or stopping the server process on unmount', async () => {
    const fetch = backend({ sessions: [session] })
    const view = render(<TerminalPanel project={project} theme="dark" />)
    await waitFor(() => expect(Socket.instances).toHaveLength(1))
    view.unmount()
    expect(Socket.instances[0].close).toHaveBeenCalled()
    expect(emulator.instances[0].dispose).toHaveBeenCalled()
    expect(emulator.observers[0].disconnect).toHaveBeenCalled()
    render(<TerminalPanel project={project} theme="dark" />)
    await waitFor(() => expect(Socket.instances).toHaveLength(2))
    expect(fetch.mock.calls.every(([, init]) => init?.method !== 'POST')).toBe(true)
  })

  it('stops a running session explicitly and shows server errors', async () => {
    const user = userEvent.setup()
    const fetch = backend({ sessions: [session] })
    render(<TerminalPanel project={project} theme="dark" />)
    await waitFor(() => expect(Socket.instances).toHaveLength(1))
    act(() => Socket.instances[0].message({ type: 'error', message: 'PTY connection failed.' }))
    expect(screen.getByRole('alert')).toHaveTextContent('PTY connection failed.')
    await user.click(screen.getByRole('button', { name: 'Stop terminal' }))
    await waitFor(() => expect(screen.getByText('Exited (-15)')).toBeInTheDocument())
    expect(fetch).toHaveBeenCalledWith('/api/terminal/sessions/session-1/stop', expect.objectContaining({ method: 'POST' }))
    act(() => Socket.instances[0].onclose?.())
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  })

  it('reconnects to the same session after a lost socket without starting another process', async () => {
    const user = userEvent.setup()
    const fetch = backend({ sessions: [session] })
    render(<TerminalPanel project={project} theme="dark" />)
    await waitFor(() => expect(Socket.instances).toHaveLength(1))
    act(() => { Socket.instances[0].open(); Socket.instances[0].onclose?.() })
    expect(screen.getByRole('alert')).toHaveTextContent('Terminal connection closed.')
    await user.click(screen.getByRole('button', { name: 'Reconnect' }))
    expect(Socket.instances).toHaveLength(2)
    expect(emulator.instances[0].reset).toHaveBeenCalledTimes(2)
    expect(Socket.instances[1].url).toBe(Socket.instances[0].url)
    act(() => Socket.instances[1].open())
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
    expect(fetch.mock.calls.every(([, init]) => init?.method !== 'POST')).toBe(true)
  })

  it('clamps PTY dimensions to server bounds for start and resize', async () => {
    const user = userEvent.setup()
    const fetch = backend()
    render(<TerminalPanel project={project} theme="dark" />)
    await waitFor(() => expect(screen.getByRole('button', { name: 'Start terminal' })).toBeEnabled())
    emulator.instances[0].cols = 900
    emulator.instances[0].rows = 400
    await user.click(screen.getByRole('button', { name: 'Start terminal' }))
    await waitFor(() => expect(Socket.instances).toHaveLength(1))
    const request = fetch.mock.calls.find(([url, init]) => url === '/api/terminal/sessions' && init?.method === 'POST')
    expect(JSON.parse(request![1]!.body as string)).toMatchObject({ cols: 500, rows: 200 })
    emulator.instances[0].cols = 0
    emulator.instances[0].rows = 0
    act(() => Socket.instances[0].open())
    expect(Socket.instances[0].send).toHaveBeenCalledWith(JSON.stringify({ type: 'resize', cols: 2, rows: 2 }))
  })

  it('ignores a pending launch response after switching to another project', async () => {
    const user = userEvent.setup()
    const fetch = backend()
    let complete: (response: Response) => void = () => {}
    const pending = new Promise<Response>(resolve => { complete = resolve })
    const normalFetch = fetch.getMockImplementation()!
    fetch.mockImplementation((url, init) => url === '/api/terminal/sessions' && init?.method === 'POST' ? pending : normalFetch(url, init))
    const view = render(<TerminalPanel project={project} theme="dark" />)
    await waitFor(() => expect(screen.getByRole('button', { name: 'Start terminal' })).toBeEnabled())
    await user.click(screen.getByRole('button', { name: 'Start terminal' }))
    const other = { name: 'Other', path: '/home/alice/Documents/other' }
    view.rerender(<TerminalPanel project={other} theme="dark" />)
    await waitFor(() => expect(screen.getByRole('button', { name: 'Start terminal' })).toBeEnabled())
    await act(async () => { complete(Response.json(session)); await pending })
    expect(Socket.instances).toHaveLength(0)
    expect(screen.queryByText('PID 2345')).not.toBeInTheDocument()
  })

  it('does not attach the previous process or accept its pending stop after a project change', async () => {
    const user = userEvent.setup()
    const fetch = backend({ sessions: [session] })
    let complete: (response: Response) => void = () => {}
    const pending = new Promise<Response>(resolve => { complete = resolve })
    const normalFetch = fetch.getMockImplementation()!
    fetch.mockImplementation((url, init) => url.endsWith('/stop') ? pending : normalFetch(url, init))
    const view = render(<TerminalPanel project={project} theme="dark" />)
    await waitFor(() => expect(Socket.instances).toHaveLength(1))
    await user.click(screen.getByRole('button', { name: 'Stop terminal' }))
    view.rerender(<TerminalPanel project={{ name: 'Other', path: '/home/alice/Documents/other' }} theme="dark" />)
    await waitFor(() => expect(screen.getByRole('button', { name: 'Start terminal' })).toBeEnabled())
    await act(async () => { complete(Response.json({ ...session, state: 'exited', exit_code: -15 })); await pending })
    expect(Socket.instances).toHaveLength(1)
    expect(Socket.instances[0].close).toHaveBeenCalled()
    expect(screen.queryByText('PID 2345')).not.toBeInTheDocument()
  })

  it('shows launch failures and allows retrying', async () => {
    const user = userEvent.setup()
    backend({ startError: 'A terminal is already running for this project.' })
    render(<TerminalPanel project={project} theme="dark" />)
    await waitFor(() => expect(screen.getByRole('button', { name: 'Start terminal' })).toBeEnabled())
    await user.click(screen.getByRole('button', { name: 'Start terminal' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('A terminal is already running for this project.')
    expect(screen.getByRole('button', { name: 'Start terminal' })).toBeEnabled()
  })

  it('disables unsupported platforms, missing CLIs and unsupported sandbox modes', async () => {
    backend({ supported: false })
    const first = render(<TerminalPanel project={project} theme="dark" />)
    expect(await screen.findByText(/not supported on this platform/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Start terminal' })).toBeDisabled()
    first.unmount()
    backend({ launchers: [{ ...launcher, installed: false, available: false }] })
    const second = render(<TerminalPanel project={project} theme="dark" />)
    expect(await screen.findByText(/install a supported local cli/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Start terminal' })).toBeDisabled()
    second.unmount()
    backend({ launchers: [{ ...launcher, sandbox_supported: false }] })
    render(<TerminalPanel project={project} theme="dark" />)
    await waitFor(() => expect(screen.getByRole('button', { name: 'Start terminal' })).toBeEnabled())
    expect(screen.getByRole('checkbox', { name: 'Sandbox mode' })).toBeDisabled()
    expect(screen.getByText(/sandbox mode is not available for this cli/i)).toBeInTheDocument()
  })
})

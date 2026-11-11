import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { ProjectWorkflows } from './ProjectWorkflows'

function response(payload: unknown, status = 200) {
  return new Response(JSON.stringify(payload), { status, headers: { 'Content-Type': 'application/json' } })
}

function mockApi(handle: (path: string, options?: RequestInit) => Response | Promise<Response> | undefined = () => undefined) {
  const fetcher = vi.fn(async (url: string, options?: RequestInit) => {
    const result = handle(url, options)
    if (result !== undefined) return result
    if (url.endsWith('/defaults')) return response({ path: '/home/user/Documents' })
    if (url.endsWith('/mcp')) return response({ servers: [] })
    throw new Error(`Unexpected request: ${url}`)
  })
  vi.stubGlobal('fetch', fetcher)
  return fetcher
}

const input = (name: string) => screen.getByLabelText(name) as HTMLInputElement
const submit = () => screen.getAllByRole('button', { name: 'Create project' })[1]

describe('Project workflows', () => {
  it('starts at Documents, browses from that folder and registers the selected project', async () => {
    const project = { id: 'fixture-id', name: 'Mock preview', path: '/projects/mock' }
    const fetcher = mockApi(url => {
      if (url.endsWith('/pick-folder')) return response({ path: project.path })
      if (url.endsWith('/sync')) return response({ action: 'registered', project })
    })
    const complete = vi.fn()
    render(<ProjectWorkflows onComplete={complete}/>)
    fireEvent.click(screen.getByRole('button', { name: 'Add existing project' }))
    await waitFor(() => expect(input('Project folder')).toHaveValue('/home/user/Documents'))
    fireEvent.click(screen.getByRole('button', { name: 'Browse Folder' }))
    await waitFor(() => expect(input('Project folder')).toHaveValue(project.path))
    expect(fetcher.mock.calls.find(([url]) => url.endsWith('/pick-folder'))?.[1]?.body)
      .toBe(JSON.stringify({ initial_path: '/home/user/Documents' }))
    fireEvent.click(screen.getByRole('button', { name: 'Add project' }))
    await waitFor(() => expect(complete).toHaveBeenCalledWith(project))
    expect(fetcher.mock.calls.find(([url]) => url.endsWith('/sync'))?.[1]?.body)
      .toBe(JSON.stringify({ path: project.path }))
    expect(screen.queryByRole('dialog')).toBeNull()
  })

  it('shows the shared folder suggestion and creates with only selected installed MCP servers', async () => {
    const project = { id: 'new-id', name: 'Mi laboratorio', path: '/projects/mi_laboratorio' }
    const fetcher = mockApi(url => {
      if (url.endsWith('/mcp')) return response({ servers: [
        { name: 'marconi', installed: true, description: 'RF tools' },
        { name: 'vsil_hil_mcp', installed: false },
      ] })
      if (url.includes('/folder-name?')) return response({ folder: 'mi_laboratorio', error: null })
      if (url.endsWith('/create')) return response({ project })
    })
    const complete = vi.fn()
    render(<ProjectWorkflows onComplete={complete}/>)
    fireEvent.click(screen.getByRole('button', { name: 'Create project' }))
    await screen.findByRole('checkbox', { name: /marconi/ })
    expect(screen.getByRole('checkbox', { name: /vsil_hil_mcp/ })).toBeDisabled()
    await waitFor(() => expect(input('Choose Folder')).toHaveValue('/home/user/Documents'))
    fireEvent.change(input('Project name'), { target: { value: project.name } })
    fireEvent.change(input('Choose Folder'), { target: { value: '/projects' } })
    await waitFor(() => expect(input('Folder name')).toHaveValue('mi_laboratorio'))
    fireEvent.click(screen.getByRole('checkbox', { name: /marconi/ }))
    fireEvent.click(submit())
    await waitFor(() => expect(complete).toHaveBeenCalledWith(project))
    expect(JSON.parse(fetcher.mock.calls.find(([url]) => url.endsWith('/create'))![1]!.body as string)).toEqual({
      name: project.name, parent_path: '/projects', folder: 'mi_laboratorio', mcp_servers: ['marconi'],
    })
  })

  it('keeps manual folder entry available after the native picker fails', async () => {
    mockApi(url => {
      if (url.endsWith('/pick-folder')) return response({ detail: 'Native folder selection is unavailable.' }, 409)
      if (url.endsWith('/sync')) return response({ detail: 'No project manifest was found.' }, 400)
    })
    const complete = vi.fn()
    render(<ProjectWorkflows onComplete={complete}/>)
    fireEvent.click(screen.getByRole('button', { name: 'Add existing project' }))
    await waitFor(() => expect(screen.getByRole('button', { name: 'Browse Folder' })).toBeEnabled())
    fireEvent.click(screen.getByRole('button', { name: 'Browse Folder' }))
    await screen.findByText(/You can enter the folder path below/)
    expect(input('Project folder')).toBeEnabled()
    fireEvent.change(input('Project folder'), { target: { value: '/not-a-project' } })
    fireEvent.click(screen.getByRole('button', { name: 'Add project' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('No project manifest was found.')
    expect(complete).not.toHaveBeenCalled()
  })

  it('cancels without mutations and returns focus to the opening control', () => {
    const fetcher = mockApi()
    render(<ProjectWorkflows onComplete={vi.fn()}/>)
    const opener = screen.getByRole('button', { name: 'Add existing project' })
    fireEvent.click(opener)
    fireEvent.keyDown(screen.getByRole('dialog'), { key: 'Escape' })
    expect(screen.queryByRole('dialog')).toBeNull()
    expect(document.activeElement).toBe(opener)
    expect(fetcher.mock.calls.every(([, options]) => options?.method !== 'POST')).toBe(true)
  })

  it('preserves a custom folder across name changes and can return to the shared suggestion', async () => {
    mockApi(url => {
      if (url.includes('/folder-name?')) {
        const name = new URL(url, 'http://localhost').searchParams.get('name')
        return response({ folder: name === 'Señales RF' ? 'seales_rf' : 'otro_proyecto', error: null })
      }
    })
    render(<ProjectWorkflows onComplete={vi.fn()}/>)
    fireEvent.click(screen.getByRole('button', { name: 'Create project' }))
    fireEvent.change(input('Project name'), { target: { value: 'Señales RF' } })
    await waitFor(() => expect(input('Folder name')).toHaveValue('seales_rf'))
    fireEvent.change(input('Folder name'), { target: { value: 'custom' } })
    fireEvent.change(input('Project name'), { target: { value: 'Otro proyecto' } })
    expect(input('Folder name')).toHaveValue('custom')
    fireEvent.change(input('Folder name'), { target: { value: '' } })
    await waitFor(() => expect(input('Folder name')).toHaveValue('otro_proyecto'))
  })

  it('never submits an old suggestion while a newer name is waiting', async () => {
    const pending = new Map<string, (value: Response) => void>()
    const fetcher = mockApi(url => {
      if (url.includes('/folder-name?')) return new Promise<Response>(resolve => {
        pending.set(new URL(url, 'http://localhost').searchParams.get('name')!, resolve)
      })
    })
    render(<ProjectWorkflows onComplete={vi.fn()}/>)
    fireEvent.click(screen.getByRole('button', { name: 'Create project' }))
    await waitFor(() => expect(input('Choose Folder')).toHaveValue('/home/user/Documents'))
    fireEvent.change(input('Project name'), { target: { value: 'Old' } })
    fireEvent.change(input('Project name'), { target: { value: 'Current' } })
    expect(submit()).toBeDisabled()
    pending.get('Old')!(response({ folder: 'old', error: null }))
    await waitFor(() => expect(input('Folder name')).toHaveValue(''))
    expect(submit()).toBeDisabled()
    expect(fetcher.mock.calls.some(([url]) => url.endsWith('/create'))).toBe(false)
    pending.get('Current')!(response({ folder: 'current', error: null }))
    await waitFor(() => expect(input('Folder name')).toHaveValue('current'))
    expect(submit()).toBeEnabled()
  })

  it('allows an explicit folder when the shared naming rule cannot derive one', async () => {
    mockApi(url => url.includes('/folder-name?')
      ? response({ folder: '', error: 'Cannot derive a folder name.' }) : undefined)
    render(<ProjectWorkflows onComplete={vi.fn()}/>)
    fireEvent.click(screen.getByRole('button', { name: 'Create project' }))
    fireEvent.change(input('Project name'), { target: { value: '!!!' } })
    await screen.findByText(/Cannot derive a folder name/)
    expect(submit()).toBeDisabled()
    fireEvent.change(input('Folder name'), { target: { value: 'my_project' } })
    expect(submit()).toBeEnabled()
  })

  it('keeps a manually entered path when a slow defaults request finishes', async () => {
    let resolveDefault!: (value: Response) => void
    mockApi(url => url.endsWith('/defaults') ? new Promise<Response>(resolve => { resolveDefault = resolve }) : undefined)
    render(<ProjectWorkflows onComplete={vi.fn()}/>)
    fireEvent.click(screen.getByRole('button', { name: 'Add existing project' }))
    fireEvent.change(input('Project folder'), { target: { value: '/chosen' } })
    resolveDefault(response({ path: '/home/user/Documentos' }))
    await waitFor(() => expect(screen.getByRole('button', { name: 'Browse Folder' })).toBeEnabled())
    expect(input('Project folder')).toHaveValue('/chosen')
  })
})

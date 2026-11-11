import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { ProjectWorkflows } from './ProjectWorkflows'

function response(payload: unknown, status = 200) {
  return new Response(JSON.stringify(payload), { status, headers: { 'Content-Type': 'application/json' } })
}

afterEach(() => { cleanup(); vi.unstubAllGlobals() })

describe('Project workflows', () => {
  it('selects an existing folder and registers the returned project', async () => {
    const project = { id: 'fixture-id', name: 'Mock preview', path: '/projects/mock' }
    const fetcher = vi.fn()
      .mockResolvedValueOnce(response({ path: project.path }))
      .mockResolvedValueOnce(response({ action: 'registered', project }))
    vi.stubGlobal('fetch', fetcher)
    const complete = vi.fn()
    render(<ProjectWorkflows onComplete={complete}/>)
    fireEvent.click(screen.getByRole('button', { name: 'Add existing project' }))
    fireEvent.click(screen.getByRole('button', { name: 'Browse folders' }))
    await waitFor(() => expect((screen.getByLabelText(/Project folder/) as HTMLInputElement).value).toBe(project.path))
    fireEvent.click(screen.getByRole('button', { name: 'Add project' }))
    await waitFor(() => expect(complete).toHaveBeenCalledWith(project))
    expect(JSON.parse(fetcher.mock.calls[1][1].body)).toEqual({ path: project.path })
    expect(screen.queryByRole('dialog')).toBeNull()
  })

  it('creates a project with only selected installed MCP servers', async () => {
    const project = { id: 'new-id', name: 'Mi laboratorio', path: '/projects/mi_laboratorio' }
    const fetcher = vi.fn()
      .mockResolvedValueOnce(response({ servers: [
        { name: 'marconi', installed: true, description: 'RF tools' },
        { name: 'vsil_hil_mcp', installed: false },
      ] }))
      .mockResolvedValueOnce(response({ project }))
    vi.stubGlobal('fetch', fetcher)
    const complete = vi.fn()
    render(<ProjectWorkflows onComplete={complete}/>)
    fireEvent.click(screen.getByRole('button', { name: 'Create project' }))
    await screen.findByRole('checkbox', { name: /marconi/ })
    expect((screen.getByRole('checkbox', { name: /vsil_hil_mcp/ }) as HTMLInputElement).disabled).toBe(true)
    fireEvent.change(screen.getByLabelText('Project name'), { target: { value: project.name } })
    fireEvent.change(screen.getByLabelText(/Parent folder/), { target: { value: '/projects' } })
    fireEvent.click(screen.getByRole('checkbox', { name: /marconi/ }))
    fireEvent.click(screen.getAllByRole('button', { name: 'Create project' })[1])
    await waitFor(() => expect(complete).toHaveBeenCalledWith(project))
    expect(JSON.parse(fetcher.mock.calls[1][1].body)).toEqual({
      name: project.name, parent_path: '/projects', mcp_servers: ['marconi'],
    })
  })

  it('keeps manual folder entry available after the native picker fails', async () => {
    const fetcher = vi.fn()
      .mockResolvedValueOnce(response({ detail: 'Native folder selection is unavailable.' }, 409))
      .mockResolvedValueOnce(response({ detail: 'No project manifest was found.' }, 400))
    vi.stubGlobal('fetch', fetcher)
    const complete = vi.fn()
    render(<ProjectWorkflows onComplete={complete}/>)
    fireEvent.click(screen.getByRole('button', { name: 'Add existing project' }))
    fireEvent.click(screen.getByRole('button', { name: 'Browse folders' }))
    await screen.findByText(/You can enter the folder path below/)
    const folder = screen.getByLabelText(/Project folder/) as HTMLInputElement
    expect(folder.disabled).toBe(false)
    fireEvent.change(folder, { target: { value: '/not-a-project' } })
    fireEvent.click(screen.getByRole('button', { name: 'Add project' }))
    expect((await screen.findByRole('alert')).textContent).toBe('No project manifest was found.')
    expect(complete).not.toHaveBeenCalled()
  })

  it('cancels without registering and returns focus to the opening control', () => {
    const fetcher = vi.fn()
    vi.stubGlobal('fetch', fetcher)
    render(<ProjectWorkflows onComplete={vi.fn()}/>)
    const opener = screen.getByRole('button', { name: 'Add existing project' })
    fireEvent.click(opener)
    fireEvent.keyDown(screen.getByRole('dialog'), { key: 'Escape' })
    expect(screen.queryByRole('dialog')).toBeNull()
    expect(document.activeElement).toBe(opener)
    expect(fetcher).not.toHaveBeenCalled()
  })
})

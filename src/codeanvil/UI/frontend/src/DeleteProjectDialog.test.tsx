import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { DeleteProjectDialog } from './DeleteProjectDialog'

const project = { id: 'project-id', name: 'My project', path: '/projects/my_project' }

describe('Delete project confirmation', () => {
  it('shows the exact target, keeps files by default and cancels without a request', async () => {
    const user = userEvent.setup()
    const fetcher = vi.fn()
    const close = vi.fn()
    vi.stubGlobal('fetch', fetcher)
    render(<DeleteProjectDialog project={project} onClose={close} onDeleted={vi.fn()}/>)
    expect(screen.getByText(project.path)).toBeInTheDocument()
    expect(screen.getByRole('checkbox')).not.toBeChecked()
    expect(screen.getByRole('heading', { name: 'Are you sure you want to delete?' })).toBeInTheDocument()
    expect(screen.queryByRole('textbox')).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Delete' })).toBeEnabled()
    expect(screen.getByRole('button', { name: 'Cancel' })).toHaveFocus()
    await user.keyboard('{Escape}')
    expect(close).toHaveBeenCalledOnce()
    expect(fetcher).not.toHaveBeenCalled()
  })

  it.each([false, true])('confirms with a click and sends the explicit remove_files=%s choice', async removeFiles => {
    const user = userEvent.setup()
    const deleted = vi.fn()
    const fetcher = vi.fn().mockResolvedValue(new Response(JSON.stringify({ project, removed_files: removeFiles })))
    vi.stubGlobal('fetch', fetcher)
    render(<DeleteProjectDialog project={project} onClose={vi.fn()} onDeleted={deleted}/>)
    if (removeFiles) {
      await user.click(screen.getByRole('checkbox'))
      expect(screen.getByRole('note')).toHaveTextContent('permanently deletes all files')
    }
    await user.click(screen.getByRole('button', { name: 'Delete' }))
    expect(deleted).toHaveBeenCalledOnce()
    expect(fetcher).toHaveBeenCalledWith('/api/workflows/delete', expect.objectContaining({
      method: 'POST', body: JSON.stringify({
        project_id: project.id, expected_path: project.path, remove_files: removeFiles,
        confirm: true, confirmation_name: project.name,
      }),
    }))
  })

  it('leaves the dialog and selection available when the server rejects deletion', async () => {
    const user = userEvent.setup()
    const deleted = vi.fn()
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify({ detail: 'The project path changed. Reload and retry.' }), { status: 409 })))
    render(<DeleteProjectDialog project={project} onClose={vi.fn()} onDeleted={deleted}/>)
    await user.click(screen.getByRole('button', { name: 'Delete' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('The project path changed')
    expect(screen.getByRole('dialog')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Delete' })).toBeEnabled()
    expect(deleted).not.toHaveBeenCalled()
  })

  it('traps keyboard focus and never enables deletion without a registry ID', async () => {
    const user = userEvent.setup()
    render(<DeleteProjectDialog project={{ name: project.name, path: project.path }} onClose={vi.fn()} onDeleted={vi.fn()}/>)
    const cancel = screen.getByRole('button', { name: 'Cancel' })
    cancel.focus()
    await user.tab()
    expect(screen.getByRole('button', { name: 'Close delete dialog' })).toHaveFocus()
    expect(screen.getByRole('button', { name: 'Delete' })).toBeDisabled()
  })

  it('keeps focus inside the busy dialog and waits for server completion', async () => {
    const user = userEvent.setup()
    let finish!: (value: Response) => void
    const close = vi.fn()
    const deleted = vi.fn()
    const fetcher = vi.fn(() => new Promise<Response>(resolve => { finish = resolve }))
    vi.stubGlobal('fetch', fetcher)
    render(<DeleteProjectDialog project={project} onClose={close} onDeleted={deleted}/>)
    await user.click(screen.getByRole('button', { name: 'Delete' }))
    expect(screen.getByRole('button', { name: 'Deleting…' })).toBeDisabled()
    await user.keyboard('{Escape}')
    await user.tab()
    expect(screen.getByRole('dialog')).toHaveFocus()
    expect(close).not.toHaveBeenCalled()
    expect(deleted).not.toHaveBeenCalled()
    expect(fetcher).toHaveBeenCalledOnce()
    finish(new Response(JSON.stringify({ project, removed_files: false })))
    await waitFor(() => expect(deleted).toHaveBeenCalledOnce())
  })
})

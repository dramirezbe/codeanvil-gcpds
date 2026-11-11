import { useEffect, useRef, useState } from 'react'
import type { FormEvent, KeyboardEvent } from 'react'
import { X } from 'lucide-react'
import type { Project } from './api'
import './styles/project-delete.css'

export function DeleteProjectDialog({ project, onClose, onDeleted }: {
  project: Project
  onClose: () => void
  onDeleted: () => void
}) {
  const [removeFiles, setRemoveFiles] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const dialog = useRef<HTMLDivElement>(null)
  const cancel = useRef<HTMLButtonElement>(null)
  const canDelete = !!project.id

  useEffect(() => { cancel.current?.focus() }, [])
  useEffect(() => { if (busy) dialog.current?.focus() }, [busy])

  function keyDown(event: KeyboardEvent<HTMLDivElement>) {
    if (event.key === 'Escape' && !busy) {
      event.stopPropagation()
      onClose()
    }
    if (event.key !== 'Tab') return
    if (busy) {
      event.preventDefault()
      return
    }
    const controls = Array.from(dialog.current?.querySelectorAll<HTMLElement>(
      'button:not(:disabled), input:not(:disabled)',
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

  async function submit(event: FormEvent) {
    event.preventDefault()
    if (!canDelete || busy) return
    setBusy(true)
    setError('')
    try {
      const response = await fetch('/api/workflows/delete', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          project_id: project.id, expected_path: project.path, remove_files: removeFiles,
          confirm: true, confirmation_name: project.name,
        }),
      })
      const result = await response.json()
      if (!response.ok) throw new Error(typeof result.detail === 'string' ? result.detail : `Deletion failed (${response.status}).`)
      if (result.project?.id !== project.id) throw new Error('The server did not confirm the selected project was deleted.')
      onDeleted()
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Could not delete the project.')
      setBusy(false)
    }
  }

  return <div className="dialog-backdrop">
    <div className="dialog-surface delete-project-dialog" role="dialog" aria-modal="true" tabIndex={-1}
      aria-labelledby="delete-project-title" aria-describedby="delete-project-effect" ref={dialog} onKeyDown={keyDown}>
      <div className="panel-head">
        <h2 id="delete-project-title">Are you sure you want to delete?</h2>
        <button type="button" className="icon-btn" aria-label="Close delete dialog" disabled={busy} onClick={onClose}><X size={18}/></button>
      </div>
      <p className="delete-project-name">{project.name}</p>
      <code className="delete-project-path">{project.path}</code>
      <p id="delete-project-effect" className="workflow-help">Remove this project from CodeAnvil's project list. Its folder and files will be kept unless you select the option below.</p>
      <form onSubmit={submit} aria-busy={busy}>
        <fieldset className="workflow-fields" disabled={busy}>
          <label className="confirm-action">
            <input type="checkbox" checked={removeFiles} onChange={event => setRemoveFiles(event.target.checked)}/>
            <span>Also delete the project folder and its contents</span>
          </label>
          {removeFiles && <p className="delete-files-warning" role="note">This permanently deletes all files in the folder shown above, including source code and reports.</p>}
        </fieldset>
        {error && <p className="workflow-error" role="alert">{error}</p>}
        <div className="workflow-actions">
          <button ref={cancel} type="button" className="secondary-button" disabled={busy} onClick={onClose}>Cancel</button>
          <button type="submit" className="secondary-button destructive-button" disabled={!canDelete || busy}>{busy ? 'Deleting…' : 'Delete'}</button>
        </div>
      </form>
    </div>
  </div>
}

import { useEffect, useState } from 'react'
import { request, workspaceUrl } from './api'

type BackupListing = { backups: Record<string, [string, number | null, string][]> }

export function BackupsView({ projectPath }: { projectPath: string }) {
  const [listing, setListing] = useState<BackupListing | null>(null)
  const [error, setError] = useState('')
  useEffect(() => {
    const controller = new AbortController()
    request<BackupListing>(workspaceUrl('backups', projectPath), controller.signal)
      .then(value => { if (!controller.signal.aborted) setListing(value) })
      .catch(reason => { if (!controller.signal.aborted) setError(reason.message) })
    return () => controller.abort()
  }, [projectPath])
  return <div className="workspace workspace-canvas"><div className="page-head"><div>
    <div className="eyebrow">SAVED ARTIFACTS</div><h1>Backups</h1><p className="lede">Latest saved artifact per stage and producing cycle.</p>
  </div></div><section className="content-panel backup-list">
    {error ? <p role="alert">{error}</p> : !listing ? <p role="status">Loading backups…</p>
      : !Object.keys(listing.backups).length ? <div className="viewer-empty"><h2>No backups yet</h2><p>Backups appear when a stage saves its previous working artifacts before rework.</p></div>
      : Object.entries(listing.backups).map(([cycle, entries]) => <div key={cycle}><h2>{cycle}</h2>
        {entries.map(([stage, iteration, path]) => <div className="backup-entry" key={path}>
          <strong>{stage}{iteration ? ` · iteration ${iteration}` : ' · unknown producer'}</strong><code>.codeanvil/backups/{path}/</code>
        </div>)}
      </div>)}
  </section></div>
}

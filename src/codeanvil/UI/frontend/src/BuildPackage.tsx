import { useEffect, useRef, useState } from 'react'
import { ChevronLeft, ChevronRight, FileText, Upload, X } from 'lucide-react'
import { ArtifactViewer, MarkdownContent } from './ArtifactViewer'
import { type Artifact, request, workspaceUrl } from './api'
import './styles/build-package.css'

const endpoint = 'build-package'
const dateFormat = new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' })
type Upload = { batch: string; index: number; name: string; archive: string | null; uploaded_at: string }
type Existing = { path: string; name: string; modified_at: string }
type SourceDocument = Upload | Existing
type Inventory = { files: SourceDocument[] }
type Preview =
  | { format: 'markdown' | 'text'; content: string; clipped: boolean }
  | { format: 'table'; rows: string[][]; sheets: string[]; sheet: number; clipped: boolean }
  | { format: 'pdf'; pages: number }

function identity(file: SourceDocument) {
  return 'path' in file ? `existing:${file.path}` : `${file.batch}/${file.index}`
}

function previewUrl(file: SourceDocument, action: string, projectPath: string, extra: Record<string, string>) {
  return 'path' in file
    ? workspaceUrl(`${endpoint}/existing/${action}`, projectPath, { path: file.path, ...extra })
    : workspaceUrl(`${endpoint}/${identity(file)}/${action}`, projectPath, extra)
}

export function BuildPackage({ artifact, projectPath, revision }: {
  artifact: Artifact; projectPath: string; revision: number
}) {
  const [files, setFiles] = useState<SourceDocument[]>([])
  const [selected, setSelected] = useState<SourceDocument | null>(null)
  const [opened, setOpened] = useState<SourceDocument | null>(null)
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState('')
  const picker = useRef<HTMLInputElement>(null)
  const url = workspaceUrl(endpoint, projectPath)

  useEffect(() => {
    const controller = new AbortController()
    setLoading(true)
    setError('')
    request<Inventory>(url, controller.signal)
      .then(result => { if (!controller.signal.aborted) setFiles(result.files) })
      .catch(reason => { if (!controller.signal.aborted) setError(reason.message) })
      .finally(() => { if (!controller.signal.aborted) setLoading(false) })
    return () => controller.abort()
  }, [url, revision])

  async function upload(chosen: File[]) {
    if (!chosen.length) return
    setUploading(true)
    setError('')
    const body = new FormData()
    for (const file of chosen) body.append('files', file)
    try {
      const response = await fetch(url, { method: 'POST', body })
      const result = await response.json()
      if (!response.ok) throw new Error(typeof result.detail === 'string' ? result.detail : 'Upload failed.')
      setFiles(current => [...result.files, ...current])
      setSelected(result.files[0] ?? null)
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Upload failed.')
    } finally {
      setUploading(false)
    }
  }

  return <section className="artifact-viewer build-package" aria-label="Build Package">
    <header className="artifact-toolbar">
      <div className="artifact-title"><strong>Build Package</strong><small>Source documents · shared across cycles</small></div>
      <input type="file" multiple hidden ref={picker} aria-label="Build Package files" onChange={event => {
        const chosen = Array.from(event.currentTarget.files ?? [])
        event.currentTarget.value = ''
        void upload(chosen)
      }} />
      <button type="button" className="primary-button" disabled={loading || uploading} onClick={() => picker.current?.click()}>
        <Upload size={15} />{uploading ? 'Uploading…' : 'Upload Build Package'}
      </button>
    </header>
    {error && <p className="build-notice error-state" role="alert">{error}</p>}
    <div className="build-layout">
      <div className="build-inventory">
        <div className="build-list-toolbar">
          <b>Documents</b>
          <button className="secondary-button small" disabled={!selected} onClick={() => setOpened(selected)}>Open preview</button>
        </div>
        {loading ? <p className="build-notice" role="status">Loading documents…</p>
          : !files.length ? <p className="build-notice">Upload documents or an archive to get started.</p>
            : <div className="build-files" aria-label="Build Package documents">
              {files.map(file => <button type="button" className="build-file" key={identity(file)}
                aria-pressed={Boolean(selected && identity(selected) === identity(file))}
                title={`Double-click to preview ${file.name}`}
                onClick={event => { setSelected(file); if (event.detail === 0) setOpened(file) }}
                onDoubleClick={() => { setSelected(file); setOpened(file) }}>
                <FileText size={16} />
                <span>
                  <b>{file.name}</b>
                  {'path' in file
                    ? <time dateTime={file.modified_at}>Modified · {dateFormat.format(new Date(file.modified_at))}</time>
                    : <time dateTime={file.uploaded_at}>Uploaded · {dateFormat.format(new Date(file.uploaded_at))}</time>}
                  {'archive' in file && file.archive && <small>From {file.archive}</small>}
                </span>
              </button>)}
            </div>}
      </div>
      {opened ? <DocumentPreview key={identity(opened)} file={opened} projectPath={projectPath} onClose={() => setOpened(null)} />
        : artifact.exists ? <ArtifactViewer artifact={artifact} projectPath={projectPath} revision={revision} />
          : <div className="viewer-empty"><h2>Document preview</h2><p>Double-click a document to open it here.</p></div>}
    </div>
  </section>
}

function DocumentPreview({ file, projectPath, onClose }: { file: SourceDocument; projectPath: string; onClose: () => void }) {
  const [preview, setPreview] = useState<Preview | null>(null)
  const [sheet, setSheet] = useState(0)
  const [page, setPage] = useState(1)
  const [pdfError, setPdfError] = useState(false)
  const [error, setError] = useState('')
  const url = previewUrl(file, 'preview', projectPath, { sheet: String(sheet) })

  useEffect(() => {
    const controller = new AbortController()
    setError('')
    request<Preview>(url, controller.signal)
      .then(result => { if (!controller.signal.aborted) setPreview(result) })
      .catch(reason => { if (!controller.signal.aborted) setError(reason.message) })
    return () => controller.abort()
  }, [url])

  return <section className="artifact-viewer build-document" aria-label="Document preview">
    <header className="artifact-toolbar">
      <div className="artifact-title"><strong>{file.name}</strong></div>
      <button className="icon-btn" onClick={onClose} title="Close preview" aria-label="Close preview"><X size={16} /></button>
    </header>
    {error ? <p className="build-notice error-state" role="alert">{error}</p>
      : !preview ? <p className="build-notice" role="status">Opening preview…</p>
        : preview.format === 'pdf' ? <>
          <div className="build-page-controls" aria-label="PDF pages">
            <button className="secondary-button small" aria-label="Previous page" disabled={page <= 1}
              onClick={() => { setPdfError(false); setPage(page - 1) }}><ChevronLeft size={15} /></button>
            <span>Page {preview.pages ? page : 0} of {preview.pages}</span>
            <button className="secondary-button small" aria-label="Next page" disabled={page >= preview.pages}
              onClick={() => { setPdfError(false); setPage(page + 1) }}><ChevronRight size={15} /></button>
          </div>
          {pdfError && <p className="build-notice error-state" role="alert">Could not render this PDF page.</p>}
          {preview.pages > 0 && !pdfError && <div className="build-pdf">
            <img key={page} alt={`Page ${page} of ${file.name}`}
              onError={() => setPdfError(true)} src={previewUrl(file, 'pdf-page', projectPath, { page: String(page) })} />
          </div>}
        </> : <>
          {preview.clipped && <p className="build-notice" role="status">Showing the beginning of this document.</p>}
          {preview.format === 'table' ? <>
            {preview.sheets.length > 0 && <label className="build-sheet">Worksheet
              <select value={sheet} onChange={event => setSheet(Number(event.target.value))}>
                {preview.sheets.map((name, index) => <option key={index} value={index}>{name}</option>)}
              </select>
            </label>}
            {preview.rows.length > 0 ? <div className="build-table"><table aria-label="Document cells"><tbody>
              {preview.rows.map((row, i) => <tr key={i}><th scope="row">{i + 1}</th>
                {row.map((value, j) => <td key={j}>{value}</td>)}
              </tr>)}
            </tbody></table></div> : <p className="build-notice">This sheet has no visible rows.</p>}
          </> : <article className="markdown-body">
            {preview.format === 'markdown' ? <MarkdownContent content={preview.content} /> : <pre>{preview.content}</pre>}
          </article>}
        </>}
  </section>
}

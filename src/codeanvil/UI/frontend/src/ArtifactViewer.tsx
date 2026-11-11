import { useEffect, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { type Artifact, type ArtifactDocument, request, workspaceUrl } from './api'

export function ArtifactViewer({ artifact, projectPath, revision = 0 }: {
  artifact: Artifact | null
  projectPath: string
  revision?: number
}) {
  const [document, setDocument] = useState<ArtifactDocument | null>(null)
  const [iteration, setIteration] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const identity = `${projectPath}:${artifact?.path ?? ''}`

  useEffect(() => {
    setIteration('')
    setDocument(null)
    setError('')
  }, [identity])

  useEffect(() => {
    if (!artifact?.exists) {
      setDocument(null)
      setError('')
      setLoading(false)
      return
    }
    const controller = new AbortController()
    setLoading(true)
    setError('')
    request<ArtifactDocument>(workspaceUrl('artifact', projectPath, {
      path: artifact.path,
      ...(iteration ? { iteration } : {}),
    }), controller.signal)
      .then(value => { if (!controller.signal.aborted) setDocument(value) })
      .catch(reason => { if (!controller.signal.aborted) setError(reason.message) })
      .finally(() => { if (!controller.signal.aborted) setLoading(false) })
    return () => controller.abort()
  }, [identity, artifact?.exists, iteration, revision])

  if (!artifact) return <div className="viewer-empty">No artifacts are available in this view.</div>

  return <section className="artifact-viewer" aria-label="Artifact viewer">
    <header className="artifact-toolbar">
      <div className="artifact-title"><strong>{artifact.label}</strong><small>{artifact.path}</small></div>
      {artifact.working_copy && <span className="tag tag-muted">Working copy · shared across cycles</span>}
      {document && document.iterations.length > 0 && <label className="iteration-control">
        <span>Iteration</span>
        <select aria-label="Report iteration" value={iteration} onChange={event => setIteration(event.target.value)}>
          <option value="">All iterations</option>
          {document.iterations.map(item => <option key={item.number} value={item.number}>
            Iteration {item.number} · {item.hitl || 'No verdict'}
          </option>)}
        </select>
      </label>}
    </header>
    {!artifact.exists ? <div className="viewer-empty"><h2>Not produced yet</h2><p>{artifact.label} does not exist in this project yet.</p></div>
      : loading ? <div className="viewer-empty" role="status">Loading artifact…</div>
      : error ? <div className="viewer-empty error-state" role="alert"><h2>Could not open artifact</h2><p>{error}</p></div>
      : document?.format === 'html' ? <iframe className="document-frame" title={artifact.label} sandbox="allow-scripts" srcDoc={document.content} />
      : document ? <article className="markdown-body">
        {document.format === 'markdown'
          ? <ReactMarkdown remarkPlugins={[remarkGfm]} skipHtml components={{
            a: ({ children, href }) => {
              const external = href?.startsWith('https://') || href?.startsWith('http://')
              return <a href={href} target={external ? '_blank' : undefined} rel={external ? 'noopener noreferrer' : undefined}>{children}</a>
            },
            img: ({ alt }) => <span className="image-placeholder">{alt || 'Image'} · external images are not loaded automatically</span>,
          }}>{document.content}</ReactMarkdown>
          : <pre>{document.content}</pre>}
      </article> : null}
  </section>
}

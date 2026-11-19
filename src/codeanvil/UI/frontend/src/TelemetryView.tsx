import { useEffect, useMemo, useRef, useState } from 'react'
import { Activity, AlertTriangle, FileText, Gauge, RefreshCw, Thermometer } from 'lucide-react'
import uPlot from 'uplot'
import 'uplot/dist/uPlot.min.css'
import { type MachineMeasurement, type TelemetrySample, type TelemetryStream, type WorkspaceEvidence, request, workspaceUrl } from './api'

type Metric = { key: string; label: string; unit: string }

function numericLeaves(value: unknown, prefix = ''): [string, number][] {
  if (typeof value === 'number' && Number.isFinite(value)) return prefix ? [[prefix, value]] : []
  if (!value || typeof value !== 'object' || Array.isArray(value) || 'unavailable' in value) return []
  return Object.entries(value).flatMap(([key, child]) => numericLeaves(child, prefix ? `${prefix}.${key}` : key))
}

function metricsFor(sample: TelemetrySample): [string, number][] {
  return ['process', 'system', 'temperature_c', 'counters'].flatMap(section =>
    numericLeaves((sample as Record<string, unknown>)[section], section))
}

function metricLabel(key: string): Metric {
  const known: Record<string, [string, string]> = {
    'process.cpu_percent': ['Process CPU', '%'],
    'process.rss_bytes': ['Process memory', 'bytes'],
    'process.memory_percent': ['Process memory share', '%'],
    'process.processes': ['Processes', 'count'],
    'system.cpu_percent': ['System CPU', '%'],
    'system.memory_percent': ['System memory', '%'],
    'system.memory_used_bytes': ['System memory used', 'bytes'],
    'system.memory_total_bytes': ['System memory total', 'bytes'],
    'temperature_c.value': ['Temperature', '°C'],
  }
  const [label, unit] = known[key] || [key.replaceAll('_', ' ').replaceAll('.', ' · '), '']
  return { key, label, unit }
}

function formatValue(value: number | null | undefined, unit: string) {
  if (value == null) return '—'
  const shown = unit === 'bytes' ? `${(value / 1024 / 1024).toFixed(1)} MB` : `${Number(value.toFixed(2))}${unit ? ` ${unit}` : ''}`
  return shown
}

function TelemetryPlot({ stream, metric }: { stream: TelemetryStream; metric: Metric }) {
  const values = useMemo(() => stream.samples.map(sample =>
    new Map(metricsFor(sample)).get(metric.key) ?? null), [stream, metric.key])
  const present = values.filter((value): value is number => value !== null)
  const mount = useRef<HTMLDivElement>(null)
  const plot = useRef<uPlot | null>(null)
  const low = present.length ? Math.min(...present) : 0, high = present.length ? Math.max(...present) : 0
  const mean = present.length ? present.reduce((sum, value) => sum + value, 0) / present.length : 0
  const timed = stream.samples.length > 0 && stream.samples.every(sample => sample.timestamp && Number.isFinite(Date.parse(sample.timestamp)))
  const xValues = useMemo(() => stream.samples.map((sample, index) =>
    timed ? Date.parse(sample.timestamp!) / 1000 : index), [stream, timed])
  const xMin = Math.min(...xValues), xMax = Math.max(...xValues)
  const xPad = xMin === xMax ? (timed ? 1 : 0.5) : 0
  const yPad = high === low ? Math.max(Math.abs(high) * 0.08, 1) : (high - low) * 0.08

  useEffect(() => {
    const target = mount.current
    if (!target || !present.length) return
    const palette = getComputedStyle(target)
    const lineColor = palette.getPropertyValue('--line').trim() || '#354148'
    const labelColor = palette.getPropertyValue('--muted').trim() || '#87949b'
    const accent = palette.getPropertyValue('--cyan').trim() || '#59c9e8'
    const timestamps: uPlot.AlignedData = [xValues, values]
    const options: uPlot.Options = {
      width: Math.max(220, target.clientWidth), height: 270,
      scales: { x: { time: timed } },
      cursor: { drag: { setScale: true }, points: { size: 7, fill: accent } },
      legend: { show: true, live: true },
      axes: [
        { stroke: labelColor, grid: { stroke: lineColor, width: 1 }, ticks: { stroke: lineColor, width: 1 },
          values: timed ? (_plot, ticks) => ticks.map(value => new Date(value * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }))
            : (_plot, ticks) => ticks.map(value => `#${Math.round(value) + 1}`) },
        { stroke: labelColor, grid: { stroke: lineColor, width: 1 }, ticks: { stroke: lineColor, width: 1 },
          values: (_plot, ticks) => ticks.map(value => metric.unit === 'bytes' ? `${(value / 1048576).toFixed(1)} MB` : `${Number(value.toFixed(2))}${metric.unit ? ` ${metric.unit}` : ''}`) },
      ],
      series: [
        {},
        { label: metric.label, stroke: accent, width: 2, spanGaps: false, points: { show: false },
          value: (_plot, value) => formatValue(value, metric.unit) },
      ],
    }
    const chart = new uPlot(options, timestamps, target)
    plot.current = chart
    const resize = () => {
      const width = target.clientWidth
      if (width > 0) chart.setSize({ width: Math.max(220, width), height: 270 })
    }
    const observer = new ResizeObserver(resize)
    observer.observe(target)
    return () => { observer.disconnect(); chart.destroy(); plot.current = null }
  }, [metric.key, metric.label, metric.unit, stream, timed, values, xValues])

  if (!present.length) return <div className="plot-empty">This signal is unavailable in this run.</div>
  return <div className="telemetry-plot-wrap">
    <div className="plot-stats">
      <span>MIN <b>{formatValue(low, metric.unit)}</b></span>
      <span>MEAN <b>{formatValue(mean, metric.unit)}</b></span>
      <span>MAX <b>{formatValue(high, metric.unit)}</b></span>
    </div>
    <div className="uplot-host" ref={mount} role="img" aria-label={`${metric.label} across ${present.length} telemetry samples`}/>
    <div className="plot-footer"><p className="plot-footnote">{present.length} measured points · {stream.samples.length} samples · {timed ? 'UTC/local time' : 'sample index'} · {metric.unit || 'unit not declared'}</p>
      <button className="small secondary-button" onClick={() => { plot.current?.setScale('x', { min: xMin - xPad, max: xMax + xPad }); plot.current?.setScale('y', { min: low - yPad, max: high + yPad }) }}>Reset zoom</button></div>
  </div>
}

function ResultTag({ value, level }: { value: string; level?: 'VL-2' }) {
  const scoped = level && value.match(/\bVL-2\s*:?\s+([^;]+)/i)?.[1]
  const result = scoped || value
  const kind = /\b(?:fail(?:ed)?|blocked)\b/i.test(result) ? 'fail'
    : /\b(?:missing|inconclusive|no evidence)\b/i.test(result) ? 'inconclusive'
      : /^(?:pass|passed|ok)\b/i.test(result) ? 'pass' : 'unknown'
  return <span className={`evidence-result ${kind}`}>{value || 'Not recorded'}</span>
}

function MeasurementCard({ item, onOpen }: { item: MachineMeasurement; onOpen: (path: string) => void }) {
  const record = item.record
  return <article className="measurement-card">
    <div className="measurement-heading"><div><b>{record.stage || 'Unknown stage'} · iteration {record.iteration ?? '—'}</b>
      <small>{record.run_id || 'Unknown run'} · {item.path}</small></div>
      <div className="measurement-actions"><ResultTag value={record.exit_code === 0 ? 'Run exit 0' : `Exit ${record.exit_code ?? 'unknown'}`} />
        <button className="small secondary-button" onClick={() => onOpen(item.path)}>Source record</button></div></div>
    {!item.valid_v2 ? <p className="evidence-muted">Record is malformed or is not a v2 measurement. {item.error || ''}</p> : <>
      <p className="measurement-command"><b>Target:</b> {record.target} <span>·</span> <b>Command:</b> {record.command}</p>
      {record.error && <p className="evidence-warning">{record.error}</p>}
      <div className="measurement-table-wrap"><table className="measurement-table"><thead><tr><th>Requirement</th><th>Metric</th><th>Measured value</th><th>Criterion</th><th>Result</th></tr></thead>
        <tbody>{(record.measurements || []).map((measurement, index) => <tr key={`${measurement.requirement_id}-${index}`}>
          <td>{measurement.requirement_id || '—'}</td><td>{measurement.metric || '—'}</td>
          <td>{String(measurement.value ?? '—')}{measurement.unit ? ` ${measurement.unit}` : ''}</td><td>{measurement.criterion || '—'}</td>
          <td><ResultTag value={measurement.result || 'inconclusive'} /></td>
        </tr>)}</tbody></table></div>
    </>}
  </article>
}

export function TelemetryView({ projectPath, cycle, revision = 0, theme = 'dark' }: {
  projectPath: string; cycle: string | null; revision?: number; theme?: 'dark' | 'light'
}) {
  const [data, setData] = useState<WorkspaceEvidence | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [streamIndex, setStreamIndex] = useState(0)
  const [metricKey, setMetricKey] = useState('')
  const [openLog, setOpenLog] = useState<{ path: string; content: string } | null>(null)
  useEffect(() => {
    const controller = new AbortController()
    setLoading(true); setError(''); setData(null); setOpenLog(null)
    request<WorkspaceEvidence>(workspaceUrl('evidence', projectPath, cycle ? { cycle } : {}), controller.signal)
      .then(value => { if (!controller.signal.aborted) setData(value) })
      .catch(reason => { if (!controller.signal.aborted) setError(reason.message) })
      .finally(() => { if (!controller.signal.aborted) setLoading(false) })
    return () => controller.abort()
  }, [projectPath, cycle, revision])

  const streams = data?.telemetry || []
  const stream = streams[streamIndex]
  const metrics = useMemo(() => {
    const keys = new Set(stream?.samples.flatMap(sample => metricsFor(sample).map(([key]) => key)) || [])
    return [...keys].map(metricLabel).sort((a, b) => a.label.localeCompare(b.label))
  }, [stream])
  const selectedMetric = metrics.find(metric => metric.key === metricKey) || metrics[0]

  async function showLog(path: string) {
    try {
      const document = await request<{ content: string }>(workspaceUrl('artifact', projectPath, { path }))
      setOpenLog({ path, content: document.content })
    } catch (reason) { setError(reason instanceof Error ? reason.message : 'Could not open test log') }
  }

  const sampleCount = streams.reduce((sum, item) => sum + item.sample_count, 0)
  const vl2Items = data?.vl2.items || []
  const explicitNoEvidence = /no evidence|missing/i.test(data?.vl2.statement || '')

  return <div className={`telemetry-view${theme === 'light' ? ' light' : ''}`}>
    <div className="telemetry-intro"><div><span className="eyebrow">MEASUREMENTS · MACHINE EVIDENCE</span>
      <h2>Telemetry &amp; VL-2</h2><p>Collected measurements and hardware-validation records for {cycle || 'the selected cycle'}.</p></div>
      <span className="evidence-cycle">{cycle || 'NO CYCLE'}</span></div>
    {loading ? <div className="workspace-message">Loading telemetry evidence…</div> : error ? <div className="workspace-message error-state" role="alert">{error}</div> : data && <>
      <div className="evidence-metrics">
        <div className="evidence-metric"><Activity size={17}/><span><b>{sampleCount}</b><small>telemetry samples</small></span></div>
        <div className="evidence-metric"><Gauge size={17}/><span><b>{data.measurements.length}</b><small>measurement records</small></span></div>
        <div className="evidence-metric"><Thermometer size={17}/><span><b>{vl2Items.length}</b><small>VL-2 claims in G3</small></span></div>
      </div>

      <section className={`vl2-honesty ${explicitNoEvidence ? 'no-evidence' : ''}`}>
        <div className="vl2-honesty-icon"><AlertTriangle size={18}/></div>
        <div><span className="eyebrow">AS RECORDED BY G3</span><p>{data.vl2.statement}</p>
          <small>This summarizes the saved G3 evidence; the UI does not assign a verdict.</small>
          <small>Source: .codeanvil/report/{cycle}/G3_artifacts/verified_prototype.md</small>
          <span className={`prototype-freshness ${data.vl2.prototype_current ? 'current' : 'stale'}`}>{data.vl2.freshness}</span></div>
      </section>

      <section className="telemetry-panel">
        <div className="telemetry-panel-head"><div><span className="eyebrow">SYSTEM · PROCESS · DEVICE</span><h3>Telemetry trends</h3></div>
          {streams.length > 0 && <label><span>Run</span><select value={streamIndex} onChange={event => { setStreamIndex(Number(event.target.value)); setMetricKey('') }}>
            {streams.map((item, index) => <option key={item.path} value={index}>{item.run_id} · {item.sample_count} samples</option>)}
          </select></label>}
        </div>
        {!streams.length ? <div className="evidence-empty"><Activity size={22}/><b>No telemetry samples recorded</b>
          <p>This cycle has no JSONL samples to plot. Test-run text logs are shown below, but they are not device measurements.</p></div>
          : stream?.error ? <div className="evidence-warning">Could not read this stream: {stream.error}</div>
          : !selectedMetric ? <div className="evidence-empty">No numeric process, system, temperature, or counter signals are available in this run.</div>
          : <><div className="plot-controls"><b>{selectedMetric.label}</b><label><span>Signal</span><select value={selectedMetric.key} onChange={event => setMetricKey(event.target.value)}>
            {metrics.map(metric => <option key={metric.key} value={metric.key}>{metric.label}{metric.unit ? ` (${metric.unit})` : ''}</option>)}
          </select></label></div>
            <TelemetryPlot stream={stream!} metric={selectedMetric}/>
            {(stream!.truncated_tail || stream!.truncated_count) && <p className="evidence-warning">{stream!.truncated_tail && 'The last JSONL line is incomplete. '}{stream!.truncated_count && 'Only the first 10,000 samples are shown.'}</p>}
          </>}
        {stream?.unavailable_signals.length ? <div className="unavailable-list"><b>Signals reported unavailable</b>
          {stream.unavailable_signals.map(item => <p key={item.signal}><code>{item.signal}</code><span>{item.reasons.join(' · ')}</span></p>)}
        </div> : null}
        {data.vl2.manual_telemetry.length > 0 && <div className="manual-telemetry">
          <div><b>Manually recorded target readings</b><small>Shown as written in G3; these readings are not a time series.</small></div>
          <div className="manual-reading-grid">{data.vl2.manual_telemetry.map((reading, index) => <article key={`${reading.Signal}-${index}`}>
            <span>{reading.Signal || 'Signal'}</span><b>{reading.Reading || '—'}</b>
            <small>{Object.entries(reading).find(([name]) => /^Envelope\b/i.test(name))?.[1]}</small>
            <ResultTag value={reading.Status || 'Not recorded'} />
          </article>)}</div>
        </div>}
      </section>

      <section className="telemetry-panel"><div className="telemetry-panel-head"><div><span className="eyebrow">S3 / G3</span><h3>Machine measurement records</h3></div></div>
        {!data.measurements.length ? <div className="evidence-empty"><FileText size={22}/><b>No v2 measurement.json records</b>
          <p>VL-2 runs can attach requirement-level measurements here. Empty or missing records stay unavailable; they are never treated as a pass.</p></div>
          : <div className="measurement-list">{data.measurements.map(item => <MeasurementCard key={item.path} item={item} onOpen={showLog}/>)}</div>}
      </section>

      <section className="telemetry-panel"><div className="telemetry-panel-head"><div><span className="eyebrow">G3 ASSESSMENT</span><h3>VL-2 module and path evidence</h3></div></div>
        {!vl2Items.length ? <div className="evidence-empty"><b>No VL-2 rows declared in the saved G3 report.</b></div> :
          <div className="vl2-table-wrap"><table className="vl2-table"><thead><tr><th>Scope</th><th>Item</th><th>Environment</th><th>Command</th><th>Recorded result</th><th>Telemetry</th></tr></thead>
            <tbody>{vl2Items.map((item, index) => <tr key={`${item.scope}-${item.id}-${index}`}>
              <td>{item.scope}</td><td><b>{item.id}</b><small>{item.level}</small></td><td>{item.environment || '—'}</td>
              <td><code>{item.command || '—'}</code></td><td><ResultTag value={item.result} level="VL-2"/></td><td>{item.telemetry || '—'}</td>
            </tr>)}</tbody></table></div>}
      </section>

      <section className="telemetry-panel"><div className="telemetry-panel-head"><div><span className="eyebrow">RUN OUTPUTS</span><h3>Test logs</h3></div></div>
        {!data.test_logs.length ? <div className="evidence-empty">No captured VL test logs for this cycle.</div> : <div className="test-log-list">
          {data.test_logs.map(log => <button key={log.path} className="test-log-button" onClick={() => showLog(log.path)}>
            <FileText size={16}/><span><b>{log.label}</b><small>{log.path} · {(log.size_bytes / 1024).toFixed(1)} KB</small></span><RefreshCw size={13}/>
          </button>)}
        </div>}
        {openLog && <div className="test-log-content"><div><b>{openLog.path}</b><button className="small secondary-button" onClick={() => setOpenLog(null)}>Close</button></div><pre>{openLog.content}</pre></div>}
      </section>
    </>}
  </div>
}

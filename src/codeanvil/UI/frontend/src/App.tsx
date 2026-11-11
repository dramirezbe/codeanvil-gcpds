import { useEffect, useState } from 'react'
import { Activity, Anvil, Archive, ArrowDownRight, ArrowUpRight, ChevronDown, CircleHelp, Command, Cpu, FileText, FolderOpen, Gauge, HardDrive, LayoutDashboard, Menu, Moon, Radio, RefreshCw, Search, Settings2, ShieldCheck, Sun, Terminal, Wifi } from 'lucide-react'

type Project = {name:string; path:string; id?:string}
type Bootstrap = {mode?:'launcher'|'workspace'; project?:Project|null; projects?:Project[]}
type Gate = {iteration:number|null;hitl:string|null;based_on?:[string,number]|null;superseded_by?:string|null}
type Progress = {active_cycle?:string|null;cycles:Record<string,Record<string,Gate>>;backups:Record<string,Array<[string,number|null,string]>>}
const API='/api'

function useBootstrap(projectPath?:string,revision=0){
 const [state,setState]=useState<Bootstrap>({mode:'launcher',projects:[]})
 useEffect(()=>{let live=true;const query=projectPath?`?project_path=${encodeURIComponent(projectPath)}`:'';fetch(`${API}/ui/bootstrap${query}`).then(r=>r.ok?r.json():Promise.reject()).then(d=>live&&setState(d)).catch(()=>{if(live)setState({mode:'launcher',projects:[]})});return()=>{live=false}},[projectPath,revision])
 return state
}

const stages=[['S0','Normalize'],['G0','GT Gate'],['S1','Design'],['G1','Review'],['S2','Implement'],['G2','Verify']] as const

export default function App(){
 const [active,setActive]=useState('Overview'),[dark,setDark]=useState(true),[mobile,setMobile]=useState(false),[selected,setSelected]=useState<Project|null>(null),[forceLauncher,setForceLauncher]=useState(false),[actionRevision,setActionRevision]=useState(0)
 const data=useBootstrap(selected?.path,actionRevision)
 const [uiZoom,setUiZoom]=useState(()=>{
  const saved=Number(localStorage.getItem('codeanvil-ui-zoom'))
  return Number.isFinite(saved)&&saved>=0.8&&saved<=1.3?saved:1
 })
 useEffect(()=>{
  const onWheel=(event:WheelEvent)=>{
   if(!event.ctrlKey)return
   event.preventDefault()
   setUiZoom(current=>{
    const next=Math.min(1.3,Math.max(0.8,Math.round((current+(event.deltaY<0?0.05:-0.05))*100)/100))
    localStorage.setItem('codeanvil-ui-zoom',String(next))
    return next
   })
  }
  window.addEventListener('wheel',onWheel,{passive:false})
  return()=>window.removeEventListener('wheel',onWheel)
 },[])
 const project=forceLauncher?null:(selected||data.project||null), workspace=!forceLauncher&&(data.mode==='workspace'||!!selected)
 return <div className={dark?'app':'app light'} style={{zoom:uiZoom}}>
  <header className="topbar"><button className="icon-btn mobile-menu" onClick={()=>setMobile(!mobile)} aria-label="Toggle navigation"><Menu size={18}/></button><div className="brand"><span className="brand-mark"><Anvil size={19}/></span><span>CODE<span className="ember">ANVIL</span></span><span className="brand-tag">FORGE</span></div><div className="top-separator"/><button className="project-switch" onClick={()=>{setSelected(null);setForceLauncher(true)}}><span className="project-dot"/><span>{forceLauncher?'Project launcher':project?.name||'Project launcher'}</span><ChevronDown size={14}/></button><div className="top-spacer"/><div className="status-pill"><span className="pulse"/> LOCAL ENGINE <span className="status-sep"/> READY</div><button className="icon-btn" aria-label="Search"><Search size={17}/></button><button className="icon-btn" onClick={()=>setDark(!dark)} aria-label="Toggle theme">{dark?<Sun size={17}/>:<Moon size={17}/>}</button><button className="avatar">JD</button></header>
  <div className="shell">
   <nav className={`rail ${mobile?'rail-open':''}`}><div className="rail-group"><span className="rail-label">WORKSPACE</span>{[[LayoutDashboard,'Overview'],[Activity,'Activity'],[FileText,'Reports'],[FolderOpen,'Ground truth'],[Cpu,'Hardware'],[Archive,'Backups'],[Terminal,'CLI actions']].map(([Icon,label]:any)=><button key={label} className={`rail-item ${active===label?'selected':''}`} onClick={()=>{setActive(label);setMobile(false)}}><Icon size={17}/><span>{label}</span></button>)}</div><div className="rail-bottom"><button className="rail-item" onClick={()=>setActive('Settings')}><Settings2 size={17}/><span>Settings</span></button><button className="rail-item"><CircleHelp size={17}/><span>Help</span></button></div></nav>
   <main className="main-area">{active==='CLI actions'?<ActionsPanel projectPath={project?.path} onComplete={()=>setActionRevision(v=>v+1)}/>:workspace?<Workspace key={project?.path||'workspace'} project={project} active={active} onSetActive={setActive}/>:<Launcher projects={data.projects||[]} onSelect={p=>{setSelected(p);setForceLauncher(false)}}/>}</main>
  </div>
  <footer className="statusbar"><span><span className="online-dot"/> CODEANVIL 0.7.0</span><span>{project?.path||'No project selected'}</span><span className="footer-right">{Math.round(uiZoom*100)}% · CTRL+SCROLL <span className="status-sep"/> <Wifi size={13}/> LOCAL <span className="status-sep"/> <CircleHelp size={13}/> DOCS</span></footer>
 </div>
}

function Launcher({projects,onSelect}:{projects:Project[];onSelect:(p:Project)=>void}){return <div className="launcher"><div className="eyebrow"><span className="eyebrow-line"/> PROJECT DESK</div><h1>Choose your <span>workpiece.</span></h1><p className="lede">Your projects, gates, and tools in one place.</p><div className="section-heading"><div><span className="eyebrow">RECENT PROJECTS</span><h2>Projects in CodeAnvil</h2></div></div><div className="project-grid">{projects.length?projects.map(p=><button className="project-card" key={p.path} onClick={()=>onSelect(p)}><div className="card-top"><span className="project-icon"><Anvil size={18}/></span></div><strong>{p.name}</strong><span className="project-path">{p.path}</span><div className="card-foot"><span><FolderOpen size={13}/> Open workspace</span><ArrowUpRight size={15}/></div></button>):<div className="empty-projects"><div className="empty-icon"><HardDrive size={21}/></div><div><b>No registered projects</b><span>Register a project with the CodeAnvil CLI to see it here.</span></div></div>}</div><PendingFeatures/><div className="launcher-footer"><span><Command size={13}/> CODEANVIL TOOLCHAIN</span><span>GLOBAL CONFIG <ArrowDownRight size={12}/></span></div></div>}

function PendingFeatures(){return <section className="pending-panel" aria-labelledby="pending-heading"><div className="pending-heading"><div><span className="eyebrow"><span className="eyebrow-line"/> IMPLEMENTATION STATUS</span><h2 id="pending-heading">Still in progress</h2><p>These capabilities are not available in the UI yet.</p></div><span className="pending-count">8 items</span></div><div className="pending-grid">
 <div className="pending-item"><b>PTY-based CLI actions</b><span>Actions that need an interactive terminal or long-running process still need the live PTY session.</span></div>
 <div className="pending-item"><b>Themed Markdown viewer</b><span>Reports and documents still show Markdown source. The planned web renderer will style headings, tables, links, quotes and code blocks with the forge palette in light and dark themes.</span></div>
 <div className="pending-item"><b>Launch agents and editors</b><span>The launcher registry exists, but install detection and launch buttons are not connected to the UI.</span></div>
 <div className="pending-item"><b>Live terminal and chat</b><span>Agent sessions, PTY terminal and chat are not implemented.</span></div>
 <div className="pending-item"><b>Live updates and logs</b><span>Automatic refresh, application logs and telemetry charts are not available yet.</span></div>
 <div className="pending-item"><b>Hardware validation</b><span>HIL target controls and telemetry are not shown in the UI.</span></div>
 <div className="pending-item"><b>Hardware photo gallery</b><span>COTS image lookup, caching and attribution are not implemented.</span></div>
 <div className="pending-item"><b>Desktop app</b><span>The current UI runs in a browser; Tauri packaging is future work.</span></div>
 </div></section>}

type ActionField={name:string;label?:string;flag?:string|null;type?:string;required?:boolean;choices?:string[];default?:string|number|boolean|string[];secret?:boolean;help?:string;multiple?:boolean;nargs?:string|number;positional?:boolean}
type CliAction={id:string;label:string;help:string;available:boolean;reason?:string;requires_confirmation?:boolean;requires_project_path?:boolean;argv_prefix?:string[];fields:ActionField[]}
type ActionResult={ok:boolean;exit_code:number;stdout:string;stderr:string;error?:string}

function ActionsPanel({projectPath,onComplete}:{projectPath?:string;onComplete:()=>void}){
 const [actions,setActions]=useState<CliAction[]>([]),[actionId,setActionId]=useState(''),[values,setValues]=useState<Record<string,string|boolean|string[]>>({}),[confirmed,setConfirmed]=useState(false),[busy,setBusy]=useState(false),[message,setMessage]=useState(''),[result,setResult]=useState<ActionResult|null>(null),[targetPath,setTargetPath]=useState(projectPath||'')
 useEffect(()=>{let live=true;fetch(`${API}/actions/catalog`).then(r=>r.ok?r.json():Promise.reject(new Error('Could not load CLI actions'))).then(d=>live&&setActions(d.actions||[])).catch(e=>live&&setMessage(e.message));return()=>{live=false}},[])
 useEffect(()=>setTargetPath(projectPath||''),[projectPath])
 const action=actions.find(a=>a.id===actionId)||null
 const choose=(id:string)=>{setActionId(id);setConfirmed(false);setResult(null);setMessage('');const found=actions.find(a=>a.id===id);setValues(Object.fromEntries((found?.fields||[]).map(f=>[f.name,f.multiple&&f.choices?[]:id==='telemetry'&&f.name==='duration'?'10':Array.isArray(f.default)?f.default.join(','):String(f.default??'')])))}
 const run=async()=>{
  if(!action)return
  setBusy(true);setMessage('');setResult(null)
  const missing=(action.fields||[]).find(f=>f.required&&((Array.isArray(values[f.name])&&!(values[f.name] as string[]).length)||(!Array.isArray(values[f.name])&&String(values[f.name]??'').trim()==='')))
  if(missing){setMessage(`${missing.label||missing.name} is required.`);setBusy(false);return}
  if(action.requires_project_path&&!targetPath.trim()){setMessage('Choose the cloned project folder to sync.');setBusy(false);return}
  const argv=[...(action.argv_prefix||[])];
  for(const field of action.fields||[]){
   const raw=values[field.name];if(field.type==='boolean'){if(raw===true||raw==='true')argv.push(field.flag||field.name);continue}
   const value=Array.isArray(raw)?'':String(raw??'').trim();if(!value&&!Array.isArray(raw))continue
   const chunks=Array.isArray(raw)?raw:(field.multiple||field.nargs==='+'||field.nargs==='*'?value.split(/[,\n]/).map(x=>x.trim()).filter(Boolean):[value])
   if(field.multiple&&field.nargs==null&&field.flag){for(const chunk of chunks)argv.push(field.flag,chunk)}
   else{if(field.flag)argv.push(field.flag);argv.push(...chunks)}
  }
  try{
   const response=await fetch(`${API}/actions/run`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({argv,project_path:action.requires_project_path?targetPath:projectPath,confirm:confirmed})})
   const payload=await response.json()
   if(!response.ok){setMessage(payload.detail||`Request failed (${response.status})`);return}
   const data=payload as ActionResult
   setResult(data);if(data.ok){onComplete();if(action.id==='upgrade')setMessage('Upgrade finished. Restart the UI to load the installed version.')}else setMessage(data.error||data.stderr||'Action failed')
  }catch(e){setMessage(e instanceof Error?e.message:'Action request failed')}
  finally{setBusy(false)}
 }
 return <div className="workspace actions-workspace"><div className="page-head"><div><div className="eyebrow"><span className="eyebrow-line"/> CODEANVIL CLI</div><h1>Run an action</h1><p className="lede">Actions call CodeAnvil's Python logic directly. Project actions use the selected project.</p></div></div>
  <section className="content-panel action-panel"><label className="action-field"><b>Command</b><select value={actionId} onChange={e=>choose(e.target.value)}><option value="">Choose a CLI action…</option>{actions.map(a=><option key={a.id} value={a.id} disabled={!a.available}>{a.label}{!a.available?' — unavailable':''}</option>)}</select></label>
   {action&&<><p className="action-help">{action.help}</p>{action.reason&&<p className="action-notice">{action.reason}</p>}
    {action.requires_project_path&&<label className="action-field"><b>Project folder *</b><small>Folder containing .codeanvil/project.yaml</small><input type="text" required value={targetPath} onChange={e=>setTargetPath(e.target.value)}/></label>}
    <div className="action-fields">{action.fields.map(field=><label className="action-field" key={field.name}><b>{field.name.replaceAll('_',' ')}{field.required?' *':''}</b>{field.help&&<small>{field.help}</small>}{field.type==='boolean'?<input type="checkbox" checked={values[field.name]===true||values[field.name]==='true'} onChange={e=>setValues(v=>({...v,[field.name]:e.target.checked}))}/>:field.choices?<select multiple={field.multiple} required={field.required} value={Array.isArray(values[field.name])?values[field.name] as string[]:String(values[field.name]??'')} onChange={e=>setValues(v=>({...v,[field.name]:field.multiple?Array.from(e.currentTarget.selectedOptions,o=>o.value).filter(Boolean):e.currentTarget.value}))}><option value="">Select…</option>{field.choices.map(choice=><option key={choice}>{choice}</option>)}</select>:<input type={field.secret?'password':field.type==='number'?'number':'text'} required={field.required} value={Array.isArray(values[field.name])?(values[field.name] as string[]).join(','):String(values[field.name]??'')} placeholder={field.multiple||field.nargs==='+'?'Separate values with commas':''} onChange={e=>setValues(v=>({...v,[field.name]:e.target.value}))}/>}</label>)}</div>
    {action.requires_confirmation&&<label className="confirm-action"><input type="checkbox" checked={confirmed} onChange={e=>setConfirmed(e.target.checked)}/> I understand this action can modify system or project state.</label>}
    <button className="primary-button" disabled={busy||!action.available||(action.requires_confirmation&&!confirmed)} onClick={run}>{busy?'Running…':'Run action'}</button>
   </>}
   {message&&<p className="action-notice" role="alert">{message}</p>}
   {result&&<section className={`action-result ${result.ok?'success':'failure'}`}><h2>{result.ok?'Completed':'Failed'} · exit {result.exit_code}</h2>{result.stdout&&<pre>{result.stdout}</pre>}{result.stderr&&<pre>{result.stderr}</pre>}</section>}
  </section>
 </div>
}

function Workspace({project,active,onSetActive}:{project:Project|null;active:string;onSetActive:(active:string)=>void}){
 const [progress,setProgress]=useState<Progress|null>(null),[error,setError]=useState(''),[document,setDocument]=useState<{name:string;content:string}|null>(null),[selectedReport,setSelectedReport]=useState<{cycle:string;name:string}|null>(null)
 const [docName,setDocName]=useState(''),[refreshRevision,setRefreshRevision]=useState(0)
 const query=project?.path?`?project_path=${encodeURIComponent(project.path)}`:''
 useEffect(()=>{let live=true;fetch(`${API}/workspace/progress${query}`).then(r=>r.ok?r.json():Promise.reject(new Error('Could not load project progress'))).then(d=>{if(live){setProgress(d);setError('')}}).catch(e=>live&&setError(e.message));return()=>{live=false}},[project?.path,refreshRevision])
 useEffect(()=>{let live=true;if(!docName){setDocument(null);return()=>{live=false}};const area=active==='Ground truth'?'gt':'design';fetch(`${API}/workspace/documents/${area}/${encodeURIComponent(docName)}${query}`).then(r=>r.ok?r.json():Promise.reject(new Error('Document not found'))).then(d=>live&&setDocument(d)).catch(e=>live&&setDocument({name:docName,content:e.message}));return()=>{live=false}},[docName,active,project?.path,refreshRevision])
 useEffect(()=>{let live=true;if(!selectedReport)return;fetch(`${API}/workspace/reports/${encodeURIComponent(selectedReport.cycle)}/${encodeURIComponent(selectedReport.name+'.md')}${query}`).then(r=>r.ok?r.json():Promise.reject(new Error('Report not found'))).then(d=>live&&setDocument(d)).catch(e=>live&&setDocument({name:selectedReport.name,content:e.message}));return()=>{live=false}},[selectedReport,project?.path,refreshRevision])
 const cycle=progress?.active_cycle||null
 const gates=cycle?progress?.cycles[cycle]||{}:{}
 const gateIds=['S0','G0','S1','G1','S2','G2']
 const predecessor:Record<string,string>={G0:'S0',S1:'G0',G1:'S1',S2:'G1',G2:'S2'}
 const isStale=(id:string):boolean=>{
  const state=gates[id]
  if(!state)return false
  if(state.superseded_by)return true
  const previous=predecessor[id],basedOn=state.based_on
  if(!previous)return false
  if(isStale(previous))return true
  return !!basedOn&&basedOn[0]===previous&&gates[previous]?.iteration!=null&&gates[previous].iteration!==basedOn[1]
 }
 const completed=gateIds.filter(id=>gates[id]?.hitl==='PASS'&&!isStale(id)).length
 const docs=active==='Ground truth'?['build_package.md','StRS.md','SyRS.md']:['SDD.md','dependency_graph.html']
 return <div className="workspace"><div className="page-head"><div><div className="eyebrow"><span className="eyebrow-line"/> {active.toUpperCase()} <span className="slash">/</span> V-SIL METHOD</div><h1>{active==='Overview'?'Project overview':active}</h1><p className="lede">{project?.path||'Workspace'} · Cycle {cycle||'not started'}</p></div><button className="secondary-button" onClick={()=>setRefreshRevision(value=>value+1)}><RefreshCw size={14}/> Refresh</button></div>
 {error&&<p className="lede">{error}</p>}{!cycle&&<p className="lede">No active cycle is set in project.yaml.</p>}{active==='Overview'&&<PendingFeatures/>}
 {active==='Ground truth'||active==='Design'?<div className="document-layout"><nav className="document-list">{docs.map(name=><button className="secondary-button" key={name} onClick={()=>{setSelectedReport(null);setDocName(name)}}>{name}</button>)}</nav>{docName==='dependency_graph.html'&&document?<iframe className="document-frame" title="Service dependency graph" sandbox="allow-scripts" srcDoc={document.content}/>:<pre className="document-view">{document?.content||'Select a document to view it.'}</pre>}</div>:active==='Backups'?<section className="content-panel"><h2>Backups</h2>{Object.entries(progress?.backups||{}).map(([c,entries])=><div key={c}><h3>{c}</h3>{entries.map(([stage,iteration,path])=><p key={path}>{stage} · {iteration??'unknown iteration'} · {path}</p>)}</div>)}</section>:active==='Reports'?<section className="content-panel"><h2>Gate reports</h2>{Object.entries(progress?.cycles||{}).map(([c,items])=><div key={c}><h3>{c}</h3>{Object.entries(items).map(([id,state])=><button className="report-row report-button" key={id} onClick={()=>{setDocName('');setSelectedReport({cycle:c,name:id})}}><span className="report-id">{id}</span><span className="report-name"><b>Iteration {state.iteration??'—'}</b></span><span className="tag">{isStale(id)?'STALE':state.hitl||'No verdict'}</span><ArrowUpRight size={14}/></button>)}</div>)}{selectedReport&&<article className="report-content"><h3>{selectedReport.cycle}/{selectedReport.name}</h3><pre className="document-view">{document?.content||'Loading report…'}</pre></article>}</section>:<><div className="summary-row"><div className="summary-card"><span className="metric-label"><Gauge size={14}/> FLOW PROGRESS</span><div className="metric">{completed}<span>/{gateIds.length}</span><small>non-stale PASS reports in active cycle</small></div><div className="progress-track"><i style={{width:`${completed/gateIds.length*100}%`}}/></div></div><div className="summary-card"><span className="metric-label"><ShieldCheck size={14}/> REPORTS</span><div className="metric">{gateIds.filter(id=>gates[id]).length}<small>chain reports in {cycle||'no cycle'}</small></div></div><div className="summary-card"><span className="metric-label"><Radio size={14}/> HARDWARE TARGETS</span><div className="metric metric-small">{project?'See project configuration':'No project'}</div><small className="muted">Target status is not available</small></div></div><section className="flow-panel"><div className="panel-head"><div><span className="eyebrow">METHODOLOGY</span><h2>V-SIL flow</h2></div></div><div className="flow-line">{stages.map(([id,label],i)=>{const gate=gates[id];const done=gate?.hitl==='PASS'&&!isStale(id);const feedback=gate?.hitl==='FEEDBACK';return <div key={id} className={`flow-stage ${done?'done':''} ${feedback?'current':''}`}><div className="stage-node">{done?<ShieldCheck size={16}/>:id}</div><span className="stage-id">{id}</span><span className="stage-name">{label}</span><small>{isStale(id)?'STALE':gate?.hitl||'—'}</small>{i<stages.length-1&&<div className="stage-connector"/>}</div>})}</div></section><section className="content-panel"><div className="panel-head"><h2>Latest reports</h2></div>{gateIds.filter(id=>gates[id]).map(id=>{const state=gates[id];return <button className="report-row report-button" key={id} onClick={()=>{onSetActive('Reports');setSelectedReport({cycle:cycle||'',name:id})}}><span className="report-id">{id}</span><span className="report-name"><b>Iteration {state.iteration??'—'}</b><small>{state.based_on?`Based on ${state.based_on[0]} iteration ${state.based_on[1]}`:'No predecessor metadata'}</small></span><span className="tag">{isStale(id)?'STALE':state.hitl||'No verdict'}</span><ArrowUpRight size={14}/></button>})}</section></>}
 </div>
}

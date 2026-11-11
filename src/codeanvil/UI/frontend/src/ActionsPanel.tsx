import { useEffect, useState } from 'react'

const API = '/api'

type ActionField={name:string;label?:string;flag?:string|null;type?:string;required?:boolean;choices?:string[];default?:string|number|boolean|string[];secret?:boolean;help?:string;multiple?:boolean;nargs?:string|number;positional?:boolean}
type CliAction={id:string;label:string;help:string;available:boolean;reason?:string;requires_confirmation?:boolean;requires_project_path?:boolean;argv_prefix?:string[];fields:ActionField[]}
type ActionResult={ok:boolean;exit_code:number;stdout:string;stderr:string;error?:string}

export function ActionsPanel({projectPath,onComplete}:{projectPath?:string;onComplete:()=>void}){
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


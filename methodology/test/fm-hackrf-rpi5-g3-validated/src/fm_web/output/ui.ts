/**
 * Inline HTML dashboard — four views, alert bar, no external assets (StRS §3.3).
 * Colour encoding: Occupied=red, Free=green, Uncertain=yellow, Withheld=grey (SDD §1.4).
 * Refresh: 6 s for spectrum/alerts, 60 s for history views (PROTO-025).
 */
export function buildDashboardHtml(activeRoute = "/power"): string {
  return `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>FM Screening — COL-001</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{background:#0d1117;color:#e6edf3;font-family:ui-monospace,monospace;font-size:13px;min-height:100vh;display:flex;flex-direction:column}
a{color:inherit;text-decoration:none}
/* nav */
nav{background:#161b22;border-bottom:1px solid #30363d;display:flex;align-items:center;gap:0;padding:0 12px;flex-shrink:0}
nav .brand{font-size:13px;color:#58a6ff;padding:10px 16px 10px 0;border-right:1px solid #30363d;margin-right:4px;white-space:nowrap}
nav a{padding:10px 14px;font-size:12px;color:#8b949e;border-bottom:2px solid transparent;transition:color .15s}
nav a:hover{color:#e6edf3}
nav a.active{color:#e6edf3;border-bottom-color:#58a6ff}
/* alert bar */
#alert-bar{display:flex;align-items:center;gap:10px;padding:7px 14px;background:#161b22;border-bottom:1px solid #30363d;font-size:12px;flex-shrink:0}
.dot{width:9px;height:9px;border-radius:50%;background:#3fb950;flex-shrink:0}
.dot.warn{background:#f85149;animation:pulse 1.5s infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.4}}
.sync-badge{margin-left:auto;font-size:11px;padding:2px 7px;border-radius:3px;background:#21262d;color:#8b949e}
.sync-badge.unsynced{background:#3d2a0a;color:#d29922}
/* evidence label */
.evidence{font-size:11px;color:#8b949e;padding:5px 14px;background:#0d1117;border-bottom:1px solid #21262d;flex-shrink:0}
/* data-state banner */
.state-banner{display:none;padding:5px 14px;font-size:12px;border-bottom:1px solid #30363d}
.state-banner.show{display:block}
.state-banner.insufficient{background:#1a1f2b;color:#58a6ff}
.state-banner.no_data{background:#2d1a1a;color:#f85149}
.state-banner.unavailable{background:#2d1a1a;color:#f85149}
/* main */
main{flex:1;padding:14px;overflow:auto}
h2{font-size:12px;color:#8b949e;text-transform:uppercase;letter-spacing:.06em;margin-bottom:10px}
/* cards */
.card{background:#161b22;border:1px solid #30363d;border-radius:6px;padding:12px;margin-bottom:12px}
/* spectrum canvas */
#spectrum-canvas{width:100%;height:160px;display:block;cursor:crosshair}
#spectrum-tooltip{position:fixed;background:#1c2128;border:1px solid #444;border-radius:4px;padding:4px 8px;font-size:11px;pointer-events:none;display:none;white-space:nowrap;z-index:100}
/* power table */
.power-table-wrap{max-height:420px;overflow-y:auto}
table{width:100%;border-collapse:collapse}
th,td{text-align:left;padding:4px 8px;border-bottom:1px solid #21262d;font-size:12px;white-space:nowrap}
th{color:#8b949e;font-weight:normal;position:sticky;top:0;background:#161b22;z-index:1}
/* occupancy badges */
.occ{padding:2px 6px;border-radius:3px;font-size:11px;font-weight:600}
.occ-red{background:#3d1a1a;color:#f85149}
.occ-green{background:#1a2d1a;color:#3fb950}
.occ-yellow{background:#2d2a1a;color:#d29922}
.occ-grey{background:#21262d;color:#8b949e}
/* power heatmap row colours */
tr.row-red td:first-child{border-left:3px solid #f85149}
tr.row-green td:first-child{border-left:3px solid #3fb950}
tr.row-yellow td:first-child{border-left:3px solid #d29922}
tr.row-grey td:first-child{border-left:3px solid #444}
/* status grid */
.stat-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:10px}
.stat-card{background:#0d1117;border:1px solid #30363d;border-radius:4px;padding:10px}
.stat-label{font-size:11px;color:#8b949e;margin-bottom:4px}
.stat-value{font-size:16px;font-weight:600}
.stat-value.ok{color:#3fb950}.stat-value.warn{color:#f85149}.stat-value.info{color:#58a6ff}
/* stations view */
.stations-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:12px}
.station-card{background:#161b22;border:1px solid #30363d;border-radius:6px;padding:10px}
.station-name{font-size:12px;color:#58a6ff;margin-bottom:6px;font-weight:600}
.station-freq{font-size:11px;color:#8b949e;margin-bottom:8px}
#dc-canvas-wrap canvas{width:100%;height:60px;display:block}
/* reports */
.report-row{display:flex;align-items:center;gap:10px;padding:8px 0;border-bottom:1px solid #21262d}
.report-row:last-child{border-bottom:none}
.report-id{font-size:12px;color:#58a6ff;flex:1}
.report-meta{font-size:11px;color:#8b949e}
.report-dl{padding:3px 10px;background:#21262d;border-radius:3px;font-size:11px;color:#e6edf3;cursor:pointer}
.report-dl:hover{background:#30363d}
/* refresh note */
.refresh-note{font-size:11px;color:#484f58;margin-top:8px}
</style>
</head>
<body>
<nav>
  <span class="brand">FM Screening &#x25CF; COL-001</span>
  <a href="/power"    id="nav-power"    class="${activeRoute==="/power"?"active":""}">Power / Time</a>
  <a href="/spectrum" id="nav-spectrum" class="${activeRoute==="/spectrum"?"active":""}">Spectrum</a>
  <a href="/stations" id="nav-stations" class="${activeRoute==="/stations"?"active":""}">Stations 24 h</a>
  <a href="/status"   id="nav-status"   class="${activeRoute==="/status"?"active":""}">Node Status</a>
  <a href="/alerts"   id="nav-alerts"   class="${activeRoute==="/alerts"?"active":""}">Alerts</a>
  <a href="/reports"  id="nav-reports"  class="${activeRoute==="/reports"?"active":""}">Reports</a>
</nav>

<div id="alert-bar">
  <div class="dot" id="alert-dot"></div>
  <span id="alert-text">Loading…</span>
  <span class="sync-badge" id="sync-badge">synced</span>
</div>

<div class="evidence">Screening evidence only: not a compliance determination</div>
<div class="state-banner" id="state-banner"></div>

<div id="spectrum-tooltip"></div>

<main id="main-content">Loading…</main>

<script>
const VIEW = ${JSON.stringify(activeRoute)};
const FAST_MS  = 6000;   // spectrum + alerts
const SLOW_MS  = 60000;  // history views

// ── helpers ───────────────────────────────────────────────────────────────────
function el(id){ return document.getElementById(id); }
function mhz(hz){ return (hz/1e6).toFixed(1); }
function fmtAge(s){ if(s===null||s===undefined) return "—"; return parseFloat(s).toFixed(1)+"s"; }
function fmtDrift(d){ if(d===null||d===undefined) return "—"; return (d>=0?"+":"")+parseFloat(d).toFixed(1)+" dB"; }

function occBadge(occ, withheld){
  if(withheld && withheld!=="none") return \`<span class="occ occ-grey">withheld: \${withheld}</span>\`;
  const map={Occupied:"occ-red",Free:"occ-green",Uncertain:"occ-yellow"};
  return \`<span class="occ \${map[occ]||"occ-yellow"}">\${occ||"Uncertain"}</span>\`;
}

function rowClass(colour){ return colour==="red"?"row-red":colour==="green"?"row-green":colour==="yellow"?"row-yellow":"row-grey"; }

function showStateBanner(state){
  const b=el("state-banner");
  if(!state||state==="ok"){b.className="state-banner";b.textContent="";return;}
  const msgs={insufficient_history:"Insufficient history — data shown covers available window only.",no_data:"No data available yet.",unavailable:"Data source unavailable."};
  b.className="state-banner show "+state;
  b.textContent=msgs[state]||state;
}

function updateSyncBadge(sync){
  const b=el("sync-badge");
  b.textContent=sync||"unknown";
  b.className="sync-badge"+(sync==="unsynced"||sync==="stepped"?" unsynced":"");
}

// ── alert bar (always refreshing at 6 s) ─────────────────────────────────────
async function refreshAlertBar(){
  try{
    const d=await fetch("/api/alerts").then(r=>r.json());
    const count=d.active_count??0;
    el("alert-dot").className="dot"+(count>0?" warn":"");
    if(count===0){
      el("alert-text").textContent="No active alerts";
    } else {
      el("alert-text").textContent=count+" active alert"+(count!==1?"s":"")+": "+
        (d.alerts||[]).map(a=>a.rule+(a.channels?.length?" ch"+a.channels.join(","):"")).join("; ");
    }
    updateSyncBadge(d.sync_state);
  }catch(e){el("alert-text").textContent="Alert bar unavailable";}
}

// ── view renderers ────────────────────────────────────────────────────────────

async function renderPower(){
  const main=el("main-content");
  try{
    const d=await fetch("/api/power").then(r=>r.json());
    showStateBanner(d.data_state);
    if(!d.channels?.length){main.innerHTML='<div class="card">No channel data.</div>';return;}

    // Build a compact table: each row = one channel, columns = last N bins
    const BIN_COLS = Math.min(10, (d.channels[0]?.bins?.length||0));
    const times = BIN_COLS>0 ? d.channels[0].bins.slice(-BIN_COLS).map(b=>b.ts_iso.substring(11,16)+" UTC") : [];

    let html='<div class="card"><h2>Power by Channel — last '+BIN_COLS+' minutes</h2><div class="power-table-wrap"><table><thead><tr><th>Ch</th><th>Freq (MHz)</th>';
    times.forEach(t=>{ html+='<th>'+t+'</th>'; });
    html+='<th>Latest state</th></tr></thead><tbody>';

    d.channels.forEach(ch=>{
      const bins=ch.bins.slice(-BIN_COLS);
      const latest=bins[bins.length-1];
      const c=latest?.colour||"grey";
      html+='<tr class="'+rowClass(c)+'"><td>'+ch.channel+'</td><td>'+mhz(ch.freq_hz)+'</td>';
      bins.forEach(b=>{
        const val=b.power_dbm!==null?b.power_dbm.toFixed(1):("—"+(b.withheld_reason?":"+b.withheld_reason:""));
        const bg=b.colour==="red"?"#3d1a1a":b.colour==="green"?"#1a2d1a":b.colour==="yellow"?"#2d2a1a":"#21262d";
        const fg=b.colour==="red"?"#f85149":b.colour==="green"?"#3fb950":b.colour==="yellow"?"#d29922":"#8b949e";
        html+='<td style="background:'+bg+';color:'+fg+'">'+val+'</td>';
      });
      html+='<td>'+occBadge(latest?.occupancy,latest?.withheld_reason)+'</td></tr>';
    });
    html+='</tbody></table></div>';
    if(d.data_state==="insufficient_history") html+='<p class="refresh-note">History starts: '+(d.history_start_utc_us?new Date(d.history_start_utc_us/1000).toISOString():"unknown")+'</p>';
    html+='<p class="refresh-note">Refreshes every 60 s</p></div>';
    main.innerHTML=html;
  }catch(e){main.innerHTML='<div class="card">Error loading power data.</div>';}
}

// ── Spectrum state: keep last 4 traces for persistence ────────────────────────
const _specHistory = [];   // [{pts, channels}] newest last, max 4
let   _specChannels = [];  // latest 199-ch summary with occupancy

async function renderSpectrum(){
  const main=el("main-content");
  try{
    const d=await fetch("/api/spectrum").then(r=>r.json());
    showStateBanner(d.data_state);

    // Build a flat sorted array of {freq_hz, power_dbm} from all raw steps
    const allPts=[];
    for(const step of (d.raw_steps||[])){
      if(!step.points_dbm) continue;
      step.points_dbm.forEach((p,i)=>{
        allPts.push({freq_hz: step.first_frequency_hz + i*step.point_spacing_hz, power_dbm: p});
      });
    }
    allPts.sort((a,b)=>a.freq_hz-b.freq_hz);

    if(allPts.length){
      _specHistory.push(allPts);
      if(_specHistory.length>4) _specHistory.shift();
    }
    _specChannels=d.points||[];

    if(!el("spectrum-canvas")){
      const occupied=_specChannels.filter(p=>p.occupancy==="Occupied");
      let html='<div class="card">';
      html+='<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:6px">';
      html+='<h2 style="margin:0">Spectrum — 87.6–107.5 MHz</h2>';
      html+='<span style="font-size:11px;color:#8b949e" id="scan-meta"></span></div>';
      html+='<canvas id="spectrum-canvas" style="width:100%;height:260px;display:block;cursor:crosshair"></canvas>';
      html+='<div id="spectrum-tooltip"></div>';
      html+='<div style="font-size:11px;color:#8b949e;margin-top:6px">';
      html+='&#9632; <span style="color:#f85149">Occupied</span>&nbsp;';
      html+='&#9632; <span style="color:#3fb950">Free / noise floor</span>&nbsp;';
      html+='&#9644; <span style="color:#30363d">Ghost traces (last 3 scans)</span>&nbsp;';
      html+='&nbsp;&nbsp;Hover for readout</div>';
      html+='<p class="refresh-note" id="spectrum-refresh-note">Waiting for data…</p></div>';
      if(occupied.length){
        html+='<div class="card"><h2>Occupied channel markers (STK-REQ-042)</h2>';
        html+='<table><thead><tr><th>Ch</th><th>Freq (MHz)</th><th>Power (dBm)</th><th>State</th><th>DC adj</th></tr></thead><tbody id="markers-tbody"></tbody></table></div>';
      }
      main.innerHTML=html;
      _attachSpectrumTooltip();
    }

    _drawSpectrumAnalyzer(_specHistory, _specChannels);

    const meta=el("scan-meta");
    if(meta&&d.scan_ts_iso) meta.textContent='Scan #'+d.scan_id+' · '+d.scan_ts_iso.substring(11,19)+' UTC'+(d.sync_state!=="synced"?' ('+d.sync_state+')':'');
    const note=el("spectrum-refresh-note");
    if(note) note.textContent='Refreshes every 6 s · '+new Date().toLocaleTimeString();

    const tbody=el("markers-tbody");
    if(tbody){
      tbody.innerHTML=_specChannels.filter(p=>p.occupancy==="Occupied").map(p=>
        '<tr><td>'+p.channel+'</td><td>'+mhz(p.freq_hz)+'</td><td>'+(p.power_dbm!==null?p.power_dbm.toFixed(1):"—")+'</td><td>'+occBadge(p.occupancy,p.withheld_reason)+'</td><td>'+(p.dc_adjacent?'<span style="color:#d29922">⚠ yes</span>':'no')+'</td></tr>'
      ).join("");
    }
  }catch(e){console.error(e);el("main-content").innerHTML='<div class="card">Error loading spectrum.</div>';}
}

function _drawSpectrumAnalyzer(history, channels){
  const canvas=el("spectrum-canvas");
  if(!canvas) return;
  const W=canvas.clientWidth||900, H=canvas.clientHeight||260;
  canvas.width=W; canvas.height=H;
  const ctx=canvas.getContext("2d");

  const pad={l:42,r:8,t:12,b:22};
  const pw=W-pad.l-pad.r, ph=H-pad.t-pad.b;
  const MIN_P=-120, MAX_P=-40;
  const MIN_F=87_500_000, MAX_F=107_600_000;

  function fx(f){ return pad.l+pw*(f-MIN_F)/(MAX_F-MIN_F); }
  function py(p){ return pad.t+ph*(1-(p-MIN_P)/(MAX_P-MIN_P)); }

  // Background
  ctx.fillStyle="#0d1117"; ctx.fillRect(0,0,W,H);

  // dBm gridlines + labels
  [-120,-110,-100,-90,-80,-70,-60,-50,-40].forEach(db=>{
    const y=py(db);
    ctx.strokeStyle=db%20===0?"#21262d":"#161b22";
    ctx.setLineDash(db%20===0?[]:[2,4]);
    ctx.lineWidth=1;
    ctx.beginPath(); ctx.moveTo(pad.l,y); ctx.lineTo(W-pad.r,y); ctx.stroke();
    ctx.setLineDash([]);
    ctx.fillStyle="#484f58"; ctx.font="10px ui-monospace,monospace";
    ctx.textAlign="right";
    ctx.fillText(db,pad.l-3,y+3);
  });

  // Frequency gridlines every 2 MHz
  ctx.textAlign="center";
  for(let f=88e6;f<=108e6;f+=2e6){
    const x=fx(f);
    ctx.strokeStyle="#161b22"; ctx.lineWidth=1;
    ctx.beginPath(); ctx.moveTo(x,pad.t); ctx.lineTo(x,pad.t+ph); ctx.stroke();
    ctx.fillStyle="#484f58"; ctx.font="10px ui-monospace,monospace";
    ctx.fillText((f/1e6).toFixed(0),x,H-4);
  }

  // Channel occupancy colour bands (background tint)
  channels.forEach(ch=>{
    if(!ch.power_dbm) return;
    const x=fx(ch.freq_hz-50_000), w=pw*100_000/(MAX_F-MIN_F);
    const col=ch.occupancy==="Occupied"?"rgba(192,57,43,0.08)":ch.occupancy==="Free"?"rgba(39,174,96,0.05)":"rgba(210,153,34,0.05)";
    ctx.fillStyle=col;
    ctx.fillRect(x,pad.t,w,ph);
  });

  // Ghost traces (oldest to newest, most transparent first)
  history.forEach((trace,hi)=>{
    if(hi===history.length-1) return; // current drawn separately
    const alpha=(hi+1)/history.length*0.25;
    ctx.strokeStyle=\`rgba(88,166,255,\${alpha})\`;
    ctx.lineWidth=1;
    ctx.beginPath();
    let first=true;
    trace.forEach(p=>{
      if(p.power_dbm===null) return;
      const x=fx(p.freq_hz), y=py(p.power_dbm);
      if(first){ctx.moveTo(x,y);first=false;}else ctx.lineTo(x,y);
    });
    ctx.stroke();
  });

  // Current trace — gradient fill below line
  const current=history[history.length-1];
  if(current&&current.length){
    // Filled area
    const grad=ctx.createLinearGradient(0,pad.t,0,pad.t+ph);
    grad.addColorStop(0,"rgba(39,174,96,0.3)");
    grad.addColorStop(1,"rgba(39,174,96,0.0)");
    ctx.fillStyle=grad;
    ctx.beginPath();
    let first=true;
    const baseY=pad.t+ph;
    current.forEach(p=>{
      if(p.power_dbm===null) return;
      const x=fx(p.freq_hz), y=py(p.power_dbm);
      if(first){ctx.moveTo(x,baseY);ctx.lineTo(x,y);first=false;}else ctx.lineTo(x,y);
    });
    ctx.lineTo(fx(current[current.length-1].freq_hz),baseY);
    ctx.closePath(); ctx.fill();

    // Line
    ctx.strokeStyle="#3fb950"; ctx.lineWidth=1.5; ctx.setLineDash([]);
    ctx.beginPath(); first=true;
    current.forEach(p=>{
      if(p.power_dbm===null) return;
      const x=fx(p.freq_hz), y=py(p.power_dbm);
      if(first){ctx.moveTo(x,y);first=false;}else ctx.lineTo(x,y);
    });
    ctx.stroke();
  }

  // Occupied channel markers — peak labels
  channels.filter(ch=>ch.occupancy==="Occupied"&&ch.power_dbm!==null).forEach(ch=>{
    const x=fx(ch.freq_hz);
    const y=py(ch.power_dbm);
    // Vertical tick
    ctx.strokeStyle="#f85149"; ctx.lineWidth=1; ctx.setLineDash([2,2]);
    ctx.beginPath(); ctx.moveTo(x,pad.t); ctx.lineTo(x,y); ctx.stroke();
    ctx.setLineDash([]);
    // Label box
    const label=mhz(ch.freq_hz);
    ctx.font="bold 10px ui-monospace,monospace";
    const tw=ctx.measureText(label).width+6;
    const lx=Math.min(Math.max(x-tw/2,pad.l),W-pad.r-tw);
    ctx.fillStyle="rgba(192,57,43,0.85)";
    ctx.fillRect(lx,pad.t,tw,13);
    ctx.fillStyle="#fff"; ctx.textAlign="left";
    ctx.fillText(label,lx+3,pad.t+10);
    // Dot at peak
    ctx.fillStyle="#f85149";
    ctx.beginPath(); ctx.arc(x,y,3,0,Math.PI*2); ctx.fill();
  });

  // Axes borders
  ctx.strokeStyle="#30363d"; ctx.lineWidth=1; ctx.setLineDash([]);
  ctx.strokeRect(pad.l,pad.t,pw,ph);
}

function _attachSpectrumTooltip(){
  const canvas=el("spectrum-canvas");
  const tip=el("spectrum-tooltip");
  if(!canvas||!tip) return;
  const MIN_F=87_500_000, MAX_F=107_600_000;
  const pad={l:42,r:8,t:12,b:22};

  canvas.onmousemove=function(e){
    const rect=canvas.getBoundingClientRect();
    const mx=e.clientX-rect.left;
    const pw=rect.width-pad.l-pad.r;
    const f=MIN_F+(mx-pad.l)/pw*(MAX_F-MIN_F);
    // Find nearest raw point in latest trace
    const trace=_specHistory[_specHistory.length-1];
    if(!trace){tip.style.display="none";return;}
    const nearest=trace.reduce((best,p)=>Math.abs(p.freq_hz-f)<Math.abs(best.freq_hz-f)?p:best, trace[0]);
    // Find channel
    const ch=_specChannels.find(c=>Math.abs(c.freq_hz-nearest.freq_hz)<150_000);
    const chStr=ch?" · Ch "+ch.channel+" "+ch.occupancy:"";
    tip.style.display="block";
    tip.style.left=(e.clientX+14)+"px";
    tip.style.top=(e.clientY-8)+"px";
    tip.textContent=(nearest.freq_hz/1e6).toFixed(4)+" MHz · "+(nearest.power_dbm!==null?nearest.power_dbm.toFixed(1)+" dBm":"withheld")+chStr;
  };
  canvas.onmouseleave=function(){tip.style.display="none";};
}

async function renderStations(){
  const main=el("main-content");
  try{
    const d=await fetch("/api/stations?span_h=24").then(r=>r.json());
    showStateBanner(d.data_state);
    if(!d.stations?.length){main.innerHTML='<div class="card">No station data.</div>';return;}

    let html='<div style="margin-bottom:10px"><span style="font-size:12px;color:#8b949e">Span: 24 h — duty cycle per 10 min interval — up to 10 stations</span></div>';
    html+='<div class="stations-grid">';

    d.stations.forEach(s=>{
      const pwr=s.latest_power_dbm!==null?s.latest_power_dbm.toFixed(1)+" dBm":"—";
      const maxDC=Math.max(...(s.bins||[]).map(b=>b.duty_cycle_pct??0));
      html+='<div class="station-card">';
      html+='<div class="station-name">'+(s.callsign||"Ch "+s.channel)+'</div>';
      html+='<div class="station-freq">Ch '+s.channel+' &bull; '+mhz(s.freq_hz)+' MHz &bull; '+pwr+'</div>';
      html+='<canvas id="dc-'+s.channel+'" height="60" style="width:100%;display:block"></canvas>';
      html+='<div style="font-size:11px;color:#8b949e;margin-top:4px">Peak duty cycle: '+(maxDC>0?maxDC.toFixed(1)+"%":"—")+'</div>';
      html+='</div>';
    });
    html+='</div><p class="refresh-note">Refreshes every 60 s</p>';
    main.innerHTML=html;

    // Draw duty-cycle sparklines
    d.stations.forEach(s=>{
      const c=el("dc-"+s.channel);
      if(!c) return;
      const W=c.clientWidth||240, H=60;
      c.width=W; c.height=H;
      const ctx=c.getContext("2d");
      ctx.fillStyle="#0d1117"; ctx.fillRect(0,0,W,H);
      const bins=s.bins||[];
      if(!bins.length) return;
      const bw=W/bins.length;
      bins.forEach((b,i)=>{
        const pct=b.duty_cycle_pct??0;
        const barH=Math.round((pct/100)*H);
        const unc=b.uncertain_pct??0;
        const uh=Math.round((unc/100)*H);
        ctx.fillStyle="#2d2a1a";
        ctx.fillRect(i*bw, H-barH-uh, Math.max(1,bw-1), uh);
        ctx.fillStyle=pct>80?"#c0392b":pct>40?"#d29922":"#27ae60";
        ctx.fillRect(i*bw, H-barH, Math.max(1,bw-1), barH);
      });
    });
  }catch(e){main.innerHTML='<div class="card">Error loading stations.</div>';}
}

async function renderStatus(){
  const main=el("main-content");
  try{
    const d=await fetch("/api/status").then(r=>r.json());
    showStateBanner(d.data_state);
    const warn=v=>v?"ok":"warn";
    // Five mandated fields (STK-REQ-044) + extras
    main.innerHTML=\`
<div class="card">
  <h2>Node Status</h2>
  <div class="stat-grid">
    <div class="stat-card">
      <div class="stat-label">Online (1/5)</div>
      <div class="stat-value \${d.online?"ok":"warn"}">\${d.online?"ONLINE":"OFFLINE"}</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Last scan age (2/5)</div>
      <div class="stat-value \${d.last_scan_age_s!==null&&d.last_scan_age_s<10?"ok":"warn"}">\${fmtAge(d.last_scan_age_s)}</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Noise floor drift 24 h (3/5)</div>
      <div class="stat-value \${Math.abs(d.noise_floor_drift_db??0)<=3?"ok":"warn"}">\${fmtDrift(d.noise_floor_drift_db)}</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Overflow count (4/5)</div>
      <div class="stat-value \${d.overflow_count===0?"ok":"warn"}">\${d.overflow_count}</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Dropped frames (5/5)</div>
      <div class="stat-value \${d.dropped_frame_count===0?"ok":"warn"}">\${d.dropped_frame_count}</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">CPU temp</div>
      <div class="stat-value \${d.thermal_ok?"ok":"warn"}">\${d.temp_c!==null?d.temp_c.toFixed(1)+"°C":"—"}</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">HAL mode</div>
      <div class="stat-value info">\${d.hal}</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Clock sync</div>
      <div class="stat-value \${d.sync_state==="synced"?"ok":"warn"}">\${d.sync_state}</div>
    </div>
  </div>
  <p class="refresh-note">Refreshes every 60 s — Tick \${d.tick}</p>
</div>\`;
  }catch(e){main.innerHTML='<div class="card">Error loading status.</div>';}
}

async function renderAlerts(){
  const main=el("main-content");
  try{
    const d=await fetch("/api/alerts").then(r=>r.json());
    showStateBanner(d.data_state);
    if(!d.alerts?.length){
      main.innerHTML='<div class="card"><h2>Alerts</h2><div style="color:#3fb950;font-size:13px;padding:8px 0">&#10003; No active alerts</div><p class="refresh-note">Refreshes every 6 s</p></div>';
      return;
    }
    let html='<div class="card"><h2>Active Alerts ('+d.active_count+')</h2><table><thead><tr><th>Rule</th><th>Channels</th><th>Since (UTC)</th><th>Reason</th></tr></thead><tbody>';
    d.alerts.forEach(a=>{
      html+='<tr><td style="color:#f85149">'+a.rule+'</td><td>'+(a.channels?.join(", ")||"—")+'</td><td>'+a.since_iso.replace("T"," ").substring(0,19)+'</td><td style="color:#8b949e">'+a.reason+'</td></tr>';
    });
    html+='</tbody></table><p class="refresh-note">Refreshes every 6 s</p></div>';
    main.innerHTML=html;
  }catch(e){main.innerHTML='<div class="card">Error loading alerts.</div>';}
}

async function renderReports(){
  const main=el("main-content");
  try{
    const d=await fetch("/api/reports").then(r=>r.json());
    showStateBanner(d.data_state);
    if(!d.runs?.length){main.innerHTML='<div class="card">No saved reports.</div>';return;}
    let html='<div class="card"><h2>Saved Screening Reports</h2>';
    d.runs.forEach(r=>{
      const int=r.interrupted?'<span style="color:#d29922;font-size:11px"> (interrupted)</span>':'';
      html+='<div class="report-row">';
      html+='<div class="report-id">'+r.run_id+int+'</div>';
      html+='<div class="report-meta">'+r.started_iso.substring(0,10)+'&nbsp;&bull;&nbsp;'+r.segments+' seg&nbsp;&bull;&nbsp;'+(r.size_mb!==null?r.size_mb+" MB":"?")+' </div>';
      html+='<a class="report-dl" href="/reports/'+r.run_id+'/report_header.csv" download>header.csv</a>';
      html+='</div>';
    });
    html+='<p class="refresh-note">Not auto-refreshed</p></div>';
    main.innerHTML=html;
  }catch(e){main.innerHTML='<div class="card">Error loading reports.</div>';}
}

// ── routing ───────────────────────────────────────────────────────────────────
const RENDERERS = {
  "/power":    {fn: renderPower,    ms: SLOW_MS},
  "/spectrum": {fn: renderSpectrum, ms: FAST_MS},
  "/stations": {fn: renderStations, ms: SLOW_MS},
  "/status":   {fn: renderStatus,   ms: SLOW_MS},
  "/alerts":   {fn: renderAlerts,   ms: FAST_MS},
  "/reports":  {fn: renderReports,  ms: 0},
};

const r = RENDERERS[VIEW];
if(r){
  r.fn();
  if(r.ms>0) setInterval(r.fn, r.ms);
}

// Alert bar always refreshes at 6 s regardless of view
refreshAlertBar();
setInterval(refreshAlertBar, FAST_MS);

// Redraw spectrum canvas on resize
window.addEventListener("resize", ()=>{ if(VIEW==="/spectrum") renderSpectrum(); });
</script>
</body>
</html>`;
}

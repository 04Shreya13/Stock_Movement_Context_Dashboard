const $=id=>document.getElementById(id), D=window.STOCK_DATA;
const companies={AAPL:'Apple',ADBE:'Adobe',AMZN:'Amazon',GOOGL:'Alphabet',META:'Meta',MSFT:'Microsoft',NVDA:'NVIDIA',TSLA:'Tesla'};
const money=n=>new Intl.NumberFormat('en-US',{style:'currency',currency:'USD'}).format(n), pct=n=>(n*100).toFixed(2)+'%', date=s=>new Date(s+'T12:00:00Z').toLocaleDateString('en-US',{month:'short',day:'numeric',year:'numeric',timeZone:'UTC'}), shortdate=s=>new Date(s+'T12:00:00Z').toLocaleDateString('en-US',{month:'short',day:'numeric',timeZone:'UTC'});
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let state={company:'AAPL',year:'2025',threshold:'5',selected:'2025-04-09',mode:'close',tab:'news'},saved=[];
try{saved=JSON.parse(localStorage.getItem('stock-context-shortlist')||'[]');if(!Array.isArray(saved))saved=[]}catch{}
const byCompany={};for(const symbol of Object.keys(companies))byCompany[symbol]=D.prices.filter(p=>p.symbol===symbol).sort((a,b)=>a.date.localeCompare(b.date));
function quantile(a,q){const s=[...a].sort((a,b)=>a-b),pos=(s.length-1)*q,i=Math.floor(pos);return s[i]+(s[Math.min(i+1,s.length-1)]-s[i])*(pos-i)}
function range(p){return (p.high-p.low)/p.close}
const cutoffCache={};
function cutoff(symbol){const k=symbol+'|'+state.threshold;if(!(k in cutoffCache))cutoffCache[k]=state.threshold==='all'?0:quantile(byCompany[symbol].map(range),1-Number(state.threshold)/100);return cutoffCache[k]}
function flagged(p){return range(p)>=cutoff(p.symbol)-1e-12}
function visible(symbol=state.company){return byCompany[symbol].filter(p=>state.year==='all'||p.date.startsWith(state.year))}
function coflags(day){return D.prices.filter(p=>p.date===day&&flagged(p))}
function selected(){return byCompany[state.company].find(p=>p.date===state.selected)}
function events(){return visible().filter(flagged).sort((a,b)=>range(b)-range(a))}
function latestFiling(symbol,day,type){return D.filings.filter(f=>f.symbol===symbol&&f.date<=day&&(!type||f.document_type===type)).sort((a,b)=>b.date.localeCompare(a.date))[0]}
function toast(s){$('toast').textContent=s;$('toast').style.display='block';clearTimeout(window.toastTimer);window.toastTimer=setTimeout(()=>$('toast').style.display='none',2600)}
function render(){
 const rows=visible(),ev=events();if(!rows.some(p=>p.date===state.selected))state.selected=(ev[0]||rows[0])?.date;
 $('company').value=state.company;$('year').value=state.year;$('threshold').value=state.threshold;
 $('companyCards').innerHTML=Object.entries(companies).map(([s,n])=>{const r=visible(s),count=r.filter(flagged).length;return `<button class="company-card ${s===state.company?'active':''}" data-company="${s}" aria-pressed="${s===state.company}"><strong>${s}</strong><small>${n}</small><b>${r.length?money(r.at(-1).close):'—'}</b><em>${count} ${state.threshold==='all'?'trading':'flagged'} days</em></button>`}).join('');
 $('chartTitle').textContent=`${companies[state.company]} · ${state.company}`;
 $('coverage').textContent=rows.length?`${shortdate(rows[0].date)} – ${date(rows.at(-1).date)} · ${rows.length} trading days`: 'No price records';
 $('eventCount').textContent=ev.length;
 $('eventRows').innerHTML=ev.length?ev.map(p=>`<tr class="${p.date===state.selected?'chosen':''}" data-date="${p.date}"><td><button aria-label="Inspect ${date(p.date)}">${date(p.date)}</button></td><td class="range">${pct(range(p))}</td><td>${money(p.high-p.low)}</td><td>${coflags(p.date).length} / 8</td></tr>`).join(''):`<tr><td colspan="4"><div class="empty">No flagged days in this year.<br>Choose another year or widen the threshold.</div></td></tr>`;
 renderSelection();renderSaved();
}
function quickSummary(text,kind){
 const points=window.summarizeSource(text,kind);
 return points.length?`<div class="quick-summary"><span class="summary-label">QUICK TAKEAWAYS</span><ul>${points.map(p=>`<li><strong>${esc(p.label)}</strong><span>${esc(p.text)}</span></li>`).join('')}</ul></div>`:'<p class="data-note">No concise takeaway could be extracted. Review the full text below.</p>';
}
function renderSelection(){
 const p=selected();if(!p)return;
 $('selectedPrice').textContent=money(p.close);$('selectedDate').textContent=date(p.date);$('rangeMetric').textContent=pct(range(p));
 const co=coflags(p.date);$('coMetric').textContent=`${co.length} / 8`;
 $('contextTitle').textContent=`${state.company} · ${date(p.date)}`;
 $('selectedFacts').innerHTML=`High <b>${money(p.high)}</b> &nbsp; Low <b>${money(p.low)}</b> &nbsp; Range <b>${money(p.high-p.low)}</b><br>${co.length>=4?'Shared movement worth checking':co.length>1?'Several companies flagged':'Review company-specific context'} · ${co.length?co.map(p=>p.symbol).join(', '):'No companies meet this threshold'}${state.threshold==='all'?' (all trading days selected)':''}`;
 const start=new Date(p.date+'T12:00:00Z');start.setUTCDate(start.getUTCDate()-7);const news=D.news.filter(n=>n.symbol===state.company&&n.date>=start.toISOString().slice(0,10)&&n.date<=p.date).sort((a,b)=>b.date.localeCompare(a.date));
 $('newsPanel').innerHTML=`<p class="data-note">Selected day + previous 7 calendar days · ${news.length} daily summaries<br>Quick takeaways select source sentences; AI-written news may contain errors. Associations do not prove causation.</p>`+(news.length?news.map(n=>`<article class="news-item"><span class="news-date">${date(n.date)} ${n.date===p.date?' · SELECTED DAY':''}${n.highlights_low_info?' · LIMITED INFORMATION':''}</span>${quickSummary(n.highlights,'news')}<details class="source-details"><summary>Read full dataset summary</summary><div class="filing-text">${esc(n.highlights||'No highlights available.')}</div></details></article>`).join(''):'<div class="empty">No news records for this window.</div>');
 const f=latestFiling(state.company,p.date);let filing='';if(f){
  const annual=f.risk_refers_to_10k?latestFiling(state.company,p.date,'10-K'):null;
  filing=`<div class="filing-meta"><span class="filing-type">${esc(f.document_type)}</span><span class="muted">Filed ${date(f.date)}</span></div><p class="data-note">Most recent filing dated on or before the selected day.${f.date===p.date?' Same-day filing: intraday release time is not available.':''}<br>Automatically selected source sentences; expand the excerpts for full context.</p><h3 class="summary-heading">Performance & financial position</h3>${quickSummary(f.mda_content,'mda')}<h3 class="summary-heading">Reported risks</h3>${quickSummary(f.risk_content,'risk')}<details class="filing-section"><summary>Read full MD&A excerpt</summary><div class="filing-text">${esc(f.mda_content||'No MD&A excerpt available.')}</div></details><details class="filing-section"><summary>Read full risk excerpt</summary><div class="filing-text">${esc(f.risk_content||'No risk excerpt available.')}</div></details>`;
  if(f.risk_refers_to_10k)filing+=`<p class="data-note">This risk section refers to an annual report.${annual?' Latest available 10-K: '+date(annual.date)+'.':' No earlier 10-K is available in this dataset.'}</p>${annual?`<h3 class="summary-heading">Annual 10-K risk takeaways · ${date(annual.date)}</h3>${quickSummary(annual.risk_content,'risk')}<details class="filing-section"><summary>Read full annual risk excerpt</summary><div class="filing-text">${esc(annual.risk_content)}</div></details>`:''}`;
 }else filing='<div class="empty">No filing available on or before this date.</div>';
 $('filingPanel').innerHTML=filing;updateSave();drawChart();
 document.querySelectorAll('#eventRows tr[data-date]').forEach(r=>r.classList.toggle('chosen',r.dataset.date===p.date));
}
function drawChart(){
 const rows=visible(),w=1000,h=235,pad={l:50,r:20,t:18,b:30};if(!rows.length){$('chart').innerHTML='<div class="empty">No price records in this year.</div>';return}
 const values=rows.map(p=>state.mode==='close'?p.close:range(p)*100);let min=Math.min(...values),max=Math.max(...values),extra=(max-min)*.15||1;min=Math.max(0,min-extra);max+=extra;
 const x=i=>pad.l+i/Math.max(1,rows.length-1)*(w-pad.l-pad.r),y=v=>h-pad.b-(v-min)/(max-min)*(h-pad.t-pad.b),v=p=>state.mode==='close'?p.close:range(p)*100;
 let svg=`<svg viewBox="0 0 ${w} ${h}" role="img" aria-label="${esc(state.company)} ${state.mode==='close'?'closing price':'daily range'} over selected year"><defs><linearGradient id="area" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#16816f" stop-opacity=".14"/><stop offset="1" stop-color="#16816f" stop-opacity="0"/></linearGradient></defs>`;
 for(let i=0;i<5;i++){const val=min+(max-min)*i/4,yy=y(val);svg+=`<line x1="${pad.l}" y1="${yy}" x2="${w-pad.r}" y2="${yy}" stroke="#edf1ee"/><text x="${pad.l-9}" y="${yy+3}" text-anchor="end">${state.mode==='close'?'$':''}${val.toFixed(state.mode==='close'?0:1)}${state.mode==='range'?'%':''}</text>`}
 const path=rows.map((p,i)=>`${i?'L':'M'}${x(i).toFixed(2)},${y(v(p)).toFixed(2)}`).join(' ');svg+=`<path d="${path} L${x(rows.length-1)},${h-pad.b} L${pad.l},${h-pad.b} Z" fill="url(#area)"/><path d="${path}" stroke="#16816f" fill="none" stroke-width="2"/>`;
 const labelIndices=new Set([0,Math.round((rows.length-1)/4),Math.round((rows.length-1)/2),Math.round((rows.length-1)*.75),rows.length-1]);for(const i of labelIndices)svg+=`<text x="${x(i)}" y="${h-6}" text-anchor="middle">${shortdate(rows[i].date)}</text>`;
 const si=rows.findIndex(p=>p.date===state.selected);if(si>=0)svg+=`<line x1="${x(si)}" x2="${x(si)}" y1="${pad.t}" y2="${h-pad.b}" stroke="#506e69" stroke-dasharray="4 4"/>`;
 svg+=rows.map((p,i)=>`<circle data-day="${p.date}" cx="${x(i)}" cy="${y(v(p))}" r="${p.date===state.selected?5:flagged(p)?3.5:4}" fill="${p.date===state.selected?'#142b36':flagged(p)?'#cf8244':'transparent'}" tabindex="0" role="button" aria-label="${date(p.date)}, close ${money(p.close)}, daily range ${pct(range(p))}"><title>${date(p.date)} · Close ${money(p.close)} · Range ${pct(range(p))}</title></circle>`).join('');svg+='</svg>';$('chart').innerHTML=svg;
 document.querySelector('.legend .teal').textContent=state.mode==='close'?'━ Close price':'━ Daily range %';
}
function key(p){return p.symbol+'|'+p.date}
function updateSave(){const p=selected(),has=p&&saved.some(s=>s.key===key(p));$('saveBtn').textContent=has?'★ Shortlisted':'☆ Shortlist';$('saveBtn').setAttribute('aria-pressed',!!has);$('savedCount').textContent=saved.length}
function persist(){try{localStorage.setItem('stock-context-shortlist',JSON.stringify(saved))}catch{toast('Browser storage unavailable. Export to retain your shortlist.')}updateSave();renderSaved()}
function renderSaved(){const valid=saved.filter(s=>D.prices.some(p=>key(p)===s.key));$('shortlistItems').innerHTML=valid.length?valid.map(s=>{const p=D.prices.find(p=>key(p)===s.key);return `<article class="saved-card"><div><h3>${esc(p.symbol)} <span class="muted">${date(p.date)}</span></h3><p>Daily range ${pct(range(p))} · Close ${money(p.close)} · Saved for human follow-up</p></div><button class="outline" data-open="${esc(s.key)}">Review context ↗</button><button class="outline" data-remove="${esc(s.key)}" aria-label="Remove ${esc(p.symbol)} ${p.date}">Remove</button></article>`}).join(''):'<div class="panel empty">Your research shortlist is empty.<br>Save a trading day from the explorer to review it here.</div>';$('savedCount').textContent=valid.length}
function navigate(shortlist){$('explorer').hidden=shortlist;$('shortlistView').hidden=!shortlist;$('overviewNav').classList.toggle('active',!shortlist);$('shortlistNav').classList.toggle('active',shortlist)}
$('company').innerHTML=Object.entries(companies).map(([s,n])=>`<option value="${s}">${n} (${s})</option>`).join('');
for(const id of ['company','year','threshold'])$(id).addEventListener('change',e=>{state[id]=e.target.value;state.selected=null;render()});
$('companyCards').addEventListener('click',e=>{const b=e.target.closest('[data-company]');if(b){state.company=b.dataset.company;state.selected=null;render()}});
$('eventRows').addEventListener('click',e=>{const r=e.target.closest('[data-date]');if(r){state.selected=r.dataset.date;renderSelection()}});
function selectPoint(e){const p=e.target.closest('[data-day]');if(p){state.selected=p.dataset.day;renderSelection()}}
$('chart').addEventListener('click',selectPoint);$('chart').addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();selectPoint(e)}});
document.querySelectorAll('[data-mode]').forEach(b=>b.addEventListener('click',()=>{state.mode=b.dataset.mode;document.querySelectorAll('[data-mode]').forEach(x=>x.classList.toggle('selected',x===b));drawChart()}));
document.querySelectorAll('[data-tab]').forEach(b=>b.addEventListener('click',()=>{state.tab=b.dataset.tab;$('newsPanel').hidden=state.tab!=='news';$('filingPanel').hidden=state.tab!=='filing';document.querySelectorAll('[data-tab]').forEach(x=>x.classList.toggle('selected',x===b))}));
$('saveBtn').addEventListener('click',()=>{const p=selected();if(!p)return;const k=key(p),i=saved.findIndex(s=>s.key===k);if(i>=0){saved.splice(i,1);toast('Removed from shortlist')}else{saved.push({key:k});toast('Added to review shortlist')}persist()});
$('overviewNav').onclick=()=>navigate(false);$('shortlistNav').onclick=()=>navigate(true);
$('shortlistItems').onclick=e=>{const b=e.target.closest('[data-open],[data-remove]');if(!b)return;if(b.dataset.remove){saved=saved.filter(s=>s.key!==b.dataset.remove);persist()}else{const [symbol,day]=b.dataset.open.split('|');state.company=symbol;state.year=day.slice(0,4);state.selected=day;navigate(false);render();window.scrollTo({top:0,behavior:'smooth'})}};
for(const id of ['methodBtn','aboutBtn'])$(id).onclick=()=>$('methodDialog').showModal();$('closeDialog').onclick=()=>$('methodDialog').close();$('methodDialog').addEventListener('click',e=>{if(e.target===$('methodDialog')){const r=e.target.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)e.target.close()}});
$('exportBtn').onclick=()=>{if(!saved.length){toast('Add a movement to your shortlist first.');return}const lines=['symbol,date,close,high,low,daily_range_pct,review_status'];for(const s of saved){const p=D.prices.find(p=>key(p)===s.key);if(p)lines.push([p.symbol,p.date,p.close.toFixed(2),p.high.toFixed(2),p.low.toFixed(2),(range(p)*100).toFixed(4),'For human follow-up'].join(','))}const a=document.createElement('a'),url=URL.createObjectURL(new Blob([lines.join('\r\n')],{type:'text/csv;charset=utf-8'}));a.href=url;a.download='stock-context-shortlist.csv';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);toast('Shortlist exported')};
render();

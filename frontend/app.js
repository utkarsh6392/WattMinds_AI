'use strict';

const $ = (id) => document.getElementById(id);
const money = (n) => '₹' + Number(n || 0).toLocaleString('en-IN', {maximumFractionDigits: 2, minimumFractionDigits: 2});
const number = (n, digits = 2) => Number(n || 0).toLocaleString('en-IN', {maximumFractionDigits: digits});
const safe = (value) => String(value ?? '').replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
const first = (obj, keys, fallback = undefined) => {
  if (!obj || typeof obj !== 'object') return fallback;
  for (const key of keys) if (obj[key] !== undefined && obj[key] !== null) return obj[key];
  return fallback;
};
const numeric = (v) => v === null || v === undefined || v === '' ? null : Number.isFinite(Number(v)) ? Number(v) : null;
let chartData = [0.45,0.42,0.38,0.35,0.33,0.42,0.71,1.1,0.9,0.79,0.74,0.82,0.88,0.94,1.13,1.26,1.16,1.38,1.48,1.52,1.72,1.61,1.13,0.68];
let chartLabels = chartData.map((_, i) => String(i).padStart(2, '0'));
let toastTimer;

function toast(message, isError = false) {
  const element = $('toast');
  element.textContent = message;
  element.className = 'toast show' + (isError ? ' error' : '');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => {element.className = 'toast';}, 4700);
}

function navigate(view) {
  if (!$('view-' + view)) return;
  document.querySelectorAll('.view').forEach(node => node.classList.toggle('active', node.id === 'view-' + view));
  document.querySelectorAll('.nav-item').forEach(node => node.classList.toggle('active', node.dataset.view === view));
  const link = document.querySelector('.nav-item[data-view="' + view + '"]');
  $('breadcrumb-current').textContent = link ? link.textContent.replace('⌘1', '').trim() : view;
  $('sidebar').classList.remove('open');
  try { history.replaceState(null, '', '#' + view); } catch (_) {}
  if (view === 'overview') requestAnimationFrame(drawChart);
  window.scrollTo({top: 0, behavior: 'smooth'});
}

document.querySelectorAll('[data-view]').forEach(node => node.addEventListener('click', () => navigate(node.dataset.view)));
document.querySelectorAll('[data-go]').forEach(node => node.addEventListener('click', () => navigate(node.dataset.go)));
document.querySelectorAll('[data-view-link]').forEach(node => node.addEventListener('click', (e) => { e.preventDefault(); navigate(node.dataset.viewLink); }));
$('overview-action').addEventListener('click', () => navigate('forecast'));
$('side-upload').addEventListener('click', () => navigate('forecast'));
$('menu-btn').addEventListener('click', () => $('sidebar').classList.toggle('open'));
$('date-chip').textContent = new Intl.DateTimeFormat('en-IN', {day:'2-digit',month:'short',year:'numeric'}).format(new Date());

async function api(path, options = {}) {
  // Wait for auth.js to finish starting, then attach the Supabase access token.
  const headers = new Headers(options.headers || {});
  try {
    if (window.WattAuth) {
      await window.WattAuth.ready;
      const token = await window.WattAuth.getAccessToken();
      if (token) headers.set('Authorization', 'Bearer ' + token);
    }
  } catch (_) { /* continue without a token; the server decides */ }
  let response;
  try {
    response = await fetch('/api/' + path, {...options, headers});
  } catch (_) {
    throw new Error('Cannot reach FastAPI. Run: python -m uvicorn backend.main:app --reload');
  }
  let payload;
  try { payload = await response.json(); } catch (_) { throw new Error('Server returned an unexpected response.'); }
  if (response.status === 401) throw new Error('Your session has expired. Please sign in again.');
  if (!response.ok) {
    let detail = payload.detail || 'Request failed.';
    if (Array.isArray(detail)) detail = detail.map(x => x.msg || JSON.stringify(x)).join('; ');
    throw new Error(String(detail));
  }
  return payload;
}

async function withLoading(button, job) {
  const original = button.textContent;
  button.disabled = true;
  button.textContent = 'Working...';
  try { await job(); } catch (error) { console.error(error); toast(error.message || String(error), true); }
  finally { button.disabled = false; button.textContent = original; }
}

async function updateHealth() {
  try {
    const info = await api('health');
    const demoMode = info.mode === 'demo';
    $('sidebar-status').textContent = demoMode ? 'Demo mode' : 'API connected';
    $('header-status').textContent = demoMode ? 'Demo mode' : 'System online';
    $('sidebar-status-dot').classList.add('online');
    $('header-status-dot').classList.add('online');
    $('forecast-capability').textContent = info.model_found
      ? 'Forecast model detected · full ML mode'
      : 'Forecast model not found · download the demo CSV for other analyses';
    if (!info.src_found) toast('Place frontend/ and backend/ folders in the original WattMinds project root.', true);
  } catch (_) {
    $('sidebar-status').textContent = 'API offline';
    $('header-status').textContent = 'Disconnected';
    $('forecast-capability').textContent = 'Start FastAPI to check model availability';
    toast('Start FastAPI from WattMinds root to connect your Python modules.', true);
  }
}

// Chart uses browser canvas (no JavaScript chart dependency needed).
function drawChart() {
  const canvas = $('consumption-chart');
  if (!canvas || !canvas.offsetWidth) return;
  const bounds = canvas.getBoundingClientRect();
  const scale = window.devicePixelRatio || 1;
  const width = bounds.width, height = bounds.height;
  canvas.width = Math.round(width * scale);
  canvas.height = Math.round(height * scale);
  const ctx = canvas.getContext('2d');
  ctx.scale(scale, scale);
  const padding = {left: 33, right: 15, top: 16, bottom: 25};
  const cw = width - padding.left - padding.right;
  const ch = height - padding.top - padding.bottom;
  const ymax = Math.max(2, ...chartData.filter(Number.isFinite)) * 1.12;
  ctx.font = '11px Manrope, system-ui, sans-serif';
  ctx.textAlign = 'right';
  for (let i = 0; i <= 4; i++) {
    const y = padding.top + (ch * i) / 4;
    ctx.strokeStyle = 'rgba(255,255,255,.07)'; ctx.lineWidth = 1;
    ctx.beginPath();ctx.moveTo(padding.left, y);ctx.lineTo(width-padding.right,y);ctx.stroke();
    ctx.fillStyle = '#9aa8bc'; ctx.fillText((ymax*(4-i)/4).toFixed(1),padding.left-8,y+3);
  }
  ctx.textAlign = 'center';ctx.fillStyle = '#9aa8bc';
  for (let i = 0; i < chartData.length; i += Math.max(1,Math.ceil(chartData.length/6))) {
    const x = padding.left + (cw * i) / Math.max(1,chartData.length-1);
    ctx.fillText((chartLabels[i] || i) + (chartLabels[i]?.length === 2 ? ':00' : ''),x,height-5);
  }
  const points = chartData.map((value,i) => ({x:padding.left+cw*i/Math.max(1,chartData.length-1),y:padding.top+ch-(value/ymax)*ch}));
  if (!points.length) return;
  ctx.beginPath();ctx.moveTo(points[0].x,points[0].y);
  points.slice(1).forEach(p => ctx.lineTo(p.x,p.y));
  ctx.lineTo(points.at(-1).x,padding.top+ch);ctx.lineTo(points[0].x,padding.top+ch);ctx.closePath();
  const gradient = ctx.createLinearGradient(0,padding.top,0,height);
  gradient.addColorStop(0,'rgba(63,224,197,.28)');gradient.addColorStop(1,'rgba(63,224,197,0)');
  ctx.fillStyle = gradient;ctx.fill();
  ctx.beginPath();points.forEach((p,i) => i ? ctx.lineTo(p.x,p.y) : ctx.moveTo(p.x,p.y));
  ctx.strokeStyle = '#3fe0c5';ctx.lineWidth = 2.7;ctx.lineJoin = 'round';ctx.stroke();
  const last = points.at(-1);ctx.fillStyle = '#3fe0c5';ctx.beginPath();ctx.arc(last.x,last.y,4,0,Math.PI*2);ctx.fill();
}
window.addEventListener('resize', () => requestAnimationFrame(drawChart));

// Appliance analysis: sends exactly the existing agent's expected schema via backend.
const initialAppliances = [
  {name:'Air Conditioner',watts:1500,hours:6,quantity:1},
  {name:'Refrigerator',watts:200,hours:8,quantity:1},
  {name:'LED Bulb',watts:9,hours:6,quantity:4},
];
function addApplianceRow(row = {name:'',watts:100,hours:4,quantity:1}) {
  const tr = document.createElement('tr');
  tr.innerHTML = `<td><input class="app-name" placeholder="Appliance" value="${safe(row.name)}" required></td><td><input class="app-watts" type="number" min="0" step="any" value="${Number(row.watts)}" required></td><td><input class="app-hours" type="number" min="0" max="24" step="any" value="${Number(row.hours)}" required></td><td><input class="app-qty" type="number" min="1" max="100" value="${Number(row.quantity)}" required></td><td><button class="delete-row" type="button" title="Remove appliance">×</button></td>`;
  tr.querySelector('button').addEventListener('click', () => {
    if ($('appliance-rows').children.length <= 1) return toast('Keep at least one appliance.',true);
    tr.remove();
  });
  $('appliance-rows').appendChild(tr);
}
initialAppliances.forEach(addApplianceRow);
$('add-appliance').addEventListener('click', () => addApplianceRow());

function toAdviceList(raw) {
  if (raw === null || raw === undefined) return [];
  if (Array.isArray(raw)) return raw.flatMap(toAdviceList).slice(0, 12);
  if (typeof raw === 'string' || typeof raw === 'number') return [String(raw)];
  if (typeof raw === 'object') {
    if ('message' in raw) return [String(raw.message)];
    if ('recommendation' in raw) return [String(raw.recommendation)];
    return Object.entries(raw).map(([k,v]) => k + ': ' + (typeof v === 'object' ? JSON.stringify(v) : v)).slice(0, 12);
  }
  return [];
}
function renderAdvice(target, values, emptyText) {
  const list = toAdviceList(values);
  target.innerHTML = (list.length ? list : [emptyText]).map(x => `<div class="insight">✧ &nbsp; ${safe(x)}</div>`).join('');
}
$('appliance-form').addEventListener('submit', e => {
  e.preventDefault();
  withLoading($('manual-submit'), async () => {
    const appliances = [...$('appliance-rows').querySelectorAll('tr')].map(tr => ({
      name:tr.querySelector('.app-name').value.trim(),
      watts:Number(tr.querySelector('.app-watts').value),
      hours:Number(tr.querySelector('.app-hours').value),
      quantity:Number(tr.querySelector('.app-qty').value)
    }));
    const tariff = Number($('manual-tariff').value);
    const output = await api('manual', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({appliances,tariff,target_savings:Number($('manual-target').value)})});
    const r = output.result || {};
    const daily = numeric(first(r,['total_daily_energy_kwh','daily_energy_kwh']));
    const monthlyCost = numeric(first(r,['total_monthly_cost','monthly_cost']));
    const savings = numeric(first(r,['projected_savings','potential_monthly_savings']));
    $('manual-placeholder').classList.add('hidden');$('manual-result').classList.remove('hidden');
    $('appliance-daily').textContent = daily === null ? '—' : number(daily) + ' kWh';
    $('appliance-bill').textContent = monthlyCost === null ? '—' : money(monthlyCost);
    $('appliance-savings').textContent = savings === null ? '—' : money(savings);
    const sums = appliances.map(x => ({name:x.name,energy:x.watts*x.hours*x.quantity/1000}));
    const maxEnergy = Math.max(.001,...sums.map(x => x.energy));
    $('appliance-bars').innerHTML = sums.sort((a,b)=>b.energy-a.energy).map(x => `<div class="breakdown-row"><div class="breakdown-row-head"><span>${safe(x.name)}</span><strong>${number(x.energy)} kWh/day</strong></div><div class="bar-track"><div class="bar-fill" style="width:${(x.energy/maxEnergy*100).toFixed(1)}%"></div></div></div>`).join('');
    renderAdvice($('appliance-recs'), first(r,['recommendations','action_plan','analysis']), 'Analysis complete. Inspect appliance breakdown for large consumers.');
    if (daily !== null) {
      $('metric-energy').textContent = number(daily);
      $('metric-cost').textContent = number(daily*tariff);
      $('metric-analysis').textContent = 'Analyzed';
      $('metric-analysis-foot').textContent = appliances.length + ' appliance types';
      $('overview-source').textContent = 'Derived from your appliance inputs · estimates based on rated watts';
      $('overview-badge').textContent = 'Your input';
      $('metric-energy').parentElement.parentElement.querySelector('.metric-foot').textContent = 'Estimated from entered appliances';
      $('metric-cost').parentElement.parentElement.querySelector('.metric-foot').textContent = 'At ₹'+number(tariff)+' per kWh';
    }
    toast('Appliance analysis completed using your Python module.');
  });
});

function setupUpload(inputId, labelId) {
  const input = $(inputId);
  input.addEventListener('change', () => {$(labelId).textContent = input.files[0] ? '✓ ' + input.files[0].name : 'No file selected';});
}
setupUpload('forecast-file','forecast-filename');setupUpload('anomaly-file','anomaly-filename');

function collectNumbers(obj, prefix = '', depth = 0) {
  if (depth > 3 || !obj || typeof obj !== 'object') return [];
  return Object.entries(obj).flatMap(([k,v]) => {
    const fullKey = (prefix + ' ' + k).trim();
    if (typeof v === 'number' && Number.isFinite(v)) return [{key:fullKey,value:v}];
    if (v && typeof v === 'object' && !Array.isArray(v)) return collectNumbers(v,fullKey,depth+1);
    return [];
  });
}
$('forecast-form').addEventListener('submit', e => {
  e.preventDefault();
  withLoading($('forecast-submit'),async () => {
    const file = $('forecast-file').files[0];
    if (!file) throw new Error('Choose a CSV file first.');
    const tariff = Number($('forecast-tariff').value);
    const body = new FormData();body.append('file',file);
    const output = await api('forecast?tariff='+encodeURIComponent(tariff),{method:'POST',body});
    const r = output.result;
    $('forecast-placeholder').classList.add('hidden');$('forecast-result').classList.remove('hidden');
    const candidates = collectNumbers(r).filter(x => /predicted|prediction|forecast/i.test(x.key) && /energy|kwh|consumption/i.test(x.key));
    const specific = candidates[0] || collectNumbers(r).find(x => /predict|forecast/i.test(x.key));
    $('forecast-primary').textContent = specific ? number(specific.value,3)+( /kwh|energy|consumption/i.test(specific.key) ? ' kWh' : '') : 'Prediction completed';
    $('forecast-primary-label').textContent = specific ? specific.key.replace(/_/g,' ') : 'Review model results below';
    $('forecast-json').textContent = JSON.stringify(r,null,2);
    $('metric-analysis').textContent = 'Forecasted';
    $('metric-analysis-foot').textContent = 'ML response received';
    toast('ML forecast completed using your existing model.');
  });
});

$('anomaly-form').addEventListener('submit',e => {
  e.preventDefault();
  withLoading($('anomaly-submit'),async () => {
    const file = $('anomaly-file').files[0];
    if (!file) throw new Error('Choose an hourly energy CSV first.');
    const body = new FormData();body.append('file',file);
    const output = await api('anomalies',{method:'POST',body});
    const r = output.result || {};
    $('anomaly-placeholder').classList.add('hidden');$('anomaly-result').classList.remove('hidden');
    $('anomaly-rows').textContent = number(r.rows_analyzed,0);
    $('anomaly-count').textContent = number(r.anomaly_count,0);
    $('anomaly-rate').textContent = number(r.anomaly_rate_pct) + '%';
    $('metric-anomalies').textContent = number(r.anomaly_count,0);
    $('metric-anomalies-foot').textContent = number(r.rows_analyzed,0) + ' readings analyzed';
    const alerts = Array.isArray(r.anomalies) ? [...r.anomalies].reverse().slice(0,15) : [];
    $('anomaly-table').innerHTML = alerts.length ? alerts.map(x => `<tr><td>${number(x.Energy_kWh)} kWh</td><td>${x.Expected_Energy_kWh == null ? '—' : number(x.Expected_Energy_kWh)+' kWh'}</td><td class="${String(x.Anomaly_Type).includes('High') ? 'status-high' : 'status-low'}">${safe(x.Anomaly_Type)}</td></tr>`).join('') : '<tr><td colspan="3">No anomalies were flagged in the uploaded readings.</td></tr>';
    $('anomaly-info').textContent = 'Showing up to 15 latest anomalies. Statistical flags are not a diagnosis.';
    const readings = (r.recent_readings || []).filter(x => Number.isFinite(Number(x.Energy_kWh))).slice(-24);
    if (readings.length > 1) {
      chartData = readings.map(x=>Number(x.Energy_kWh));
      chartLabels = readings.map((_,i)=>String(i+1));
      $('overview-chart-sub').textContent = 'Latest readings from your uploaded CSV';
      $('overview-source').textContent = 'Anomaly scan completed · chart reflects latest uploaded readings';
      $('overview-badge').textContent = 'Your data';
    }
    toast('Anomaly scan complete: ' + r.anomaly_count + ' flagged readings.');
  });
});

function weatherInsights(r) {
  const values = [first(r,['alerts','recommendations','advice','energy_advice','suggestions'],null)];
  const keys = ['alerts','recommendations','advice','suggestions'];
  for (const [k,v] of Object.entries(r)) {
    if (/alert|recommend|suggest|advice|tip/i.test(k) && !keys.includes(k)) values.push(v);
  }
  return values.flatMap(toAdviceList);
}
$('weather-form').addEventListener('submit',e => {
  e.preventDefault();
  withLoading($('weather-submit'),async () => {
    const appliances = [...document.querySelectorAll('.check-cards input:checked')].map(x=>x.value);
    const output = await api('weather',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({city:$('weather-city').value.trim(),appliances,tariff:Number($('weather-tariff').value)})});
    const r = output.result || {};
    $('weather-placeholder').classList.add('hidden');$('weather-result').classList.remove('hidden');
    $('weather-location').textContent = [first(r,['city','location','name'],$('weather-city').value),first(r,['country'],'')].filter(Boolean).join(', ');
    const t = numeric(first(r,['temperature_c','temperature','temp_c','current_temperature','temperature_2m']));
    $('weather-temp').textContent = t === null ? 'Weather data' : number(t,1)+'°C';
    const daytime = first(r,['is_day','is_daytime','daytime'],null);
    $('weather-condition').textContent = daytime === null ? 'Current conditions' : daytime ? 'Daytime' : 'Nighttime';
    $('weather-big-icon').textContent = daytime === false || daytime === 0 ? '☾' : '☀';
    const extras = [
      ['Humidity',first(r,['humidity','relative_humidity','relative_humidity_2m'])],
      ['Sunrise',first(r,['sunrise'])],
      ['Sunset',first(r,['sunset'])],
      ['Local time',first(r,['local_time','time'])],
    ].filter(x=>x[1]!==null && x[1]!==undefined);
    $('weather-extra').innerHTML = extras.map(([k,v])=>`<span>${safe(k)}: ${safe(v)}${k==='Humidity'?'%':''}</span>`).join('');
    renderAdvice($('weather-alerts'),weatherInsights(r),'Weather lookup completed. See the full response for available guidance.');
    $('weather-json').textContent=JSON.stringify(r,null,2);
    toast('Weather-aware analysis completed.');
  });
});

function updateSimulator() {
  const watts = Math.max(0,Number($('sim-watts').value) || 0);
  const hours = Math.max(0,Math.min(24,Number($('sim-hours').value)||0));
  const reduction = Math.max(0,Math.min(hours,Number($('sim-reduction').value)||0));
  const quantity = Math.max(1,Math.floor(Number($('sim-qty').value)||1));
  const tariff = Math.max(0,Number($('sim-tariff').value)||0);
  $('sim-reduction-val').textContent = number(reduction,1);
  const before = watts*hours*quantity/1000*30*tariff;
  const savingsKwh = watts*reduction*quantity/1000*30;
  const after = Math.max(0,before-savingsKwh*tariff);
  $('sim-savings').textContent = money(before-after);
  $('sim-energy').textContent = number(savingsKwh) + ' kWh saved per month';
  $('sim-before').textContent = money(before);
  $('sim-after').textContent = money(after);
  $('sim-track-fill').style.width = (before===0 ? 0 : Math.max(0,after/before)*100)+'%';
}
['sim-watts','sim-hours','sim-reduction','sim-qty','sim-tariff'].forEach(id=>$(id).addEventListener('input',updateSimulator));
updateSimulator();

const initialView = location.hash.substring(1);
navigate($('view-' + initialView) ? initialView : 'overview');
requestAnimationFrame(drawChart);
updateHealth();


// Energy Copilot: calculated, transparent tool-based assistant.
$('copilot-form').addEventListener('submit', event => {
  event.preventDefault();
  withLoading($('agent-submit'), async () => {
    const payload = {
      question: $('copilot-question').value,
      tariff: Number($('agent-tariff').value),
      appliances: [{name:$('agent-name').value, watts:Number($('agent-watts').value),
        hours:Number($('agent-hours').value), quantity:Number($('agent-qty').value)}]
    };
    const response = await api('copilot', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
    const r=response.result;
    $('agent-placeholder').classList.add('hidden');$('agent-result').classList.remove('hidden');
    $('agent-question').textContent=payload.question;
    $('agent-answer').textContent=r.answer;
    $('agent-tools').innerHTML=(r.tools_used||[]).map(t=>`<span class="agent-pill">↗ ${safe(t.replaceAll('_',' '))}</span>`).join('') || '<span class="muted">No tools needed</span>';
    $('agent-actions').innerHTML=(r.actions||[]).map(x=>`<div class="agent-action"><strong>${safe(x.appliance)}</strong><span>Reduce ${number(x.reduction_hours_per_day,1)} h/day → ${money(x.monthly_inr_saved)}/month (estimate)</span></div>`).join('') || '<p class="muted small">Ask for saving suggestions to generate scenarios.</p>';
    $('agent-assumptions').textContent=r.assumptions||'';
    renderCopilotReplacements(r);
    toast('Energy decision engine completed.');
  });
});

$('patterns-file').addEventListener('change',()=> {$('patterns-filename').textContent=$('patterns-file').files[0]?.name||'No file selected';});
$('patterns-form').addEventListener('submit', event => {
  event.preventDefault();
  withLoading($('patterns-submit'), async () => {
    const form = new FormData(); form.append('file',$('patterns-file').files[0]);
    const contamination=Number($('patterns-contamination').value)/100;
    const response=await api('ml-patterns?contamination='+encodeURIComponent(contamination),{method:'POST',body:form});
    const r=response.result;
    $('patterns-placeholder').classList.add('hidden');$('patterns-result').classList.remove('hidden');
    $('patterns-rows').textContent=number(r.total_scanned,0);
    $('patterns-count').textContent=number(r.outliers,0);
    $('patterns-median').textContent=number(r.typical_energy_kwh,3);
    $('patterns-features').innerHTML=(r.features_used||[]).map(x=>`<span class="agent-pill">${safe(x)}</span>`).join('');
    $('patterns-list').innerHTML=(r.highest_outlier_examples||[]).map((x,i)=>`<div class="agent-action"><strong>Outlier ${i+1}</strong><span>${number(x.Energy_kWh,3)} kWh · Score ${number(x.anomaly_score,4)}</span></div>`).join('');
    $('patterns-notes').textContent=r.limitations||'';
    toast('Isolation Forest ML analysis complete.');
  });
});


// The app is hidden until the user signs in, so the chart (which measures its canvas)
// and the health check need to run again once the "authenticated" state appears.
new MutationObserver(() => {
  if (document.body.classList.contains('authenticated')) {
    requestAnimationFrame(drawChart);
    updateHealth();
  }
}).observe(document.body, {attributes: true, attributeFilter: ['class']});


/* ==========================================================================
   REPLACEMENT ADVISOR
   Appended to app.js. Reuses $, api, withLoading, toast, navigate, safe,
   money, number and numeric from above; nothing above was renamed.
   API: GET /api/replacement-types, POST /api/replacements (both need login;
   api() attaches the Supabase token).
   ========================================================================== */
let replTypes = [];
let replTypesState = 'idle'; // idle | loading | ready

const replSampleRows = [
  {name: 'Old tube light', type: 'tube_light', watts: 40, hours: 6, quantity: 4},
  {name: 'Ceiling fan', type: 'ceiling_fan', watts: 75, hours: 10, quantity: 3},
  {name: 'Bedroom bulb', type: 'incandescent_bulb', watts: 60, hours: 5, quantity: 2},
];

function replTypeOptions(selected) {
  return ['<option value="">Auto-detect from name</option>'].concat(
    replTypes.map(t => `<option value="${safe(t.type_key)}"${t.type_key === selected ? ' selected' : ''}>${safe(t.label)}</option>`)
  ).join('');
}

function replFmtPayback(months) {
  const m = numeric(months);
  if (m === null) return '—';
  return m < 24 ? number(m, 1) + ' months' : number(m / 12, 1) + ' years';
}

// Placeholders show the typical values for the chosen type, so users know what a "quote" is compared with.
function updateReplRowHints(tr) {
  const type = replTypes.find(t => t.type_key === tr.dataset.type);
  const range = type && Array.isArray(type.typical_old_watts) ? number(type.typical_old_watts[0], 0) + '–' + number(type.typical_old_watts[1], 0) : '';
  tr.querySelector('.repl-watts').placeholder = range || 'Watts';
  tr.querySelector('.repl-new-watts').placeholder = type ? String(type.replacement_watts) : 'Typical';
  tr.querySelector('.repl-new-cost').placeholder = type ? String(type.replacement_cost_rs) : 'Typical';
  tr.querySelector('.repl-type').title = type
    ? 'Recommended: ' + type.replacement + ' (about ' + type.replacement_watts + ' W, about ₹' + number(type.replacement_cost_rs, 0) + ' each)'
    : 'The type is guessed from the appliance name';
}

function addReplRow(row = {}, focus = false) {
  const tr = document.createElement('tr');
  tr.dataset.type = row.type || '';
  tr.innerHTML = `<td><input class="repl-name" aria-label="Appliance name" placeholder="e.g. Bedroom fan" maxlength="80" value="${safe(row.name ?? '')}"></td>`
    + `<td><select class="repl-type" aria-label="Appliance type">${replTypeOptions(tr.dataset.type)}</select></td>`
    + `<td><input class="repl-watts" type="number" min="0" step="any" aria-label="Rated watts" value="${row.watts ?? ''}"></td>`
    + `<td><input class="repl-hours" type="number" min="0" max="24" step="any" aria-label="Hours used per day" value="${row.hours ?? ''}"></td>`
    + `<td><input class="repl-qty" type="number" min="1" max="100" step="1" aria-label="Quantity" value="${row.quantity ?? 1}"></td>`
    + `<td><input class="repl-age" type="number" min="0" max="100" step="any" aria-label="Age in years (optional)" value="${row.age ?? ''}"></td>`
    + `<td class="adv-col"><input class="repl-new-watts" type="number" min="0" step="any" aria-label="Replacement watts from your quote (optional)"></td>`
    + `<td class="adv-col"><input class="repl-new-cost" type="number" min="0" step="any" aria-label="Replacement price in rupees from your quote (optional)"></td>`
    + `<td><button class="delete-row" type="button" aria-label="Remove this appliance" title="Remove appliance">×</button></td>`;
  tr.querySelector('.repl-type').addEventListener('change', e => { tr.dataset.type = e.target.value; updateReplRowHints(tr); });
  tr.querySelector('.delete-row').addEventListener('click', () => {
    if ($('repl-rows').children.length <= 1) return toast('Keep at least one appliance.', true);
    tr.remove();
  });
  $('repl-rows').appendChild(tr);
  updateReplRowHints(tr);
  if (focus) tr.querySelector('.repl-name').focus();
}

function applyReplTypes() {
  $('repl-rows').querySelectorAll('tr').forEach(tr => {
    tr.querySelector('.repl-type').innerHTML = replTypeOptions(tr.dataset.type);
    updateReplRowHints(tr);
  });
}

async function loadReplTypes() {
  // Only ask the server once signed in, so there is never a pointless 401.
  if (replTypesState !== 'idle' || !document.body.classList.contains('authenticated')) return;
  replTypesState = 'loading';
  try {
    const output = await api('replacement-types');
    replTypes = Array.isArray(output.types) ? output.types : [];
    replTypesState = 'ready';
    $('repl-status').textContent = '';
    applyReplTypes();
  } catch (error) {
    replTypesState = 'idle';
    $('repl-status').textContent = 'Appliance types could not be loaded (' + error.message + '). "Auto-detect from name" still works.';
  }
}

function importReplFromStudio() {
  const rows = [...$('appliance-rows').querySelectorAll('tr')].map(tr => ({
    name: tr.querySelector('.app-name').value.trim(),
    watts: numeric(tr.querySelector('.app-watts').value),
    hours: numeric(tr.querySelector('.app-hours').value),
    quantity: numeric(tr.querySelector('.app-qty').value) ?? 1,
  })).filter(r => r.name);
  if (!rows.length) return toast('Appliance Studio has no appliances yet. Add some there, or enter them here.', true);
  $('repl-rows').innerHTML = '';
  rows.forEach(r => addReplRow(r));
  toast('Copied ' + rows.length + ' appliance' + (rows.length === 1 ? '' : 's') + ' from Appliance Studio. Check the Type column.');
}

function collectReplPayload() {
  const rows = [...$('repl-rows').querySelectorAll('tr')];
  document.querySelectorAll('#view-replacements [aria-invalid]').forEach(el => el.removeAttribute('aria-invalid'));
  if (!rows.length) throw new Error('Add at least one appliance.');
  const fail = (el, message) => { el.setAttribute('aria-invalid', 'true'); el.focus(); throw new Error(message); };
  const useQuotes = $('repl-advanced').open;
  const appliances = rows.map((tr, i) => {
    const at = 'Row ' + (i + 1) + ': ';
    const el = (cls) => tr.querySelector(cls);
    const name = el('.repl-name').value.trim();
    if (!name) fail(el('.repl-name'), at + 'enter an appliance name.');
    const watts = numeric(el('.repl-watts').value);
    if (watts === null || watts <= 0) fail(el('.repl-watts'), at + 'enter the rated watts (more than 0).');
    const hours = numeric(el('.repl-hours').value);
    if (hours === null || hours < 0 || hours > 24) fail(el('.repl-hours'), at + 'hours per day must be between 0 and 24.');
    const quantity = numeric(el('.repl-qty').value);
    if (quantity === null || !Number.isInteger(quantity) || quantity < 1 || quantity > 100) fail(el('.repl-qty'), at + 'quantity must be a whole number from 1 to 100.');
    const age = numeric(el('.repl-age').value);
    if (el('.repl-age').value.trim() !== '' && (age === null || age < 0 || age > 100)) fail(el('.repl-age'), at + 'age must be between 0 and 100 years.');
    let newWatts = null, newCost = null;
    if (useQuotes) {
      newWatts = numeric(el('.repl-new-watts').value);
      if (el('.repl-new-watts').value.trim() !== '' && (newWatts === null || newWatts <= 0)) fail(el('.repl-new-watts'), at + 'replacement watts must be more than 0.');
      newCost = numeric(el('.repl-new-cost').value);
      if (el('.repl-new-cost').value.trim() !== '' && (newCost === null || newCost < 0)) fail(el('.repl-new-cost'), at + 'replacement price cannot be negative.');
    }
    return {name, type_key: tr.dataset.type || null, watts, hours_per_day: hours, quantity, age_years: age,
            replacement_watts: newWatts, replacement_cost_rs: newCost};
  });
  const tariff = numeric($('repl-tariff').value);
  if (tariff === null || tariff <= 0 || tariff > 1000) fail($('repl-tariff'), 'Enter your tariff in ₹ per kWh (more than 0).');
  return {appliances, tariff};
}

function replCardHtml(r) {
  const priority = String(r.priority || 'Low');
  const share = Math.max(0, Math.min(100, Number(r.share_of_savings_pct) || 0));
  const rep = r.replacement || {};
  const meta = [
    r.quantity + ' × ' + number(r.hours_per_day, 1) + ' h/day',
    (r.type_label || '') + (r.auto_detected ? ' (auto-detected)' : ''),
    'price: ' + (rep.cost_source || 'catalog estimate'),
  ].filter(Boolean).join(' · ');
  const notes = (r.notes || []).map(n => `<p class="repl-note">${safe(n)}</p>`).join('');
  const warnings = (r.warnings || []).map(w => `<p class="repl-note repl-warn">⚠ ${safe(w)}</p>`).join('');
  return `<article class="repl-card">`
    + `<div class="repl-card-head"><h5 class="repl-headline">${safe(r.headline)}</h5><span class="priority-badge ${safe(priority.toLowerCase())}">${safe(priority)} priority</span></div>`
    + `<p class="repl-detail">${safe(r.detail)}</p>`
    + `<dl class="repl-facts">`
    + `<div><dt>Saves per day</dt><dd>${number(r.kwh_saved_per_day, 2)} kWh</dd></div>`
    + `<div><dt>Saves per month</dt><dd>${money(r.monthly_saving_rs)}</dd></div>`
    + `<div><dt>Saves per year</dt><dd>${money(r.yearly_saving_rs)}</dd></div>`
    + `<div><dt>Replacement cost</dt><dd>${money(r.total_replacement_cost_rs)}</dd></div>`
    + `<div><dt>Payback</dt><dd>${safe(replFmtPayback(r.payback_months))}</dd></div>`
    + `</dl>`
    + `<div><div class="breakdown-row-head"><span>Share of total savings</span><strong>${number(share, 1)}%</strong></div><div class="bar-track"><div class="bar-fill" style="width:${share.toFixed(1)}%"></div></div></div>`
    + `<p class="repl-note">${safe(meta)}</p>${notes}${warnings}</article>`;
}

function replMutedItem(x, mark) {
  return `<div class="repl-muted-item"><span class="repl-mark" aria-hidden="true">${mark}</span><div><strong>${safe(x.name)}</strong><small>${safe(x.reason)}</small></div></div>`;
}

function renderReplacements(r) {
  const s = r.summary || {};
  const recs = r.recommendations || [];
  const efficient = r.already_efficient || [];
  const skipped = r.not_assessed || [];
  $('repl-placeholder').classList.add('hidden');
  $('repl-result').classList.remove('hidden');
  $('repl-total-year').textContent = money(s.total_yearly_saving_rs);
  $('repl-total-invest').textContent = money(s.total_investment_rs);
  const months = numeric(s.overall_payback_months);
  $('repl-payback').textContent = months === null ? '—' : number(months, 1) + ' months';
  $('repl-payback-sub').textContent = months !== null && months >= 24 ? '≈ ' + replFmtPayback(months) : '';
  $('repl-kwh-year').textContent = number(s.kwh_saved_per_year, 1) + ' kWh';
  $('repl-cards').innerHTML = recs.length
    ? recs.map(replCardHtml).join('')
    : '<div class="insight">No replacement is worth recommending right now: everything you entered is either already efficient or could not be matched to a type.</div>';
  $('repl-efficient').innerHTML = efficient.map(x => replMutedItem(x, '✓')).join('');
  $('repl-efficient-wrap').classList.toggle('hidden', !efficient.length);
  $('repl-skipped').innerHTML = skipped.map(x => replMutedItem(x, '–')).join('');
  $('repl-skipped-wrap').classList.toggle('hidden', !skipped.length);
  $('repl-assumptions').innerHTML = '<strong>Assumptions</strong><ul>' + (r.assumptions || []).map(a => `<li>${safe(a)}</li>`).join('') + '</ul>';
  $('repl-status').textContent = recs.length
    ? 'Found ' + recs.length + ' replacement' + (recs.length === 1 ? '' : 's') + ' worth considering.'
    : 'No replacements recommended.';
  // When the two panels are stacked (tablet / phone) bring the results into view.
  if (window.matchMedia('(max-width: 1180px)').matches) {
    const calm = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    $('repl-result').scrollIntoView({behavior: calm ? 'auto' : 'smooth', block: 'start'});
  }
}

replSampleRows.forEach(row => addReplRow(row));
$('repl-add').addEventListener('click', () => addReplRow({}, true));
$('repl-import').addEventListener('click', importReplFromStudio);
$('repl-advanced').addEventListener('toggle', () => $('repl-table').classList.toggle('show-adv', $('repl-advanced').open));
$('repl-form').addEventListener('input', e => e.target.removeAttribute && e.target.removeAttribute('aria-invalid'));
$('repl-form').addEventListener('submit', event => {
  event.preventDefault();
  // Typos in the form are reported with a toast only; withLoading is kept for real server/network failures.
  let payload;
  try { payload = collectReplPayload(); } catch (error) { toast(error.message, true); return; }
  withLoading($('repl-submit'), async () => {
    const output = await api('replacements', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload)});
    renderReplacements(output.result || {});
  });
});

// Load the dropdown once the user is signed in, and again whenever this view opens (covers a failed first try).
new MutationObserver(loadReplTypes).observe(document.body, {attributes: true, attributeFilter: ['class']});
new MutationObserver(() => { if ($('view-replacements').classList.contains('active')) loadReplTypes(); })
  .observe($('view-replacements'), {attributes: true, attributeFilter: ['class']});
loadReplTypes();

// Energy Copilot: show replacement answers (called from the copilot handler above).
function renderCopilotReplacements(r) {
  const list = Array.isArray(r.replacement_actions) ? r.replacement_actions : [];
  if (!list.length) return;
  $('agent-actions').innerHTML = list.map(x => `<div class="agent-action"><strong>${safe(x.appliance)} → ${safe(x.replacement)}</strong><span>${number(x.kwh_saved_per_day, 2)} kWh/day · ${money(x.yearly_saving_rs)}/year saved · pays back in ${safe(replFmtPayback(x.payback_months))} (estimate)</span></div>`).join('')
    + '<button type="button" class="text-action" id="agent-open-replacements">Open Replacement Advisor ↗</button>';
  $('agent-open-replacements').addEventListener('click', () => navigate('replacements'));
}
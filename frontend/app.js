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
  let response;
  try {
    response = await fetch('/api/' + path, options);
  } catch (_) {
    throw new Error('Cannot reach FastAPI. Run: python -m uvicorn backend.main:app --reload');
  }
  let payload;
  try { payload = await response.json(); } catch (_) { throw new Error('Server returned an unexpected response.'); }
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
    $('sidebar-status').textContent = 'API connected';
    $('header-status').textContent = 'System online';
    $('sidebar-status-dot').classList.add('online');
    $('header-status-dot').classList.add('online');
    if (!info.src_found) toast('Place frontend/ and backend/ folders in the original WattMinds project root.', true);
  } catch (_) {
    $('sidebar-status').textContent = 'API offline';
    $('header-status').textContent = 'Disconnected';
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
  ctx.font = '10px Plus Jakarta Sans, sans-serif';
  ctx.textAlign = 'right';
  for (let i = 0; i <= 4; i++) {
    const y = padding.top + (ch * i) / 4;
    ctx.strokeStyle = '#29354a'; ctx.lineWidth = 1;
    ctx.beginPath();ctx.moveTo(padding.left, y);ctx.lineTo(width-padding.right,y);ctx.stroke();
    ctx.fillStyle = '#7989a5'; ctx.fillText((ymax*(4-i)/4).toFixed(1),padding.left-8,y+3);
  }
  ctx.textAlign = 'center';ctx.fillStyle = '#788aa6';
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
  gradient.addColorStop(0,'rgba(147,123,255,.38)');gradient.addColorStop(1,'rgba(147,123,255,0)');
  ctx.fillStyle = gradient;ctx.fill();
  ctx.beginPath();points.forEach((p,i) => i ? ctx.lineTo(p.x,p.y) : ctx.moveTo(p.x,p.y));
  ctx.strokeStyle = '#a18cff';ctx.lineWidth = 2.7;ctx.lineJoin = 'round';ctx.stroke();
  const last = points.at(-1);ctx.fillStyle = '#a18cff';ctx.beginPath();ctx.arc(last.x,last.y,4,0,Math.PI*2);ctx.fill();
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
      $('overview-badge').textContent = 'YOUR INPUT';
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
      $('overview-badge').textContent = 'YOUR DATA';
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


// Kinetic UI: pointer-based depth on metric cards; decorative only.
(() => {
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
  if (reduced.matches || !window.matchMedia('(hover: hover) and (pointer: fine)').matches) return;
  document.querySelectorAll('.metric-card').forEach(card => {
    card.addEventListener('pointermove', event => {
      const box = card.getBoundingClientRect();
      const x = (event.clientX - box.left) / box.width - .5;
      const y = (event.clientY - box.top) / box.height - .5;
      card.style.transform = `perspective(850px) rotateX(${-y * 5}deg) rotateY(${x * 6}deg) translateY(-3px)`;
    });
    card.addEventListener('pointerleave', () => { card.style.transform = ''; });
  });
})();


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
    $('agent-answer').textContent=r.answer;
    $('agent-tools').innerHTML=(r.tools_used||[]).map(t=>`<span class="agent-pill">↗ ${safe(t.replaceAll('_',' '))}</span>`).join('') || '<span class="muted">No tools needed</span>';
    $('agent-actions').innerHTML=(r.actions||[]).map(x=>`<div class="agent-action"><strong>${safe(x.appliance)}</strong><span>Reduce ${number(x.reduction_hours_per_day,1)} h/day → ${money(x.monthly_inr_saved)}/month (estimate)</span></div>`).join('') || '<p class="muted small">Ask for saving suggestions to generate scenarios.</p>';
    $('agent-assumptions').textContent=r.assumptions||'';
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

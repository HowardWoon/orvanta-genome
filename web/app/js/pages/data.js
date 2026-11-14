import {data, esc, fmt, pct, kpis, header, badge, table, bars, chartBox, select, download, toCSV, C, tag} from '../core.js';

export async function render(el, ctx) {
  const m = await data('meta');
  const S = {summary, dictionary, quality, distributions, lineage}[ctx.sub];
  return S(el, m, ctx);
}

function summary(el, m) {
  const d = m.distributions, share = (k, v) => (d[k].find(x => x.k === v)?.n || 0) / m.rows;
  el.innerHTML = header('Data observatory', 'Dataset summary', 'The full case file after RFC-4180 parsing. All counts are exact over 10,000,000 rows.') + badge('OBSERVED DATA') +
    kpis([[fmt(m.rows), 'rows'], [m.columns_raw, 'raw columns'], [m.currencies, 'currencies'], [fmt(m.banks_total), 'distinct BIC8 banks'],
      [fmt(m.sender_accounts), 'sender accounts'], [fmt(m.beneficiary_accounts), 'beneficiary accounts'], [fmt(m.anomalies), 'labelled anomalies'],
      [`${m.start.slice(0, 10)} → ${m.end.slice(0, 10)}`, 'UTC time span']]) +
    `<div class="grid g2">
      ${chartBox('Routing type', bars(d['Routing type'].map(x => ({label: x.k, value: x.n})), {horizontal: true, left: 80, label: 'Routing type', vfmt: v => pct(v / m.rows)}), 'Share of all rows.')}
      ${chartBox('Participants per payment', bars(d['Participants'].map(x => ({label: x.k, value: x.n})), {label: 'Participants', vfmt: v => pct(v / m.rows, 2), h: 220}), 'Known BICs in the path (rule R6).')}
      ${chartBox('Anomaly labels', bars(d['Anomaly label'].filter(x => x.k !== 'NORMAL').map(x => ({label: x.k.replace(/_/g, ' ').toLowerCase(), value: x.n, color: C.coral})), {horizontal: true, left: 190, label: 'Anomaly labels', vfmt: fmt}), `${pct(1 - share('Anomaly label', 'NORMAL'), 3)} of rows carry a label.`)}
    </div>
    <div class="note">Sender type is a business (B) for ${pct(share('Sender type', 'B'))} of payments; the receiver is a business for ${pct(share('Receiver type', 'B'))}.
      Continuity flag Y on ${pct(share('Continuity', 'Y'))}. Detailed breakdowns: <a href="#/data/distributions">Distributions</a> · filter any combination in the <a href="#/lab/explorer">Observed data explorer</a>.</div>`;
}

function dictionary(el, m, ctx) {
  const q = ctx.params.q || '';
  const draw = () => {
    const qq = (el.querySelector('#dq')?.value || '').toLowerCase();
    const rows = m.dictionary.filter(r => !qq || JSON.stringify(r).toLowerCase().includes(qq));
    el.querySelector('#dt').innerHTML = table(rows, [{key: 'field', label: 'Field', f: v => `<code>${esc(v)}</code>`}, {key: 'dtype', label: 'Type'}, {key: 'observed', label: 'Observed range / values'},
      {key: 'missing', label: 'Missing', num: true, f: v => fmt(v)}, {key: 'origin', label: 'Origin'}, {key: 'derived', label: 'Derived features'}, {key: 'rules', label: 'Rules'}, {key: 'limitation', label: 'Limitation'}], {empty: 'No field matches this search.'});
    ctx.setParams({q: qq});
  };
  el.innerHTML = header('Data observatory', 'Field dictionary', 'Every raw field: type, observed range, missingness, derived features and the rules that use it.') + badge('OBSERVED DATA') +
    `<div class="controls"><label class="ctl">Search fields<input id="dq" type="search" value="${esc(q)}" placeholder="e.g. IBAN, path, amount"></label><button class="sec" id="dx">Export CSV</button></div><div id="dt"></div>
    <div class="note">Only <code>ANOMALY_TYPE</code> has missing values (${fmt(m.dictionary.find(r => r.field === 'ANOMALY_TYPE')?.missing)} rows) — blank means a normal payment.</div>`;
  el.querySelector('#dq').addEventListener('input', draw);
  el.querySelector('#dx').addEventListener('click', () => download('field_dictionary.csv', toCSV(m.dictionary, Object.keys(m.dictionary[0])), 'text/csv'));
  draw();
}

function quality(el, m, ctx) {
  const sel = ctx.params.check;
  const draw = id => {
    el.querySelector('#qt').innerHTML = table(m.quality.map((r, i) => ({...r, i: String(i)})), [{key: 'check', label: 'Check'}, {key: 'result', label: 'Result'},
      {key: 'status', label: 'Status', f: v => tag(v.toUpperCase(), v)}], {pick: 'i', sel: id});
    const r = m.quality[+id];
    el.querySelector('#qd').innerHTML = r ? `<div class="card"><h3>${esc(r.check)}</h3>${tag(r.status.toUpperCase(), r.status)}<dl class="kv"><dt>Result</dt><dd>${esc(r.result)}</dd><dt>Detail</dt><dd>${esc(r.detail)}</dd></dl></div>` :
      '<div class="card">Select a check to see how it was run and what was decided.</div>';
    el.querySelectorAll('#qt tr.pick').forEach(tr => { const f = () => { draw(tr.dataset.id); ctx.setParams({check: tr.dataset.id}); }; tr.onclick = f; tr.onkeydown = e => { if (e.key === 'Enter') f(); }; });
  };
  const nPass = m.quality.filter(r => r.status === 'pass').length;
  el.innerHTML = header('Data observatory', 'Quality checks', `${m.quality.length} checks run during ingestion and profiling. ${nPass} pass outright; the rest are documented decisions, not silent fixes.`) + badge('OBSERVED DATA') +
    `<div class="split"><div id="qt"></div><div id="qd"></div></div>`;
  draw(sel);
}

function distributions(el, m, ctx) {
  const keys = Object.keys(m.distributions), k = keys.includes(ctx.params.v) ? ctx.params.v : keys[0];
  const draw = () => {
    const v = el.querySelector('#dv').value, rows = m.distributions[v], tot = rows.reduce((a, b) => a + b.n, 0);
    const sorted = el.querySelector('#ds').value === 'count' ? [...rows].sort((a, b) => b.n - a.n) : rows;
    el.querySelector('#dc').innerHTML = chartBox(esc(v), bars(sorted.map(x => ({label: x.k, value: x.n})), rows.length > 10 ? {label: v, vfmt: n => `${fmt(n)} (${pct(n / tot, 2)})`} : {horizontal: true, left: 170, label: v, vfmt: n => pct(n / tot, 2)}),
      `${fmt(tot)} rows · ${rows.length} categories`) +
      table(sorted.map(x => ({...x, sh: x.n / tot})), [{key: 'k', label: 'Value'}, {key: 'n', label: 'Rows', num: true, f: fmt}, {key: 'sh', label: 'Share', num: true, f: v => pct(v, 3)}], {h: 300});
    ctx.setParams({v, sort: el.querySelector('#ds').value});
  };
  el.innerHTML = header('Data observatory', 'Distributions', 'Univariate distributions of every engineered feature. For conditional views use the explorer.') + badge('OBSERVED DATA') +
    `<div class="controls">${select('dv', 'Feature', keys, k)}${select('ds', 'Order', [['natural', 'Natural'], ['count', 'By count']], ctx.params.sort || 'natural')}</div><div id="dc" class="grid"></div>`;
  el.querySelectorAll('select').forEach(s => s.addEventListener('change', draw));
  draw();
}

function lineage(el, m) {
  const L = m.lineage;
  el.innerHTML = header('Data observatory', 'Lineage & hashes', 'Every artefact the site and PDFs read, the module that produced it, and its SHA-256. The schema contract is checked on every build.') +
    kpis([[L.artefacts.length, 'artefacts fingerprinted'], [L.contract_ok ? 'OK' : 'BROKEN', 'schema contract'], [L.pipeline.length, 'pipeline stages'], [esc(L.environment.python), 'Python']]) +
    `<div class="card"><b>Raw input.</b> <code>${esc(L.raw.path)}</code> · ${fmt(L.raw.bytes / 1e9, 2)} GB · ${fmt(L.raw.rows)} rows × ${L.raw.columns} columns. ${esc(L.raw.note)}</div>
    <h2>Pipeline</h2><div class="flow">${L.pipeline.map((p, i) => `<div><b>${i + 1}</b><span>${esc(p)}</span></div>`).join('')}</div>
    <h2>Artefacts</h2>` + table(L.artefacts, [{key: 'path', label: 'Path', f: v => `<code>${esc(v)}</code>`}, {key: 'producer', label: 'Producer'}, {key: 'rows', label: 'Rows', num: true, f: v => v == null ? '—' : fmt(v)},
      {key: 'bytes', label: 'Size', num: true, f: v => v > 1e6 ? fmt(v / 1e6, 1) + ' MB' : fmt(v / 1e3, 1) + ' kB'}, {key: 'sha256', label: 'SHA-256', f: v => `<code title="${esc(v)}">${esc((v || '').slice(0, 16))}…</code>`}, {key: 'modified', label: 'Modified'}]) +
    `<h2>Recent pipeline activity</h2>` + table(m.activity, [{key: 'when', label: 'When'}, {key: 'what', label: 'What'}, {key: 'sha', label: 'SHA', f: v => `<code>${esc(v)}</code>`}]) +
    `<h2>Environment</h2><div class="card">${Object.entries(L.environment.packages).map(([k, v]) => tag(`${k} ${v}`, 'info')).join('')}<p class="mono">${esc(L.environment.platform)}</p></div>`;
}

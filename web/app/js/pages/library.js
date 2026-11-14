// Research library: the Evidence Ledger (claim → rule → method → calculation → data → validation) and data governance.
import {data, esc, fmt, header, badge, table, select, download, toCSV, tag} from '../core.js';

export async function render(el, ctx) {
  return ctx.sub === 'governance' ? governance(el) : ledger(el, ctx);
}

async function ledger(el, ctx) {
  const L = await data('ledger'), types = ['ALL', ...new Set(L.entries.map(e => e.type))];
  const st = {q: ctx.params.q || '', type: types.includes(ctx.params.type) ? ctx.params.type : 'ALL', id: ctx.params.id || ''};
  el.innerHTML = header('Research library', 'Evidence ledger',
    `${fmt(L.n)} evidence records, each with a unique ID, the rule it supports, the method and parameters, the result, sample size, uncertainty and the source artefact (with its SHA-256 prefix where fingerprinted). Search by rule (e.g. C2), by ID (EV-RULE-009) or by word.`) +
    `<div class="controls"><label class="ctl">Search<input id="lq" type="search" value="${esc(st.q)}" placeholder="C2, EV-CX-004, Benford…"></label>${select('lt', 'Evidence type', types, st.type)}<button class="sec" id="lx">Export CSV</button></div>
    <div class="split"><div id="lt2"></div><div id="ld"></div></div>`;
  const draw = () => {
    const q = el.querySelector('#lq').value.trim().toLowerCase(), t = el.querySelector('#lt').value;
    const rows = L.entries.filter(e => (t === 'ALL' || e.type === t) && (!q || e.id.toLowerCase() === q || e.rules.some(r => r.toLowerCase() === q) || JSON.stringify(e).toLowerCase().includes(q)));
    if (!st.id && rows.length) st.id = rows[0].id;
    el._rows = rows;
    ctx.setParams({q, type: t === 'ALL' ? '' : t, id: st.id});
    el.querySelector('#lt2').innerHTML = `<div class="mono">${fmt(rows.length)} records</div>` + table(rows.slice(0, 500), [{key: 'id', label: 'ID', f: v => `<b>${esc(v)}</b>`}, {key: 'type', label: 'Type'}, {key: 'rules', label: 'Rule', f: v => v.join(', ') || '—'}, {key: 'title', label: 'Evidence'}],
      {pick: 'id', sel: st.id, h: 620, empty: 'No evidence record matches.'});
    const e = L.entries.find(x => x.id === st.id);
    el.querySelector('#ld').innerHTML = e ? `<div class="card">${tag(e.type.toUpperCase(), 'info')}<h3>${esc(e.id)} · ${esc(e.title)}</h3><dl class="kv">
        <dt>Rule</dt><dd>${e.rules.length ? e.rules.map(r => `<a href="#/rules/explorer?id=${r}">${r}</a>`).join(' ') : '—'}</dd><dt>Method</dt><dd>${esc(e.method)}</dd><dt>Parameters</dt><dd><code>${esc(e.parameters || '—')}</code></dd>
        <dt>Result</dt><dd>${esc(e.result)}</dd><dt>Sample size</dt><dd>${esc(e.n)}</dd><dt>Uncertainty</dt><dd>${esc(e.uncertainty)}</dd><dt>Source</dt><dd><code>${esc(e.source)}</code>${e.sha ? ` · sha256 ${esc(e.sha)}…` : ''}</dd>
        ${e.detail ? `<dt>Detail</dt><dd>${esc(e.detail)}</dd>` : ''}</dl>
        <p>${e.replay ? `<a href="#/forensics/replay?rule=${encodeURIComponent(e.replay)}">Inspect the records →</a> ` : ''}${e.chart ? `<a href="charts/${esc(e.chart)}.png" target="_blank" rel="noopener">Chart →</a> ` : ''}${e.rules[0] ? `<a href="#/genome/genealogy?id=${e.rules[0]}">Genealogy →</a>` : ''}</p></div>` : '<div class="card">Select a record.</div>';
    el.querySelectorAll('#lt2 tr.pick').forEach(tr => { const f = () => { st.id = tr.dataset.id; draw(); }; tr.onclick = f; tr.onkeydown = ev => { if (ev.key === 'Enter') f(); }; });
  };
  el.querySelector('#lq').addEventListener('input', () => { st.id = ''; draw(); });
  el.querySelector('#lt').addEventListener('change', () => { st.id = ''; draw(); });
  el.querySelector('#lx').onclick = () => download('evidence_ledger.csv', toCSV((el._rows || []).map(e => ({...e, rules: e.rules.join(' ')})), ['id', 'type', 'rules', 'title', 'method', 'parameters', 'result', 'n', 'uncertainty', 'source', 'sha']), 'text/csv');
  draw();
}

async function governance(el) {
  const m = await data('meta');
  el.innerHTML = header('Research library', 'Data governance & references', 'What data was used, what leaves the pipeline, and what the external references are for.') + badge('OBSERVED DATA') +
    `<div class="grid g2"><div class="card"><h3>Data used</h3><ul>
      <li>Only the supplied file: ${fmt(m.rows)} rows × ${m.columns_raw} columns (the DISCLAIMER column, filled on one row, is dropped; the row is kept).</li>
      <li>No external payment, FX or bank data enters rule discovery. General payment-industry knowledge is used only to <i>interpret</i> rules, and every such reading is labelled as interpretation.</li>
      <li>CUSTOMER_RECALL (317 rows) is not in the case appendix. It is kept and analysed (X5: no observable signature) rather than dropped or guessed.</li></ul></div>
    <div class="card"><h3>What leaves the pipeline</h3><ul>
      <li>Aggregates: an additive cube (10,396 cells), route patterns with n ≥ 150, the top-600 bank table, token shares from a 500k sample, test statistics.</li>
      <li>Forensic Replay: at most 75 records per rule, generator-relevant columns only; row ids one-way hashed; no account numbers, names, free-text details or tokens.</li>
      <li>The raw CSV and row-level Parquet are never redistributed (competition rules 2.1–2.2) and are excluded from the review ZIP.</li>
      <li>The site is team-only (Vercel Authentication) until judging; it may be made public only after the deadline and with team agreement.</li></ul></div>
    <div class="card"><h3>Synthetic data caveats</h3><ul><li>Distributions, country effects and rates are the generator's settings, not real market shares or real Swift performance.</li>
      <li>BIC8 codes, accounts and party details are synthetic; nothing here identifies a real institution or person.</li><li>Anomaly labels are synthetic labels, not confirmed crimes; their prevalence is not real-world prevalence.</li></ul></div>
    <div class="card"><h3>References and tools</h3><ul><li>Official UMDAC Datathon 2026 case study, rules and handbook (authoritative for field definitions and deliverables).</li>
      <li>General payment background for interpretation only (correspondent banking, MT103/MT202 COV cover payments, ISO 13616 IBAN, ISO 9362 BIC). The team keeps the verified citation list in <code>docs/source_register.md</code>.</li>
      <li>Tools: Python ${esc(m.lineage.environment.python)}, ${Object.entries(m.lineage.environment.packages).map(([k, v]) => `${k} ${v}`).join(', ')}. AI assistance was used for coding and drafting; every figure is produced by the code.</li></ul></div></div>`;
}

import {data, esc, fmt, header, badge, level, table, LEVEL_CLS} from '../core.js';

// Minimal, safe Markdown → HTML for our own docs (headings, lists, bold, code, tables, paragraphs). Input is escaped first.
export function md(src) {
  const out = [], lines = src.replace(/\r/g, '').split('\n'); let i = 0;
  const inline = s => esc(s).replace(/`([^`]+)`/g, '<code>$1</code>').replace(/\*\*([^*]+)\*\*/g, '<b>$1</b>').replace(/\*([^*]+)\*/g, '<i>$1</i>');
  while (i < lines.length) {
    const l = lines[i];
    if (/^#{1,4} /.test(l)) { const n = l.match(/^#+/)[0].length; out.push(`<h${Math.min(n + 1, 4)}>${inline(l.replace(/^#+ /, ''))}</h${Math.min(n + 1, 4)}>`); i++; continue; }
    if (/^\|/.test(l)) { const rows = []; while (i < lines.length && /^\|/.test(lines[i])) { if (!/^\|[\s:|-]+\|$/.test(lines[i])) rows.push(lines[i].split('|').slice(1, -1).map(c => c.trim())); i++; }
      out.push(`<div class="tbl"><table><thead><tr>${rows[0].map(c => `<th>${inline(c)}</th>`).join('')}</tr></thead><tbody>${rows.slice(1).map(r => `<tr>${r.map(c => `<td>${inline(c)}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`); continue; }
    if (/^\s*([-*]|\d+\.) /.test(l)) { const items = []; while (i < lines.length && /^\s*([-*]|\d+\.) /.test(lines[i])) { items.push(lines[i].replace(/^\s*([-*]|\d+\.) /, '')); i++; } out.push(`<ul>${items.map(x => `<li>${inline(x)}</li>`).join('')}</ul>`); continue; }
    if (!l.trim()) { i++; continue; }
    const para = []; while (i < lines.length && lines[i].trim() && !/^(#|\||\s*([-*]|\d+\.) )/.test(lines[i])) { para.push(lines[i]); i++; }
    out.push(`<p>${inline(para.join(' '))}</p>`);
  }
  return out.join('');
}

export async function render(el, ctx) {
  const reg = await data('registry');
  return ({approach, hypotheses, architecture, limitations})[ctx.sub](el, reg, ctx);
}

function approach(el, reg) {
  const L = [['OBSERVED DATA', 'Counts, shares and distributions computed directly from the 10M rows (or exact aggregates of them).'],
    ['CONDITIONAL ESTIMATE', 'A statistic computed within a slice or after adjustment (fixed effects, residuals, CIs). Still data — but it depends on the conditioning chosen.'],
    ['MODEL SIMULATION', 'Output of the reconstructed generator run as Monte Carlo. Tests the reconstruction at the estimated parameters.'],
    ['STRUCTURAL SCENARIO', 'A model run with parameters moved away from the estimates, or the dependency graph itself: a statement about a hypothetical generator.'],
    ['VALIDATED RULE', 'A rule that passed its pre-declared criterion on all five splits; its confidence level says how strongly.']];
  el.innerHTML = header('Research & methodology', 'Approach & confidence scale', 'How a pattern becomes a rule, how strongly we believe it, and how every view on this site is labelled.') +
    `<div class="flow"><div><b>1 · Observe</b><span>RFC-4180 parse · 14 quality checks · profiling</span></div><div><b>2 · Discover</b><span>276 feature pairs · trees · forensics · graph</span></div>
      <div><b>3 · Formalise</b><span>rule statement + SQL validator + Python twin</span></div><div><b>4 · Validate</b><span>5 splits · effect sizes · BH per family · out-of-sample</span></div></div>
    <h2>Six-level confidence scale</h2>${table(Object.entries(reg.levels).map(([k, v]) => ({level: k, criterion: v, n: reg.rules.filter(r => r.level === k).length})), [{key: 'level', label: 'Level', f: v => level(v)}, {key: 'criterion', label: 'Criterion'}, {key: 'n', label: 'Entries', num: true}])}
    <h2>Output labels</h2><div class="grid g2">${L.map(([k, v]) => `<div class="card">${badge(k)}<p style="margin:6px 0 0">${esc(v)}</p></div>`).join('')}</div>
    <h2>Statistical stance</h2><div class="card"><ul>
      <li>Decisions rest on effect sizes (exact-match share, Cohen's w, Cramér's V, KS distance, maximum deviation), because with n = 10M every p-value is tiny.</li>
      <li>Where p-values are reported, Benjamini–Hochberg is applied within each test family, never pooled across unrelated families.</li>
      <li>Learned classes (cover-prone banks, slow banks) are fitted on one random half and tested on the other.</li>
      <li>Simpson checks: hour-of-day and country effects are re-estimated with bank fixed effects.</li>
      <li>Every rule states its best alternative and why it fits worse; rejected hypotheses stay on the record.</li>
      <li>Atlas edges are generation dependencies consistent with the data — not causal identification.</li></ul></div>`;
}

function hypotheses(el, reg, ctx) {
  const H = reg.hypotheses;
  el.innerHTML = header('Research & methodology', 'Hypothesis register', `All ${H.length} hypotheses in the order they were tested, including those rejected. Outcomes link to the rule they became.`) +
    `<div class="controls"><label class="ctl">Search<input id="hq" type="search" value="${esc(ctx.params.q || '')}"></label></div><div id="ho"></div>`;
  const draw = () => {
    const q = el.querySelector('#hq').value.toLowerCase(); ctx.setParams({q});
    el.querySelector('#ho').innerHTML = table(H.filter(h => !q || JSON.stringify(h).toLowerCase().includes(q)), [{key: 'id', label: 'ID'}, {key: 'hypothesis', label: 'Hypothesis'}, {key: 'test', label: 'Test'},
      {key: 'outcome', label: 'Outcome', f: v => md(v).replace(/^<p>|<\/p>$/g, '')}, {key: 'consequence', label: 'Consequence', f: v => esc(v).replace(/\b([RCADTPXGF]\d+b?)\b/g, '<a href="#/rules/explorer?id=$1">$1</a>')}], {h: 640, empty: 'No hypothesis matches.'});
  };
  el.querySelector('#hq').addEventListener('input', draw); draw();
}

function architecture(el) {
  const mods = [['src/ingestion.py', 'CSV → Parquet (RFC-4180, row count asserted) → slim typed table'], ['src/graph.py · stats.py', 'network metrics, PageRank, CIs, tails, detectors'],
    ['src/discovery.py', '276-pair dependency search, mediation triage, depth-3 trees'], ['src/forensics.py', 'Benford, cents, timestamp grain, grammar, change points, CI tests'],
    ['src/rules.py · rulelib.py', '34 SQL validators on 5 splits + pure-Python reference rules'], ['src/validation.py', 'runs validators, cross-checks SQL vs Python, writes the report'],
    ['src/evidence.py · cube.py · register.py', 'evidence tables, additive cubes, the evidence register and per-rule reports'], ['src/atlas.py · lineage.py', 'dependency atlas; SHA-256 lineage and schema contract'],
    ['src/charts.py · reporting.py', 'static figures, dashboard PDF and slide PDF'], ['src/webdata.py · web.py', 'browser aggregates (this site) and the static build'],
    ['dashboard/app.py', 'Streamlit edition of the lab (local)'], ['tests/', 'unit, output, submission, dashboard and browser end-to-end tests']];
  el.innerHTML = header('Research & methodology', 'Architecture', 'One evidence system feeds every surface: the PDFs, the Streamlit lab and this site read the same JSON artefacts, so a number cannot differ between them.') +
    `<div class="flow"><div><b>Raw CSV</b><span>4.6 GB · read-only</span></div><div><b>Parquet</b><span>DuckDB, out-of-core</span></div><div><b>Evidence JSON</b><span>validation · register · atlas · stats</span></div><div><b>Surfaces</b><span>PDFs · Streamlit · web</span></div></div>
    ${table(mods.map(([m, d]) => ({m, d})), [{key: 'm', label: 'Module', f: v => `<code>${esc(v)}</code>`}, {key: 'd', label: 'Responsibility'}])}
    <h2>Privacy and data-handling by design</h2><div class="card"><ul>
      <li>The browser receives aggregates only: an additive cube of ${fmt(10396)} cells, route patterns with n ≥ 150, the top-600 bank table, token shares from a sample, and summary statistics.</li>
      <li>No account numbers, party names or free-text details are shipped. BIC8 codes in the dataset are synthetic.</li>
      <li>The site is served with <code>noindex</code> headers and, until judging, behind Vercel deployment protection (team members only).</li>
      <li>Everything runs client-side: no analytics, no cookies, no third-party calls except Google Fonts.</li></ul></div>
    <h2>Front-end</h2><div class="card"><p>Vanilla ES modules, no framework or chart library: a hash router (<code>js/main.js</code>), a small SVG chart kit (<code>js/core.js</code>), the cube engine (<code>js/cube.js</code>), the Monte-Carlo generator (<code>js/sim.js</code>) and the JavaScript rule port (<code>js/rulelib.js</code>). Data files load lazily per page. Page state lives in the URL, so every view is linkable and survives refresh, back and forward.</p></div>`;
}

async function limitations(el) {
  const [lim, eco] = await Promise.all(['limitations', 'economic_interpretation'].map(f => fetch(`data/docs/${f}.md`).then(r => r.ok ? r.text() : `*${f}.md unavailable*`)));
  el.innerHTML = header('Research & methodology', 'Limitations & economics', 'What the analysis cannot claim, and how the reconstructed rules read economically. Economic readings are interpretation, labelled as such; the data is synthetic.') +
    `<div class="grid g2"><div class="card">${md(lim)}</div><div class="card">${md(eco)}</div></div>`;
}

import {data, esc, fmt, pct, sig, kpis, header, badge, level, tag, table, bars, chartBox, select, C} from '../core.js';
import {ruleDetail} from './rules.js';

const SPLITS = ['full', 'half_0', 'half_1', 'P1', 'P2'];
export async function render(el, ctx) {
  const [reg, m] = await Promise.all([data('registry'), data('meta')]);
  return ({scorecard, splits, reproducibility})[ctx.sub](el, reg, m, ctx);
}

function scorecard(el, reg, m, ctx) {
  const rules = reg.rules.filter(r => r.kind === 'rule'), pass = rules.filter(r => r.status === 'PASS').length;
  const types = ['ALL', ...new Set(rules.map(r => r.type))].sort();
  const t0 = types.includes(ctx.params.type) ? ctx.params.type : 'ALL';
  el.innerHTML = header('Validation centre', 'Scorecard', 'Every rule has a pre-declared acceptance criterion on effect size and is re-run on five splits: full data, two random halves (hash of row id) and two time periods. A rule passes only if it passes on all five.') +
    badge('VALIDATED RULE') + kpis([[`${pass}/${rules.length}`, 'validators pass'], [SPLITS.length, 'splits per rule'], [pct(m.validation.cross_check.R6_python_match), 'R6 SQL = Python'], [pct(m.validation.cross_check.C2_python_match), 'C2 SQL = Python'], [fmt(m.validation.runtime_s / 60, 1) + ' min', 'full validation runtime']]) +
    `<div class="controls">${select('vt', 'Rule type', types.map(t => [t, t === 'ALL' ? 'All types' : t]), t0)}</div><div id="vo"></div>
    <div class="note">Rule types (docs/methodology.md): A = deterministic (exact match on all rows), B = probabilistic (MLE + goodness-of-fit effect size), C = conditional (stratified contrasts, fixed effects), D = template/fingerprint, E = composite (joint predictions). Passing is necessary for a confidence level, not sufficient — see the six-level criteria.</div>`;
  const draw = () => {
    const t = el.querySelector('#vt').value; ctx.setParams({type: t === 'ALL' ? '' : t});
    const rows = rules.filter(r => t === 'ALL' || r.type === t);
    el.querySelector('#vo').innerHTML = table(rows, [{key: 'id', label: 'Rule', f: v => `<a href="#/validation/splits?id=${v}">${v}</a>`}, {key: 'title', label: 'Statement'}, {key: 'type', label: 'Type'}, {key: 'criterion', label: 'Acceptance', f: v => `<code>${esc(v)}</code>`},
      {key: 'status', label: 'Result', f: v => tag(v, v)}, {key: 'level', label: 'Level', f: v => level(v)}], {h: 640});
  };
  el.querySelector('#vt').addEventListener('change', draw); draw();
}

function splits(el, reg, m, ctx) {
  const rules = reg.rules.filter(r => r.kind === 'rule'), id = rules.some(r => r.id === ctx.params.id) ? ctx.params.id : 'R1';
  el.innerHTML = header('Validation centre', 'Split matrix', 'All metrics of one rule on each of the five splits, with the acceptance criterion applied to each.') +
    `<div class="controls">${select('vs', 'Rule', rules.map(r => [r.id, `${r.id} · ${r.title.slice(0, 70)}`]), id)}</div><div id="vso"></div>`;
  const draw = () => {
    const r = rules.find(x => x.id === el.querySelector('#vs').value); ctx.setParams({id: r.id});
    const k = Object.keys(r.metrics?.full || {}).find(x => x !== 'n' && typeof r.metrics.full[x] === 'number');
    el.querySelector('#vso').innerHTML = (k ? chartBox(`${esc(r.id)} · ${esc(k)} by split`, bars(SPLITS.map(s => ({label: s, value: r.metrics[s]?.[k] ?? 0, color: s === 'full' ? C.ink : C.blue, note: `n = ${fmt(r.metrics[s]?.n)}`})), {label: 'Split metric', h: 220, vfmt: v => sig(v, 5)}),
      `Acceptance: ${esc(r.criterion)} — must hold on every bar.`) : '') + '<div style="margin-top:14px"></div>' + ruleDetail(r, reg);
  };
  el.querySelector('#vs').addEventListener('change', draw); draw();
}

function reproducibility(el, reg, m) {
  const L = m.lineage, cc = m.validation.cross_check;
  el.innerHTML = header('Validation centre', 'Reproducibility', 'How to rebuild every number on this site from the raw CSV, and the checks that guard each step.') +
    kpis([[L.contract_ok ? 'OK' : 'BROKEN', 'schema contract'], [fmt(cc.sample), 'cross-check sample rows'], [pct(cc.R7_python_match), 'R7 SQL = Python'], [L.artefacts.length, 'hashed artefacts']]) +
    `<div class="grid g2"><div class="card"><h3>Rebuild from scratch</h3><div class="formula">python run_all.py          # ingestion → rules → evidence → charts → PDFs → web → tests
python -m src.validation    # re-run the 34 validators on 5 splits
python -m src.webdata       # rebuild this site's aggregate data
python -m src.web           # assemble web/dist
python -m pytest -q         # unit, output, dashboard and browser tests</div>
      <p>The raw CSV is never redistributed (competition rules 2.1–2.2). The site only ships aggregates: the explorer cube, route patterns with n ≥ 150, the top-600 bank table and summary statistics.</p></div>
    <div class="card"><h3>Two-implementation check</h3><p>Deterministic rules are implemented twice — in DuckDB SQL (<code>src/rules.py</code>) and in pure Python (<code>src/rulelib.py</code>) — and compared on a ${fmt(cc.sample)}-row sample: R6 ${pct(cc.R6_python_match)}, R7 ${pct(cc.R7_python_match)}, C2 ${pct(cc.C2_python_match)} agreement.
      The browser playground uses a third, JavaScript port (<code>web/app/js/rulelib.js</code>) whose parity with the Python reference is checked by the end-to-end tests.</p></div></div>
    <h2>Environment</h2><div class="card">${Object.entries(L.environment.packages).map(([k, v]) => tag(`${k} ${v}`, 'info')).join('')}<p class="mono">Python ${esc(L.environment.python)} · ${esc(L.environment.platform)}</p></div>
    <h2>Schema contract</h2>` + table(L.contract, Object.keys(L.contract[0] || {}).map(k => ({key: k, label: k, f: v => esc(typeof v === 'object' ? JSON.stringify(v) : v)}))) +
    `<p><a href="#/data/lineage">Full artefact list with SHA-256 →</a></p>`;
}

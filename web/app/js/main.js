// Router + navigation. Hash routes #/<group>/<page>?<state>. Page state lives in the query string, so refresh/back/forward restore it.
import {data, esc} from './core.js';

// [route, title, module, stage]. Stages: DISCOVER · RECONSTRUCT · CHALLENGE · VALIDATE · SIMULATE · EXPLAIN
export const NAV = [
  {g: "★ Judge's path", judge: true, items: [['tour', 'Guided tour · 2 minutes', 'tour', 'EXPLAIN']]},
  {g: '01 · Intelligence Command Centre', items: [['overview', 'Executive overview', 'overview', 'EXPLAIN'], ['command/coverage', 'Research coverage', 'command', 'EXPLAIN']]},
  {g: '02 · Data Observatory', items: [['data/summary', 'Dataset overview', 'data', 'DISCOVER'], ['data/quality', 'Data quality & integrity', 'data', 'DISCOVER'], ['data/dictionary', 'Feature dictionary', 'data', 'DISCOVER'],
    ['data/distributions', 'Distribution explorer', 'data', 'DISCOVER'], ['data/lineage', 'Data lineage', 'data', 'VALIDATE']]},
  {g: '03 · Payment Intelligence', items: [['feature/temporal', 'Temporal', 'features', 'RECONSTRUCT'], ['feature/currency', 'Currency & value', 'features', 'RECONSTRUCT'], ['feature/institution', 'Institution', 'features', 'RECONSTRUCT'],
    ['feature/route', 'Route', 'features', 'RECONSTRUCT'], ['feature/duration', 'Duration & continuity', 'features', 'RECONSTRUCT'], ['feature/fx', 'FX & participant', 'features', 'RECONSTRUCT'],
    ['feature/ttype', 'Transaction type', 'features', 'RECONSTRUCT'], ['feature/party', 'Party', 'features', 'RECONSTRUCT'], ['feature/token', 'Token', 'features', 'RECONSTRUCT'], ['feature/anomaly', 'Anomaly', 'features', 'RECONSTRUCT']]},
  {g: '04 · Generator Genome', items: [['genome/blueprint', 'Generator blueprint', 'genome', 'RECONSTRUCT'], ['rules/atlas', 'Rule dependency atlas', 'atlas', 'RECONSTRUCT'],
    ['rules/discovery', 'Feature relationship explorer', 'rules', 'DISCOVER'], ['genome/genealogy', 'Rule genealogy', 'genome', 'CHALLENGE'], ['method/hypotheses', 'Hypothesis registry', 'method', 'CHALLENGE']]},
  {g: '05 · Rule Foundry', items: [['rules/explorer', 'Rule explorer', 'rules', 'RECONSTRUCT'], ['foundry/builder', 'Rule builder', 'foundry', 'CHALLENGE'], ['rules/compare', 'Rule comparison', 'rules', 'CHALLENGE'],
    ['rules/registry', 'Rule evidence registry', 'rules', 'VALIDATE']]},
  {g: '06 · Research Playground', items: [['lab/explorer', 'Observed data explorer', 'explorer', 'DISCOVER'], ['lab/playground', 'Synthetic rule playground', 'playground', 'RECONSTRUCT'],
    ['lab/simulator', 'Scenario studio', 'simulator', 'SIMULATE'], ['lab/sensitivity', 'Sensitivity analysis', 'sensitivity', 'SIMULATE'], ['lab/routes', 'Route playground', 'routes', 'DISCOVER'], ['lab/anomalies', 'Anomaly explorer', 'anomalies', 'DISCOVER']]},
  {g: '07 · Forensic Intelligence', items: [['forensics/replay', 'Forensic replay', 'replay', 'CHALLENGE'], ['forensics/distribution', 'Distribution fingerprints', 'forensics', 'CHALLENGE'],
    ['forensics/digits', 'Digit & grammar forensics', 'forensics', 'CHALLENGE'], ['forensics/tests', 'Statistical tests (BH)', 'forensics', 'VALIDATE'], ['forensics/alternatives', 'Alternative hypotheses', 'forensics', 'CHALLENGE'],
    ['forensics/stability', 'Stability testing', 'forensics', 'VALIDATE']]},
  {g: '08 · Validation Centre', items: [['validation/scorecard', 'Independent validation', 'validation', 'VALIDATE'], ['validation/splits', 'Split robustness', 'validation', 'VALIDATE'],
    ['forensics/counterexamples', 'Counterexamples', 'forensics', 'CHALLENGE'], ['method/approach', 'Confidence assessment', 'method', 'VALIDATE'], ['validation/reproducibility', 'Reproducibility', 'validation', 'VALIDATE']]},
  {g: '09 · Research Library', items: [['library/ledger', 'Evidence ledger', 'library', 'VALIDATE'], ['method/architecture', 'Technical architecture', 'method', 'EXPLAIN'],
    ['method/limitations', 'Limitations & economics', 'method', 'EXPLAIN'], ['library/governance', 'Data governance & references', 'library', 'EXPLAIN']]},
  {g: '10 · Deliverables', items: [['deliverables', 'Submission files & exports', 'deliverables', 'EXPLAIN']]},
];
// Judge-facing research journey (highlighted in the menu); everything else is the extended research environment.
// "How to read this page" for the judge-facing and most technical pages: what it shows, why it matters, how to read it, limits.
const GUIDE = {
  'overview': ['The three strongest reconstructed rules and what is still open.', 'C2 is exact, R1 is a law with one constant, R2 shows we overturned our own rule.', 'Each card links to the rule, its records (replay) and its evidence ID.', 'Synthetic data: rules describe this generator, not real Swift traffic.'],
  'genome/blueprint': ['The reconstructed generator, stage by stage.', 'It turns 34 separate rules into one mechanism.', 'Badges give each rule’s confidence; red notes list what is unresolved.', 'Stages are an ordering we inferred; the source code is not known.'],
  'rules/explorer': ['Every rule with formula, executable logic and metrics on five partitions.', 'This is the evidence behind each statement in the PDFs.', 'Pick a rule; the split table should be stable across rows; "Violations" lists exceptions.', 'Passing a validator is necessary, not sufficient — read the confidence level.'],
  'genome/genealogy': ['How a rule was reached, from the logged hypotheses (H1–H38).', 'Shows the team rejecting ideas when evidence turned against them.', 'Red steps = rejected, blue = accepted; the last step is the final validation.', 'Rules without a logged history say so; none is invented.'],
  'forensics/replay': ['Real payments that support or contradict a rule.', 'Lets a judge see the exceptions, not just a percentage.', 'Counts at the top are exact over all rows; the table is a fixed sample.', 'Records are de-identified; at most 75 per rule are shipped.'],
  'validation/scorecard': ['Each rule’s acceptance criterion and result.', 'Criteria were fixed before the test, so a pass is not curve-fitting.', 'Open a rule for its metrics on all five partitions.', 'Effect sizes, not p-values, decide acceptance (n = 10 million).'],
  'library/ledger': ['Every evidence record with method, parameters, result, n and source file.', 'Any number on the site or in the PDFs traces back to one of these IDs.', 'Search by rule (C2) or ID (EV-RULE-009); RULE/VAL/CX/STAT/DISC are the record types.', 'SHA-256 prefixes identify the exact artefact version.'],
  'lab/explorer': ['Exact counts and distributions for any filter combination of 10 fields.', 'Lets you check conditional patterns yourself.', 'Selection A vs reference B; read ratios, Cohen’s d and KS, not p-values.', 'Medians and KS are at bin resolution; associations, not causes.'],
  'forensics/tests': ['All recorded statistical tests with Benjamini–Hochberg control per family.', 'Shows which differences survive multiple testing.', 'q < .05 = significant after correction; with millions of rows, read the effect column.', 'BH is applied within families, never pooled.'],
  'lab/simulator': ['The reconstructed generator run as a seeded Monte Carlo, next to the observed data.', 'If the rebuilt rules reproduce the data, the reconstruction is credible.', 'At the estimates it is a test; moving a slider makes it a hypothetical scenario.', 'Simulated values are model output, never observations.'],
};
export const JUDGE = new Set(['tour', 'overview', 'genome/blueprint', 'rules/explorer', 'forensics/replay', 'validation/scorecard', 'lab/simulator']);
const ROUTES = Object.fromEntries(NAV.flatMap(s => s.items.map(([r, t, m, st]) => [r, {title: t, mod: m, group: s.g, stage: st}])));
const main = document.getElementById('main');
let current = null;

export function parse() {
  const h = location.hash.replace(/^#\/?/, '') || 'overview';
  const [path, qs] = h.split('?');
  return {path: path.replace(/\/$/, ''), params: Object.fromEntries(new URLSearchParams(qs || ''))};
}
export function go(path, params = {}) {
  const qs = new URLSearchParams(Object.entries(params).filter(([, v]) => v !== '' && v != null)).toString();
  location.hash = '#/' + path + (qs ? '?' + qs : '');
}
// Update query state without adding a history entry for every slider move
export function setParams(params) {
  const {path} = parse();
  const qs = new URLSearchParams(Object.entries(params).filter(([, v]) => v !== '' && v != null)).toString();
  history.replaceState(null, '', '#/' + path + (qs ? '?' + qs : ''));
}

function buildNav() {
  const closed = new Set(JSON.parse(safeGet('srl-closed') || '[]'));
  let n = 0;
  document.getElementById('nav').innerHTML = NAV.map(s => `<div class="ng${closed.has(s.g) ? ' closed' : ''}${s.judge ? ' judge' : ''}" data-g="${esc(s.g)}"><button type="button" aria-expanded="${!closed.has(s.g)}">${esc(s.g)}</button>` +
    s.items.map(([r, t]) => `<a class="ni${JUDGE.has(r) ? ' jp' : ''}" href="#/${r}" data-r="${r}"${JUDGE.has(r) ? ' title="Judge-facing research journey"' : ''}><small>${JUDGE.has(r) ? '★' : String(++n).padStart(2, '0')}</small>${esc(t)}</a>`).join('') + '</div>').join('') +
    '<div class="sidefoot" style="margin-top:10px"><b>★</b> = judge-facing journey: Tour → Overview → Blueprint → Rule explorer → Forensic replay → Validation → Scenario studio. Everything else is the extended research environment for deeper questions.</div>';
  document.querySelectorAll('.ng>button').forEach(b => b.addEventListener('click', () => {
    const g = b.parentElement; g.classList.toggle('closed'); b.setAttribute('aria-expanded', !g.classList.contains('closed'));
    safeSet('srl-closed', JSON.stringify([...document.querySelectorAll('.ng.closed')].map(x => x.dataset.g)));
  }));
}
const safeGet = k => { try { return localStorage.getItem(k); } catch { return null; } };
const safeSet = (k, v) => { try { localStorage.setItem(k, v); } catch { /* storage blocked */ } };

async function navSearch() {
  const inp = document.getElementById('navsearch'), reg = await data('registry').catch(() => null);
  inp.addEventListener('input', () => {
    const q = inp.value.trim().toLowerCase();
    document.querySelectorAll('.ni').forEach(a => a.classList.toggle('hide', !!q && !a.textContent.toLowerCase().includes(q)));
    if (q) document.querySelectorAll('.ng').forEach(g => g.classList.remove('closed'));
  });
  inp.addEventListener('keydown', e => {
    if (e.key !== 'Enter') return;
    const q = inp.value.trim();
    if (/^EV-/i.test(q)) { go('library/ledger', {q: q.toUpperCase()}); inp.value = ''; inp.dispatchEvent(new Event('input')); return; }
    const rule = reg?.rules.find(r => r.id.toLowerCase() === q.toLowerCase());
    if (rule) { go('rules/explorer', {id: rule.id}); inp.value = ''; inp.dispatchEvent(new Event('input')); return; }
    const first = [...document.querySelectorAll('.ni:not(.hide)')][0]; if (first) { location.hash = first.getAttribute('href'); inp.value = ''; inp.dispatchEvent(new Event('input')); }
  });
}

async function route() {
  const {path, params} = parse();
  const r = ROUTES[path];
  document.querySelectorAll('.ni').forEach(a => { const on = a.dataset.r === path; a.classList.toggle('on', on); if (on) a.setAttribute('aria-current', 'page'); else a.removeAttribute('aria-current'); });
  if (document.getElementById('side').classList.contains('open')) { document.getElementById('side').classList.remove('open'); document.body.classList.remove('navlock'); const mb = document.getElementById('menu'); mb.setAttribute('aria-expanded', 'false'); mb.textContent = 'Menu'; }
  if (!r) { main.innerHTML = `<div class="sect">404</div><h1>Page not found</h1><p class="lede">No page at <code>#/${esc(path)}</code>. <a href="#/overview">Return to the command centre</a>.</p>`; document.title = 'Not found · ORVANTA'; return; }
  document.title = `${r.title} · ORVANTA`;
  const token = Symbol(); current = token;
  if (main.dataset.path !== path) { main.innerHTML = '<div class="loading">Loading data…</div>'; main.dataset.path = path; window.scrollTo(0, 0); }
  try {
    const mod = await import(`./pages/${r.mod}.js`);
    if (current !== token) return;
    const sub = path.split('/')[1] || path;
    const wrap = document.createElement('div');
    wrap.innerHTML = `<div class="crumbs"><a href="#/overview">ORVANTA</a> / ${esc(r.group.replace(/^\d+ · /, ''))} / ${esc(r.title)} <span class="stage st-${r.stage.toLowerCase()}" title="Research stage">${esc(r.stage)}</span></div>`;
    if (GUIDE[path]) { const g = GUIDE[path]; wrap.insertAdjacentHTML('beforeend', `<details class="guide"><summary>How to read this page</summary><dl class="kv"><dt>What it shows</dt><dd>${esc(g[0])}</dd><dt>Why it matters</dt><dd>${esc(g[1])}</dd><dt>How to read it</dt><dd>${esc(g[2])}</dd><dt>Limits</dt><dd>${esc(g[3])}</dd></dl></details>`); }
    const body = document.createElement('div'); wrap.appendChild(body);
    await mod.render(body, {sub, path, params, setParams, go});
    if (current !== token) return;
    main.replaceChildren(wrap);
    main.focus({preventScroll: true});
  } catch (e) {
    console.error(e);
    main.innerHTML = `<div class="err">This page failed to load: ${esc(e.message)}</div><p>Try reloading. If the problem persists the build data may be missing — run <code>python -m src.web</code>.</p>`;
  }
}

async function footer() {
  try {
    const m = await data('meta');
    document.getElementById('sidefoot').innerHTML = `<b>${(m.rows / 1e6).toFixed(0)}M</b> rows · <b>${m.feature_groups}</b> feature groups<br>Build <b>${esc(m.generated.slice(0, 16).replace('T', ' '))}</b><br>Aggregates only — no row-level records reach the browser.<br>Synthetic data: findings describe the generator, not real Swift traffic.`;
  } catch { document.getElementById('sidefoot').textContent = 'Build metadata unavailable.'; }
}

buildNav(); navSearch(); footer();
// Mobile drawer: toggles, locks background scroll, closes on Escape / selection / outside resize, returns focus to the menu button.
const side = document.getElementById('side'), menuBtn = document.getElementById('menu');
const setNav = open => { side.classList.toggle('open', open); document.body.classList.toggle('navlock', open && window.innerWidth <= 900); menuBtn.setAttribute('aria-expanded', open); menuBtn.textContent = open ? 'Close' : 'Menu'; if (open) document.getElementById('navsearch').focus({preventScroll: true}); };
menuBtn.addEventListener('click', () => setNav(!side.classList.contains('open')));
document.addEventListener('keydown', e => { if (e.key === 'Escape' && side.classList.contains('open')) { setNav(false); menuBtn.focus(); } });
// Charts size themselves to the viewport at render time; re-render when the width crosses a bucket (rotation, resize).
const bucket = () => { const w = window.innerWidth; return w < 360 ? 0 : w < 480 ? 1 : w < 620 ? 2 : w < 1000 ? 3 : 4; };
let lastBucket = bucket(), rz;
window.addEventListener('resize', () => { clearTimeout(rz); rz = setTimeout(() => { if (window.innerWidth > 900) setNav(false); const b = bucket(); if (b !== lastBucket) { lastBucket = b; delete main.dataset.path; route(); } }, 250); });
window.addEventListener('hashchange', route);
route();

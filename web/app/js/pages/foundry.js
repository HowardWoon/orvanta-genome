// Rule Foundry · Rule Builder: formulate a structured hypothesis and test it on the 10M-row cube, with stratification and a
// temporal replication (discover on P1, validate on P2). A user hypothesis is never promoted to a validated rule automatically.
import {esc, fmt, pct, sig, kpis, header, badge, table, bars, grouped, chartBox, select, download, C} from '../core.js';
import {cube, aggregate, breakdown} from '../cube.js';

const erfc = x => { const z = Math.abs(x), t = 1 / (1 + .5 * z), r = t * Math.exp(-z * z - 1.26551223 + t * (1.00002368 + t * (.37409196 + t * (.09678418 + t * (-.18628806 + t * (.27886807 + t * (-1.13520398 + t * (1.48851587 + t * (-.82215223 + t * .17087277))))))))); return x >= 0 ? r : 2 - r; };
const pNorm2 = z => erfc(Math.abs(z) / Math.SQRT2);                                         // two-sided normal p
const pChi2 = (x, k) => { if (k <= 0) return 1; const h = 2 / (9 * k), z = (Math.cbrt(x / k) - (1 - h)) / Math.sqrt(h); return .5 * erfc(z / Math.SQRT2); };  // Wilson–Hilferty
const fp = p => p == null ? '—' : p < 1e-300 ? '< 1e-300' : sig(p, 3);

const TARGETS = [['manual', 'Manual step (> 120 s) — binary'], ['amount', 'ln(USD amount) — continuous'], ...['ttype', 'cur', 'anom', 'otype', 'btype', 'pc', 'fx', 'cont'].map(d => [d, `Distribution of ${d} — categorical`])];

export async function render(el, ctx) {
  const cb = await cube(), P = ctx.params;
  const lab = d => cb.labels[d] || d;
  const st = {target: P.target || 'manual', cd: P.cd || 'pc', cv: P.cv || '2', comp: P.comp || 'rest', ov: P.ov || '', strat: P.strat || 'none', dir: P.dir || 'lower', scope: P.scope || 'ALL'};
  el.innerHTML = header('Rule foundry', 'Rule builder',
    'Write a hypothesis as IF condition → THEN examine target → COMPARED WITH a reference → WHILE stratifying for a third variable. The builder chooses the test from the target type, runs it on exact aggregates of all 10M rows, checks Simpson reversals, and replicates the result on an independent time period.') +
    badge('CONDITIONAL ESTIMATE') + `<div class="note red">A hypothesis tested here is a user hypothesis, not a reconstructed rule. Promotion to the registry needs a validator on five splits, an alternative tested and counterexamples examined (see Confidence assessment).</div>
    <div class="card"><div class="fgrid">
      ${select('bt', 'THEN examine (target)', TARGETS, st.target)}
      ${select('bcd', 'IF condition: variable', cb.dims.filter(d => !['period'].includes(d)).map(d => [d, lab(d)]), st.cd)}<span id="bcvw"></span>
      ${select('bcomp', 'COMPARED WITH', [['rest', 'all other values (complement)'], ['value', 'one other value']], st.comp)}<span id="bovw"></span>
      ${select('bst', 'WHILE stratifying for', [['none', 'nothing (crude comparison)'], ...cb.dims.filter(d => d !== 'period').map(d => [d, lab(d)])], st.strat)}
      ${select('bdir', 'Expected direction', [['higher', 'condition is higher'], ['lower', 'condition is lower'], ['different', 'just different']], st.dir)}
      ${select('bsc', 'Time scope', [['ALL', 'All data (discovery = P1, replication = P2)'], ['P1', 'P1 only'], ['P2', 'P2 only']], st.scope)}
    </div><div class="controls"><button id="brun">Run test</button><button class="sec" id="bexp">Export hypothesis report</button></div></div><div id="bo"></div>`;
  const $ = id => el.querySelector('#' + id);
  const valSel = (wrap, id, dim, cur, label, exclude) => { const vs = cb.values[dim].filter(v => v !== exclude); $(wrap).innerHTML = select(id, label, vs.map(v => [v, v]), vs.includes(cur) ? cur : vs[0]); $(id).addEventListener('change', run); };
  const refresh = () => { valSel('bcvw', 'bcv', $('bcd').value, st.cv, 'IF condition: value'); $('bovw').style.display = $('bcomp').value === 'value' ? '' : 'none'; valSel('bovw', 'bov', $('bcd').value, st.ov, 'Other value', $('bcv').value); };
  ['bcd', 'bcomp'].forEach(id => $(id).addEventListener('change', () => { refresh(); run(); }));
  ['bt', 'bst', 'bdir', 'bsc'].forEach(id => $(id).addEventListener('change', run));
  $('brun').onclick = run;
  let report = '';
  $('bexp').onclick = () => report && download('hypothesis_report.md', report, 'text/markdown');
  refresh();

  function test(base, condF, compF, target) {   // returns {effect, label, ci, p, nA, nB, A, B}
    const fa = {...base, ...condF}, fb = {...base, ...compF};
    if (target === 'manual' || target === 'amount') {
      const A = aggregate(cb, fa), B = aggregate(cb, fb);
      if (!A.n || !B.n) return null;
      if (target === 'manual') {
        const pa = A.manual / A.n, pb = B.manual / B.n, d = pa - pb, se = Math.sqrt(pa * (1 - pa) / A.n + pb * (1 - pb) / B.n), p0 = (A.manual + B.manual) / (A.n + B.n);
        const z = d / Math.sqrt(p0 * (1 - p0) * (1 / A.n + 1 / B.n)), or = (pa / (1 - pa)) / (pb / (1 - pb)), seor = Math.sqrt(1 / A.manual + 1 / (A.n - A.manual) + 1 / B.manual + 1 / (B.n - B.manual));
        return {kind: 'binary', effect: d, se, ci: [d - 1.96 * se, d + 1.96 * se], p: pNorm2(z), nA: A.n, nB: B.n, a: pa, b: pb, or, orci: [or * Math.exp(-1.96 * seor), or * Math.exp(1.96 * seor)], method: 'two-proportion z-test; risk difference and odds ratio with 95% CI'};
      }
      const ma = A.s1 / A.n, mb = B.s1 / B.n, va = A.s2 / A.n - ma * ma, vb = B.s2 / B.n - mb * mb, d = ma - mb, se = Math.sqrt(va / A.n + vb / B.n);
      const sp = Math.sqrt(((A.n - 1) * va + (B.n - 1) * vb) / (A.n + B.n - 2));
      return {kind: 'continuous', effect: d, se, ci: [d - 1.96 * se, d + 1.96 * se], p: pNorm2(d / se), nA: A.n, nB: B.n, a: ma, b: mb, cohen: d / sp, method: "Welch t-test on ln(amount) from exact sums (normal approximation, n large); Cohen's d"};
    }
    const bA = breakdown(cb, fa, target), bB = breakdown(cb, fb, target), vals = cb.values[target];
    const nA = vals.reduce((s, v) => s + (bA[v] || 0), 0), nB = vals.reduce((s, v) => s + (bB[v] || 0), 0); if (!nA || !nB) return null;
    let chi = 0, k = 0; const N = nA + nB;
    for (const v of vals) { const col = (bA[v] || 0) + (bB[v] || 0); if (!col) continue; k++; for (const [o, n] of [[bA[v] || 0, nA], [bB[v] || 0, nB]]) { const e = n * col / N; chi += (o - e) ** 2 / e; } }
    const V = Math.sqrt(chi / (N * Math.max(Math.min(1, k - 1), 1)));
    return {kind: 'categorical', effect: V, se: null, ci: null, p: pChi2(chi, k - 1), chi, dof: k - 1, nA, nB, distA: vals.map(v => (bA[v] || 0) / nA), distB: vals.map(v => (bB[v] || 0) / nB), vals, method: "χ² test of homogeneity (2 × k); effect size Cramér's V"};
  }

  function run() {
    Object.assign(st, {target: $('bt').value, cd: $('bcd').value, cv: $('bcv').value, comp: $('bcomp').value, ov: $('bov')?.value, strat: $('bst').value, dir: $('bdir').value, scope: $('bsc').value});
    ctx.setParams({...st, ov: st.comp === 'value' ? st.ov : ''});
    if (st.target === st.cd) { $('bo').innerHTML = '<div class="empty">The target and the condition are the same variable — choose a different target.</div>'; return; }
    const cond = {[st.cd]: new Set([st.cv])}, comp = {[st.cd]: new Set(st.comp === 'value' ? [st.ov] : cb.values[st.cd].filter(v => v !== st.cv))};
    const scopeF = st.scope === 'ALL' ? {} : {period: new Set([st.scope])};
    const main = test(scopeF, cond, comp, st.target);
    if (!main) { $('bo').innerHTML = `<div class="empty">One of the two groups is empty in this scope (${esc(lab(st.cd))} = ${esc(st.cv)}). This combination does not occur — choose another value.</div>`; return; }
    const strata = st.strat === 'none' || st.strat === st.cd || st.strat === st.target ? [] : cb.values[st.strat].map(v => ({v, r: test({...scopeF, [st.strat]: new Set([v])}, cond, comp, st.target)})).filter(x => x.r && x.r.nA >= 30 && x.r.nB >= 30);
    let pooled = null;
    if (strata.length && main.kind !== 'categorical') { let w = 0, s = 0; for (const {r} of strata) { const wi = 1 / (r.se ** 2 || 1e-12); w += wi; s += wi * r.effect; } pooled = {effect: s / w, se: Math.sqrt(1 / w)}; }
    if (strata.length && main.kind === 'categorical') { const N = strata.reduce((a, x) => a + x.r.nA + x.r.nB, 0); pooled = {effect: strata.reduce((a, x) => a + x.r.effect * (x.r.nA + x.r.nB), 0) / N}; }
    const simpson = pooled && main.kind !== 'categorical' && Math.sign(pooled.effect) !== Math.sign(main.effect) && Math.abs(pooled.effect) > 2 * pooled.se;
    const disc = st.scope === 'ALL' ? test({period: new Set(['P1'])}, cond, comp, st.target) : null, val = st.scope === 'ALL' ? test({period: new Set(['P2'])}, cond, comp, st.target) : null;
    const eff = pooled ? pooled.effect : main.effect;
    const dirOK = main.kind === 'categorical' || st.dir === 'different' || (st.dir === 'higher' ? eff > 0 : eff < 0);
    const tiny = main.kind === 'binary' ? Math.abs(eff) < .005 : main.kind === 'continuous' ? Math.abs(main.cohen) < .05 : eff < .02;
    const replicates = disc && val && (main.kind === 'categorical' ? Math.abs(disc.effect - val.effect) < Math.max(.02, .25 * disc.effect) : Math.sign(disc.effect) === Math.sign(val.effect) && Math.abs(val.effect - disc.effect) < 3 * Math.hypot(disc.se, val.se) + .1 * Math.abs(disc.effect));
    const verdict = !dirOK ? ['REVERSED / NOT SUPPORTED', 'fail'] : tiny ? ['NEGLIGIBLE EFFECT', 'warn'] : simpson ? ['EXPLAINED BY THE STRATIFIER (Simpson)', 'warn'] : disc && !replicates ? ['DOES NOT REPLICATE ACROSS PERIODS', 'warn'] : ['SUPPORTED IN THIS DATA', 'pass'];
    const effTxt = r => r.kind === 'binary' ? `${(100 * r.effect).toFixed(2)} pt (CI ${(100 * r.ci[0]).toFixed(2)} to ${(100 * r.ci[1]).toFixed(2)})` : r.kind === 'continuous' ? `${sig(r.effect, 3)} ln units = ×${sig(Math.exp(r.effect), 3)} (CI ×${sig(Math.exp(r.ci[0]), 3)}–×${sig(Math.exp(r.ci[1]), 3)}), d = ${sig(r.cohen, 3)}` : `Cramér's V = ${sig(r.effect, 3)} (χ² = ${fmt(r.chi)}, dof ${r.dof})`;
    const spec = `IF ${lab(st.cd)} = ${st.cv}\nTHEN examine ${TARGETS.find(t => t[0] === st.target)[1]}\nCOMPARED WITH ${st.comp === 'value' ? `${lab(st.cd)} = ${st.ov}` : `all other ${lab(st.cd)} values`}\nWHILE stratifying for ${st.strat === 'none' ? '— (crude)' : lab(st.strat)}\nEXPECT ${st.dir}\nSCOPE ${st.scope === 'ALL' ? 'all rows; discover on P1, replicate on P2' : st.scope}`;
    $('bo').innerHTML = `<div class="grid g2"><div class="card"><h3>Hypothesis specification</h3><div class="formula">${esc(spec)}</div><div class="mono">Method: ${esc(main.method)}</div></div>
      <div class="card ${verdict[1] === 'pass' ? 'y' : 'warn'}"><h3>Result: ${verdict[0]}</h3><p>${effTxt(main)}${pooled && main.kind !== 'categorical' ? `<br>Stratified (inverse-variance pooled within ${esc(lab(st.strat))}): ${main.kind === 'binary' ? (100 * pooled.effect).toFixed(2) + ' pt' : sig(pooled.effect, 3) + ' ln units'} ± ${main.kind === 'binary' ? (196 * pooled.se).toFixed(2) + ' pt' : sig(1.96 * pooled.se, 2)}` : ''}${pooled && main.kind === 'categorical' ? `<br>Mean within-stratum V: ${sig(pooled.effect, 3)}` : ''}</p>
        <p class="mono">p = ${fp(main.p)} — with n in the millions read the effect size, not the p-value.</p></div></div>` +
      kpis([[fmt(main.nA), 'rows meeting the condition'], [fmt(main.nB), 'rows in the comparison'], ...(main.kind === 'binary' ? [[pct(main.a, 2), 'manual share · condition'], [pct(main.b, 2), 'manual share · comparison'], [`${sig(main.or, 3)}`, `odds ratio (CI ${sig(main.orci[0], 3)}–${sig(main.orci[1], 3)})`]] :
        main.kind === 'continuous' ? [['$' + fmt(Math.exp(main.a), 0), 'geometric mean · condition'], ['$' + fmt(Math.exp(main.b), 0), 'geometric mean · comparison']] : [])]) +
      (main.kind === 'categorical' ? chartBox(`Distribution of ${esc(lab(st.target))}`, grouped(main.vals, [{name: 'condition', color: C.blue, values: main.distA}, {name: 'comparison', color: C.coral, values: main.distB}], {label: 'Builder dist', vfmt: v => pct(v, 2), yfmt: v => pct(v, 0)}), '') : '') +
      (disc ? `<h3>Temporal replication</h3>` + table([{split: 'P1 · discovery (before 15 Jun 2023)', r: disc}, {split: 'P2 · validation (from 15 Jun 2023)', r: val}].filter(x => x.r), [{key: 'split', label: 'Partition'}, {key: 'r', label: 'n (condition / comparison)', f: r => `${fmt(r.nA)} / ${fmt(r.nB)}`}, {key: 'r', label: 'Effect', f: r => effTxt(r)}, {key: 'r', label: 'p', num: true, f: r => fp(r.p)}]) +
        `<div class="note">${replicates ? 'The effect replicates on the independent later period.' : 'The effect differs between periods — treat it as unstable.'} Random halves are not in the browser cube; the registry validators also check two hash-random halves.</div>` : '') +
      (strata.length ? `<h3>Within each stratum of ${esc(lab(st.strat))}</h3>` + chartBox('Effect by stratum', bars(strata.map(x => ({label: x.v, value: main.kind === 'binary' ? 100 * x.r.effect : x.r.effect, color: x.r.effect >= 0 ? C.blue : C.coral, note: `n = ${fmt(x.r.nA)} / ${fmt(x.r.nB)}`})), {horizontal: true, left: 160, label: 'Strata', vfmt: v => main.kind === 'binary' ? v.toFixed(2) + ' pt' : sig(v, 3)}),
        simpson ? 'The crude effect reverses inside strata: the stratifier explains it (Simpson).' : 'Strata with fewer than 30 rows on either side are omitted.') : '') +
      `<div class="grid g2"><div class="card"><h3>Assumptions</h3><ul><li>Rows treated as independent draws (true for the generator's per-payment draws; bursts such as X1/X2 violate it locally).</li><li>${main.kind === 'continuous' ? 'ln(amount) has finite variance; normal approximation is safe at these n.' : main.kind === 'binary' ? 'Normal approximation to the binomial (n large).' : 'Expected counts ≥ 5 in most cells.'}</li><li>Currencies outside the top 12 pooled as "Other"; participants 6+ and FX 3+ pooled.</li></ul></div>
        <div class="card"><h3>Limitations</h3><ul><li>Association, not intervention: the generator may set both variables from a common driver (check the atlas).</li><li>Only the ten cube dimensions are available here; bank- and country-level effects need the registry validators.</li><li>One stratifier at a time.</li></ul></div></div>`;
    report = `# Hypothesis report (ORVANTA Rule Builder)\n\n\`\`\`\n${spec}\n\`\`\`\n\n- Method: ${main.method}\n- Result: **${verdict[0]}** — ${effTxt(main)}\n- n: ${main.nA} (condition) vs ${main.nB} (comparison); p = ${fp(main.p)}\n` +
      (pooled ? `- Stratified by ${lab(st.strat)}: ${sig(pooled.effect, 4)}${simpson ? ' (Simpson reversal)' : ''}\n` : '') + (disc ? `- P1 (discovery): ${effTxt(disc)}\n- P2 (validation): ${effTxt(val)}\n- Replicates: ${replicates ? 'yes' : 'no'}\n` : '') +
      `\nSource: explorer cube (exact aggregates of all 10,000,000 rows). This is a user hypothesis, not a validated generator rule.\n`;
  }
  run();
}

import {data, esc, fmt, pct, sig, usd, kpis, header, badge, level, tag, table, bars, grouped, lines, scatter, distCompare, chartBox, select, download, toCSV, C} from '../core.js';
import {cube, aggregate, compare, ksLabel} from '../cube.js';

export async function render(el, ctx) {
  const m = await data('meta');
  return ({distribution, digits, tests, stability, counterexamples, alternatives})[ctx.sub](el, m, ctx);
}

async function distribution(el, m, ctx) {
  const cb = await cube(), st = m.stats, ar = st.amount_residual;
  const dims = cb.dims, d0 = dims.includes(ctx.params.d) ? ctx.params.d : 'otype';
  el.innerHTML = header('Statistical forensics', 'Distribution analysis', 'Shape, tails and conditional distributions. The amount model claims ln(amount) residuals are Gaussian with a lognormal (not power-law) tail; the checks below test that claim.') +
    badge('OBSERVED DATA') + badge('CONDITIONAL ESTIMATE') +
    kpis([[sig(ar.sd, 4), 'residual sd (ln)'], [sig(ar.skew, 3), 'skewness'], [sig(ar.excess_kurtosis, 3), 'excess kurtosis'], [sig(ar.ks_D_vs_normal, 3), 'KS D vs normal']]) +
    `<div class="grid g2">
      ${chartBox('Q–Q: standardised ln-amount residuals vs normal', scatter(ar.qq.map(q => ({x: q.normal, y: q.empirical, label: 'q = ' + q.q})), {label: 'QQ', diag: true, r: 4, alpha: .9, xlabel: 'normal quantile', ylabel: 'empirical'}), 'Residual after segment and sender-country effects, 400k normal payments. Points on the dashed line = Gaussian.')}
      ${chartBox('Hill tail index α(k)', lines(st.hill.map(h => fmt(h.k)), [{name: 'α', color: C.blue, values: st.hill.map(h => h.alpha), points: true}], {label: 'Hill', zero: false, vfmt: v => sig(v, 3)}), 'A power-law tail gives a flat α; α drifting with k is the lognormal signature (A3).')}
      ${chartBox('Exceedance: model-implied vs observed', grouped(st.exceedance.map(x => usd(x.threshold)), [{name: 'observed', color: C.blue, values: st.exceedance.map(x => x.observed)}, {name: 'model', color: C.yellow, values: st.exceedance.map(x => x.predicted)}], {label: 'Exceedance', vfmt: fmt}), 'Counts of payments above each threshold. Ratios: ' + st.exceedance.map(x => sig(x.ratio, 3)).join(' · '))}
      ${chartBox('Largest amounts by label', table(st.top_amounts, Object.keys(st.top_amounts[0] || {}).map(k => ({key: k, label: k}))), 'Labels among the 1,000 largest amounts.')}
    </div>
    <h2>Conditional ECDF</h2><div class="controls">${select('fd', 'Split amounts by', dims.map(d => [d, cb.labels[d]]), d0)}${select('fm', 'Variable', [['amt', 'Amount'], ['dur', 'Duration']], ctx.params.v || 'amt')}</div><div id="fe"></div>`;
  const draw = () => {
    const d = el.querySelector('#fd').value, v = el.querySelector('#fm').value; ctx.setParams({d, v});
    const vals = cb.values[d].slice(0, 6), pal = [C.blue, C.coral, C.ink, C.teal, C.yellow, C.grey];
    const series = vals.map((x, i) => { const a = aggregate(cb, {[d]: new Set([x])}); return {name: `${x} (n=${fmt(a.n)})`, color: pal[i], counts: v === 'amt' ? a.ah : a.dh}; });
    const edges = v === 'amt' ? cb.amt_edges : [...cb.dur_edges, 16];
    const pairs = series.length >= 2 ? (() => { const A = aggregate(cb, {[d]: new Set([vals[0]])}), B = aggregate(cb, {[d]: new Set([vals[1]])}); const c = compare(cb, A, B); return v === 'amt' ? c.ksAmt : c.ksDur; })() : null;
    el.querySelector('#fe').innerHTML = chartBox(`ECDF of ${v === 'amt' ? 'USD amount' : 'duration'} by ${esc(cb.labels[d])}`, distCompare(edges, series, {ecdf: true, label: 'ECDF', binLabel: e => v === 'amt' ? (e % 1 === 0 ? '$' + (e >= 0 ? fmt(10 ** e) : 10 ** e) : '') : (2 ** e >= 3600 ? fmt(2 ** e / 3600, 1) + 'h' : fmt(2 ** e) + 's'), xt: 30}),
      `${vals.length < cb.values[d].length ? `First 6 of ${cb.values[d].length} values shown. ` : ''}${pairs != null ? `KS between the first two groups: ${sig(pairs, 3)} (${ksLabel(pairs)}).` : ''} Binned ECDF from the explorer cube.`);
  };
  el.querySelectorAll('select').forEach(s => s.addEventListener('change', draw)); draw();
}

function digits(el, m) {
  const f = m.forensics, b = f.benford;
  const uni = [f.second_uniform, f.minute_uniform, f.duration_last_digit];
  el.innerHTML = header('Statistical forensics', 'Digit & grammar forensics', 'Generator fingerprints: leading digits, cents, timestamp grain, identifier grammar and account templates. Large n makes every χ² significant, so conformity is judged by effect size (Cohen\'s w, Nigrini MAD).') + badge('OBSERVED DATA') +
    `<div class="grid g2">
      ${chartBox('First digit vs Benford', grouped(b.digits.map(d => String(d.d)), [{name: 'observed', color: C.blue, values: b.digits.map(d => d.observed)}, {name: 'Benford', color: C.yellow, values: b.digits.map(d => d.benford)}], {label: 'Benford', vfmt: v => pct(v, 2), yfmt: v => pct(v, 0)}),
        `n = ${fmt(b.n)} · χ² = ${fmt(b.chi2)} (p ≈ 0 by sample size) · Cohen's w = ${sig(b.cohen_w, 3)} · Nigrini MAD = ${sig(b.nigrini_mad, 3)} → "${esc(b.conformity)}" conformity. Lognormal amounts with sd ≈ 2 in ln are expected to be near-Benford.`)}
      ${chartBox('Zero cents by segment', bars(f.cents_by_segment.map(s => ({label: s.seg, value: s.cents00, note: `×100: ${pct(s.mult100, 2)} · ×1000: ${pct(s.mult1000, 2)}`})), {label: 'Cents', vfmt: v => pct(v, 2), h: 220}), 'Segment = sender type + receiver type. Business-to-business payments are slightly rounder (7.7% vs 6.9% zero cents for CC; ×1000 multiples 2.7% vs 0.9%). Hover a bar for the ×100/×1000 shares.')}
    </div>
    <h2>Uniformity tests</h2>${table(uni, [{key: 'test', label: 'Test'}, {key: 'n', label: 'n', num: true, f: fmt}, {key: 'chi2', label: 'χ²', num: true, f: v => sig(v, 4)}, {key: 'dof', label: 'dof', num: true}, {key: 'p', label: 'p', num: true, f: v => sig(v, 3)}, {key: 'cohen_w', label: "Cohen's w", num: true, f: v => sig(v, 3)}])}
    <div class="note">Seconds are uniform (p = ${sig(f.second_uniform.p, 3)}). The duration last digit is "significant" only because n = 10M; w = ${sig(f.duration_last_digit.cohen_w, 3)} is negligible.</div>
    <h2>Identifier grammar</h2><div class="grid g3">
      <div class="card"><h3>BIC8</h3><p>${fmt(f.bic.banks)} banks in ${f.bic.countries} countries; grammar match ${pct(f.bic.grammar_match)}; max bank number ${fmt(f.bic.max_bank_number)}; ${f.bic.countries_with_multiple_location_codes} countries with more than one location code.</p></div>
      <div class="card"><h3>IBAN length</h3><p>${pct(f.iban_single_length_share)} of IBAN countries use exactly one length — consistent with a per-country template.</p></div>
      <div class="card"><h3>Local accounts</h3><p>${fmt(f.local_account_templates.distinct)} distinct digit/letter templates; the top template covers ${fmt(f.local_account_templates.top[0].n)} accounts.</p></div></div>
    ${table(f.local_account_templates.top, [{key: 'tpl', label: 'Template (A = letter, 9 = digit)', f: v => `<code>${esc(v)}</code>`}, {key: 'n', label: 'Accounts', num: true, f: fmt}])}
    <h2>Fixed FX-rate search (negative result)</h2>${table(f.fixed_rate_search, [{key: 'currency', label: 'Currency'}, {key: 'best_rate', label: 'Best rate', num: true, f: v => sig(v, 5)}, {key: 'best_near_integer_share', label: 'Near-integer at best', num: true, f: v => pct(v, 2)}, {key: 'median_share', label: 'Median over grid', num: true, f: v => pct(v, 2)}])}
    <div class="note red">No single rate makes converted amounts round (≈2% vs ≈1.2% baseline). We therefore do not claim a fixed conversion table (hypothesis H37 rejected).</div>
    <h2>Conditional-independence tests (feed the atlas)</h2>${table(f.ci_tests, [{key: 'x', label: 'X'}, {key: 'y', label: 'Y'}, {key: 'given', label: 'Given'}, {key: 'cramers_v', label: "Cramér's V", num: true, f: v => sig(v, 3)}, {key: 'verdict', label: 'Verdict'}])}`;
}

async function tests(el, m, ctx) {
  const T = await data('tests'), fams = ['ALL', ...new Set(T.tests.map(t => t.family))];
  const st = {fam: fams.includes(ctx.params.fam) ? ctx.params.fam : (fams.find(f => ctx.params.fam && f.startsWith(ctx.params.fam)) || 'ALL'), sig: ctx.params.sig || 'all', q: ctx.params.q || ''};
  el.innerHTML = header('Statistical forensics', 'Hypothesis testing', `${fmt(T.tests.length)} recorded tests across ${fams.length - 1} families. ${esc(T.note)}`) + badge('OBSERVED DATA') +
    `<div class="controls">${select('tf', 'Family', fams, st.fam)}${select('ts', 'Show', [['all', 'All tests'], ['sig', 'Significant after BH (q < 0.05)'], ['ns', 'Not significant']], st.sig)}<label class="ctl">Search<input id="tq" type="search" value="${esc(st.q)}"></label><button class="sec" id="tx">Export CSV</button></div><div id="to"></div>`;
  const draw = () => {
    st.fam = el.querySelector('#tf').value; st.sig = el.querySelector('#ts').value; st.q = el.querySelector('#tq').value.toLowerCase();
    ctx.setParams({fam: st.fam === 'ALL' ? '' : st.fam, sig: st.sig === 'all' ? '' : st.sig, q: st.q});
    const rows = T.tests.filter(t => (st.fam === 'ALL' || t.family === st.fam) && (st.sig === 'all' || (st.sig === 'sig' ? t.significant_bh_05 === true : t.significant_bh_05 === false)) && (!st.q || JSON.stringify(t).toLowerCase().includes(st.q)));
    el._rows = rows;
    const nSig = rows.filter(t => t.significant_bh_05).length;
    el.querySelector('#to').innerHTML = kpis([[fmt(rows.length), 'tests shown'], [fmt(nSig), 'significant after BH'], [fmt(rows.filter(t => t.p_bh == null).length), 'without a p-value (effect-size only)']]) +
      table(rows, [{key: 'family', label: 'Family'}, {key: 'test', label: 'Test'}, {key: 'n', label: 'n'}, {key: 'effect', label: 'Effect'}, {key: 'p', label: 'p', num: true, f: v => v == null ? '—' : v < 1e-300 ? '< 1e-300' : sig(v, 3)},
        {key: 'p_bh', label: 'p (BH)', num: true, f: v => v == null ? '—' : v < 1e-300 ? '< 1e-300' : sig(v, 3)}, {key: 'family_size', label: 'Family m', num: true}, {key: 'significant_bh_05', label: 'q < .05', f: v => v == null ? '—' : v ? tag('YES', 'lv-val') : tag('NO', 'info')}], {h: 560, empty: 'No test matches these filters.'});
  };
  el.querySelectorAll('select,input').forEach(x => x.addEventListener('input', draw));
  el.querySelector('#tx').onclick = () => download('hypothesis_tests.csv', toCSV(el._rows || [], ['family', 'test', 'n', 'effect', 'p', 'p_bh', 'family_size', 'significant_bh_05']), 'text/csv');
  draw();
}

async function stability(el, m, ctx) {
  const [reg, cb] = await Promise.all([data('registry'), cube()]), st = m.stats;
  const P1 = aggregate(cb, {period: new Set(['P1'])}), P2 = aggregate(cb, {period: new Set(['P2'])}), c = compare(cb, P1, P2);
  // per-rule spread of the main metric across the five splits
  const SPL = ['full', 'half_0', 'half_1', 'P1', 'P2'];
  const spread = reg.rules.filter(r => r.kind === 'rule' && r.metrics).map(r => {
    const keys = Object.keys(r.metrics.full || {}).filter(k => k !== 'n' && typeof r.metrics.full[k] === 'number');
    const k = keys[0]; if (!k) return null;
    const vs = SPL.map(s => r.metrics[s]?.[k]).filter(v => typeof v === 'number');
    const mx = Math.max(...vs), mn = Math.min(...vs), ref = Math.abs(r.metrics.full[k]) || 1;
    return {id: r.id, level: r.level, metric: k, full: r.metrics.full[k], min: mn, max: mx, rel: (mx - mn) / ref};
  }).filter(Boolean).sort((a, b) => b.rel - a.rel);
  el.innerHTML = header('Statistical forensics', 'Stability analysis', 'A generator rule should hold in every slice of the data. We check each rule on two random halves and two time periods, and the key parameters across countries and segments.') + badge('OBSERVED DATA') +
    `<h2>Time periods P1 vs P2 (split at 15 Jun 2023)</h2>` + kpis([[fmt(P1.n), 'P1 payments'], [fmt(P2.n), 'P2 payments'], [sig(c.ratio, 4) + '×', 'amount ratio P1/P2'], [sig(c.ksAmt, 3), 'KS amount (binned)'], [sig(c.ksDur, 3), 'KS duration (binned)'], [(100 * c.manualDiff).toFixed(2) + ' pt', 'manual-share difference']]) +
    `<div class="note">Volume changes between periods (T4b change points) but the per-payment distributions do not — the generator's levels step, its rules stay fixed.</div>
    <div class="grid g2">${chartBox('R1 continuation q by sender country', bars(st.R1_by_country.map(r => ({label: r.cc, value: r.q, note: `n = ${fmt(r.n)}`})), {label: 'q country', vfmt: v => sig(v, 4), h: 230, max: .4}), `Range ${sig(Math.min(...st.R1_by_country.map(r => r.q)), 4)} – ${sig(Math.max(...st.R1_by_country.map(r => r.q)), 4)}; 1/e = 0.3679.`)}
      ${chartBox('R1 continuation q by segment', bars(st.R1_by_segment.map(r => ({label: `${r.seg}${r.normal ? '' : '*'}`, value: r.q, note: `n = ${fmt(r.n)}`})), {label: 'q segment', vfmt: v => sig(v, 4), h: 230, max: .4}), '* = anomalous payments in that segment.')}</div>
    <h2>Rule metrics across five splits</h2>` + table(spread, [{key: 'id', label: 'Rule', f: v => `<a href="#/validation/splits?id=${v}">${v}</a>`}, {key: 'level', label: 'Level', f: v => level(v)}, {key: 'metric', label: 'Primary metric', f: v => `<code>${esc(v)}</code>`},
      {key: 'full', label: 'Full', num: true, f: v => sig(v, 4)}, {key: 'min', label: 'Min', num: true, f: v => sig(v, 4)}, {key: 'max', label: 'Max', num: true, f: v => sig(v, 4)}, {key: 'rel', label: 'Spread / |full|', num: true, f: v => pct(v, 2)}], {h: 520}) +
    `<div class="note">Spread is (max − min) over the five splits relative to the full-data value; large relative spreads on metrics near zero (e.g. a deviation) are expected and harmless.</div>`;
}

async function counterexamples(el, m) {
  const reg = await data('registry'), rules = reg.rules.filter(r => r.kind === 'rule');
  const withV = rules.filter(r => r.violation && r.violation.rate > 0).sort((a, b) => b.violation.rate - a.violation.rate);
  el.innerHTML = header('Statistical forensics', 'Counterexamples', 'Where the reconstructed rules fail, and the hypotheses that the data refuted. A rule set without counterexamples would be suspicious; these are recorded, not hidden.') +
    kpis([[rules.filter(r => !r.violation?.rate).length, 'rules with zero violating rows'], [withV.length, 'rules with measured violations'], [reg.rules.filter(r => r.level === 'REJECTED').length, 'rejected hypotheses']]) +
    `<h2>Measured violations</h2>` + table(withV, [{key: 'id', label: 'Rule', f: v => `<a href="#/rules/explorer?id=${v}">${v}</a>`}, {key: 'title', label: 'Rule'}, {key: 'violation', label: 'Violation rate', num: true, f: v => pct(v.rate, 3)}, {key: 'violation', label: 'What', f: v => esc(v.text)}, {key: 'counterexamples', label: 'Counterexamples'}], {empty: 'No measured violations.'}) +
    `<h2>Documented counterexamples per rule</h2>` + table(rules.filter(r => r.counterexamples && !/^none/i.test(r.counterexamples)), [{key: 'id', label: 'Rule', f: v => `<a href="#/rules/explorer?id=${v}">${v}</a>`}, {key: 'level', label: 'Level', f: v => level(v)}, {key: 'counterexamples', label: 'Counterexamples'}, {key: 'limitations', label: 'Limitation'}], {h: 420}) +
    `<h2>Rejected hypotheses</h2>` + table(reg.rules.filter(r => r.level === 'REJECTED'), [{key: 'id', label: 'ID'}, {key: 'hypothesis', label: 'Hypothesis'}, {key: 'method', label: 'Test'}, {key: 'effect_size', label: 'Outcome'}], {h: 460});
}

async function alternatives(el, m, ctx) {
  const reg = await data('registry'), rules = reg.rules.filter(r => r.kind === 'rule'), rej = reg.rules.filter(r => r.level === 'REJECTED');
  el.innerHTML = header('Forensic intelligence', 'Alternative hypotheses',
    'For every rule, the strongest competing explanation we tested and why it lost — next to the hypotheses the data refuted outright. A rule is only as credible as the alternatives it beat.') +
    `<div class="controls"><label class="ctl">Search<input id="aq" type="search" value="${esc(ctx.params.q || '')}" placeholder="rule, field, word"></label></div><div id="ao"></div>`;
  const draw = () => {
    const q = el.querySelector('#aq').value.toLowerCase(); ctx.setParams({q});
    const f = r => !q || JSON.stringify(r).toLowerCase().includes(q);
    el.querySelector('#ao').innerHTML = '<h2>Rule vs best alternative</h2>' + table(rules.filter(f), [{key: 'id', label: 'Rule', f: v => `<a href="#/rules/explorer?id=${v}">${v}</a>`}, {key: 'level', label: 'Level', f: v => level(v)},
        {key: 'title', label: 'Accepted mechanism'}, {key: 'alternative', label: 'Best alternative tested (and outcome)'}, {key: 'id', label: 'History', f: v => `<a href="#/genome/genealogy?id=${v}">genealogy</a>`}], {h: 520, empty: 'No rule matches.'}) +
      '<h2>Refuted hypotheses</h2>' + table(rej.filter(f), [{key: 'id', label: 'ID'}, {key: 'hypothesis', label: 'Hypothesis'}, {key: 'method', label: 'Test'}, {key: 'effect_size', label: 'Outcome'}], {h: 460, empty: 'No refuted hypothesis matches.'});
  };
  el.querySelector('#aq').addEventListener('input', draw); draw();
}

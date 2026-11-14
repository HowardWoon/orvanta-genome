// Observed Data Explorer: every control re-aggregates the additive cube (10M rows → 10,396 cells). Comparison statistics are computed from exact sums.
import {esc, fmt, pct, sig, usd, dur, kpis, header, badge, table, bars, distCompare, chartBox, select, download, toCSV, C} from '../core.js';
import {cube, aggregate, breakdown, summary, compare, dLabel, ksLabel} from '../cube.js';

const VAL_LABEL = {pc: v => v === '6' ? '6+' : v, fx: v => v === '3' ? '3+' : v, manual: v => v === '1' ? '>120 s' : '≤120 s', anom: v => v.replace(/_/g, ' ').toLowerCase(), otype: v => v === 'B' ? 'business' : 'consumer', btype: v => v === 'B' ? 'business' : 'consumer'};
const lab = (d, v) => (VAL_LABEL[d] || (x => x))(String(v));

export async function render(el, ctx) {
  const cb = await cube();
  const P = ctx.params;
  const st = {f: {}, mode: P.mode || 'complement', cd: P.cd || 'otype', cv: P.cv || '', by: P.by || 'ttype'};
  for (const d of cb.dims) if (P[d]) st.f[d] = new Set(P[d].split('|'));
  el.innerHTML = header('Interactive research lab', 'Observed data explorer',
    `Filter the full 10,000,000 rows on ten dimensions and compare the selection with a reference group. Each click re-aggregates ${fmt(cb.rows.length)} additive cells exactly — counts, sums and binned distributions — in your browser. No row-level data is shipped.`) +
    badge('OBSERVED DATA') + badge('CONDITIONAL ESTIMATE') +
    `<details class="fold" open><summary>Selection A — filters (empty = all values)</summary><div><div class="fgrid" id="ff">${cb.dims.map(d => `<fieldset class="fbox"><legend>${esc(cb.labels[d])}</legend><div class="chips">${cb.values[d].map(v =>
      `<button type="button" class="chip${st.f[d]?.has(v) ? ' on' : ''}" data-d="${d}" data-v="${esc(v)}" aria-pressed="${!!st.f[d]?.has(v)}">${esc(lab(d, v))}</button>`).join('')}</div></fieldset>`).join('')}</div></div></details>
    <div class="controls">${select('em', 'Compare A with', [['complement', 'Complement (everything not in A)'], ['all', 'Full dataset'], ['swap', 'A with one dimension changed']], st.mode)}
      <span id="eswap">${select('ecd', 'Dimension', cb.dims.map(d => [d, cb.labels[d]]), st.cd)}<span id="ecvw"></span></span>
      ${select('eby', 'Composition by', cb.dims.map(d => [d, cb.labels[d]]), st.by)}
      <button class="sec" id="ereset">Reset all</button><button class="sec" id="eexp">Export summary CSV</button></div>
    <div id="eout"></div>`;
  const ff = el.querySelector('#ff');
  ff.addEventListener('click', e => { const b = e.target.closest('.chip'); if (!b) return; const {d, v} = b.dataset; st.f[d] = st.f[d] || new Set(); st.f[d].has(v) ? st.f[d].delete(v) : st.f[d].add(v); if (!st.f[d].size) delete st.f[d]; b.classList.toggle('on'); b.setAttribute('aria-pressed', !!st.f[d]?.has(v)); draw(); });
  const cvw = () => { el.querySelector('#ecvw').innerHTML = select('ecv', 'Value for B', cb.values[st.cd].map(v => [v, lab(st.cd, v)]), cb.values[st.cd].includes(st.cv) ? st.cv : cb.values[st.cd][0]); el.querySelector('#ecv').addEventListener('change', e => { st.cv = e.target.value; draw(); }); st.cv = el.querySelector('#ecv').value; };
  el.querySelector('#em').addEventListener('change', e => { st.mode = e.target.value; draw(); });
  el.querySelector('#ecd').addEventListener('change', e => { st.cd = e.target.value; st.cv = ''; cvw(); draw(); });
  el.querySelector('#eby').addEventListener('change', e => { st.by = e.target.value; draw(); });
  el.querySelector('#ereset').addEventListener('click', () => { st.f = {}; st.mode = 'complement'; st.by = 'ttype'; ff.querySelectorAll('.chip').forEach(c => { c.classList.remove('on'); c.setAttribute('aria-pressed', 'false'); }); el.querySelector('#em').value = 'complement'; el.querySelector('#eby').value = 'ttype'; draw(); });
  let last = null;
  el.querySelector('#eexp').addEventListener('click', () => { if (!last) return; download('explorer_summary.csv', toCSV(last, Object.keys(last[0])), 'text/csv'); });
  cvw();

  function groupB() {
    if (st.mode === 'all') return {filter: {}, name: 'Full dataset'};
    if (st.mode === 'swap') { const f = {...st.f, [st.cd]: new Set([st.cv])}; return {filter: f, name: `A with ${cb.labels[st.cd]} = ${lab(st.cd, st.cv)}`}; }
    return {filter: null, name: 'Complement of A'};
  }
  function draw() {
    el.querySelector('#eswap').style.display = st.mode === 'swap' ? '' : 'none';
    const params = {mode: st.mode === 'complement' ? '' : st.mode, by: st.by === 'ttype' ? '' : st.by, cd: st.mode === 'swap' ? st.cd : '', cv: st.mode === 'swap' ? st.cv : ''};
    for (const d of cb.dims) params[d] = st.f[d] ? [...st.f[d]].join('|') : '';
    ctx.setParams(params);
    const out = el.querySelector('#eout');
    const A = aggregate(cb, st.f), T = aggregate(cb, {}), gb = groupB();
    let B;
    if (gb.filter) B = aggregate(cb, gb.filter);
    else B = {n: T.n - A.n, s1: T.s1 - A.s1, s2: T.s2 - A.s2, sd: T.sd - A.sd, manual: T.manual - A.manual, ah: T.ah.map((v, i) => v - A.ah[i]), dh: T.dh.map((v, i) => v - A.dh[i])};
    if (!A.n) { out.innerHTML = `<div class="empty">No payments match selection A. This combination does not occur in the data — remove a filter (e.g. ${esc(Object.keys(st.f).map(d => cb.labels[d]).join(', '))}).</div>`; last = null; return; }
    const sa = summary(cb, A), sb = B.n ? summary(cb, B) : null, cmp = sb ? compare(cb, A, B) : null;
    const desc = Object.keys(st.f).length ? Object.entries(st.f).map(([d, s]) => `${cb.labels[d]} ∈ {${[...s].map(v => lab(d, v)).join(', ')}}`).join(' · ') : 'all payments';
    const row = (n, s) => ({group: n, n: s?.n ?? 0, share: (s?.n ?? 0) / T.n, geo_mean_usd: s?.geo, median_usd: s?.medAmt, p10_usd: s?.p10Amt, p90_usd: s?.p90Amt, manual_share: s?.manual, mean_dur_s: s?.meanDur, median_dur_s: s?.medDur});
    last = [row('A', sa), row('B: ' + gb.name, sb)];
    const kpiRow = s => kpis([[fmt(s.n), 'payments'], [pct(s.n / T.n, 2), 'of all rows'], [usd(s.geo), 'geometric mean USD'], [usd(s.medAmt), 'median USD (binned)'], [pct(s.manual, 1), 'manual step (>120 s)'], [dur(s.medDur), 'median duration (binned)']]);
    const edgesA = [...cb.amt_edges], edgesD = [...cb.dur_edges, 16];
    out.innerHTML = `<div class="card y"><b>A:</b> ${esc(desc)} &nbsp;·&nbsp; <b>B:</b> ${esc(gb.name)}${sb ? '' : ' — empty (A covers everything)'}</div>
      <h3 style="margin-top:14px">Selection A</h3>${kpiRow(sa)}
      ${sb ? `<h3>Reference B</h3>${kpiRow(sb)}` : ''}
      ${cmp ? `<h2>A versus B</h2><div class="grid g4">
        <div class="card"><h3>Amount ratio A/B</h3><b style="font-family:var(--display);font-size:28px">${sig(cmp.ratio, 3)}×</b><div class="mono">95% CI ${sig(cmp.ratioCI[0], 3)} – ${sig(cmp.ratioCI[1], 3)}</div><p style="font-size:12.5px;margin:4px 0 0">Ratio of geometric means (Welch CI on mean ln amount).</p></div>
        <div class="card"><h3>Cohen's d (ln amount)</h3><b style="font-family:var(--display);font-size:28px">${sig(cmp.cohenD, 3)}</b><div class="mono">${dLabel(cmp.cohenD)} effect</div></div>
        <div class="card"><h3>KS distance</h3><b style="font-family:var(--display);font-size:28px">${sig(cmp.ksAmt, 3)}</b><div class="mono">amount · ${ksLabel(cmp.ksAmt)}</div><div class="mono">duration ${sig(cmp.ksDur, 3)} · ${ksLabel(cmp.ksDur)}</div></div>
        <div class="card"><h3>Manual-step difference</h3><b style="font-family:var(--display);font-size:28px">${cmp.manualDiff >= 0 ? '+' : ''}${(100 * cmp.manualDiff).toFixed(2)} pt</b><div class="mono">95% CI ${(100 * cmp.manualCI[0]).toFixed(2)} – ${(100 * cmp.manualCI[1]).toFixed(2)}</div></div></div>
        <div class="note">With hundreds of thousands of rows almost every difference is "significant"; read the effect sizes. These are associations within the synthetic data, not causal effects. KS is computed on 0.5-decade amount bins and log₂ duration bins, so it is a lower bound on the exact KS.</div>` : ''}
      <div class="grid g2">
        ${chartBox('Amount distribution (USD, log scale)', distCompare(edgesA, [{name: 'A', color: C.blue, counts: A.ah}, ...(sb ? [{name: 'B', color: C.coral, counts: B.ah, dash: true}] : [])], {label: 'Amount distribution', binLabel: e => e % 1 === 0 ? (e >= 0 ? '$' + fmt(10 ** e) : '$' + 10 ** e) : '', xt: 30, xlabel: 'USD amount bin (0.5 decade)'}), 'Share of each group per bin.')}
        ${chartBox('Duration distribution (seconds, log₂ bins)', distCompare(edgesD, [{name: 'A', color: C.blue, counts: A.dh}, ...(sb ? [{name: 'B', color: C.coral, counts: B.dh, dash: true}] : [])], {label: 'Duration distribution', binLabel: e => dur(2 ** e), xt: 8, xlabel: 'duration bin start'}), 'The second mode is the manual step (rule D1/D3).')}
      </div>
      ${(() => { const bd = breakdown(cb, st.f, st.by), tot = Object.values(bd).reduce((a, b) => a + b, 0); const rows = cb.values[st.by].map(v => ({label: lab(st.by, v), value: bd[v] || 0}));
        return chartBox(`Composition of A by ${esc(cb.labels[st.by])}`, bars(rows, {horizontal: true, left: 170, label: 'Composition', vfmt: v => `${pct(v / (tot || 1), 2)} · ${fmt(v)}`}), 'Counts within selection A (other filters applied).'); })()}
      ${table(last, [{key: 'group', label: 'Group'}, {key: 'n', label: 'n', num: true, f: fmt}, {key: 'share', label: 'Share', num: true, f: v => pct(v, 2)}, {key: 'geo_mean_usd', label: 'Geo mean', num: true, f: usd},
        {key: 'median_usd', label: 'Median', num: true, f: usd}, {key: 'p10_usd', label: 'P10', num: true, f: usd}, {key: 'p90_usd', label: 'P90', num: true, f: usd}, {key: 'manual_share', label: 'Manual', num: true, f: v => pct(v, 2)},
        {key: 'mean_dur_s', label: 'Mean s', num: true, f: v => fmt(v)}, {key: 'median_dur_s', label: 'Median s', num: true, f: v => fmt(v)}])}
      <div class="note">Medians and percentiles are interpolated inside histogram bins (amount bins 0.5 decade wide, duration bins one power of 2); means and the geometric mean are exact. Currencies outside the top 12 are pooled as "Other".</div>`;
  }
  draw();
}

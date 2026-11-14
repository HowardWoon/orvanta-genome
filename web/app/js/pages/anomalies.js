// Anomaly Explorer: pick a label, see its observed profile against normal payments (from the cube) and the rule-specific evidence.
import {data, esc, fmt, pct, sig, usd, dur, kpis, header, badge, level, table, bars, grouped, lines, distCompare, chartBox, select, C} from '../core.js';
import {cube, aggregate, summary, compare, breakdown, dLabel} from '../cube.js';

const RULE = {ROMANCE_SCAM: 'X1', DUPLICATE_PAYMENT: 'X2', FAT_FINGER_MISTAKE: 'X3', CEO_SCAM: 'X4', ACCOUNT_REPLACEMENT_SCAM: 'X4', CUSTOMER_RECALL: 'X5'};
const nice = a => a.replace(/_/g, ' ').toLowerCase();

export async function render(el, ctx) {
  const [cb, m, reg] = await Promise.all([cube(), data('meta'), data('registry')]);
  const labels = cb.values.anom.filter(a => a !== 'NORMAL'), a0 = labels.includes(ctx.params.a) ? ctx.params.a : 'ROMANCE_SCAM';
  el.innerHTML = header('Interactive research lab', 'Anomaly explorer', `The dataset labels ${fmt(m.anomalies)} payments with six anomaly types. Choose one to compare it with normal payments and to see the evidence behind its rule.`) +
    badge('OBSERVED DATA') + `<div class="controls">${select('aa', 'Anomaly label', labels.map(a => [a, nice(a)]), a0)}${select('ab', 'Breakdown by', cb.dims.filter(d => d !== 'anom').map(d => [d, cb.labels[d]]), ctx.params.by || 'ttype')}</div><div id="ao"></div>`;
  const draw = () => {
    const a = el.querySelector('#aa').value, by = el.querySelector('#ab').value;
    ctx.setParams({a, by: by === 'ttype' ? '' : by});
    const A = aggregate(cb, {anom: new Set([a])}), N = aggregate(cb, {anom: new Set(['NORMAL'])}), sa = summary(cb, A), sn = summary(cb, N), cmp = compare(cb, A, N);
    const r = reg.rules.find(x => x.id === RULE[a]), e = m.evidence, st = m.stats;
    const bA = breakdown(cb, {anom: new Set([a])}, by), bN = breakdown(cb, {anom: new Set(['NORMAL'])}, by), tA = Object.values(bA).reduce((x, y) => x + y, 0), tN = Object.values(bN).reduce((x, y) => x + y, 0);
    const vals = cb.values[by];
    const rate = st.anomaly_rates.find(x => x.anom === a);
    let extra = '';
    if (a === 'ROMANCE_SCAM') extra = chartBox('X1 · escalation inside a burst', lines(e.romance_steps.map(s => 'step ' + s.k), [{name: 'mean ln amount', color: C.coral, values: e.romance_steps.map(s => s.mlog), points: true}], {label: 'Romance steps', zero: false, vfmt: v => `${sig(v, 3)} (≈ ${usd(Math.exp(v))})`}),
      'Each later payment in a consumer burst is larger (≈ ×1.5 per step). Burst sizes: ' + e.romance_series.map(s => `${s.n}: ${s.series}`).join(' · '));
    if (a === 'DUPLICATE_PAYMENT') extra = table(e.dup_groups, [{key: 'n', label: 'Copies', num: true}, {key: 'ngroups', label: 'Groups', num: true, f: fmt}, {key: 'med_span', label: 'Median span s', num: true, f: fmt}, {key: 'max_span', label: 'Max span s', num: true, f: fmt}, {key: 'max_paths', label: 'Distinct paths', num: true}, {key: 'max_durs', label: 'Distinct durations', num: true}]) +
      '<div class="cfoot">X2: copies share amount, path and duration and arrive within 2 hours; every copy carries the label.</div>';
    if (a === 'FAT_FINGER_MISTAKE') extra = chartBox('X3 · residual vs expectation (log10)', grouped(e.fat_finger_hist.map(h => String(h.lb)), [{name: 'fat finger', color: C.coral, values: e.fat_finger_hist.map(h => h.n / A.n)}, {name: 'normal', color: C.blue, values: e.fat_finger_hist.map(h => (e.normal_resid_hist.find(x => x.lb === h.lb)?.n || 0) / e.normal_resid_hist.reduce((s, x) => s + x.n, 0))}], {label: 'Fat finger', vfmt: v => pct(v, 2), yfmt: v => pct(v, 0), xlabel: 'log10(amount / expected)'}),
      `Amounts sit about two decades (×100 or ÷100) away from the A1/A2 expectation. A z-score detector reaches PR-AUC ${sig(st.fat_finger_pr_auc, 3)} — the label overlaps normal noise heavily.`);
    if (['CEO_SCAM', 'ACCOUNT_REPLACEMENT_SCAM'].includes(a)) { const mu = e.mule.find(x => x.a === a), sb = e.scam_bank.find(x => x.a === a), nb = e.scam_bank.find(x => x.a === 'NORMAL');
      extra = kpis([[pct(mu.only_anom_bacc), 'beneficiary accounts used only by this label'], [fmt(mu.med_senders), 'median senders per account'], [fmt(sb.bene_bank_size), `beneficiary bank size (normal ${fmt(nb.bene_bank_size)})`], [pct(sb.slow_b), `slow beneficiary banks (normal ${pct(nb.slow_b)})`]]) +
        '<div class="note">X4: money goes to mule-like accounts at small, slow banks — a structural signature, not a timing one.</div>'; }
    if (a === 'CUSTOMER_RECALL') extra = `<div class="card warn"><h3>X5 · no observable signature (negative result)</h3><p>Every test of recall payments against normal ones is non-significant after per-family Benjamini–Hochberg control (see <a href="#/forensics/tests?fam=X5">hypothesis tests</a>). The label looks like a random draw on normal payments, so it is INCONCLUSIVE, not a rule.</p></div>`;
    el.querySelector('#ao').innerHTML = kpis([[fmt(sa.n), 'labelled payments'], [rate ? `${sig(rate.per_10k, 3)} / 10k` : '—', 'rate (95% CI ' + (rate ? `${sig(rate.lo, 3)}–${sig(rate.hi, 3)}` : '—') + ')'], [usd(sa.medAmt), `median USD (normal ${usd(sn.medAmt)})`], [dur(sa.medDur), `median duration (normal ${dur(sn.medDur)})`], [pct(sa.manual), `manual (normal ${pct(sn.manual)})`], [sig(cmp.cohenD, 2), `Cohen's d ln amount · ${dLabel(cmp.cohenD)}`]]) +
      (r ? `<div class="card">${level(r.level)}<b><a href="#/rules/explorer?id=${r.id}">${r.id}</a></b> ${esc(r.title)}<div class="formula">${esc(r.formulation)}</div></div>` : '') +
      `<div class="grid g2" style="margin-top:14px">${chartBox(`Amount: ${nice(a)} vs normal`, distCompare(cb.amt_edges, [{name: nice(a), color: C.coral, counts: A.ah}, {name: 'normal', color: C.blue, counts: N.ah, dash: true}], {label: 'Amount anomaly', binLabel: e => e % 1 === 0 ? '$' + (e >= 0 ? fmt(10 ** e) : 10 ** e) : '', xt: 30}), 'Share per 0.5-decade bin.')}
        ${chartBox(`Breakdown by ${esc(cb.labels[by])}`, grouped(vals, [{name: nice(a), color: C.coral, values: vals.map(v => (bA[v] || 0) / (tA || 1))}, {name: 'normal', color: C.blue, values: vals.map(v => (bN[v] || 0) / tN)}], {label: 'Breakdown', vfmt: v => pct(v, 2), yfmt: v => pct(v, 0)}), 'Shares within each group.')}</div>
      <h2>Rule-specific evidence</h2>${extra || '<div class="card">No additional evidence block for this label.</div>'}
      <h2>Rule-based detectors</h2>${table(st.detectors, [{key: 'label', label: 'Label'}, {key: 'detector', label: 'Detector'}, {key: 'tp', label: 'TP', num: true, f: fmt}, {key: 'fp', label: 'FP', num: true, f: fmt}, {key: 'fn', label: 'FN', num: true, f: fmt}, {key: 'precision', label: 'Precision', num: true, f: v => pct(v)}, {key: 'recall', label: 'Recall', num: true, f: v => pct(v)}])}`;
  };
  el.querySelectorAll('select').forEach(s => s.addEventListener('change', draw));
  draw();
}

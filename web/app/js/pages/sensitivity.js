// Sensitivity analysis: sweep one parameter of the reconstructed generator, recompute the model output live, and compare with the observed benchmark.
// q and p use the closed forms of R1 and R4; m uses seeded Monte Carlo of D1/D3. Every curve is model output; observed values come from the data files.
import {data, fmt, pct, sig, header, badge, table, lines, chartBox, select, kpis, C} from '../core.js';
import {simDuration} from '../sim.js';
import {cube, aggregate, summary} from '../cube.js';

export async function render(el, ctx) {
  const [S, m, cb] = await Promise.all([data('sim'), data('meta'), cube()]);
  const tot = m.distributions['Participants'].reduce((a, b) => a + b.n, 0);
  const rt = Object.fromEntries(m.distributions['Routing type'].map(x => [x.k, x.n]));
  const hh = m.distributions['Hidden-hop count'], pcs = m.distributions['Participants'];
  const O2 = summary(cb, aggregate(cb, {pc: new Set(['2'])}));
  const P = {
    q: {name: 'R1 continuation probability q', out: 'Share of payments that are Direct', rule: 'R1', est: S.route.q, lo: .2, hi: .6, step: .005,
        formula: 'Share Direct = P(K = 0) = 1 − q          (K ~ Geometric: P(K = k) = (1 − q)·qᵏ)',
        f: q => 1 - q, d: () => -1, obs: rt.Direct / tot, obsLabel: 'observed Direct share (all 10M rows)',
        note: 'Linear: every 0.01 in q moves the Direct share by exactly 1 point. The observed share has a 95% CI of ±0.03 points, so q is pinned down to about the fourth decimal.'},
    p: {name: 'R4 per-link hidden probability p', out: 'Share of payments with ≥ 1 hidden hop', rule: 'R4', est: S.route.p_link, lo: 0, hi: .12, step: .002,
        formula: 'Share hidden = Σₖ P(pc = k) · (1 − (1 − p)^(k−1))          P(pc = k) = observed participant mix',
        f: p => pcs.reduce((a, x) => a + x.n / tot * (1 - (1 - p) ** (+x.k - 1)), 0),
        d: p => pcs.reduce((a, x) => a + x.n / tot * (+x.k - 1) * (1 - p) ** (+x.k - 2), 0), obs: 1 - hh[0].n / tot, obsLabel: 'observed share with a "..." hop',
        note: 'Almost linear for small p; the slope equals the mean number of links per payment (E[pc − 1]).'},
    m: {name: 'D1 per-bank manual probability m', out: 'Manual-step share (> 120 s) at 2 participants', rule: 'D1 · D3', est: S.duration.m_bank, lo: 0, hi: .48, step: .02,
        formula: 'Closed form (ignoring rare slow fast-steps): share = 1 − (1 − m)²          Monte Carlo: Σ of 2 Gamma steps, manual w.p. m',
        f: x => 1 - (1 - x) ** 2, d: x => 2 * (1 - x), obs: O2.manual, obsLabel: 'observed manual share at pc = 2', mc: true,
        note: 'Concave: each extra point of m matters less as m grows. Monte-Carlo points sit slightly above the closed form because two fast steps can also exceed 120 s.'},
  };
  const key0 = P[ctx.params.p] ? ctx.params.p : 'q';
  el.innerHTML = header('Research playground', 'Sensitivity analysis',
    'Which conclusions depend on which numbers? Pick a parameter, move it, and the model output is recomputed from the reconstructed rule. The estimate (from the data) and the observed benchmark stay fixed for comparison.') +
    badge('MODEL SIMULATION') + badge('OBSERVED DATA') +
    `<div class="controls">${select('sp', 'Parameter', [...Object.entries(P).map(([k, v]) => [k, `${v.name} → ${v.out.toLowerCase()}`]), ['th', 'D1 analyst thresholds (pipeline table)']], ctx.params.p === 'th' ? 'th' : key0)}</div><div id="so"></div>`;
  const so = el.querySelector('#so');
  const draw = () => {
    const k = el.querySelector('#sp').value;
    if (k === 'th') {
      ctx.setParams({p: 'th'});
      so.innerHTML = table(m.stats.sensitivity_D1, [{key: 'slow_threshold_s', label: 'Slow threshold (s)', num: true}, {key: 'class_threshold', label: 'Bank-class cut', num: true}, {key: 'med_0', label: 'Median, 0 slow banks', num: true}, {key: 'med_1', label: '1 slow', num: true}, {key: 'med_2', label: '2 slow', num: true}, {key: 'additivity', label: 'Additivity (2 vs 1)', num: true, f: v => sig(v, 3)}]) +
        `<div class="note">D1's conclusion (two slow banks take about twice as long as one) holds for every analyst-chosen threshold combination: additivity stays between ${sig(Math.min(...m.stats.sensitivity_D1.map(r => r.additivity)), 3)} and ${sig(Math.max(...m.stats.sensitivity_D1.map(r => r.additivity)), 3)}.</div>`;
      return;
    }
    const X = P[k], v0 = ctx.params.p === k && ctx.params.v != null ? +ctx.params.v : X.est;
    so.innerHTML = `<div class="card"><h3>${X.name} → ${X.out}</h3><div class="formula">${X.formula}</div>
        <label class="ctl">Selected value of ${k} <output id="sv_o">${v0.toFixed(4)}</output><input id="sv" type="range" min="${X.lo}" max="${X.hi}" step="any" value="${v0}"></label>
        <div class="controls"><button class="sec" id="sreset">Reset to estimate (${X.est.toFixed(4)})</button></div></div><div id="sout"></div>`;
    const xs = Array.from({length: Math.round((X.hi - X.lo) / X.step) + 1}, (_, i) => +(X.lo + i * X.step).toFixed(6));
    const mc = X.mc ? xs.map(x => simDuration(S.duration, {pc: 2, m: x, draws: 12000, batches: 3}, cb.dur_edges).manual) : null;
    const out = () => {
      const v = +el.querySelector('#sv').value; el.querySelector('#sv_o').textContent = v.toFixed(4); ctx.setParams({p: k, v: Math.abs(v - X.est) < 1e-9 ? '' : v.toFixed(4)});
      const y = X.f(v), yEst = X.f(X.est), slope = X.d(v);
      const sel = xs.map(x => Math.abs(x - v) <= X.step / 2 ? X.f(x) : null), est = xs.map(x => Math.abs(x - X.est) <= X.step / 2 ? X.f(x) : null);
      const series = [{name: 'model (closed form)', color: C.blue, values: xs.map(X.f)}, ...(mc ? [{name: 'model (Monte Carlo, 12k draws/point)', color: C.ink, values: mc, points: true, dash: true}] : []),
        {name: X.obsLabel, color: C.coral, dash: true, values: xs.map(() => X.obs)}, {name: 'estimate', color: C.yellow, values: est, points: true}, {name: 'selected', color: C.teal, values: sel, points: true}];
      el.querySelector('#sout').innerHTML = kpis([[v.toFixed(4), `selected ${k}`], [pct(y, 2), 'model output at selected value'], [pct(yEst, 2), `model at estimate (${k} = ${X.est.toFixed(4)})`], [pct(X.obs, 2), 'observed benchmark'],
          [`${slope >= 0 ? '+' : ''}${slope.toFixed(2)} pt`, `sensitivity: change in output per +0.01 in ${k}`]]) +
        (Math.abs(v - X.est) > X.step / 2 ? `<div class="note red">${badge('STRUCTURAL SCENARIO')} At ${k} = ${v.toFixed(4)} the model differs from the observed data by ${((y - X.obs) * 100).toFixed(2)} points — a hypothetical generator, not the data.</div>` : `<div class="note">At the estimate the model reproduces the observed benchmark within ${Math.abs((yEst - X.obs) * 100).toFixed(2)} points.</div>`) +
        chartBox(`${X.out} as ${k} varies`, lines(xs.map(x => x.toFixed(3)), series, {label: `${k} sweep`, xlabel: k, yfmt: q => pct(q, 0), vfmt: q => pct(q, 2), zero: false, xt: 10, legend: true}),
          `${X.note} Source: ${X.rule} parameters in data/sim.json; observed benchmark from data/meta.json (all 10M rows).`);
    };
    el.querySelector('#sv').addEventListener('input', out);
    el.querySelector('#sreset').onclick = () => { el.querySelector('#sv').value = X.est; out(); };
    out();
  };
  el.querySelector('#sp').addEventListener('change', () => { ctx.params.v = null; draw(); });
  draw();
}

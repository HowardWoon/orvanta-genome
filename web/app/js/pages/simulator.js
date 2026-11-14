// Scenario Simulator: Monte-Carlo runs of the reconstructed generator, compared against the observed cube. Every output is a MODEL SIMULATION.
import {data, esc, fmt, pct, sig, usd, dur, kpis, header, badge, table, grouped, distCompare, chartBox, select, slider, download, C} from '../core.js';
import {cube, aggregate, summary} from '../cube.js';
import {simRoute, simAmount, simDuration, defaultW} from '../sim.js';

const ks = (h1, h2) => { const t1 = h1.reduce((a, b) => a + b, 0) || 1, t2 = h2.reduce((a, b) => a + b, 0) || 1; let c1 = 0, c2 = 0, m = 0; for (let i = 0; i < h1.length; i++) { c1 += h1[i] / t1; c2 += h2[i] / t2; m = Math.max(m, Math.abs(c1 - c2)); } return m; };
const fitWord = k => k < .03 ? 'close fit' : k < .08 ? 'approximate fit' : 'poor fit — the model misses something here';

export async function render(el, ctx) {
  const [S, m, cb] = await Promise.all([data('sim'), data('meta'), cube()]);
  const tab = ['route', 'amount', 'duration'].includes(ctx.params.tab) ? ctx.params.tab : 'route';
  el.innerHTML = header('Interactive research lab', 'Scenario simulator',
    'Runs the reconstructed generator as a seeded Monte-Carlo model, starting from parameters estimated on the data, and places the result next to what was observed. Move a parameter to ask "what would the data look like if this rule were different?"') +
    badge('MODEL SIMULATION') + badge('STRUCTURAL SCENARIO') +
    `<div class="note red">Simulated numbers are model output, not observations. At the estimated parameters they test the reconstruction; away from them they are hypothetical scenarios about this synthetic generator only — not forecasts of real payment systems.</div>
    <div class="chips" role="tablist" id="stabs">${[['route', 'Routing (R1 · R2 · R4)'], ['amount', 'Amounts (A1 · A2)'], ['duration', 'Duration (D1 · D3)']].map(([k, t]) => `<button type="button" role="tab" class="chip${k === tab ? ' on' : ''}" data-t="${k}" aria-selected="${k === tab}">${t}</button>`).join('')}</div>
    <div id="spanel" style="margin-top:14px"></div>
    <div class="controls" style="margin-top:16px"><button id="spin">Pin this scenario for comparison</button><button class="sec" id="sclear">Clear pinned</button><button class="sec" id="sexp">Export scenario report</button></div><div id="scmp"></div>
    <div class="card" style="margin-top:18px"><h3>Not simulated: FX conversions and currency (C2, C3)</h3><p>C2 is deterministic — the conversion count is the number of home-currency changes along the path — so simulating it would only replay the path. C3 needs the full bank-to-currency table, which is a row-level structure we do not ship to the browser. Both are validated in the <a href="#/rules/explorer?id=C2">rule explorer</a>.</p></div>`;
  el.querySelector('#stabs').addEventListener('click', e => { const b = e.target.closest('.chip'); if (!b) return; ctx.setParams({tab: b.dataset.t}); el.querySelectorAll('#stabs .chip').forEach(c => { c.classList.toggle('on', c === b); c.setAttribute('aria-selected', c === b); }); show(b.dataset.t); });
  const panel = el.querySelector('#spanel');
  let current = null; const pinned = [];
  const drawCmp = () => {
    const box = el.querySelector('#scmp');
    if (!pinned.length) { box.innerHTML = '<div class="note">Pin two or more scenarios (any tab) to compare their inputs and outputs side by side.</div>'; return; }
    box.innerHTML = '<h2>Scenario comparison</h2>' + table(pinned.map((x, i) => ({...x, n: i + 1})), [{key: 'n', label: '#', num: true}, {key: 'tab', label: 'Model'}, {key: 'rules', label: 'Rules'},
      {key: 'scenario', label: 'Kind', f: v => v ? badge('STRUCTURAL SCENARIO') : badge('MODEL SIMULATION')}, {key: 'params', label: 'Inputs', f: v => Object.entries(v).map(([k, w]) => `<code>${esc(k)} = ${esc(w)}</code>`).join(' ')},
      {key: 'out', label: 'Outputs', f: v => Object.entries(v).map(([k, w]) => `${esc(k)}: <b>${esc(w)}</b>`).join('<br>')}]) +
      (pinned.length >= 2 ? `<div class="note">Differences between rows come only from the changed inputs: every run uses the same seeds, so Monte-Carlo noise is common to all scenarios of a model (standard errors are shown in the KPI captions).</div>` : '');
  };
  el.querySelector('#spin').onclick = () => { if (current) { pinned.push(JSON.parse(JSON.stringify(current))); drawCmp(); } };
  el.querySelector('#sclear').onclick = () => { pinned.length = 0; drawCmp(); };
  el.querySelector('#sexp').onclick = () => {
    const list = pinned.length ? pinned : current ? [current] : [];
    const md = `# ORVANTA Scenario Studio report

Generated ${new Date().toISOString()} · data: synthetic Swift case dataset (10,000,000 rows) · parameters estimated in web/build_data/sim.json

` +
      list.map((x, i) => `## Scenario ${i + 1}: ${x.tab} (${x.scenario ? 'STRUCTURAL SCENARIO — parameters moved off the estimates' : 'MODEL SIMULATION at the estimates'})

- Rules: ${x.rules}
- Inputs: ${Object.entries(x.params).map(([k, v]) => `${k} = ${v}`).join(', ')}
- Outputs: ${Object.entries(x.out).map(([k, v]) => `${k}: ${v}`).join('; ')}
`).join(String.fromCharCode(10)) +
      `
## Assumptions and limits

- Simulations run the reconstructed generator (R1/R2/R4 routing, A1/A2 amounts, D1/D3 duration) as seeded Monte Carlo; they are not observations.
- Moving a parameter off its estimate describes a hypothetical generator, not a forecast or a causal intervention on real payment systems.
- FX conversions and currency choice (C2, C3) are not simulated.
- Participants above 9 are thinly observed; results there are extrapolation.
`;
    download('scenario_report.md', md, 'text/markdown');
  };
  const show = t => ({route, amount, duration})[t]();
  let timer;
  const debounce = f => { clearTimeout(timer); timer = setTimeout(f, 120); };
  const bindSliders = (ids, units, run) => ids.forEach(id => { const s = panel.querySelector('#' + id); s.addEventListener('input', () => { panel.querySelector('#' + id + '_o').textContent = (units[id] || (v => v))(+s.value); debounce(run); }); });

  function route() {
    const R = S.route, w0 = defaultW(R), P = ctx.params;
    const st = {q: +(P.q ?? R.q), p: +(P.p ?? R.p_link), w: +(P.w ?? w0)};
    panel.innerHTML = `<div class="controls">${slider('rq', 'Continuation q (R1)', 0.05, 0.7, 0.001, st.q.toFixed(3))}${slider('rp', 'Hidden-link probability (R4)', 0, 0.3, 0.001, st.p.toFixed(3))}
      ${slider('rw', 'Share of non-direct sent by cover-prone banks (R2)', 0, 1, 0.005, st.w.toFixed(3))}<button class="sec" id="rreset">Reset to estimates</button></div><div id="rout"></div>
      <div class="mono" style="text-transform:none">Estimates: q = ${R.q.toFixed(4)} (${esc(S.sources.q)}), p = ${R.p_link.toFixed(4)} (${esc(S.sources.p_link)}), class cover shares ${pct(R.cover_share_cover_banks)} / ${pct(R.cover_share_other)} (${esc(S.sources.cover)}); w = ${w0.toFixed(3)} reproduces the pooled ${pct(R.pooled_cover, 2)}.</div>`;
    const units = {rq: v => v.toFixed(3), rp: v => v.toFixed(3), rw: v => v.toFixed(3)};
    const run = () => {
      st.q = +panel.querySelector('#rq').value; st.p = +panel.querySelector('#rp').value; st.w = +panel.querySelector('#rw').value;
      ctx.setParams({tab: 'route', q: st.q, p: st.p, w: st.w});
      const r = simRoute(R, {q: st.q, pLink: st.p, w: st.w});
      const op = m.distributions['Participants'], oT = op.reduce((a, b) => a + b.n, 0), last = op.length - 1;
      const ks_ = op.map((x, i) => i === last ? x.k + '+' : x.k);
      const simP = op.map((x, i) => { const k = +x.k; return i === last ? Object.entries(r.pcCounts).filter(([kk]) => +kk >= k).reduce((a, [, v]) => a + v, 0) : (r.pcCounts[k] || 0); });
      const oh = m.distributions['Hidden-hop count'], simH = oh.map((x, i) => i === oh.length - 1 ? Object.entries(r.gapCounts).filter(([kk]) => +kk >= +x.k).reduce((a, [, v]) => a + v, 0) : (r.gapCounts[+x.k] || 0));
      const rt = Object.fromEntries(m.distributions['Routing type'].map(x => [x.k, x.n])), oDirect = rt.Direct / oT, oCov = rt.Covered / (rt.Covered + rt.Indirect), oGap = 1 - oh[0].n / oT;
      const kP = ks(simP, op.map(x => x.n)), kH = ks(simH, oh.map(x => x.n));
      current = {tab: 'Routing', rules: 'R1 · R2 · R4', scenario: !(Math.abs(st.q - R.q) < 1e-3 && Math.abs(st.p - R.p_link) < 1e-3 && Math.abs(st.w - w0) < 5e-3), params: {q: st.q.toFixed(3), p_link: st.p.toFixed(3), w_cover: st.w.toFixed(3)}, out: {'Direct (sim)': pct(r.direct, 2), 'Covered | non-direct': pct(r.covered, 2), '≥1 hidden link': pct(r.gap, 2), 'KS participants': sig(kP, 3)}};
      const atEst = Math.abs(st.q - R.q) < 1e-3 && Math.abs(st.p - R.p_link) < 1e-3 && Math.abs(st.w - w0) < 5e-3;
      panel.querySelector('#rout').innerHTML = `${atEst ? '<div class="note">Parameters at their estimates: this is a test of the reconstruction.</div>' : `<div class="note red">${badge('STRUCTURAL SCENARIO')} Parameters moved away from the estimates — a hypothetical generator.${st.q > .55 ? ' q above 0.55 produces many paths longer than the 22 participants ever observed: extrapolation.' : ''}</div>`}
        ${kpis([[pct(r.direct, 2), `Direct (sim) · obs ${pct(oDirect, 2)}`], [pct(r.covered, 2), `Covered | non-direct (sim) · obs ${pct(oCov, 2)}`], [pct(r.gap, 2), `≥1 hidden link (sim) · obs ${pct(oGap, 2)}`], [sig(kP, 3), `KS participants · ${fitWord(kP)}`], [fmt(r.draws), 'simulated payments (seed 3)']])}
        <div class="grid g2">${chartBox('Participants per payment', grouped(ks_, [{name: 'observed (10M)', color: C.blue, values: op.map(x => x.n / oT)}, {name: 'simulated', color: C.coral, values: simP.map(v => v / r.draws)}], {label: 'Participants', vfmt: v => pct(v, 3), yfmt: v => pct(v, 0)}), 'Observed data vs model simulation.')}
        ${chartBox('Hidden links per payment', grouped(oh.map((x, i) => i === oh.length - 1 ? x.k + '+' : x.k), [{name: 'observed', color: C.blue, values: oh.map(x => x.n / oT)}, {name: 'simulated', color: C.coral, values: simH.map(v => v / r.draws)}], {label: 'Hidden links', vfmt: v => pct(v, 3), yfmt: v => pct(v, 0)}), `KS = ${sig(kH, 3)} (${fitWord(kH)}).`)}</div>`;
    };
    bindSliders(['rq', 'rp', 'rw'], units, run);
    panel.querySelector('#rreset').onclick = () => { panel.querySelector('#rq').value = R.q; panel.querySelector('#rp').value = R.p_link; panel.querySelector('#rw').value = w0; ['rq', 'rp', 'rw'].forEach(id => panel.querySelector('#' + id + '_o').textContent = (+panel.querySelector('#' + id).value).toFixed(3)); run(); };
    run();
  }

  function amount() {
    const A = S.amount, P = ctx.params, cs = [...A.country].sort((a, b) => a.cc.localeCompare(b.cc));
    const st = {s: P.s || 'B', r: P.r || 'C', c: P.c || 'ALL', k: +(P.k ?? 1)};
    panel.innerHTML = `<div class="controls">${select('as', 'Sender type', [['B', 'business'], ['C', 'consumer']], st.s)}${select('ar', 'Receiver type', [['B', 'business'], ['C', 'consumer']], st.r)}
      ${select('ac', 'Sender bank country', [['ALL', `All (volume-weighted, ${cs.length} countries)`], ...cs.map(c => [c.cc, `${c.cc} (effect ${c.eff >= 0 ? '+' : ''}${c.eff.toFixed(2)})`])], st.c)}
      ${slider('ak', 'Residual sd multiplier', 0.25, 2, 0.05, st.k)}<button class="sec" id="areset">Reset</button></div><div id="aout"></div>
      <div class="formula">ln(USD) = 6 + 2·[sender = B] + 2·[receiver = B] + country effect + ε,  ε ~ N(0, ${A.sd_noise.toFixed(3)}²)\nA1 fitted cell effects for reference: sender B ${A.b_sender.toFixed(3)}, receiver B ${A.b_receiver.toFixed(3)}, interaction ${A.interaction.toFixed(3)} (≈ additive).</div>`;
    const run = () => {
      st.s = panel.querySelector('#as').value; st.r = panel.querySelector('#ar').value; st.c = panel.querySelector('#ac').value; st.k = +panel.querySelector('#ak').value;
      ctx.setParams({tab: 'amount', s: st.s, r: st.r, c: st.c, k: st.k});
      const r = simAmount(A, {stype: st.s, rtype: st.r, country: st.c, sdScale: st.k}, cb.amt_edges);
      const O = aggregate(cb, {otype: new Set([st.s]), btype: new Set([st.r]), anom: new Set(['NORMAL'])}), so = summary(cb, O), k = ks(r.counts, O.ah);
      current = {tab: 'Amounts', rules: 'A1 · A2', scenario: st.k !== 1, params: {sender: st.s, receiver: st.r, country: st.c, sd_multiplier: st.k}, out: {'geometric mean (sim)': usd(r.geo), 'geometric mean (obs)': usd(so.geo), KS: sig(k, 3)}};
      const warn = st.c !== 'ALL' ? `<div class="note">The observed comparison pools all sender countries (the cube has no country dimension), so with one country selected the gap reflects that country's effect — that is the point of A2, not a misfit.</div>` : '';
      panel.querySelector('#aout').innerHTML = (st.k !== 1 ? `<div class="note red">${badge('STRUCTURAL SCENARIO')} Residual spread changed: a hypothetical generator.</div>` : '') + warn +
        kpis([[usd(r.geo), `geometric mean (sim) ± ${usd(1.96 * r.geoSE)}`], [usd(so.geo), 'geometric mean (observed, normal rows)'], [sig(k, 3), `KS distance · ${st.c === 'ALL' && st.k === 1 ? fitWord(k) : 'scenario'}`], [fmt(r.draws), 'simulated payments (seed 2)']]) +
        chartBox(`Amount distribution · sender ${st.s === 'B' ? 'business' : 'consumer'} → receiver ${st.r === 'B' ? 'business' : 'consumer'}`, distCompare(cb.amt_edges, [{name: 'observed (normal payments)', color: C.blue, counts: O.ah}, {name: 'simulated', color: C.coral, counts: r.counts, dash: true}], {label: 'Amount sim', binLabel: e => e % 1 === 0 ? '$' + (e >= 0 ? fmt(10 ** e) : 10 ** e) : '', xt: 30, xlabel: 'USD amount bin (0.5 decade)'}),
          `Observed: ${fmt(O.n)} normal payments in this segment. Monte-Carlo SE from 5 independent batches.`);
    };
    panel.querySelectorAll('select').forEach(s => s.addEventListener('change', run));
    bindSliders(['ak'], {ak: v => v.toFixed(2)}, run);
    panel.querySelector('#areset').onclick = () => { panel.querySelector('#as').value = 'B'; panel.querySelector('#ar').value = 'C'; panel.querySelector('#ac').value = 'ALL'; panel.querySelector('#ak').value = 1; panel.querySelector('#ak_o').textContent = '1.00'; run(); };
    run();
  }

  function duration() {
    const D = S.duration, P = ctx.params, st = {pc: +(P.pc ?? 2), m: +(P.m ?? D.m_bank)};
    panel.innerHTML = `<div class="controls">${slider('dp', 'Participants (banks on the path)', 2, 9, 1, st.pc)}${slider('dm', 'Per-bank manual probability', 0, 0.8, 0.005, st.m.toFixed(3))}<button class="sec" id="dreset">Reset</button></div><div id="dout"></div>
      <div class="formula">duration = Σ over pc banks of  { manual step ~ Gamma(${D.manual_shape.toFixed(2)}, ${D.manual_scale.toFixed(0)} s) with prob m;  fast step ~ Gamma(${D.fast_shape.toFixed(2)}, ${D.fast_scale.toFixed(2)} s) otherwise }\nm estimated = ${D.m_bank.toFixed(4)} — solves 1 − (1 − m)² = ${pct(D.pc2_manual_observed, 2)} observed manual share at pc = 2. ${esc(S.sources.duration)}</div>`;
    const run = () => {
      st.pc = +panel.querySelector('#dp').value; st.m = +panel.querySelector('#dm').value;
      ctx.setParams({tab: 'duration', pc: st.pc, m: st.m});
      const r = simDuration(D, {pc: st.pc, m: st.m}, cb.dur_edges);
      const pcKey = String(Math.min(st.pc, 6)), O = aggregate(cb, {pc: new Set([pcKey])}), so = summary(cb, O), k = ks(r.counts, O.dh);
      const atEst = Math.abs(st.m - D.m_bank) < 1e-3;
      current = {tab: 'Duration', rules: 'D1 · D3', scenario: !atEst, params: {participants: st.pc, m: st.m.toFixed(3)}, out: {'median (sim)': dur(r.median), 'median (obs)': dur(so.medDur), 'manual share (sim)': pct(r.manual, 1), 'manual share (obs)': pct(so.manual, 1), KS: sig(k, 3)}};
      panel.querySelector('#dout').innerHTML = (st.pc > 6 ? `<div class="note red">The cube pools 6+ participants, so the observed curve for pc = ${st.pc} is the 6+ group. pc above ${S.support.pc_reliable_max} is thinly observed: extrapolation.</div>` : '') +
        (!atEst ? `<div class="note red">${badge('STRUCTURAL SCENARIO')} Manual probability moved away from the estimate.</div>` : '') +
        kpis([[dur(r.median), `median (sim) ± ${fmt(1.96 * r.medianSE, 1)} s`], [dur(so.medDur), 'median (observed, binned)'], [pct(r.manual, 1), `manual share (sim) ± ${(196 * r.manualSE).toFixed(1)} pt`], [pct(so.manual, 1), 'manual share (observed)'], [sig(k, 3), `KS · ${atEst ? fitWord(k) : 'scenario'}`]]) +
        chartBox(`Duration distribution at ${st.pc} participants`, distCompare([...cb.dur_edges, 16], [{name: 'observed', color: C.blue, counts: O.dh}, {name: 'simulated', color: C.coral, counts: r.counts, dash: true}], {label: 'Duration sim', binLabel: e => dur(2 ** e), xt: 8, xlabel: 'duration bin start (log₂)'}),
          `Observed: ${fmt(O.n)} payments with ${pcKey === '6' ? '6+' : pcKey} participants. The fit at pc = 2 is the calibration target; pc ≥ 3 is an out-of-calibration test of additivity (D1).`);
    };
    bindSliders(['dp', 'dm'], {dp: v => v, dm: v => v.toFixed(3)}, run);
    panel.querySelector('#dreset').onclick = () => { panel.querySelector('#dp').value = 2; panel.querySelector('#dm').value = D.m_bank; panel.querySelector('#dp_o').textContent = '2'; panel.querySelector('#dm_o').textContent = D.m_bank.toFixed(3); run(); };
    run();
  }
  show(tab); drawCmp();
}

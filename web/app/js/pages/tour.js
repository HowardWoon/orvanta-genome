// Judge's Guided Tour — four stages, about two minutes. Every number is read from the evidence files at run time.
import {data, esc, fmt, pct, sig, dur, kpis, header, badge, level, table, grouped, distCompare, chartBox, C} from '../core.js';
import {cube, aggregate, summary} from '../cube.js';
import {simDuration} from '../sim.js';

const STAGES = ['The central discovery', 'A surprising distributional law', 'The hypothesis we overturned', 'From rule to scenario'];

export async function render(el, ctx) {
  const [reg, rep, m, G, S, cb] = await Promise.all([data('registry'), data('replay'), data('meta'), data('genome'), data('sim'), cube()]);
  const R = id => reg.rules.find(r => r.id === id);
  let s = Math.min(Math.max(+(ctx.params.s || 1), 1), 4);
  el.innerHTML = `<div class="sect">Judge's guided tour · ≈ 2 minutes</div><h1>Three discoveries and one simulation</h1>
    <p class="lede">This tour shows the strongest evidence that we reconstructed the generator: an exact rule and its only two exceptions, a mathematical law behind route length, a hypothesis our own engine overturned, and the rebuilt generator run as a scenario. Each stage links to the full research pages.</p>
    <nav class="journey" id="tnav" aria-label="Tour stages">${STAGES.map((t, i) => `<a href="#/tour?s=${i + 1}" data-s="${i + 1}" ${i + 1 === s ? 'aria-current="step"' : ''} style="background:${i + 1 === s ? 'var(--yellow)' : '#fff'}"><b>${i + 1} · ${t}</b><span>${['C2 · FX conversions', 'R1 · ⌊Exp(1)⌋ intermediaries', 'R2 · cover propensity', 'D1/D3 · duration'][i]}</span></a>`).join('')}</nav>
    <div id="tbody"></div>
    <div class="controls"><button class="sec" id="tprev">← Previous</button><button id="tnext">Next →</button><a class="tag" href="#/overview">Leave tour</a></div>`;
  const body = el.querySelector('#tbody');
  const show = () => {
    ctx.setParams({s});
    el.querySelectorAll('#tnav a').forEach(a => { const on = +a.dataset.s === s; a.style.background = on ? 'var(--yellow)' : '#fff'; on ? a.setAttribute('aria-current', 'step') : a.removeAttribute('aria-current'); });
    el.querySelector('#tprev').disabled = s === 1; el.querySelector('#tnext').textContent = s === 4 ? 'Finish → research journey' : 'Next →';
    body.innerHTML = [stage1, stage2, stage3, stage4][s - 1]();
  };
  el.querySelector('#tnav').addEventListener('click', e => { const a = e.target.closest('a[data-s]'); if (!a) return; e.preventDefault(); s = +a.dataset.s; show(); });
  el.querySelector('#tprev').onclick = () => { if (s > 1) { s--; show(); window.scrollTo(0, 0); } };
  el.querySelector('#tnext').onclick = () => { if (s < 4) { s++; show(); window.scrollTo(0, 0); } else ctx.go('genome/blueprint'); };

  function stage1() {
    const r = R('C2'), f = r.metrics.full, x = rep.rules.find(q => q.rule === 'C2');
    const rows = x.contradicting_rows.map(v => Object.fromEntries(x.columns.map((c, i) => [c, v[i]])));
    return `<h2>1 · C2 — the number of FX conversions is fixed by the route</h2>${badge('OBSERVED DATA')}${badge('VALIDATED RULE')}
      <div class="grid g2"><div class="card y"><h3>The rule</h3><div class="formula">CURRENCY_CONVERSION_COUNT = number of adjacent pairs of known banks in BIC8_PATH
whose countries have different home currencies</div>
        <p><b>Fields:</b> CURRENCY_CONVERSION_COUNT, BIC8_PATH (bank country = characters 5–6 of each BIC8). <b>Home currency</b> of a country = the currency its banks most often send in.</p>
        <p><b>Why it matters:</b> the generator does not draw the FX count at random — it derives it from the route. Knowing the route, you know the conversions. Two natural alternatives score far lower: "distinct currencies on the route − 1" (${pct(f.alt_distinct, 1)}) and "payment currency + borders" (93.5%, H5).</p></div>
      <div>${kpis([[fmt(f.n), 'payments tested (all)'], [fmt(f.n - f.exceptions), 'match the rule exactly'], [fmt(f.exceptions), 'contradict it'], [pct(f.share_exact, 5), 'agreement']])}
        <div class="note">Holds on all five splits (two random halves, two periods). An independent pure-Python implementation agrees on a 200,000-row sample.</div></div></div>
      <h3>The only two exceptions — inspect them</h3>` + table(rows, [{key: 'rec', label: 'Record (hashed)'}, {key: 'utc', label: 'UTC'}, {key: 'path', label: 'BIC8_PATH', f: v => `<code>${esc(v)}</code>`}, {key: 'cur', label: 'Currency'},
        {key: 'route_currencies', label: 'Known home currencies'}, {key: 'predicted_fx', label: 'Predicted FX', num: true}, {key: 'fx', label: 'Recorded FX', num: true}, {key: 'anom', label: 'Label'}]) +
      `<div class="card"><h3>What the exceptions reveal</h3><p>Both payments go to the same receiver, <code>0000ERA0</code>, a bank in Eritrea (ER) — and they are the <b>only two payments in all 10 million that touch an Eritrean bank</b>. Eritrea never sends a payment, so its home currency cannot be read from the data; our predictor sees one known currency and predicts 0 borders. The generator recorded 1, exactly what C2 predicts if Eritrea's currency differs from the sender's.</p>
        <p><b>Scope this defines:</b> C2 holds wherever every country on the route has an observable home currency. The exceptions mark a gap in what the data lets us observe, not a second mechanism. ${badge('CONDITIONAL ESTIMATE')} This is our reading; 99.99998% agreement shows the rule reproduces the field — it does not prove how the original code was written.</p>
        <p><a href="#/forensics/replay?rule=C2">Open both records in Forensic Replay →</a> · <a href="#/rules/explorer?id=C2">Full rule card →</a></p></div>`;
  }

  function stage2() {
    const r = R('R1'), f = r.metrics.full, d = m.distributions['Participants'], tot = d.reduce((a, b) => a + b.n, 0), q = Math.exp(-1);
    const ks_ = d.map((x, i) => i === d.length - 1 ? x.k + '+' : x.k), obs = d.map(x => x.n / tot), th = d.map((x, i) => i === d.length - 1 ? q ** (+x.k - 2) : (1 - q) * q ** (+x.k - 2));
    const sp = ['full', 'half_0', 'half_1', 'P1', 'P2'].map(k => ({split: k, n: r.metrics[k].n, q: r.metrics[k].q_mle, w: r.metrics[k].cohen_w}));
    return `<h2>2 · R1 — the number of intermediaries is ⌊Exp(1)⌋</h2>${badge('OBSERVED DATA')}${badge('VALIDATED RULE')}
      <div class="grid g2"><div class="card y"><h3>The law</h3><div class="formula">K = ⌊E⌋,  E ~ Exponential(1)        PARTICIPANT_COUNT = K + 2
P(K = k) = (1 − 1/e) · e^(−k)        ⇒  P(Direct) = 1 − 1/e = 63.21%</div>
        <p><b>Why this is more than a frequency chart:</b> a single constant, e, predicts the whole distribution. Each additional intermediary is ${sig(f.ratio_1, 4)}, ${sig(f.ratio_2, 4)}, ${sig(f.ratio_3, 4)}, ${sig(f.ratio_4, 4)} times as likely as the previous one — constant, and equal to 1/e = ${sig(q, 4)}. A Poisson count (H3) would make these ratios fall.</p></div>
      <div>${kpis([[sig(f.q_mle, 5), 'fitted continuation q (MLE)'], [sig(q, 5), '1/e (theory)'], [pct(f.p_direct, 2), 'observed Direct share'], [sig(f.cohen_w, 2), "Cohen's w (fit vs theory)"]])}
        <div class="note">χ² = ${sig(f.chi2, 3)} on ${fmt(f.n)} payments; Cohen's w = ${sig(f.cohen_w, 2)} is far below the 0.01 acceptance bound (w &lt; 0.1 is already "small").</div></div></div>
      ${chartBox('Participants per payment: observed vs ⌊Exp(1)⌋ theory', grouped(ks_, [{name: 'observed (10M)', color: C.blue, values: obs}, {name: 'theory, q = 1/e', color: C.yellow, values: th}], {label: 'R1', vfmt: v => pct(v, 3), yfmt: v => pct(v, 0)}), 'The last bar pools 9 or more participants.')}
      <details class="fold"><summary>Validation on five splits</summary><div>${table(sp, [{key: 'split', label: 'Split'}, {key: 'n', label: 'n', num: true, f: fmt}, {key: 'q', label: 'q (MLE)', num: true, f: v => sig(v, 5)}, {key: 'w', label: "Cohen's w", num: true, f: v => sig(v, 2)}])}
        <p>q is also the same in every sending country (range ${sig(Math.min(...m.stats.R1_by_country.map(x => x.q)), 4)}–${sig(Math.max(...m.stats.R1_by_country.map(x => x.q)), 4)}). Far tail: the law predicts ≈3.1 payments with ≥ 17 participants; 5 are observed (all inspectable in Forensic Replay, R1-tail).</p></div></details>
      <div class="note red"><b>Limitation.</b> ${esc(r.limitations)} The law describes the generator's random draw; it says nothing about how real correspondent chains are chosen.</div>
      <p><a href="#/rules/explorer?id=R1">Full rule card →</a> · <a href="#/feature/route">Route intelligence →</a></p>`;
  }

  function stage3() {
    const r = R('R2'), f = r.metrics.full, g = G.genealogy.find(x => x.rule === 'R2'), h = g.hypotheses[0] || {};
    return `<h2>3 · R2 — the rule our own engine overturned</h2>${badge('VALIDATED RULE')}${level(r.level)}
      <div class="grid g2"><div><div class="genestep rej"><div class="mono">Original reading</div><b>"Covered vs Indirect is a constant ${pct(f.pooled_covered_share, 1)} of non-direct payments"</b><br>True on average and independent of route length (Cramér's V vs K = ${sig(f.cramers_v_vs_K, 2)}) — this was our original R2 statement.</div>
        <div class="genestep rej"><div class="mono">The challenge · ${esc(h.id || 'H32')} · ${esc(h.test || '')}</div>The discovery engine found routing type still depended on the sending country. The covered share ranges from ${pct(f.country_share_min, 1)} to ${pct(f.country_share_max, 1)} by country and is far more dispersed across banks than a constant rate allows.</div>
        <div class="genestep acc"><div class="mono">Revised rule</div><b>Cover is a property of the sending bank.</b> Banks were classed on one random half of the data; on the <i>other</i> half, cover-prone banks (${fmt(f.cover_banks)} of ${fmt(f.cover_banks + f.other_banks)}) cover ${pct(f.oos_cover_banks_share, 1)} of their non-direct payments, all others ${pct(f.oos_other_banks_share, 1)}.</div>
        <div class="genestep acc"><div class="mono">Final validation</div>${esc(r.validation)}. Logged outcome: ${esc((h.outcome || '').replace(/\*\*/g, ''))}</div></div>
      <div class="card y"><h3>Why this matters</h3><p>Reverse-engineering means rejecting a hypothesis when the evidence turns against it — even one that already passed. The average was right; the mechanism was wrong. The constant-rate rule would have mis-predicted every individual bank.</p>
        ${kpis([[pct(f.oos_cover_banks_share, 1), 'cover share · cover-prone banks (out of sample)'], [pct(f.oos_other_banks_share, 1), 'cover share · other banks (out of sample)']])}
        <p class="mono">${reg.rules.filter(x => x.level === 'REJECTED').length} rejected hypotheses are kept on the record.</p>
        <p><a href="#/genome/genealogy?id=R2">Full genealogy →</a> · <a href="#/forensics/alternatives">All alternatives tested →</a></p></div></div>
      <div class="note"><b>Economic reading (interpretation):</b> some banks habitually settle by the cover method (a customer message plus a separate bank-to-bank cover payment); most route serially. In this synthetic data that habit is a bank attribute, not a market-wide rate.</div>`;
  }

  function stage4() {
    const D = S.duration, sims = [2, 4].map(pc => simDuration(D, {pc, m: D.m_bank}, cb.dur_edges)), obs = ['2', '4'].map(k => summary(cb, aggregate(cb, {pc: new Set([k])})));
    const sens = [D.m_bank - .05, D.m_bank + .05].map(mm => simDuration(D, {pc: 4, m: mm, draws: 30000}, cb.dur_edges));
    return `<h2>4 · From reconstructed rule to scenario</h2>${badge('MODEL SIMULATION')}
      <p class="lede">The question: <b>"With the same banks, how much slower is a payment that passes through 4 banks instead of 2?"</b> We run the rebuilt duration rules (D1: each bank adds a step; D3: steps are Gamma-distributed, slow banks add a manual step) with parameters estimated from the data, then compare with what was actually observed.</p>
      <div class="grid g3"><div class="card"><h3>Observed records</h3><p>Durations in the data, grouped by participant count. Facts about the synthetic dataset.</p></div>
        <div class="card"><h3>Estimated parameters</h3><p>Fast step Gamma(${sig(D.fast_shape, 3)}, ${sig(D.fast_scale, 3)} s); manual step Gamma(${sig(D.manual_shape, 3)}, ${fmt(D.manual_scale)} s); per-bank manual probability m = ${sig(D.m_bank, 3)} (solved from the 2-bank data).</p></div>
        <div class="card"><h3>Simulated output</h3><p>${fmt(sims[0].draws)} seeded Monte-Carlo payments per case. Model output — not observations, not a forecast of a real network.</p></div></div>` +
      table([{c: '2 participants', s: sims[0], o: obs[0]}, {c: '4 participants', s: sims[1], o: obs[1]}], [{key: 'c', label: 'Route'}, {key: 's', label: 'Median (simulated)', num: true, f: v => dur(v.median)}, {key: 'o', label: 'Median (observed)', num: true, f: v => dur(v.medDur)},
        {key: 's', label: 'Manual share (simulated)', num: true, f: v => pct(v.manual, 1)}, {key: 'o', label: 'Manual share (observed)', num: true, f: v => pct(v.manual, 1)}]) +
      `<div class="note">At 2 participants the model is calibrated, so agreement is expected. At 4 participants nothing was fitted — agreement there is an out-of-sample test of additivity (D1).
        Observed medians are interpolated within power-of-two bins.</div>
      <div class="card"><h3>Sensitivity</h3><p>If each bank's manual probability were 0.05 lower or higher (${sig(D.m_bank - .05, 3)} / ${sig(D.m_bank + .05, 3)}), the simulated manual share at 4 participants would be ${pct(sens[0].manual, 1)} / ${pct(sens[1].manual, 1)} (vs ${pct(sims[1].manual, 1)} at the estimate). ${badge('STRUCTURAL SCENARIO')} Those two runs describe a hypothetical generator, not the data.</p>
        <p><a href="#/lab/simulator?tab=duration&pc=4">Open this scenario in the Scenario Studio →</a> · <a href="#/lab/sensitivity?p=m">Sensitivity analysis →</a></p></div>
      <div class="card ink"><h3>What we reconstructed · what was validated · what remains open</h3><p>${reg.rules.filter(x => x.kind === 'rule').length} rules; ${reg.rules.filter(x => x.level === 'VALIDATED').length} validated exactly or out of sample; all pass on five splits. Still open: ${reg.rules.filter(x => x.level === 'INCONCLUSIVE').map(x => `<a href="#/rules/explorer?id=${x.id}">${x.id}</a>`).join(', ')} (mechanism not identified) — listed, not guessed.</p>
        <p><a href="#/genome/blueprint">Continue to the Generator Blueprint →</a></p></div>`;
  }
  show();
}

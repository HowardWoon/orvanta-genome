// Feature Intelligence: one page per feature group. Each combines the group's rules, interactive evidence and links into the lab.
import {data, esc, fmt, pct, sig, kpis, header, badge, level, table, bars, grouped, lines, heatmap, chartBox, img, select, C} from '../core.js';

const G = {temporal: 'Temporal', currency: 'Currency & Value', institution: 'Institution', route: 'Route', duration: 'Duration & Continuity', fx: 'FX & Participant',
  ttype: 'Transaction Type', party: 'Party Details', token: 'Token', anomaly: 'Anomaly'};
const LEDE = {
  temporal: 'When payments happen: UTC timestamps, reconstructed local clocks, weekly volume regimes and the Monday change points.',
  currency: 'What currency and how much: home-currency selection, route-drawn currencies (C3), amount model (A1/A2), tails (A3) and the USD roundness fingerprint (F1).',
  institution: 'Who sends and relays: bank size, hub structure, the cover-propensity classes behind R2 and the bank-level customer mix (P5).',
  route: 'How a payment travels: geometric number of intermediaries (R1), hidden hops (R4), path/BIC consistency (R6) and loop frequency (G3).',
  duration: 'How long settlement takes: fast and manual processing steps, additivity over banks (D1/D3) and the hour-of-day Simpson effect (D2).',
  fx: 'How many conversions occur: FX count equals currency changes along the path (C2), with the participant count derived from the path (R6).',
  ttype: 'Direct, Indirect or Covered: routing type is implied by participants (R1) and cover is a bank-level propensity (R2, revised).',
  party: 'Who the parties are: IBAN availability by country (P2), structured details (P1b), business/consumer types (P4) and per-bank customer mix (P5).',
  token: 'What the free-text party fields contain: address-line tokens, structure markers and how they co-occur.',
  anomaly: 'The six labelled anomaly types: their rates, profiles and how well simple detectors recover them (X1–X6).'};
const slug = Object.fromEntries(Object.entries(G).map(([k, v]) => [v, k]));

export async function render(el, ctx) {
  const key = ctx.sub, name = G[key];
  const [reg, m] = await Promise.all([data('registry'), data('meta')]);
  const ids = reg.groups[name] || [], rules = ids.map(id => reg.rules.find(r => r.id === id)).filter(Boolean);
  const charts = [...new Set(rules.flatMap(r => r.charts || []))];
  const nav = Object.entries(G).map(([k, v]) => k === key ? `<b class="tag lv-sup">${esc(v)}</b>` : `<a class="tag" href="#/feature/${k}">${esc(v)}</a>`).join('');
  el.innerHTML = header('Payment intelligence', name, LEDE[key]) + `<div style="margin:6px 0 10px">${nav}</div>` +
    `<h2>Rules in this group</h2><div class="grid g3">${rules.map(r => `<div class="card">${level(r.level)}<h3><a href="#/rules/explorer?id=${r.id}">${r.id}</a> · ${esc(r.title)}</h3>
      <div class="formula">${esc(r.formulation)}</div><div class="mono">Effect: ${esc(r.effect_size)}</div></div>`).join('')}</div>
    <h2>Evidence</h2><div id="evhead" class="evhead"></div><div id="ev" class="grid g2"><div class="loading">Loading evidence…</div></div>
    ${charts.length ? `<details class="fold"><summary>Static figures used in the PDF (${charts.length}) — same pipeline, not interactive</summary><div><div class="grid g2">${charts.map(c => img(c, c.replace(/_/g, ' '))).join('')}</div></div></details>` : ''}`;
  const ev = el.querySelector('#ev');
  const html = await (EV[key])(m, ev, ctx);
  const lead = html.match(/^(?:<span class="badge[^"]*">[^<]*<\/span>|<div><\/div>|<div class="mono">[^<]*<\/div>)+/);
  el.querySelector('#evhead').innerHTML = lead ? lead[0].replace(/<div><\/div>/g, '') : '';
  ev.innerHTML = lead ? html.slice(lead[0].length) : html;
  if (POST[key]) POST[key](ev, m, ctx);
}

const EV = {
  async temporal(m) {
    const t = await data('temporal');
    const wk = t.weekly;
    const hours = [...Array(24).keys()], byType = o => hours.map(h => t.local_hour.find(x => x.otype === o && x.lh === h)?.n || 0);
    const cp = t.change_points;
    return badge('OBSERVED DATA') + `<div></div>` +
      chartBox('Weekly volume and the Monday change points', lines(wk.map(w => w.wk.slice(5)), [{name: 'payments per week', color: C.blue, values: wk.map(w => w.n), points: true}], {label: 'Weekly volume', xlabel: 'week starting (UTC)'}),
        `Binary segmentation with a BIC penalty found ${cp.change_points.length} change points in ${cp.n_days} days — all on ${[...new Set(cp.weekdays)].join('/')}s (rule T4b). First and last weeks are partial.`) +
      `<div id="tdaily"></div>` +
      chartBox('Reconstructed local hour of sending', grouped(hours.map(String), [{name: 'business sender', color: C.blue, values: byType('B')}, {name: 'consumer sender', color: C.yellow, values: byType('C')}], {label: 'Local hour', xlabel: 'local hour (UTC + country offset, T1)'}),
        'Local clock = UTC + the sender country offset that best aligns activity (T1). Business senders concentrate in office hours.') +
      chartBox('Weekly profile', lines(wk.map(w => w.wk.slice(5)), [{name: 'share business sender', color: C.ink, values: wk.map(w => w.ob)}, {name: 'share direct', color: C.teal, values: wk.map(w => w.direct)}], {label: 'Weekly shares', ymin: 0, ymax: 1, yfmt: v => pct(v, 0), vfmt: v => pct(v, 2)}),
        'Mix stays flat while volume steps: levels change, composition does not.');
  },
  async currency(m) {
    const e = m.evidence, f = m.forensics, s = await data('sim');
    const eff = [...s.amount.country].sort((a, b) => a.eff - b.eff);
    const pick = [...eff.slice(0, 8), ...eff.slice(-8)];
    return badge('OBSERVED DATA') + badge('CONDITIONAL ESTIMATE') + '<div></div>' +
      chartBox('A2 · country effect on ln(amount)', bars(pick.map(c => ({label: c.cc, value: c.eff, color: c.eff < 0 ? C.coral : C.blue, note: `n = ${fmt(c.n)}`})), {horizontal: true, left: 40, label: 'Country effects', vfmt: v => sig(v, 3)}),
        `Lowest and highest 8 of ${eff.length} sender-country effects (ln scale, relative to the pooled mean, after sender/receiver type). exp(effect) is the multiplicative factor.`) +
      chartBox('F1 · whole-unit amounts: USD vs converted', bars(f.usd_roundness.map(r => ({label: r.usd_denominated ? 'USD-denominated' : 'other currencies', value: r.whole_units, color: r.usd_denominated ? C.blue : C.grey, note: `n = ${fmt(r.n)}`})), {horizontal: true, left: 130, label: 'Whole units', vfmt: v => pct(v, 1)}),
        'Amounts are generated in USD and converted: USD keeps round values, other currencies lose them. A fixed-rate search could not restore roundness (negative result).') +
      chartBox('Cents = .00 by currency', bars(f.cents00_by_currency.map(r => ({label: r.cur, value: r.cents00, color: r.cur === 'USD' ? C.blue : C.grey})), {label: 'cents00', vfmt: v => pct(v, 2), h: 230}), 'Share of amounts with zero cents.') +
      chartBox('Vehicle currencies (payment currency ≠ either home currency)', bars(e.vehicle_ccy.map(r => ({label: r.cur, value: r.n})), {horizontal: true, left: 50, label: 'Vehicle currencies', vfmt: fmt}), 'Under C3 the currency is drawn from the currencies of banks on the route.') +
      `<div>${table(e.local_ccy_by_country.slice(0, 14), [{key: 'cc', label: 'Sender country'}, {key: 'n', label: 'Rows', num: true, f: fmt}, {key: 'local_sh', label: 'Local currency', num: true, f: v => pct(v)},
        {key: 'eur', label: 'EUR', num: true, f: v => pct(v)}, {key: 'usd', label: 'USD', num: true, f: v => pct(v)}, {key: 'gbp', label: 'GBP', num: true, f: v => pct(v)}], {h: 340})}<div class="cfoot">C1: payment currency usually equals the sender's home currency.</div></div>`;
  },
  async institution(m) {
    const I = await data('institutions');
    return badge('OBSERVED DATA') + '<div></div>' + kpis([[fmt(I.total_banks), 'banks'], [pct(I.concentration.top1pct_share), 'hops via top 1% banks'], [sig(I.concentration.gini_strength, 3), 'Gini of strength'], [pct(I.network.reciprocity), 'edge reciprocity']]) +
      chartBox('Hub size vs straight-through processing', bars(I.hub_stp.map(h => ({label: 'D' + h.pr_decile, value: h.slow_bank_share, note: `${h.banks} banks`})), {label: 'Slow banks by PageRank decile', vfmt: v => pct(v), h: 230, xlabel: 'PageRank decile (1 = smallest)'}),
        'Share of banks classed slow (manual-prone) by PageRank decile. Deciles 1–9 sit near 50–58%; only the top decile drops (28%). Observed association, not a causal claim.') +
      chartBox('Bank size by sender share', bars(m.evidence.stp_by_size.map(s => ({label: s.sz, value: s.slow_bank_share, note: `${fmt(s.banks)} banks`})), {label: 'Slow share by size', vfmt: v => pct(v), h: 230}), 'Slow-bank share by payments handled: the 119 banks with 10k+ payments are almost never slow (0.8%), small banks about 55%.') +
      `<div>${table(I.top_hubs, [{key: 'b', label: 'BIC8'}, {key: 'cc', label: 'Country'}, {key: 'pagerank', label: 'PageRank', num: true, f: v => sig(v, 3)}, {key: 'out_s', label: 'Out', num: true, f: fmt}, {key: 'in_s', label: 'In', num: true, f: fmt}, {key: 'slow', label: 'Manual share', num: true, f: v => pct(v)}], {h: 360})}
        <div class="cfoot">Top hubs. Synthetic BIC8 codes — not real institutions. Full ranking in the <a href="#/lab/routes">Route playground</a>.</div></div>` +
      `<div class="card"><h3>Who pairs with whom (G1 · inconclusive)</h3><p>Pair counts deviate from a size-only configuration model (χ²/dof = ${fmt(I.pairing.chi2_per_dof)}; ${fmt(I.pairing.chi2_per_dof_given_country_pair)} given the country pair).
        Corr(log observed, log expected) = ${sig(I.pairing.corr_log, 3)}. Something beyond size and country drives pairing, but we could not pin down the mechanism, so G1 stays INCONCLUSIVE.</p></div>`;
  },
  async route(m) {
    const s = await data('sim'), I = await data('institutions'), q = s.route.q, d = m.distributions['Participants'], tot = d.reduce((a, b) => a + b.n, 0);
    const ks = d.map((x, i) => i === d.length - 1 ? x.k + '+' : x.k), obs = d.map(x => x.n / tot), pred = ks.map((k, i) => { const kk = parseInt(k); return i === ks.length - 1 ? q ** (kk - 2) : (1 - q) * q ** (kk - 2); });
    const st = m.stats;
    return badge('OBSERVED DATA') + badge('VALIDATED RULE') + '<div></div>' +
      chartBox('R1 · participants: observed vs geometric(q)', grouped(ks, [{name: 'observed', color: C.blue, values: obs}, {name: `geometric, q = ${q.toFixed(4)}`, color: C.yellow, values: pred}], {label: 'Participants', vfmt: v => pct(v, 3), yfmt: v => pct(v, 0)}),
        `Intermediaries K ~ Geometric: P(K = k) = (1 − q)qᵏ. MLE q = ${q.toFixed(4)} ≈ 1/e, so P(Direct) = ${pct(1 - q, 2)}.`) +
      chartBox('R1 · q by sender country', bars(st.R1_by_country.map(r => ({label: r.cc, value: r.q, note: `n = ${fmt(r.n)}`})), {label: 'q by country', vfmt: v => sig(v, 4), h: 230, max: .45}),
        'q is the same everywhere (within sampling error) — routing depth does not depend on geography.') +
      chartBox('G3 · repeated intermediaries: observed vs birthday prediction', grouped(I.loops.map(l => 'pc ' + l.pc), [{name: 'observed', color: C.blue, values: I.loops.map(l => l.obs_inter_repeat)}, {name: 'predicted (i.i.d. size-weighted draws)', color: C.yellow, values: I.loops.map(l => l.pred_iid)}], {label: 'Loops', vfmt: v => pct(v, 3), yfmt: v => pct(v, 1)}),
        'Intermediaries are drawn independently in proportion to size, so repeats follow the birthday problem.') +
      chartBox('R4 · hidden-hop rate by routing type and participants', bars(st.R4_by_ttype.map(r => ({label: `${r.ttype[0]}·${r.pc}`, value: r.p, note: `n = ${fmt(r.n)}`})), {label: 'R4', vfmt: v => pct(v, 2), h: 230}),
        `Each link is hidden with p ≈ ${pct(s.route.p_link, 2)}, so P(gap) = 1 − (1 − p)^(pc−1).`);
  },
  async duration(m) {
    const st = m.stats, e = m.evidence;
    return badge('OBSERVED DATA') + badge('CONDITIONAL ESTIMATE') + '<div></div>' +
      kpis([[st.fast_step.median + ' s', 'median pc=2 all-STP'], [fmt(st.manual_step.median) + ' s', 'median manual step'], [sig(st.manual_step.ks_gamma, 3), 'KS gamma fit (manual)'], [sig(st.fast_step.ks_D, 3), 'KS gamma fit (fast)']]) +
      chartBox('D1 · duration by bank speed class', bars(e.dur_bank_class.map(r => ({label: `${r.o_cls}→${r.b_cls}`, value: r.med, note: `slow share ${pct(r.slow_share)}`})), {horizontal: true, left: 90, label: 'Median by class', vfmt: v => v + ' s'}),
        'Median seconds by sender/receiver bank speed class. Slow banks add a manual step; effects add up across banks.') +
      chartBox('D2 · hour-of-day effect: raw vs bank fixed effects', lines([...Array(24).keys()].map(String), [{name: 'raw', color: C.coral, values: e.simpson_hour.map(h => h.raw)}, {name: 'adjusted (two-way FE)', color: C.blue, values: e.simpson_hour.map(h => h.adjusted)}], {label: 'Simpson hour', zero: false, vfmt: v => sig(v, 3)}),
        'Raw hourly differences disappear once bank composition is held fixed — a Simpson effect, not a time-of-day rule.') +
      chartBox('D1 sensitivity to thresholds', table(st.sensitivity_D1, [{key: 'slow_threshold_s', label: 'Slow s', num: true}, {key: 'class_threshold', label: 'Class cut', num: true}, {key: 'med_0', label: '0 slow', num: true}, {key: 'med_1', label: '1 slow', num: true}, {key: 'med_2', label: '2 slow', num: true}, {key: 'additivity', label: 'Additivity', num: true, f: v => sig(v, 3)}]),
        'Additivity ≈ 2 means two slow banks take about twice as long as one: the conclusion is stable across thresholds.');
  },
  async fx(m) {
    const d = m.distributions['FX conversions'], tot = d.reduce((a, b) => a + b.n, 0);
    return badge('OBSERVED DATA') + badge('VALIDATED RULE') + '<div></div>' +
      chartBox('FX conversions per payment', bars(d.map(x => ({label: x.k, value: x.n})), {label: 'FX', vfmt: v => pct(v / tot, 2), h: 230}), 'C2: the count equals the number of currency changes along the path when each bank uses its home currency — exact on all rows.') +
      `<div class="card"><h3>Why FX is deterministic here</h3><p>Each bank holds a home currency (the currency it most often sends). Walking the path from sender to receiver and counting changes reproduces
       <code>FX_CONVERSIONS</code> exactly on 100% of rows, and a separate pure-Python implementation agrees on a 200k sample. C3 then explains the payment currency itself: it is drawn from the currencies present on the route,
       which is why it is usually one of the endpoints' currencies.</p><p><a href="#/lab/explorer?fx=0">Explore FX = 0 payments</a> · <a href="#/lab/explorer?fx=3">FX = 3+</a></p></div>`;
  },
  async ttype(m) {
    const s = await data('sim'), d = m.distributions['Routing type'], tot = d.reduce((a, b) => a + b.n, 0);
    return badge('OBSERVED DATA') + badge('CONDITIONAL ESTIMATE') + '<div></div>' +
      chartBox('Routing type', bars(d.map(x => ({label: x.k, value: x.n})), {horizontal: true, left: 80, label: 'Routing type', vfmt: v => pct(v / tot, 2)}), 'Direct ⇔ 2 participants (exact). Non-direct payments are Covered or Indirect.') +
      chartBox('R2 (revised) · cover is a bank-level propensity', bars([{label: 'cover-prone banks', value: s.route.cover_share_cover_banks, color: C.blue}, {label: 'other banks', value: s.route.cover_share_other, color: C.grey}, {label: 'pooled', value: s.route.pooled_cover, color: C.yellow}], {horizontal: true, left: 120, label: 'Cover share', vfmt: v => pct(v, 1)}),
        `Classes learned on one half, tested on the other (out of sample). ${pct(s.route.cover_bank_share, 1)} of banks are cover-prone. The original "constant 11.3%" rule was rejected by the discovery engine.`);
  },
  async party(m) {
    const e = m.evidence;
    return badge('OBSERVED DATA') + '<div></div>' +
      `<div>${table(e.iban_by_country, [{key: 'cc', label: 'Bank country'}, {key: 'n', label: 'Rows', num: true, f: fmt}, {key: 'iban', label: 'IBAN share', num: true, f: v => pct(v, 2)}, {key: 'strct', label: 'Structured', num: true, f: v => pct(v, 2)}], {h: 380})}
        <div class="cfoot">P2: an account is an IBAN exactly when the bank's country uses IBANs — the share is ≈0% or ≈100% per country.</div></div>` +
      `<div>${table(e.ob_share_by_country, [{key: 'cc', label: 'Country'}, {key: 'n', label: 'Rows', num: true, f: fmt}, {key: 'ob', label: 'Sender business', num: true, f: v => pct(v)}, {key: 'bb', label: 'Receiver business', num: true, f: v => pct(v)}], {h: 380})}
        <div class="cfoot">P5: the business share is a per-bank property (split-half r ≈ 0.99), which aggregates into these country differences.</div></div>`;
  },
  async token(m) {
    const T = await data('tokens');
    const pres = T.presence.filter(p => p.side === 'ordering');
    const toks = [...new Set(pres.map(p => p.token))];
    return badge('OBSERVED DATA') + `<div class="mono">Computed on a ${fmt(T.sample)}-row random sample of the free-text party fields.</div>` +
      chartBox('Token presence in sender details', grouped(toks, [{name: 'business', color: C.blue, values: toks.map(t => pres.find(p => p.token === t && p.party === 'B')?.share || 0)}, {name: 'consumer', color: C.yellow, values: toks.map(t => pres.find(p => p.token === t && p.party === 'C')?.share || 0)}], {label: 'Tokens', vfmt: v => pct(v, 1), yfmt: v => pct(v, 0)}),
        `Structured (/key/value) details: ${pct(T.structured_share, 1)} of rows; double-slash markers: ${pct(T.double_slash_share, 1)}.`) +
      chartBox('Token co-occurrence (φ-style share)', heatmap(T.cooc_tokens, T.cooc_tokens, T.cooc, {label: 'Co-occurrence', text: true, cw: 52, rh: 26, vfmt: v => sig(v, 2)}), 'Share of rows containing the row token that also contain the column token.') +
      chartBox('Lines per party field', bars(Object.entries(T.lines).map(([k, v]) => ({label: k, value: v})), {label: 'Lines', vfmt: fmt, h: 220}), 'Most fields follow the 4×35 MT layout (rule P1b).');
  },
  async anomaly(m) {
    const st = m.stats, e = m.evidence;
    return badge('OBSERVED DATA') + '<div></div>' +
      chartBox('Anomaly rate per 10,000 payments (95% CI)', bars(st.anomaly_rates.map(a => ({label: a.anom.replace(/_/g, ' ').toLowerCase(), value: a.per_10k, color: C.coral, note: `CI ${sig(a.lo, 3)}–${sig(a.hi, 3)} · n = ${fmt(a.n)}`})), {horizontal: true, left: 190, label: 'Anomaly rates', vfmt: v => sig(v, 3)}),
        'Wilson 95% intervals over all 10M rows.') +
      `<div>${table(e.anom_profile, [{key: 'a', label: 'Label'}, {key: 'n', label: 'n', num: true, f: fmt}, {key: 'oB', label: 'Sender business', num: true, f: v => pct(v)}, {key: 'bB', label: 'Receiver business', num: true, f: v => pct(v)},
        {key: 'med_amt', label: 'Median amount', num: true, f: v => fmt(v, 0)}, {key: 'med_dur', label: 'Median s', num: true, f: v => fmt(v)}])}<div class="cfoot">Profiles differ by type; drill down in the <a href="#/lab/anomalies">Anomaly explorer</a>.</div></div>` +
      `<div>${table(st.detectors, [{key: 'label', label: 'Label'}, {key: 'detector', label: 'Detector'}, {key: 'precision', label: 'Precision', num: true, f: v => pct(v)}, {key: 'recall', label: 'Recall', num: true, f: v => pct(v)}, {key: 'f1', label: 'F1', num: true, f: v => sig(v, 3)}])}
        <div class="cfoot">Rule-based detectors built from the reconstructed mechanisms.</div></div>`;
  },
};
const POST = {
  async temporal(ev, m, ctx) {   // interactive daily series from the temporal cube
    const t = await data('temporal'), c = t.cube, ix = Object.fromEntries(c.cols.map((k, i) => [k, i]));
    const box = ev.querySelector('#tdaily');
    const draw = () => {
      const tt = box.querySelector('#tt').value, me = box.querySelector('#tm').value;
      const by = {};
      for (const r of c.rows) { if (tt !== 'ALL' && r[ix.ttype] !== tt) continue; const d = r[ix.d]; by[d] = by[d] || {n: 0, s1: 0, nm: 0}; by[d].n += r[ix.n]; by[d].s1 += r[ix.s1]; by[d].nm += r[ix.nm]; }
      const days = Object.keys(by).sort(), val = d => me === 'n' ? by[d].n : me === 'amt' ? Math.exp(by[d].s1 / by[d].n) : by[d].nm / by[d].n;
      box.querySelector('#tc').innerHTML = lines(days.map(d => d.slice(5)), [{name: me, color: C.blue, values: days.map(val)}], {label: 'Daily series', xt: 13, vfmt: v => me === 'manual' ? pct(v, 2) : me === 'amt' ? '$' + fmt(v, 0) : fmt(v), yfmt: me === 'manual' ? (v => pct(v, 0)) : undefined, zero: me === 'n'});
      ctx.setParams({tt, me});
    };
    box.innerHTML = chartBox('Daily series (interactive)', `<div class="controls">${select('tt', 'Routing type', [['ALL', 'All'], 'Direct', 'Indirect', 'Covered'], ctx.params.tt || 'ALL')}${select('tm', 'Measure', [['n', 'Payments'], ['amt', 'Geometric mean amount (USD)'], ['manual', 'Manual-step share']], ctx.params.me || 'n')}</div><div id="tc"></div>`,
      'Each control re-aggregates the daily cube (date × weekday × type × anomaly × party types). Amounts and manual share are flat; only volume changes.');
    box.querySelectorAll('select').forEach(s => s.addEventListener('change', draw)); draw();
  },
};
export {slug};

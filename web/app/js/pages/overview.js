// Executive overview: headline first, the three strongest findings next, depth on demand.
import {data, esc, fmt, pct, sig, badge, level} from '../core.js';

export async function render(el) {
  const [m, reg, rep, L] = await Promise.all([data('meta'), data('registry'), data('replay'), data('ledger')]);
  const rules = reg.rules.filter(r => r.kind === 'rule'), R = id => rules.find(r => r.id === id);
  const ev = id => { const e = L.entries.find(x => x.type === 'rule' && x.rules[0] === id); return e ? `<a class="tag" href="#/library/ledger?q=${e.id}">${e.id}</a>` : ''; };
  const c2 = R('C2').metrics.full, r1 = R('R1').metrics.full, r2 = R('R2').metrics.full;
  const nVal = rules.filter(r => r.level === 'VALIDATED').length, open = rules.filter(r => r.level === 'INCONCLUSIVE');
  const strong = m.discovery.pairs.filter(p => p.verdict).length;
  el.innerHTML = `<div class="sect">ORVANTA · Generator Genome</div><h1>The generator behind 10 million payments is a small set of simple, testable rules.</h1>
    <p class="lede">We reconstructed ${rules.length} explicit rules from the synthetic Swift dataset alone — ${nVal} validated exactly or out of sample, all passing on five independent splits — and we show where they fail.</p>
    <div class="tourcta"><span><b>New here?</b> The guided tour walks through the three strongest discoveries, their exceptions and one simulation in about two minutes.</span><a class="go" href="#/tour">Start the 2-minute tour →</a></div>
    <h2>The three findings that matter most</h2>
    <div class="hl3">
      <div class="card">${level(R('C2').level)}<b class="big">${fmt(c2.n - c2.exceptions)} / ${fmt(c2.n)}</b><h3>C2 · FX conversions are fixed by the route</h3>
        <p>Conversions = number of home-currency borders between adjacent banks in BIC8_PATH. The only 2 exceptions are the only 2 payments that touch an Eritrean bank, whose home currency is unobservable.</p>
        <p><a href="#/forensics/replay?rule=C2">See the 2 exceptions</a> · <a href="#/rules/explorer?id=C2">rule</a> ${ev('C2')}</p></div>
      <div class="card">${level(R('R1').level)}<b class="big">q = ${sig(r1.q_mle, 4)} ≈ 1/e</b><h3>R1 · Intermediaries follow ⌊Exp(1)⌋</h3>
        <p>One constant predicts the route-length distribution: P(K = k) = (1 − 1/e)e<sup>−k</sup>, so ${pct(r1.p_direct, 2)} of payments are Direct. Fit vs theory: Cohen's w = ${sig(r1.cohen_w, 2)}.</p>
        <p><a href="#/tour?s=2">See the fit</a> · <a href="#/rules/explorer?id=R1">rule</a> ${ev('R1')}</p></div>
      <div class="card">${level(R('R2').level)}<b class="big">${pct(r2.oos_cover_banks_share, 1)} vs ${pct(r2.oos_other_banks_share, 1)}</b><h3>R2 · Overturned by our own engine</h3>
        <p>"Cover is a constant ${pct(r2.pooled_covered_share, 1)}" was wrong: cover is a property of the sending bank. Classes learned on one half, tested on the other.</p>
        <p><a href="#/genome/genealogy?id=R2">See how it was overturned</a> · <a href="#/rules/explorer?id=R2">rule</a> ${ev('R2')}</p></div>
    </div>
    <details class="fold"><summary>Supporting discoveries (C3, F1, D1, T4b, P5)</summary><div>${['C3', 'F1', 'D1', 'T4b', 'P5'].map(id => R(id)).map(r => `<p style="margin:7px 0">${level(r.level)}<a href="#/rules/explorer?id=${r.id}"><b>${r.id}</b></a> ${esc(r.title)} ${ev(r.id)}</p>`).join('')}
      <p class="mono">C3's 1.27% outside-route currencies are mostly a route-independent EUR/USD vehicle draw (EUR 1.41%, USD 0.75% on routes without either; H38, supported, not separately validated).</p></div></details>
    <h2>The research journey</h2><div class="journey">
      <a href="#/rules/discovery" style="background:#fff"><b>1 · Discover</b><span>${m.discovery.pairs.length} feature pairs · ${strong} strong · all explained</span></a>
      <a href="#/genome/blueprint" style="background:#cfe3f8"><b>2 · Reconstruct</b><span>generator blueprint</span></a>
      <a href="#/forensics/replay" style="background:#fde2df"><b>3 · Challenge</b><span>real records · counterexamples</span></a>
      <a href="#/validation/scorecard" style="background:var(--blue);color:#fff"><b>4 · Validate</b><span>5 splits · out of sample</span></a>
      <a href="#/lab/simulator" style="background:var(--coral);color:#fff"><b>5 · Simulate</b><span>scenario studio</span></a>
      <a href="#/method/limitations" style="background:var(--yellow)"><b>6 · Explain</b><span>economics & limits</span></a></div>
    <h2>What remains unresolved</h2><div class="grid g3">${open.map(r => `<div class="card warn">${level(r.level)}<h3><a href="#/rules/explorer?id=${r.id}">${r.id}</a> · ${esc(r.title)}</h3><p style="font-size:13.5px">${esc(r.limitations)}</p></div>`).join('')}</div>
    <p class="mono">${fmt(m.rows)} payments · ${rules.length} rules · ${reg.rules.filter(r => r.level === 'REJECTED').length} rejected hypotheses kept · ${fmt(L.n)} evidence records · <a href="#/command/coverage">research coverage by feature group</a></p>
    <div class="note red"><b>Scope.</b> The data is synthetic. Findings describe this generator, not real Swift traffic, real banks or causal mechanisms. Rules are reconstructions consistent with the data; we have not recovered the generator's source code.</div>`;
}

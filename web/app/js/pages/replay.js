// Forensic Replay: exact supporting / contradicting counts and real (hash-sampled, de-identified) records per rule.
import {data, esc, fmt, pct, kpis, header, badge, level, tag, table, select, download, toCSV} from '../core.js';

const WHY = {
  R6: r => `known BICs = ${r.known_bics}; PARTICIPANT_COUNT = ${r.pc}`,
  R7: r => `path ${r.has_gap ? 'contains' : 'has no'} '...'; flag = ${r.cont}`,
  R1: r => `${r.pc} participants (${r.intermediaries} intermediaries); type = ${r.ttype}`,
  C2: r => `route currencies ${r.route_currencies}: ${r.predicted_fx} border(s) predicted; recorded FX = ${r.fx}`,
  C3: r => `payment currency ${r.cur} ${String(r.route_currencies).split('›').includes(r.cur) ? 'is' : 'is NOT'} among route currencies ${r.route_currencies}`,
  R5: r => `first path BIC ${r.first_replaced ? '≠' : '='} ORDERING_BIC8; last ${r.last_replaced ? '≠' : '='} BENEFICIARY_BIC8`,
  P2: r => `IBAN prefix ${r.iban_prefix} vs bank country ${r.bic_country}`,
  'R1-tail': r => `${r.pc} participants — part of the predicted far tail`,
  X3: r => `log10(amount / A1 baseline) = ${r.log10_vs_A1_baseline}`,
  X2: r => `${r.copies_in_group} labelled copies share amount, path and duration within 2 h`,
};

export async function render(el, ctx) {
  const [R, reg] = await Promise.all([data('replay'), data('registry')]);
  const ids = R.rules.map(r => r.rule), id = ids.includes(ctx.params.rule) ? ctx.params.rule : 'C2', side0 = ctx.params.side === 'support' ? 'support' : 'contra';
  el.innerHTML = header('Forensic intelligence', 'Forensic replay',
    'Pick a rule and inspect the actual payments behind it: exact counts of supporting and contradicting records over all eligible rows, the condition that decides each one, and a reproducible sample of the records themselves.') +
    badge('OBSERVED DATA') +
    `<div class="note">Counts are exact over the full 10M rows. Records are a deterministic hash-ordered sample (seed ${R.seed}), so the same rows appear every time; up to ${R.n_sup} supporting and ${R.n_cx} contradicting rows are shown, and every contradicting row is shown when there are ${R.n_cx} or fewer. Privacy: ${esc(R.privacy)}.</div>
    <div class="controls">${select('rr', 'Rule', R.rules.map(r => [r.rule, `${r.rule} · ${r.title}`]), id)}${select('rs', 'Show', [['contra', 'Contradicting records'], ['support', 'Supporting records']], side0)}
      <label class="ctl">Filter shown records<input id="rf" type="search" placeholder="currency, BIC, label…"></label><button class="sec" id="rx">Export shown records (CSV)</button></div><div id="ro"></div>`;
  const draw = () => {
    const x = R.rules.find(r => r.rule === el.querySelector('#rr').value), side = el.querySelector('#rs').value, q = el.querySelector('#rf').value.toLowerCase();
    ctx.setParams({rule: x.rule, side: side === 'contra' ? '' : side});
    const base = reg.rules.find(r => r.id === x.rule.split('-')[0]);
    const rows = (side === 'support' ? x.supporting_rows : x.contradicting_rows).map(v => Object.fromEntries(x.columns.map((c, i) => [c, v[i]])))
      .filter(r => !q || JSON.stringify(r).toLowerCase().includes(q));
    el._rows = rows; el._cols = x.columns;
    const why = WHY[x.rule] || (() => '');
    const shownTotal = side === 'support' ? x.sample.supporting_shown : x.sample.contradicting_shown, pop = side === 'support' ? x.supporting : x.contradicting;
    el.querySelector('#ro').innerHTML = `<div class="card">${base ? level(base.level) : ''}${tag(x.kind, 'info')}<h3>${esc(x.rule)} · ${esc(x.title)}</h3><p>${esc(x.plain)}</p>
        <div class="formula">ELIGIBLE  ${esc(x.condition.eligible)}\nSUPPORTS  ${esc(x.condition.supports)}</div>
        <p class="mono">${base ? `<a href="#/rules/explorer?id=${base.id}">Rule ${base.id}</a> · <a href="#/validation/splits?id=${base.id}">split validation</a> · <a href="#/rules/atlas?focus=${base.id}">atlas</a> · ` : ''}<a href="#/library/ledger?q=${encodeURIComponent(x.rule)}">evidence ledger</a></p></div>` +
      kpis([[fmt(x.eligible), 'eligible records'], [fmt(x.supporting), 'supporting'], [fmt(x.contradicting), 'contradicting'], [x.support_rate == null ? '—' : pct(x.support_rate, x.support_rate > .9999 && x.support_rate < 1 ? 5 : 2), 'support rate (exact)'],
        [`${shownTotal} of ${fmt(pop)}`, `${side === 'support' ? 'supporting' : 'contradicting'} records inspected`]]) +
      (!pop ? `<div class="empty">No ${side === 'support' ? 'supporting' : 'contradicting'} record exists among ${fmt(x.eligible)} eligible rows — the rule holds without exception.${side === 'contra' ? ' Switch to supporting records to see examples.' : ''}</div>` :
        `<div class="note">${pop > shownTotal ? `Showing a ${shownTotal}-row sample of ${fmt(pop)}. The sample illustrates the condition; it is not used to estimate rates (those are the exact counts above).` : 'These are all the records in this group.'}</div>` +
        table(rows.map(r => ({...r, why: why(r)})), [{key: 'why', label: 'Why it ' + (side === 'support' ? 'supports' : 'contradicts'), f: v => `<span class="${side === 'support' ? 'ok-cell' : 'bad-cell'}">${esc(v)}</span>`},
          ...x.columns.map(c => ({key: c, label: c, num: ['usd', 'dur', 'fx', 'pc'].includes(c), f: v => c === 'path' ? `<code class="recrow">${esc(v)}</code>` : esc(v === true ? 'yes' : v === false ? 'no' : v)}))],
          {h: 520, empty: 'No shown record matches the filter.'}));
  };
  el.querySelectorAll('select').forEach(s => s.addEventListener('change', draw));
  el.querySelector('#rf').addEventListener('input', draw);
  el.querySelector('#rx').onclick = () => download(`replay_${el.querySelector('#rr').value}_${el.querySelector('#rs').value}.csv`, toCSV(el._rows || [], el._cols || []), 'text/csv');
  draw();
}

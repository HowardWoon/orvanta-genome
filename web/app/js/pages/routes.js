// Route Playground: country-level route patterns (aggregates with n ≥ 150) and the top-600 institution table.
import {data, esc, fmt, pct, sig, usd, dur, kpis, header, badge, table, bars, scatter, chartBox, select, download, toCSV, C} from '../core.js';

const rowsOf = d => d.rows.map(r => Object.fromEntries(d.cols.map((c, i) => [c, r[i]])));
export async function render(el, ctx) {
  const [R, I] = await Promise.all([data('routes'), data('institutions')]);
  const routes = rowsOf(R), banks = rowsOf(I), P = ctx.params, view = P.view === 'banks' ? 'banks' : 'routes';
  el.innerHTML = header('Interactive research lab', 'Route playground',
    `Explore how payments travel between countries and which institutions carry them. Route patterns are aggregated by sender-bank country › receiver-bank country, routing type, currency, continuity and participants; only patterns with at least ${R.min_n} payments are shipped (they cover ${pct(R.coverage)} of all rows).`) +
    badge('OBSERVED DATA') +
    `<div class="chips" id="rtab">${[['routes', 'Route patterns'], ['banks', 'Institutions (top 600)']].map(([k, t]) => `<button type="button" class="chip${k === view ? ' on' : ''}" data-v="${k}">${t}</button>`).join('')}</div><div id="rbody" style="margin-top:12px"></div>`;
  const body = el.querySelector('#rbody');
  el.querySelector('#rtab').addEventListener('click', e => { const b = e.target.closest('.chip'); if (!b) return; el.querySelectorAll('#rtab .chip').forEach(c => c.classList.toggle('on', c === b)); (b.dataset.v === 'banks' ? bankView : routeView)({}); });

  function routeView(p) {
    const curs = ['ALL', ...[...new Set(routes.map(r => r.cur))].sort()];
    body.innerHTML = `<div class="controls"><label class="ctl">Country or route<input id="rq" type="search" value="${esc(p.q || '')}" placeholder="e.g. US, GB › DE"></label>
      ${select('rt', 'Routing type', ['ALL', 'Direct', 'Indirect', 'Covered'], p.t || 'ALL')}${select('rc', 'Currency', curs, p.c || 'ALL')}${select('rk', 'Continuity', ['ALL', 'Y', 'N'], p.k || 'ALL')}
      ${select('rp', 'Participants', ['ALL', ...[...new Set(routes.map(r => r.pc))].sort((a, b) => a - b).map(String)], p.p || 'ALL')}
      ${select('rs', 'Sort by', [['n', 'Payments'], ['med_dur', 'Median duration'], ['manual', 'Manual share'], ['med_amt', 'Median amount'], ['fx', 'Mean FX conversions']], p.s || 'n')}
      <button class="sec" id="rr">Reset</button><button class="sec" id="rx">Export CSV</button></div><div id="ro"></div>`;
    const draw = () => {
      const q = body.querySelector('#rq').value.trim().toUpperCase().replace('>', '›'), t = body.querySelector('#rt').value, c = body.querySelector('#rc').value, k = body.querySelector('#rk').value, pp = body.querySelector('#rp').value, s = body.querySelector('#rs').value;
      const f = routes.filter(r => (!q || r.route.toUpperCase().includes(q)) && (t === 'ALL' || r.ttype === t) && (c === 'ALL' || r.cur === c) && (k === 'ALL' || r.cont === k) && (pp === 'ALL' || String(r.pc) === pp)).sort((a, b) => b[s] - a[s]);
      ctx.setParams({view: 'routes', q, t: t === 'ALL' ? '' : t, c: c === 'ALL' ? '' : c, k: k === 'ALL' ? '' : k, p: pp === 'ALL' ? '' : pp, s: s === 'n' ? '' : s});
      body._rows = f;
      const o = body.querySelector('#ro');
      if (!f.length) { o.innerHTML = '<div class="empty">No route pattern matches. Patterns with fewer than 150 payments are not shipped — widen the filters.</div>'; return; }
      const n = f.reduce((a, r) => a + r.n, 0), w = key => f.reduce((a, r) => a + r[key] * r.n, 0) / n;
      const byPc = {}; for (const r of f) { byPc[r.pc] = byPc[r.pc] || {n: 0, d: 0, m: 0}; byPc[r.pc].n += r.n; byPc[r.pc].d += r.med_dur * r.n; byPc[r.pc].m += r.manual * r.n; }
      const pcs = Object.keys(byPc).map(Number).sort((a, b) => a - b);
      o.innerHTML = kpis([[fmt(f.length), 'route patterns'], [fmt(n), 'payments covered'], [dur(w('med_dur')), 'weighted median duration'], [pct(w('manual')), 'manual share'], [sig(w('fx'), 3), 'mean FX conversions']]) +
        `<div class="grid g2">${chartBox('Manual share by participants (filtered)', bars(pcs.map(k => ({label: String(k), value: byPc[k].m / byPc[k].n, note: `${fmt(byPc[k].n)} payments`})), {label: 'Manual by pc', vfmt: v => pct(v, 1), h: 230, xlabel: 'participants'}),
          'More banks → more chances of a manual step (D1/D3). Payment-weighted over the matching patterns.')}
        ${chartBox('Top patterns by payments', bars(f.slice(0, 12).map(r => ({label: `${r.route} ${r.ttype[0]}${r.pc}`, value: r.n})), {horizontal: true, left: 140, label: 'Top patterns', vfmt: fmt}), 'Label: route, routing type initial and participants.')}</div>` +
        table(f.slice(0, 400), [{key: 'route', label: 'Route'}, {key: 'ttype', label: 'Type'}, {key: 'cur', label: 'Currency'}, {key: 'cont', label: 'Cont.'}, {key: 'pc', label: 'pc', num: true}, {key: 'n', label: 'Payments', num: true, f: fmt},
          {key: 'med_dur', label: 'Median s', num: true, f: v => fmt(v)}, {key: 'p90_dur', label: 'P90 s', num: true, f: v => fmt(v)}, {key: 'manual', label: 'Manual', num: true, f: v => pct(v, 1)}, {key: 'fx', label: 'FX', num: true, f: v => sig(v, 3)}, {key: 'med_amt', label: 'Median USD', num: true, f: v => fmt(v, 0)}], {h: 460}) +
        (f.length > 400 ? `<div class="mono">Showing 400 of ${fmt(f.length)}; export for all.</div>` : '');
    };
    body.querySelectorAll('input,select').forEach(x => x.addEventListener('input', draw));
    body.querySelector('#rr').onclick = () => { body.querySelector('#rq').value = ''; ['rt', 'rc', 'rk', 'rp'].forEach(id => body.querySelector('#' + id).value = 'ALL'); body.querySelector('#rs').value = 'n'; draw(); };
    body.querySelector('#rx').onclick = () => download('route_patterns.csv', toCSV(body._rows || [], R.cols), 'text/csv');
    draw();
  }

  function bankView(p) {
    const ccs = ['ALL', ...[...new Set(banks.map(b => b.cc))].sort()];
    body.innerHTML = `<div class="controls"><label class="ctl">BIC8 contains<input id="bq" type="search" value="${esc(p.bq || '')}" placeholder="e.g. 0309"></label>${select('bc', 'Country', ccs, p.bc || 'ALL')}
      ${select('bs', 'Sort by', [['as_intermediary', 'As intermediary'], ['sent', 'Sent'], ['received', 'Received'], ['cover_share', 'Cover share'], ['manual_pc2', 'Manual share (pc = 2)'], ['sender_b', 'Business-sender share']], p.bs || 'as_intermediary')}
      <button class="sec" id="bx">Export CSV</button></div><div id="bo"></div>`;
    const draw = () => {
      const q = body.querySelector('#bq').value.trim().toUpperCase(), c = body.querySelector('#bc').value, s = body.querySelector('#bs').value;
      const f = banks.filter(b => (!q || b.bic.includes(q)) && (c === 'ALL' || b.cc === c)).sort((a, b) => b[s] - a[s]);
      ctx.setParams({view: 'banks', bq: q, bc: c === 'ALL' ? '' : c, bs: s === 'as_intermediary' ? '' : s});
      body._rows = f;
      body.querySelector('#bo').innerHTML = !f.length ? '<div class="empty">No institution in the top 600 matches.</div>' :
        `<div class="grid g2">${chartBox('Cover share vs payments relayed', scatter(f.map(b => ({x: Math.max(b.as_intermediary, 1), y: b.cover_share, label: b.bic, color: b.cover_share > .3 ? C.blue : C.grey})), {logX: true, label: 'Cover scatter', xlabel: 'payments as intermediary (log)', ylabel: 'cover share', ymin: 0, ymax: 1, yfmt: v => pct(v, 0)}),
          'R2 (revised): cover is a property of the instructing bank — most banks sit near zero while a minority cover a large share, instead of one constant rate.')}
        ${chartBox('Business share: as sender vs as receiver bank', scatter(f.map(b => ({x: b.sender_b, y: b.receiver_b, label: b.bic})), {label: 'P5 scatter', xmin: 0, xmax: 1, ymin: 0, ymax: 1, diag: false, xlabel: 'business share of senders', ylabel: 'business share of receivers', yfmt: v => pct(v, 0)}),
          'P5: each bank has its own customer mix, stable across halves of the data.')}</div>` +
        table(f, [{key: 'bic', label: 'BIC8 (synthetic)'}, {key: 'cc', label: 'Country'}, {key: 'sent', label: 'Sent', num: true, f: fmt}, {key: 'received', label: 'Received', num: true, f: fmt}, {key: 'as_intermediary', label: 'Intermediary', num: true, f: fmt},
          {key: 'sender_b', label: 'Biz sender', num: true, f: v => pct(v)}, {key: 'receiver_b', label: 'Biz receiver', num: true, f: v => pct(v)}, {key: 'cover_share', label: 'Cover', num: true, f: v => pct(v)}, {key: 'manual_pc2', label: 'Manual pc=2', num: true, f: v => pct(v)}], {h: 460});
    };
    body.querySelectorAll('input,select').forEach(x => x.addEventListener('input', draw));
    body.querySelector('#bx').onclick = () => download('institutions_top600.csv', toCSV(body._rows || [], I.cols), 'text/csv');
    draw();
  }
  (view === 'banks' ? bankView : routeView)(P);
}

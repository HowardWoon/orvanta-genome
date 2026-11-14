// Rule Dependency Atlas: zoom (wheel/buttons/pinch-free), pan (drag), search, upstream/downstream tracing, edge-kind filters, rule focus.
import {data, esc, header, badge, table, select, chips} from '../core.js';

const STY = {deterministic: ['#111827', 3.2, 'none'], stochastic: ['#2479D8', 2.2, 'none'], unresolved: ['#2479D8', 2.2, '8 5'], independent: ['#747474', 1.6, '4 4'], confounded: ['#9a7b00', 1.8, '1 4']};
const OX = 95, OY = 34, W = 178, H = 36, VB0 = [0, 0, 1380, 590];
const DIRECTED = new Set(['deterministic', 'stochastic', 'unresolved']);

export async function render(el, ctx) {
  const A = (await data('meta')).atlas, N = Object.fromEntries(A.nodes.map(n => [n.id, n]));
  const st = {node: ctx.params.node || '', dir: ctx.params.dir || 'both', focus: ctx.params.focus || '', kinds: new Set((ctx.params.kinds || Object.keys(STY).join(',')).split(',').filter(k => STY[k])), vb: window.innerWidth < 700 ? [0, 0, 470, 590] : [...VB0]};   // phones start zoomed on the left of the graph; drag to pan, Fit to see all
  el.innerHTML = header('Rule intelligence', 'Rule dependency atlas',
    'The reconstructed generator as a dependency graph. Scroll or use the buttons to zoom, drag to pan, click a node to trace what it depends on (upstream) and what depends on it (downstream).') +
    badge('STRUCTURAL SCENARIO') + `<div class="note red">${esc(A.note)}</div>
    <div class="controls"><label class="ctl">Find a node<input id="as" type="search" list="anodes" value="" placeholder="e.g. PATH, amount"></label>
      <datalist id="anodes">${A.nodes.map(n => `<option value="${esc(n.label)}">`).join('')}</datalist>
      ${select('ad', 'Trace direction', [['both', 'Upstream + downstream'], ['up', 'Upstream only'], ['down', 'Downstream only']], st.dir)}
      <label class="ctl">Focus rule<input id="ar" type="search" value="${esc(st.focus)}" placeholder="e.g. R1" style="min-width:90px"></label>
      <button class="sec" id="ax">Reset view</button></div>
    <div id="ak">${chips('edge kind', Object.keys(STY).map(k => [k, k]), st.kinds)}</div>
    <div style="margin-top:12px">
      <div><div class="atlasbox" id="ab"><div class="zoom"><button id="zi" aria-label="Zoom in">+</button><button id="zo" aria-label="Zoom out">−</button><button id="zf" class="sec" aria-label="Fit">Fit</button></div><svg id="asvg" role="img" aria-label="Rule dependency atlas"></svg></div>
        <p class="mono" style="text-transform:none">${Object.entries(A.legend).map(([k, v]) => `<b>${k}</b> ${esc(v)}`).join(' · ')} · dashed box = latent generator entity</p></div>
      <div id="ap" style="margin-top:14px"></div></div>`;
  const svg = el.querySelector('#asvg');
  const sync = () => ctx.setParams({node: st.node, dir: st.dir === 'both' ? '' : st.dir, focus: st.focus, kinds: st.kinds.size === 5 ? '' : [...st.kinds].join(',')});
  const trace = id => {   // BFS over directed edges; undirected kinds (independent/confounded) shown only as adjacent context
    const up = new Set(), down = new Set(), E = A.edges.filter(e => st.kinds.has(e.kind) && DIRECTED.has(e.kind));
    const walk = (start, fwd, out) => { const q = [start]; while (q.length) { const c = q.shift(); for (const e of E) { const [from, to] = fwd ? [e.source, e.target] : [e.target, e.source]; if (from === c && !out.has(to) && to !== id) { out.add(to); q.push(to); } } } };
    if (st.dir !== 'down') walk(id, false, up); if (st.dir !== 'up') walk(id, true, down);
    return {up, down};
  };
  const draw = () => {
    const f = st.node, fr = st.focus.trim().toUpperCase();
    const T = f ? trace(f) : null, onNode = new Set(f ? [f, ...T.up, ...T.down] : []);
    const edgeOn = e => {
      if (fr) return e.rules.some(r => r.toUpperCase() === fr);
      if (!f) return true;
      if (!DIRECTED.has(e.kind)) return e.source === f || e.target === f;
      return onNode.has(e.source) && onNode.has(e.target) && ((T.up.has(e.source) || e.source === f) && (T.up.has(e.target) || e.target === f) || (T.down.has(e.target) || e.target === f) && (T.down.has(e.source) || e.source === f));
    };
    const ruleNodes = fr ? new Set(A.edges.filter(edgeOn).flatMap(e => [e.source, e.target])) : null;
    let s = `<defs>${Object.entries(STY).map(([k, [c]]) => `<marker id="ar_${k}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="${c}"/></marker>`).join('')}</defs><g id="vp">`;
    for (const e of A.edges) {
      if (!st.kinds.has(e.kind)) continue;
      const a = N[e.source], b = N[e.target], [c, w, da] = STY[e.kind], on = edgeOn(e);
      const x1 = a.x + OX, y1 = a.y + OY, x2 = b.x + OX, y2 = b.y + OY, dx = x2 - x1, dy = y2 - y1, L = Math.max(Math.hypot(dx, dy), 1);
      const mk = DIRECTED.has(e.kind) ? `marker-end="url(#ar_${e.kind})"` : '';
      s += `<path class="edge${on ? '' : ' dim'}" d="M${x1},${y1}L${(x2 - dx / L * 24).toFixed(0)},${(y2 - dy / L * 22).toFixed(0)}" stroke="${c}" stroke-width="${w}" stroke-dasharray="${da}" fill="none" ${mk}><title>${esc(a.label)} → ${esc(b.label)} · ${e.kind} · ${e.rules.join(', ')}: ${esc(e.evidence)}</title></path>`;
      if (on && !DIRECTED.has(e.kind) || on && e.kind === 'unresolved') s += `<text x="${((x1 + x2) / 2).toFixed(0)}" y="${((y1 + y2) / 2 - 4).toFixed(0)}" font-size="15" font-weight="700" fill="${c}" text-anchor="middle">${{independent: '⟂', confounded: '≈', unresolved: '?'}[e.kind]}</text>`;
    }
    for (const n of A.nodes) {
      const x = n.x + OX, y = n.y + OY, on = ruleNodes ? ruleNodes.has(n.id) : (!f || onNode.has(n.id) || A.edges.some(e => st.kinds.has(e.kind) && !DIRECTED.has(e.kind) && [e.source, e.target].includes(f) && [e.source, e.target].includes(n.id)));
      const fill = n.id === f ? '#F4D52E' : T?.up.has(n.id) ? '#cfe3f8' : T?.down.has(n.id) ? '#fde2df' : n.kind === 'field' ? '#fff' : '#F5F0E6';
      s += `<g class="node${on ? '' : ' dim'}" data-id="${n.id}" tabindex="0" role="button" aria-label="${esc(n.label)}"><rect x="${x - W / 2}" y="${y - H / 2}" width="${W}" height="${H}" fill="${fill}" stroke="#111827" stroke-width="2.2" stroke-dasharray="${n.kind === 'latent' ? '5 3' : 'none'}"/><text x="${x}" y="${y + 4}" font-size="11" font-weight="600" text-anchor="middle">${esc(n.label)}</text></g>`;
    }
    svg.innerHTML = s + '</g>';
    svg.setAttribute('viewBox', st.vb.join(' '));
    svg.querySelectorAll('g.node').forEach(g => { const pick = () => { st.node = st.node === g.dataset.id ? '' : g.dataset.id; st.focus = ''; el.querySelector('#ar').value = ''; draw(); }; g.addEventListener('click', ev => { if (!moved) pick(); }); g.addEventListener('keydown', ev => { if (ev.key === 'Enter' || ev.key === ' ') { ev.preventDefault(); pick(); } }); });
    panel(T);
    sync();
  };
  const panel = T => {
    const f = st.node, fr = st.focus.trim().toUpperCase(), P = el.querySelector('#ap');
    const rows = A.edges.filter(e => st.kinds.has(e.kind) && (fr ? e.rules.some(r => r.toUpperCase() === fr) : !f || e.source === f || e.target === f)).map(e => ({...e, s: N[e.source].label, t: N[e.target].label}));
    const ruleLinks = rs => rs.map(r => `<a href="#/rules/explorer?id=${esc(r)}">${esc(r)}</a>`).join(' ');
    P.innerHTML = (f ? `<div class="card y"><h3>${esc(N[f].label)}</h3><div class="mono">${esc(N[f].kind)} · ${T.up.size} upstream · ${T.down.size} downstream</div>
        <p style="margin:6px 0 0"><b>Depends on:</b> ${[...T.up].map(i => esc(N[i].label)).join(', ') || '— (root)'}<br><b>Feeds:</b> ${[...T.down].map(i => esc(N[i].label)).join(', ') || '— (leaf)'}</p></div>` :
      fr ? `<div class="card y"><h3>Rule ${esc(fr)}</h3><div class="mono">${rows.length} edge(s) carry this rule</div></div>` : `<div class="card">Click a node to trace it, or type a rule id to see where it acts. ${A.nodes.length} nodes · ${A.edges.length} edges.</div>`) +
      `<h3 style="margin-top:14px">Edges${f || fr ? ' in focus' : ''}</h3>` + table(rows, [{key: 's', label: 'From'}, {key: 't', label: 'To'}, {key: 'kind', label: 'Kind'}, {key: 'rules', label: 'Rules', f: ruleLinks}, {key: 'evidence', label: 'Evidence'}], {h: 420, empty: fr ? `No atlas edge carries rule ${fr}. Not every rule is an edge (e.g. anomaly-profile rules).` : 'No edges of the selected kinds.'});
  };
  // ---- zoom & pan on the viewBox
  let drag = null, moved = false;
  const zoom = (k, cx, cy) => { const [x, y, w, h] = st.vb, nw = Math.min(Math.max(w * k, 250), 2400), nh = nw * h / w; cx ??= x + w / 2; cy ??= y + h / 2; st.vb = [cx - (cx - x) * nw / w, cy - (cy - y) * nh / h, nw, nh]; svg.setAttribute('viewBox', st.vb.join(' ')); };
  const toSvg = (ev) => { const r = svg.getBoundingClientRect(), [x, y, w, h] = st.vb, s = Math.max(w / r.width, h / r.height); return [x + (ev.clientX - r.left - (r.width - w / s) / 2) * s, y + (ev.clientY - r.top - (r.height - h / s) / 2) * s, s]; };
  svg.addEventListener('wheel', ev => { ev.preventDefault(); const [cx, cy] = toSvg(ev); zoom(ev.deltaY > 0 ? 1.15 : 1 / 1.15, cx, cy); }, {passive: false});
  svg.addEventListener('pointerdown', ev => { drag = {x: ev.clientX, y: ev.clientY, vb: [...st.vb]}; moved = false; });
  window.addEventListener("pointermove", ev => { if (!drag || !svg.isConnected) return; const r = svg.getBoundingClientRect(), s = Math.max(drag.vb[2] / r.width, drag.vb[3] / r.height), dx = ev.clientX - drag.x, dy = ev.clientY - drag.y;
    if (Math.abs(dx) + Math.abs(dy) > 4) { moved = true; svg.classList.add('drag'); } if (moved) { st.vb = [drag.vb[0] - dx * s, drag.vb[1] - dy * s, drag.vb[2], drag.vb[3]]; svg.setAttribute('viewBox', st.vb.join(' ')); } });
  window.addEventListener('pointerup', () => { drag = null; svg.classList.remove('drag'); setTimeout(() => { moved = false; }, 0); });
  el.querySelector('#zi').onclick = () => zoom(1 / 1.3); el.querySelector('#zo').onclick = () => zoom(1.3); el.querySelector('#zf').onclick = () => { st.vb = [...VB0]; svg.setAttribute('viewBox', st.vb.join(' ')); };
  el.querySelector('#as').addEventListener('change', e => { const q = e.target.value.trim().toLowerCase(); const n = A.nodes.find(n => n.label.toLowerCase() === q) || A.nodes.find(n => n.label.toLowerCase().includes(q) || n.id === q);
    if (n) { st.node = n.id; st.focus = ''; el.querySelector('#ar').value = ''; const x = n.x + OX, y = n.y + OY; st.vb = [x - 450, y - 190, 900, 385]; draw(); } else if (q) el.querySelector('#ap').insertAdjacentHTML('afterbegin', `<div class="empty">No node matches “${esc(e.target.value)}”.</div>`); });
  el.querySelector('#ad').addEventListener('change', e => { st.dir = e.target.value; draw(); });
  el.querySelector('#ar').addEventListener('input', e => { st.focus = e.target.value; if (st.focus) st.node = ''; draw(); });
  el.querySelector('#ak').addEventListener('click', e => { const b = e.target.closest('.chip'); if (!b) return; const k = b.dataset.v; st.kinds.has(k) ? st.kinds.delete(k) : st.kinds.add(k); b.classList.toggle('on'); b.setAttribute('aria-pressed', st.kinds.has(k)); draw(); });
  el.querySelector('#ax').addEventListener('click', () => { st.node = ''; st.focus = ''; st.dir = 'both'; st.kinds = new Set(Object.keys(STY)); st.vb = [...VB0]; el.querySelector('#ar').value = ''; el.querySelector('#as').value = ''; el.querySelector('#ad').value = 'both'; el.querySelectorAll('#ak .chip').forEach(c => { c.classList.add('on'); c.setAttribute('aria-pressed', 'true'); }); draw(); });
  draw();
}

// Core: data loading, formatting, UI components, SVG chart library. No external dependencies.
const cache = {};
export async function data(name) {
  if (!cache[name]) cache[name] = fetch(`data/${name}.json`).then(r => { if (!r.ok) throw new Error(`data/${name}.json → HTTP ${r.status}`); return r.json(); });
  return cache[name];
}
export const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));
// d/p are ignored unless numeric, so these can be passed straight to table/chart callbacks that supply extra arguments.
const dig = (d, def, lo, hi) => typeof d === 'number' && Number.isFinite(d) ? Math.min(Math.max(Math.round(d), lo), hi) : def;
export const fmt = (x, d) => x == null || Number.isNaN(+x) ? '—' : Number(x).toLocaleString('en-US', {minimumFractionDigits: dig(d, 0, 0, 10), maximumFractionDigits: dig(d, 0, 0, 10)});
export const pct = (x, d) => x == null || Number.isNaN(+x) ? '—' : (100 * x).toFixed(dig(d, 1, 0, 10)) + '%';
export const sig = (x, p) => x == null || Number.isNaN(+x) ? '—' : (x > 0.999 && x < 1 ? (+x).toFixed(7) : Math.abs(x) >= 1e5 ? fmt(x) : String(Number(Number(x).toPrecision(dig(p, 4, 1, 21)))));   // exact-match shares never shown as 1
export const usd = x => x == null ? '—' : '$' + (x >= 1e6 ? fmt(x / 1e6, 2) + 'M' : x >= 1e3 ? fmt(x, 0) : fmt(x, 2));
export const dur = s => s == null ? '—' : s < 120 ? fmt(s, 0) + ' s' : s < 7200 ? fmt(s / 60, 1) + ' min' : fmt(s / 3600, 2) + ' h';

// ---------------------------------------------------------------- components
export const card = (h, cls = '') => `<div class="card ${cls}">${h}</div>`;
export const kpis = items => `<div class="kpis">${items.map(([v, l, t]) => `<div class="card kpi"${t ? ` title="${esc(t)}"` : ''}><b>${v}</b><span>${l}</span></div>`).join('')}</div>`;
export const tag = (t, cls = '') => `<span class="tag ${esc(cls || t)}">${esc(t)}</span>`;
export const LEVEL_CLS = {'VALIDATED': 'lv-val', 'STRONGLY SUPPORTED': 'lv-strong', 'SUPPORTED': 'lv-sup', 'CANDIDATE': 'lv-cand', 'INCONCLUSIVE': 'lv-inc', 'REJECTED': 'lv-rej'};
export const level = l => `<span class="tag ${LEVEL_CLS[l] || ''}">${esc(l)}</span>`;
export const badge = t => `<span class="badge b-${esc(t.toLowerCase().replace(/[^a-z]+/g, '-'))}">${esc(t)}</span>`;   // OBSERVED DATA · MODEL SIMULATION · …
export function header(section, title, lede) {
  return `<div class="sect">${esc(section)}</div><h1>${esc(title)}</h1>${lede ? `<p class="lede">${lede}</p>` : ''}`;
}
export function table(rows, cols, opt = {}) {
  if (!rows.length) return `<div class="empty">${esc(opt.empty || 'No rows match the current selection.')}</div>`;
  const head = cols.map(c => `<th${c.num ? ' class="num"' : ''}>${esc(c.label)}</th>`).join('');
  const body = rows.map(r => `<tr${opt.pick ? ` class="pick${opt.sel === r[opt.pick] ? ' sel' : ''}" data-id="${esc(r[opt.pick])}" tabindex="0"` : ''}>` +
    cols.map(c => `<td${c.num ? ' class="num"' : ''}>${c.f ? c.f(r[c.key], r) : esc(r[c.key])}</td>`).join('') + '</tr>').join('');
  return `<div class="tbl"${opt.h ? ` style="max-height:${opt.h}px"` : ''}><table><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table></div>`;
}
export function chartBox(title, svg, foot, opt = {}) {
  return `<figure class="chart${opt.cls ? ' ' + opt.cls : ''}"><figcaption class="ctitle">${title}</figcaption>${svg}${foot ? `<div class="cfoot">${foot}</div>` : ''}</figure>`;
}
export const img = (f, cap) => `<figure class="chart"><img src="charts/${f}.png" alt="${esc(cap)}" loading="lazy"><div class="cfoot">${esc(cap)} · static figure from the analysis pipeline</div></figure>`;
export function select(id, label, options, value, opt = {}) {
  return `<label class="ctl">${esc(label)}<select id="${id}"${opt.multiple ? ' multiple size="4"' : ''}>${options.map(o => {
    const [v, t] = Array.isArray(o) ? o : [o, o];
    const on = opt.multiple ? (value || []).includes(String(v)) : String(v) === String(value);
    return `<option value="${esc(v)}"${on ? ' selected' : ''}>${esc(t)}</option>`;
  }).join('')}</select></label>`;
}
export function chips(group, options, active) {
  return `<div class="chips" role="group" aria-label="${esc(group)}">${options.map(([v, t]) =>
    `<button type="button" class="chip${active.has(String(v)) ? ' on' : ''}" data-group="${esc(group)}" data-v="${esc(v)}" aria-pressed="${active.has(String(v))}">${esc(t)}</button>`).join('')}</div>`;
}
export function slider(id, label, min, max, step, value, unit = '') {
  return `<label class="ctl">${esc(label)} <output id="${id}_o">${esc(value)}${unit}</output><input type="range" id="${id}" min="${min}" max="${max}" step="${step}" value="${value}"></label>`;
}
export function download(filename, text, mime = 'text/plain') {
  const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob([text], {type: mime})); a.download = filename;
  document.body.appendChild(a); a.click(); setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 500);
}
export const toCSV = (rows, cols) => [cols.join(','), ...rows.map(r => cols.map(c => { const v = r[c] ?? ''; const s = typeof v === 'object' ? JSON.stringify(v) : String(v); return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s; }).join(','))].join('\n');

// ---------------------------------------------------------------- charts (SVG, responsive via viewBox)
export const C = {ink: '#111827', blue: '#2479D8', yellow: '#F4D52E', coral: '#EF5147', grey: '#747474', teal: '#1F8A70', olive: '#9a7b00', paper: '#F5F0E6', grid: '#e8e2d4'};
export const PALETTE = [C.blue, C.ink, C.teal, C.yellow, C.grey, C.olive];
const niceTicks = (lo, hi, n = 5) => {
  if (!(hi > lo)) return [lo];
  const step0 = (hi - lo) / n, mag = 10 ** Math.floor(Math.log10(step0)), step = [1, 2, 2.5, 5, 10].map(m => m * mag).find(s => s >= step0);
  const out = []; for (let v = Math.ceil(lo / step) * step; v <= hi + 1e-9; v += step) out.push(+v.toFixed(10)); return out;
};
const tickFmt = v => Math.abs(v) >= 1e6 ? fmt(v / 1e6, 1) + 'M' : Math.abs(v) >= 1e3 ? fmt(v / 1e3, Math.abs(v) >= 1e4 ? 0 : 1) + 'k' : (Math.abs(v) < 1 && v !== 0 ? String(+v.toFixed(3)) : fmt(v, v % 1 ? 1 : 0));
function legend(series) {
  return `<div class="legend">${series.map(s => `<span><i style="background:${s.color};${s.dash ? 'border-top:2px dashed ' + s.color + ';background:none;height:0' : ''}"></i>${esc(s.name)}</span>`).join('')}</div>`;
}
function frame(W, H, P, x0, x1, y0, y1, opt) {
  const sx = v => P.l + (v - x0) / (x1 - x0 || 1) * (W - P.l - P.r), sy = v => H - P.b - (v - y0) / (y1 - y0 || 1) * (H - P.t - P.b);
  let g = '';
  for (const t of (opt.yticks || niceTicks(y0, y1))) g += `<line x1="${P.l}" x2="${W - P.r}" y1="${sy(t)}" y2="${sy(t)}" stroke="${C.grid}"/><text x="${P.l - 6}" y="${sy(t) + 3}" text-anchor="end">${opt.yfmt ? opt.yfmt(t) : tickFmt(t)}</text>`;
  g += `<line x1="${P.l}" x2="${W - P.r}" y1="${H - P.b}" y2="${H - P.b}" stroke="${C.ink}" stroke-width="1.5"/><line x1="${P.l}" x2="${P.l}" y1="${P.t}" y2="${H - P.b}" stroke="${C.ink}" stroke-width="1.5"/>`;
  if (opt.xlabel) g += `<text x="${(P.l + W - P.r) / 2}" y="${H - 4}" text-anchor="middle" class="axl">${esc(opt.xlabel)}</text>`;
  if (opt.ylabel) g += `<text x="12" y="${(P.t + H - P.b) / 2}" text-anchor="middle" class="axl" transform="rotate(-90 12 ${(P.t + H - P.b) / 2})">${esc(opt.ylabel)}</text>`;
  return {sx, sy, g};
}
// Responsive sizing: on touch-size screens the chart's coordinate width matches the real width, so 10-unit labels render at ~10 px
// instead of being scaled down to 4–5 px. Pages re-render when the viewport crosses a width bucket (main.js).
export const fitW = d => { const vw = window.innerWidth || 1200; return vw < 1000 ? Math.max(290, Math.min(d, vw - 58)) : d; };
const fmtv = (opt, v) => opt.vfmt ? opt.vfmt(v) : sig(v);
// Accessible data alternative under every chart: the exact plotted values, readable without hover (touch screens, screen readers)
function dataDetails(head, rows) {
  if (!rows.length) return '';
  return `<details class="cdata"><summary>Data table (${rows.length} rows)</summary><div class="tbl" style="max-height:300px;box-shadow:none"><table><thead><tr>${head.map(h => `<th>${esc(h)}</th>`).join('')}</tr></thead><tbody>${rows.map(r => `<tr>${r.map((c, i) => `<td${i ? ' class="num"' : ''}>${esc(c)}</td>`).join('')}</tr>`).join('')}</tbody></table></div></details>`;
}
const svgOpen = (W, H, label) => `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(label || 'chart')}" preserveAspectRatio="xMidYMid meet">`;

export function bars(data, opt = {}) {   // data: [{label, value, color?, note?}]
  if (!data.length) return '<div class="empty">No data in the current selection.</div>';
  if (opt.horizontal) {
    const W = opt.w || fitW(640), rowH = opt.rowH || 22, L0 = opt.left || 120, P = {l: W < 520 ? Math.min(L0, Math.round(W * .4)) : L0, r: W < 520 ? 48 : 60, t: 8, b: 26}, H = P.t + P.b + rowH * data.length;
    const cut = t => { const mx = Math.max(6, Math.floor((P.l - 8) / 6.1)); t = String(t); return t.length > mx ? t.slice(0, mx - 1) + '…' : t; };
    const max = opt.max ?? Math.max(...data.map(d => d.value), 0), min = Math.min(0, ...data.map(d => d.value));
    const sx = v => P.l + (v - min) / (max - min || 1) * (W - P.l - P.r);
    let s = svgOpen(W, H, opt.label);
    for (const t of niceTicks(min, max, 4)) s += `<line x1="${sx(t)}" x2="${sx(t)}" y1="${P.t}" y2="${H - P.b}" stroke="${C.grid}"/><text x="${sx(t)}" y="${H - 8}" text-anchor="middle">${opt.xfmt ? opt.xfmt(t) : tickFmt(t)}</text>`;
    data.forEach((d, i) => {
      const y = P.t + i * rowH, x0 = sx(Math.min(0, d.value)), w = Math.abs(sx(d.value) - sx(0));
      s += `<text x="${P.l - 6}" y="${y + rowH / 2 + 4}" text-anchor="end"><title>${esc(d.label)}</title>${esc(cut(d.label))}</text><rect x="${x0}" y="${y + 3}" width="${Math.max(w, 1)}" height="${rowH - 6}" fill="${d.color || C.blue}" stroke="${C.ink}" stroke-width="1"><title>${esc(d.label)}: ${esc(opt.vfmt ? opt.vfmt(d.value) : sig(d.value))}${d.note ? ' · ' + esc(d.note) : ''}</title></rect>`;
      if (opt.labels !== false) s += `<text x="${sx(d.value) + (d.value >= 0 ? 4 : -4)}" y="${y + rowH / 2 + 4}" text-anchor="${d.value >= 0 ? 'start' : 'end'}" class="vl">${esc(opt.vfmt ? opt.vfmt(d.value) : sig(d.value, 3))}</text>`;
    });
    s += `<line x1="${sx(0)}" x2="${sx(0)}" y1="${P.t}" y2="${H - P.b}" stroke="${C.ink}" stroke-width="1.5"/>`;
    return s + '</svg>' + dataDetails(['Category', 'Value'], data.map(d => [d.label, fmtv(opt, d.value) + (d.note ? ' · ' + d.note : '')]));
  }
  const W = opt.w || fitW(760), H = opt.h || 260, P = {l: 56, r: 12, t: 12, b: opt.xlabel ? 46 : 34}, n = data.length;
  const max = opt.max ?? (Math.max(...data.map(d => d.value), 0) * 1.05 || 1);
  const {sy, g} = frame(W, H, P, 0, 1, 0, max, opt); const bw = (W - P.l - P.r) / n;
  let s = svgOpen(W, H, opt.label) + g;
  data.forEach((d, i) => {
    const h = H - P.b - sy(d.value);
    s += `<rect x="${P.l + i * bw + bw * .1}" y="${sy(d.value)}" width="${Math.max(bw * .8, 1)}" height="${Math.max(h, 0)}" fill="${d.color || C.blue}" stroke="${C.ink}" stroke-width="${bw > 8 ? 1 : 0}"><title>${esc(d.label)}: ${esc(opt.vfmt ? opt.vfmt(d.value) : sig(d.value))}${d.note ? ' · ' + esc(d.note) : ''}</title></rect>`;
    const every = Math.ceil(n / Math.max(3, Math.round((opt.xt || 14) * Math.min(1, W / 760))));
    if (i % every === 0) s += `<text x="${P.l + i * bw + bw / 2}" y="${H - P.b + 14}" text-anchor="middle">${esc(d.label)}</text>`;
  });
  return s + '</svg>' + dataDetails(['Category', 'Value'], data.map(d => [d.label, fmtv(opt, d.value) + (d.note ? ' · ' + d.note : '')]));
}
export function grouped(categories, series, opt = {}) {   // series: [{name, color, values[]}]
  const W = opt.w || fitW(760), Hb = opt.h || 260, bw0 = (W - 68) / categories.length, rot = bw0 < Math.max(...categories.map(c => String(c).length)) * 6.3;
  const H = Hb + (rot ? 34 : 0), P = {l: 56, r: 12, t: 12, b: (opt.xlabel ? 46 : 34) + (rot ? 34 : 0)};
  const max = opt.max ?? (Math.max(...series.flatMap(s => s.values), 0) * 1.08 || 1);
  const {sy, g} = frame(W, H, P, 0, 1, 0, max, opt), bw = (W - P.l - P.r) / categories.length, inner = bw * .8 / series.length;
  let s = svgOpen(W, H, opt.label) + g;
  categories.forEach((c, i) => {
    series.forEach((se, j) => {
      const v = se.values[i] ?? 0;
      s += `<rect x="${P.l + i * bw + bw * .1 + j * inner}" y="${sy(v)}" width="${Math.max(inner - 1, 1)}" height="${Math.max(H - P.b - sy(v), 0)}" fill="${se.color}" stroke="${C.ink}" stroke-width="1"><title>${esc(c)} · ${esc(se.name)}: ${esc(opt.vfmt ? opt.vfmt(v) : sig(v))}</title></rect>`;
    });
    const tx = P.l + i * bw + bw / 2, ty = H - P.b + 14;
    s += rot ? `<text x="${tx}" y="${ty}" text-anchor="end" transform="rotate(-40 ${tx} ${ty})">${esc(c)}</text>` : `<text x="${tx}" y="${ty}" text-anchor="middle">${esc(c)}</text>`;
  });
  return s + '</svg>' + legend(series) + dataDetails(['Category', ...series.map(x => x.name)], categories.map((c, i) => [c, ...series.map(x => fmtv(opt, x.values[i] ?? 0))]));
}
export function lines(x, series, opt = {}) {   // series: [{name, color, values[], dash?, points?}]
  const W = opt.w || fitW(760), H = opt.h || 260, P = {l: 58, r: 14, t: 12, b: opt.xlabel ? 46 : 34};
  const ys = series.flatMap(s => s.values.filter(v => v != null && isFinite(v)));
  if (!ys.length) return '<div class="empty">No data in the current selection.</div>';
  let y0 = opt.ymin ?? Math.min(...ys), y1 = opt.ymax ?? Math.max(...ys); if (opt.zero !== false && opt.ymin == null) y0 = Math.min(0, y0);
  if (y1 === y0) y1 = y0 + 1; y1 += (y1 - y0) * .05;
  const xs = x.map((v, i) => typeof v === 'number' && opt.numericX ? v : i), x0 = Math.min(...xs), x1 = Math.max(...xs);
  const {sx, sy, g} = frame(W, H, P, x0, x1, y0, y1, opt);
  let s = svgOpen(W, H, opt.label) + g;
  const every = Math.ceil(x.length / Math.max(3, Math.round((opt.xt || 12) * Math.min(1, W / 760))));
  x.forEach((v, i) => { if (i % every === 0) s += `<text x="${sx(xs[i])}" y="${H - P.b + 14}" text-anchor="middle">${esc(opt.xfmt ? opt.xfmt(v) : v)}</text>`; });
  for (const se of series) {
    const pts = se.values.map((v, i) => v == null || !isFinite(v) ? null : `${sx(xs[i]).toFixed(1)},${sy(v).toFixed(1)}`);
    let d = '', pen = false; pts.forEach(p => { if (p) { d += (pen ? 'L' : 'M') + p; pen = true; } else pen = false; });
    s += `<path d="${d}" fill="none" stroke="${se.color}" stroke-width="${se.width || 2.4}"${se.dash ? ' stroke-dasharray="6 4"' : ''}/>`;
    if (se.points) se.values.forEach((v, i) => { if (v != null && isFinite(v)) s += `<circle cx="${sx(xs[i])}" cy="${sy(v)}" r="3.2" fill="${se.color}" stroke="${C.ink}" stroke-width=".8"><title>${esc(se.name)} · ${esc(x[i])}: ${esc(opt.vfmt ? opt.vfmt(v) : sig(v))}</title></circle>`; });
  }
  return s + '</svg>' + (series.length > 1 || opt.legend ? legend(series) : '') + dataDetails([opt.xlabel || 'x', ...series.map(x => x.name)], x.map((v, i) => [opt.xfmt ? opt.xfmt(v) : v, ...series.map(se => se.values[i] == null ? '—' : fmtv(opt, se.values[i]))]));
}
export function distCompare(edges, series, opt = {}) {   // binned distributions → share per bin (step) or ECDF
  const norm = series.map(s => { const t = s.counts.reduce((a, b) => a + b, 0) || 1; let c = 0; return {...s, share: s.counts.map(v => v / t), cdf: s.counts.map(v => (c += v) / t)}; });
  const labels = edges.slice(0, -1).map((e, i) => opt.binLabel ? opt.binLabel(e, edges[i + 1]) : e);
  return lines(labels, norm.map(s => ({name: s.name, color: s.color, dash: s.dash, values: opt.ecdf ? s.cdf : s.share, points: !opt.ecdf})),
    {...opt, yfmt: v => (100 * v).toFixed(opt.ecdf ? 0 : 1) + '%', vfmt: v => (100 * v).toFixed(2) + '%', ymin: 0, ymax: opt.ecdf ? 1 : undefined, legend: true});
}
export function heatmap(rows, cols, values, opt = {}) {
  const cw = opt.cw || 46, rh = opt.rh || 24, L = opt.left || 120, T = opt.top || 60, W = L + cw * cols.length + 10, H = T + rh * rows.length + 10;
  const flat = values.flat().filter(v => v != null), max = opt.max ?? Math.max(...flat, 1e-9);
  const col = v => { if (v == null) return '#fff'; const t = Math.min(v / max, 1); return t < .5 ? mix('#ffffff', C.yellow, t * 2) : mix(C.yellow, C.blue, (t - .5) * 2); };
  let s = `<div class="hscroll" tabindex="0" aria-label="Scrollable matrix"><svg viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(opt.label || 'matrix')}" style="width:${W}px;max-width:none;max-height:none">`;
  cols.forEach((c, j) => s += `<text x="${L + j * cw + cw / 2}" y="${T - 8}" text-anchor="end" transform="rotate(-45 ${L + j * cw + cw / 2} ${T - 8})">${esc(c)}</text>`);
  rows.forEach((r, i) => { s += `<text x="${L - 6}" y="${T + i * rh + rh / 2 + 4}" text-anchor="end">${esc(r)}</text>`;
    cols.forEach((c, j) => { const v = values[i][j]; s += `<rect x="${L + j * cw}" y="${T + i * rh}" width="${cw - 1}" height="${rh - 1}" fill="${col(v)}"><title>${esc(r)} × ${esc(c)}: ${esc(opt.vfmt ? opt.vfmt(v) : sig(v))}</title></rect>`;
      if (opt.text && v != null) s += `<text x="${L + j * cw + cw / 2}" y="${T + i * rh + rh / 2 + 4}" text-anchor="middle" class="vl">${esc(opt.vfmt ? opt.vfmt(v) : sig(v, 2))}</text>`; }); });
  return s + '</svg></div>';
}
function mix(a, b, t) {
  const p = h => [1, 3, 5].map(i => parseInt(h.slice(i, i + 2), 16)), A = p(a), B = p(b);
  return '#' + A.map((v, i) => Math.round(v + (B[i] - v) * t).toString(16).padStart(2, '0')).join('');
}
export function scatter(points, opt = {}) {   // points: [{x, y, label?}]
  const W = opt.w || fitW(640), H = opt.h || 300, P = {l: 60, r: 14, t: 12, b: 44};
  const tx = v => opt.logX ? Math.log10(v) : v, ty = v => opt.logY ? Math.log10(v) : v;
  const X = points.map(p => tx(p.x)), Y = points.map(p => ty(p.y));
  const x0 = opt.xmin ?? Math.min(...X), x1 = opt.xmax ?? Math.max(...X), y0 = opt.ymin ?? Math.min(...Y), y1 = opt.ymax ?? Math.max(...Y);
  const {sx, sy, g} = frame(W, H, P, x0, x1, y0, y1, {...opt, yfmt: opt.logY ? (v => tickFmt(10 ** v)) : opt.yfmt});
  let s = svgOpen(W, H, opt.label) + g;
  for (const t of niceTicks(x0, x1, 5)) s += `<text x="${sx(t)}" y="${H - P.b + 14}" text-anchor="middle">${opt.logX ? tickFmt(10 ** t) : tickFmt(t)}</text>`;
  if (opt.diag) s += `<line x1="${sx(Math.max(x0, y0))}" y1="${sy(Math.max(x0, y0))}" x2="${sx(Math.min(x1, y1))}" y2="${sy(Math.min(x1, y1))}" stroke="${C.coral}" stroke-width="2" stroke-dasharray="6 4"/>`;
  points.forEach((p, i) => s += `<circle cx="${sx(X[i])}" cy="${sy(Y[i])}" r="${opt.r || 2.6}" fill="${p.color || C.blue}" fill-opacity="${opt.alpha ?? .55}"><title>${esc(p.label || '')} (${sig(p.x)}, ${sig(p.y)})</title></circle>`);
  return s + '</svg>';
}

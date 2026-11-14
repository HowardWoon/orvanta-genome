// Explorer cube engine: exact re-aggregation of additive cells and honest comparison statistics.
import {data} from './core.js';

let CUBE = null;
export async function cube() {
  if (CUBE) return CUBE;
  const raw = await data('explorer');
  const ix = Object.fromEntries(raw.cols.map((c, i) => [c, i]));
  const values = Object.fromEntries(raw.dims.map(d => [d, [...new Set(raw.rows.map(r => String(r[ix[d]])))].sort((a, b) => isNaN(a) ? a.localeCompare(b) : a - b)]));
  CUBE = {...raw, ix, values};
  return CUBE;
}
// filter: {dim: Set(values)} — dims absent or with an empty Set... absent = all; empty Set = nothing
export function aggregate(cb, filter) {
  const {ix, rows, nab, ndb, dims} = cb, a = {n: 0, s1: 0, s2: 0, sd: 0, ah: new Array(nab).fill(0), dh: new Array(ndb).fill(0), manual: 0};
  const active = dims.filter(d => filter[d]);
  for (const r of rows) {
    let ok = true;
    for (const d of active) if (!filter[d].has(String(r[ix[d]]))) { ok = false; break; }
    if (!ok) continue;
    const n = r[ix.n]; a.n += n; a.s1 += r[ix.s1]; a.s2 += r[ix.s2]; a.sd += r[ix.sd];
    if (r[ix.manual] === 1) a.manual += n;
    for (let k = 0; k < nab; k++) a.ah[k] += r[ix['a' + k]];
    for (let k = 0; k < ndb; k++) a.dh[k] += r[ix['d' + k]];
  }
  return a;
}
export function breakdown(cb, filter, dim) {   // counts per value of dim within filter
  const {ix, rows, dims} = cb, out = {}, active = dims.filter(d => filter[d] && d !== dim);
  for (const r of rows) {
    let ok = true; for (const d of active) if (!filter[d].has(String(r[ix[d]]))) { ok = false; break; }
    if (ok && (!filter[dim] || filter[dim].has(String(r[ix[dim]])))) { const k = String(r[ix[dim]]); out[k] = (out[k] || 0) + r[ix.n]; }
  }
  return out;
}
// quantile from a histogram whose bins are [edges[i], edges[i+1]) in a transformed scale; linear interpolation inside the bin
export function histQuantile(counts, edges, q) {
  const tot = counts.reduce((x, y) => x + y, 0); if (!tot) return null;
  let c = 0;
  for (let i = 0; i < counts.length; i++) { if (c + counts[i] >= q * tot) { const f = counts[i] ? (q * tot - c) / counts[i] : 0; return edges[i] + f * (edges[i + 1] - edges[i]); } c += counts[i]; }
  return edges[edges.length - 1];
}
export function summary(cb, a) {
  if (!a.n) return null;
  const mean = a.s1 / a.n, sd = Math.sqrt(Math.max(a.s2 / a.n - mean * mean, 0));
  const dEdges = [...cb.dur_edges, cb.dur_edges[cb.dur_edges.length - 1] + 1];
  return {n: a.n, meanLn: mean, sdLn: sd, geo: Math.exp(mean), medAmt: 10 ** histQuantile(a.ah, cb.amt_edges, .5),
          p10Amt: 10 ** histQuantile(a.ah, cb.amt_edges, .1), p90Amt: 10 ** histQuantile(a.ah, cb.amt_edges, .9),
          meanDur: a.sd / a.n, medDur: 2 ** histQuantile(a.dh, dEdges, .5), manual: a.manual / a.n};
}
const ks = (h1, h2) => { const t1 = h1.reduce((a, b) => a + b, 0), t2 = h2.reduce((a, b) => a + b, 0); let c1 = 0, c2 = 0, m = 0; for (let i = 0; i < h1.length; i++) { c1 += h1[i] / t1; c2 += h2[i] / t2; m = Math.max(m, Math.abs(c1 - c2)); } return m; };
export function compare(cb, A, B) {   // A = selection, B = comparison group
  const sa = summary(cb, A), sb = summary(cb, B); if (!sa || !sb) return null;
  const diff = sa.meanLn - sb.meanLn, se = Math.sqrt(sa.sdLn ** 2 / sa.n + sb.sdLn ** 2 / sb.n);
  const pooled = Math.sqrt(((sa.n - 1) * sa.sdLn ** 2 + (sb.n - 1) * sb.sdLn ** 2) / (sa.n + sb.n - 2));
  const pd = sa.manual - sb.manual, sep = Math.sqrt(sa.manual * (1 - sa.manual) / sa.n + sb.manual * (1 - sb.manual) / sb.n);
  return {sa, sb, lnDiff: diff, lnCI: [diff - 1.96 * se, diff + 1.96 * se], ratio: Math.exp(diff), ratioCI: [Math.exp(diff - 1.96 * se), Math.exp(diff + 1.96 * se)],
          cohenD: pooled ? diff / pooled : null, ksAmt: ks(A.ah, B.ah), ksDur: ks(A.dh, B.dh), manualDiff: pd, manualCI: [pd - 1.96 * sep, pd + 1.96 * sep]};
}
export const dLabel = d => d == null ? '—' : Math.abs(d) < .2 ? 'negligible' : Math.abs(d) < .5 ? 'small' : Math.abs(d) < .8 ? 'medium' : 'large';
export const ksLabel = k => k < .05 ? 'negligible' : k < .15 ? 'small' : k < .3 ? 'moderate' : 'large';

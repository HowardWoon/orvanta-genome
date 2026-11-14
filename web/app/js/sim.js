// Monte-Carlo implementation of the RECONSTRUCTED generator (rules R1, R2, R4, A1, A2, D1, D3).
// Every parameter comes from data/sim.json (estimated from the dataset). Outputs are MODEL SIMULATIONS, never observations.
export function rng(seed = 2026) {   // mulberry32 — seeded so results are reproducible
  let a = seed >>> 0;
  return () => { a = (a + 0x6D2B79F5) >>> 0; let t = a; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
}
export const normal = r => { let u = 0, v = 0; while (u === 0) u = r(); while (v === 0) v = r(); return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v); };
export function gamma(r, k, theta) {   // Marsaglia–Tsang (k ≥ 1); boost for k < 1
  if (k < 1) return gamma(r, k + 1, theta) * Math.pow(r(), 1 / k);
  const d = k - 1 / 3, c = 1 / Math.sqrt(9 * d);
  for (;;) { let x, v; do { x = normal(r); v = 1 + c * x; } while (v <= 0); v = v * v * v; const u = r();
    if (u < 1 - .0331 * x ** 4 || Math.log(u) < .5 * x * x + d * (1 - v + Math.log(v))) return d * v * theta; }
}
const binIdx = (v, edges) => { for (let i = edges.length - 2; i >= 0; i--) if (v >= edges[i]) return i; return 0; };

// Duration (D1 + D3): each of pc participating banks contributes a fast step (Gamma) or, with probability m, a manual step (Gamma).
export function simDuration(P, {pc, m, draws = 60000, seed = 1, batches = 5}, durEdges) {
  const counts = new Array(durEdges.length).fill(0), meds = [], manual = [];
  const per = Math.floor(draws / batches);
  for (let b = 0; b < batches; b++) {
    const r = rng(seed * 101 + b), xs = new Float64Array(per); let man = 0;
    for (let i = 0; i < per; i++) {
      let t = 0, anyManual = false;
      for (let j = 0; j < pc; j++) { if (r() < m) { t += gamma(r, P.manual_shape, P.manual_scale); anyManual = true; } else t += gamma(r, P.fast_shape, P.fast_scale); }
      t = Math.max(2, Math.round(t)); xs[i] = t; if (t > 120) man++;
      counts[binIdx(Math.min(Math.max(Math.floor(Math.log2(t)), 1), 15) - 1, durEdges.map((_, k) => k))] += 1;
    }
    xs.sort(); meds.push(xs[Math.floor(per / 2)]); manual.push(man / per);
  }
  return {counts, median: mean(meds), medianSE: sdev(meds) / Math.sqrt(batches), manual: mean(manual), manualSE: sdev(manual) / Math.sqrt(batches), draws: per * batches};
}
// Amount (A1 + A2): ln(USD amount) = 6 + 2·[sender=B] + 2·[receiver=B] + country effect + N(0, sd²)
// Same structural model as stats.py (its implied exceedance counts match observation within 0.4% at $100k). Country effects are
// avg residual vs the 6+2+2 baseline per sender-bank country (n ≥ 20,000); "ALL" draws countries in proportion to their volume.
export function simAmount(P, {stype, rtype, country, sdScale = 1, draws = 60000, seed = 2, batches = 5}, amtEdges) {
  const counts = new Array(amtEdges.length - 1).fill(0), means = [];
  const cs = P.country, tot = cs.reduce((a, c) => a + c.n, 0), cum = []; let acc = 0; for (const c of cs) { acc += c.n / tot; cum.push(acc); }
  const per = Math.floor(draws / batches), sd = P.sd_noise * sdScale;
  for (let b = 0; b < batches; b++) {
    const r = rng(seed * 97 + b); let s = 0;
    for (let i = 0; i < per; i++) {
      let ce;
      if (country === 'ALL') { const u = r(); let k = cum.findIndex(c => c >= u); if (k < 0) k = cs.length - 1; ce = cs[k].eff; } else ce = cs.find(c => c.cc === country)?.eff ?? 0;
      const ln = 6 + 2 * (stype === 'B') + 2 * (rtype === 'B') + ce + sd * normal(r);
      s += ln; const l10 = ln / Math.LN10; counts[Math.min(Math.max(Math.floor((l10 - amtEdges[0]) / .5), 0), counts.length - 1)]++;
    }
    means.push(s / per);
  }
  const m = mean(means);
  return {counts, meanLn: m, geo: Math.exp(m), geoSE: Math.exp(m) * sdev(means) / Math.sqrt(batches), draws: per * batches};
}
// Route (R1 + R2 + R4): K ~ Geometric(q) intermediaries (pc = K + 2, Direct ⇔ K = 0); a non-direct payment is Covered with the cover share
// of its instructing bank's class (R2: cover-prone vs other, estimated out of sample); each of the pc − 1 links is hidden independently w.p. pLink (R4).
// w = share of non-direct payments instructed by cover-prone banks. Default w reproduces the pooled cover share exactly.
export const defaultW = P => (P.pooled_cover - P.cover_share_other) / (P.cover_share_cover_banks - P.cover_share_other);
export function simRoute(P, {q, pLink, w, draws = 100000, seed = 3}) {
  const r = rng(seed), pcCounts = {}, gapCounts = {}; let direct = 0, covered = 0, gap = 0;
  for (let i = 0; i < draws; i++) {
    let K = 0; while (r() < q && K < 40) K++;
    const pc = K + 2; pcCounts[pc] = (pcCounts[pc] || 0) + 1;
    if (K === 0) direct++; else if (r() < (r() < w ? P.cover_share_cover_banks : P.cover_share_other)) covered++;
    let h = 0; for (let j = 0; j < pc - 1; j++) if (r() < pLink) h++;
    if (h) gap++; gapCounts[h] = (gapCounts[h] || 0) + 1;
  }
  return {pcCounts, gapCounts, direct: direct / draws, covered: covered / Math.max(draws - direct, 1), gap: gap / draws, draws};
}
const mean = a => a.reduce((x, y) => x + y, 0) / a.length;
const sdev = a => { const m = mean(a); return Math.sqrt(a.reduce((x, y) => x + (y - m) ** 2, 0) / Math.max(a.length - 1, 1)); };

// JavaScript port of src/rulelib.py (the pure-Python reference rules). Same names, same semantics; tests/test_web_e2e.py checks parity.
export const GAP = '...';
export const knownBics = path => path.split(';').map(s => s.trim()).filter(b => b && b !== GAP);
export const bicCountry = bic8 => bic8.slice(4, 6);
export const participantCount = path => knownBics(path).length;                                   // R6
export const continuityFlag = path => path.split(';').map(s => s.trim()).includes(GAP) ? 'N' : 'Y'; // R7
export function fxCount(path, homeCcy) {                                                           // C2
  const cl = knownBics(path).map(b => homeCcy[bicCountry(b)]);
  let n = 0; for (let i = 1; i < cl.length; i++) if (cl[i] !== cl[i - 1]) n++; return n;
}
export const hopPmf = (k, q = Math.exp(-1)) => (1 - q) * q ** k;                                    // R1
export const pGap = (pc, pLink = 0.05) => 1 - (1 - pLink) ** (pc - 1);                             // R4
export const logAmountMean = (otype, btype, ce = 0) => 6 + 2 * (otype === 'B') + 2 * (btype === 'B') + ce;   // A1/A2
export const isIbanCountryConsistent = (account, bic8) => account.replace('_FAKE_', '').slice(0, 2) === bicCountry(bic8); // P2
export function mt4x35ok(details) {                                                                // P3 / P1b
  const lines = details.split('\n'); const body = lines.length && lines[0].startsWith('/') ? lines.slice(1) : lines;
  return body.length <= 4 && body.every(x => x.length <= 35);
}
export function romanceLike(series, maxSpan = 4200, minN = 3) {                                    // X1 detector
  if (series.length < minN) return false;
  const ts = series.map(s => s[0]); if (Math.max(...ts) - Math.min(...ts) > maxSpan) return false;
  const ys = series.map(s => Math.log(s[1])), mx = ts.reduce((a, b) => a + b, 0) / ts.length, my = ys.reduce((a, b) => a + b, 0) / ys.length;
  let sxy = 0, sxx = 0, syy = 0; ts.forEach((x, i) => { sxy += (x - mx) * (ys[i] - my); sxx += (x - mx) ** 2; syy += (ys[i] - my) ** 2; });
  return sxx > 0 && syy > 0 && sxy / Math.sqrt(sxx * syy) > 0.5;
}

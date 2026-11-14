// Synthetic Rule Playground: build a payment by hand and watch the reconstructed rules derive its fields.
import {data, esc, fmt, pct, sig, usd, header, badge, tag, table, select} from '../core.js';
import * as RL from '../rulelib.js';

const DEFAULT = {path: '0309CHZ0;1022DEA1;...;0004IMD0', ccy: 'CH:CHF,DE:EUR,IM:GBP,US:USD', o: 'B', b: 'C', acct: 'IM29EXAMPLE00000000001', det: '/IM29EXAMPLE00000000001\nACME TRADING LTD\n12 HARBOUR ROAD\nDOUGLAS', ser: '0:120,900:450,2100:1800,3600:5200'};

export async function render(el, ctx) {
  const [S, reg] = await Promise.all([data('sim'), data('registry')]);
  const known = new Set(reg.rules.map(r => r.id));
  const P = {...DEFAULT, ...ctx.params};
  const cs = [...S.amount.country].sort((a, b) => a.cc.localeCompare(b.cc));
  el.innerHTML = header('Interactive research lab', 'Synthetic rule playground',
    'Type a payment the way the generator would see it. The panel on the right runs the reconstructed rules — a JavaScript port of the reference library <code>src/rulelib.py</code> — and shows which fields they force and which they only make likely.') +
    badge('VALIDATED RULE') + badge('CONDITIONAL ESTIMATE') +
    `<div class="note">BIC codes here are synthetic placeholders in the dataset's format (4 bank chars · 2 country · 2 location). Use <code>...</code> for a hidden hop. Nothing typed here is sent anywhere.</div>
    <div class="split"><div class="card">
      <label class="ctl">BIC8 path (sender ; intermediaries ; receiver)<input type="text" id="pp" value="${esc(P.path)}" style="width:100%;font-family:var(--mono)"></label>
      <label class="ctl" style="margin-top:10px">Home currency per country (CC:CUR, comma separated)<input type="text" id="pc" value="${esc(P.ccy)}" style="width:100%;font-family:var(--mono)"></label>
      <div class="controls">${select('po', 'Sender type', [['B', 'business'], ['C', 'consumer']], P.o)}${select('pb', 'Receiver type', [['B', 'business'], ['C', 'consumer']], P.b)}
        ${select('pk', 'Sender-bank country effect (A2)', [['', 'auto from first BIC'], ...cs.map(c => [c.cc, `${c.cc} ${c.eff >= 0 ? '+' : ''}${c.eff.toFixed(2)}`])], P.k || '')}</div>
      <label class="ctl">Receiver account<input type="text" id="pa" value="${esc(P.acct)}" style="width:100%;font-family:var(--mono)"></label>
      <label class="ctl" style="margin-top:10px">Receiver details (free text)<textarea id="pd" rows="5" style="width:100%;font-family:var(--mono);border:2px solid var(--ink);padding:6px">${esc(P.det)}</textarea></label>
      <label class="ctl" style="margin-top:10px">Payment series for the romance detector (seconds:USD, …)<input type="text" id="ps" value="${esc(P.ser)}" style="width:100%;font-family:var(--mono)"></label>
      <div class="controls"><button class="sec" id="preset">Reset example</button><button class="sec" id="pdirect">Direct example</button><button class="sec" id="pbad">Broken example</button></div>
    </div><div id="pout"></div></div>`;
  const $ = id => el.querySelector('#' + id);
  const draw = () => {
    const path = $('pp').value, homes = Object.fromEntries($('pc').value.split(',').map(x => x.split(':').map(s => s.trim())).filter(x => x.length === 2 && x[0]));
    const bics = RL.knownBics(path), bad = bics.filter(b => !/^[A-Z0-9]{4}[A-Z]{2}[A-Z0-9]{2}$/.test(b));
    const pc = RL.participantCount(path), cont = RL.continuityFlag(path), missing = [...new Set(bics.map(RL.bicCountry).filter(c => !homes[c]))];
    const fx = missing.length ? null : RL.fxCount(path, homes);
    const sender = bics[0] || '', receiver = bics[bics.length - 1] || '';
    const ccSel = $('pk').value || RL.bicCountry(sender), ce = cs.find(c => c.cc === ccSel);
    const mu = RL.logAmountMean($('po').value, $('pb').value, ce?.eff ?? 0);
    const ser = $('ps').value.split(',').map(x => x.split(':').map(Number)).filter(x => x.length === 2 && x.every(Number.isFinite) && x[1] > 0);
    const acct = $('pa').value, ibanLike = /^[A-Z]{2}\d{2}/.test(acct), det = $('pd').value;
    const q = S.route.q, pl = S.route.p_link, hops = Math.max(pc - 2, 0);
    const rows = [
      {rule: 'R6', field: 'PARTICIPANT_COUNT', out: pc < 2 ? `${pc} — a valid path has ≥ 2 known BICs` : String(pc), kind: 'deterministic'},
      {rule: 'R7', field: 'CONTINUITY_QFLAG', out: cont, kind: 'deterministic'},
      {rule: 'C2', field: 'CURRENCY_CONVERSION_COUNT', out: fx == null ? `needs a home currency for ${missing.join(', ')}` : String(fx), kind: 'deterministic'},
      {rule: 'R1', field: 'TRANSACTION_TYPE_CODE', out: pc === 2 ? 'Direct (forced: pc = 2)' : pc > 2 ? 'Covered or Indirect (not Direct)' : '—', kind: 'deterministic'},
      {rule: 'R1', field: 'P(this many intermediaries)', out: pc >= 2 ? pct(RL.hopPmf(hops, q), 3) : '—', kind: 'probability'},
      {rule: 'R4', field: 'P(path shows ≥ 1 hidden hop)', out: pc >= 2 ? pct(RL.pGap(pc, pl), 2) : '—', kind: 'probability'},
      {rule: 'A1·A2', field: 'E[ln USD_AMOUNT]', out: `${mu.toFixed(2)} → typical ${usd(Math.exp(mu))}; 95% band ${usd(Math.exp(mu - 1.96 * S.amount.sd_noise))} – ${usd(Math.exp(mu + 1.96 * S.amount.sd_noise))}${ce ? '' : ' (no country effect: country outside the fitted set)'}`, kind: 'expectation'},
      {rule: 'P2', field: 'Account vs receiver BIC', out: !ibanLike ? 'not IBAN-formatted — fine only if the bank country does not use IBANs' : RL.isIbanCountryConsistent(acct, receiver) ? `consistent (${acct.slice(0, 2)} = ${RL.bicCountry(receiver)})` : `violates P2: IBAN prefix ${acct.slice(0, 2)} ≠ BIC country ${RL.bicCountry(receiver)}`, kind: 'deterministic'},
      {rule: 'P3', field: 'Details fit the 4×35 MT layout', out: RL.mt4x35ok(det) ? 'yes' : 'no — more than 4 body lines or a line over 35 characters', kind: 'deterministic'},
      {rule: 'X1', field: 'Romance-scam detector on the series', out: ser.length < 3 ? 'needs ≥ 3 payments' : RL.romanceLike(ser) ? 'flagged (≥ 3 payments within 70 min, amounts rising)' : 'not flagged', kind: 'detector'},
    ];
    $('pout').innerHTML = (bad.length ? `<div class="empty">Not BIC8-shaped: ${bad.map(esc).join(', ')}. Expected 4 alphanumerics + 2-letter country + 2 alphanumerics.</div>` : '') +
      `<div class="card ink"><div class="mono">Sender ${esc(sender || '—')} · receiver ${esc(receiver || '—')} · ${pc} known BICs${cont === 'N' ? ' · hidden hop present' : ''}</div></div>` +
      table(rows, [{key: 'rule', label: 'Rule', f: v => v.split('·').map(id => known.has(id.trim()) ? `<a href="#/rules/explorer?id=${esc(id.trim())}">${esc(id.trim())}</a>` : `<span title="reference-library rule (src/rulelib.py)">${esc(id.trim())}</span>`).join('·')}, {key: 'field', label: 'Field'}, {key: 'out', label: 'Derived'},
        {key: 'kind', label: 'Kind', f: v => tag(v, v === 'deterministic' ? 'lv-val' : v === 'detector' ? 'warn' : 'info')}]) +
      `<div class="note">Deterministic rows are forced by the reconstructed generator (validated on all 10M rows). Probability and expectation rows use parameters estimated from the data (q = ${q.toFixed(4)}, p = ${pl.toFixed(4)}, residual sd ${S.amount.sd_noise.toFixed(2)}); the generator draws the actual value.</div>`;
    ctx.setParams({path, ccy: $('pc').value, o: $('po').value, b: $('pb').value, k: $('pk').value, acct, det, ser: $('ps').value});
  };
  const set = v => { $('pp').value = v.path; $('pc').value = v.ccy; $('po').value = v.o; $('pb').value = v.b; $('pa').value = v.acct; $('pd').value = v.det; $('ps').value = v.ser; $('pk').value = ''; draw(); };
  el.querySelectorAll('input,select,textarea').forEach(x => x.addEventListener('input', draw));
  $('preset').onclick = () => set(DEFAULT);
  $('pdirect').onclick = () => set({...DEFAULT, path: '0450USA1;0812USB3', ccy: 'US:USD', o: 'C', b: 'C', acct: '000123456789', det: 'JANE DOE\n5 MAIN ST', ser: '0:50,86400:60'});
  $('pbad').onclick = () => set({...DEFAULT, path: '0309CHZ0;BAD;0004IMD0', acct: 'DE89EXAMPLE00000000001', det: 'A VERY LONG COMPANY NAME THAT EXCEEDS THE LIMIT\n1\n2\n3\n4'});
  draw();
}

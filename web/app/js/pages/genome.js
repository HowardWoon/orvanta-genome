// Generator Genome: the reconstructed blueprint (by generation stage) and the recorded genealogy of each rule.
import {data, esc, header, badge, level, select, tag} from '../core.js';
import {md} from './method.js';

export async function render(el, ctx) {
  const [G, reg, L] = await Promise.all([data('genome'), data('registry'), data('ledger')]);
  return ctx.sub === 'genealogy' ? genealogy(el, G, reg, L, ctx) : blueprint(el, G, reg, ctx);
}

function blueprint(el, G, reg, ctx) {
  const lv = ctx.params.level || 'ALL';
  el.innerHTML = header('Generator genome', 'Generator blueprint',
    'The reconstructed generator, written as the sequence of decisions it appears to make for each payment. Only mechanisms backed by a validated rule appear; anything we could not pin down is listed as unresolved, not filled in.') +
    badge('VALIDATED RULE') + badge('STRUCTURAL SCENARIO') +
    `<div class="controls">${select('bl', 'Show mechanisms at level', [['ALL', 'All levels'], 'VALIDATED', 'STRONGLY SUPPORTED', 'SUPPORTED', 'INCONCLUSIVE'], lv)}<a class="tag" href="#/rules/atlas">Open as dependency graph →</a></div><div id="bo"></div>`;
  const draw = () => {
    const v = el.querySelector('#bl').value; ctx.setParams({level: v === 'ALL' ? '' : v});
    el.querySelector('#bo').innerHTML = G.blueprint.map((s, i) => {
      const ms = s.mechanisms.filter(m => v === 'ALL' || m.level === v);
      return `<details class="fold" open><summary>${String(i + 1).padStart(2, '0')} · ${esc(s.section)} <span class="mono" style="font-weight:400">— ${esc(s.covers)}</span></summary><div>
        ${ms.length ? ms.map(m => `<div style="margin:8px 0">${level(m.level)}<a href="#/rules/explorer?id=${m.rule}"><b>${m.rule}</b></a><div class="formula">${esc(m.statement)}</div></div>`).join('') : '<div class="mono">No mechanism at this level.</div>'}
        ${s.note ? `<div class="note">${esc(s.note)}</div>` : ''}
        ${s.unresolved.length ? `<div class="note red"><b>Unresolved / partly inferred</b><ul>${s.unresolved.map(u => `<li><b>${u.rule}</b>: ${esc(u.text)}</li>`).join('')}</ul></div>` : ''}</div></details>`;
    }).join('');
  };
  el.querySelector('#bl').addEventListener('change', draw); draw();
}

function genealogy(el, G, reg, L, ctx) {
  const ids = G.genealogy.map(g => g.rule), id = ids.includes(ctx.params.id) ? ctx.params.id : 'R2';
  el.innerHTML = header('Generator genome', 'Rule genealogy',
    'How each rule was reached: the hypotheses we logged in the order we tested them, what each test showed, the alternative that lost, the counterexamples that remain and the final validation. Built only from the recorded hypothesis log (H1–H37) — rules without a logged history say so.') +
    `<div class="controls">${select('gr', 'Rule', G.genealogy.map(g => [g.rule, `${g.rule} · ${g.title.slice(0, 70)}${g.recorded ? '' : ' (no logged history)'}`]), id)}</div><div id="go"></div>`;
  const draw = () => {
    const g = G.genealogy.find(x => x.rule === el.querySelector('#gr').value); ctx.setParams({id: g.rule});
    const evs = L.entries.filter(e => e.rules.includes(g.rule)).slice(0, 12);
    const cls = o => /accepted|\*\*pc|exact|fits better|→ \*\*/i.test(o) && !/^rejected/i.test(o) ? 'acc' : /rejected|not supported/i.test(o) ? 'rej' : '';
    el.querySelector('#go').innerHTML = `<div class="card">${level(g.level)}<h2 style="margin:4px 0">${esc(g.rule)} · ${esc(g.title)}</h2></div><div style="margin-top:14px">` +
      (g.hypotheses.length ? g.hypotheses.map((h, i) => `<div class="genestep ${cls(h.outcome)}"><div class="mono">Step ${i + 1} · ${esc(h.id)} · tested by ${esc(h.test)}</div><b>${esc(h.hypothesis)}</b><div>${md(h.outcome).replace(/^<p>|<\/p>$/g, '')}</div><div class="mono">${esc(h.consequence)}</div></div>`).join('')
        : `<div class="empty">No hypothesis in the log points to ${esc(g.rule)}. Its history was not recorded step by step, so none is shown — see the rule's method and alternative below.</div>`) +
      `<div class="genestep"><div class="mono">Best alternative tested</div>${esc(g.alternative || '—')}</div>
       <div class="genestep rej"><div class="mono">Counterexamples that remain</div>${esc(g.counterexamples || '—')}</div>
       <div class="genestep acc"><div class="mono">Final validation</div>${esc(g.validation)}</div></div>
      <h3>Evidence records</h3><div>${evs.map(e => `<a class="tag" href="#/library/ledger?q=${e.id}">${e.id}</a>`).join('')}</div>`;
  };
  el.querySelector('#gr').addEventListener('change', draw); draw();
}

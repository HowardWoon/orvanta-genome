// Research coverage: what has been done for every feature group — not just whether it has charts.
import {data, esc, fmt, header, table, tag, grouped, chartBox, C} from '../core.js';

const SLUG = {'Temporal': 'temporal', 'Currency & Value': 'currency', 'Institution': 'institution', 'Route': 'route', 'Duration & Continuity': 'duration', 'FX & Participant': 'fx',
  'Transaction Type': 'ttype', 'Party Details': 'party', 'Token': 'token', 'Anomaly': 'anomaly'};

export async function render(el) {
  const [G, m] = await Promise.all([data('genome'), data('meta')]);
  const cov = G.coverage, status = c => c.validated + c.strong >= 2 ? ['DEEP', 'lv-val'] : c.rules >= 2 ? ['COVERED', 'lv-sup'] : ['THIN', 'warn'];
  el.innerHTML = header('Intelligence command centre', 'Research coverage',
    `For each of the ${cov.length} feature groups: how many reconstructed rules it has and at which confidence, how many logged hypotheses fed them, how many statistical tests and replayable record checks exist, and what is still open. A group is not "done" because it has charts.`) +
    `<div class="note">All ${m.quality.length} data-quality checks run on every field before any group analysis (Data quality). Rules can serve two groups (e.g. R6 is both Route and FX & participant), so totals across groups exceed 34.</div>` +
    table(cov.map(c => ({...c, st: status(c)})), [{key: 'group', label: 'Feature group', f: (v) => `<a href="#/feature/${SLUG[v]}">${esc(v)}</a>`}, {key: 'st', label: 'Depth', f: v => tag(v[0], v[1])},
      {key: 'rules', label: 'Rules', num: true}, {key: 'validated', label: 'Validated', num: true}, {key: 'strong', label: 'Strongly sup.', num: true}, {key: 'supported', label: 'Supported', num: true},
      {key: 'inconclusive', label: 'Inconclusive', num: true}, {key: 'hypotheses', label: 'Hypotheses', num: true}, {key: 'tests', label: 'Tests', num: true}, {key: 'replay', label: 'Replay checks', num: true},
      {key: 'economic', label: 'Economic readings', num: true}, {key: 'open', label: 'Open questions', f: v => v.length ? v.map(esc).join('<br>') : '—'}]) +
    chartBox('Rules per group by confidence', grouped(cov.map(c => c.group.split(' ')[0]), [{name: 'validated', color: C.blue, values: cov.map(c => c.validated)}, {name: 'strongly supported', color: '#9cc3ef', values: cov.map(c => c.strong)},
      {name: 'supported', color: C.yellow, values: cov.map(c => c.supported)}, {name: 'inconclusive', color: '#d6d1c4', values: cov.map(c => c.inconclusive)}], {label: 'Coverage', vfmt: fmt}),
      'Token is deliberately marked thin: the token fields are engineered summaries and we found no generator rule beyond P1b/P4.');
}

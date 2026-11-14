# Visualisation and data traceability audit (V5)

Every visual on the website classified by the brief's four categories. "Interactive" = rendered in the browser from data files, with values exposed (hover/tap titles + a data table under the chart) and/or controls that recompute it.

| Module | Visual | Category | Data / formula | Controls that recompute it |
|---|---|---|---|---|
| Overview | 3 headline cards, unresolved list | 1 (values from registry) | `registry.json` metrics; each card links to its rule, replay, ledger | — |
| Guided tour | C2 exception table; R1 observed vs theory bars; R2 genealogy; duration scenario table | 1 | registry, replay, meta distributions, sim.json + seeded Monte Carlo | stage navigation |
| Data observatory | distributions, routing/participants/anomaly bars | 1 | `meta.json` distributions (exact counts) | feature + order selectors |
| Payment intelligence (10) | ~30 SVG charts (weekly series, local hour, country effects, R1 fit, G3 loops, R4 rates, D1 classes, Simpson hour, tokens heatmap, anomaly rates …) | 1 | `meta.json`, `temporal.json`, `institutions.json`, `sim.json`, `tokens.json` | temporal daily series: routing type + measure |
| Payment intelligence | PDF figures (PNG) | 3 — static, data-driven | `outputs/charts/*.png` from `src/charts.py` | collapsed under "Static figures used in the PDF", labelled not interactive |
| Generator blueprint | sectioned mechanism list | 2 | `genome.json` (rules by generation stage, unresolved from limitations) | level filter |
| Dependency atlas | SVG graph, 21 nodes / 37 edges | 2 | `meta.json → atlas` (edges typed, each with rules + evidence) | zoom, pan (mouse/touch), node search, up/downstream trace, rule focus, edge-kind filter |
| Feature relationship explorer | Cramér's V matrix; pair table | 1 | `meta.json → discovery` | verdict, feature, min-V filters |
| Rule genealogy | vertical timeline | 2 | `genome.json → genealogy` (logged H-entries only) | rule selector |
| Rule builder | distribution comparison, strata bars, replication table | 1 | explorer cube (exact aggregates of 10M rows) | target, condition, comparison, stratifier, direction, scope |
| Observed data explorer | amount/duration distributions, composition bars | 1 | explorer cube | 10 dimension filters, comparison mode |
| Scenario studio | simulated vs observed bars/distributions | 1 (MODEL SIMULATION) | `sim.json` parameters + seeded Monte Carlo vs cube | sliders/selectors per model; pin/compare/export |
| Sensitivity analysis | model curve, Monte-Carlo points, estimate, selected value, observed line | 1 (MODEL SIMULATION + OBSERVED) | closed forms of R1/R4, Monte Carlo of D1/D3; observed from meta/cube | parameter selector, value slider (recomputes output, slope, scenario flag) |
| Route playground | bars, two scatters | 1 | `routes.json` (n ≥ 150), `institutions.json` | 6 route filters; bank search/sort |
| Anomaly explorer | distributions, breakdown, rule evidence | 1 | cube + `meta.json → evidence/stats` | label, breakdown dimension |
| Forensic replay | record tables | 1 (OBSERVED, de-identified) | `replay.json` exact counts + fixed samples | rule, side, text filter, CSV export |
| Statistical forensics | QQ, Hill, exceedance, ECDF, Benford, cents, uniformity tables, BH test registry | 1 | `meta.json → stats/forensics`, `tests.json`, cube | split dimension/variable; family/significance filters |
| Validation centre | split bars, scorecard | 1 | `registry.json` metrics per split | rule/type selectors |
| Evidence ledger | record list + detail | 1 | `ledger.json` | search, type filter, export |

Decorative illustrations (category 4): none. No random or hard-coded chart values: the chart kit only plots arrays read from the data files or computed from them (closed forms or seeded Monte Carlo with the seed shown).

Numerical checks in the test suite that tie visuals to sources: explorer counts = Python re-aggregation; simulator Direct within 1 pt of observed; sensitivity output at q = 0.5 equals 1 − q; replay C2 = validator exceptions; cube totals = 10M.

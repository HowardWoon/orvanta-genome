# Route inventory and defect register — web platform audit (14 Nov 2026)

Scope: the deployed team-only web edition (old 11-route single-file lab), compared against the ORVANTA implementation directive.
Severity: **P0** blocks judging or breaks correctness · **P1** a required capability is missing or misleading · **P2** degrades use or trust · **P3** polish.

## 1. Route inventory — before

| # | Old route | Content | Interactive? |
|---|---|---|---|
| 1 | `#overview` | KPIs, lab log, four-stage flow | buttons only |
| 2 | `#observatory` | dataset summary, issue table | no |
| 3 | `#transactions` | daily cube with 4 filters | yes (filters) |
| 4 | `#discovery` | pair table, trees | no |
| 5 | `#forensics` | Benford, cents, change points | no |
| 6 | `#rules` | rule list + detail | search on blur only |
| 7 | `#atlas` | static SVG, click focus, edge-kind chips | partial |
| 8 | `#routes` | top route patterns | no |
| 9 | `#validation` | pass/fail table | no |
| 10 | `#anomalies` | anomaly table and detector metrics | no |
| 11 | `#method` | method text, lineage | no |

## 2. Route inventory — after (39 routes, 9 groups)

| Group | Routes |
|---|---|
| Intelligence Overview | `overview` |
| Data Observatory | `data/summary`, `data/dictionary`, `data/quality`, `data/distributions`, `data/lineage` |
| Feature Intelligence | `feature/temporal`, `currency`, `institution`, `route`, `duration`, `fx`, `ttype`, `party`, `token`, `anomaly` |
| Rule Intelligence | `rules/explorer`, `rules/registry`, `rules/atlas`, `rules/discovery`, `rules/compare` |
| Interactive Research Lab | `lab/explorer`, `lab/playground`, `lab/simulator`, `lab/routes`, `lab/anomalies` |
| Statistical Forensics | `forensics/distribution`, `digits`, `tests`, `stability`, `counterexamples` |
| Validation Centre | `validation/scorecard`, `splits`, `reproducibility` |
| Research & Methodology | `method/approach`, `hypotheses`, `architecture`, `limitations` |
| Deliverables | `deliverables` |

Every route keeps its state in the URL query (`#/lab/explorer?otype=C&btype=B`), so refresh, back, forward and shared links restore the view.

## 3. Defect register

| ID | Sev | Defect (before) | Resolution | Verified by |
|---|---|---|---|---|
| D-W01 | P0 | Pooled Benjamini–Hochberg across unrelated families let X5 "gap" look significant (p_bh 0.04) | BH applied within each family (`src/webdata.py: bh`); X5 now 0/11 significant (gap p_bh 0.266) | `test_web.py::test_bh_is_per_family`, `test_web_e2e.py::test_x5_not_significant_after_bh` |
| D-W02 | P0 | R2 statement quoted in-sample class shares (≈76% / ≈5%) while the evidence is out-of-sample (61.4% / 6.7%) | Statement corrected in `src/rules.py` and the economic table; all reports regenerated | validation report, rule explorer |
| D-W03 | P1 | No feature-group pages; 10 feature groups not navigable | 10 Feature Intelligence pages: rules, interactive evidence, pipeline figures | route sweep test |
| D-W04 | P1 | No way to query the data: only one daily cube with 4 filters | Observed Data Explorer over a 10-dimension additive cube (10,396 cells, exact re-aggregation), comparison groups, Welch CI, Cohen's d, binned KS, CSV export | `test_explorer_matches_python_and_state_survives_reload` (counts equal an independent Python re-aggregation) |
| D-W05 | P1 | No simulator or playground — the "reconstructed generator" could not be run | Scenario Simulator (seeded Monte Carlo of R1/R2/R4, A1/A2, D1/D3 vs observed, KS fit, scenario labels); Synthetic Rule Playground (JS port of `rulelib`) | `test_simulator_calibrated_and_scenarios_labelled`, `test_js_rulelib_matches_python` |
| D-W06 | P1 | Atlas had no zoom, pan, search or upstream/downstream tracing | Wheel/button zoom, drag pan, node search, BFS trace by direction, rule focus, edge-kind filter, URL state | `test_atlas_trace_focus_zoom` |
| D-W07 | P1 | Rule search only filtered on blur | Live filtering on input, level chips, family filter, rejected candidates toggle | `test_rule_search_is_live` |
| D-W08 | P1 | No confidence scale beyond High/Medium/Low | Six-level scale with fixed criteria (VALIDATED … REJECTED); 29 rejected hypotheses kept as registry entries | Evidence registry page, `test_cube_reconciles…` checks the level set |
| D-W09 | P1 | Outputs were not labelled by kind; simulated and observed numbers could be confused | Five badges on every page (OBSERVED DATA, CONDITIONAL ESTIMATE, MODEL SIMULATION, STRUCTURAL SCENARIO, VALIDATED RULE); simulator flags any parameter moved off its estimate | visual review |
| D-W10 | P1 | No hypothesis-testing view | Forensics › Hypothesis testing: 297 tests, per-family BH, filters, CSV | route sweep |
| D-W11 | P2 | Quality checks had no drill-down | Selectable checks with detail; duplicate-row finding documented (one labelled DUPLICATE_PAYMENT pair, consistent with X2) | Data › Quality |
| D-W12 | P2 | All data embedded in one 2–3 MB HTML; every page paid for every dataset | Modular ES modules; JSON files lazy-loaded per page and cached | network panel |
| D-W13 | P2 | State lost on refresh; back/forward did not restore views | Hash routes with query-string state | `test_back_forward_restore_routes` |
| D-W14 | P2 | Number formatter crashed when used as a table callback (`minimumFractionDigits out of range`) — found during this rebuild | Formatters ignore non-numeric precision arguments | route sweep (39/39 render) |
| D-W15 | P2 | Mixed `??`/`||` without parentheses made the chart module fail to parse — found during this rebuild | Parenthesised; all modules syntax-checked with Node | route sweep |
| D-W16 | P2 | Some captions overstated evidence (e.g. "bank speed is independent of size"; "anomaly rates flat over time") — found during this rebuild | Captions rewritten to what the data shows (top-decile and 10k+ banks are rarely slow; rates shown with Wilson CIs only) | text review against JSON |
| D-W17 | P2 | Simulator amount model double-counted the intercept (A1 cell intercept + country effect measured against the 6+2+2 baseline) | Simulator uses the same structural form as `stats.py` (validated by the exceedance check, ratio 0.996 at $100k) | simulator KS |
| D-W18 | P2 | Route-cover simulation used a bank-share mixture that reproduced 9.1% instead of the observed 11.3% | Mixture weight solved so the pooled share is reproduced exactly at the estimates (sim 11.4% vs obs 11.3%) | simulator test |
| D-W19 | P3 | Mobile: sidebar pushed content below the fold | Collapsible menu under 900 px; no horizontal scroll at 390 px | `test_phone_layout_has_no_horizontal_scroll` |
| D-W20 | P3 | Missing favicon (404 on every load) | Inline SVG favicon | console clean in tests |
| D-W21 | P3 | Playground linked to rule P3, which is not in the registry | Links only to registered rules; reference-library rules are marked | visual review |

## 4. Protection by design (kept)

- The browser receives aggregates only: cube cells, route patterns with n ≥ 150, the top-600 bank table, token shares from a 500k sample and summary statistics. Tests assert that no account identifier or IBAN-shaped string is present in any shipped JSON.
- `noindex` meta and headers, `robots.txt` disallow-all, CSP (`script-src 'self'`), `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer`.
- `.vercelignore` excludes `.env*` (Vercel CLI writes an OIDC token there) and link metadata; the review ZIP excludes them too.
- Deployment stays team-only (Vercel SSO-protected preview) until judging; the public production alias serves a placeholder.

## 5. ORVANTA upgrade (second pass, 14 Nov 2026)

Route inventory after: **48 routes in 10 groups** (01 Command Centre 2 · 02 Data Observatory 5 · 03 Payment Intelligence 10 · 04 Generator Genome 5 · 05 Rule Foundry 4 · 06 Research Playground 6 · 07 Forensic Intelligence 6 · 08 Validation Centre 5 · 09 Research Library 4 · 10 Deliverables 1). Existing URLs kept.

| ID | Sev | Defect / gap | Resolution | Verified by |
|---|---|---|---|---|
| D-W22 | P1 | No way to inspect the records behind a rule | Forensic Replay (`src/replay.py`): exact counts on all rows, de-identified hash-ordered samples | `test_replay_counts_consistent_and_deidentified`, `test_forensic_replay_shows_exact_counterexamples` |
| D-W23 | P1 | Claims had no evidence IDs | Evidence Ledger, 459 EV records, linked from rules, genealogy, overview | `test_ledger_covers_every_rule…`, `test_ledger_genealogy_blueprint` |
| D-W24 | P1 | No structured hypothesis testing for users | Rule Builder with P1→P2 replication and Simpson flag | `test_rule_builder_runs_and_replicates` |
| D-W25 | P1 | Generator not summarised as a mechanism; discovery history invisible | Generator Blueprint; Rule Genealogy from the hypothesis log only | e2e + contract tests |
| D-W26 | P2 | Scenarios could not be compared or exported | Pin / compare / export in Scenario Studio | `test_scenario_pin_compare_and_sensitivity` |
| D-W27 | P2 | Builder's default example tested the wrong direction (fewer banks → *lower* manual share, D1) | default expectation set to "lower" | e2e |
| D-W28 | P3 | Literal newline inside a quoted JS string in the scenario export broke the module (found during this pass) | fixed; every module syntax-checked with Node | sweep 48/48 |

## 6. V4 final refinement (14 Nov 2026)

| ID | Sev | Defect | Resolution | Verified by |
|---|---|---|---|---|
| D-W29 | P1 | Judges met 48 routes before the strongest findings | Judge's guided tour (C2 → R1 → R2 → scenario), tour button on the overview, ★ judge-facing journey in the menu; overview reduced to headline + three findings + unresolved | `test_judge_guided_tour` |
| D-W30 | P1 | Slide 1 called all 34 rules "validated" (only 8 are at the VALIDATED level) | "34 rules reconstructed and tested"; dashboard p.1 "tested on five independent splits" | PDF text check |
| D-W31 | P1 | "FX = distinct currencies" alternative quoted as 90.6% (early sample) on slide 17, Q&A and the registry, while the validator reports 91.7% on all rows | all surfaces use the validator value; the hypothesis log keeps both with their scope | grep for 90.6 |
| D-W32 | P1 | C3 statement said "+≈3 pts per intermediary, outside ≈1.4%, first bank ≈94%" while its own metrics are 2.4 pts, 1.28%, 94.7% | statement corrected in `src/rules.py`; validation re-run | validation_report |
| D-W33 | P2 | Manual step quoted as "~20 minutes"; median is 1,456 s (≈24 min) | text now computed from `stats.json` | PDF text check |
| D-W34 | P2 | Limits slide listed country business shares as open (explained by P5) and the vehicle currency as unexplained (now quantified, H38) | replaced with G1 and the quantified H38 note | slide 17 |
| D-W35 | P2 | Conclusion did not say what was reconstructed / validated / unresolved | first bullet now states all three | slide 18 |
| D-W36 | P1 | References slide said "to be verified"; one title and one URL were outdated; UK Finance unverifiable | 5 references verified and corrected, BIS FX survey and Swift GPI added, UK Finance removed (`source_register.md`) | slide 19 |
| D-W37 | P2 | C2's two exceptions were unexplained | both are the only payments touching an Eritrean bank (home currency unobservable); shown in tour, replay, rule card, dashboard p.4, Q&A | replay + tour test |
| D-W38 | P2 | README described 39 Playwright routes | 49 routes (tour + 48) | test source |

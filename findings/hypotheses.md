# Hypothesis log (in the order tested)

Each entry: hypothesis → test → outcome → what changed. This is the "analysis loop" the rubric (1.1) rewards.

| # | Hypothesis | Test | Outcome | Consequence |
|---|---|---|---|---|
| H1 | PARTICIPANT_COUNT counts path elements | equality on 10M | Rejected as stated; **pc = known BICs** (excl. `...`) exactly | → R6 |
| H2 | Routing type depends on bank pair | purity of pairs; per-bank Direct share | Rejected: every bank ≈ 0.632 ± binomial noise | → R1 (global random draw) |
| H3 | Hop count ~ Poisson | successive ratios | Rejected; ratios constant at 1/e → **geometric** | → R1 |
| H4 | FX = distinct currencies on route | exact match | Rejected (91.7% on all 10M rows; 90.6% on the early sample) | — |
| H5 | FX = payment-currency start + borders | exact match | Rejected (93.5%) | — |
| H6 | FX = borders between adjacent known BICs | exact match | **Accepted, 9,999,998/10M** | → C2 |
| H7 | Intermediaries sit in the payment-currency zone | share in zone | Rejected (17%) | → R3 (size-weighted) |
| H8 | Slow durations come from off-hours queuing | slow share by hour | Raw effect 0.037 found, then explained by bank mix (FE range 0.003) | → D2 (Simpson) |
| H9 | Slow durations come from large-amount review | slow share by amount decile | Rejected (slightly reversed) | → D2 |
| H10 | Duration = per-bank additive steps | medians by bank class, out-of-sample | Accepted (both slow ≈ 1.9 × one slow) | → D1 |
| H11 | Amount depends on party types | 2×2 cell means | Accepted, exact 2-unit lattice | → A1 |
| H12 | Amount depends on beneficiary country | effect sd | Rejected (sd 0.23 vs 1.09 ordering) | → A2 |
| H13 | Individual accounts have own wealth level | variance component | Rejected (0.019 of 5.22) | → A2 |
| H14 | Timestamps in UTC office hours | night share | Rejected; **local clock** | → T1 |
| H15 | Local clock uses true DST offsets | offset estimation | Rejected; January offsets | → T1 note |
| H16 | Gulf/Israel banks have Fri–Sat weekend | weekday shares | Rejected; one universal shape | → T3 |
| H17 | Header BICs equal path endpoints | 30-row sample showed 28/30; full data 95.0% | Rejected → independent 5% swap per end | → R5 |
| H18 | On swaps, header BIC drives currency | home-ccy match by side | Rejected; path[1] drives currency & clock, header drives account/IBAN | → R5b, C1 & T1 re-specified on path[1] |
| H19 | Romance = C→C | type shares | Partly rejected: sender C 100%, receiver follows base mix | → X1 |
| H20 | Duplicates: first copy unlabelled | label share by copy order | Rejected; every copy labelled | → X2 |
| H21 | Fat finger ×10/×100/×1000 | GMM on residual | Two modes ≈ ±2 (log10) → ×100 / ÷100 | → X3 |
| H22 | Account-replacement reuses legit payee name | name match with different account | Rejected (1/649) | → X4 negative |
| H23 | Scams are slow because of added delay | stratified by bank speed | Rejected; scams sit at slow (small) banks | → X4 |
| H24 | CUSTOMER_RECALL has a signature | 11 tests, Bonferroni | Rejected (no feature significant) | → X5 negative |
| H25 | Weekly multiplier reflects month/quarter end | visual | Inconclusive | → T4 marked uncertain |
| H26 | Sender and receiver banks are paired independently | χ²/dof vs product of margins (raw, unique relationships, within country pair) | **Rejected**: 358 / 125 / 287; affinities directional (r = 0.11) | → G1 (Low confidence, mechanism open) |
| H27 | Path loops are deliberate | birthday prediction from intermediary size distribution | Rejected as deliberate: i.i.d. draws with replacement predict loops within 3.1% | → G3 |
| H28 | Amounts have a power-law tail | Hill estimator drift, exceedances vs lognormal | Rejected; lognormal (Hill α 2.21 → 1.21; exceedances within 1–15%) | → A3 |
| H29 | Manual step is lognormal | Gamma vs lognormal KS | Gamma(2) fits better (KS 0.023 vs 0.066) | → D3 |
| H30 | Fat finger is identifiable from the amount alone | PR curve of residual threshold | Only partly: best F1 0.22, PR-AUC 0.10 (500× base rate) | → X3 detector |
| H31 | CEO scam identifiable by a simple payee heuristic | precision/recall | Rejected: precision 0.03% | → X4 limitation |
| H32 | Covered share is constant across sending banks | discovery engine flag (V .095); bank dispersion 378× binomial; out-of-sample classes | **Rejected** → per-bank propensity (61% vs 6.7%) | → R2 revised |
| H33 | Payment currency independent of route | currency position among route-bank currencies | Rejected: 98.7% in a route currency; receiver 3.8%; +2.4 pts per intermediary | → C3 (new) |
| H34 | Customer-type share set per country | bank-level split-half correlation | Rejected: bank attribute (r ≈ 0.99) | → P5 (new) |
| H35 | Weekly levels change at arbitrary dates | binary segmentation | Rejected: 10/10 change points on Mondays | → T4b |
| H36 | Amounts drawn directly in USD | cents by currency | Rejected: USD 39% whole units vs 1.0% for converted currencies | → F1 |
| H37 | Conversion uses one fixed rate per currency | near-integer search over rate grid | Not supported (≈2% vs 1.2% baseline) | → F1 limitation |
| H38 | Outside-route currencies are a route-independent vehicle draw | EUR/USD share on routes without an EUR or USD bank, by route length and split (all 10M rows) | Supported: EUR 1.41% (1.39–1.42% across splits), USD 0.75%, other 0.30%; flat across pc 2–5; 77.7% of outside-route payments are EUR/USD | → C3 limitation refined (vehicle draw); not promoted to a separate rule |

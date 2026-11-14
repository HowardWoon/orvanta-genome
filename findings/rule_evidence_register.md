# Rule evidence register

Built from validation run 2026-11-14T17:00:29. Status = validator outcome on all splits (full, random halves, two periods).

| ID | Group | Type | Confidence | Rule | Headline evidence (full data) | Status | In deck |
|---|---|---|---|---|---|---|---|
| R6 | Routing | A | High | PARTICIPANT_COUNT = number of known BICs in BIC8_PATH | share_exact=1; n=1e+07 | PASS | Yes (method slide) |
| R7 | Routing | A | High | CONTINUITY_QFLAG = 'N' iff path contains '...' | share_exact=1; n=1e+07 | PASS | Yes |
| R5 | Routing | B | High | Path endpoints differ from ORDERING/BENEFICIARY_BIC8 independently with p≈0.05 each | p_first=0.04984; p_last=0.04993; p_both=0.002469; indep_ratio=0.9924 | PASS | Yes |
| R5b | Routing / Currency | E | Medium | On endpoint mismatch, currency follows the path's first bank; account/IBAN follows ORDERING_BIC8 | ccy_follows_path_first=0.9348; ccy_follows_obic=0.1386; iban_follows_obic=1; n=4.984e+05 | PASS | Yes |
| R1 | Routing | B | High | Intermediaries K = floor(Exp(1)): P(K=k) = (1-1/e)e^-k | n=1e+07; q_mle=0.3677; inv_e=0.3679; cohen_w=0.0005785 | PASS | Yes |
| R2 | Routing | C | High | Covered vs Indirect is a per-sending-bank propensity (cover-prone banks ≈61%, others ≈7%, out of sample), independent of route length | n=3.677e+06; pooled_covered_share=0.1131; cramers_v_vs_K=0.000513; share_k2=0.1129 | PASS | Yes |
| R4 | Routing | B | High | Each link hidden with p=0.05: P(N | pc) = 1-0.95^(pc-1) | max_abs_dev=0.004366; p_link_mle=0.04991 | PASS | Yes |
| R3 | Routing | C | High | Intermediaries chosen in proportion to bank size, not by payment currency | corr_log=0.9423; share_in_currency_zone=0.173 | PASS | Dashboard |
| C2 | Currency | A | High | FX count = adjacent known-BIC pairs with different home currencies | share_exact=0.9999998; n=1e+07; exceptions=2; alt_distinct=0.9168 | PASS | Yes |
| C3 | Currency | E | High | Payment currency is drawn from the currencies on the route: first bank ≈ 95% (direct), receiver bank ≈ 3.8%, +≈2.4 pts per intermediary, outside-route vehicle ≈ 1.3% | n_sample=3e+06; in_route_share=0.9872; receiver_only_mean=0.0379; receiver_only_range=0.002558 | PASS | Yes |
| C1 | Currency | C | Medium | Payment currency = home currency of the instructing (first-path) bank ~93% | home_share=0.9342; n=1e+07 | PASS | Yes |
| A1 | Amount | C | High | ln(amount) = 6 + 2·[O=B] + 2·[B=B], σ≈2.28 (no interaction) | intercept=6.062; effect_ordering_B=1.932; effect_beneficiary_B=1.965; interaction=0.03887 | PASS | Yes |
| A2 | Amount | C | Medium | Ordering-country effect replicates across independent halves (beneficiary country ≈ no effect) | split_half_corr=0.9998446; sd_ordering=1.091; sd_beneficiary=0.2321; countries=62 | PASS | Yes |
| D1 | Duration | E | Medium | Duration = sum of per-bank steps; bank speed class learned on half_0 predicts half_1 | fast->fast={'n': 2111142.0, 'slow_share': 0.13415345817571722, 'median_s': 27.0}; fast->slow={'n': 349335.0, 'slow_share': 0.9707844905320108, 'median_s': 1412.0}; slow->fast={'n': 493927.0, 'slow_share': 0.9617757279921931, 'median_s': 1387.0}; slow->slow={'n': 141699.0, 'slow_share': 0.9993295647816851, 'median_s': 2641.0} | PASS | Yes |
| D2 | Duration | C | Medium | Manual (slow) processing is a bank attribute: hour/weekday/amount effects vanish once bank fixed effects are removed | raw_range_by_hour=0.03688; fe_range_by_hour=0.002913; fe_range_by_weekday=0.001452; fe_corr_ln_amount=-0.0008232 | PASS | Yes |
| T1 | Time | C | High | Activity follows the instructing bank's local clock (fixed offsets) | night_local=0.04594; night_utc=0.1237 | PASS | Yes |
| T3 | Time | B | High | One weekday shape for all countries (local weekday) | max_dev=0.003874; countries=35 | PASS | Yes |
| T4 | Time | B | Medium | Weekly volume multiplier is global (shared by all countries) | min_corr=0.9992217 | PASS | Yes |
| P2 | Parties | A | High | IBAN prefix always equals BIC country; IBAN used only by IBAN-country banks | o_prefix=1; b_prefix=1; countries_ambiguous=0 | PASS | Yes |
| P4 | Parties | C | Medium | Ordering party lives in its bank's country; beneficiary residence is decoupled from its bank | o_match=1; b_match=0.009796 | PASS | Yes |
| P5 | Parties | C | High | Customer-type mix is a bank attribute: each bank has its own business share of senders and of receivers | sender_split_half_r=0.9945; sender_banks=2412; sender_bank_share_min=0.03201; sender_bank_share_max=1 | PASS | Dashboard |
| P1b | Parties | B | High | Beneficiary type independent of ordering type | pB_given_oB=0.2884; pB_given_oC=0.2873; diff=0.001093 | PASS | Dashboard |
| X1 | Anomalies | E | High | ROMANCE_SCAM: consumer bursts of 2-8 escalating payments (×~1.5 each) | sender_consumer_share=1; median_ln_step=0.4001; mean_ln_step=0.3903; labelled_share_in_series=1 | PASS | Yes |
| X2 | Anomalies | A | High | DUPLICATE_PAYMENT: 2-5 identical copies (amount, path, duration) within 2h; all copies labelled | groups=185; max_paths=1; max_durations=1; max_span_s=7043 | PASS | Yes |
| X3 | Anomalies | C | Medium | FAT_FINGER_MISTAKE: amount ×100 or ÷100 relative to expectation | mode_low=-1.95; mode_high=2.435; component_sd=1.139; up_share=0.7727 | PASS | Yes |
| X4 | Anomalies | C | Medium | CEO & ACCOUNT_REPLACEMENT scams pay mule accounts at small banks | ROMANCE_SCAM=0.603; ACCOUNT_REPLACEMENT_SCAM=0.47; CEO_SCAM=0.4836; CUSTOMER_RECALL=0.183 | PASS | Yes |
| X5 | Anomalies | B | Low | CUSTOMER_RECALL has no observable signature (negative result) | weekend={'recall': 0.09779179810725552, 'normal': 0.11184275703557912, 'z': -0.7937554721582865, 'p': 0.42733779958172613, 'p_bonf': 1}; domestic={'recall': 0.05362776025236593, 'normal': 0.07113223524401195, 'z': -1.2124631466829425, 'p': 0.22533514151605205, 'p_bonf': 1}; gap={'recall': 0.11041009463722397, 'normal': 0.076720050067077, 'z': 2.2537725009717793, 'p': 0.024210483620425945, 'p_bonf': 0.24210483620425943}; ord_B={'recall': 0.7760252365930599, 'normal': 0.7876368183549395, 'z': -0.5054967868810158, 'p': 0.613209954662462, 'p_bonf': 1} | PASS | Yes (negative result) |
| X6 | Anomalies | B | High | Anomaly label is independent of routing type | chi2=204.3; p=4.307e-37; dof=12; cramers_v=0.003196 | PASS | Dashboard |
| F1 | Fingerprints | D | High | Fingerprint: USD-denominated amounts keep whole-unit roundness (≈39% .00) while converted currencies have uniform cents (≈1%) | usd_whole_share=0.3864; non_usd_whole_share=0.009885; n_usd=1.702e+06 | PASS | Yes |
| T4b | Time | B | High | Weekly volume levels are piecewise-constant with every change point on a Monday (week boundary) | change_points=10; share_on_monday=1; residual_sd_log=0.01831; segments=11 | PASS | Yes |
| G3 | Routing graph | E | High | Intermediaries drawn i.i.d. with replacement ∝ bank size — predicts the path revisit (loop) rate | max_rel_err=0.0306; pc7_obs=0.05701; pc6_obs=0.03514; pc4_obs=0.006031 | PASS | Yes |
| G1 | Routing graph | C | Low | Sender and receiver banks are NOT paired independently (directional affinities) — independence rejected | chi2_dof_raw=358.2; chi2_dof_unique=125.4; chi2_dof_within_country=286.6; domestic_affinity=1.201 | PASS | Yes (partial result) |
| A3 | Amount | B | High | Within-country log-amount residual is Normal (lognormal amounts, no power-law tail) | sd=2.08; skew=-0.02395; excess_kurtosis=0.006827; ks_D=0.003462 | PASS | Dashboard |
| D3 | Duration | B | Medium | Manual processing step ≈ Gamma(shape≈2, scale≈820 s); fast step pair ≈ Gamma(3, 8.7 s) | manual_shape=2.045; manual_scale_s=817.1; manual_ks_gamma=0.02321; manual_ks_lognormal=0.06561 | PASS | Dashboard |

## Entries

### R6 — PARTICIPANT_COUNT = number of known BICs in BIC8_PATH
- **Hypothesis / why it matters:** PARTICIPANT_COUNT is derived from the path, not drawn independently.
- **Fields:** PARTICIPANT_COUNT, BIC8_PATH
- **Sample size:** 10,000,000 rows (splits ≈5M each) unless stated
- **Explicit rule:** PARTICIPANT_COUNT := number of BIC8 entries in BIC8_PATH that are not '...'
- **Logic:** `pc = |{b ∈ split(path,';') : b ≠ '...'}|  · rulelib.participant_count`
- **Method:** Exact equality test on all rows; pure-Python re-implementation on 200k sample.
- **Acceptance criterion:** share_exact == 1
- **Result:** PASS — share_exact=1; n=1e+07
- **Confidence:** High
- **Counterexamples / exceptions:** None found.
- **Limitations:** Says nothing about how many hops were hidden.
- **Economic interpretation (interpretation, not proven by data):** Counts observed institutions only, i.e. what the messaging layer can see.
- **Visualisation:** pc vs path elements table · **Presentation:** Yes (method slide)

### R7 — CONTINUITY_QFLAG = 'N' iff path contains '...'
- **Hypothesis / why it matters:** CONTINUITY_QFLAG encodes the presence of '...' placeholders.
- **Fields:** CONTINUITY_QFLAG, BIC8_PATH
- **Sample size:** 10,000,000 rows (splits ≈5M each) unless stated
- **Explicit rule:** CONTINUITY_QFLAG := 'N' if BIC8_PATH contains '...', else 'Y'
- **Logic:** `cont = N ⇔ '...' ∈ split(path)  · rulelib.continuity_flag`
- **Method:** Exact equivalence test.
- **Acceptance criterion:** share_exact == 1
- **Result:** PASS — share_exact=1; n=1e+07
- **Confidence:** High
- **Counterexamples / exceptions:** None.
- **Limitations:** Flag is an observability marker, not payment success/failure.
- **Economic interpretation (interpretation, not proven by data):** A leg left the observed channel (e.g. a domestic clearing leg).
- **Visualisation:** - · **Presentation:** Yes

### R5 — Path endpoints differ from ORDERING/BENEFICIARY_BIC8 independently with p≈0.05 each
- **Hypothesis / why it matters:** Header BICs and path endpoints can disagree; disagreement is random noise or a structural role split.
- **Fields:** ORDERING_BIC8, BENEFICIARY_BIC8, BIC8_PATH
- **Sample size:** 10,000,000 rows (splits ≈5M each) unless stated
- **Explicit rule:** With probability 0.05 the first known path BIC is replaced by another bank; independently, with probability 0.05 the last known BIC is replaced
- **Logic:** `P(k₁ ≠ ORDERING_BIC8) = P(k_last ≠ BENEFICIARY_BIC8) = 0.05; P(both) = 0.05²`
- **Method:** Mismatch rates per end, joint vs product (independence), stratified by type, pc, anomaly.
- **Acceptance criterion:** first & last mismatch in [0.045,0.055] and joint/product ratio in [0.9,1.1]
- **Result:** PASS — p_first=0.04984; p_last=0.04993; p_both=0.002469; indep_ratio=0.9924
- **Confidence:** High
- **Counterexamples / exceptions:** ROMANCE_SCAM never swaps; CEO/ACCOUNT_REPLACEMENT never swap at the beneficiary end (mule bank is the true receiver).
- **Limitations:** Cannot tell which institution is 'real' from one field alone; R5b resolves it with currency/clock/IBAN evidence.
- **Economic interpretation (interpretation, not proven by data):** Ordering institution (account servicer, MT field 52) ≠ instructing agent that sends the message — common when a smaller bank uses a correspondent to send.
- **Visualisation:** 2×2 mismatch table · **Presentation:** Yes

### R5b — On endpoint mismatch, currency follows the path's first bank; account/IBAN follows ORDERING_BIC8
- **Hypothesis / why it matters:** On swapped rows, which BIC drives currency, timing and account format?
- **Fields:** CURRENCY_CODE, EPOCH_SECONDS, ORDERING_ACCOUNT, BIC8_PATH
- **Sample size:** 10,000,000 rows (splits ≈5M each) unless stated
- **Explicit rule:** On replaced rows, CURRENCY_CODE and the local clock follow path[1] (instructing bank); account IBAN and ordering address follow ORDERING_BIC8 (account-servicing bank)
- **Logic:** `compare P(cur = home(path[1])) vs P(cur = home(ORDERING_BIC8)) on rows with path[1] ≠ ORDERING_BIC8`
- **Method:** Compare home-currency match, local-night share and IBAN prefix against path[1] vs ORDERING_BIC8.
- **Acceptance criterion:** home-ccy share via path[1] > 0.85 and via ORDERING_BIC8 < 0.25; IBAN prefix = ORDERING_BIC8 country == 1
- **Result:** PASS — ccy_follows_path_first=0.9348; ccy_follows_obic=0.1386; iban_follows_obic=1; n=4.984e+05
- **Confidence:** Medium
- **Counterexamples / exceptions:** Small share of non-home currency on both sides (vehicle currencies).
- **Limitations:** Relies on our data-derived country→currency map.
- **Economic interpretation (interpretation, not proven by data):** The instructing bank books and times the payment; the customer's account stays at the servicing bank.
- **Visualisation:** bar: match via path[1] vs header · **Presentation:** Yes

### R1 — Intermediaries K = floor(Exp(1)): P(K=k) = (1-1/e)e^-k
- **Hypothesis / why it matters:** Number of intermediaries follows a simple distribution.
- **Fields:** PARTICIPANT_COUNT, TRANSACTION_TYPE_CODE
- **Sample size:** 10,000,000 rows (splits ≈5M each) unless stated
- **Explicit rule:** Number of intermediaries K ~ ⌊Exp(1)⌋; PARTICIPANT_COUNT = K + 2
- **Logic:** `P(K = k) = (1 − e⁻¹)·e⁻ᵏ; MLE q̂ = K̄/(1+K̄); GOF χ² → Cohen's w`
- **Method:** Geometric MLE, successive ratios, chi-square GOF with Cohen's w, per split; per-bank Direct share vs binomial.
- **Acceptance criterion:** MLE continuation q within ±0.005 of 1/e and Cohen's w < 0.01 on every split
- **Result:** PASS — n=1e+07; q_mle=0.3677; inv_e=0.3679; cohen_w=0.0005785
- **Confidence:** High
- **Counterexamples / exceptions:** None beyond sampling noise. Max pc = 22 is the far tail: the rule predicts 10M·e^-15 ≈ 3.1 rows with pc ≥ 17; 5 are observed (Poisson P(X≥5 | 3.1) ≈ 0.2).
- **Limitations:** Correspondent choice is random in the generator; real networks depend on bilateral relationships.
- **Economic interpretation (interpretation, not proven by data):** Each extra correspondent hop is a fixed-probability event; most payments have a direct relationship.
- **Visualisation:** observed vs predicted (log) · **Presentation:** Yes

### R2 — Covered vs Indirect is a per-sending-bank propensity (cover-prone banks ≈61%, others ≈7%, out of sample), independent of route length
- **Hypothesis / why it matters:** How Covered vs Indirect is chosen among non-direct routes.
- **Fields:** TRANSACTION_TYPE_CODE, ORDERING_BIC8, PARTICIPANT_COUNT
- **Sample size:** 10,000,000 rows (splits ≈5M each) unless stated
- **Explicit rule:** Among non-direct routes, TRANSACTION_TYPE = Covered with a sending-bank propensity π_b (cover banks π ≈ 0.6–0.8, others π ≈ 0.05); independent of K
- **Logic:** `π_b estimated on half 0; Covered share on half 1 by class; Cramér's V(type × K)`
- **Method:** Share by K (Cramér's V); per-bank propensity with classes learned on half_0 and tested on half_1; within-country dispersion vs binomial.
- **Acceptance criterion:** Cramér's V(type×K) < 0.01 on every split; out-of-sample: banks classed as cover banks on half_0 send >50% Covered on half_1, others <10%
- **Result:** PASS — n=3.677e+06; pooled_covered_share=0.1131; cramers_v_vs_K=0.000513; share_k2=0.1129
- **Confidence:** High
- **Counterexamples / exceptions:** Original claim 'constant 11.3%' REJECTED by the discovery engine: share ranges 3–50% by sending country (IM 50%, SG 6%) and is 378× over-dispersed within countries — the parameter lives at bank level.
- **Limitations:** Cover-bank class boundary (0.5) is analyst-chosen; cover share of a bank is not explained further.
- **Economic interpretation (interpretation, not proven by data):** The cover method (MT103 direct + MT202 COV through correspondents) is a bank's operating choice — some institutions habitually settle by cover.
- **Visualisation:** bank-class bars · **Presentation:** Yes

### R4 — Each link hidden with p=0.05: P(N | pc) = 1-0.95^(pc-1)
- **Hypothesis / why it matters:** Hidden hops arise per link with constant probability.
- **Fields:** CONTINUITY_QFLAG, PARTICIPANT_COUNT, BIC8_PATH
- **Sample size:** 10,000,000 rows (splits ≈5M each) unless stated
- **Explicit rule:** Each link between consecutive known BICs is hidden ('...') independently with p = 0.05; extra '...' per hidden link ~ Geometric(0.05)
- **Logic:** `P(cont = N | pc) = 1 − 0.95^(pc−1); p̂ by MLE over pc strata`
- **Method:** Binomial-per-link model, MLE of p, max deviation per pc.
- **Acceptance criterion:** max |obs-pred| over pc 2..7 < 0.006
- **Result:** PASS — max_abs_dev=0.004366; p_link_mle=0.04991
- **Confidence:** High
- **Counterexamples / exceptions:** Consecutive '...' chain geometrically (ratio ≈ 0.05).
- **Limitations:** None material.
- **Economic interpretation (interpretation, not proven by data):** Each inter-bank leg independently may run outside the observed network.
- **Visualisation:** obs vs formula · **Presentation:** Yes

### R3 — Intermediaries chosen in proportion to bank size, not by payment currency
- **Hypothesis / why it matters:** Intermediaries are chosen by size (popularity), not by currency zone.
- **Fields:** BIC8_PATH, CURRENCY_CODE
- **Sample size:** 10,000,000 rows (splits ≈5M each) unless stated
- **Explicit rule:** Intermediaries are sampled with probability proportional to bank activity, not from the payment-currency zone
- **Logic:** `corr(log uses_as_intermediary, log payments_sent); share of intermediaries whose home currency = payment currency`
- **Method:** Correlation of log usage vs log sending volume; share in currency zone.
- **Acceptance criterion:** corr(log intermediary uses, log payments sent) > 0.9; share in payment-currency zone < 0.25
- **Result:** PASS — corr_log=0.9423; share_in_currency_zone=0.173
- **Confidence:** High
- **Counterexamples / exceptions:** Currency-zone hypothesis rejected (17% vs >50% expected under it).
- **Limitations:** Size proxy is sending volume, itself endogenous.
- **Economic interpretation (interpretation, not proven by data):** Large banks hold the most nostro accounts and act as hubs.
- **Visualisation:** scatter · **Presentation:** Dashboard

### C2 — FX count = adjacent known-BIC pairs with different home currencies
- **Hypothesis / why it matters:** FX count is deterministic in the route.
- **Fields:** CURRENCY_CONVERSION_COUNT, BIC8_PATH
- **Sample size:** 10,000,000 rows (splits ≈5M each) unless stated
- **Explicit rule:** CURRENCY_CONVERSION_COUNT := Σ over consecutive known BICs of 1[home_ccy(country(bᵢ)) ≠ home_ccy(country(bᵢ₊₁))]
- **Logic:** `home_ccy = modal currency of the country's sending banks  · rulelib.fx_count`
- **Method:** Exact rule test on all rows; two rejected alternatives; pure-Python cross-check.
- **Acceptance criterion:** share_exact >= 0.99999
- **Result:** PASS — share_exact=0.9999998; n=1e+07; exceptions=2; alt_distinct=0.9168
- **Confidence:** High
- **Counterexamples / exceptions:** 2 rows, and they are the only 2 payments in the dataset that touch an Eritrean bank (0000ERA0, receiver). Eritrea never sends, so its home currency cannot be inferred and the rule's input is unobservable there; if ER's currency differs from the sender's, C2 predicts exactly the recorded 1 conversion. Scope: C2 holds wherever every route country has an observable home currency.
- **Limitations:** Home currency per country is inferred from the data (modal currency).
- **Economic interpretation (interpretation, not proven by data):** Each correspondent converts into the currency of its next nostro account; conversions happen at currency borders.
- **Visualisation:** pc × fx heatmap · **Presentation:** Yes

### C3 — Payment currency is drawn from the currencies on the route: first bank ≈ 95% (direct), receiver bank ≈ 3.8%, +≈2.4 pts per intermediary, outside-route vehicle ≈ 1.3%
- **Hypothesis / why it matters:** Where the payment currency comes from.
- **Fields:** CURRENCY_CODE, BIC8_PATH
- **Sample size:** 10,000,000 rows (splits ≈5M each) unless stated
- **Explicit rule:** CURRENCY_CODE is drawn from the route: home currency of path[1] (≈95% if direct), else the receiver bank's currency (≈3.8%), else an intermediary's currency (≈+2.4 pts per intermediary), else a global vehicle (≈1.3%)
- **Logic:** `position of cur among home currencies of path BICs, by route length; weighted linear slope per intermediary`
- **Method:** Currency matched against the home currencies of every bank on the path, by route length; per split on a 3M-row reservoir sample.
- **Acceptance criterion:** ≥98% of payments in a route-bank currency on every split; receiver-only share stable across route lengths (range < 0.006); intermediary-only share rises ≈ linearly per intermediary (slope 0.02–0.035)
- **Result:** PASS — n_sample=3e+06; in_route_share=0.9872; receiver_only_mean=0.0379; receiver_only_range=0.002558
- **Confidence:** High
- **Counterexamples / exceptions:** 1.27% of payments (126,857) use a currency of no route bank; 77.7% of them are EUR or USD. H38 (all 10M rows, 5 splits): on routes with no EUR or USD bank the payment is in EUR 1.41% and USD 0.75% of the time, stable across route length (pc 2–5) and splits (EUR 1.39–1.42%) — a route-independent vehicle draw that shows up as 'outside' only when that currency is not already on the route. Supported refinement, not a separate validated rule (the EUR/USD set was chosen after inspection).
- **Limitations:** Direction (route first, then currency) is consistent with the data, not identified; the per-intermediary probability is approximate (linear fit).
- **Economic interpretation (interpretation, not proven by data):** A payment is denominated in a currency some bank in the chain can book: the sender's (most), the receiver's, or a correspondent's clearing currency; otherwise a global vehicle currency.
- **Visualisation:** share by route position · **Presentation:** Yes

### C1 — Payment currency = home currency of the instructing (first-path) bank ~93%
- **Hypothesis / why it matters:** Payment currency is the instructing bank's home currency.
- **Fields:** CURRENCY_CODE, BIC8_PATH
- **Sample size:** 10,000,000 rows (splits ≈5M each) unless stated
- **Explicit rule:** CURRENCY_CODE = home currency of the instructing bank with probability ≈ 0.93 (country-specific 0.73–0.98)
- **Logic:** `P(cur = home(path[1])) per split and per country`
- **Method:** Share by split; per-country range.
- **Acceptance criterion:** share in [0.91,0.95] on every split; per-country share range reported
- **Result:** PASS — home_share=0.9342; n=1e+07
- **Confidence:** Medium
- **Counterexamples / exceptions:** 6.6% non-home (EUR, USD, GBP, CHF, CNY, SGD …); RU only 73% home.
- **Limitations:** Vehicle-currency selection mechanism not fully identified.
- **Economic interpretation (interpretation, not proven by data):** Local-currency funding; invoices in global vehicle currencies.
- **Visualisation:** stacked bars · **Presentation:** Yes

### A1 — ln(amount) = 6 + 2·[O=B] + 2·[B=B], σ≈2.28 (no interaction)
- **Hypothesis / why it matters:** Log-amount mean is additive in party types.
- **Fields:** USD_AMOUNT, ORDERING_TYPE, BENEFICIARY_TYPE
- **Sample size:** 10,000,000 rows (splits ≈5M each) unless stated
- **Explicit rule:** ln(USD_AMOUNT) ~ Normal(6 + 2·[ORDERING_TYPE=B] + 2·[BENEFICIARY_TYPE=B] + c_country + b_bank, σ ≈ 2.08)
- **Logic:** `2×2 cell means → intercept, main effects, interaction; σ per cell`
- **Method:** 2×2 cell means → intercept, main effects, interaction; σ per cell; per split.
- **Acceptance criterion:** intercept∈[5.9,6.2], both effects∈[1.85,2.15], |interaction|<0.1, σ spread across cells <0.03
- **Result:** PASS — intercept=6.062; effect_ordering_B=1.932; effect_beneficiary_B=1.965; interaction=0.03887
- **Confidence:** High
- **Counterexamples / exceptions:** Amount residual is slightly left-skewed (−0.12); 13.5% of fat-finger amounts are integers.
- **Limitations:** Country and bank effects add structure on top (A2).
- **Economic interpretation (interpretation, not proven by data):** Commercial flows ≫ personal flows; B2B largest.
- **Visualisation:** segment histograms · **Presentation:** Yes

### A2 — Ordering-country effect replicates across independent halves (beneficiary country ≈ no effect)
- **Hypothesis / why it matters:** Sending-country wealth level shifts amounts; beneficiary country does not.
- **Fields:** USD_AMOUNT, ORDERING_BIC8
- **Sample size:** 10,000,000 rows (splits ≈5M each) unless stated
- **Explicit rule:** Sending-country level c_country shifts ln(amount) (≈ −3.2 … +2.0); beneficiary country has ≈ no effect
- **Logic:** `country effect on half 0 vs half 1 (r); sd(ordering effects) vs sd(beneficiary effects)`
- **Method:** Country effects estimated separately on random halves; sd comparison.
- **Acceptance criterion:** corr(country effect half_0, half_1) > 0.95; sd(ordering effects) > 3×sd(beneficiary effects)
- **Result:** PASS — split_half_corr=0.9998446; sd_ordering=1.091; sd_beneficiary=0.2321; countries=62
- **Confidence:** Medium
- **Counterexamples / exceptions:** Effects are randomised by design (case text) — ranking is not real-world.
- **Limitations:** Bank-level variance (0.22) not decomposed further.
- **Economic interpretation (interpretation, not proven by data):** GDP-like scaling of ticket size at origin.
- **Visualisation:** diverging bars · **Presentation:** Yes

### D1 — Duration = sum of per-bank steps; bank speed class learned on half_0 predicts half_1
- **Hypothesis / why it matters:** Duration is a sum of per-bank processing steps.
- **Fields:** TOTAL_DURATION, BIC8_PATH
- **Sample size:** 10,000,000 rows (splits ≈5M each) unless stated
- **Explicit rule:** TOTAL_DURATION ≈ Σ over participating banks of a step: fast (seconds) with probability STP(b), manual otherwise
- **Logic:** `bank classes on half 0; medians by class pair on half 1; additivity ratio med(slow,slow)/med(one slow)`
- **Method:** Bank speed classes learned on half_0, tested on half_1 (out-of-sample).
- **Acceptance criterion:** out-of-sample: fast→fast slow-share < 0.2, any slow bank > 0.9, median(slow,slow)/median(one slow) in [1.6,2.4]
- **Result:** PASS — fast->fast={'n': 2111142.0, 'slow_share': 0.13415345817571722, 'median_s': 27.0}; fast->slow={'n': 349335.0, 'slow_share': 0.9707844905320108, 'median_s': 1412.0}; slow->fast={'n': 493927.0, 'slow_share': 0.9617757279921931, 'median_s': 1387.0}; slow->slow={'n': 141699.0, 'slow_share': 0.9993295647816851, 'median_s': 2641.0}
- **Confidence:** Medium
- **Counterexamples / exceptions:** ~13% slow cases among fast-fast pairs (each 'fast' bank has a non-zero manual rate).
- **Limitations:** Exact step distributions not fitted.
- **Economic interpretation (interpretation, not proven by data):** STP vs manual repair/compliance review.
- **Visualisation:** bank-class medians · **Presentation:** Yes

### D2 — Manual (slow) processing is a bank attribute: hour/weekday/amount effects vanish once bank fixed effects are removed
- **Hypothesis / why it matters:** Manual processing depends on bank, not on time or amount.
- **Fields:** TOTAL_DURATION, EPOCH_SECONDS, USD_AMOUNT
- **Sample size:** 10,000,000 rows (splits ≈5M each) unless stated
- **Explicit rule:** Manual-step probability depends on the bank only, not on hour, weekday or amount
- **Logic:** `y = 1[dur > 120]; r = y − ȳ_sender − ȳ_receiver + ȳ; range of r̄ by hour/weekday`
- **Method:** Two-way bank fixed-effect demeaning; residual ranges by hour/weekday; corr with amount.
- **Acceptance criterion:** after two-way (sender bank, receiver bank) demeaning among fast-fast pairs: residual range across UTC hours < 0.015, weekdays < 0.015, |corr with ln amount| < 0.02
- **Result:** PASS — raw_range_by_hour=0.03688; fe_range_by_hour=0.002913; fe_range_by_weekday=0.001452; fe_corr_ln_amount=-0.0008232
- **Confidence:** Medium
- **Counterexamples / exceptions:** Raw hour effect 0.037 is a Simpson artefact (bank mix across time zones).
- **Limitations:** Linear-probability FE approximation.
- **Economic interpretation (interpretation, not proven by data):** Automation level is an institution attribute.
- **Visualisation:** raw vs adjusted line · **Presentation:** Yes

### T1 — Activity follows the instructing bank's local clock (fixed offsets)
- **Hypothesis / why it matters:** Timestamps are generated in the instructing bank's local time.
- **Fields:** EPOCH_SECONDS, BIC8_PATH
- **Sample size:** 10,000,000 rows (splits ≈5M each) unless stated
- **Explicit rule:** Timestamp drawn on the instructing bank's local clock (fixed January UTC offsets): office curve starting 07:00
- **Logic:** `local_hour = (UTC_hour + offset(country(path[1]))) mod 24; night share 01–05h`
- **Method:** Night-share comparison local vs UTC; offset estimation by profile alignment.
- **Acceptance criterion:** night share (01-05h local) < 0.06 on every split vs > 0.15 with UTC
- **Result:** PASS — night_local=0.04594; night_utc=0.1237
- **Confidence:** High
- **Counterexamples / exceptions:** Offsets are January values (no DST).
- **Limitations:** Offsets estimated in whole hours (IN shows +5, true +5:30).
- **Economic interpretation (interpretation, not proven by data):** Office-hours behaviour; cut-off driven submissions.
- **Visualisation:** local-hour line · **Presentation:** Yes

### T3 — One weekday shape for all countries (local weekday)
- **Hypothesis / why it matters:** Weekday shape is universal.
- **Fields:** EPOCH_SECONDS
- **Sample size:** 10,000,000 rows (splits ≈5M each) unless stated
- **Explicit rule:** Local weekday shares Mon 18.9 · Tue 17.0 · Wed 17.0 · Thu 18.0 · Fri 18.9 · Sat 3.6 · Sun 6.5 % for every country
- **Logic:** `max |share_country − share_pooled| over countries with ≥ 50k rows`
- **Method:** Max deviation of country weekday shares from pooled.
- **Acceptance criterion:** max deviation of any country's weekday share from pooled share < 0.01 (countries ≥50k rows)
- **Result:** PASS — max_dev=0.003874; countries=35
- **Confidence:** High
- **Counterexamples / exceptions:** Fri–Sat weekend hypothesis for Gulf/Israel rejected.
- **Limitations:** -
- **Economic interpretation (interpretation, not proven by data):** Sunday batch preparation > Saturday.
- **Visualisation:** weekday bars · **Presentation:** Yes

### T4 — Weekly volume multiplier is global (shared by all countries)
- **Hypothesis / why it matters:** Weekly volume level is global.
- **Fields:** EPOCH_SECONDS
- **Sample size:** 10,000,000 rows (splits ≈5M each) unless stated
- **Explicit rule:** Weekly volume = base × level(week), the same level for every country
- **Logic:** `min corr(weekly volume of country, total) over top-10 countries`
- **Method:** Correlation of country weekly series with total.
- **Acceptance criterion:** min corr of weekly volume between top-10 countries and the total > 0.98
- **Result:** PASS — min_corr=0.9992217
- **Confidence:** Medium
- **Counterexamples / exceptions:** Cause of levels unexplained.
- **Limitations:** Only 13 full weeks.
- **Economic interpretation (interpretation, not proven by data):** Possibly calendar-driven (month/quarter end).
- **Visualisation:** daily bars · **Presentation:** Yes

### P2 — IBAN prefix always equals BIC country; IBAN used only by IBAN-country banks
- **Hypothesis / why it matters:** Account format follows the IBAN registry by country.
- **Fields:** ORDERING/BENEFICIARY_ACCOUNT, *_TOKENS
- **Sample size:** 10,000,000 rows (splits ≈5M each) unless stated
- **Explicit rule:** Account is IBAN-formatted only for banks in IBAN countries; IBAN country prefix = BIC country; one IBAN length per country
- **Logic:** `prefix match; per-country IBAN share bimodality; distinct IBAN lengths per country`
- **Method:** Prefix match, per-country IBAN share bimodality.
- **Acceptance criterion:** prefix match == 1; countries with 0<share<0.5 == 0
- **Result:** PASS — o_prefix=1; b_prefix=1; countries_ambiguous=0
- **Confidence:** High
- **Counterexamples / exceptions:** IBAN countries still use local formats ~8%.
- **Limitations:** -
- **Economic interpretation (interpretation, not proven by data):** Regulatory account-number standards.
- **Visualisation:** country bars · **Presentation:** Yes

### P4 — Ordering party lives in its bank's country; beneficiary residence is decoupled from its bank
- **Hypothesis / why it matters:** Ordering parties live in their bank's country; beneficiaries do not.
- **Fields:** *_TOKENS country codes, BICs
- **Sample size:** 10,000,000 rows (splits ≈5M each) unless stated
- **Explicit rule:** Ordering address country = ORDERING_BIC8 country; beneficiary address country is drawn independently of BENEFICIARY_BIC8
- **Logic:** `match rates where a <country_code> token exists`
- **Method:** Match rates where country token present (61%).
- **Acceptance criterion:** ordering match == 1, beneficiary match < 0.02 on every split
- **Result:** PASS — o_match=1; b_match=0.009796
- **Confidence:** Medium
- **Counterexamples / exceptions:** -
- **Limitations:** 39% of details carry no country token.
- **Economic interpretation (interpretation, not proven by data):** Generator samples beneficiary residence by population, bank by banking size — a modelling shortcut.
- **Visualisation:** country comparison · **Presentation:** Yes

### P5 — Customer-type mix is a bank attribute: each bank has its own business share of senders and of receivers
- **Hypothesis / why it matters:** Why the business-customer share varies by country.
- **Fields:** ORDERING_TYPE, BENEFICIARY_TYPE, BICs
- **Sample size:** 10,000,000 rows (splits ≈5M each) unless stated
- **Explicit rule:** Each bank has its own business-customer share on the sending side and on the receiving side
- **Logic:** `split-half correlation of bank-level P(type = B)`
- **Method:** Bank-level business share on each side, split-half correlation; within-country dispersion vs binomial.
- **Acceptance criterion:** split-half correlation of bank-level business share > 0.95 on both sides (banks ≥200 rows per half); within-country dispersion ≫ binomial
- **Result:** PASS — sender_split_half_r=0.9945; sender_banks=2412; sender_bank_share_min=0.03201; sender_bank_share_max=1
- **Confidence:** High
- **Counterexamples / exceptions:** Country differences (38–96% senders) are bank mix; dispersion 549× (senders) and 196× (receivers) binomial within countries.
- **Limitations:** Mechanism behind each bank's share (size? country?) not identified.
- **Economic interpretation (interpretation, not proven by data):** Banks specialise: corporate banks vs retail banks serve different customer mixes.
- **Visualisation:** split-half scatter · **Presentation:** Dashboard

### P1b — Beneficiary type independent of ordering type
- **Hypothesis / why it matters:** Receiver type independent of sender type.
- **Fields:** ORDERING_TYPE, BENEFICIARY_TYPE
- **Sample size:** 10,000,000 rows (splits ≈5M each) unless stated
- **Explicit rule:** BENEFICIARY_TYPE is drawn independently of ORDERING_TYPE
- **Logic:** `|P(bB | oB) − P(bB | oC)|`
- **Method:** Conditional shares by split.
- **Acceptance criterion:** |P(bB|oB)-P(bB|oC)| < 0.005
- **Result:** PASS — pB_given_oB=0.2884; pB_given_oC=0.2873; diff=0.001093
- **Confidence:** High
- **Counterexamples / exceptions:** -
- **Limitations:** -
- **Economic interpretation (interpretation, not proven by data):** Independent sampling per side.
- **Visualisation:** - · **Presentation:** Dashboard

### X1 — ROMANCE_SCAM: consumer bursts of 2-8 escalating payments (×~1.5 each)
- **Hypothesis / why it matters:** Romance scams are escalating consumer bursts.
- **Fields:** ANOMALY_TYPE, accounts, amounts, timestamps
- **Sample size:** 10,000,000 rows (splits ≈5M each) unless stated
- **Explicit rule:** ROMANCE_SCAM: consumer → same beneficiary, 2–8 payments minutes apart, each ≈ ×1.5 the previous; all labelled
- **Logic:** `within-series regression slope of ln(amount) on position`
- **Method:** Series reconstruction, within-series log slope, detector precision/recall.
- **Acceptance criterion:** sender C share == 1; within-series ln step in [0.3,0.5]; every series fully labelled
- **Result:** PASS — sender_consumer_share=1; median_ln_step=0.4001; mean_ln_step=0.3903; labelled_share_in_series=1
- **Confidence:** High
- **Counterexamples / exceptions:** Case text says C→C, but receiver type follows base mix (27% B).
- **Limitations:** Timing (minutes apart) is unrealistic vs real grooming over weeks.
- **Economic interpretation (interpretation, not proven by data):** Escalating repeated transfers by a groomed victim.
- **Visualisation:** escalation line · **Presentation:** Yes

### X2 — DUPLICATE_PAYMENT: 2-5 identical copies (amount, path, duration) within 2h; all copies labelled
- **Hypothesis / why it matters:** Duplicates are message replays.
- **Fields:** all fields
- **Sample size:** 10,000,000 rows (splits ≈5M each) unless stated
- **Explicit rule:** DUPLICATE_PAYMENT: 2–5 identical copies (sender, beneficiary, amount, path, duration) within ≤ 2 h; every copy labelled
- **Logic:** `GROUP BY (oacc, bacc, amt): distinct path = distinct duration = 1; span ≤ 7,043 s`
- **Method:** Exact-key grouping; detector over full data.
- **Acceptance criterion:** every group has 1 path & 1 duration; span ≤ 7200s; sizes ⊂ {2..5}
- **Result:** PASS — groups=185; max_paths=1; max_durations=1; max_span_s=7043
- **Confidence:** High
- **Counterexamples / exceptions:** 5 normal groups and 10 romance groups also match the key.
- **Limitations:** Labelling convention: every copy is labelled, including the original.
- **Economic interpretation (interpretation, not proven by data):** Back-office race condition resends the same instruction.
- **Visualisation:** group sizes · **Presentation:** Yes

### X3 — FAT_FINGER_MISTAKE: amount ×100 or ÷100 relative to expectation
- **Hypothesis / why it matters:** Fat-finger amounts are scaled by 10^±2.
- **Fields:** USD_AMOUNT
- **Sample size:** 10,000,000 rows (splits ≈5M each) unless stated
- **Explicit rule:** FAT_FINGER_MISTAKE: amount × 100 (≈77%) or ÷ 100 (≈23%)
- **Logic:** `2-component Gaussian mixture on log10(amount / expected)`
- **Method:** Residual vs country+segment expectation, 2-component Gaussian mixture.
- **Acceptance criterion:** bimodal log10 residual: both modes within ±0.6 of ±2; up share in [0.65,0.9]
- **Result:** PASS — mode_low=-1.95; mode_high=2.435; component_sd=1.139; up_share=0.7727
- **Confidence:** Medium
- **Counterexamples / exceptions:** Cannot separate ×100 from ×1000 per row (residual sd ≈ 0.9 log10).
- **Limitations:** Expectation model has its own noise.
- **Economic interpretation (interpretation, not proven by data):** Comma/dot decimal-separator confusion.
- **Visualisation:** residual histogram · **Presentation:** Yes

### X4 — CEO & ACCOUNT_REPLACEMENT scams pay mule accounts at small banks
- **Hypothesis / why it matters:** CEO/account-replacement scams target mule accounts.
- **Fields:** BENEFICIARY_ACCOUNT, BENEFICIARY_BIC8
- **Sample size:** 10,000,000 rows (splits ≈5M each) unless stated
- **Explicit rule:** CEO / ACCOUNT_REPLACEMENT scams pay accounts that receive only anomalous money (mules) at small, often manual banks
- **Logic:** `share of beneficiary accounts with zero normal inflows; bank size and STP comparison`
- **Method:** Share of beneficiary accounts that only receive anomalous money; bank size/STP comparison; stratified duration.
- **Acceptance criterion:** share of beneficiary accounts receiving only anomalous money > 0.35 (vs < 0.25 for error types)
- **Result:** PASS — ROMANCE_SCAM=0.603; ACCOUNT_REPLACEMENT_SCAM=0.47; CEO_SCAM=0.4836; CUSTOMER_RECALL=0.183
- **Confidence:** Medium
- **Counterexamples / exceptions:** No name-swap evidence for account replacement (1/649).
- **Limitations:** Mule definition is data-driven.
- **Economic interpretation (interpretation, not proven by data):** Fraud proceeds concentrate in mule accounts at weaker-control banks.
- **Visualisation:** mule share bars · **Presentation:** Yes

### X5 — CUSTOMER_RECALL has no observable signature (negative result)
- **Hypothesis / why it matters:** CUSTOMER_RECALL has a signature.
- **Fields:** all
- **Sample size:** 10,000,000 rows (splits ≈5M each) unless stated
- **Explicit rule:** CUSTOMER_RECALL rows are statistically indistinguishable from normal rows on all tested features
- **Logic:** `10 two-proportion z-tests + Mann–Whitney on amount residual; Bonferroni`
- **Method:** 10 two-proportion z-tests + Mann-Whitney, Bonferroni.
- **Acceptance criterion:** no feature differs from normal after Bonferroni (α=0.05/m)
- **Result:** PASS — weekend={'recall': 0.09779179810725552, 'normal': 0.11184275703557912, 'z': -0.7937554721582865, 'p': 0.42733779958172613, 'p_bonf': 1}; domestic={'recall': 0.05362776025236593, 'normal': 0.07113223524401195, 'z': -1.2124631466829425, 'p': 0.22533514151605205, 'p_bonf': 1}; gap={'recall': 0.11041009463722397, 'normal': 0.076720050067077, 'z': 2.2537725009717793, 'p': 0.024210483620425945, 'p_bonf': 0.24210483620425943}; ord_B={'recall': 0.7760252365930599, 'normal': 0.7876368183549395, 'z': -0.5054967868810158, 'p': 0.613209954662462, 'p_bonf': 1}
- **Confidence:** Low
- **Counterexamples / exceptions:** Path-gap share nominal p=0.024, not significant after correction.
- **Limitations:** Label not documented in official materials.
- **Economic interpretation (interpretation, not proven by data):** A recall happens after sending, so message fields cannot reveal it.
- **Visualisation:** test table · **Presentation:** Yes (negative result)

### X6 — Anomaly label is independent of routing type
- **Hypothesis / why it matters:** Anomaly label independent of routing type.
- **Fields:** ANOMALY_TYPE, TRANSACTION_TYPE_CODE
- **Sample size:** 10,000,000 rows (splits ≈5M each) unless stated
- **Explicit rule:** ANOMALY_TYPE is assigned independently of TRANSACTION_TYPE
- **Logic:** `χ² + Cramér's V on the 7 × 3 table`
- **Method:** Chi-square + Cramér's V.
- **Acceptance criterion:** Cramér's V(anomaly × ttype) < 0.01
- **Result:** PASS — chi2=204.3; p=4.307e-37; dof=12; cramers_v=0.003196
- **Confidence:** High
- **Counterexamples / exceptions:** -
- **Limitations:** -
- **Economic interpretation (interpretation, not proven by data):** Anomalies injected after routing is generated.
- **Visualisation:** - · **Presentation:** Dashboard

### F1 — Fingerprint: USD-denominated amounts keep whole-unit roundness (≈39% .00) while converted currencies have uniform cents (≈1%)
- **Hypothesis / why it matters:** How amounts were produced: drawn in USD, or drawn in the payment currency and converted?
- **Fields:** USD_AMOUNT, CURRENCY_CODE
- **Sample size:** 10,000,000 rows (splits ≈5M each) unless stated
- **Explicit rule:** USD-denominated amounts keep whole-unit roundness (≈39% end .00, ≈16% multiples of 100); non-USD amounts have uniform cents (≈1%)
- **Logic:** `share of round(amount·100) mod 100 = 0 by currency = USD; fixed-rate search for EUR/GBP/CHF (negative)`
- **Method:** Cents-digit distribution by currency; multiples of 100; search for a fixed FX rate that restores round originals (EUR/GBP/CHF).
- **Acceptance criterion:** USD whole-unit share > 0.30 and non-USD share in [0.008,0.013] on every split
- **Result:** PASS — usd_whole_share=0.3864; non_usd_whole_share=0.009885; n_usd=1.702e+06
- **Confidence:** High
- **Counterexamples / exceptions:** No single fixed rate restores round originals for EUR/GBP/CHF (best near-integer share ≈2% vs 1.2% baseline) — conversion mechanism not identified.
- **Limitations:** Roundness of non-USD originals cannot be observed after conversion.
- **Economic interpretation (interpretation, not proven by data):** Invoices are typically issued in round units of the invoicing currency; USD is the only currency that needs no conversion to USD.
- **Visualisation:** cents by currency · **Presentation:** Yes

### T4b — Weekly volume levels are piecewise-constant with every change point on a Monday (week boundary)
- **Hypothesis / why it matters:** Do weekly levels change at random times or at week boundaries?
- **Fields:** EPOCH_SECONDS
- **Sample size:** 10,000,000 rows (splits ≈5M each) unless stated
- **Explicit rule:** level(week) is piecewise-constant and changes only at week boundaries (Mondays)
- **Logic:** `binary segmentation of weekday-normalised log volume with BIC penalty 2·ln(n)·σ̂²`
- **Method:** Binary segmentation with BIC penalty on weekday-normalised log daily volume (91 full days); residual normality.
- **Acceptance criterion:** binary segmentation (BIC penalty) on weekday-normalised log volume: ≥1 change point, 100% on Mondays, residual sd < 0.03
- **Result:** PASS — change_points=10; share_on_monday=1; residual_sd_log=0.01831; segments=11
- **Confidence:** High
- **Counterexamples / exceptions:** Several adjacent weeks share a level (segments of 1–3 weeks).
- **Limitations:** 13 weeks only; cause of the levels still open (T4).
- **Economic interpretation (interpretation, not proven by data):** Volume plans are set per week (business calendars), not per day.
- **Visualisation:** segmented series · **Presentation:** Yes

### G3 — Intermediaries drawn i.i.d. with replacement ∝ bank size — predicts the path revisit (loop) rate
- **Hypothesis / why it matters:** Loops in paths (a bank visited twice) are a by-product of independent size-weighted intermediary draws.
- **Fields:** BIC8_PATH
- **Sample size:** 10,000,000 rows (splits ≈5M each) unless stated
- **Explicit rule:** Intermediaries are drawn i.i.d. with replacement, P(b) ∝ size(b)^β with β ≈ 1
- **Logic:** `P(revisit | K) = 1 − Π_{j=1}^{K−1}(1 − j·Σ_b p_b²)  · src/rules.py g3`
- **Method:** Birthday-problem prediction from the intermediary collision probability Σp²; size exponent by log-log fit; per split.
- **Acceptance criterion:** size exponent β∈[0.9,1.1]; predicted vs observed intermediary-repeat rate within 10% relative for pc 4–8 on every split
- **Result:** PASS — max_rel_err=0.0306; pc7_obs=0.05701; pc6_obs=0.03514; pc4_obs=0.006031
- **Confidence:** High
- **Counterexamples / exceptions:** pc=8–9 within 3%; no residual excess of loops.
- **Limitations:** Assumes the same size distribution at every position.
- **Economic interpretation (interpretation, not proven by data):** Hubs appear repeatedly because the generator samples correspondents with replacement — real routes would avoid loops.
- **Visualisation:** obs vs predicted loop rate · **Presentation:** Yes

### G1 — Sender and receiver banks are NOT paired independently (directional affinities) — independence rejected
- **Hypothesis / why it matters:** Sender and receiver banks are paired independently (configuration model).
- **Fields:** ORDERING_BIC8, BENEFICIARY_BIC8
- **Sample size:** 10,000,000 rows (splits ≈5M each) unless stated
- **Explicit rule:** Sender and receiver banks are NOT paired independently; pair counts deviate from n_i·n_j/N even within country pairs and unique relationships
- **Logic:** `Pearson χ²/dof of O vs E = n_o·n_b/N over pairs with E ≥ 5`
- **Method:** Pearson χ²/dof of pair counts vs product-of-margins expectation, on raw payments, unique account relationships and within country pairs; affinity symmetry.
- **Acceptance criterion:** χ²/dof > 10 for raw pairs, unique relationships and within country pairs; country affinity symmetry r < 0.3
- **Result:** PASS — chi2_dof_raw=358.2; chi2_dof_unique=125.4; chi2_dof_within_country=286.6; domestic_affinity=1.201
- **Confidence:** Low
- **Counterexamples / exceptions:** Independence REJECTED in all three; domestic pairs 1.2× expected; affinities directional (r = 0.11).
- **Limitations:** Mechanism of the affinity (bank-level preference lists?) not identified.
- **Economic interpretation (interpretation, not proven by data):** Real correspondent networks are relationship-driven; the generator encodes directional bank-to-bank preferences.
- **Visualisation:** pair O/E scatter · **Presentation:** Yes (partial result)

### A3 — Within-country log-amount residual is Normal (lognormal amounts, no power-law tail)
- **Hypothesis / why it matters:** Amounts are lognormal, not heavy-tailed power law.
- **Fields:** USD_AMOUNT
- **Sample size:** 10,000,000 rows (splits ≈5M each) unless stated
- **Explicit rule:** Within-country residual of ln(amount) is Normal → amounts lognormal; no power-law tail
- **Logic:** `skew, excess kurtosis, KS D vs N(0,1); Hill α(k) drift; model exceedances`
- **Method:** Within-country residual moments, KS vs Normal, Hill estimator drift, model-implied exceedances $100k–$1bn.
- **Acceptance criterion:** |skew|<0.05, |excess kurtosis|<0.1, KS D<0.01 on every split; Hill α drifts (>0.5 between k=100 and k=100k)
- **Result:** PASS — sd=2.08; skew=-0.02395; excess_kurtosis=0.006827; ks_D=0.003462
- **Confidence:** High
- **Counterexamples / exceptions:** Exceedance ratio 0.86 at $100M (132 vs 154 predicted, z≈−1.7).
- **Limitations:** Fat-finger rows excluded; top 1,000 amounts are 26.5% fat finger.
- **Economic interpretation (interpretation, not proven by data):** Payment sizes multiply many factors (firm size, invoice size) → lognormal; extreme tickets come from errors, not a fat natural tail.
- **Visualisation:** Q-Q / Hill plot · **Presentation:** Dashboard

### D3 — Manual processing step ≈ Gamma(shape≈2, scale≈820 s); fast step pair ≈ Gamma(3, 8.7 s)
- **Hypothesis / why it matters:** The manual step has a specific distribution.
- **Fields:** TOTAL_DURATION
- **Sample size:** 10,000,000 rows (splits ≈5M each) unless stated
- **Explicit rule:** Manual step ~ Gamma(k ≈ 2, θ ≈ 817 s); two fast steps ~ Gamma(k ≈ 3.1, θ ≈ 8.7 s)
- **Logic:** `MLE gamma fit (loc = 0) vs lognormal; KS D`
- **Method:** Gamma vs lognormal MLE fits with KS on manual-step and fast-pair durations.
- **Acceptance criterion:** manual-step gamma shape∈[1.6,2.5] and KS D<0.05 better than lognormal; fast-pair gamma shape∈[2.5,3.6], KS D<0.05
- **Result:** PASS — manual_shape=2.045; manual_scale_s=817.1; manual_ks_gamma=0.02321; manual_ks_lognormal=0.06561
- **Confidence:** Medium
- **Counterexamples / exceptions:** Manual tail up to 21,649 s on multi-hop routes.
- **Limitations:** Fitted on pc=2 rows with exactly one slow bank.
- **Economic interpretation (interpretation, not proven by data):** Manual handling ≈ two exponential stages (queue + review) → Gamma(2).
- **Visualisation:** fitted density · **Presentation:** Dashboard

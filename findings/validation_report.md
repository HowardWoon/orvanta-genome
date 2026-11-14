# Validation report

Generated 2026-11-14T17:00:29 · runtime 521.7 s · 10,000,000 rows.

Splits: **full**; **half_0 / half_1** = random halves by `hash(rid) % 2` (independent-subset check); **P1 / P2** = before / after 2023-06-15 (temporal check). A rule passes only if its criterion holds on every split it reports. D1 is a true out-of-sample test: bank speed classes are learned on half_0 and evaluated on half_1.

| ID | Type | Rule | Criterion | Status |
|---|---|---|---|---|
| R6 | A | PARTICIPANT_COUNT = number of known BICs in BIC8_PATH | share_exact == 1 | **PASS** |
| R7 | A | CONTINUITY_QFLAG = 'N' iff path contains '...' | share_exact == 1 | **PASS** |
| R5 | B | Path endpoints differ from ORDERING/BENEFICIARY_BIC8 independently with p≈0.05 each | first & last mismatch in [0.045,0.055] and joint/product ratio in [0.9,1.1] | **PASS** |
| R5b | E | On endpoint mismatch, currency follows the path's first bank; account/IBAN follows ORDERING_BIC8 | home-ccy share via path[1] > 0.85 and via ORDERING_BIC8 < 0.25; IBAN prefix = ORDERING_BIC8 country == 1 | **PASS** |
| R1 | B | Intermediaries K = floor(Exp(1)): P(K=k) = (1-1/e)e^-k | MLE continuation q within ±0.005 of 1/e and Cohen's w < 0.01 on every split | **PASS** |
| R2 | C | Covered vs Indirect is a per-sending-bank propensity (cover-prone banks ≈61%, others ≈7%, out of sample), independent of route length | Cramér's V(type×K) < 0.01 on every split; out-of-sample: banks classed as cover banks on half_0 send >50% Covered on half_1, others <10% | **PASS** |
| P5 | C | Customer-type mix is a bank attribute: each bank has its own business share of senders and of receivers | split-half correlation of bank-level business share > 0.95 on both sides (banks ≥200 rows per half); within-country dispersion ≫ binomial | **PASS** |
| R4 | B | Each link hidden with p=0.05: P(N | pc) = 1-0.95^(pc-1) | max |obs-pred| over pc 2..7 < 0.006 | **PASS** |
| R3 | C | Intermediaries chosen in proportion to bank size, not by payment currency | corr(log intermediary uses, log payments sent) > 0.9; share in payment-currency zone < 0.25 | **PASS** |
| C2 | A | FX count = adjacent known-BIC pairs with different home currencies | share_exact >= 0.99999 | **PASS** |
| C1 | C | Payment currency = home currency of the instructing (first-path) bank ~93% | share in [0.91,0.95] on every split; per-country share range reported | **PASS** |
| A1 | C | ln(amount) = 6 + 2·[O=B] + 2·[B=B], σ≈2.28 (no interaction) | intercept∈[5.9,6.2], both effects∈[1.85,2.15], |interaction|<0.1, σ spread across cells <0.03 | **PASS** |
| A2 | C | Ordering-country effect replicates across independent halves (beneficiary country ≈ no effect) | corr(country effect half_0, half_1) > 0.95; sd(ordering effects) > 3×sd(beneficiary effects) | **PASS** |
| D1 | E | Duration = sum of per-bank steps; bank speed class learned on half_0 predicts half_1 | out-of-sample: fast→fast slow-share < 0.2, any slow bank > 0.9, median(slow,slow)/median(one slow) in [1.6,2.4] | **PASS** |
| D2 | C | Manual (slow) processing is a bank attribute: hour/weekday/amount effects vanish once bank fixed effects are removed | after two-way (sender bank, receiver bank) demeaning among fast-fast pairs: residual range across UTC hours < 0.015, weekdays < 0.015, |corr with ln amount| < 0.02 | **PASS** |
| T1 | C | Activity follows the instructing bank's local clock (fixed offsets) | night share (01-05h local) < 0.06 on every split vs > 0.15 with UTC | **PASS** |
| T3 | B | One weekday shape for all countries (local weekday) | max deviation of any country's weekday share from pooled share < 0.01 (countries ≥50k rows) | **PASS** |
| T4 | B | Weekly volume multiplier is global (shared by all countries) | min corr of weekly volume between top-10 countries and the total > 0.98 | **PASS** |
| P2 | A | IBAN prefix always equals BIC country; IBAN used only by IBAN-country banks | prefix match == 1; countries with 0<share<0.5 == 0 | **PASS** |
| P4 | C | Ordering party lives in its bank's country; beneficiary residence is decoupled from its bank | ordering match == 1, beneficiary match < 0.02 on every split | **PASS** |
| P1b | B | Beneficiary type independent of ordering type | |P(bB|oB)-P(bB|oC)| < 0.005 | **PASS** |
| X1 | E | ROMANCE_SCAM: consumer bursts of 2-8 escalating payments (×~1.5 each) | sender C share == 1; within-series ln step in [0.3,0.5]; every series fully labelled | **PASS** |
| X2 | A | DUPLICATE_PAYMENT: 2-5 identical copies (amount, path, duration) within 2h; all copies labelled | every group has 1 path & 1 duration; span ≤ 7200s; sizes ⊂ {2..5} | **PASS** |
| X3 | C | FAT_FINGER_MISTAKE: amount ×100 or ÷100 relative to expectation | bimodal log10 residual: both modes within ±0.6 of ±2; up share in [0.65,0.9] | **PASS** |
| X4 | C | CEO & ACCOUNT_REPLACEMENT scams pay mule accounts at small banks | share of beneficiary accounts receiving only anomalous money > 0.35 (vs < 0.25 for error types) | **PASS** |
| X5 | B | CUSTOMER_RECALL has no observable signature (negative result) | no feature differs from normal after Bonferroni (α=0.05/m) | **PASS** |
| X6 | B | Anomaly label is independent of routing type | Cramér's V(anomaly × ttype) < 0.01 | **PASS** |
| G3 | E | Intermediaries drawn i.i.d. with replacement ∝ bank size — predicts the path revisit (loop) rate | size exponent β∈[0.9,1.1]; predicted vs observed intermediary-repeat rate within 10% relative for pc 4–8 on every split | **PASS** |
| G1 | C | Sender and receiver banks are NOT paired independently (directional affinities) — independence rejected | χ²/dof > 10 for raw pairs, unique relationships and within country pairs; country affinity symmetry r < 0.3 | **PASS** |
| A3 | B | Within-country log-amount residual is Normal (lognormal amounts, no power-law tail) | |skew|<0.05, |excess kurtosis|<0.1, KS D<0.01 on every split; Hill α drifts (>0.5 between k=100 and k=100k) | **PASS** |
| D3 | B | Manual processing step ≈ Gamma(shape≈2, scale≈820 s); fast step pair ≈ Gamma(3, 8.7 s) | manual-step gamma shape∈[1.6,2.5] and KS D<0.05 better than lognormal; fast-pair gamma shape∈[2.5,3.6], KS D<0.05 | **PASS** |
| C3 | E | Payment currency is drawn from the currencies on the route: first bank ≈ 95% (direct), receiver bank ≈ 3.8%, +≈2.4 pts per intermediary, outside-route vehicle ≈ 1.3% | ≥98% of payments in a route-bank currency on every split; receiver-only share stable across route lengths (range < 0.006); intermediary-only share rises ≈ linearly per intermediary (slope 0.02–0.035) | **PASS** |
| F1 | D | Fingerprint: USD-denominated amounts keep whole-unit roundness (≈39% .00) while converted currencies have uniform cents (≈1%) | USD whole-unit share > 0.30 and non-USD share in [0.008,0.013] on every split | **PASS** |
| T4b | B | Weekly volume levels are piecewise-constant with every change point on a Monday (week boundary) | binary segmentation (BIC penalty) on weekday-normalised log volume: ≥1 change point, 100% on Mondays, residual sd < 0.03 | **PASS** |

Two-implementation check (pure Python `src/rulelib.py` vs dataset fields, 200,000-row random sample): R6 1.000000, R7 1.000000, C2 1.000000.

## Metrics by split

### R6 — PARTICIPANT_COUNT = number of known BICs in BIC8_PATH  (PASS)
| split | share_exact | n |
|---|---|---|
| P1 | 1 | 4.651e+06 |
| P2 | 1 | 5.349e+06 |
| full | 1 | 1e+07 |
| half_0 | 1 | 5.004e+06 |
| half_1 | 1 | 4.996e+06 |

### R7 — CONTINUITY_QFLAG = 'N' iff path contains '...'  (PASS)
| split | share_exact | n |
|---|---|---|
| P1 | 1 | 4.651e+06 |
| P2 | 1 | 5.349e+06 |
| full | 1 | 1e+07 |
| half_0 | 1 | 5.004e+06 |
| half_1 | 1 | 4.996e+06 |

### R5 — Path endpoints differ from ORDERING/BENEFICIARY_BIC8 independently with p≈0.05 each  (PASS)
| split | p_first | p_last | p_both | indep_ratio |
|---|---|---|---|---|
| P1 | 0.04989 | 0.0499 | 0.002475 | 0.9943 |
| P2 | 0.04979 | 0.04995 | 0.002464 | 0.9906 |
| full | 0.04984 | 0.04993 | 0.002469 | 0.9924 |
| half_0 | 0.04986 | 0.05002 | 0.002468 | 0.9897 |
| half_1 | 0.04982 | 0.04983 | 0.00247 | 0.995 |

### R5b — On endpoint mismatch, currency follows the path's first bank; account/IBAN follows ORDERING_BIC8  (PASS)
| split | ccy_follows_path_first | ccy_follows_obic | iban_follows_obic | n |
|---|---|---|---|---|
| P1 | 0.9347 | 0.1381 | 1 | 2.321e+05 |
| P2 | 0.9348 | 0.1391 | 1 | 2.663e+05 |
| full | 0.9348 | 0.1386 | 1 | 4.984e+05 |
| half_0 | 0.935 | 0.1383 | 1 | 2.495e+05 |
| half_1 | 0.9345 | 0.1389 | 1 | 2.489e+05 |

### R1 — Intermediaries K = floor(Exp(1)): P(K=k) = (1-1/e)e^-k  (PASS)
| split | n | q_mle | inv_e | cohen_w | chi2 | p_direct | ratio_1 | ratio_2 | ratio_3 | ratio_4 |
|---|---|---|---|---|---|---|---|---|---|---|
| P1 | 4.651e+06 | 0.3677 | 0.3679 | 0.0009454 | 4.157 | 0.6323 | 0.3676 | 0.3686 | 0.3661 | 0.3678 |
| P2 | 5.349e+06 | 0.3677 | 0.3679 | 0.0006544 | 2.291 | 0.6324 | 0.3676 | 0.3676 | 0.368 | 0.369 |
| full | 1e+07 | 0.3677 | 0.3679 | 0.0005785 | 3.347 | 0.6323 | 0.3676 | 0.368 | 0.3671 | 0.3685 |
| half_0 | 5.004e+06 | 0.3677 | 0.3679 | 0.001323 | 8.752 | 0.6323 | 0.3676 | 0.3686 | 0.3657 | 0.3694 |
| half_1 | 4.996e+06 | 0.3678 | 0.3679 | 0.0008393 | 3.519 | 0.6324 | 0.3675 | 0.3674 | 0.3685 | 0.3675 |

### R2 — Covered vs Indirect is a per-sending-bank propensity (cover-prone banks ≈61%, others ≈7%, out of sample), independent of route length  (PASS)
| split | n | pooled_covered_share | cramers_v_vs_K | share_k4 | share_k1 | share_k3 | share_k2 | share_k5 | oos_cover_banks_share | oos_other_banks_share | cover_banks | other_banks | country_share_min | country_share_max |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| P1 | 1.71e+06 | 0.1134 | 0.0007086 | 0.1139 | 0.1134 | 0.1139 | 0.1132 | 0.1139 |  |  |  |  |  |  |
| P2 | 1.967e+06 | 0.1129 | 0.0006585 | 0.1123 | 0.113 | 0.1128 | 0.1126 | 0.1137 |  |  |  |  |  |  |
| full | 3.677e+06 | 0.1131 | 0.000513 | 0.1131 | 0.1132 | 0.1133 | 0.1129 | 0.1138 | 0.6142 | 0.06704 | 93 | 2061 | 0.03075 | 0.5037 |
| half_0 | 1.84e+06 | 0.1129 | 0.001319 | 0.1111 | 0.113 | 0.1134 | 0.1126 | 0.1118 |  |  |  |  |  |  |
| half_1 | 1.837e+06 | 0.1134 | 0.001378 | 0.115 | 0.1133 | 0.1133 | 0.1132 | 0.1158 |  |  |  |  |  |  |

### P5 — Customer-type mix is a bank attribute: each bank has its own business share of senders and of receivers  (PASS)
| split | sender_split_half_r | sender_banks | sender_bank_share_min | sender_bank_share_max | receiver_split_half_r | receiver_banks | receiver_bank_share_min | receiver_bank_share_max |
|---|---|---|---|---|---|---|---|---|
| full | 0.9945 | 2412 | 0.03201 | 1 | 0.9867 | 2189 | 0.02751 | 0.8639 |

### R4 — Each link hidden with p=0.05: P(N | pc) = 1-0.95^(pc-1)  (PASS)
| split | max_abs_dev | p_link_mle |
|---|---|---|
| P1 | 0.004334 | 0.04989 |
| P2 | 0.004394 | 0.04993 |
| full | 0.004366 | 0.04991 |
| half_0 | 0.005678 | 0.04995 |
| half_1 | 0.003047 | 0.04987 |

### R3 — Intermediaries chosen in proportion to bank size, not by payment currency  (PASS)
| split | corr_log | share_in_currency_zone |
|---|---|---|
| full | 0.9423 | 0.173 |

### C2 — FX count = adjacent known-BIC pairs with different home currencies  (PASS)
| split | share_exact | n | exceptions | alt_distinct |
|---|---|---|---|---|
| P1 | 1 | 4.651e+06 | 2 | 0.9169 |
| P2 | 1 | 5.349e+06 | 0 | 0.9168 |
| full | 1 | 1e+07 | 2 | 0.9168 |
| half_0 | 1 | 5.004e+06 | 0 | 0.9166 |
| half_1 | 1 | 4.996e+06 | 2 | 0.917 |

### C1 — Payment currency = home currency of the instructing (first-path) bank ~93%  (PASS)
| split | home_share | n |
|---|---|---|
| P1 | 0.9342 | 4.651e+06 |
| P2 | 0.9341 | 5.349e+06 |
| full | 0.9342 | 1e+07 |
| half_0 | 0.9343 | 5.004e+06 |
| half_1 | 0.934 | 4.996e+06 |

### A1 — ln(amount) = 6 + 2·[O=B] + 2·[B=B], σ≈2.28 (no interaction)  (PASS)
| split | intercept | effect_ordering_B | effect_beneficiary_B | interaction | sd_min | sd_max |
|---|---|---|---|---|---|---|
| P1 | 6.063 | 1.929 | 1.964 | 0.04263 | 2.284 | 2.289 |
| P2 | 6.062 | 1.934 | 1.966 | 0.0356 | 2.284 | 2.295 |
| full | 6.062 | 1.932 | 1.965 | 0.03887 | 2.284 | 2.292 |
| half_0 | 6.064 | 1.929 | 1.961 | 0.04309 | 2.284 | 2.292 |
| half_1 | 6.061 | 1.935 | 1.969 | 0.03464 | 2.281 | 2.292 |

### A2 — Ordering-country effect replicates across independent halves (beneficiary country ≈ no effect)  (PASS)
| split | split_half_corr | sd_ordering | sd_beneficiary | countries |
|---|---|---|---|---|
| full | 0.9998 | 1.091 | 0.2321 | 62 |

### D1 — Duration = sum of per-bank steps; bank speed class learned on half_0 predicts half_1  (PASS)
| split | n | slow_share | median_s | value |
|---|---|---|---|---|
| fast->fast | 2.111e+06 | 0.1342 | 27 |  |
| fast->slow | 3.493e+05 | 0.9708 | 1412 |  |
| slow->fast | 4.939e+05 | 0.9618 | 1387 |  |
| slow->slow | 1.417e+05 | 0.9993 | 2641 |  |
| additivity_ratio |  |  |  | 1.887 |

### D2 — Manual (slow) processing is a bank attribute: hour/weekday/amount effects vanish once bank fixed effects are removed  (PASS)
| split | raw_range_by_hour | fe_range_by_hour | fe_range_by_weekday | fe_corr_ln_amount |
|---|---|---|---|---|
| full | 0.03688 | 0.002913 | 0.001452 | -0.0008232 |

### T1 — Activity follows the instructing bank's local clock (fixed offsets)  (PASS)
| split | night_local | night_utc |
|---|---|---|
| P1 | 0.04583 | 0.1225 |
| P2 | 0.04604 | 0.1247 |
| full | 0.04594 | 0.1237 |
| half_0 | 0.04593 | 0.1238 |
| half_1 | 0.04596 | 0.1236 |

### T3 — One weekday shape for all countries (local weekday)  (PASS)
| split | max_dev | countries |
|---|---|---|
| full | 0.003874 | 35 |

### T4 — Weekly volume multiplier is global (shared by all countries)  (PASS)
| split | min_corr |
|---|---|
| full | 0.9992 |

### P2 — IBAN prefix always equals BIC country; IBAN used only by IBAN-country banks  (PASS)
| split | o_prefix | b_prefix | countries_ambiguous |
|---|---|---|---|
| P1 | 1 | 1 |  |
| P2 | 1 | 1 |  |
| full | 1 | 1 | 0 |
| half_0 | 1 | 1 |  |
| half_1 | 1 | 1 |  |

### P4 — Ordering party lives in its bank's country; beneficiary residence is decoupled from its bank  (PASS)
| split | o_match | b_match |
|---|---|---|
| P1 | 1 | 0.009813 |
| P2 | 1 | 0.009781 |
| full | 1 | 0.009796 |
| half_0 | 1 | 0.009727 |
| half_1 | 1 | 0.009865 |

### P1b — Beneficiary type independent of ordering type  (PASS)
| split | pB_given_oB | pB_given_oC | diff |
|---|---|---|---|
| P1 | 0.2883 | 0.2876 | 0.0007233 |
| P2 | 0.2885 | 0.2871 | 0.001414 |
| full | 0.2884 | 0.2873 | 0.001093 |
| half_0 | 0.2884 | 0.287 | 0.001357 |
| half_1 | 0.2884 | 0.2876 | 0.0008283 |

### X1 — ROMANCE_SCAM: consumer bursts of 2-8 escalating payments (×~1.5 each)  (PASS)
| split | sender_consumer_share | median_ln_step | mean_ln_step | labelled_share_in_series | series |
|---|---|---|---|---|---|
| full | 1 | 0.4001 | 0.3903 | 1 | 500 |

### X2 — DUPLICATE_PAYMENT: 2-5 identical copies (amount, path, duration) within 2h; all copies labelled  (PASS)
| split | groups | max_paths | max_durations | max_span_s | min_size | max_size |
|---|---|---|---|---|---|---|
| full | 185 | 1 | 1 | 7043 | 2 | 5 |

### X3 — FAT_FINGER_MISTAKE: amount ×100 or ÷100 relative to expectation  (PASS)
| split | mode_low | mode_high | component_sd | up_share | n |
|---|---|---|---|---|---|
| full | -1.95 | 2.435 | 1.139 | 0.7727 | 1940 |

### X4 — CEO & ACCOUNT_REPLACEMENT scams pay mule accounts at small banks  (PASS)
| split | ROMANCE_SCAM | ACCOUNT_REPLACEMENT_SCAM | CEO_SCAM | CUSTOMER_RECALL | FAT_FINGER_MISTAKE | DUPLICATE_PAYMENT |
|---|---|---|---|---|---|---|
| full | 0.603 | 0.47 | 0.4836 | 0.183 | 0.2057 | 0.1929 |

### X5 — CUSTOMER_RECALL has no observable signature (negative result)  (PASS)
| split | recall | normal | z | p | p_bonf |
|---|---|---|---|---|---|
| weekend | 0.09779 | 0.1118 | -0.7938 | 0.4273 | 1 |
| domestic | 0.05363 | 0.07113 | -1.212 | 0.2253 | 1 |
| gap | 0.1104 | 0.07672 | 2.254 | 0.02421 | 0.2421 |
| ord_B | 0.776 | 0.7876 | -0.5055 | 0.6132 | 1 |
| ben_B | 0.2681 | 0.2882 | -0.7873 | 0.4311 | 1 |
| direct | 0.5899 | 0.6323 | -1.567 | 0.1172 | 1 |
| slow | 0.4637 | 0.4604 | 0.1186 | 0.9056 | 1 |
| fx0 | 0.1009 | 0.1087 | -0.4427 | 0.658 | 1 |
| iban_b | 0.5142 | 0.4978 | 0.5856 | 0.5581 | 1 |
| struct_o | 0.1546 | 0.1553 | -0.03373 | 0.9731 | 1 |
| amount_resid_mwu |  |  |  | 0.8254 | 1 |

### X6 — Anomaly label is independent of routing type  (PASS)
| split | chi2 | p | dof | cramers_v |
|---|---|---|---|---|
| full | 204.3 | 4.307e-37 | 12 | 0.003196 |

### G3 — Intermediaries drawn i.i.d. with replacement ∝ bank size — predicts the path revisit (loop) rate  (PASS)
| split | max_rel_err | pc4_obs | pc8_obs | pc7_obs | pc5_obs | pc6_obs | pc4_pred | pc8_pred | pc7_pred | pc5_pred | pc6_pred | beta | collision_prob |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| P1 | 0.06166 | 0.005959 | 0.08222 | 0.05677 | 0.01722 | 0.03345 | 0.006006 | 0.08708 | 0.05881 | 0.01795 | 0.03564 |  |  |
| P2 | 0.0271 | 0.006094 | 0.08685 | 0.05722 | 0.01771 | 0.03661 | 0.006006 | 0.08708 | 0.05881 | 0.01795 | 0.03564 |  |  |
| full | 0.0306 | 0.006031 | 0.08468 | 0.05701 | 0.01749 | 0.03514 | 0.006006 | 0.08708 | 0.05881 | 0.01795 | 0.03564 | 0.9807 | 0.006006 |
| half_0 | 0.05183 | 0.006057 | 0.08551 | 0.05871 | 0.01702 | 0.03522 | 0.006006 | 0.08708 | 0.05881 | 0.01795 | 0.03564 |  |  |
| half_1 | 0.05951 | 0.006005 | 0.08388 | 0.05531 | 0.01795 | 0.03506 | 0.006006 | 0.08708 | 0.05881 | 0.01795 | 0.03564 |  |  |

### G1 — Sender and receiver banks are NOT paired independently (directional affinities) — independence rejected  (PASS)
| split | chi2_dof_raw | chi2_dof_unique | chi2_dof_within_country | domestic_affinity | affinity_symmetry_r | country_cramers_v |
|---|---|---|---|---|---|---|
| full | 358.2 | 125.4 | 286.6 | 1.201 | 0.1056 | 0.1225 |

### A3 — Within-country log-amount residual is Normal (lognormal amounts, no power-law tail)  (PASS)
| split | sd | skew | excess_kurtosis | ks_D | hill_alpha_k100 | hill_alpha_k100000 |
|---|---|---|---|---|---|---|
| full | 2.08 | -0.02395 | 0.006827 | 0.003462 | 2.209 | 1.212 |
| half_0 | 2.081 | -0.01987 | -0.02221 | 0.003673 |  |  |
| half_1 | 2.077 | -0.02831 | 0.03694 | 0.003105 |  |  |
| P1 | 2.087 | -0.02697 | 0.002299 | 0.002898 |  |  |
| P2 | 2.072 | -0.02074 | 0.008869 | 0.004458 |  |  |

### D3 — Manual processing step ≈ Gamma(shape≈2, scale≈820 s); fast step pair ≈ Gamma(3, 8.7 s)  (PASS)
| split | manual_shape | manual_scale_s | manual_ks_gamma | manual_ks_lognormal | fast_pair_shape | fast_pair_scale_s | fast_ks | n_manual | n_fast |
|---|---|---|---|---|---|---|---|---|---|
| full | 2.045 | 817.1 | 0.02321 | 0.06561 | 3.062 | 8.734 | 0.03105 | 1.018e+05 | 2.229e+05 |

### C3 — Payment currency is drawn from the currencies on the route: first bank ≈ 95% (direct), receiver bank ≈ 3.8%, +≈2.4 pts per intermediary, outside-route vehicle ≈ 1.3%  (PASS)
| split | n_sample | in_route_share | receiver_only_mean | receiver_only_range | intermediary_slope_per_hop | outside_share | first_bank_direct |
|---|---|---|---|---|---|---|---|
| P1 | 1.395e+06 | 0.9873 | 0.03809 | 0.002456 | 0.02447 | 0.01271 | 0.9471 |
| P2 | 1.605e+06 | 0.9872 | 0.03773 | 0.003076 | 0.0242 | 0.01279 | 0.9476 |
| full | 3e+06 | 0.9872 | 0.0379 | 0.002558 | 0.02433 | 0.01275 | 0.9474 |
| half_0 | 1.503e+06 | 0.9873 | 0.03771 | 0.00397 | 0.0244 | 0.01273 | 0.9476 |
| half_1 | 1.497e+06 | 0.9872 | 0.03809 | 0.001597 | 0.02426 | 0.01277 | 0.9472 |

### F1 — Fingerprint: USD-denominated amounts keep whole-unit roundness (≈39% .00) while converted currencies have uniform cents (≈1%)  (PASS)
| split | usd_whole_share | non_usd_whole_share | n_usd |
|---|---|---|---|
| P1 | 0.3867 | 0.01016 | 7.872e+05 |
| P2 | 0.386 | 0.009648 | 9.149e+05 |
| full | 0.3864 | 0.009885 | 1.702e+06 |
| half_0 | 0.3862 | 0.0099 | 8.511e+05 |
| half_1 | 0.3866 | 0.00987 | 8.51e+05 |

### T4b — Weekly volume levels are piecewise-constant with every change point on a Monday (week boundary)  (PASS)
| split | change_points | share_on_monday | residual_sd_log | segments |
|---|---|---|---|---|
| full | 10 | 1 | 0.01831 | 11 |

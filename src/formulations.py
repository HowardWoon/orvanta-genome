"""Explicit rule formulations and computational logic (RECONSTRUCT). Imported by src.register.

FORM[id] = (explicit rule formulation, mathematical / computational logic incl. code pointer)
"""
FORM = {
 "R6": ("PARTICIPANT_COUNT := number of BIC8 entries in BIC8_PATH that are not '...'", "pc = |{b ∈ split(path,';') : b ≠ '...'}|  · rulelib.participant_count"),
 "R7": ("CONTINUITY_QFLAG := 'N' if BIC8_PATH contains '...', else 'Y'", "cont = N ⇔ '...' ∈ split(path)  · rulelib.continuity_flag"),
 "R5": ("With probability 0.05 the first known path BIC is replaced by another bank; independently, with probability 0.05 the last known BIC is replaced", "P(k₁ ≠ ORDERING_BIC8) = P(k_last ≠ BENEFICIARY_BIC8) = 0.05; P(both) = 0.05²"),
 "R5b": ("On replaced rows, CURRENCY_CODE and the local clock follow path[1] (instructing bank); account IBAN and ordering address follow ORDERING_BIC8 (account-servicing bank)", "compare P(cur = home(path[1])) vs P(cur = home(ORDERING_BIC8)) on rows with path[1] ≠ ORDERING_BIC8"),
 "R1": ("Number of intermediaries K ~ ⌊Exp(1)⌋; PARTICIPANT_COUNT = K + 2", "P(K = k) = (1 − e⁻¹)·e⁻ᵏ; MLE q̂ = K̄/(1+K̄); GOF χ² → Cohen's w"),
 "R2": ("Among non-direct routes, TRANSACTION_TYPE = Covered with a sending-bank propensity π_b (cover banks π ≈ 0.6–0.8, others π ≈ 0.05); independent of K", "π_b estimated on half 0; Covered share on half 1 by class; Cramér's V(type × K)"),
 "R4": ("Each link between consecutive known BICs is hidden ('...') independently with p = 0.05; extra '...' per hidden link ~ Geometric(0.05)", "P(cont = N | pc) = 1 − 0.95^(pc−1); p̂ by MLE over pc strata"),
 "R3": ("Intermediaries are sampled with probability proportional to bank activity, not from the payment-currency zone", "corr(log uses_as_intermediary, log payments_sent); share of intermediaries whose home currency = payment currency"),
 "G3": ("Intermediaries are drawn i.i.d. with replacement, P(b) ∝ size(b)^β with β ≈ 1", "P(revisit | K) = 1 − Π_{j=1}^{K−1}(1 − j·Σ_b p_b²)  · src/rules.py g3"),
 "G1": ("Sender and receiver banks are NOT paired independently; pair counts deviate from n_i·n_j/N even within country pairs and unique relationships", "Pearson χ²/dof of O vs E = n_o·n_b/N over pairs with E ≥ 5"),
 "C2": ("CURRENCY_CONVERSION_COUNT := Σ over consecutive known BICs of 1[home_ccy(country(bᵢ)) ≠ home_ccy(country(bᵢ₊₁))]", "home_ccy = modal currency of the country's sending banks  · rulelib.fx_count"),
 "C1": ("CURRENCY_CODE = home currency of the instructing bank with probability ≈ 0.93 (country-specific 0.73–0.98)", "P(cur = home(path[1])) per split and per country"),
 "C3": ("CURRENCY_CODE is drawn from the route: home currency of path[1] (≈95% if direct), else the receiver bank's currency (≈3.8%), else an intermediary's currency (≈+2.4 pts per intermediary), else a global vehicle (≈1.3%)", "position of cur among home currencies of path BICs, by route length; weighted linear slope per intermediary"),
 "A1": ("ln(USD_AMOUNT) ~ Normal(6 + 2·[ORDERING_TYPE=B] + 2·[BENEFICIARY_TYPE=B] + c_country + b_bank, σ ≈ 2.08)", "2×2 cell means → intercept, main effects, interaction; σ per cell"),
 "A2": ("Sending-country level c_country shifts ln(amount) (≈ −3.2 … +2.0); beneficiary country has ≈ no effect", "country effect on half 0 vs half 1 (r); sd(ordering effects) vs sd(beneficiary effects)"),
 "A3": ("Within-country residual of ln(amount) is Normal → amounts lognormal; no power-law tail", "skew, excess kurtosis, KS D vs N(0,1); Hill α(k) drift; model exceedances"),
 "D1": ("TOTAL_DURATION ≈ Σ over participating banks of a step: fast (seconds) with probability STP(b), manual otherwise", "bank classes on half 0; medians by class pair on half 1; additivity ratio med(slow,slow)/med(one slow)"),
 "D2": ("Manual-step probability depends on the bank only, not on hour, weekday or amount", "y = 1[dur > 120]; r = y − ȳ_sender − ȳ_receiver + ȳ; range of r̄ by hour/weekday"),
 "D3": ("Manual step ~ Gamma(k ≈ 2, θ ≈ 817 s); two fast steps ~ Gamma(k ≈ 3.1, θ ≈ 8.7 s)", "MLE gamma fit (loc = 0) vs lognormal; KS D"),
 "T1": ("Timestamp drawn on the instructing bank's local clock (fixed January UTC offsets): office curve starting 07:00", "local_hour = (UTC_hour + offset(country(path[1]))) mod 24; night share 01–05h"),
 "T3": ("Local weekday shares Mon 18.9 · Tue 17.0 · Wed 17.0 · Thu 18.0 · Fri 18.9 · Sat 3.6 · Sun 6.5 % for every country", "max |share_country − share_pooled| over countries with ≥ 50k rows"),
 "T4": ("Weekly volume = base × level(week), the same level for every country", "min corr(weekly volume of country, total) over top-10 countries"),
 "T4b": ("level(week) is piecewise-constant and changes only at week boundaries (Mondays)", "binary segmentation of weekday-normalised log volume with BIC penalty 2·ln(n)·σ̂²"),
 "P2": ("Account is IBAN-formatted only for banks in IBAN countries; IBAN country prefix = BIC country; one IBAN length per country", "prefix match; per-country IBAN share bimodality; distinct IBAN lengths per country"),
 "P4": ("Ordering address country = ORDERING_BIC8 country; beneficiary address country is drawn independently of BENEFICIARY_BIC8", "match rates where a <country_code> token exists"),
 "P1b": ("BENEFICIARY_TYPE is drawn independently of ORDERING_TYPE", "|P(bB | oB) − P(bB | oC)|"),
 "P5": ("Each bank has its own business-customer share on the sending side and on the receiving side", "split-half correlation of bank-level P(type = B)"),
 "F1": ("USD-denominated amounts keep whole-unit roundness (≈39% end .00, ≈16% multiples of 100); non-USD amounts have uniform cents (≈1%)", "share of round(amount·100) mod 100 = 0 by currency = USD; fixed-rate search for EUR/GBP/CHF (negative)"),
 "X1": ("ROMANCE_SCAM: consumer → same beneficiary, 2–8 payments minutes apart, each ≈ ×1.5 the previous; all labelled", "within-series regression slope of ln(amount) on position"),
 "X2": ("DUPLICATE_PAYMENT: 2–5 identical copies (sender, beneficiary, amount, path, duration) within ≤ 2 h; every copy labelled", "GROUP BY (oacc, bacc, amt): distinct path = distinct duration = 1; span ≤ 7,043 s"),
 "X3": ("FAT_FINGER_MISTAKE: amount × 100 (≈77%) or ÷ 100 (≈23%)", "2-component Gaussian mixture on log10(amount / expected)"),
 "X4": ("CEO / ACCOUNT_REPLACEMENT scams pay accounts that receive only anomalous money (mules) at small, often manual banks", "share of beneficiary accounts with zero normal inflows; bank size and STP comparison"),
 "X5": ("CUSTOMER_RECALL rows are statistically indistinguishable from normal rows on all tested features", "10 two-proportion z-tests + Mann–Whitney on amount residual; Bonferroni"),
 "X6": ("ANOMALY_TYPE is assigned independently of TRANSACTION_TYPE", "χ² + Cramér's V on the 7 × 3 table"),
}

EFFECT_KEYS = ["cramers_v", "cramers_v_vs_K", "cohen_w", "share_exact", "split_half_corr", "sender_split_half_r", "fe_range_by_hour", "max_abs_dev",
               "max_rel_err", "in_route_share", "home_share", "usd_whole_share", "chi2_dof_raw", "diff", "max_dev", "min_corr", "ks_D", "additivity_ratio"]
N_KEYS = ["n", "n_sample", "n_usd", "series", "groups"]

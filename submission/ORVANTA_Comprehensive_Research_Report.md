# ORVANTA — Comprehensive Research Report

**Reconstructing the hidden generator behind 10,000,000 synthetic cross-border payments**  
UMDAC Datathon 2026 · Swift case · Team Nai Long · generated 2026-11-14 from the project's canonical artefacts

> This is a supplementary research document. The official deliverables are the dashboard PDF and the presentation PDF; all three are generated from the same pipeline (see §17).

## Contents

1. Executive summary
2. Problem definition
3. Background: cross-border payments
4. Dataset description
5. Research architecture
6. Methodology
7. Discovery process (H1–H38)
8. Rule catalogue (34 rules)
9. The mathematics behind the findings
10. Generator reconstruction
11. Economic interpretation
12. Validation and robustness
13. Alternative hypotheses and negative findings
14. Data integrity and governance
15. Limitations and unresolved questions
16. Conclusions and future research
17. References and reproducibility

## 1. Executive summary

Swift supplied 10,000,000 synthetic payment records and asked participants to reverse-engineer the rules that generated them, using only the data. We reconstructed **34 explicit rules** covering all ten feature groups. Every rule has a pre-declared acceptance criterion that was re-tested on five partitions (full data, two hash-random halves, and the periods before and after 15 June 2023); all 34 validators pass. Passing a validator is necessary but not sufficient for confidence, so each rule also carries a level on a six-step scale:

| Level | Rules | Meaning |
|---|---|---|
| VALIDATED | 8 | Deterministic rule reproducing its field exactly (≥ 99.999% of rows) on every split, or a parameter whose 95% CI contains the theoretical value and which passes on all 5 splits with an independent second implementation / out-of-sample test. |
| STRONGLY SUPPORTED | 14 | Validator passes on all 5 splits with a wide margin; mechanism specified explicitly; best alternative tested and rejected. |
| SUPPORTED | 9 | Validator passes, but part of the mechanism is inferred, thresholds are analyst-chosen, or the rule rests on one evidence line. |
| CANDIDATE | 0 | Pattern detected and replicated, mechanism not yet formulated as a testable rule. |
| INCONCLUSIVE | 3 | Dependence or effect established but the generating mechanism is not identified, or the result is a documented negative (no signature found). |
| REJECTED | 29 | Hypothesis tested and contradicted by the data (kept for transparency). |

**Three findings carry the reconstruction.**

1. **C2 — FX conversions are determined by the route.** The number of currency conversions equals the number of adjacent known banks in BIC8_PATH whose countries have different home currencies, on 9,999,998 of 10,000,000 payments. The only two exceptions are the only two payments in the dataset that touch an Eritrean bank, whose home currency cannot be observed.
2. **R1 — route length follows K = ⌊Exp(1)⌋.** The number of intermediaries is geometric with continuation probability q = 0.3677 against the theoretical 1/e = 0.3679; goodness of fit Cohen's w = 0.0006; P(Direct) = 63.23%.
3. **R2 — a rule we overturned.** Our first reading, “Covered vs Indirect is a constant 11.3%”, was refuted by our own discovery engine (H32). Cover is a property of the sending bank: classes learned on one random half predict 61.4% vs 6.7% on the other half.

A systematic scan of 276 feature pairs found 55 strong, stable dependencies; every one is explained by a rule or by mediation through rules. Three mechanisms remain unresolved and are reported as such: the weekly volume levels (T4), directional bank-pair affinities (G1), and the undocumented CUSTOMER_RECALL label (X5). The data is synthetic: the rules describe this generator, not real Swift traffic, and we have not recovered its source code.

## 2. Problem definition

**Plain language.** A computer program produced ten million fictional cross-border payments. We see only its output. The task is to work backwards: which fields are drawn at random, from which distributions, and which are calculated from others?

**Technically.** Let each record be a vector x = (x₁ … x₂₀). The generator is an unknown program G that samples latent choices (banks, route length, party types, time) and derives the remaining fields. A *rule* is a statement of the form “field y = g(x_S)” (deterministic) or “y | x_S ~ D(θ)” (stochastic) with an explicit scope, testable on held-out data. Success is measured by how much of the joint distribution the rule set reproduces, how exactly, and how honestly the residual is described.

## 3. Background: cross-border payments

*This section is general background (established knowledge), not a finding from the data.*

| Term | Meaning |
|---|---|
| Ordering customer / beneficiary | the payer and the payee (business or consumer) |
| Ordering / beneficiary institution | the banks that hold the payer's and payee's accounts |
| Intermediary (correspondent) bank | a bank that relays the payment between two banks that have no direct account relationship |
| BIC (ISO 9362) | bank identifier: 4-character bank code, 2-letter country, 2-character location (BIC8); characters 5–6 give the country |
| Payment route | the ordered list of banks the payment passes through (here BIC8_PATH, with '...' for an unobserved hop) |
| Serial vs cover method | serial: the payment message travels bank to bank; cover: a customer message goes direct while a separate bank-to-bank cover payment settles funds |
| Currency conversion | a bank converts value into another currency, typically into the currency of the account it pays from |
| IBAN (ISO 13616) | international account number beginning with a 2-letter country code; formats are registered per country |
| Straight-through processing (STP) | automated handling without manual intervention |

The dataset's fields mimic these concepts. Where our rules use these words (e.g. “instructing bank”, “cover-prone bank”) they name generator behaviour we inferred; they are not claims about how real banks behave.

## 4. Dataset description

10,000,000 rows × 21 raw columns; UTC span 2023-04-30 11:22:26 → 2023-07-31 09:56:01; 155 currencies; 8,727 distinct BIC8 banks; 391,132 sender and 2,590,877 beneficiary accounts; 7,006 labelled anomalies.

**Table 1. Field dictionary (observed ranges and missingness computed over all rows)**

| Field | Type | Observed | Missing | Derived features | Rules | Limitation |
|---|---|---|---|---|---|---|
| EPOCH_SECONDS | integer (Unix s, UTC) | 1,682,853,746 – 1,690,797,361 | 0 | ts, date, UTC hour, local hour | time features; T1–T4b | UTC only; local clock reconstructed (T1) |
| CURRENCY_CODE | string, ISO 4217 | 85 codes | 0 | home currency of route banks | C1, C3, F1 | home-currency map inferred from data |
| USD_AMOUNT | decimal (USD) | 0.01 – 15,664,132,213.09 | 0 | ln(amount) | A1–A3, F1, X3 | normalised; original-currency amount absent |
| ORDERING_BIC8 | string NNNN·CC·LL | 8,392 banks | 0 | bank country | R5, R5b, P2, P5, G1 | account-servicing bank; 5% differ from path[1] |
| BENEFICIARY_BIC8 | string NNNN·CC·LL | 8,266 banks | 0 | bank country | R5, P4, P5, G1 | 5% differ from last path BIC |
| BIC8_PATH | string, ';'-separated | 2–22 known BICs; '...' = hidden | 0 | known BICs, gaps, route countries | R1–R7, C2, C3, G3 | hidden hops unobservable |
| TOTAL_DURATION | integer seconds | 2 – 21,649 | 0 | manual flag (>120 s) | D1–D3 | elapsed time to completion or observation end; not proven settlement time |
| CONTINUITY_QFLAG | Y / N | N on 7.7% | 0 | — | R7, R4 | observability marker, not success/failure |
| CURRENCY_CONVERSION_COUNT | integer | 0–17 | 0 | — | C2 | = currency borders on known path |
| PARTICIPANT_COUNT | integer | 2–22 | 0 | K = pc − 2 | R6, R1 | counts known BICs only |
| TRANSACTION_TYPE_CODE | Direct/Indirect/Covered | 63.2 / 32.6 / 4.2% | 0 | — | R1, R2 | — |
| ORDERING_ACCOUNT | string _FAKE_… | 391,132 accounts | 0 | IBAN flag | P2, X-detectors | synthetic identifiers |
| BENEFICIARY_ACCOUNT | string _FAKE_… | 2,590,877 accounts | 0 | IBAN flag | P2, X4 | synthetic identifiers |
| ORDERING_DETAILS | free text, multi-line | ≤ 4×35 MT layout | 0 | structured flag, line count | P2, P4 | synthetic Faker-style text |
| ORDERING_TOKENS | engineered token string | <type:len> tokens | 0 | token presence | P1b, P4 | pattern summaries, not original content |
| BENEFICIARY_DETAILS | free text, multi-line | ≤ 4×35 MT layout | 0 | structured flag | P4 | synthetic |
| BENEFICIARY_TOKENS | engineered token string | <type:len> tokens | 0 | address country token | P4 | pattern summaries |
| ORDERING_TYPE | B / C | 78.7% B | 0 | — | A1, P5, X1, X4 | — |
| BENEFICIARY_TYPE | B / C | 28.8% B | 0 | — | A1, P1b, P5 | — |
| ANOMALY_TYPE | label or empty | 6 labels, 7,006 rows | 9,992,994 | NORMAL = empty | X1–X6 | CUSTOMER_RECALL undocumented by organiser |

**Table 2. Data-quality checks**

| Check | Result | Status | Detail |
|---|---|---|---|
| Rows parsed (RFC-4180, multi-line fields) | 10,000,000 | pass | row count asserted after every stage |
| Exact duplicate rows (time, accounts, amount, currency, path, duration) | 1 | info | the one exact duplicate is a labelled DUPLICATE_PAYMENT pair sent in the same second (0-s gap), consistent with rule X2; kept |
| Currency codes not 3 upper-case letters | 0 | pass | regex [A-Z]{3} |
| ORDERING_BIC8 failing NNNN·CC·LL grammar | 0 | pass | regex |
| BENEFICIARY_BIC8 failing grammar | 0 | pass | regex |
| Non-positive amounts / durations | 0 / 0 | pass | domain check |
| PARTICIPANT_COUNT ≠ known BICs in path | 0 | pass | rule R6 |
| CONTINUITY_QFLAG inconsistent with '...' | 0 | pass | rule R7 |
| Unexpected categorical values (flag / type / party) | 0 | pass | domain sets |
| Malformed path separators (';;', leading/trailing ';') | 0 | pass | route structure |
| Header BIC ≠ path endpoint | ≈9.7% of rows | info | explained by rule R5 (5% swap per end), not an error |
| Country token absent from party details | ≈39% per side | info | analysis uses BIC country as primary |
| Detail text beyond MT 4×35 | 0.17% of rows | info | generator quirk, kept |
| DISCLAIMER column | 1 non-empty row | info | legal notice; dropped from analytic tables |

**Anomaly labels.** ROMANCE_SCAM 2,476, FAT_FINGER_MISTAKE 1,940, CEO_SCAM 945, DUPLICATE_PAYMENT 679, ACCOUNT_REPLACEMENT_SCAM 649, CUSTOMER_RECALL 317. CUSTOMER_RECALL is not defined in the case appendix; it is kept and analysed (X5) rather than dropped or interpreted.

**Transformations.** RFC-4180 parsing (multi-line quoted DETAILS fields), identifiers kept as strings, the DISCLAIMER column (filled on one row) dropped with the row kept; derived columns (bank country, path length, hidden-hop count, IBAN flags) are documented in `src/ingestion.py`. No row was removed and no value altered.

## 5. Research architecture

```
raw CSV (immutable) → Parquet (DuckDB, out-of-core) → discovery (276 pairs, trees, forensics, graph)
  → 34 SQL validators × 5 splits + pure-Python twin → register (narrative, six-level confidence)
  → evidence ledger, forensic replay, blueprint → dashboard PDF · slide PDF · this report · Streamlit lab · web platform
```

One pipeline (`python run_all.py`) produces every artefact; nothing is copied by hand between deliverables (`docs/SINGLE_SOURCE_OF_TRUTH.md`).

## 6. Methodology

| Step | Method | Why it fits |
|---|---|---|
| Ingestion | DuckDB RFC-4180 parser, row count asserted at every stage | 10M rows with embedded newlines; out-of-core; exact counts |
| Descriptive statistics | exact counts, shares, quantiles over all rows | no sampling error to manage |
| Dependency discovery | Cramér's V and symmetric uncertainty for all 276 pairs on a development half, re-measured on a validation half | categorical-heavy data; scale-free effect size; replication guards against chance |
| Mediation triage | residual V after stratifying by one or two candidate mediators (threshold 0.03) | separates direct generator links from composites of other rules |
| Rule search | depth-3 decision trees (search device only) | readable IF–THEN candidates |
| Distribution fitting | MLE (geometric, gamma, lognormal), KS distance, Q–Q, Hill tail index | explicit parametric generator steps |
| Conditional testing | stratified contrasts; two-way fixed effects (bank × bank) | removes composition effects (Simpson) |
| Graph analysis | PageRank, configuration-model χ², birthday-problem loop prediction | routes are a weighted multigraph |
| Hypothesis testing | χ², two-proportion z, Mann–Whitney; Bonferroni inside validators; Benjamini–Hochberg within families in the test registry | 297 recorded tests; multiplicity controlled per family |
| Validation | every validator on 5 splits; learned classes fitted on one half and tested on the other | independence from the data used to find the rule |
| Independent implementation | pure-Python twin (`src/rulelib.py`) and a JavaScript port checked against SQL | catches implementation errors |

**Acceptance on effect sizes.** With n = 10⁷ almost every p-value is ≈ 0, so rules are accepted on exactness (share of rows reproduced), Cohen's w, Cramér's V, KS distance or maximum deviation, with thresholds declared in the validator before it ran.

## 7. Discovery process (H1–H38)

Hypotheses in the order they were tested. Outcomes are as logged; the arrow shows the rule each became.

| ID | Hypothesis | Test | Outcome | → |
|---|---|---|---|---|
| H1 | PARTICIPANT_COUNT counts path elements | equality on 10M | Rejected as stated; pc = known BICs (excl. `...`) exactly | → R6 |
| H2 | Routing type depends on bank pair | purity of pairs; per-bank Direct share | Rejected: every bank ≈ 0.632 ± binomial noise | → R1 (global random draw) |
| H3 | Hop count ~ Poisson | successive ratios | Rejected; ratios constant at 1/e → geometric | → R1 |
| H4 | FX = distinct currencies on route | exact match | Rejected (91.7% on all 10M rows; 90.6% on the early sample) | — |
| H5 | FX = payment-currency start + borders | exact match | Rejected (93.5%) | — |
| H6 | FX = borders between adjacent known BICs | exact match | Accepted, 9,999,998/10M | → C2 |
| H7 | Intermediaries sit in the payment-currency zone | share in zone | Rejected (17%) | → R3 (size-weighted) |
| H8 | Slow durations come from off-hours queuing | slow share by hour | Raw effect 0.037 found, then explained by bank mix (FE range 0.003) | → D2 (Simpson) |
| H9 | Slow durations come from large-amount review | slow share by amount decile | Rejected (slightly reversed) | → D2 |
| H10 | Duration = per-bank additive steps | medians by bank class, out-of-sample | Accepted (both slow ≈ 1.9 × one slow) | → D1 |
| H11 | Amount depends on party types | 2×2 cell means | Accepted, exact 2-unit lattice | → A1 |
| H12 | Amount depends on beneficiary country | effect sd | Rejected (sd 0.23 vs 1.09 ordering) | → A2 |
| H13 | Individual accounts have own wealth level | variance component | Rejected (0.019 of 5.22) | → A2 |
| H14 | Timestamps in UTC office hours | night share | Rejected; local clock | → T1 |
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
| H26 | Sender and receiver banks are paired independently | χ²/dof vs product of margins (raw, unique relationships, within country pair) | Rejected: 358 / 125 / 287; affinities directional (r = 0.11) | → G1 (Low confidence, mechanism open) |
| H27 | Path loops are deliberate | birthday prediction from intermediary size distribution | Rejected as deliberate: i.i.d. draws with replacement predict loops within 3.1% | → G3 |
| H28 | Amounts have a power-law tail | Hill estimator drift, exceedances vs lognormal | Rejected; lognormal (Hill α 2.21 → 1.21; exceedances within 1–15%) | → A3 |
| H29 | Manual step is lognormal | Gamma vs lognormal KS | Gamma(2) fits better (KS 0.023 vs 0.066) | → D3 |
| H30 | Fat finger is identifiable from the amount alone | PR curve of residual threshold | Only partly: best F1 0.22, PR-AUC 0.10 (500× base rate) | → X3 detector |
| H31 | CEO scam identifiable by a simple payee heuristic | precision/recall | Rejected: precision 0.03% | → X4 limitation |
| H32 | Covered share is constant across sending banks | discovery engine flag (V .095); bank dispersion 378× binomial; out-of-sample classes | Rejected → per-bank propensity (61% vs 6.7%) | → R2 revised |
| H33 | Payment currency independent of route | currency position among route-bank currencies | Rejected: 98.7% in a route currency; receiver 3.8%; +2.4 pts per intermediary | → C3 (new) |
| H34 | Customer-type share set per country | bank-level split-half correlation | Rejected: bank attribute (r ≈ 0.99) | → P5 (new) |
| H35 | Weekly levels change at arbitrary dates | binary segmentation | Rejected: 10/10 change points on Mondays | → T4b |
| H36 | Amounts drawn directly in USD | cents by currency | Rejected: USD 39% whole units vs 1.0% for converted currencies | → F1 |
| H37 | Conversion uses one fixed rate per currency | near-integer search over rate grid | Not supported (≈2% vs 1.2% baseline) | → F1 limitation |
| H38 | Outside-route currencies are a route-independent vehicle draw | EUR/USD share on routes without an EUR or USD bank, by route length and split (all 10M rows) | Supported: EUR 1.41% (1.39–1.42% across splits), USD 0.75%, other 0.30%; flat across pc 2–5; 77.7% of outside-route payments are EUR/USD | → C3 limitation refined (vehicle draw); not promoted to a separate rule |

**The R2 revision.** Rejected → per-bank propensity (61% vs 6.7%) — the discovery engine found that routing type still depended on sending country (covered share 3.1%–50.4% by country, far more dispersed across banks than a constant rate allows). Bank classes learned on half_0 were evaluated on half_1, giving 61.4% vs 6.7%.

## 8. Rule catalogue

Each entry is generated from the registry and the validator output. *Split metrics* lists every numeric metric the validator recorded on each partition. Evidence IDs refer to the Evidence Ledger (web platform › Research library).

### R6 — PARTICIPANT_COUNT = number of known BICs in BIC8_PATH

**Feature group:** FX & Participant · **Confidence:** VALIDATED · **Validator type:** A · **Validator result:** PASS on 5 partitions

| Item | Content |
|---|---|
| Research question / hypothesis | PARTICIPANT_COUNT is derived from the path, not drawn independently. |
| Initial hypothesis (log) | H1: PARTICIPANT_COUNT counts path elements — Rejected as stated; pc = known BICs (excl. `...`) exactly |
| Formal formulation | PARTICIPANT_COUNT := number of BIC8 entries in BIC8_PATH that are not '...' |
| Executable logic | pc = \|{b ∈ split(path,';') : b ≠ '...'}\|  · rulelib.participant_count |
| Variables | PARTICIPANT_COUNT, BIC8_PATH |
| Method | Exact equality test on all rows; pure-Python re-implementation on 200k sample. |
| Acceptance criterion | share_exact == 1 |
| Sample size | 10,000,000 (n) |
| Effect size | share_exact = 1 |
| Uncertainty | share_exact ranges 1 – 1 across the five partitions |
| Counterexamples / scope | None found. 0 violating rows |
| Best alternative tested | — |
| Economic interpretation (interpretation, not evidence) | Counts observed institutions only, i.e. what the messaging layer can see. |
| Limitations | Says nothing about how many hops were hidden. |
| Related rules | — |
| Evidence IDs | EV-RULE-001, EV-VAL-001, EV-CX-001 |

*Split metrics*

| Metric | full | half_0 | half_1 | P1 | P2 |
|---|---|---|---|---|---|
| n | 10,000,000 | 5,004,013 | 4,995,987 | 4,650,900 | 5,349,100 |
| share_exact | 1 | 1 | 1 | 1 | 1 |

### R7 — CONTINUITY_QFLAG = 'N' iff path contains '...'

**Feature group:** Duration & Continuity · **Confidence:** VALIDATED · **Validator type:** A · **Validator result:** PASS on 5 partitions

| Item | Content |
|---|---|
| Research question / hypothesis | CONTINUITY_QFLAG encodes the presence of '...' placeholders. |
| Initial hypothesis (log) | no separate log entry (formulated directly from the discovery scan) |
| Formal formulation | CONTINUITY_QFLAG := 'N' if BIC8_PATH contains '...', else 'Y' |
| Executable logic | cont = N ⇔ '...' ∈ split(path)  · rulelib.continuity_flag |
| Variables | CONTINUITY_QFLAG, BIC8_PATH |
| Method | Exact equivalence test. |
| Acceptance criterion | share_exact == 1 |
| Sample size | 10,000,000 (n) |
| Effect size | share_exact = 1 |
| Uncertainty | share_exact ranges 1 – 1 across the five partitions |
| Counterexamples / scope | None. 0 violating rows |
| Best alternative tested | — |
| Economic interpretation (interpretation, not evidence) | A leg left the observed channel (e.g. a domestic clearing leg). |
| Limitations | Flag is an observability marker, not payment success/failure. |
| Related rules | — |
| Evidence IDs | EV-RULE-002, EV-VAL-002, EV-CX-002 |

*Split metrics*

| Metric | full | half_0 | half_1 | P1 | P2 |
|---|---|---|---|---|---|
| n | 10,000,000 | 5,004,013 | 4,995,987 | 4,650,900 | 5,349,100 |
| share_exact | 1 | 1 | 1 | 1 | 1 |

### R5 — Path endpoints differ from ORDERING/BENEFICIARY_BIC8 independently with p≈0.05 each

**Feature group:** Institution · **Confidence:** STRONGLY SUPPORTED · **Validator type:** B · **Validator result:** PASS on 5 partitions

| Item | Content |
|---|---|
| Research question / hypothesis | Header BICs and path endpoints can disagree; disagreement is random noise or a structural role split. |
| Initial hypothesis (log) | H17: Header BICs equal path endpoints — Rejected → independent 5% swap per end |
| Formal formulation | With probability 0.05 the first known path BIC is replaced by another bank; independently, with probability 0.05 the last known BIC is replaced |
| Executable logic | P(k₁ ≠ ORDERING_BIC8) = P(k_last ≠ BENEFICIARY_BIC8) = 0.05; P(both) = 0.05² |
| Variables | ORDERING_BIC8, BENEFICIARY_BIC8, BIC8_PATH |
| Method | Mismatch rates per end, joint vs product (independence), stratified by type, pc, anomaly. |
| Acceptance criterion | first & last mismatch in [0.045,0.055] and joint/product ratio in [0.9,1.1] |
| Sample size | 10,000,000 (full data) |
| Effect size | see metrics |
| Uncertainty | p_first ranges 0.04979 – 0.04989 across the five partitions |
| Counterexamples / scope | ROMANCE_SCAM never swaps; CEO/ACCOUNT_REPLACEMENT never swap at the beneficiary end (mule bank is the true receiver). |
| Best alternative tested | random label noise (rejected: swapped BIC predicts currency and clock) |
| Economic interpretation (interpretation, not evidence) | Ordering institution (account servicer, MT field 52) ≠ instructing agent that sends the message — common when a smaller bank uses a correspondent to send. |
| Limitations | Cannot tell which institution is 'real' from one field alone; R5b resolves it with currency/clock/IBAN evidence. |
| Related rules | R5b |
| Evidence IDs | EV-RULE-003, EV-VAL-003, EV-CX-006 |

*Split metrics*

| Metric | full | half_0 | half_1 | P1 | P2 |
|---|---|---|---|---|---|
| p_first | 0.04984 | 0.04986 | 0.04982 | 0.04989 | 0.04979 |
| p_last | 0.04993 | 0.05002 | 0.04983 | 0.0499 | 0.04995 |
| p_both | 0.002469 | 0.002468 | 0.00247 | 0.002475 | 0.002464 |
| indep_ratio | 0.9924 | 0.9897 | 0.995 | 0.9943 | 0.9906 |

### R5b — On endpoint mismatch, currency follows the path's first bank; account/IBAN follows ORDERING_BIC8

**Feature group:** Institution · **Confidence:** SUPPORTED · **Validator type:** E · **Validator result:** PASS on 5 partitions

| Item | Content |
|---|---|
| Research question / hypothesis | On swapped rows, which BIC drives currency, timing and account format? |
| Initial hypothesis (log) | H18: On swaps, header BIC drives currency — Rejected; path[1] drives currency & clock, header drives account/IBAN |
| Formal formulation | On replaced rows, CURRENCY_CODE and the local clock follow path[1] (instructing bank); account IBAN and ordering address follow ORDERING_BIC8 (account-servicing bank) |
| Executable logic | compare P(cur = home(path[1])) vs P(cur = home(ORDERING_BIC8)) on rows with path[1] ≠ ORDERING_BIC8 |
| Variables | CURRENCY_CODE, EPOCH_SECONDS, ORDERING_ACCOUNT, BIC8_PATH |
| Method | Compare home-currency match, local-night share and IBAN prefix against path[1] vs ORDERING_BIC8. |
| Acceptance criterion | home-ccy share via path[1] > 0.85 and via ORDERING_BIC8 < 0.25; IBAN prefix = ORDERING_BIC8 country == 1 |
| Sample size | 498,399 (n) |
| Effect size | see metrics |
| Uncertainty | ccy_follows_path_first ranges 0.9345 – 0.935 across the five partitions |
| Counterexamples / scope | Small share of non-home currency on both sides (vehicle currencies). |
| Best alternative tested | — |
| Economic interpretation (interpretation, not evidence) | The instructing bank books and times the payment; the customer's account stays at the servicing bank. |
| Limitations | Relies on our data-derived country→currency map. |
| Related rules | R5 |
| Evidence IDs | EV-RULE-004, EV-VAL-004 |

*Split metrics*

| Metric | full | half_0 | half_1 | P1 | P2 |
|---|---|---|---|---|---|
| n | 498,399 | 249,497 | 248,902 | 232,052 | 266,347 |
| ccy_follows_path_first | 0.9348 | 0.935 | 0.9345 | 0.9347 | 0.9348 |
| ccy_follows_obic | 0.1386 | 0.1383 | 0.1389 | 0.1381 | 0.1391 |
| iban_follows_obic | 1 | 1 | 1 | 1 | 1 |

### R1 — Intermediaries K = floor(Exp(1)): P(K=k) = (1-1/e)e^-k

**Feature group:** Route · **Confidence:** VALIDATED · **Validator type:** B · **Validator result:** PASS on 5 partitions

| Item | Content |
|---|---|
| Research question / hypothesis | Number of intermediaries follows a simple distribution. |
| Initial hypothesis (log) | H2: Routing type depends on bank pair — Rejected: every bank ≈ 0.632 ± binomial noise; H3: Hop count ~ Poisson — Rejected; ratios constant at 1/e → geometric |
| Formal formulation | Number of intermediaries K ~ ⌊Exp(1)⌋; PARTICIPANT_COUNT = K + 2 |
| Executable logic | P(K = k) = (1 − e⁻¹)·e⁻ᵏ; MLE q̂ = K̄/(1+K̄); GOF χ² → Cohen's w |
| Variables | PARTICIPANT_COUNT, TRANSACTION_TYPE_CODE |
| Method | Geometric MLE, successive ratios, chi-square GOF with Cohen's w, per split; per-bank Direct share vs binomial. |
| Acceptance criterion | MLE continuation q within ±0.005 of 1/e and Cohen's w < 0.01 on every split |
| Sample size | 10,000,000 (n) |
| Effect size | cohen_w = 0.0005785 |
| Uncertainty | q_mle ranges 0.3677 – 0.3678 across the five partitions |
| Counterexamples / scope | None beyond sampling noise. Max pc = 22 is the far tail: the rule predicts 10M·e^-15 ≈ 3.1 rows with pc ≥ 17; 5 are observed (Poisson P(X≥5 \| 3.1) ≈ 0.2). |
| Best alternative tested | Poisson hop counts (successive ratios not constant) |
| Economic interpretation (interpretation, not evidence) | Each extra correspondent hop is a fixed-probability event; most payments have a direct relationship. |
| Limitations | Correspondent choice is random in the generator; real networks depend on bilateral relationships. |
| Related rules | G3 |
| Evidence IDs | EV-RULE-005, EV-VAL-005, EV-CX-003, EV-CX-008, EV-DISC-007, EV-DISC-025, EV-DISC-027 |

*Split metrics*

| Metric | full | half_0 | half_1 | P1 | P2 |
|---|---|---|---|---|---|
| n | 10,000,000 | 5,004,013 | 4,995,987 | 4,650,900 | 5,349,100 |
| q_mle | 0.3677 | 0.3677 | 0.3678 | 0.3677 | 0.3677 |
| inv_e | 0.3679 | 0.3679 | 0.3679 | 0.3679 | 0.3679 |
| cohen_w | 0.0005785 | 0.001323 | 0.0008393 | 0.0009454 | 0.0006544 |
| chi2 | 3.347 | 8.752 | 3.519 | 4.157 | 2.291 |
| p_direct | 0.6323 | 0.6323 | 0.6324 | 0.6323 | 0.6324 |
| ratio_1 | 0.3676 | 0.3676 | 0.3675 | 0.3676 | 0.3676 |
| ratio_2 | 0.368 | 0.3686 | 0.3674 | 0.3686 | 0.3676 |
| ratio_3 | 0.3671 | 0.3657 | 0.3685 | 0.3661 | 0.368 |
| ratio_4 | 0.3685 | 0.3694 | 0.3675 | 0.3678 | 0.369 |

### R2 — Covered vs Indirect is a per-sending-bank propensity (cover-prone banks ≈61%, others ≈7%, out of sample), independent of route length

**Feature group:** Transaction Type · **Confidence:** STRONGLY SUPPORTED · **Validator type:** C · **Validator result:** PASS on 5 partitions

| Item | Content |
|---|---|
| Research question / hypothesis | How Covered vs Indirect is chosen among non-direct routes. |
| Initial hypothesis (log) | H32: Covered share is constant across sending banks — Rejected → per-bank propensity (61% vs 6.7%) |
| Formal formulation | Among non-direct routes, TRANSACTION_TYPE = Covered with a sending-bank propensity π_b (cover banks π ≈ 0.6–0.8, others π ≈ 0.05); independent of K |
| Executable logic | π_b estimated on half 0; Covered share on half 1 by class; Cramér's V(type × K) |
| Variables | TRANSACTION_TYPE_CODE, ORDERING_BIC8, PARTICIPANT_COUNT |
| Method | Share by K (Cramér's V); per-bank propensity with classes learned on half_0 and tested on half_1; within-country dispersion vs binomial. |
| Acceptance criterion | Cramér's V(type×K) < 0.01 on every split; out-of-sample: banks classed as cover banks on half_0 send >50% Covered on half_1, others <10% |
| Sample size | 3,676,720 (n) |
| Effect size | cramers_v_vs_K = 0.000513 |
| Uncertainty | pooled_covered_share ranges 0.1129 – 0.1134 across the five partitions |
| Counterexamples / scope | Original claim 'constant 11.3%' REJECTED by the discovery engine: share ranges 3–50% by sending country (IM 50%, SG 6%) and is 378× over-dispersed within countries — the parameter lives at bank level. |
| Best alternative tested | constant 11.3% Covered share (rejected: 3–50% by sending country, bank propensity) |
| Economic interpretation (interpretation, not evidence) | The cover method (MT103 direct + MT202 COV through correspondents) is a bank's operating choice — some institutions habitually settle by cover. |
| Limitations | Cover-bank class boundary (0.5) is analyst-chosen; cover share of a bank is not explained further. |
| Related rules | — |
| Evidence IDs | EV-RULE-006, EV-VAL-006, EV-DISC-034, EV-DISC-054 |

*Split metrics*

| Metric | full | half_0 | half_1 | P1 | P2 |
|---|---|---|---|---|---|
| n | 3,676,720 | 1,840,175 | 1,836,545 | 1,710,136 | 1,966,584 |
| pooled_covered_share | 0.1131 | 0.1129 | 0.1134 | 0.1134 | 0.1129 |
| cramers_v_vs_K | 0.000513 | 0.001319 | 0.001378 | 0.0007086 | 0.0006585 |
| share_k2 | 0.1129 | 0.1126 | 0.1132 | 0.1132 | 0.1126 |
| share_k1 | 0.1132 | 0.113 | 0.1133 | 0.1134 | 0.113 |
| share_k3 | 0.1133 | 0.1134 | 0.1133 | 0.1139 | 0.1128 |
| share_k4 | 0.1131 | 0.1111 | 0.115 | 0.1139 | 0.1123 |
| share_k5 | 0.1138 | 0.1118 | 0.1158 | 0.1139 | 0.1137 |
| oos_cover_banks_share | 0.6142 | — | — | — | — |
| oos_other_banks_share | 0.06704 | — | — | — | — |

### R4 — Each link hidden with p=0.05: P(N | pc) = 1-0.95^(pc-1)

**Feature group:** Route · **Confidence:** VALIDATED · **Validator type:** B · **Validator result:** PASS on 5 partitions

| Item | Content |
|---|---|
| Research question / hypothesis | Hidden hops arise per link with constant probability. |
| Initial hypothesis (log) | no separate log entry (formulated directly from the discovery scan) |
| Formal formulation | Each link between consecutive known BICs is hidden ('...') independently with p = 0.05; extra '...' per hidden link ~ Geometric(0.05) |
| Executable logic | P(cont = N \| pc) = 1 − 0.95^(pc−1); p̂ by MLE over pc strata |
| Variables | CONTINUITY_QFLAG, PARTICIPANT_COUNT, BIC8_PATH |
| Method | Binomial-per-link model, MLE of p, max deviation per pc. |
| Acceptance criterion | max \|obs-pred\| over pc 2..7 < 0.006 |
| Sample size | 10,000,000 (full data) |
| Effect size | max_abs_dev = 0.004366 |
| Uncertainty | max_abs_dev ranges 0.003047 – 0.005678 across the five partitions |
| Counterexamples / scope | Consecutive '...' chain geometrically (ratio ≈ 0.05). largest deviation from the formula 0.0044 |
| Best alternative tested | — |
| Economic interpretation (interpretation, not evidence) | Each inter-bank leg independently may run outside the observed network. |
| Limitations | None material. |
| Related rules | — |
| Evidence IDs | EV-RULE-007, EV-VAL-007, EV-DISC-024, EV-DISC-026, EV-DISC-027 |

*Split metrics*

| Metric | full | half_0 | half_1 | P1 | P2 |
|---|---|---|---|---|---|
| max_abs_dev | 0.004366 | 0.005678 | 0.003047 | 0.004334 | 0.004394 |
| p_link_mle | 0.04991 | 0.04995 | 0.04987 | 0.04989 | 0.04993 |

### R3 — Intermediaries chosen in proportion to bank size, not by payment currency

**Feature group:** Route · **Confidence:** STRONGLY SUPPORTED · **Validator type:** C · **Validator result:** PASS on 1 partitions

| Item | Content |
|---|---|
| Research question / hypothesis | Intermediaries are chosen by size (popularity), not by currency zone. |
| Initial hypothesis (log) | H7: Intermediaries sit in the payment-currency zone — Rejected (17%) |
| Formal formulation | Intermediaries are sampled with probability proportional to bank activity, not from the payment-currency zone |
| Executable logic | corr(log uses_as_intermediary, log payments_sent); share of intermediaries whose home currency = payment currency |
| Variables | BIC8_PATH, CURRENCY_CODE |
| Method | Correlation of log usage vs log sending volume; share in currency zone. |
| Acceptance criterion | corr(log intermediary uses, log payments sent) > 0.9; share in payment-currency zone < 0.25 |
| Sample size | 10,000,000 (full data) |
| Effect size | see metrics |
| Uncertainty | single-partition metric |
| Counterexamples / scope | Currency-zone hypothesis rejected (17% vs >50% expected under it). |
| Best alternative tested | intermediaries from the payment-currency zone (only 17% are) |
| Economic interpretation (interpretation, not evidence) | Large banks hold the most nostro accounts and act as hubs. |
| Limitations | Size proxy is sending volume, itself endogenous. |
| Related rules | G3 |
| Evidence IDs | EV-RULE-008, EV-VAL-008 |

*Split metrics*

| Metric | full |
|---|---|
| corr_log | 0.9423 |
| share_in_currency_zone | 0.173 |

### C2 — FX count = adjacent known-BIC pairs with different home currencies

**Feature group:** FX & Participant · **Confidence:** VALIDATED · **Validator type:** A · **Validator result:** PASS on 5 partitions

| Item | Content |
|---|---|
| Research question / hypothesis | FX count is deterministic in the route. |
| Initial hypothesis (log) | H6: FX = borders between adjacent known BICs — Accepted, 9,999,998/10M |
| Formal formulation | CURRENCY_CONVERSION_COUNT := Σ over consecutive known BICs of 1[home_ccy(country(bᵢ)) ≠ home_ccy(country(bᵢ₊₁))] |
| Executable logic | home_ccy = modal currency of the country's sending banks  · rulelib.fx_count |
| Variables | CURRENCY_CONVERSION_COUNT, BIC8_PATH |
| Method | Exact rule test on all rows; two rejected alternatives; pure-Python cross-check. |
| Acceptance criterion | share_exact >= 0.99999 |
| Sample size | 10,000,000 (n) |
| Effect size | share_exact = 0.9999998 |
| Uncertainty | share_exact ranges 0.9999996 – 1 across the five partitions |
| Counterexamples / scope | 2 rows, and they are the only 2 payments in the dataset that touch an Eritrean bank (0000ERA0, receiver). Eritrea never sends, so its home currency cannot be inferred and the rule's input is unobservable there; if ER's currency differs from the sender's, C2 predicts exactly the recorded 1 conversion. Scope: C2 holds wherever every route country has an observable home currency. 2 of 10,000,000 rows violate the exact rule |
| Best alternative tested | FX = distinct currencies on route (91.7% on all rows); payment-currency start + borders (93.5%) |
| Economic interpretation (interpretation, not evidence) | Each correspondent converts into the currency of its next nostro account; conversions happen at currency borders. |
| Limitations | Home currency per country is inferred from the data (modal currency). |
| Related rules | — |
| Evidence IDs | EV-RULE-009, EV-VAL-009, EV-CX-004, EV-DISC-005, EV-DISC-007, EV-DISC-008, EV-DISC-026, EV-DISC-028 |

*Split metrics*

| Metric | full | half_0 | half_1 | P1 | P2 |
|---|---|---|---|---|---|
| n | 10,000,000 | 5,004,013 | 4,995,987 | 4,650,900 | 5,349,100 |
| share_exact | 0.9999998 | 1 | 0.9999996 | 0.9999996 | 1 |
| exceptions | 2 | 0 | 2 | 2 | 0 |
| alt_distinct | 0.9168 | 0.9166 | 0.917 | 0.9169 | 0.9168 |

### C3 — Payment currency is drawn from the currencies on the route: first bank ≈ 95% (direct), receiver bank ≈ 3.8%, +≈2.4 pts per intermediary, outside-route vehicle ≈ 1.3%

**Feature group:** Currency & Value · **Confidence:** STRONGLY SUPPORTED · **Validator type:** E · **Validator result:** PASS on 5 partitions

| Item | Content |
|---|---|
| Research question / hypothesis | Where the payment currency comes from. |
| Initial hypothesis (log) | H33: Payment currency independent of route — Rejected: 98.7% in a route currency; receiver 3.8%; +2.4 pts per intermediary; H38: Outside-route currencies are a route-independent vehicle draw — Supported: EUR 1.41% (1.39–1.42% across splits), USD 0.75%, other 0.30%; flat across pc 2–5; 77.7% of outside-route payments are EUR/USD |
| Formal formulation | CURRENCY_CODE is drawn from the route: home currency of path[1] (≈95% if direct), else the receiver bank's currency (≈3.8%), else an intermediary's currency (≈+2.4 pts per intermediary), else a global vehicle (≈1.3%) |
| Executable logic | position of cur among home currencies of path BICs, by route length; weighted linear slope per intermediary |
| Variables | CURRENCY_CODE, BIC8_PATH |
| Method | Currency matched against the home currencies of every bank on the path, by route length; per split on a 3M-row reservoir sample. |
| Acceptance criterion | ≥98% of payments in a route-bank currency on every split; receiver-only share stable across route lengths (range < 0.006); intermediary-only share rises ≈ linearly per intermediary (slope 0.02–0.035) |
| Sample size | 3,000,000 (n_sample) |
| Effect size | in_route_share = 0.9872 |
| Uncertainty | n_sample ranges 1,394,910 – 3,000,000 across the five partitions |
| Counterexamples / scope | 1.27% of payments (126,857) use a currency of no route bank; 77.7% of them are EUR or USD. H38 (all 10M rows, 5 splits): on routes with no EUR or USD bank the payment is in EUR 1.41% and USD 0.75% of the time, stable across route length (pc 2–5) and splits (EUR 1.39–1.42%) — a route-independent vehicle draw that shows up as 'outside' only when that currency is not already on the route. Supported refinement, not a separate validated rule (the EUR/USD set was chosen after inspection). 1.28% of payments use a currency of no route bank |
| Best alternative tested | currency chosen before routing (cannot be excluded; route-first is the more parsimonious reading) |
| Economic interpretation (interpretation, not evidence) | A payment is denominated in a currency some bank in the chain can book: the sender's (most), the receiver's, or a correspondent's clearing currency; otherwise a global vehicle currency. |
| Limitations | Direction (route first, then currency) is consistent with the data, not identified; the per-intermediary probability is approximate (linear fit). |
| Related rules | C1 |
| Evidence IDs | EV-RULE-010, EV-VAL-010, EV-CX-005, EV-DISC-014, EV-DISC-043, EV-DISC-046, EV-DISC-047, EV-DISC-054 |

*Split metrics*

| Metric | full | half_0 | half_1 | P1 | P2 |
|---|---|---|---|---|---|
| n_sample | 3,000,000 | 1,502,902 | 1,497,098 | 1,394,910 | 1,605,090 |
| in_route_share | 0.9872 | 0.9873 | 0.9872 | 0.9873 | 0.9872 |
| receiver_only_mean | 0.0379 | 0.03771 | 0.03809 | 0.03809 | 0.03773 |
| receiver_only_range | 0.002558 | 0.00397 | 0.001597 | 0.002456 | 0.003076 |
| intermediary_slope_per_hop | 0.02433 | 0.0244 | 0.02426 | 0.02447 | 0.0242 |
| outside_share | 0.01275 | 0.01273 | 0.01277 | 0.01271 | 0.01279 |
| first_bank_direct | 0.9474 | 0.9476 | 0.9472 | 0.9471 | 0.9476 |

### C1 — Payment currency = home currency of the instructing (first-path) bank ~93%

**Feature group:** Currency & Value · **Confidence:** SUPPORTED · **Validator type:** C · **Validator result:** PASS on 5 partitions

| Item | Content |
|---|---|
| Research question / hypothesis | Payment currency is the instructing bank's home currency. |
| Initial hypothesis (log) | H18: On swaps, header BIC drives currency — Rejected; path[1] drives currency & clock, header drives account/IBAN |
| Formal formulation | CURRENCY_CODE = home currency of the instructing bank with probability ≈ 0.93 (country-specific 0.73–0.98) |
| Executable logic | P(cur = home(path[1])) per split and per country |
| Variables | CURRENCY_CODE, BIC8_PATH |
| Method | Share by split; per-country range. |
| Acceptance criterion | share in [0.91,0.95] on every split; per-country share range reported |
| Sample size | 10,000,000 (n) |
| Effect size | home_share = 0.9342 |
| Uncertainty | home_share ranges 0.934 – 0.9343 across the five partitions |
| Counterexamples / scope | 6.6% non-home (EUR, USD, GBP, CHF, CNY, SGD …); RU only 73% home. 6.6% not in the instructing bank's home currency (explained by C3) |
| Best alternative tested | — |
| Economic interpretation (interpretation, not evidence) | Local-currency funding; invoices in global vehicle currencies. |
| Limitations | Vehicle-currency selection mechanism not fully identified. |
| Related rules | C3 |
| Evidence IDs | EV-RULE-011, EV-VAL-011, EV-DISC-003, EV-DISC-006, EV-DISC-018, EV-DISC-020, EV-DISC-028, EV-DISC-033 |

*Split metrics*

| Metric | full | half_0 | half_1 | P1 | P2 |
|---|---|---|---|---|---|
| n | 10,000,000 | 5,004,013 | 4,995,987 | 4,650,900 | 5,349,100 |
| home_share | 0.9342 | 0.9343 | 0.934 | 0.9342 | 0.9341 |

### A1 — ln(amount) = 6 + 2·[O=B] + 2·[B=B], σ≈2.28 (no interaction)

**Feature group:** Currency & Value · **Confidence:** STRONGLY SUPPORTED · **Validator type:** C · **Validator result:** PASS on 5 partitions

| Item | Content |
|---|---|
| Research question / hypothesis | Log-amount mean is additive in party types. |
| Initial hypothesis (log) | H11: Amount depends on party types — Accepted, exact 2-unit lattice |
| Formal formulation | ln(USD_AMOUNT) ~ Normal(6 + 2·[ORDERING_TYPE=B] + 2·[BENEFICIARY_TYPE=B] + c_country + b_bank, σ ≈ 2.08) |
| Executable logic | 2×2 cell means → intercept, main effects, interaction; σ per cell |
| Variables | USD_AMOUNT, ORDERING_TYPE, BENEFICIARY_TYPE |
| Method | 2×2 cell means → intercept, main effects, interaction; σ per cell; per split. |
| Acceptance criterion | intercept∈[5.9,6.2], both effects∈[1.85,2.15], \|interaction\|<0.1, σ spread across cells <0.03 |
| Sample size | 10,000,000 (full data) |
| Effect size | see metrics |
| Uncertainty | intercept ranges 6.061 – 6.064 across the five partitions |
| Counterexamples / scope | Amount residual is slightly left-skewed (−0.12); 13.5% of fat-finger amounts are integers. |
| Best alternative tested | — |
| Economic interpretation (interpretation, not evidence) | Commercial flows ≫ personal flows; B2B largest. |
| Limitations | Country and bank effects add structure on top (A2). |
| Related rules | — |
| Evidence IDs | EV-RULE-012, EV-VAL-012, EV-DISC-009, EV-DISC-012 |

*Split metrics*

| Metric | full | half_0 | half_1 | P1 | P2 |
|---|---|---|---|---|---|
| intercept | 6.062 | 6.064 | 6.061 | 6.063 | 6.062 |
| effect_ordering_B | 1.932 | 1.929 | 1.935 | 1.929 | 1.934 |
| effect_beneficiary_B | 1.965 | 1.961 | 1.969 | 1.964 | 1.966 |
| interaction | 0.03887 | 0.04309 | 0.03464 | 0.04263 | 0.0356 |
| sd_min | 2.284 | 2.284 | 2.281 | 2.284 | 2.284 |
| sd_max | 2.292 | 2.292 | 2.292 | 2.289 | 2.295 |

### A2 — Ordering-country effect replicates across independent halves (beneficiary country ≈ no effect)

**Feature group:** Currency & Value · **Confidence:** SUPPORTED · **Validator type:** C · **Validator result:** PASS on 1 partitions

| Item | Content |
|---|---|
| Research question / hypothesis | Sending-country wealth level shifts amounts; beneficiary country does not. |
| Initial hypothesis (log) | H12: Amount depends on beneficiary country — Rejected (sd 0.23 vs 1.09 ordering); H13: Individual accounts have own wealth level — Rejected (0.019 of 5.22) |
| Formal formulation | Sending-country level c_country shifts ln(amount) (≈ −3.2 … +2.0); beneficiary country has ≈ no effect |
| Executable logic | country effect on half 0 vs half 1 (r); sd(ordering effects) vs sd(beneficiary effects) |
| Variables | USD_AMOUNT, ORDERING_BIC8 |
| Method | Country effects estimated separately on random halves; sd comparison. |
| Acceptance criterion | corr(country effect half_0, half_1) > 0.95; sd(ordering effects) > 3×sd(beneficiary effects) |
| Sample size | 10,000,000 (full data) |
| Effect size | split_half_corr = 0.9998446 |
| Uncertainty | single-partition metric |
| Counterexamples / scope | Effects are randomised by design (case text) — ranking is not real-world. |
| Best alternative tested | beneficiary-country wealth effect (sd 0.23 vs 1.09) |
| Economic interpretation (interpretation, not evidence) | GDP-like scaling of ticket size at origin. |
| Limitations | Bank-level variance (0.22) not decomposed further. |
| Related rules | D1, T1 |
| Evidence IDs | EV-RULE-013, EV-VAL-013, EV-DISC-035 |

*Split metrics*

| Metric | full |
|---|---|
| split_half_corr | 0.9998446 |
| sd_ordering | 1.091 |
| sd_beneficiary | 0.2321 |
| countries | 62 |

### D1 — Duration = sum of per-bank steps; bank speed class learned on half_0 predicts half_1

**Feature group:** Duration & Continuity · **Confidence:** SUPPORTED · **Validator type:** E · **Validator result:** PASS on 0 partitions

| Item | Content |
|---|---|
| Research question / hypothesis | Duration is a sum of per-bank processing steps. |
| Initial hypothesis (log) | H10: Duration = per-bank additive steps — Accepted (both slow ≈ 1.9 × one slow) |
| Formal formulation | TOTAL_DURATION ≈ Σ over participating banks of a step: fast (seconds) with probability STP(b), manual otherwise |
| Executable logic | bank classes on half 0; medians by class pair on half 1; additivity ratio med(slow,slow)/med(one slow) |
| Variables | TOTAL_DURATION, BIC8_PATH |
| Method | Bank speed classes learned on half_0, tested on half_1 (out-of-sample). |
| Acceptance criterion | out-of-sample: fast→fast slow-share < 0.2, any slow bank > 0.9, median(slow,slow)/median(one slow) in [1.6,2.4] |
| Sample size | 2,111,142 (n) |
| Effect size | see metrics |
| Uncertainty | see split metrics |
| Counterexamples / scope | ~13% slow cases among fast-fast pairs (each 'fast' bank has a non-zero manual rate). |
| Best alternative tested | — |
| Economic interpretation (interpretation, not evidence) | STP vs manual repair/compliance review. |
| Limitations | Exact step distributions not fitted. |
| Related rules | A2, D3 |
| Evidence IDs | EV-RULE-014, EV-VAL-014, EV-DISC-021, EV-DISC-025 |

### D2 — Manual (slow) processing is a bank attribute: hour/weekday/amount effects vanish once bank fixed effects are removed

**Feature group:** Duration & Continuity · **Confidence:** SUPPORTED · **Validator type:** C · **Validator result:** PASS on 1 partitions

| Item | Content |
|---|---|
| Research question / hypothesis | Manual processing depends on bank, not on time or amount. |
| Initial hypothesis (log) | H8: Slow durations come from off-hours queuing — Raw effect 0.037 found, then explained by bank mix (FE range 0.003); H9: Slow durations come from large-amount review — Rejected (slightly reversed) |
| Formal formulation | Manual-step probability depends on the bank only, not on hour, weekday or amount |
| Executable logic | y = 1[dur > 120]; r = y − ȳ_sender − ȳ_receiver + ȳ; range of r̄ by hour/weekday |
| Variables | TOTAL_DURATION, EPOCH_SECONDS, USD_AMOUNT |
| Method | Two-way bank fixed-effect demeaning; residual ranges by hour/weekday; corr with amount. |
| Acceptance criterion | after two-way (sender bank, receiver bank) demeaning among fast-fast pairs: residual range across UTC hours < 0.015, weekdays < 0.015, \|corr with ln amount\| < 0.02 |
| Sample size | 10,000,000 (full data) |
| Effect size | fe_range_by_hour = 0.002913 |
| Uncertainty | single-partition metric |
| Counterexamples / scope | Raw hour effect 0.037 is a Simpson artefact (bank mix across time zones). |
| Best alternative tested | off-hours queuing (hour effect vanishes with bank fixed effects); large-amount review (reversed) |
| Economic interpretation (interpretation, not evidence) | Automation level is an institution attribute. |
| Limitations | Linear-probability FE approximation. |
| Related rules | — |
| Evidence IDs | EV-RULE-015, EV-VAL-015 |

*Split metrics*

| Metric | full |
|---|---|
| raw_range_by_hour | 0.03688 |
| fe_range_by_hour | 0.002913 |
| fe_range_by_weekday | 0.001452 |
| fe_corr_ln_amount | -0.0008232 |

### T1 — Activity follows the instructing bank's local clock (fixed offsets)

**Feature group:** Temporal · **Confidence:** STRONGLY SUPPORTED · **Validator type:** C · **Validator result:** PASS on 5 partitions

| Item | Content |
|---|---|
| Research question / hypothesis | Timestamps are generated in the instructing bank's local time. |
| Initial hypothesis (log) | H14: Timestamps in UTC office hours — Rejected; local clock; H15: Local clock uses true DST offsets — Rejected; January offsets; H18: On swaps, header BIC drives currency — Rejected; path[1] drives currency & clock, header drives account/IBAN |
| Formal formulation | Timestamp drawn on the instructing bank's local clock (fixed January UTC offsets): office curve starting 07:00 |
| Executable logic | local_hour = (UTC_hour + offset(country(path[1]))) mod 24; night share 01–05h |
| Variables | EPOCH_SECONDS, BIC8_PATH |
| Method | Night-share comparison local vs UTC; offset estimation by profile alignment. |
| Acceptance criterion | night share (01-05h local) < 0.06 on every split vs > 0.15 with UTC |
| Sample size | 10,000,000 (full data) |
| Effect size | see metrics |
| Uncertainty | night_local ranges 0.04583 – 0.04604 across the five partitions |
| Counterexamples / scope | Offsets are January values (no DST). |
| Best alternative tested | — |
| Economic interpretation (interpretation, not evidence) | Office-hours behaviour; cut-off driven submissions. |
| Limitations | Offsets estimated in whole hours (IN shows +5, true +5:30). |
| Related rules | A2 |
| Evidence IDs | EV-RULE-016, EV-VAL-016, EV-DISC-018, EV-DISC-019, EV-DISC-053 |

*Split metrics*

| Metric | full | half_0 | half_1 | P1 | P2 |
|---|---|---|---|---|---|
| night_local | 0.04594 | 0.04593 | 0.04596 | 0.04583 | 0.04604 |
| night_utc | 0.1237 | 0.1238 | 0.1236 | 0.1225 | 0.1247 |

### T3 — One weekday shape for all countries (local weekday)

**Feature group:** Temporal · **Confidence:** STRONGLY SUPPORTED · **Validator type:** B · **Validator result:** PASS on 1 partitions

| Item | Content |
|---|---|
| Research question / hypothesis | Weekday shape is universal. |
| Initial hypothesis (log) | H16: Gulf/Israel banks have Fri–Sat weekend — Rejected; one universal shape |
| Formal formulation | Local weekday shares Mon 18.9 · Tue 17.0 · Wed 17.0 · Thu 18.0 · Fri 18.9 · Sat 3.6 · Sun 6.5 % for every country |
| Executable logic | max \|share_country − share_pooled\| over countries with ≥ 50k rows |
| Variables | EPOCH_SECONDS |
| Method | Max deviation of country weekday shares from pooled. |
| Acceptance criterion | max deviation of any country's weekday share from pooled share < 0.01 (countries ≥50k rows) |
| Sample size | 10,000,000 (full data) |
| Effect size | max_dev = 0.003874 |
| Uncertainty | single-partition metric |
| Counterexamples / scope | Fri–Sat weekend hypothesis for Gulf/Israel rejected. |
| Best alternative tested | Fri–Sat weekend for Gulf/Israel (identical shape) |
| Economic interpretation (interpretation, not evidence) | Sunday batch preparation > Saturday. |
| Limitations | - |
| Related rules | T4, T4b |
| Evidence IDs | EV-RULE-017, EV-VAL-017, EV-DISC-053 |

*Split metrics*

| Metric | full |
|---|---|
| max_dev | 0.003874 |
| countries | 35 |

### T4 — Weekly volume multiplier is global (shared by all countries)

**Feature group:** Temporal · **Confidence:** INCONCLUSIVE · **Validator type:** B · **Validator result:** PASS on 1 partitions

| Item | Content |
|---|---|
| Research question / hypothesis | Weekly volume level is global. |
| Initial hypothesis (log) | H25: Weekly multiplier reflects month/quarter end — Inconclusive |
| Formal formulation | Weekly volume = base × level(week), the same level for every country |
| Executable logic | min corr(weekly volume of country, total) over top-10 countries |
| Variables | EPOCH_SECONDS |
| Method | Correlation of country weekly series with total. |
| Acceptance criterion | min corr of weekly volume between top-10 countries and the total > 0.98 |
| Sample size | 10,000,000 (full data) |
| Effect size | min_corr = 0.9992217 |
| Uncertainty | single-partition metric |
| Counterexamples / scope | Cause of levels unexplained. |
| Best alternative tested | — |
| Economic interpretation (interpretation, not evidence) | Possibly calendar-driven (month/quarter end). |
| Limitations | Only 13 full weeks. |
| Related rules | T3, T4b |
| Evidence IDs | EV-RULE-018, EV-VAL-018 |

*Split metrics*

| Metric | full |
|---|---|
| min_corr | 0.9992217 |

### P2 — IBAN prefix always equals BIC country; IBAN used only by IBAN-country banks

**Feature group:** Token · **Confidence:** VALIDATED · **Validator type:** A · **Validator result:** PASS on 5 partitions

| Item | Content |
|---|---|
| Research question / hypothesis | Account format follows the IBAN registry by country. |
| Initial hypothesis (log) | no separate log entry (formulated directly from the discovery scan) |
| Formal formulation | Account is IBAN-formatted only for banks in IBAN countries; IBAN country prefix = BIC country; one IBAN length per country |
| Executable logic | prefix match; per-country IBAN share bimodality; distinct IBAN lengths per country |
| Variables | ORDERING/BENEFICIARY_ACCOUNT, *_TOKENS |
| Method | Prefix match, per-country IBAN share bimodality. |
| Acceptance criterion | prefix match == 1; countries with 0<share<0.5 == 0 |
| Sample size | 10,000,000 (full data) |
| Effect size | see metrics |
| Uncertainty | o_prefix ranges 1 – 1 across the five partitions |
| Counterexamples / scope | IBAN countries still use local formats ~8%. IBAN prefix mismatches: 0.0000% |
| Best alternative tested | — |
| Economic interpretation (interpretation, not evidence) | Regulatory account-number standards. |
| Limitations | - |
| Related rules | — |
| Evidence IDs | EV-RULE-019, EV-VAL-019, EV-CX-007, EV-DISC-001, EV-DISC-002, EV-DISC-006, EV-DISC-010, EV-DISC-030 |

*Split metrics*

| Metric | full | half_0 | half_1 | P1 | P2 |
|---|---|---|---|---|---|
| o_prefix | 1 | 1 | 1 | 1 | 1 |
| b_prefix | 1 | 1 | 1 | 1 | 1 |
| countries_ambiguous | 0 | — | — | — | — |

### P4 — Ordering party lives in its bank's country; beneficiary residence is decoupled from its bank

**Feature group:** Party Details · **Confidence:** SUPPORTED · **Validator type:** C · **Validator result:** PASS on 5 partitions

| Item | Content |
|---|---|
| Research question / hypothesis | Ordering parties live in their bank's country; beneficiaries do not. |
| Initial hypothesis (log) | no separate log entry (formulated directly from the discovery scan) |
| Formal formulation | Ordering address country = ORDERING_BIC8 country; beneficiary address country is drawn independently of BENEFICIARY_BIC8 |
| Executable logic | match rates where a <country_code> token exists |
| Variables | *_TOKENS country codes, BICs |
| Method | Match rates where country token present (61%). |
| Acceptance criterion | ordering match == 1, beneficiary match < 0.02 on every split |
| Sample size | 10,000,000 (full data) |
| Effect size | see metrics |
| Uncertainty | o_match ranges 1 – 1 across the five partitions |
| Counterexamples / scope |  |
| Best alternative tested | — |
| Economic interpretation (interpretation, not evidence) | Generator samples beneficiary residence by population, bank by banking size — a modelling shortcut. |
| Limitations | 39% of details carry no country token. |
| Related rules | — |
| Evidence IDs | EV-RULE-020, EV-VAL-020 |

*Split metrics*

| Metric | full | half_0 | half_1 | P1 | P2 |
|---|---|---|---|---|---|
| o_match | 1 | 1 | 1 | 1 | 1 |
| b_match | 0.009796 | 0.009727 | 0.009865 | 0.009813 | 0.009781 |

### P5 — Customer-type mix is a bank attribute: each bank has its own business share of senders and of receivers

**Feature group:** Institution · **Confidence:** STRONGLY SUPPORTED · **Validator type:** C · **Validator result:** PASS on 1 partitions

| Item | Content |
|---|---|
| Research question / hypothesis | Why the business-customer share varies by country. |
| Initial hypothesis (log) | H34: Customer-type share set per country — Rejected: bank attribute (r ≈ 0.99) |
| Formal formulation | Each bank has its own business-customer share on the sending side and on the receiving side |
| Executable logic | split-half correlation of bank-level P(type = B) |
| Variables | ORDERING_TYPE, BENEFICIARY_TYPE, BICs |
| Method | Bank-level business share on each side, split-half correlation; within-country dispersion vs binomial. |
| Acceptance criterion | split-half correlation of bank-level business share > 0.95 on both sides (banks ≥200 rows per half); within-country dispersion ≫ binomial |
| Sample size | 10,000,000 (full data) |
| Effect size | sender_split_half_r = 0.9945 |
| Uncertainty | single-partition metric |
| Counterexamples / scope | Country differences (38–96% senders) are bank mix; dispersion 549× (senders) and 196× (receivers) binomial within countries. |
| Best alternative tested | — |
| Economic interpretation (interpretation, not evidence) | Banks specialise: corporate banks vs retail banks serve different customer mixes. |
| Limitations | Mechanism behind each bank's share (size? country?) not identified. |
| Related rules | — |
| Evidence IDs | EV-RULE-021, EV-VAL-021, EV-DISC-031, EV-DISC-051 |

*Split metrics*

| Metric | full |
|---|---|
| sender_split_half_r | 0.9945 |
| sender_banks | 2,412 |
| sender_bank_share_min | 0.03201 |
| sender_bank_share_max | 1 |
| receiver_split_half_r | 0.9867 |
| receiver_banks | 2,189 |
| receiver_bank_share_min | 0.02751 |
| receiver_bank_share_max | 0.8639 |

### P1b — Beneficiary type independent of ordering type

**Feature group:** Party Details · **Confidence:** STRONGLY SUPPORTED · **Validator type:** B · **Validator result:** PASS on 5 partitions

| Item | Content |
|---|---|
| Research question / hypothesis | Receiver type independent of sender type. |
| Initial hypothesis (log) | no separate log entry (formulated directly from the discovery scan) |
| Formal formulation | BENEFICIARY_TYPE is drawn independently of ORDERING_TYPE |
| Executable logic | \|P(bB \| oB) − P(bB \| oC)\| |
| Variables | ORDERING_TYPE, BENEFICIARY_TYPE |
| Method | Conditional shares by split. |
| Acceptance criterion | \|P(bB\|oB)-P(bB\|oC)\| < 0.005 |
| Sample size | 10,000,000 (full data) |
| Effect size | diff = 0.001093 |
| Uncertainty | pB_given_oB ranges 0.2883 – 0.2885 across the five partitions |
| Counterexamples / scope |  |
| Best alternative tested | — |
| Economic interpretation (interpretation, not evidence) | Independent sampling per side. |
| Limitations | - |
| Related rules | — |
| Evidence IDs | EV-RULE-022, EV-VAL-022 |

*Split metrics*

| Metric | full | half_0 | half_1 | P1 | P2 |
|---|---|---|---|---|---|
| pB_given_oB | 0.2884 | 0.2884 | 0.2884 | 0.2883 | 0.2885 |
| pB_given_oC | 0.2873 | 0.287 | 0.2876 | 0.2876 | 0.2871 |
| diff | 0.001093 | 0.001357 | 0.0008283 | 0.0007233 | 0.001414 |

### X1 — ROMANCE_SCAM: consumer bursts of 2-8 escalating payments (×~1.5 each)

**Feature group:** Anomaly · **Confidence:** STRONGLY SUPPORTED · **Validator type:** E · **Validator result:** PASS on 1 partitions

| Item | Content |
|---|---|
| Research question / hypothesis | Romance scams are escalating consumer bursts. |
| Initial hypothesis (log) | H19: Romance = C→C — Partly rejected: sender C 100%, receiver follows base mix |
| Formal formulation | ROMANCE_SCAM: consumer → same beneficiary, 2–8 payments minutes apart, each ≈ ×1.5 the previous; all labelled |
| Executable logic | within-series regression slope of ln(amount) on position |
| Variables | ANOMALY_TYPE, accounts, amounts, timestamps |
| Method | Series reconstruction, within-series log slope, detector precision/recall. |
| Acceptance criterion | sender C share == 1; within-series ln step in [0.3,0.5]; every series fully labelled |
| Sample size | 500 (series) |
| Effect size | see metrics |
| Uncertainty | single-partition metric |
| Counterexamples / scope | Case text says C→C, but receiver type follows base mix (27% B). |
| Best alternative tested | — |
| Economic interpretation (interpretation, not evidence) | Escalating repeated transfers by a groomed victim. |
| Limitations | Timing (minutes apart) is unrealistic vs real grooming over weeks. |
| Related rules | X3, X4 |
| Evidence IDs | EV-RULE-023, EV-VAL-023 |

*Split metrics*

| Metric | full |
|---|---|
| sender_consumer_share | 1 |
| median_ln_step | 0.4001 |
| mean_ln_step | 0.3903 |
| labelled_share_in_series | 1 |
| series | 500 |

### X2 — DUPLICATE_PAYMENT: 2-5 identical copies (amount, path, duration) within 2h; all copies labelled

**Feature group:** Anomaly · **Confidence:** VALIDATED · **Validator type:** A · **Validator result:** PASS on 1 partitions

| Item | Content |
|---|---|
| Research question / hypothesis | Duplicates are message replays. |
| Initial hypothesis (log) | H20: Duplicates: first copy unlabelled — Rejected; every copy labelled |
| Formal formulation | DUPLICATE_PAYMENT: 2–5 identical copies (sender, beneficiary, amount, path, duration) within ≤ 2 h; every copy labelled |
| Executable logic | GROUP BY (oacc, bacc, amt): distinct path = distinct duration = 1; span ≤ 7,043 s |
| Variables | all fields |
| Method | Exact-key grouping; detector over full data. |
| Acceptance criterion | every group has 1 path & 1 duration; span ≤ 7200s; sizes ⊂ {2..5} |
| Sample size | 185 (groups) |
| Effect size | see metrics |
| Uncertainty | single-partition metric |
| Counterexamples / scope | 5 normal groups and 10 romance groups also match the key. |
| Best alternative tested | — |
| Economic interpretation (interpretation, not evidence) | Back-office race condition resends the same instruction. |
| Limitations | Labelling convention: every copy is labelled, including the original. |
| Related rules | — |
| Evidence IDs | EV-RULE-024, EV-VAL-024, EV-CX-010 |

*Split metrics*

| Metric | full |
|---|---|
| groups | 185 |
| max_paths | 1 |
| max_durations | 1 |
| max_span_s | 7,043 |
| min_size | 2 |
| max_size | 5 |

### X3 — FAT_FINGER_MISTAKE: amount ×100 or ÷100 relative to expectation

**Feature group:** Anomaly · **Confidence:** SUPPORTED · **Validator type:** C · **Validator result:** PASS on 1 partitions

| Item | Content |
|---|---|
| Research question / hypothesis | Fat-finger amounts are scaled by 10^±2. |
| Initial hypothesis (log) | H21: Fat finger ×10/×100/×1000 — Two modes ≈ ±2 (log10) → ×100 / ÷100; H30: Fat finger is identifiable from the amount alone — Only partly: best F1 0.22, PR-AUC 0.10 (500× base rate) |
| Formal formulation | FAT_FINGER_MISTAKE: amount × 100 (≈77%) or ÷ 100 (≈23%) |
| Executable logic | 2-component Gaussian mixture on log10(amount / expected) |
| Variables | USD_AMOUNT |
| Method | Residual vs country+segment expectation, 2-component Gaussian mixture. |
| Acceptance criterion | bimodal log10 residual: both modes within ±0.6 of ±2; up share in [0.65,0.9] |
| Sample size | 1,940 (n) |
| Effect size | see metrics |
| Uncertainty | single-partition metric |
| Counterexamples / scope | Cannot separate ×100 from ×1000 per row (residual sd ≈ 0.9 log10). |
| Best alternative tested | — |
| Economic interpretation (interpretation, not evidence) | Comma/dot decimal-separator confusion. |
| Limitations | Expectation model has its own noise. |
| Related rules | X1 |
| Evidence IDs | EV-RULE-025, EV-VAL-025, EV-CX-009 |

*Split metrics*

| Metric | full |
|---|---|
| n | 1,940 |
| mode_low | -1.95 |
| mode_high | 2.435 |
| component_sd | 1.139 |
| up_share | 0.7727 |

### X4 — CEO & ACCOUNT_REPLACEMENT scams pay mule accounts at small banks

**Feature group:** Anomaly · **Confidence:** SUPPORTED · **Validator type:** C · **Validator result:** PASS on 1 partitions

| Item | Content |
|---|---|
| Research question / hypothesis | CEO/account-replacement scams target mule accounts. |
| Initial hypothesis (log) | H22: Account-replacement reuses legit payee name — Rejected (1/649); H23: Scams are slow because of added delay — Rejected; scams sit at slow (small) banks; H31: CEO scam identifiable by a simple payee heuristic — Rejected: precision 0.03% |
| Formal formulation | CEO / ACCOUNT_REPLACEMENT scams pay accounts that receive only anomalous money (mules) at small, often manual banks |
| Executable logic | share of beneficiary accounts with zero normal inflows; bank size and STP comparison |
| Variables | BENEFICIARY_ACCOUNT, BENEFICIARY_BIC8 |
| Method | Share of beneficiary accounts that only receive anomalous money; bank size/STP comparison; stratified duration. |
| Acceptance criterion | share of beneficiary accounts receiving only anomalous money > 0.35 (vs < 0.25 for error types) |
| Sample size | 10,000,000 (full data) |
| Effect size | see metrics |
| Uncertainty | single-partition metric |
| Counterexamples / scope | No name-swap evidence for account replacement (1/649). |
| Best alternative tested | account-replacement reuses payee name with swapped account (1/649) |
| Economic interpretation (interpretation, not evidence) | Fraud proceeds concentrate in mule accounts at weaker-control banks. |
| Limitations | Mule definition is data-driven. |
| Related rules | X1 |
| Evidence IDs | EV-RULE-026, EV-VAL-026 |

*Split metrics*

| Metric | full |
|---|---|
| ROMANCE_SCAM | 0.603 |
| ACCOUNT_REPLACEMENT_SCAM | 0.47 |
| CEO_SCAM | 0.4836 |
| CUSTOMER_RECALL | 0.183 |
| FAT_FINGER_MISTAKE | 0.2057 |
| DUPLICATE_PAYMENT | 0.1929 |

### X5 — CUSTOMER_RECALL has no observable signature (negative result)

**Feature group:** Anomaly · **Confidence:** INCONCLUSIVE · **Validator type:** B · **Validator result:** PASS on 0 partitions

| Item | Content |
|---|---|
| Research question / hypothesis | CUSTOMER_RECALL has a signature. |
| Initial hypothesis (log) | H24: CUSTOMER_RECALL has a signature — Rejected (no feature significant) |
| Formal formulation | CUSTOMER_RECALL rows are statistically indistinguishable from normal rows on all tested features |
| Executable logic | 10 two-proportion z-tests + Mann–Whitney on amount residual; Bonferroni |
| Variables | all |
| Method | 10 two-proportion z-tests + Mann-Whitney, Bonferroni. |
| Acceptance criterion | no feature differs from normal after Bonferroni (α=0.05/m) |
| Sample size | 10,000,000 (full data) |
| Effect size | see metrics |
| Uncertainty | see split metrics |
| Counterexamples / scope | Path-gap share nominal p=0.024, not significant after correction. |
| Best alternative tested | any of 11 tested features differs from normal (none after Bonferroni) |
| Economic interpretation (interpretation, not evidence) | A recall happens after sending, so message fields cannot reveal it. |
| Limitations | Label not documented in official materials. |
| Related rules | — |
| Evidence IDs | EV-RULE-027, EV-VAL-027, EV-STAT-001, EV-STAT-002, EV-STAT-003, EV-STAT-004, EV-STAT-005, EV-STAT-006 |

### X6 — Anomaly label is independent of routing type

**Feature group:** Anomaly · **Confidence:** STRONGLY SUPPORTED · **Validator type:** B · **Validator result:** PASS on 1 partitions

| Item | Content |
|---|---|
| Research question / hypothesis | Anomaly label independent of routing type. |
| Initial hypothesis (log) | no separate log entry (formulated directly from the discovery scan) |
| Formal formulation | ANOMALY_TYPE is assigned independently of TRANSACTION_TYPE |
| Executable logic | χ² + Cramér's V on the 7 × 3 table |
| Variables | ANOMALY_TYPE, TRANSACTION_TYPE_CODE |
| Method | Chi-square + Cramér's V. |
| Acceptance criterion | Cramér's V(anomaly × ttype) < 0.01 |
| Sample size | 10,000,000 (full data) |
| Effect size | cramers_v = 0.003196 |
| Uncertainty | single-partition metric |
| Counterexamples / scope |  |
| Best alternative tested | — |
| Economic interpretation (interpretation, not evidence) | Anomalies injected after routing is generated. |
| Limitations | - |
| Related rules | — |
| Evidence IDs | EV-RULE-028, EV-VAL-028 |

*Split metrics*

| Metric | full |
|---|---|
| chi2 | 204.3 |
| p | 4.307e-37 |
| dof | 12 |
| cramers_v | 0.003196 |

### F1 — Fingerprint: USD-denominated amounts keep whole-unit roundness (≈39% .00) while converted currencies have uniform cents (≈1%)

**Feature group:** Currency & Value · **Confidence:** STRONGLY SUPPORTED · **Validator type:** D · **Validator result:** PASS on 5 partitions

| Item | Content |
|---|---|
| Research question / hypothesis | How amounts were produced: drawn in USD, or drawn in the payment currency and converted? |
| Initial hypothesis (log) | H36: Amounts drawn directly in USD — Rejected: USD 39% whole units vs 1.0% for converted currencies; H37: Conversion uses one fixed rate per currency — Not supported (≈2% vs 1.2% baseline) |
| Formal formulation | USD-denominated amounts keep whole-unit roundness (≈39% end .00, ≈16% multiples of 100); non-USD amounts have uniform cents (≈1%) |
| Executable logic | share of round(amount·100) mod 100 = 0 by currency = USD; fixed-rate search for EUR/GBP/CHF (negative) |
| Variables | USD_AMOUNT, CURRENCY_CODE |
| Method | Cents-digit distribution by currency; multiples of 100; search for a fixed FX rate that restores round originals (EUR/GBP/CHF). |
| Acceptance criterion | USD whole-unit share > 0.30 and non-USD share in [0.008,0.013] on every split |
| Sample size | 1,702,039 (n_usd) |
| Effect size | usd_whole_share = 0.3864 |
| Uncertainty | usd_whole_share ranges 0.386 – 0.3867 across the five partitions |
| Counterexamples / scope | No single fixed rate restores round originals for EUR/GBP/CHF (best near-integer share ≈2% vs 1.2% baseline) — conversion mechanism not identified. |
| Best alternative tested | amounts drawn directly in USD (USD-only roundness contradicts) |
| Economic interpretation (interpretation, not evidence) | Invoices are typically issued in round units of the invoicing currency; USD is the only currency that needs no conversion to USD. |
| Limitations | Roundness of non-USD originals cannot be observed after conversion. |
| Related rules | — |
| Evidence IDs | EV-RULE-029, EV-VAL-029 |

*Split metrics*

| Metric | full | half_0 | half_1 | P1 | P2 |
|---|---|---|---|---|---|
| usd_whole_share | 0.3864 | 0.3862 | 0.3866 | 0.3867 | 0.386 |
| non_usd_whole_share | 0.009885 | 0.0099 | 0.00987 | 0.01016 | 0.009648 |
| n_usd | 1,702,039 | 851,084 | 850,955 | 787,151 | 914,888 |

### T4b — Weekly volume levels are piecewise-constant with every change point on a Monday (week boundary)

**Feature group:** Temporal · **Confidence:** STRONGLY SUPPORTED · **Validator type:** B · **Validator result:** PASS on 1 partitions

| Item | Content |
|---|---|
| Research question / hypothesis | Do weekly levels change at random times or at week boundaries? |
| Initial hypothesis (log) | H35: Weekly levels change at arbitrary dates — Rejected: 10/10 change points on Mondays |
| Formal formulation | level(week) is piecewise-constant and changes only at week boundaries (Mondays) |
| Executable logic | binary segmentation of weekday-normalised log volume with BIC penalty 2·ln(n)·σ̂² |
| Variables | EPOCH_SECONDS |
| Method | Binary segmentation with BIC penalty on weekday-normalised log daily volume (91 full days); residual normality. |
| Acceptance criterion | binary segmentation (BIC penalty) on weekday-normalised log volume: ≥1 change point, 100% on Mondays, residual sd < 0.03 |
| Sample size | 10,000,000 (full data) |
| Effect size | see metrics |
| Uncertainty | single-partition metric |
| Counterexamples / scope | Several adjacent weeks share a level (segments of 1–3 weeks). |
| Best alternative tested | — |
| Economic interpretation (interpretation, not evidence) | Volume plans are set per week (business calendars), not per day. |
| Limitations | 13 weeks only; cause of the levels still open (T4). |
| Related rules | T3, T4 |
| Evidence IDs | EV-RULE-030, EV-VAL-030 |

*Split metrics*

| Metric | full |
|---|---|
| change_points | 10 |
| share_on_monday | 1 |
| residual_sd_log | 0.01831 |
| segments | 11 |

### G3 — Intermediaries drawn i.i.d. with replacement ∝ bank size — predicts the path revisit (loop) rate

**Feature group:** Route · **Confidence:** VALIDATED · **Validator type:** E · **Validator result:** PASS on 5 partitions

| Item | Content |
|---|---|
| Research question / hypothesis | Loops in paths (a bank visited twice) are a by-product of independent size-weighted intermediary draws. |
| Initial hypothesis (log) | H27: Path loops are deliberate — Rejected as deliberate: i.i.d. draws with replacement predict loops within 3.1% |
| Formal formulation | Intermediaries are drawn i.i.d. with replacement, P(b) ∝ size(b)^β with β ≈ 1 |
| Executable logic | P(revisit \| K) = 1 − Π_{j=1}^{K−1}(1 − j·Σ_b p_b²)  · src/rules.py g3 |
| Variables | BIC8_PATH |
| Method | Birthday-problem prediction from the intermediary collision probability Σp²; size exponent by log-log fit; per split. |
| Acceptance criterion | size exponent β∈[0.9,1.1]; predicted vs observed intermediary-repeat rate within 10% relative for pc 4–8 on every split |
| Sample size | 10,000,000 (full data) |
| Effect size | max_rel_err = 0.0306 |
| Uncertainty | max_rel_err ranges 0.0271 – 0.06166 across the five partitions |
| Counterexamples / scope | pc=8–9 within 3%; no residual excess of loops. largest relative error 3.1% |
| Best alternative tested | — |
| Economic interpretation (interpretation, not evidence) | Hubs appear repeatedly because the generator samples correspondents with replacement — real routes would avoid loops. |
| Limitations | Assumes the same size distribution at every position. |
| Related rules | R1, R3 |
| Evidence IDs | EV-RULE-031, EV-VAL-031 |

*Split metrics*

| Metric | full | half_0 | half_1 | P1 | P2 |
|---|---|---|---|---|---|
| max_rel_err | 0.0306 | 0.05183 | 0.05951 | 0.06166 | 0.0271 |
| pc7_obs | 0.05701 | 0.05871 | 0.05531 | 0.05677 | 0.05722 |
| pc6_obs | 0.03514 | 0.03522 | 0.03506 | 0.03345 | 0.03661 |
| pc4_obs | 0.006031 | 0.006057 | 0.006005 | 0.005959 | 0.006094 |
| pc5_obs | 0.01749 | 0.01702 | 0.01795 | 0.01722 | 0.01771 |
| pc8_obs | 0.08468 | 0.08551 | 0.08388 | 0.08222 | 0.08685 |
| pc7_pred | 0.05881 | 0.05881 | 0.05881 | 0.05881 | 0.05881 |
| pc6_pred | 0.03564 | 0.03564 | 0.03564 | 0.03564 | 0.03564 |
| pc4_pred | 0.006006 | 0.006006 | 0.006006 | 0.006006 | 0.006006 |

### G1 — Sender and receiver banks are NOT paired independently (directional affinities) — independence rejected

**Feature group:** Institution · **Confidence:** INCONCLUSIVE · **Validator type:** C · **Validator result:** PASS on 1 partitions

| Item | Content |
|---|---|
| Research question / hypothesis | Sender and receiver banks are paired independently (configuration model). |
| Initial hypothesis (log) | H26: Sender and receiver banks are paired independently — Rejected: 358 / 125 / 287; affinities directional (r = 0.11) |
| Formal formulation | Sender and receiver banks are NOT paired independently; pair counts deviate from n_i·n_j/N even within country pairs and unique relationships |
| Executable logic | Pearson χ²/dof of O vs E = n_o·n_b/N over pairs with E ≥ 5 |
| Variables | ORDERING_BIC8, BENEFICIARY_BIC8 |
| Method | Pearson χ²/dof of pair counts vs product-of-margins expectation, on raw payments, unique account relationships and within country pairs; affinity symmetry. |
| Acceptance criterion | χ²/dof > 10 for raw pairs, unique relationships and within country pairs; country affinity symmetry r < 0.3 |
| Sample size | 10,000,000 (full data) |
| Effect size | chi2_dof_raw = 358.2 |
| Uncertainty | single-partition metric |
| Counterexamples / scope | Independence REJECTED in all three; domestic pairs 1.2× expected; affinities directional (r = 0.11). |
| Best alternative tested | configuration-model pairing (χ²/dof 125–358) |
| Economic interpretation (interpretation, not evidence) | Real correspondent networks are relationship-driven; the generator encodes directional bank-to-bank preferences. |
| Limitations | Mechanism of the affinity (bank-level preference lists?) not identified. |
| Related rules | — |
| Evidence IDs | EV-RULE-032, EV-VAL-032, EV-DISC-011, EV-DISC-013, EV-DISC-014 |

*Split metrics*

| Metric | full |
|---|---|
| chi2_dof_raw | 358.2 |
| chi2_dof_unique | 125.4 |
| chi2_dof_within_country | 286.6 |
| domestic_affinity | 1.201 |
| affinity_symmetry_r | 0.1056 |
| country_cramers_v | 0.1225 |

### A3 — Within-country log-amount residual is Normal (lognormal amounts, no power-law tail)

**Feature group:** Currency & Value · **Confidence:** STRONGLY SUPPORTED · **Validator type:** B · **Validator result:** PASS on 5 partitions

| Item | Content |
|---|---|
| Research question / hypothesis | Amounts are lognormal, not heavy-tailed power law. |
| Initial hypothesis (log) | H28: Amounts have a power-law tail — Rejected; lognormal (Hill α 2.21 → 1.21; exceedances within 1–15%) |
| Formal formulation | Within-country residual of ln(amount) is Normal → amounts lognormal; no power-law tail |
| Executable logic | skew, excess kurtosis, KS D vs N(0,1); Hill α(k) drift; model exceedances |
| Variables | USD_AMOUNT |
| Method | Within-country residual moments, KS vs Normal, Hill estimator drift, model-implied exceedances $100k–$1bn. |
| Acceptance criterion | \|skew\|<0.05, \|excess kurtosis\|<0.1, KS D<0.01 on every split; Hill α drifts (>0.5 between k=100 and k=100k) |
| Sample size | 10,000,000 (full data) |
| Effect size | ks_D = 0.003462 |
| Uncertainty | sd ranges 2.072 – 2.087 across the five partitions |
| Counterexamples / scope | Exceedance ratio 0.86 at $100M (132 vs 154 predicted, z≈−1.7). |
| Best alternative tested | — |
| Economic interpretation (interpretation, not evidence) | Payment sizes multiply many factors (firm size, invoice size) → lognormal; extreme tickets come from errors, not a fat natural tail. |
| Limitations | Fat-finger rows excluded; top 1,000 amounts are 26.5% fat finger. |
| Related rules | — |
| Evidence IDs | EV-RULE-033, EV-VAL-033 |

*Split metrics*

| Metric | full | half_0 | half_1 | P1 | P2 |
|---|---|---|---|---|---|
| sd | 2.08 | 2.081 | 2.077 | 2.087 | 2.072 |
| skew | -0.02395 | -0.01987 | -0.02831 | -0.02697 | -0.02074 |
| excess_kurtosis | 0.006827 | -0.02221 | 0.03694 | 0.002299 | 0.008869 |
| ks_D | 0.003462 | 0.003673 | 0.003105 | 0.002898 | 0.004458 |
| hill_alpha_k100 | 2.209 | — | — | — | — |
| hill_alpha_k100000 | 1.212 | — | — | — | — |

### D3 — Manual processing step ≈ Gamma(shape≈2, scale≈820 s); fast step pair ≈ Gamma(3, 8.7 s)

**Feature group:** Duration & Continuity · **Confidence:** SUPPORTED · **Validator type:** B · **Validator result:** PASS on 1 partitions

| Item | Content |
|---|---|
| Research question / hypothesis | The manual step has a specific distribution. |
| Initial hypothesis (log) | H29: Manual step is lognormal — Gamma(2) fits better (KS 0.023 vs 0.066) |
| Formal formulation | Manual step ~ Gamma(k ≈ 2, θ ≈ 817 s); two fast steps ~ Gamma(k ≈ 3.1, θ ≈ 8.7 s) |
| Executable logic | MLE gamma fit (loc = 0) vs lognormal; KS D |
| Variables | TOTAL_DURATION |
| Method | Gamma vs lognormal MLE fits with KS on manual-step and fast-pair durations. |
| Acceptance criterion | manual-step gamma shape∈[1.6,2.5] and KS D<0.05 better than lognormal; fast-pair gamma shape∈[2.5,3.6], KS D<0.05 |
| Sample size | 10,000,000 (full data) |
| Effect size | see metrics |
| Uncertainty | single-partition metric |
| Counterexamples / scope | Manual tail up to 21,649 s on multi-hop routes. |
| Best alternative tested | — |
| Economic interpretation (interpretation, not evidence) | Manual handling ≈ two exponential stages (queue + review) → Gamma(2). |
| Limitations | Fitted on pc=2 rows with exactly one slow bank. |
| Related rules | D1 |
| Evidence IDs | EV-RULE-034, EV-VAL-034 |

*Split metrics*

| Metric | full |
|---|---|
| manual_shape | 2.045 |
| manual_scale_s | 817.1 |
| manual_ks_gamma | 0.02321 |
| manual_ks_lognormal | 0.06561 |
| fast_pair_shape | 3.062 |
| fast_pair_scale_s | 8.734 |
| fast_ks | 0.03105 |
| n_manual | 101,844 |
| n_fast | 222,900 |

## 9. The mathematics behind the findings

**Geometric and exponential (R1).** If E ~ Exponential(1) then P(⌊E⌋ ≥ k) = P(E ≥ k) = e^(−k), so K = ⌊E⌋ has P(K = k) = e^(−k)(1 − e^(−1)) — a geometric distribution with continuation probability q = 1/e ≈ 0.3679. *Worked example:* P(Direct) = P(K = 0) = 1 − 1/e = 0.6321; observed 0.6323. The ratio P(K = k+1)/P(K = k) should be constant at q; observed ratios 0.3676, 0.3680, 0.3671, 0.3685. The MLE for a geometric with mean K̄ is q̂ = K̄/(1 + K̄) = 0.3677.

**Cohen's w.** For observed shares pᵢ and model shares p₀ᵢ, w = √Σ (pᵢ − p₀ᵢ)²/p₀ᵢ = √(χ²/n). R1: χ² = 3.347, n = 10,000,000 → w = √(3.347/10,000,000) = 0.00058. Conventionally w < 0.1 is small; our acceptance bound was 0.01.

**Exact-match share (C2).** share = (rows where predicted = recorded)/n = (10,000,000 − 2)/10,000,000 = 0.9999998. Alternative “distinct currencies − 1”: 0.9168.

**Cramér's V.** For an r × c contingency table with χ² statistic, V = √(χ² / (n·(min(r, c) − 1))) ∈ [0, 1]. It is the discovery engine's dependency measure and the independence criterion for R2 (V of routing type vs K < 0.01) and X6.

**Lognormal amounts (A1, A3).** ln(amount) = β₀ + β_S·[sender = B] + β_R·[receiver = B] + ε. Fitted: β₀ = 6.062, β_S = 1.932, β_R = 1.965, interaction 0.039. So each business party multiplies the typical amount by about e² ≈ 7.4. The residual after sender-country effects has sd 2.080, skew -0.018, excess kurtosis 0.019, KS D vs normal 0.0034. The Hill tail index drifts (2.21, 1.98, 1.83, 1.67, 1.58, 1.38, 1.21), the signature of a lognormal rather than a power-law tail; the 6 + 2 + 2 coefficients are fitted values close to round numbers, not exact constants.

**Gamma steps (D1, D3).** Each bank adds a step: fast ~ Gamma(k = 1.53, θ = 8.73 s) or, with probability m, manual ~ Gamma(k = 2.04, θ = 817 s) (mean kθ ≈ 1671 s). With two banks the manual share is 1 − (1 − m)²; solving with the observed 0.405 gives m = 0.2286. Additivity: two slow banks take ≈ 1.89× one slow bank out of sample (2.0 under pure additivity).

**Fixed effects and Simpson's paradox (D2).** A raw contrast (slow share by hour) mixes the hour effect with which banks are active at that hour. Regressing on sender-bank and receiver-bank indicators (two-way fixed effects) and then reading the hour coefficients removes that composition; the hour range falls from 0.037 to 0.003. A pattern that disappears after adjustment is a Simpson effect, not a generator rule.

**Confidence intervals.** Proportions use Wilson intervals; the geometric q uses the Fisher-information standard error √(q(1 − q)²/n). At n = 10⁷ intervals are ±0.0003 or narrower, so decisions rest on effect size.

**Multiplicity.** Bonferroni controls the family-wise error by testing at α/m (used inside validators, e.g. X5 with m = 11). Benjamini–Hochberg controls the false-discovery rate: sort p-values p₍₁₎ ≤ … ≤ p₍ₘ₎ and reject up to the largest i with p₍ᵢ₎ ≤ (i/m)α; it is applied *within* each of the test families of the registry (297 tests), never pooled across unrelated families.

**Graph analysis (G1, G3).** Banks are nodes and hops are weighted edges. G3 predicts the share of paths that revisit a bank if intermediaries are drawn i.i.d. with probability ∝ size: 1 − Π_{j}(1 − j·Σp²) (a birthday-problem form); predicted and observed agree within 3.1%. G1 compares observed sender–receiver pair counts with a configuration model that preserves each bank's totals; χ²/dof far above 1 rejects independent pairing, but does not identify the mechanism.

## 10. Generator reconstruction

The reconstructed generator by stage. Mechanisms come only from rules; parts we could not pin down are listed as unresolved.

**1. Temporal generation** — when a payment is stamped

- T1 (STRONGLY SUPPORTED): Timestamp drawn on the instructing bank's local clock (fixed January UTC offsets): office curve starting 07:00
- T3 (STRONGLY SUPPORTED): Local weekday shares Mon 18.9 · Tue 17.0 · Wed 17.0 · Thu 18.0 · Fri 18.9 · Sat 3.6 · Sun 6.5 % for every country
- T4 (INCONCLUSIVE): Weekly volume = base × level(week), the same level for every country
- T4b (STRONGLY SUPPORTED): level(week) is piecewise-constant and changes only at week boundaries (Mondays)
- *Unresolved / partly inferred:* T4: Only 13 full weeks.

**2. Payment amount generation** — how large it is

- A1 (STRONGLY SUPPORTED): ln(USD_AMOUNT) ~ Normal(6 + 2·[ORDERING_TYPE=B] + 2·[BENEFICIARY_TYPE=B] + c_country + b_bank, σ ≈ 2.08)
- A2 (SUPPORTED): Sending-country level c_country shifts ln(amount) (≈ −3.2 … +2.0); beneficiary country has ≈ no effect
- A3 (STRONGLY SUPPORTED): Within-country residual of ln(amount) is Normal → amounts lognormal; no power-law tail
- F1 (STRONGLY SUPPORTED): USD-denominated amounts keep whole-unit roundness (≈39% end .00, ≈16% multiples of 100); non-USD amounts have uniform cents (≈1%)
- *Unresolved / partly inferred:* A2: Bank-level variance (0.22) not decomposed further.

**3. Currency selection** — which currency it is sent in

- C1 (SUPPORTED): CURRENCY_CODE = home currency of the instructing bank with probability ≈ 0.93 (country-specific 0.73–0.98)
- C3 (STRONGLY SUPPORTED): CURRENCY_CODE is drawn from the route: home currency of path[1] (≈95% if direct), else the receiver bank's currency (≈3.8%), else an intermediary's currency (≈+2.4 pts per intermediary), else a global vehicle (≈1.3%)
- R5b (SUPPORTED): On replaced rows, CURRENCY_CODE and the local clock follow path[1] (instructing bank); account IBAN and ordering address follow ORDERING_BIC8 (account-servicing bank)
- *Unresolved / partly inferred:* C1: Vehicle-currency selection mechanism not fully identified. · R5b: Relies on our data-derived country→currency map.

**4. Institution assignment** — which banks send, relay and receive

- R3 (STRONGLY SUPPORTED): Intermediaries are sampled with probability proportional to bank activity, not from the payment-currency zone
- G3 (VALIDATED): Intermediaries are drawn i.i.d. with replacement, P(b) ∝ size(b)^β with β ≈ 1
- G1 (INCONCLUSIVE): Sender and receiver banks are NOT paired independently; pair counts deviate from n_i·n_j/N even within country pairs and unique relationships
- P5 (STRONGLY SUPPORTED): Each bank has its own business-customer share on the sending side and on the receiving side
- R5 (STRONGLY SUPPORTED): With probability 0.05 the first known path BIC is replaced by another bank; independently, with probability 0.05 the last known BIC is replaced
- *Unresolved / partly inferred:* G1: Mechanism of the affinity (bank-level preference lists?) not identified.

**5. Routing construction** — how many hops, which type, what is hidden

- R1 (VALIDATED): Number of intermediaries K ~ ⌊Exp(1)⌋; PARTICIPANT_COUNT = K + 2
- R2 (STRONGLY SUPPORTED): Among non-direct routes, TRANSACTION_TYPE = Covered with a sending-bank propensity π_b (cover banks π ≈ 0.6–0.8, others π ≈ 0.05); independent of K
- R4 (VALIDATED): Each link between consecutive known BICs is hidden ('...') independently with p = 0.05; extra '...' per hidden link ~ Geometric(0.05)
- R7 (VALIDATED): CONTINUITY_QFLAG := 'N' if BIC8_PATH contains '...', else 'Y'

**6. Participant & FX mechanics** — derived counts

- R6 (VALIDATED): PARTICIPANT_COUNT := number of BIC8 entries in BIC8_PATH that are not '...'
- C2 (VALIDATED): CURRENCY_CONVERSION_COUNT := Σ over consecutive known BICs of 1[home_ccy(country(bᵢ)) ≠ home_ccy(country(bᵢ₊₁))]

**7. Duration generation** — how long settlement takes

- D1 (SUPPORTED): TOTAL_DURATION ≈ Σ over participating banks of a step: fast (seconds) with probability STP(b), manual otherwise
- D2 (SUPPORTED): Manual-step probability depends on the bank only, not on hour, weekday or amount
- D3 (SUPPORTED): Manual step ~ Gamma(k ≈ 2, θ ≈ 817 s); two fast steps ~ Gamma(k ≈ 3.1, θ ≈ 8.7 s)
- *Unresolved / partly inferred:* D1: Exact step distributions not fitted. · D2: Linear-probability FE approximation. · D3: Fitted on pc=2 rows with exactly one slow bank.

**8. Party-detail generation** — accounts, IBANs and party types

- P2 (VALIDATED): Account is IBAN-formatted only for banks in IBAN countries; IBAN country prefix = BIC country; one IBAN length per country
- P4 (SUPPORTED): Ordering address country = ORDERING_BIC8 country; beneficiary address country is drawn independently of BENEFICIARY_BIC8
- P1b (STRONGLY SUPPORTED): BENEFICIARY_TYPE is drawn independently of ORDERING_TYPE
- *Unresolved / partly inferred:* P4: 39% of details carry no country token.

**9. Token generation** — engineered token summaries of the details fields

- P1b (STRONGLY SUPPORTED): BENEFICIARY_TYPE is drawn independently of ORDERING_TYPE
- *Note:* Token fields are engineered pattern summaries supplied with the data, not original text. We measured their presence and co-occurrence (Token page) but found no generator rule beyond the layout and party-type structure in P1b/P4 — this section is deliberately thin rather than padded.

**10. Anomaly labelling** — how labels are injected

- X1 (STRONGLY SUPPORTED): ROMANCE_SCAM: consumer → same beneficiary, 2–8 payments minutes apart, each ≈ ×1.5 the previous; all labelled
- X2 (VALIDATED): DUPLICATE_PAYMENT: 2–5 identical copies (sender, beneficiary, amount, path, duration) within ≤ 2 h; every copy labelled
- X3 (SUPPORTED): FAT_FINGER_MISTAKE: amount × 100 (≈77%) or ÷ 100 (≈23%)
- X4 (SUPPORTED): CEO / ACCOUNT_REPLACEMENT scams pay accounts that receive only anomalous money (mules) at small, often manual banks
- X5 (INCONCLUSIVE): CUSTOMER_RECALL rows are statistically indistinguishable from normal rows on all tested features
- X6 (STRONGLY SUPPORTED): ANOMALY_TYPE is assigned independently of TRANSACTION_TYPE
- *Unresolved / partly inferred:* X3: Expectation model has its own noise. · X4: Mule definition is data-driven. · X5: Label not documented in official materials.

Deterministic steps (exact on all rows): R6, R7, C2, P2, X2 and Direct ⇔ 2 participants. All other steps are stochastic draws with fitted parameters.

## 11. Economic interpretation

Readings below are interpretation, labelled as such; synthetic patterns do not prove real network behaviour.

| Rule | Observed in the data | Plausible real-world reading |
|---|---|---|
| R6 | PARTICIPANT_COUNT = number of known BICs in BIC8_PATH | Counts observed institutions only, i.e. what the messaging layer can see. |
| R7 | CONTINUITY_QFLAG = 'N' iff path contains '...' | A leg left the observed channel (e.g. a domestic clearing leg). |
| R5 | Path endpoints differ from ORDERING/BENEFICIARY_BIC8 independently with p≈0.05 each | Ordering institution (account servicer, MT field 52) ≠ instructing agent that sends the message — common when a smaller bank uses a correspondent to send. |
| R5b | On endpoint mismatch, currency follows the path's first bank; account/IBAN follows ORDERING_BIC8 | The instructing bank books and times the payment; the customer's account stays at the servicing bank. |
| R1 | Intermediaries K = floor(Exp(1)): P(K=k) = (1-1/e)e^-k | Each extra correspondent hop is a fixed-probability event; most payments have a direct relationship. |
| R2 | Covered vs Indirect is a per-sending-bank propensity (cover-prone banks ≈61%, others ≈7%, out of sample), independent of route length | The cover method (MT103 direct + MT202 COV through correspondents) is a bank's operating choice — some institutions habitually settle by cover. |
| R4 | Each link hidden with p=0.05: P(N \| pc) = 1-0.95^(pc-1) | Each inter-bank leg independently may run outside the observed network. |
| R3 | Intermediaries chosen in proportion to bank size, not by payment currency | Large banks hold the most nostro accounts and act as hubs. |
| C2 | FX count = adjacent known-BIC pairs with different home currencies | Each correspondent converts into the currency of its next nostro account; conversions happen at currency borders. |
| C3 | Payment currency is drawn from the currencies on the route: first bank ≈ 95% (direct), receiver bank ≈ 3.8%, +≈2.4 pts per intermediary, outside-route vehicle ≈ 1.3% | A payment is denominated in a currency some bank in the chain can book: the sender's (most), the receiver's, or a correspondent's clearing currency; otherwise a global vehicle currency. |
| C1 | Payment currency = home currency of the instructing (first-path) bank ~93% | Local-currency funding; invoices in global vehicle currencies. |
| A1 | ln(amount) = 6 + 2·[O=B] + 2·[B=B], σ≈2.28 (no interaction) | Commercial flows ≫ personal flows; B2B largest. |
| A2 | Ordering-country effect replicates across independent halves (beneficiary country ≈ no effect) | GDP-like scaling of ticket size at origin. |
| D1 | Duration = sum of per-bank steps; bank speed class learned on half_0 predicts half_1 | STP vs manual repair/compliance review. |
| D2 | Manual (slow) processing is a bank attribute: hour/weekday/amount effects vanish once bank fixed effects are removed | Automation level is an institution attribute. |
| T1 | Activity follows the instructing bank's local clock (fixed offsets) | Office-hours behaviour; cut-off driven submissions. |
| T3 | One weekday shape for all countries (local weekday) | Sunday batch preparation > Saturday. |
| T4 | Weekly volume multiplier is global (shared by all countries) | Possibly calendar-driven (month/quarter end). |
| P2 | IBAN prefix always equals BIC country; IBAN used only by IBAN-country banks | Regulatory account-number standards. |
| P4 | Ordering party lives in its bank's country; beneficiary residence is decoupled from its bank | Generator samples beneficiary residence by population, bank by banking size — a modelling shortcut. |
| P5 | Customer-type mix is a bank attribute: each bank has its own business share of senders and of receivers | Banks specialise: corporate banks vs retail banks serve different customer mixes. |
| P1b | Beneficiary type independent of ordering type | Independent sampling per side. |
| X1 | ROMANCE_SCAM: consumer bursts of 2-8 escalating payments (×~1.5 each) | Escalating repeated transfers by a groomed victim. |
| X2 | DUPLICATE_PAYMENT: 2-5 identical copies (amount, path, duration) within 2h; all copies labelled | Back-office race condition resends the same instruction. |
| X3 | FAT_FINGER_MISTAKE: amount ×100 or ÷100 relative to expectation | Comma/dot decimal-separator confusion. |
| X4 | CEO & ACCOUNT_REPLACEMENT scams pay mule accounts at small banks | Fraud proceeds concentrate in mule accounts at weaker-control banks. |
| X5 | CUSTOMER_RECALL has no observable signature (negative result) | A recall happens after sending, so message fields cannot reveal it. |
| X6 | Anomaly label is independent of routing type | Anomalies injected after routing is generated. |
| F1 | Fingerprint: USD-denominated amounts keep whole-unit roundness (≈39% .00) while converted currencies have uniform cents (≈1%) | Invoices are typically issued in round units of the invoicing currency; USD is the only currency that needs no conversion to USD. |
| T4b | Weekly volume levels are piecewise-constant with every change point on a Monday (week boundary) | Volume plans are set per week (business calendars), not per day. |
| G3 | Intermediaries drawn i.i.d. with replacement ∝ bank size — predicts the path revisit (loop) rate | Hubs appear repeatedly because the generator samples correspondents with replacement — real routes would avoid loops. |
| G1 | Sender and receiver banks are NOT paired independently (directional affinities) — independence rejected | Real correspondent networks are relationship-driven; the generator encodes directional bank-to-bank preferences. |
| A3 | Within-country log-amount residual is Normal (lognormal amounts, no power-law tail) | Payment sizes multiply many factors (firm size, invoice size) → lognormal; extreme tickets come from errors, not a fat natural tail. |
| D3 | Manual processing step ≈ Gamma(shape≈2, scale≈820 s); fast step pair ≈ Gamma(3, 8.7 s) | Manual handling ≈ two exponential stages (queue + review) → Gamma(2). |

## 12. Validation and robustness

| Rule | Level | Acceptance criterion | Result |
|---|---|---|---|
| R6 | VALIDATED | share_exact == 1 | PASS on 5 splits (P1, P2, full, half_0, half_1) |
| R7 | VALIDATED | share_exact == 1 | PASS on 5 splits (P1, P2, full, half_0, half_1) |
| R5 | STRONGLY SUPPORTED | first & last mismatch in [0.045,0.055] and joint/product ratio in [0.9,1.1] | PASS on 5 splits (P1, P2, full, half_0, half_1) |
| R5b | SUPPORTED | home-ccy share via path[1] > 0.85 and via ORDERING_BIC8 < 0.25; IBAN prefix = ORDERING_BIC8 country == 1 | PASS on 5 splits (P1, P2, full, half_0, half_1) |
| R1 | VALIDATED | MLE continuation q within ±0.005 of 1/e and Cohen's w < 0.01 on every split | PASS on 5 splits (P1, P2, full, half_0, half_1) |
| R2 | STRONGLY SUPPORTED | Cramér's V(type×K) < 0.01 on every split; out-of-sample: banks classed as cover banks on half_0 send >50% Covered on half_1, others <10% | PASS on 5 splits (P1, P2, full, half_0, half_1) |
| R4 | VALIDATED | max \|obs-pred\| over pc 2..7 < 0.006 | PASS on 5 splits (P1, P2, full, half_0, half_1) |
| R3 | STRONGLY SUPPORTED | corr(log intermediary uses, log payments sent) > 0.9; share in payment-currency zone < 0.25 | PASS · full-data / out-of-sample test |
| C2 | VALIDATED | share_exact >= 0.99999 | PASS on 5 splits (P1, P2, full, half_0, half_1) |
| C3 | STRONGLY SUPPORTED | ≥98% of payments in a route-bank currency on every split; receiver-only share stable across route lengths (range < 0.006); intermediary-only share rises ≈ linearly per intermediary (slope 0.02–0.035) | PASS on 5 splits (P1, P2, full, half_0, half_1) |
| C1 | SUPPORTED | share in [0.91,0.95] on every split; per-country share range reported | PASS on 5 splits (P1, P2, full, half_0, half_1) |
| A1 | STRONGLY SUPPORTED | intercept∈[5.9,6.2], both effects∈[1.85,2.15], \|interaction\|<0.1, σ spread across cells <0.03 | PASS on 5 splits (P1, P2, full, half_0, half_1) |
| A2 | SUPPORTED | corr(country effect half_0, half_1) > 0.95; sd(ordering effects) > 3×sd(beneficiary effects) | PASS · full-data / out-of-sample test |
| D1 | SUPPORTED | out-of-sample: fast→fast slow-share < 0.2, any slow bank > 0.9, median(slow,slow)/median(one slow) in [1.6,2.4] | PASS · full-data / out-of-sample test |
| D2 | SUPPORTED | after two-way (sender bank, receiver bank) demeaning among fast-fast pairs: residual range across UTC hours < 0.015, weekdays < 0.015, \|corr with ln amount\| < 0.02 | PASS · full-data / out-of-sample test |
| T1 | STRONGLY SUPPORTED | night share (01-05h local) < 0.06 on every split vs > 0.15 with UTC | PASS on 5 splits (P1, P2, full, half_0, half_1) |
| T3 | STRONGLY SUPPORTED | max deviation of any country's weekday share from pooled share < 0.01 (countries ≥50k rows) | PASS · full-data / out-of-sample test |
| T4 | INCONCLUSIVE | min corr of weekly volume between top-10 countries and the total > 0.98 | PASS · full-data / out-of-sample test |
| P2 | VALIDATED | prefix match == 1; countries with 0<share<0.5 == 0 | PASS on 5 splits (P1, P2, full, half_0, half_1) |
| P4 | SUPPORTED | ordering match == 1, beneficiary match < 0.02 on every split | PASS on 5 splits (P1, P2, full, half_0, half_1) |
| P5 | STRONGLY SUPPORTED | split-half correlation of bank-level business share > 0.95 on both sides (banks ≥200 rows per half); within-country dispersion ≫ binomial | PASS · full-data / out-of-sample test |
| P1b | STRONGLY SUPPORTED | \|P(bB\|oB)-P(bB\|oC)\| < 0.005 | PASS on 5 splits (P1, P2, full, half_0, half_1) |
| X1 | STRONGLY SUPPORTED | sender C share == 1; within-series ln step in [0.3,0.5]; every series fully labelled | PASS · full-data / out-of-sample test |
| X2 | VALIDATED | every group has 1 path & 1 duration; span ≤ 7200s; sizes ⊂ {2..5} | PASS · full-data / out-of-sample test |
| X3 | SUPPORTED | bimodal log10 residual: both modes within ±0.6 of ±2; up share in [0.65,0.9] | PASS · full-data / out-of-sample test |
| X4 | SUPPORTED | share of beneficiary accounts receiving only anomalous money > 0.35 (vs < 0.25 for error types) | PASS · full-data / out-of-sample test |
| X5 | INCONCLUSIVE | no feature differs from normal after Bonferroni (α=0.05/m) | PASS · full-data / out-of-sample test |
| X6 | STRONGLY SUPPORTED | Cramér's V(anomaly × ttype) < 0.01 | PASS · full-data / out-of-sample test |
| F1 | STRONGLY SUPPORTED | USD whole-unit share > 0.30 and non-USD share in [0.008,0.013] on every split | PASS on 5 splits (P1, P2, full, half_0, half_1) |
| T4b | STRONGLY SUPPORTED | binary segmentation (BIC penalty) on weekday-normalised log volume: ≥1 change point, 100% on Mondays, residual sd < 0.03 | PASS · full-data / out-of-sample test |
| G3 | VALIDATED | size exponent β∈[0.9,1.1]; predicted vs observed intermediary-repeat rate within 10% relative for pc 4–8 on every split | PASS on 5 splits (P1, P2, full, half_0, half_1) |
| G1 | INCONCLUSIVE | χ²/dof > 10 for raw pairs, unique relationships and within country pairs; country affinity symmetry r < 0.3 | PASS · full-data / out-of-sample test |
| A3 | STRONGLY SUPPORTED | \|skew\|<0.05, \|excess kurtosis\|<0.1, KS D<0.01 on every split; Hill α drifts (>0.5 between k=100 and k=100k) | PASS on 5 splits (P1, P2, full, half_0, half_1) |
| D3 | SUPPORTED | manual-step gamma shape∈[1.6,2.5] and KS D<0.05 better than lognormal; fast-pair gamma shape∈[2.5,3.6], KS D<0.05 | PASS · full-data / out-of-sample test |

Independent implementation: SQL vs pure Python on a 200,000-row sample — R6 100%, R7 100%, C2 100% agreement. Forensic replay recomputes exact supporting/contradicting counts directly from the Parquet; the C2 count equals the validator's exception count.

**Table 3. Forensic replay — exact counts over all eligible rows**

| Check | Eligible | Supporting | Contradicting |
|---|---|---|---|
| R6 | 10,000,000 | 10,000,000 | 0 |
| R7 | 10,000,000 | 10,000,000 | 0 |
| R1 | 10,000,000 | 10,000,000 | 0 |
| C2 | 10,000,000 | 9,999,998 | 2 |
| C3 | 10,000,000 | 9,873,143 | 126,857 |
| R5 | 10,000,000 | 9,027,029 | 972,971 |
| P2 | 5,048,042 | 5,048,042 | 0 |
| R1-tail | 5 | 5 | 0 |
| X3 | 1,940 | 1,485 | 455 |
| X2 | 679 | 679 | 0 |


**H38 (supported refinement of C3).** On routes with no EUR or USD bank, the payment is in EUR 1.41% and USD 0.75% of the time (full data); across the five partitions EUR ranges 1.39%–1.42%. 98,517 of 126,857 outside-route payments are EUR or USD. The EUR/USD set was chosen after inspection, so this is reported as supported, not validated; why these two currencies serve as vehicles is not identified.

## 13. Alternative hypotheses and negative findings

| Rule | Alternative tested and outcome |
|---|---|
| R5 | random label noise (rejected: swapped BIC predicts currency and clock) |
| R1 | Poisson hop counts (successive ratios not constant) |
| R2 | constant 11.3% Covered share (rejected: 3–50% by sending country, bank propensity) |
| R3 | intermediaries from the payment-currency zone (only 17% are) |
| C2 | FX = distinct currencies on route (91.7% on all rows); payment-currency start + borders (93.5%) |
| C3 | currency chosen before routing (cannot be excluded; route-first is the more parsimonious reading) |
| A2 | beneficiary-country wealth effect (sd 0.23 vs 1.09) |
| D2 | off-hours queuing (hour effect vanishes with bank fixed effects); large-amount review (reversed) |
| T3 | Fri–Sat weekend for Gulf/Israel (identical shape) |
| X4 | account-replacement reuses payee name with swapped account (1/649) |
| X5 | any of 11 tested features differs from normal (none after Bonferroni) |
| F1 | amounts drawn directly in USD (USD-only roundness contradicts) |
| G1 | configuration-model pairing (χ²/dof 125–358) |

**Table 4. Refuted hypotheses kept on the record**

| ID | Hypothesis | Test | Outcome |
|---|---|---|---|
| H1 | PARTICIPANT_COUNT counts path elements | equality on 10M | Rejected as stated; **pc = known BICs** (excl. `...`) exactly |
| H2 | Routing type depends on bank pair | purity of pairs; per-bank Direct share | Rejected: every bank ≈ 0.632 ± binomial noise |
| H3 | Hop count ~ Poisson | successive ratios | Rejected; ratios constant at 1/e → **geometric** |
| H4 | FX = distinct currencies on route | exact match | Rejected (91.7% on all 10M rows; 90.6% on the early sample) |
| H5 | FX = payment-currency start + borders | exact match | Rejected (93.5%) |
| H7 | Intermediaries sit in the payment-currency zone | share in zone | Rejected (17%) |
| H9 | Slow durations come from large-amount review | slow share by amount decile | Rejected (slightly reversed) |
| H12 | Amount depends on beneficiary country | effect sd | Rejected (sd 0.23 vs 1.09 ordering) |
| H13 | Individual accounts have own wealth level | variance component | Rejected (0.019 of 5.22) |
| H14 | Timestamps in UTC office hours | night share | Rejected; **local clock** |
| H15 | Local clock uses true DST offsets | offset estimation | Rejected; January offsets |
| H16 | Gulf/Israel banks have Fri–Sat weekend | weekday shares | Rejected; one universal shape |
| H17 | Header BICs equal path endpoints | 30-row sample showed 28/30; full data 95.0% | Rejected → independent 5% swap per end |
| H18 | On swaps, header BIC drives currency | home-ccy match by side | Rejected; path[1] drives currency & clock, header drives account/IBAN |
| H19 | Romance = C→C | type shares | Partly rejected: sender C 100%, receiver follows base mix |
| H20 | Duplicates: first copy unlabelled | label share by copy order | Rejected; every copy labelled |
| H22 | Account-replacement reuses legit payee name | name match with different account | Rejected (1/649) |
| H23 | Scams are slow because of added delay | stratified by bank speed | Rejected; scams sit at slow (small) banks |
| H24 | CUSTOMER_RECALL has a signature | 11 tests, Bonferroni | Rejected (no feature significant) |
| H26 | Sender and receiver banks are paired independently | χ²/dof vs product of margins (raw, unique relationships, within country pair) | **Rejected**: 358 / 125 / 287; affinities directional (r = 0.11) |
| H27 | Path loops are deliberate | birthday prediction from intermediary size distribution | Rejected as deliberate: i.i.d. draws with replacement predict loops within 3.1% |
| H28 | Amounts have a power-law tail | Hill estimator drift, exceedances vs lognormal | Rejected; lognormal (Hill α 2.21 → 1.21; exceedances within 1–15%) |
| H31 | CEO scam identifiable by a simple payee heuristic | precision/recall | Rejected: precision 0.03% |
| H32 | Covered share is constant across sending banks | discovery engine flag (V .095); bank dispersion 378× binomial; out-of-sample classes | **Rejected** → per-bank propensity (61% vs 6.7%) |
| H33 | Payment currency independent of route | currency position among route-bank currencies | Rejected: 98.7% in a route currency; receiver 3.8%; +2.4 pts per intermediary |
| H34 | Customer-type share set per country | bank-level split-half correlation | Rejected: bank attribute (r ≈ 0.99) |
| H35 | Weekly levels change at arbitrary dates | binary segmentation | Rejected: 10/10 change points on Mondays |
| H36 | Amounts drawn directly in USD | cents by currency | Rejected: USD 39% whole units vs 1.0% for converted currencies |
| H37 | Conversion uses one fixed rate per currency | near-integer search over rate grid | Not supported (≈2% vs 1.2% baseline) |

A negative result is informative: X5 shows that CUSTOMER_RECALL leaves no trace in the message fields we can observe (no test significant after correction), which bounds what any rule about it could say. It does not prove the generator applies no logic to that label.

## 14. Data integrity and governance

- Raw CSV is read-only; every stage asserts 10,000,000 rows.
- Only the supplied data enters rule discovery; external sources support interpretation only.
- The web platform ships aggregates and at most 75 de-identified records per replay check (no accounts, names, free text or tokens; row ids hashed); the raw data and row-level Parquet are never redistributed.
- The site is protected (team-only) until the competition deadline.
- Every artefact is fingerprinted with SHA-256 (`outputs/evidence/lineage.json`).

## 15. Limitations and unresolved questions

- **R5b** (SUPPORTED): Relies on our data-derived country→currency map.
- **C1** (SUPPORTED): Vehicle-currency selection mechanism not fully identified.
- **A2** (SUPPORTED): Bank-level variance (0.22) not decomposed further.
- **D1** (SUPPORTED): Exact step distributions not fitted.
- **D2** (SUPPORTED): Linear-probability FE approximation.
- **T4** (INCONCLUSIVE): Only 13 full weeks.
- **P4** (SUPPORTED): 39% of details carry no country token.
- **X3** (SUPPORTED): Expectation model has its own noise.
- **X4** (SUPPORTED): Mule definition is data-driven.
- **X5** (INCONCLUSIVE): Label not documented in official materials.
- **G1** (INCONCLUSIVE): Mechanism of the affinity (bank-level preference lists?) not identified.
- **D3** (SUPPORTED): Fitted on pc=2 rows with exactly one slow bank.
- **Vehicle currency (C3/H38):** rates quantified, mechanism not identified.
- **Synthetic data:** rates, country effects and bank classes are generator settings, not real market structure.
- **Source code:** agreement with the data, even exact, does not identify how the generator was written; alternative programs could produce the same output.

## 16. Conclusions and future research

The generator is a small set of simple mechanisms: geometric route length (R1), route-derived conversions (C2), route-drawn currencies (C3), bank-level habits for cover (R2), customer mix (P5) and processing speed (D1), a 6 + 2 + 2 lognormal amount model (A1/A2), a local office clock with global weekly levels (T1/T4b), and labelled anomalies injected with clear signatures (X1–X4). The highest-value open questions are the cause of the weekly levels, the bank-pair affinity structure and the vehicle-currency choice.

## 17. References and reproducibility

**Primary data:** Swift. (2026). *UMDAC Datathon 2026 fictitious payment dataset* [Data set]. Provided to participants.

**Verified context references** (interpretation only; checked 14 Nov 2026):

- Committee on Payments and Market Infrastructures. (2016, July). *Correspondent banking*. Bank for International Settlements. https://www.bis.org/cpmi/publ/d147.htm
- Financial Stability Board. (2020, October 13). *Enhancing cross-border payments: Stage 3 roadmap*. https://www.fsb.org/2020/10/enhancing-cross-border-payments-stage-3-roadmap/
- Swift. (n.d.). *Swift GPI*. Retrieved November 14, 2026, from https://www.swift.com/products/swift-gpi
- Bank for International Settlements. (2022, October 27). *OTC foreign exchange turnover in April 2022* [Triennial Central Bank Survey]. https://www.bis.org/statistics/rpfx22.htm
- Swift. (n.d.). *International Bank Account Number (IBAN)*. Retrieved November 14, 2026, from https://www.swift.com/standards/data-standards/iban-international-bank-account-number

**Reproduce:**

```bash
pip install -r requirements.txt
python run_all.py            # or --skip-ingest when the Parquet files exist
python -m pytest -q tests
```

